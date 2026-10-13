/* DS для аналитиков — главная, заметки, статистика, шпаргалка. */
(function () {
  'use strict';

  var D = window.DSC, u = D.u, P = D.Progress;
  var $ = u.$, $$ = u.$$, el = u.el, esc = u.esc, ROOT = D.ROOT;
  var page = document.body.dataset.page;

  function fmtDate(s) { return new Date(s.length === 10 ? s + 'T00:00' : s).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }); }

  // ---------- сводка по прогрессу ----------
  function summary() {
    var tasks = D.allTasks();
    var solved = tasks.filter(function (x) { return P.isSolved(x.key); });
    var clean = solved.filter(function (x) { return !(P.task(x.key).help); });
    var lessonsReady = 0, lessonsDone = 0;
    D.COURSE.forEach(function (ch) {
      ch.lessons.forEach(function (ls) {
        if (!ls.tasks.length) return;
        lessonsReady++;
        var p = D.lessonProgress(ch.id + '/' + ls.id, ls.tasks);
        if (p.complete) lessonsDone++;
      });
    });
    // решено по дням (первое решение задачи)
    var byDay = {};
    solved.forEach(function (x) { var d = u.dayStr(new Date(P.task(x.key).solved)); byDay[d] = (byDay[d] || 0) + 1; });
    // серия: дни подряд до сегодня (или до вчера, если сегодня ещё ничего)
    var streak = 0, d = new Date();
    if (!byDay[u.dayStr(d)]) d.setDate(d.getDate() - 1);
    while (byDay[u.dayStr(d)]) { streak++; d.setDate(d.getDate() - 1); }
    return { tasks: tasks, solved: solved, clean: clean, lessonsReady: lessonsReady, lessonsDone: lessonsDone, byDay: byDay, streak: streak };
  }

  function reviewList(host, limit) {
    var due = P.dueList();
    host.textContent = '';
    if (!due.length) return 0;
    var box = el('section', 'review');
    box.innerHTML = '<div class="review-head"><h2>Повторить сегодня</h2><span class="muted">' + due.length + ' ' +
      u.plural(due.length, 'задача', 'задачи', 'задач') + ' — решите заново без подсказок</span></div>';
    var ol = el('ol', 'review-list');
    due.slice(0, limit || 50).forEach(function (x) {
      var e = P.task(x.key);
      var li = el('li'); var a = el('a'); a.href = x.url;
      a.innerHTML = '<span class="rt">' + esc(x.t.title) + '</span><span class="rl">' + esc(x.ls.n + '. ' + x.ls.title) + '</span>' +
        '<span class="rw">' + (e.help === 2 ? 'было по решению' : e.help === 1 ? 'было с подсказкой' : 'на повторение') + '</span>';
      li.appendChild(a); ol.appendChild(li);
    });
    box.appendChild(ol);
    if (due.length > (limit || 50)) box.appendChild(el('p', 'muted', 'И ещё ' + (due.length - limit) + ' — на странице статистики.'));
    host.appendChild(box);
    return due.length;
  }

  // ---------- главная ----------
  function home() {
    function render() {
      var last = P.state.last;
      var e = last && D.lessonEntry(last.lesson);
      if (e) {
        $('#resume').hidden = false;
        $('#resume-title').textContent = 'Глава ' + e.ch.n + ' · Урок ' + e.ls.n + '. ' + e.ls.title;
        var where = last.anchor && last.anchor.indexOf('task-') === 0 ? 'с задачи «' + ((e.ls.tasks.filter(function (t) { return 'task-' + t.id === last.anchor; })[0] || {}).title || '') + '»' : '';
        $('#resume-where').textContent = where;
        $('#resume-link').href = e.ls.url + (last.anchor ? '#' + last.anchor : '');
      }
      var s = summary();
      $('#stats').innerHTML = '<div><b>' + s.lessonsDone + ' / ' + s.lessonsReady + '</b>уроков пройдено</div>' +
        '<div><b>' + s.solved.length + ' / ' + s.tasks.length + '</b>задач решено</div>' +
        '<div><b>' + s.streak + '</b>' + u.plural(s.streak, 'день', 'дня', 'дней') + ' подряд</div>';
      reviewList($('#review'), 6);
      var cp = $('.core-path');
      if (cp) {
        var keys = (cp.dataset.coreKeys || '').split(' ').filter(Boolean), cdone = 0, cstart = 0;
        keys.forEach(function (k) { var e2 = D.lessonEntry(k); if (!e2) return; var q = D.lessonProgress(k, e2.ls.tasks); if (q.complete) cdone++; else if (q.started) cstart++; });
        $('i', cp).style.width = (keys.length ? 100 * cdone / keys.length : 0) + '%';
        $('#core-progress').textContent = 'пройдено ' + cdone + ' из ' + keys.length + (cstart ? ' · начато ' + cstart : '');
      }
      D.markDots(document);
      if (D.treeFocus && last && last.lesson) D.treeFocus(last.lesson.split('/')[0]);
      $('#storage-note').textContent = P.mode === 'file'
        ? 'Прогресс и заметки сохраняются в файл progress/progress.json в папке курса.'
        : 'Прогресс хранится только в этом браузере — открывайте курс через ' + D.launcher + ', чтобы он сохранялся в файл.';
    }
    $('#export-btn').onclick = D.exportProgress;
    $('#import-file').onchange = function (ev) { var f = ev.target.files[0]; if (f) D.importProgress(f); };
    P.init().then(render); render();
    P.onChange(render);
  }

  // ---------- заметки ----------
  function notes() {
    function render() {
      var host = $('#notes-list'); host.textContent = '';
      var any = false, md = ['# Мои заметки — Data Science для аналитиков', ''];
      D.COURSE.forEach(function (ch) {
        ch.lessons.forEach(function (ls) {
          var n = P.state.notes[ch.id + '/' + ls.id];
          if (!n || !n.text.trim()) return;
          any = true;
          var card = el('article', 'note-card');
          card.innerHTML = '<div class="eyebrow">Глава ' + ch.n + ' · ' + esc(fmtDate(n.t)) + '</div><h2><a href="' + ROOT + ls.url + '#notes">' +
            esc(ls.n + '. ' + ls.title) + '</a></h2>';
          var body = el('div', 'note-text', n.text); card.appendChild(body);
          host.appendChild(card);
          md.push('## Глава ' + ch.n + ', урок ' + ls.n + '. ' + ls.title, '', n.text.trim(), '');
        });
      });
      if (!any) host.appendChild(el('p', 'muted', 'Заметок пока нет. Их можно писать в конце каждого урока — блок «Мои заметки».'));
      $('#notes-export').hidden = !any;
      $('#notes-export').onclick = function () {
        var blob = new Blob([md.join('\n')], { type: 'text/markdown' });
        var a = el('a'); a.href = URL.createObjectURL(blob); a.download = 'заметки-ds-course.md'; document.body.appendChild(a); a.click(); a.remove();
      };
    }
    P.init().then(render); render(); P.onChange(render);
  }

  // ---------- статистика ----------
  function stats() {
    function render() {
      var s = summary();
      var tiles = [
        [s.solved.length + ' / ' + s.tasks.length, 'задач решено'],
        [s.lessonsDone + ' / ' + s.lessonsReady, 'уроков пройдено'],
        [s.streak, u.plural(s.streak, 'день', 'дня', 'дней') + ' подряд'],
        [s.solved.length ? Math.round(100 * s.clean.length / s.solved.length) + '%' : '—', 'решено без подсказок']
      ];
      $('#tiles').innerHTML = tiles.map(function (t) { return '<div class="tile"><b>' + t[0] + '</b><span>' + t[1] + '</span></div>'; }).join('');

      // столбики: задач в день за 30 дней
      var days = [], max = 1;
      for (var i = 29; i >= 0; i--) { var d = new Date(); d.setDate(d.getDate() - i); var k = u.dayStr(d); days.push([d, s.byDay[k] || 0]); max = Math.max(max, s.byDay[k] || 0); }
      var top = Math.max(4, Math.ceil(max / 4) * 4);
      var chart = $('#chart'); chart.innerHTML = '';
      var plot = el('div', 'bars'); plot.setAttribute('role', 'img');
      plot.setAttribute('aria-label', 'Решено задач по дням за последние 30 дней, всего ' + days.reduce(function (a, x) { return a + x[1]; }, 0));
      [top, top / 2, 0].forEach(function (v) { var g = el('div', 'grid-line'); g.style.bottom = (100 * v / top) + '%'; g.dataset.v = v; plot.appendChild(g); });
      days.forEach(function (x, i) {
        var col = el('div', 'bar-col');
        var label = x[0].toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ': ' + x[1] + ' ' + u.plural(x[1], 'задача', 'задачи', 'задач');
        col.dataset.tip = label; col.setAttribute('aria-label', label); col.tabIndex = 0;
        var b = el('i'); b.style.height = (100 * x[1] / top) + '%'; if (!x[1]) b.className = 'zero';
        col.appendChild(b); plot.appendChild(col);
      });
      chart.appendChild(plot);
      var axis = el('div', 'bars-axis');
      [days[0][0], days[14][0], days[29][0]].forEach(function (d, i) { var sp = el('span', '', i === 2 ? 'сегодня' : d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })); axis.appendChild(sp); });
      chart.appendChild(axis);
      $('#chart-table').innerHTML = '<table><thead><tr><th>День</th><th>Решено</th></tr></thead><tbody>' +
        days.filter(function (x) { return x[1]; }).map(function (x) { return '<tr><td>' + x[0].toLocaleDateString('ru-RU') + '</td><td>' + x[1] + '</td></tr>'; }).join('') + '</tbody></table>';

      // темп и прогноз по готовым урокам
      // окно темпа: 14 дней, но не раньше первого решения (иначе в начале курса темп занижен)
      var first = s.solved.map(function (x) { return P.task(x.key).solved; }).sort()[0];
      var span = first ? Math.min(14, Math.floor((new Date(u.dayStr()) - new Date(u.dayStr(new Date(first)))) / 864e5) + 1) : 14;
      var lastN = 0; for (var j = 0; j < span; j++) { var dd = new Date(); dd.setDate(dd.getDate() - j); lastN += s.byDay[u.dayStr(dd)] || 0; }
      var left = s.tasks.length - s.solved.length;
      var pace = lastN / span;
      var forecast = $('#forecast');
      if (!s.solved.length) forecast.textContent = 'Темп появится, когда будут решены первые задачи.';
      else if (!left) forecast.textContent = 'Все готовые задачи решены. Новые уроки появятся на карте курса.';
      else if (!pace) forecast.textContent = 'За последние две недели задач не было. Осталось ' + left + ' ' + u.plural(left, 'задача', 'задачи', 'задач') + ' в готовых уроках.';
      else {
        var daysLeft = Math.ceil(left / pace), end = new Date(); end.setDate(end.getDate() + daysLeft);
        forecast.innerHTML = 'Темп за ' + span + ' ' + u.plural(span, 'день', 'дня', 'дней') + ' — <b>' + pace.toFixed(1).replace('.', ',') + '</b> задачи в день. Осталось ' + left + ' ' +
          u.plural(left, 'задача', 'задачи', 'задач') + ' в готовых уроках — при этом темпе примерно <b>' + daysLeft + ' ' +
          u.plural(daysLeft, 'день', 'дня', 'дней') + '</b>, до ' + end.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }) + '.';
      }

      // главы
      var chHost = $('#chapters'); chHost.innerHTML = '';
      D.COURSE.forEach(function (ch) {
        var all = 0, done = 0, ready = 0;
        ch.lessons.forEach(function (ls) { if (!ls.tasks.length) return; ready++; var p = D.lessonProgress(ch.id + '/' + ls.id, ls.tasks); all += p.count; done += p.all; });
        if (!ready) return;
        var row = el('div', 'ch-row');
        row.innerHTML = '<span class="ch-name">' + ch.n + '. ' + esc(ch.title) + '</span><div class="meter"><i style="width:' + (all ? 100 * done / all : 0) + '%"></i></div>' +
          '<span class="ch-val">' + done + ' / ' + all + '</span>';
        chHost.appendChild(row);
      });

      // трудные места
      hardSpots($('#hard'));

      // повторение
      if (!reviewList($('#review'))) {
        var later = D.allTasks().filter(function (x) { var e = P.task(x.key); return e && e.solved && e.due; }).length;
        $('#review').innerHTML = '<h2>Повторение</h2><p class="muted">Сегодня повторять нечего.' + (later ? ' Запланировано на другие дни: ' + later + '.' : '') + '</p>';
      }
    }
    P.init().then(render); render(); P.onChange(render);
  }

  // ---------- трудные места ----------
  function hardSpots(host) {
    if (!host) return;
    var byKey = {}; D.allTasks().forEach(function (x) { byKey[x.key] = x; });
    var tasks = Object.keys(P.state.tasks).filter(function (k) { return byKey[k]; }).map(function (k) {
      var e = P.state.tasks[k];
      var score = Math.max(0, (e.att || 0) - 1) + 2 * (e.hints || 0) + (e.help === 2 ? 4 : 0) + (e.solved ? 0 : (e.att ? 2 : 0));
      return { x: byKey[k], e: e, score: score };
    }).filter(function (r) { return r.score >= 2; }).sort(function (a, b) { return b.score - a.score; }).slice(0, 10);
    var wrong = Object.keys(P.state.quiz).filter(function (k) { return !P.state.quiz[k].ok; });
    var unclear = Object.keys(P.state.fb).filter(function (k) { return P.state.fb[k].v < 0; });
    var html = '<h2>Где было трудно</h2><p class="muted small">По попыткам, подсказкам, открытым решениям, ответам «Предскажите вывод» и «Проверьте себя» и отметкам «Не очень». ' +
      'По этим данным уроки и правятся.</p>';
    if (!tasks.length && !wrong.length && !unclear.length) { host.innerHTML = html + '<p class="muted">Пока трудных мест нет.</p>'; return; }
    if (tasks.length) {
      html += '<h3>Задачи</h3><ul class="hard-list">' + tasks.map(function (r) {
        var d = []; if (r.e.att) d.push('попыток: ' + r.e.att); if (r.e.hints) d.push('подсказок: ' + r.e.hints);
        if (r.e.help === 2) d.push('решено по решению'); if (!r.e.solved) d.push('не решена');
        return '<li><a href="' + r.x.url + '">' + esc(r.x.t.title) + '</a> <span class="muted">— урок ' + r.x.ls.n + '. ' + esc(r.x.ls.title) + ' · ' + d.join(' · ') + '</span></li>';
      }).join('') + '</ul>';
    }
    if (unclear.length) {
      html += '<h3>Разделы «Не очень понятно»</h3><ul class="hard-list">' + unclear.map(function (k) {
        var p = k.split('#'), e = D.lessonEntry(p[0]); var f = P.state.fb[k];
        return '<li><a href="' + (e ? ROOT + e.ls.url + '#' + p[1] : '#') + '">' + esc(e ? e.ls.n + '. ' + e.ls.title : p[0]) + ' → ' + esc(f.h || p[1].replace(/-/g, ' ')) + '</a>' +
          (f.c ? '<div class="muted small">«' + esc(f.c) + '»</div>' : '') + '</li>';
      }).join('') + '</ul>';
    }
    if (wrong.length) {
      var byL = {}; wrong.forEach(function (k) { var l = k.split('#')[0]; byL[l] = (byL[l] || 0) + 1; });
      html += '<h3>Неверные ответы: «Предскажите вывод» и «Проверьте себя»</h3><ul class="hard-list">' + Object.keys(byL).map(function (l) {
        var e = D.lessonEntry(l), isTest = /\/test$/.test(l), ch = isTest && (window.DSC_COURSE || []).filter(function (c) { return c.id === l.split('/')[0]; })[0];
        var href = e ? ROOT + e.ls.url : isTest ? ROOT + l + '.html' : '#';
        var name = e ? e.ls.n + '. ' + e.ls.title : ch ? 'Итоговый тест главы ' + ch.n + '. ' + ch.title : l;
        return '<li><a href="' + href + '">' + esc(name) + '</a> <span class="muted">— ' + byL[l] + '</span></li>';
      }).join('') + '</ul>';
    }
    host.innerHTML = html;
  }

  // ---------- шпаргалка: фильтр ----------
  function cheatsheet() {
    var input = $('#cs-filter'), cards = $$('.cs-card'), empty = $('#cs-empty');
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase().replace(/ё/g, 'е');
      var n = 0;
      cards.forEach(function (c) {
        var ok = !q || c.textContent.toLowerCase().replace(/ё/g, 'е').indexOf(q) >= 0;
        c.hidden = !ok; if (ok) n++;
      });
      $$('.cs-lesson').forEach(function (s) { s.hidden = !$$('.cs-card', s).some(function (c) { return !c.hidden; }); });
      empty.hidden = n > 0;
    });
    P.init();
  }

  ({ home: home, notes: notes, stats: stats, cheatsheet: cheatsheet }[page] || function () {})();
})();
