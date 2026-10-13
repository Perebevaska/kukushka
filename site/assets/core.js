/* DS для аналитиков — общее для всех страниц: утилиты, тема, прогресс (браузер + файл), повторение, поиск. */
(function () {
  'use strict';

  var D = window.DSC = window.DSC || {};
  var ROOT = D.ROOT = document.body.dataset.root || '';
  var COURSE = D.COURSE = window.DSC_COURSE || [];
  D.isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  D.isWin = /Win/.test(navigator.platform || navigator.userAgent);
  // запускалка курса для этой системы — в подсказках «откройте курс через …»
  D.launcher = D.isMac ? '«Курс.command»' : D.isWin ? '«Курс-Windows.bat»' : '«Курс-Linux.sh»';

  // ---------- утилиты ----------
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function btn(label, cls, title) { var b = el('button', 'btn ' + (cls || ''), label); b.type = 'button'; if (title) b.title = title; return b; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function toast(msg, ms) {
    var t = $('#toast'); if (!t) return;
    t.textContent = msg; t.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(function () { t.classList.remove('show'); }, ms || 2600);
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    var ta = el('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    ta.remove(); return Promise.resolve();
  }
  function now() { return new Date().toISOString(); }
  function dayStr(d) { d = d || new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function addDays(n) { var d = new Date(); d.setDate(d.getDate() + n); return dayStr(d); }
  function plural(n, one, few, many) {
    var m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? one : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? few : many);
  }
  D.u = { $: $, $$: $$, el: el, btn: btn, esc: esc, toast: toast, copyText: copyText, now: now, dayStr: dayStr, addDays: addDays, plural: plural };

  // ---------- каталог курса ----------
  D.lessonEntry = function (id) {
    for (var i = 0; i < COURSE.length; i++) for (var j = 0; j < COURSE[i].lessons.length; j++)
      if (COURSE[i].id + '/' + COURSE[i].lessons[j].id === id) return { ch: COURSE[i], ls: COURSE[i].lessons[j] };
    return null;
  };
  D.allTasks = function () {
    var out = [];
    COURSE.forEach(function (ch) {
      ch.lessons.forEach(function (ls) {
        (ls.tasks || []).forEach(function (t) {
          out.push({ key: ch.id + '/' + ls.id + '/' + t.id, ch: ch, ls: ls, t: t, url: ROOT + ls.url + '#task-' + t.id });
        });
      });
    });
    return out;
  };

  // ---------- тема ----------
  function initTheme() {
    var b = $('#theme-btn'); if (!b) return;
    b.addEventListener('click', function () {
      var cur = document.documentElement.dataset.theme ||
        (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('dsc.theme', next); } catch (e) {}
    });
  }

  // =====================================================================
  // Прогресс. Одно состояние:
  //   { v:2, t, last:{lesson, anchor, t}, notes:{lesson:{text,t}},
  //     tasks:{ "ch01/02-numbers/avg-check": {t, solved, help, att, ah, as, code, retry, due, ivl, reviews} } }
  // Хранится в localStorage (быстро) и, если курс открыт через tools/serve.py, — в progress/progress.json.
  // Слияние по записям: берётся более свежая (t); «решено» не теряется никогда.
  // =====================================================================
  var LS_KEY = 'dsc.v2.state';
  var P = D.Progress = { state: null, mode: 'browser', listeners: [], saveT: null, error: null };

  function ts(x) { return (x && x.t) || ''; }
  var MAPS = D.MAPS = ['notes', 'quiz', 'fb', 'exam', 'read'];
  function mergeState(a, b) {
    a = a || {}; b = b || {};
    var out = { v: 2, tasks: {}, last: null };
    var keys = {};
    Object.keys(a.tasks || {}).concat(Object.keys(b.tasks || {})).forEach(function (k) { keys[k] = 1; });
    Object.keys(keys).forEach(function (k) {
      var x = (a.tasks || {})[k], y = (b.tasks || {})[k];
      if (!x || !y) { out.tasks[k] = x || y; return; }
      var n = Object.assign({}, ts(y) >= ts(x) ? y : x);
      var s = [x.solved, y.solved].filter(Boolean).sort();
      n.solved = s[0] || null;
      out.tasks[k] = n;
    });
    // словари «ключ → {…, t}»: заметки, ответы на вопросы, «понятно/непонятно», контрольные
    MAPS.forEach(function (m) {
      out[m] = {};
      var nk = {};
      Object.keys(a[m] || {}).concat(Object.keys(b[m] || {})).forEach(function (k) { nk[k] = 1; });
      Object.keys(nk).forEach(function (k) {
        var x = (a[m] || {})[k], y = (b[m] || {})[k];
        out[m][k] = ts(y) >= ts(x) ? y : x;
      });
    });
    out.last = ts(b.last) >= ts(a.last) ? b.last : a.last;
    out.t = ts(a) > ts(b) ? a.t : (b.t || a.t || now());
    return renameMoved(out);
  }
  // задачи, переехавшие в новый урок при его делении: переносим прогресс на новый ключ
  function renameMoved(st) {
    var M = window.DSC_MOVED || {};
    [st.tasks].concat(MAPS.map(function (m) { return st[m]; })).forEach(function (d) {
      if (!d) return;
      Object.keys(d).forEach(function (k) {
        var nk = M[k];
        if (!nk) return;
        if (!d[nk]) d[nk] = d[k];
        delete d[k];
      });
    });
    return st;
  }
  D.mergeState = mergeState;

  function migrateV1() {
    var st = { v: 2, tasks: {}, notes: {}, last: null, t: now() };
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i), v = localStorage.getItem(k), m;
        if ((m = /^dsc\.v1\.ok\.(.+)\.([^.]+)$/.exec(k)) && v === '1') {
          var key = m[1] + '/' + m[2];
          st.tasks[key] = Object.assign(st.tasks[key] || {}, { solved: st.t, help: 0, t: st.t });
        } else if ((m = /^dsc\.v1\.code\.(.+)\.([^.]+)$/.exec(k))) {
          var key2 = m[1] + '/' + m[2];
          st.tasks[key2] = Object.assign(st.tasks[key2] || { solved: null, t: st.t }, { code: v });
        } else if (k === 'dsc.v1.last') {
          st.last = { lesson: v, anchor: '', t: st.t };
        }
      }
    } catch (e) {}
    return st;
  }

  P.loadLocal = function () {
    var raw = null;
    try { raw = localStorage.getItem(LS_KEY); } catch (e) {}
    var st = null;
    try { st = raw && JSON.parse(raw); } catch (e) { st = null; }
    P.state = st && st.v === 2 ? st : migrateV1();
    // прогресс старой версии курса (v1) переносим один раз, даже если v2 уже есть
    try {
      if (!localStorage.getItem('dsc.v1.migrated')) {
        var hasV1 = false;
        for (var i = 0; i < localStorage.length; i++) if (localStorage.key(i).indexOf('dsc.v1.') === 0) { hasV1 = true; break; }
        if (hasV1 && st) P.state = mergeState(P.state, migrateV1());
        localStorage.setItem('dsc.v1.migrated', '1');
        writeLocal();
      }
    } catch (e) {}
    if (!P.state.tasks) P.state.tasks = {};
    MAPS.forEach(function (m) { if (!P.state[m]) P.state[m] = {}; });
    renameMoved(P.state);
    return P.state;
  };
  function writeLocal() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(P.state)); } catch (e) {}
  }
  function emit() { P.listeners.forEach(function (f) { try { f(P.state); } catch (e) {} }); }
  P.onChange = function (f) { P.listeners.push(f); };

  function setSaveState(kind, text) {
    var b = $('#save-pill'); if (!b) return;
    b.dataset.state = kind; b.title = text; $('span', b).textContent =
      { file: 'Сохранено', saving: 'Сохраняю…', browser: 'В браузере', error: 'Не сохранено' }[kind];
  }

  function fetchJSON(url, opts, ms) {
    var ctl = 'AbortController' in window ? new AbortController() : null;
    var timer = ctl && setTimeout(function () { ctl.abort(); }, ms || 2500);
    return fetch(url, Object.assign({ cache: 'no-store', signal: ctl && ctl.signal }, opts || {})).then(function (r) {
      clearTimeout(timer);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  P.push = function () {
    if (P.mode !== 'file') return Promise.resolve();
    setSaveState('saving', 'Сохраняю в файл progress/progress.json…');
    return fetchJSON(ROOT + 'api/progress', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(P.state) }, 5000)
      .then(function (merged) {
        P.state = mergeState(P.state, merged); writeLocal();
        P.error = null;
        setSaveState('file', 'Прогресс сохранён в файл progress/progress.json в папке курса');
      }, function (e) {
        P.error = e;
        setSaveState('error', 'Не удалось записать файл прогресса (сервер курса остановлен?). Прогресс сохранён в браузере и уйдёт в файл при следующем сохранении.');
      });
  };
  // запись в файл: через 0,7 с после последнего изменения, но не реже раза в 3 с
  P.save = function () {
    P.state.t = now();
    writeLocal();
    if (P.mode === 'file') {
      var t = Date.now();
      if (!P.pendingSince) P.pendingSince = t;
      clearTimeout(P.saveT);
      setSaveState('saving', 'Сохраняю…');
      P.saveT = setTimeout(function () { P.pendingSince = 0; P.push(); }, Math.max(0, Math.min(700, 3000 - (t - P.pendingSince))));
    }
    emit();
  };
  // уходим со страницы, а запись ещё не ушла — отправляем сразу
  P.flushers = [];   // несохранённые правки в редакторах (у них свой дебаунс) — сбросить перед уходом
  window.addEventListener('pagehide', function () {
    P.flushers.forEach(function (f) { try { f(); } catch (e) {} });
    if (P.mode !== 'file' || !P.pendingSince) return;
    clearTimeout(P.saveT); P.pendingSince = 0;
    try { navigator.sendBeacon(ROOT + 'api/progress', new Blob([JSON.stringify(P.state)], { type: 'application/json' })); } catch (e) {}
  });
  // подтянуть файл с сервера и слить с тем, что в браузере
  P.pull = function () {
    if (location.protocol === 'file:') return Promise.resolve(false);
    return fetchJSON(ROOT + 'api/progress', null, 1500).then(function (server) {
      P.mode = 'file';
      var before = JSON.stringify(P.state);
      P.state = mergeState(P.state, server);
      writeLocal();
      server = server || {};
      var differs = JSON.stringify([P.state.tasks, P.state.last].concat(MAPS.map(function (m) { return P.state[m]; }))) !==
        JSON.stringify([server.tasks || {}, server.last || null].concat(MAPS.map(function (m) { return server[m] || {}; })));
      if (differs) P.push(); else setSaveState('file', 'Прогресс сохранён в файл progress/progress.json в папке курса');
      if (before !== JSON.stringify(P.state)) emit();
      return true;
    }, function () {
      P.mode = 'browser';
      setSaveState('browser', /\.github\.io$/.test(location.hostname)
        ? 'Прогресс хранится только в этом браузере. Чтобы не потерять его или перенести на другое устройство, сохраните копию в файл на главной.'
        : 'Прогресс хранится только в этом браузере. Чтобы он сохранялся в файл, открывайте курс через ' + D.launcher + '. Или сохраните прогресс в файл на главной.');
      return false;
    });
  };
  P.init = function () {
    P.loadLocal();
    // другая вкладка что-то решила — подхватываем
    window.addEventListener('storage', function (e) {
      if (e.key !== LS_KEY || !e.newValue) return;
      try { P.state = mergeState(P.state, JSON.parse(e.newValue)); emit(); } catch (err) {}
    });
    document.addEventListener('visibilitychange', function () { if (!document.hidden && P.mode === 'file') P.pull(); });
    return P.pull();
  };

  // ---------- задачи: чтение и обновление ----------
  P.task = function (key) { return P.state.tasks[key] || null; };
  P.updateTask = function (key, patch) {
    var t = Object.assign({ solved: null }, P.state.tasks[key] || {}, patch, { t: now() });
    P.state.tasks[key] = t; P.save(); return t;
  };
  P.isSolved = function (key) { var t = P.task(key); return !!(t && t.solved); };

  // Повторение: решено с помощью → вернуть через 1 (решение) или 3 (подсказки) дня;
  // чистое повторное решение → интервал 3 → 7 → 15 → выучено.
  var NEXT = { 1: 3, 3: 7, 7: 15 };
  P.onSolved = function (key) {
    var t = Object.assign({}, P.task(key) || {});
    var help = t.as ? 2 : (t.ah ? 1 : 0);
    var first = !t.solved;
    var patch = { ah: 0, as: false, retry: false, lastHelp: help, solvedAt: now() };
    if (first) {
      patch.solved = now(); patch.help = help;
      if (help) { patch.ivl = help === 2 ? 1 : 3; patch.due = addDays(patch.ivl); }
    } else {
      patch.reviews = (t.reviews || 0) + 1;
      if (help) { patch.ivl = 1; patch.due = addDays(1); }
      else if (t.due || t.retry) {
        var nx = NEXT[t.ivl || 1];
        patch.ivl = nx || null; patch.due = nx ? addDays(nx) : null;
      }
    }
    return P.updateTask(key, patch);
  };
  P.isDue = function (t) { return !!(t && t.solved && t.due && t.due <= dayStr()); };
  P.dueList = function () {
    return D.allTasks().filter(function (x) { return P.isDue(P.task(x.key)); });
  };

  // ---------- прогресс урока ----------
  D.lessonProgress = function (lessonId, tasks) {
    var base = tasks.filter(function (t) { return t.level !== 'star'; });
    var done = base.filter(function (t) { return P.isSolved(lessonId + '/' + t.id); }).length;
    var all = tasks.filter(function (t) { return P.isSolved(lessonId + '/' + t.id); }).length;
    // теория: разделы, отмеченные прочитанными (P.state.read['урок#раздел'])
    var e = D.lessonEntry(lessonId), secs = (e && e.ls.secs) || [], rd = (P.state && P.state.read) || {};
    var read = secs.filter(function (s) { return rd[lessonId + '#' + s]; }).length;
    return { done: done, total: base.length, all: all, count: tasks.length, read: read, secs: secs.length,
      complete: done >= base.length && read >= secs.length, started: all > 0 || read > 0 };
  };
  D.examEntry = function (id) {
    for (var i = 0; i < COURSE.length; i++) for (var j = 0; j < (COURSE[i].exams || []).length; j++)
      if (COURSE[i].id + '/' + COURSE[i].exams[j].id === id) return { ch: COURSE[i], ex: COURSE[i].exams[j] };
    return null;
  };
  D.markDots = function (scope) {
    setTimeout(function () { if (D.treeCounts) D.treeCounts(); }, 0);
    // страница «О главе» считается пройденной, как только её открыли
    var introPage = document.body && document.body.dataset.chintroPage;
    if (introPage && P.state) {
      P.state.read = P.state.read || {};
      if (!P.state.read[introPage + '/_intro']) { P.state.read[introPage + '/_intro'] = { t: now() }; P.save(); }
    }
    $$('[data-chintro]', scope).forEach(function (a) {
      var rd = P.state && P.state.read && P.state.read[a.dataset.chintro + '/_intro'];
      if (rd) { a.dataset.done = 'all'; a.title = 'Просмотрено'; } else { delete a.dataset.done; a.removeAttribute('title'); }
    });
    $$('[data-exam]', scope).forEach(function (a) {
      var st = P.state && P.state.exam[a.dataset.exam];
      a.dataset.done = st && st.done ? (st.score >= 80 ? 'all' : 'part') : '';
      var pc = $('[data-p]', a); if (pc) pc.textContent = st && st.done ? st.score + '%' : '';
    });
    $$('[data-ctest]', scope).forEach(function (a) {
      var id = a.dataset.ctest + '/test', n = +a.dataset.n || 0, att = ((P.state && P.state.exam[id]) || {}).n || 1;
      var ans = 0, ok = 0;
      Object.keys((P.state && P.state.quiz) || {}).forEach(function (k) {
        if (k.indexOf(id + '#') !== 0) return;
        var suf = k.split('#')[1].split('/')[1];
        if ((suf ? +suf : 1) !== att) return;
        ans++; if (P.state.quiz[k].ok) ok++;
      });
      a.dataset.done = ans >= n && n ? (ok / n >= 0.8 ? 'all' : 'part') : (ans ? 'part' : '');
      var pc = $('[data-p]', a); if (pc) pc.textContent = ans ? ok + '/' + n : '';
    });
    $$('[data-lesson]', scope).forEach(function (a) {
      var e = D.lessonEntry(a.dataset.lesson); if (!e || !(e.ls.tasks.length || (e.ls.secs || []).length)) return;
      var p = D.lessonProgress(a.dataset.lesson, e.ls.tasks);
      a.dataset.done = p.complete ? 'all' : (p.started ? 'part' : '');
      var pc = $('[data-p]', a); if (pc) pc.textContent = p.all ? p.all + '/' + p.count : '';
    });
  };

  // ---------- экспорт / импорт ----------
  D.exportProgress = function () {
    var blob = new Blob([JSON.stringify({ app: 'ds-course', v: 2, saved: now(), state: P.state }, null, 1)], { type: 'application/json' });
    var a = el('a'); a.href = URL.createObjectURL(blob); a.download = 'ds-course-прогресс-' + dayStr() + '.json';
    document.body.appendChild(a); a.click(); a.remove();
  };
  D.importProgress = function (file) {
    return file.text().then(function (txt) {
      var j; try { j = JSON.parse(txt); } catch (e) { j = null; }
      if (!j || j.app !== 'ds-course') { toast('Это не файл прогресса курса.'); return; }
      var st = j.v === 2 ? j.state : null;
      if (!st && j.data) {   // файл старого формата (v1)
        st = { v: 2, tasks: {}, notes: {}, last: null };
        Object.keys(j.data).forEach(function (k) {
          var m = /^dsc\.v1\.ok\.(.+)\.([^.]+)$/.exec(k);
          if (m && j.data[k] === '1') st.tasks[m[1] + '/' + m[2]] = { solved: j.saved || now(), help: 0, t: j.saved || now() };
        });
      }
      if (!st || typeof st.tasks !== 'object') { toast('В файле нет прогресса.'); return; }
      P.state = mergeState(P.state, st); P.save(); P.push();
      toast('Прогресс загружен и объединён с текущим.');
      setTimeout(function () { location.reload(); }, 900);
    });
  };

  // ---------- поиск (Cmd/Ctrl+K) ----------
  function norm(s) { return String(s).toLowerCase().replace(/ё/g, 'е'); }
  function initSearch() {
    var openBtn = $('#search-btn'); if (!openBtn) return;
    var dlg = null, input, list, items = [], active = 0;
    function build() {
      dlg = el('div', 'search'); dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-label', 'Поиск по курсу');
      dlg.innerHTML = '<div class="search-box"><input type="search" placeholder="Поиск: урок, тема, задача, SQL…" aria-label="Поиск по курсу">' +
        '<ol class="search-list" role="listbox"></ol><div class="search-foot">↑↓ — выбрать · Enter — открыть · Esc — закрыть</div></div>';
      document.body.appendChild(dlg);
      input = $('input', dlg); list = $('.search-list', dlg);
      dlg.addEventListener('mousedown', function (e) { if (e.target === dlg) close(); });
      input.addEventListener('input', render);
      input.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { active = Math.min(active + 1, items.length - 1); mark(); e.preventDefault(); }
        else if (e.key === 'ArrowUp') { active = Math.max(active - 1, 0); mark(); e.preventDefault(); }
        else if (e.key === 'Enter' && items[active]) { location.href = items[active].href; close(); }
        else if (e.key === 'Escape') close();
      });
    }
    function mark() {
      $$('li', list).forEach(function (li, i) { li.classList.toggle('active', i === active); if (i === active) li.scrollIntoView({ block: 'nearest' }); });
    }
    function render() {
      var q = norm(input.value.trim()); list.textContent = ''; items = []; active = 0;
      var idx = window.DSC_SEARCH || [];
      if (!q) { list.appendChild(el('li', 'search-empty', 'Начните вводить: «срез», «GROUP BY», «f-строка», «медиана»…')); return; }
      var words = q.split(/\s+/);
      var scored = [];
      idx.forEach(function (it) {
        var hay = norm(it.t + ' ' + it.x);
        if (!words.every(function (w) { return hay.indexOf(w) >= 0; })) return;
        var score = (norm(it.t).indexOf(q) >= 0 ? 0 : 10) + ({ lesson: 0, section: 1, sql: 2, task: 3, recap: 4 }[it.k] || 5);
        scored.push([score, it]);
      });
      scored.sort(function (a, b) { return a[0] - b[0]; });
      scored.slice(0, 40).forEach(function (s) {
        var it = s[1], li = el('li'), a = el('a');
        a.href = ROOT + it.u; li.setAttribute('role', 'option');
        a.innerHTML = '<span class="sk">' + esc({ lesson: 'Урок', section: 'Раздел', sql: 'SQL', task: 'Задача', recap: 'Итог' }[it.k] || '') + '</span>' +
          '<span class="st">' + esc(it.t) + '</span><span class="sw">' + esc(it.w) + '</span>';
        a.addEventListener('click', close);
        li.appendChild(a); list.appendChild(li); items.push(a);
      });
      if (!items.length) list.appendChild(el('li', 'search-empty', 'Ничего не нашлось.'));
      mark();
    }
    function open() {
      if (!dlg) build();
      dlg.classList.add('open'); input.value = ''; render(); input.focus();
    }
    function close() { if (dlg) dlg.classList.remove('open'); }
    openBtn.addEventListener('click', open);
    document.addEventListener('keydown', function (e) {
      var typing = /INPUT|TEXTAREA/.test((document.activeElement || {}).tagName || '') || (document.activeElement && document.activeElement.isContentEditable);
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); open(); }
      else if (e.key === '/' && !typing) { e.preventDefault(); open(); }
    });
  }

  // ---------- оглавление курса (боковая панель) ----------
  D.treeCounts = function () {
    $$('[data-chp]').forEach(function (c) {
      var det = c.closest('details'); if (!det) return;
      var links = $$('a[data-lesson]', det), done = links.filter(function (a) { return a.dataset.done === 'all'; }).length;
      c.textContent = done ? done + '/' + links.length : String(links.length);
      c.classList.toggle('all', !!done && done === links.length);
    });
  };
  function initTree() {
    var tree = $('.course-tree'); if (!tree) return;
    var KEY = 'dsc.tree.open', dets = $$('details.tree-ch', tree), stored = null;
    try { stored = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { /* нет хранилища */ }
    if (dets.length && !dets.some(function (d) { return d.open; })) {   // главная: запомненные или глава последнего урока
      var cur = null;
      try { cur = P.state && P.state.last && P.state.last.lesson ? P.state.last.lesson.split('/')[0] : null; } catch (e) { /* ок */ }
      dets.forEach(function (d) { d.open = stored ? stored.indexOf(d.dataset.ch) >= 0 : d.dataset.ch === (cur || dets[0].dataset.ch); });
    }
    var btn = $('[data-tree-toggle]');
    function label() { if (btn) btn.textContent = dets.every(function (d) { return d.open; }) ? 'Свернуть всё' : 'Развернуть всё'; }
    function save() {
      label();
      if (document.body.dataset.page !== 'home') return;   // на уроке открыта глава урока — не запоминаем
      try { localStorage.setItem(KEY, JSON.stringify(dets.filter(function (d) { return d.open; }).map(function (d) { return d.dataset.ch; }))); } catch (e) { /* ок */ }
    }
    dets.forEach(function (d) { d.addEventListener('toggle', save); });
    if (btn) btn.onclick = function () { var open = !dets.every(function (d) { return d.open; }); dets.forEach(function (d) { d.open = open; }); save(); };
    label();
    var curA = $('a[aria-current]', tree);
    if (curA) { var sb = tree.closest('.sidebar'); if (sb) sb.scrollTop = Math.max(0, curA.offsetTop - sb.clientHeight / 3); }
    D.treeCounts();
    // главная: когда прогресс загрузится, раскрыть главу последнего урока (если пользователь сам ничего не раскрывал)
    D.treeFocus = function (chId) {
      if (stored || !chId) return;
      dets.forEach(function (d) { d.open = d.dataset.ch === chId; });
      label();
    };
  }
  function initMenu() {
    var b = $('#menu-btn'); if (!b) return;
    function set(open) { document.body.classList.toggle('menu-open', open); b.setAttribute('aria-expanded', open); }
    b.onclick = function () { set(!document.body.classList.contains('menu-open')); };
    var scrim = $('#scrim'); if (scrim) scrim.onclick = function () { set(false); };
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  }

  // ---------- состояние окружения (на страницах без Python: главная, глава, тест, заметки…) ----------
  // На уроке lesson.js сам запускает Python и перезаписывает индикатор; здесь — быстрая проверка, что всё на месте.
  D.PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
  function checkEnv() {
    var pill = $('#py-pill'); if (!pill) return;
    function set(state, label, title) {
      if (pill.dataset.state !== 'idle' && pill.dataset.state !== 'checking') return;   // урок уже взял индикатор
      pill.dataset.state = state; pill.lastElementChild.textContent = label; pill.title = title;
    }
    if (location.protocol === 'file:') {
      return set('error', 'Нет сервера', 'Курс открыт как файл — Python в браузере не запустится. Откройте курс через ' + D.launcher + ' (см. «КАК ЗАПУСТИТЬ.txt»).');
    }
    pill.dataset.state = 'checking'; pill.lastElementChild.textContent = 'Проверяю…';
    var local = new URL(ROOT + 'assets/vendor/pyodide/pyodide.mjs', location.href).href;
    fetch(local, { method: 'HEAD', cache: 'no-store' }).then(function (r) {
      if (r.ok) return set('ready', 'Окружение готово', 'Python для браузера лежит в папке курса — работает без интернета. На странице урока он загрузится за несколько секунд.');
      return fetch(D.PYODIDE_CDN + 'pyodide.mjs', { method: 'HEAD' }).then(function (c) {
        if (c.ok) set('ready', 'Окружение готово', 'Python для браузера загрузится из интернета (локальной копии в папке курса нет).');
        else throw new Error('cdn');
      });
    }).catch(function () {
      set('error', 'Python недоступен', 'Нет ни локальной копии Python (site/assets/vendor/pyodide), ни доступа к интернету.');
    });
  }

  // ---------- «Только основной путь»: скрыть уроки-углубления в оглавлении и списках ----------
  function initCoreOnly() {
    var on = false;
    try { on = localStorage.getItem('dsc-core-only') === '1'; } catch (e) { /* без хранилища — всё видно */ }
    function apply() {
      document.body.classList.toggle('core-only', on);
      $$('[data-core-only]').forEach(function (cb) { cb.checked = on; });
    }
    $$('[data-core-only]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        on = cb.checked;
        try { localStorage.setItem('dsc-core-only', on ? '1' : '0'); } catch (e) { /* не страшно */ }
        apply(); if (D.treeCounts) D.treeCounts();
      });
    });
    apply();
  }

  // ---------- общий старт ----------
  initCoreOnly();
  initTheme();
  initMenu();
  initTree();
  initSearch();
  if (D.isMac) $$('kbd.mod').forEach(function (k) { k.textContent = '⌘'; });
  $$('.topnav a').forEach(function (a) { if (a.getAttribute('href') && location.pathname.endsWith(a.getAttribute('href').replace(/^.*\//, ''))) a.setAttribute('aria-current', 'page'); });
  setTimeout(checkEnv, 300);
  // страница главы: своих скриптов нет — подтягиваем прогресс, чтобы точки уроков были закрашены
  if (document.body.classList.contains('page-chapter')) {
    P.init().then(function () { D.markDots(document); });
    if (P.onChange) P.onChange(function () { D.markDots(document); });
  }
})();
