/* DS для аналитиков — страница урока: Python в Web Worker, живые примеры, задачи, повторение, заметки, оглавление. */
(function () {
  'use strict';

  var D = window.DSC, u = D.u, P = D.Progress;
  var $ = u.$, $$ = u.$$, el = u.el, btn = u.btn, toast = u.toast;
  var ROOT = D.ROOT;
  var CDN = D.PYODIDE_CDN;
  var LESSON = JSON.parse(document.getElementById('lesson-data').textContent);
  var ICON_PLAY = '<svg viewBox="0 0 16 16"><path d="M4 2.5v11l9-5.5z"/></svg>';
  var EXAM = LESSON.mode === 'exam';
  // у контрольной каждая попытка — свои ключи задач (отметку «решено» нельзя снять, поэтому новая попытка = новые ключи)
  function examState() { return (P.state && P.state.exam[LESSON.lesson]) || { n: 1 }; }
  function prefix() { return EXAM ? LESSON.lesson + '@' + (examState().n || 1) : LESSON.lesson; }
  function key(id) { return prefix() + '/' + id; }
  function examOpen() { return EXAM && !examState().done; }

  // ---------- Python ----------
  var pill = $('#py-pill');
  function setPill(state, text) {
    if (!pill) return;
    pill.dataset.state = state; pill.title = text || '';
    pill.lastElementChild.textContent = { idle: 'Python', loading: 'Python загружается', ready: 'Python готов', busy: 'Выполняю', error: 'Python: ошибка' }[state] || 'Python';
  }

  var Py = {
    worker: null, readyP: null, seq: 0, pending: {}, failed: null,
    pickIndex: function () {
      var local = new URL(ROOT + 'assets/vendor/pyodide/', location.href).href;
      return fetch(local + 'pyodide.mjs', { method: 'HEAD' })
        .then(function (r) { return r.ok ? local : CDN; }, function () { return CDN; });
    },
    start: function () {
      var self = this;
      if (this.readyP) return this.readyP;
      if (location.protocol === 'file:') {
        this.failed = 'Курс открыт как файл. Python в браузере так не запустится — откройте курс через ' + D.launcher + ' в папке курса (см. «КАК ЗАПУСТИТЬ.txt»).';
        setPill('error', this.failed);
        return Promise.reject(new Error(this.failed));
      }
      setPill('loading', 'Python загружается (первый раз — 5–20 секунд)');
      this.readyP = this.pickIndex().then(function (indexURL) {
        return new Promise(function (resolve, reject) {
          var w = new Worker(new URL(ROOT + 'assets/runner.js?v=' + (document.body.dataset.v || ''), location.href), { type: 'module' });
          self.worker = w;
          w.onmessage = function (e) {
            var m = e.data;
            if (m.type === 'ready') {
              setPill('ready', 'Python готов · ' + (indexURL === CDN ? 'из интернета' : 'локально'));
              var txt = (document.querySelector('main') || document.body).textContent;
              var warm = ['pandas', 'matplotlib.pyplot', 'duckdb', 'scipy.stats', 'sklearn', 'statsmodels.api'].filter(function (lib) { return txt.indexOf(lib.split('.')[0]) >= 0; });
              if (warm.length) w.postMessage({ type: 'warm', code: warm.map(function (lib) { return 'import ' + lib; }).join('\n') });
              resolve();
            }
            else if (m.type === 'error') reject(new Error(m.message));
            else if (m.type === 'status') { var p = self.pending[m.id]; p && p.onStatus && p.onStatus(m.text); }
            else if (m.type === 'result') {
              var q = self.pending[m.id]; delete self.pending[m.id];
              if (!Object.keys(self.pending).length) setPill('ready', 'Python готов');
              q && q.resolve(m.result);
            }
          };
          w.onerror = function (ev) { reject(new Error(ev.message || 'Не удалось запустить Python')); };
          w.postMessage({
            type: 'init', indexURL: indexURL,
            harnessURL: new URL(ROOT + 'assets/harness.py?v=' + (document.body.dataset.v || ''), location.href).href,
            dataURL: new URL(ROOT + 'data/', location.href).href
          });
        });
      });
      this.readyP.catch(function (e) {
        self.readyP = null; self.failed = String(e.message || e);
        setPill('error', 'Python не загрузился: ' + self.failed);
      });
      return this.readyP;
    },
    run: function (job, onStatus) {
      var self = this;
      return this.start().then(function () {
        return new Promise(function (resolve) {
          var id = ++self.seq;
          self.pending[id] = { resolve: resolve, onStatus: onStatus };
          setPill('busy');
          self.worker.postMessage({ type: 'run', id: id, code: job.code, check: job.check || null, setup: job.setup || null, files: job.files || [], display: !!LESSON.display });
        });
      });
    },
    trace: function (code, files) {
      var self = this;
      return this.start().then(function () {
        return new Promise(function (resolve) {
          var id = ++self.seq;
          self.pending[id] = { resolve: resolve };
          setPill('busy');
          self.worker.postMessage({ type: 'trace', id: id, code: code, files: files || [] });
        });
      });
    },
    stop: function () {
      if (this.worker) this.worker.terminate();
      var p = this.pending; this.pending = {}; this.worker = null; this.readyP = null;
      Object.keys(p).forEach(function (k) { p[k].resolve({ stopped: true }); });
      setPill('idle');
    }
  };

  // ---------- редактор ----------
  function toggleComment(cm) {
    var from = cm.getCursor('from').line, to = cm.getCursor('to').line;
    if (to > from && cm.getCursor('to').ch === 0) to--;
    var lines = [];
    for (var i = from; i <= to; i++) lines.push(cm.getLine(i));
    var all = lines.filter(function (l) { return l.trim(); }).every(function (l) { return /^\s*#/.test(l); });
    cm.operation(function () {
      for (var i = from; i <= to; i++) {
        var l = cm.getLine(i);
        if (!l.trim()) continue;
        var nl = all ? l.replace(/^(\s*)# ?/, '$1') : l.replace(/^(\s*)/, '$1# ');
        cm.replaceRange(nl, { line: i, ch: 0 }, { line: i, ch: l.length });
      }
    });
  }
  // Tab внутри редактора ставит отступ. Чтобы редактор не был клавиатурной ловушкой (WCAG 2.1.2),
  // Esc переключает режим: следующий Tab / Shift+Tab уводит фокус к соседним элементам.
  // Режим сбрасывается при каждом новом входе в редактор и при любом вводе.
  function mountEditor(host, value, keys) {
    var leave = false;
    var extra = { Tab: function (cm) { if (leave) return focusNear(cm, 1);
                    cm.somethingSelected() ? cm.indentSelection('add') : cm.replaceSelection('    ', 'end'); },
                  'Shift-Tab': function (cm) { if (leave) return focusNear(cm, -1); cm.indentSelection('subtract'); },
                  Esc: function (cm) { leave = true; hint.textContent = HINT_OUT;
                    if (cm.somethingSelected()) cm.setCursor(cm.getCursor('head')); } };
    extra[D.isMac ? 'Cmd-Enter' : 'Ctrl-Enter'] = keys.run; extra['Ctrl-Enter'] = keys.run;
    extra[D.isMac ? 'Cmd-/' : 'Ctrl-/'] = toggleComment;
    if (keys.check) extra['Shift-Enter'] = keys.check;
    var hint = el('div', 'cm-kbd-hint', HINT_IN);
    hint.id = 'cm-hint-' + (++hintSeq);
    var cm = CodeMirror(host, {
      value: value, mode: 'python', indentUnit: 4, tabSize: 4, lineWrapping: false, matchBrackets: true,
      autoCloseBrackets: true, viewportMargin: Infinity, extraKeys: extra, inputStyle: 'contenteditable', spellcheck: false,
      screenReaderLabel: 'Редактор кода. Tab ставит отступ; чтобы выйти, нажмите Esc, затем Tab.'
    });
    host.appendChild(hint);
    var input = cm.getInputField();
    if (input) input.setAttribute('aria-describedby', hint.id);
    cm.on('focus', function () { leave = false; hint.textContent = HINT_IN; });
    cm.on('change', function () { if (leave) { leave = false; hint.textContent = HINT_IN; } });
    return cm;
  }
  // фокус на следующий / предыдущий фокусируемый элемент страницы за пределами редактора
  function focusNear(cm, dir) {
    var wrap = cm.getWrapperElement();
    var all = $$('a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable=true]')
      .filter(function (e) { return e.offsetParent !== null || e === document.activeElement; });
    var inside = function (e) { return wrap.contains(e); };
    var i = all.findIndex(inside);
    if (i < 0) return;
    if (dir > 0) { while (i < all.length && inside(all[i])) i++; } else { i--; }
    var t = all[i];
    if (t) { cm.getInputField().blur(); t.focus(); }
  }
  var hintSeq = 0;
  var HINT_IN = 'Tab — отступ · Esc, затем Tab — выйти из редактора';
  var HINT_OUT = 'Tab / Shift+Tab — перейти к соседним элементам';

  function renderResult(out, res, opts) {
    out.textContent = '';
    if (res.stopped) { out.appendChild(el('span', 'status', 'Остановлено. Python перезапустится при следующем запуске.')); return; }
    if (res.out) out.appendChild(el('span', 'stdout', res.out.replace(/\n$/, '')));
    if (res.error) {
      var lines = res.error.text.split('\n');
      var why = lines.filter(function (l) { return l.indexOf('Что это значит: ') === 0; })[0];
      var e = el('span', 'error', lines.filter(function (l) { return l !== why; }).join('\n'));
      if (why) e.appendChild(el('span', 'why', why));
      out.appendChild(e);
    }
    if (res.display) {
      var dsp = el('div', 'display');
      if (res.display.html) { dsp.innerHTML = res.display.html; if (res.display.note) dsp.appendChild(el('div', 'df-note', res.display.note)); }
      else dsp.appendChild(el('span', 'repr', res.display.text));
      out.appendChild(dsp);
    }
    (res.figs || []).forEach(function (b64) { var i = el('img'); i.alt = 'График'; i.src = 'data:image/png;base64,' + b64; out.appendChild(i); });
    if (!res.out && !res.error && !res.display && !(res.figs || []).length && !opts.quietEmpty)
      out.appendChild(el('span', 'noout', 'Выполнено, вывода нет. Чтобы увидеть значение, оберните его в print().'));
  }

  function runner(out, getJob, onDone) {
    var busy = false;
    return function () {
      if (busy) return;
      busy = true;
      out.textContent = '';
      var st = el('span', 'status', Py.readyP ? 'Выполняю…' : 'Загружаю Python (первый раз — до 20 секунд)…');
      out.appendChild(st);
      var stop = null, t = null;
      var job = getJob();
      // «дольше обычного» считаем от начала выполнения кода, а не от загрузки Python и библиотек;
      // первый импорт sklearn/scipy/statsmodels сам по себе занимает секунды
      var heavy = /sklearn|scipy|statsmodels|matplotlib/.test((job.setup || '') + job.code + (job.check || ''));
      function arm(ms) {
        if (t) return;
        t = setTimeout(function () {
          stop = btn('Остановить', 'ghost'); stop.style.marginLeft = '10px';
          stop.onclick = function () { Py.stop(); };
          st.textContent = heavy
            ? 'Модель ещё считается — в браузере обучение может занять до минуты. Если ждать дольше — остановите и проверьте циклы. '
            : 'Выполняется дольше обычного — возможно, бесконечный цикл. ';
          st.appendChild(stop);
        }, ms);
      }
      var fallback = setTimeout(function () { arm(0); }, 90000);
      Py.run(job, function (text) {
        if (!stop) st.textContent = text;
        if (text === 'Выполняю…') arm(heavy ? 20000 : 4000);
      }).then(function (res) {
        clearTimeout(fallback);
        clearTimeout(t); busy = false;
        renderResult(out, res, { quietEmpty: !!job.check });
        onDone && onDone(res);
      }, function (err) {
        clearTimeout(t); busy = false;
        clearTimeout(fallback);
        out.textContent = '';
        out.appendChild(el('span', 'error', Py.failed || String(err.message || err)));
      });
    };
  }

  // ---------- живые примеры ----------
  function initCells() {
    $$('.cell').forEach(function (cell) {
      var src = cell.querySelector('.cell-src');
      var original = src.textContent;
      var host = el('div', 'editor');
      cell.replaceChild(host, src);
      var out = el('div', 'out'); out.setAttribute('aria-live', 'polite');
      var files = (LESSON.files || []).concat(cell.dataset.files ? cell.dataset.files.split(',') : []);
      var cm;
      var run = runner(out, function () { return { code: cm.getValue(), files: files }; });
      cm = mountEditor(host, original, { run: run });
      var bar = el('div', 'bar');
      var r = btn('', 'primary'); r.innerHTML = ICON_PLAY + 'Запустить'; r.onclick = run;
      var reset = btn('Вернуть пример', 'ghost'); reset.hidden = true;
      reset.onclick = function () { cm.setValue(original); reset.hidden = true; };
      cm.on('change', function () { reset.hidden = cm.getValue() === original; });
      var steps = btn('По шагам', 'ghost', 'Выполнить построчно и посмотреть переменные на каждом шаге');
      var stepper = el('div', 'stepper'); stepper.hidden = true;
      steps.onclick = function () { stepper.hidden ? openStepper(cm, stepper, files, steps) : closeStepper(cm, stepper, steps); };
      bar.appendChild(r); bar.appendChild(steps); bar.appendChild(reset); bar.appendChild(el('span', 'grow'));
      bar.appendChild(el('span', 'hint-key', 'Пример — меняйте и запускайте'));
      cell.appendChild(bar); cell.appendChild(stepper); cell.appendChild(out);
    });
  }

  // ---------- пошаговое выполнение ----------
  function closeStepper(cm, box, b) {
    box.hidden = true; box.textContent = ''; b.textContent = 'По шагам';
    if (box._line != null) cm.removeLineClass(box._line, 'background', 'cm-step-line');
    box._line = null; cm.setOption('readOnly', false);
    if (box._key) document.removeEventListener('keydown', box._key);
  }
  function openStepper(cm, box, files, b) {
    box.hidden = false; b.textContent = 'Закрыть шаги';
    box.textContent = ''; box.appendChild(el('div', 'status', Py.readyP ? 'Выполняю по шагам…' : 'Загружаю Python…'));
    Py.trace(cm.getValue(), files).then(function (res) {
      if (box.hidden) return;
      if (res.stopped) { closeStepper(cm, box, b); return; }
      var S = res.steps || [];
      box.textContent = '';
      if (!S.length) { box.appendChild(el('div', 'error', (res.error && res.error.text) || 'Нечего показывать.')); return; }
      cm.setOption('readOnly', true);
      var nav = el('div', 'step-nav');
      var first = btn('⏮', 'ghost', 'В начало'), prev = btn('←', '', 'Назад (стрелка влево)'), next = btn('→', 'primary', 'Вперёд (стрелка вправо)'), last = btn('⏭', 'ghost', 'В конец');
      var range = el('input'); range.type = 'range'; range.min = 0; range.max = S.length - 1; range.value = 0; range.setAttribute('aria-label', 'Шаг');
      var label = el('span', 'step-label');
      [first, prev, next, last, range, label].forEach(function (x) { nav.appendChild(x); });
      var info = el('div', 'step-info');
      var vars = el('div', 'step-vars');
      var outBox = el('pre', 'step-out');
      box.appendChild(nav); box.appendChild(info); box.appendChild(vars); box.appendChild(outBox);
      if (res.truncated) box.appendChild(el('div', 'muted small', 'Показаны первые ' + S.length + ' шагов — дальше код не трассируется (возможно, бесконечный цикл).'));
      if (res.error) box.appendChild(el('div', 'error', res.error.text.split('\n').slice(0, 2).join('\n')));
      var i = 0, prevVals = {};
      function show(n) {
        i = Math.max(0, Math.min(S.length - 1, n)); range.value = i;
        var st = S[i];
        if (box._line != null) cm.removeLineClass(box._line, 'background', 'cm-step-line');
        box._line = st.line ? st.line - 1 : null;
        if (box._line != null) { cm.addLineClass(box._line, 'background', 'cm-step-line'); }
        label.textContent = 'Шаг ' + (i + 1) + ' из ' + S.length;
        info.textContent = st.event === 'end' ? (res.error ? 'Программа остановилась с ошибкой.' : 'Программа завершилась. Итоговые значения переменных:')
          : st.event === 'return' ? 'Строка ' + st.line + ': функция возвращает ' + st.ret
          : 'Сейчас выполнится строка ' + st.line + ':  ' + (cm.getLine(st.line - 1) || '').trim();
        // значения на предыдущем шаге — чтобы подсветить изменившиеся
        var before = {};
        if (i > 0) S[i - 1].scopes.forEach(function (sc) { sc.vars.forEach(function (v) { before[sc.name + '.' + v[0]] = v[2]; }); });
        vars.textContent = '';
        st.scopes.forEach(function (sc) {
          var t = el('table', 'step-table');
          var cap = el('caption', '', sc.name === 'программа' ? 'Переменные' : 'Внутри ' + sc.name); t.appendChild(cap);
          if (!sc.vars.length) { var tr0 = el('tr'); tr0.appendChild(el('td', 'muted', 'пока нет')); t.appendChild(tr0); }
          sc.vars.forEach(function (v) {
            var tr = el('tr'); var k = sc.name + '.' + v[0];
            if (i > 0 && before[k] !== v[2]) tr.className = 'changed';
            tr.appendChild(el('td', 'vn', v[0])); tr.appendChild(el('td', 'vv', v[2])); tr.appendChild(el('td', 'vt', v[1]));
            t.appendChild(tr);
          });
          vars.appendChild(t);
        });
        outBox.textContent = st.out ? st.out.replace(/\n$/, '') : '';
        outBox.hidden = !st.out;
        prev.disabled = first.disabled = i === 0; next.disabled = last.disabled = i === S.length - 1;
      }
      first.onclick = function () { show(0); }; prev.onclick = function () { show(i - 1); };
      next.onclick = function () { show(i + 1); }; last.onclick = function () { show(S.length - 1); };
      range.oninput = function () { show(+range.value); };
      box._key = function (e) {
        if (box.hidden || !box.contains(document.activeElement) && document.activeElement !== document.body) return;
        if (e.key === 'ArrowRight') { show(i + 1); e.preventDefault(); } else if (e.key === 'ArrowLeft') { show(i - 1); e.preventDefault(); }
      };
      document.addEventListener('keydown', box._key);
      show(0); next.focus();
    });
  }

  // ---------- «Собери код из строк» ----------
  // Ведёт себя как редактор: getValue / setValue / on('change') / focus — поэтому остальной код задач не меняется.
  function seededShuffle(arr, seed) {
    var a = arr.slice(), h = 0;
    for (var i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
    function rnd() { h = (h * 1103515245 + 12345) >>> 0; return h / 4294967296; }
    for (var j = a.length - 1; j > 0; j--) { var k = Math.floor(rnd() * (j + 1)); var t = a[j]; a[j] = a[k]; a[k] = t; }
    return a;
  }
  function ParsonsEditor(host, solution, seed) {
    var lines = solution.split('\n').filter(function (l) { return l.trim(); }).map(function (l) { return l.trim(); });
    var items = [], listeners = [];
    var box = el('div', 'parsons');
    box.appendChild(el('div', 'parsons-help muted small', 'Расставьте строки по порядку: перетащите или используйте ↑ ↓. Отступ — кнопки ← →.'));
    var ol = el('ol', 'parsons-list'); box.appendChild(ol); host.appendChild(box);
    function fire() { listeners.forEach(function (f) { f(); }); }
    function shuffled() {
      // перемешивание не должно случайно дать рабочую программу: первая и последняя строки эталона уходят со своих мест
      // (иначе, например, две независимые строки в начале просто меняются местами — и задача решена без действий)
      function bad(o) {
        if (o.join('\n') === lines.join('\n')) return true;
        var n = lines.length;
        return n >= 3 && (o[0] === lines[0] || o[n - 1] === lines[n - 1]);
      }
      var order = seededShuffle(lines, seed), tries = 0;
      while (bad(order) && tries++ < 50) order = seededShuffle(lines, seed + tries);
      return order.map(function (t) { return { text: t, ind: 0 }; });
    }
    function render() {
      ol.textContent = '';
      items.forEach(function (it, i) {
        var li = el('li', 'pline'); li.draggable = true; li.dataset.i = i;
        li.style.setProperty('--ind', it.ind);
        var code = el('code', '', it.text);
        var tools = el('span', 'ptools');
        [['↑', -1, 0, 'Выше'], ['↓', 1, 0, 'Ниже'], ['←', 0, -1, 'Меньше отступ'], ['→', 0, 1, 'Больше отступ']].forEach(function (b) {
          var x = el('button', 'pbtn', b[0]); x.type = 'button'; x.title = b[3]; x.setAttribute('aria-label', b[3] + ': ' + it.text);
          x.onclick = function () { move(i, b[1], b[2]); };
          tools.appendChild(x);
        });
        li.appendChild(code); li.appendChild(tools);
        li.addEventListener('dragstart', function (e) { e.dataTransfer.setData('text/plain', String(i)); li.classList.add('drag'); });
        li.addEventListener('dragend', function () { li.classList.remove('drag'); });
        li.addEventListener('dragover', function (e) { e.preventDefault(); li.classList.add('over'); });
        li.addEventListener('dragleave', function () { li.classList.remove('over'); });
        li.addEventListener('drop', function (e) {
          e.preventDefault(); li.classList.remove('over');
          var from = +e.dataTransfer.getData('text/plain'); if (isNaN(from) || from === i) return;
          var it2 = items.splice(from, 1)[0]; items.splice(i, 0, it2); render(); fire();
        });
        ol.appendChild(li);
      });
    }
    function move(i, dy, dx) {
      if (dy) { var j = i + dy; if (j < 0 || j >= items.length) return; var t = items[i]; items[i] = items[j]; items[j] = t; }
      if (dx) items[i].ind = Math.max(0, Math.min(4, items[i].ind + dx));
      render(); fire();
      var btns = $$('.pline', ol)[dy ? i + dy : i]; if (btns) { var bb = $$('.pbtn', btns)[dy < 0 ? 0 : dy > 0 ? 1 : dx < 0 ? 2 : 3]; bb && bb.focus(); }
    }
    var api = {
      getValue: function () { return items.map(function (it) { return '    '.repeat(it.ind) + it.text; }).join('\n'); },
      setValue: function (code) {
        var got = (code || '').split('\n').filter(function (l) { return l.trim(); });
        var same = got.length === lines.length && got.map(function (l) { return l.trim(); }).slice().sort().join('\n') === lines.slice().sort().join('\n');
        items = same ? got.map(function (l) { return { text: l.trim(), ind: Math.round((l.length - l.replace(/^\s+/, '').length) / 4) }; }) : shuffled();
        render(); fire();
      },
      on: function (ev, f) { if (ev === 'change') listeners.push(f); },
      focus: function () { var b = $('.pbtn', ol); b && b.focus(); }
    };
    return api;
  }

  // ---------- «Проверьте себя»: вопрос на понимание, у каждого варианта своё объяснение ----------
  function initQuizzes() {
    var TEST = LESSON.mode === 'test';
    var attempt = TEST ? ((P.state.exam[LESSON.lesson] || {}).n || 1) : 1;
    $$('.quiz-c').forEach(function (q) {
      var key = LESSON.lesson + '#' + q.dataset.q + (attempt > 1 ? '/' + attempt : '');
      var list = $('ul', q); if (!list) return;
      var opts = el('div', 'quiz-opts'), correct = -1, whys = [];
      $$(':scope > li', list).forEach(function (li, i) {
        var why = el('div', 'quiz-why');
        $$(':scope > blockquote', li).forEach(function (bq) { while (bq.firstChild) why.appendChild(bq.firstChild); bq.remove(); });
        var h = li.innerHTML.replace(/^\s*<p>/, '').replace(/<\/p>\s*$/, '').trim(), right = /^\[x\]\s*/.test(h);
        if (right) correct = i;
        var b = el('button', 'qopt'); b.type = 'button'; b.dataset.i = i;
        b.innerHTML = h.replace(/^\[[x ]\]\s*/, '');
        b.onclick = function () { answer(i, true); };
        var wrap = el('div', 'qrow'); wrap.appendChild(b); why.hidden = true; wrap.appendChild(why);
        opts.appendChild(wrap); whys.push(why);
      });
      // порядок вариантов — свой у каждого вопроса (и у каждой попытки теста), но стабильный между заходами;
      // номер варианта в сохранённом ответе — исходный, поэтому перестановка ничего не ломает
      seededShuffle($$(':scope > .qrow', opts), key).forEach(function (row) { opts.appendChild(row); });
      list.replaceWith(opts);
      var res = el('div', 'predict-res'); opts.after(res);
      function answer(i, fresh) {
        $$('.qopt', opts).forEach(function (b) {
          var j = +b.dataset.i;
          b.disabled = true;
          b.classList.toggle('right', j === correct); b.classList.toggle('wrong', j === i && i !== correct); b.classList.toggle('picked', j === i);
        });
        whys.forEach(function (w, j) { w.hidden = false; w.classList.toggle('is-right', j === correct); });
        res.className = 'predict-res ' + (i === correct ? 'ok' : 'fail');
        res.textContent = i === correct ? 'Верно! Ниже — почему остальные варианты не подходят.' : 'Не совсем. Правильный вариант подсвечен, под каждым — объяснение.';
        if (fresh && !P.state.quiz[key]) { P.state.quiz[key] = { ok: i === correct, a: i, t: u.now() }; P.save(); }
        q.dataset.answered = i === correct ? 'ok' : 'fail';
        if (TEST) testResult();
      }
      var saved = P.state.quiz[key];
      if (saved) answer(saved.a, false);
    });
    if (TEST) testResult();

    // итог теста главы: сколько верно, какие уроки повторить, новая попытка
    function testResult() {
      var box = $('#test-result'); if (!box) return;
      var qs = $$('.quiz-c'), done = qs.filter(function (x) { return x.dataset.answered; });
      box.textContent = '';
      if (done.length < qs.length) {
        box.appendChild(el('p', 'muted', 'Отвечено ' + done.length + ' из ' + qs.length + '. Итог появится, когда ответите на все вопросы.'));
        return;
      }
      var ok = qs.filter(function (x) { return x.dataset.answered === 'ok'; }).length, pct = Math.round(100 * ok / qs.length);
      var head = el('div', 'exam-score ' + (pct >= 80 ? 'good' : pct >= 50 ? 'mid' : 'low'));
      head.appendChild(el('b', '', ok + ' из ' + qs.length));
      head.appendChild(el('span', '', pct >= 80 ? ' — глава усвоена. Можно идти дальше.' : pct >= 50 ? ' — неплохо, но стоит повторить темы ниже.' : ' — лучше вернуться к урокам ниже, а потом пройти тест ещё раз.'));
      box.appendChild(head);
      var miss = {};
      qs.forEach(function (x) {
        if (x.dataset.answered === 'ok' || !x.dataset.lesson) return;
        (miss[x.dataset.lesson] = miss[x.dataset.lesson] || []).push(x.dataset.q.replace('c', ''));
      });
      var ids = Object.keys(miss);
      if (ids.length) {
        box.appendChild(el('p', '', 'Повторить:'));
        var ul = el('ul', 'exam-miss');
        ids.forEach(function (id) {
          var e = D.lessonEntry(LESSON.lesson.split('/')[0] + '/' + id), li = el('li');
          var a = el('a', '', e ? 'Урок ' + e.ls.n + '. ' + e.ls.title : id); a.href = id + '.html';
          li.appendChild(a); li.appendChild(el('span', 'muted', ' — вопрос ' + miss[id].join(', ')));
          ul.appendChild(li);
        });
        box.appendChild(ul);
      }
      var again = btn('Пройти тест заново', 'ghost');
      again.onclick = function () {
        if (!again.dataset.armed) { again.dataset.armed = '1'; again.textContent = 'Начать новую попытку? Ответы скроются'; return; }
        P.state.exam[LESSON.lesson] = { n: attempt + 1, t: u.now(), best: Math.max(pct, (P.state.exam[LESSON.lesson] || {}).best || 0) };
        P.save(); if (P.push) P.push();
        setTimeout(function () { location.hash = ''; location.reload(); }, 300);
      };
      box.appendChild(again);
    }
  }

  // ---------- «Предскажите вывод» ----------
  function initPredicts() {
    $$('.predict').forEach(function (q) {
      var key = LESSON.lesson + '#' + q.dataset.q;
      var pre = $('pre', q), list = $('ul', q);
      var why = $$('p', q).filter(function (p) { return /^Почему/.test(p.textContent.trim()); });
      why.forEach(function (p) { p.classList.add('predict-why'); p.hidden = true; });
      if (!list) return;
      var opts = el('div', 'predict-opts'), correct = -1;
      $$('li', list).forEach(function (li, i) {
        var h = li.innerHTML.trim(), right = /^\[x\]\s*/.test(h);
        if (right) correct = i;
        var b = el('button', 'popt'); b.type = 'button';
        b.innerHTML = h.replace(/^\[x\]\s*/, '').replace(/ \| /g, '<br>');
        b.onclick = function () { answer(i, true); };
        opts.appendChild(b);
      });
      list.replaceWith(opts);
      var res = el('div', 'predict-res'), out = el('div', 'out');
      var runB = btn('', 'ghost'); runB.innerHTML = ICON_PLAY + 'Запустить и проверить'; runB.hidden = true;
      runB.onclick = runner(out, function () { return { code: pre.textContent, files: LESSON.files }; });
      opts.after(res); q.appendChild(runB); q.appendChild(out);
      function answer(i, fresh) {
        var bs = $$('.popt', opts);
        bs.forEach(function (b, j) { b.disabled = true; b.classList.toggle('right', j === correct); b.classList.toggle('wrong', j === i && i !== correct); b.classList.toggle('picked', j === i); });
        res.className = 'predict-res ' + (i === correct ? 'ok' : 'fail');
        res.textContent = i === correct ? 'Верно!' : 'Не совсем — правильный вариант подсвечен.';
        why.forEach(function (p) { p.hidden = false; });
        runB.hidden = false;
        if (fresh && !P.state.quiz[key]) { P.state.quiz[key] = { ok: i === correct, a: i, t: u.now() }; P.save(); }
      }
      var saved = P.state.quiz[key];
      if (saved) answer(saved.a, false);
    });
  }

  // ---------- задачи ----------
  function askPrompt(task, code, outText) {
    return [
      'Я прохожу курс «Data Science для аналитиков» (Python, уровень новичка).',
      'Урок: «' + LESSON.title + '». Задача: «' + task.title + '».',
      'Условие:', ($('#task-' + task.id + ' .task-text') || {}).innerText || '',
      'Мой код:', '```python', code, '```',
      outText ? 'Что получилось:\n' + outText : '',
      'Помоги разобраться: объясни, что не так, и дай подсказку. Пожалуйста, не пиши готовое решение.'
    ].filter(Boolean).join('\n');
  }

  var cards = {};   // id → {render, cm}

  function initTasks() {
    var tasks = LESSON.tasks;
    tasks.forEach(function (t, idx) {
      var k = key(t.id);
      var card = $('#task-' + t.id), ui = $('.task-ui', card), head = $('.task-head', card);
      var saved = (P.task(k) || {}).code;
      var host = el('div', 'editor');
      ui.appendChild(host);   // CodeMirror должен создаваться в документе, иначе не отрисует строки до клика
      var out = el('div', 'out'); out.setAttribute('aria-live', 'polite');
      var verdict = el('div', 'verdict'); verdict.setAttribute('aria-live', 'polite');
      var extras = el('div', 'extras');
      var badge = el('span', 'task-badge');
      head.insertBefore(badge, $('.task-state', head));
      var hintsShown = 0, cm;

      function addExtra(title, html, cls) {
        var d = el('div', 'extra prose ' + (cls || ''));
        d.appendChild(el('div', 'extra-title', title));
        var body = el('div'); body.innerHTML = html; d.appendChild(body);
        extras.appendChild(d); return d;
      }
      function showHint() {
        if (hintsShown >= t.hints.length) return;
        addExtra('Подсказка ' + (hintsShown + 1), t.hints[hintsShown]); hintsShown++; hintLabel();
      }
      function showSolution() {
        if ($('.x-sol', extras)) return;
        var d = addExtra('Решение', '', 'x-sol');
        var pre = el('pre', 'static code'); pre.appendChild(el('code', '', t.solution)); d.lastChild.appendChild(pre);
        if (t.explain && !$('.x-explain', extras)) addExtra('Разбор', t.explain, 'x-explain');
        bSol.disabled = true; bSol.textContent = 'Решение открыто';
      }

      var run = runner(out, function () { saveCode(); return { code: cm.getValue(), setup: t.setup, files: LESSON.files }; });
      var check = runner(out, function () {
        saveCode();
        return { code: cm.getValue(), setup: t.setup, check: t.check, files: LESSON.files };
      }, function (res) {
        if (res.stopped || !res.check) return;
        var e = P.task(k) || {};
        P.updateTask(k, { att: (e.att || 0) + 1 });
        verdict.textContent = '';
        if (res.check.passed) {
          var wasSolved = !!e.solved, wasDone = progressNow().done;
          var after = EXAM ? P.updateTask(k, { solved: e.solved || u.now(), help: 0, lastHelp: 0 }) : P.onSolved(k);
          if (EXAM) { verdict.className = 'verdict ok'; verdict.appendChild(el('span', '', 'Верно.')); render(); updateProgress(); renderExam(); return; }
          verdict.className = 'verdict ok';
          var msg = after.lastHelp === 2 ? 'Верно. Задача засчитана, но решение было открыто — она вернётся на повторение завтра.'
            : after.lastHelp === 1 ? 'Верно! С подсказкой — через пару дней предложим решить её ещё раз.'
            : wasSolved && after.due === null && e.due ? 'Верно, и без подсказок — задача усвоена.'
            : ['Верно!', 'Отлично, задача решена.', 'Да, так и есть.'][idx % 3];
          verdict.appendChild(el('span', '', msg));
          if (t.explain && !$('.x-explain', extras)) addExtra('Разбор', t.explain, 'x-explain');
          var next = tasks[idx + 1];
          if (next) {
            // ссылка, а не кнопка: общий обработчик якорей переключает «страницу» задачи
            // в режиме «по разделам» и прокручивает к ней в режиме «весь урок»
            var go = el('a', 'btn primary', 'Следующая задача →'); go.href = '#task-' + next.id;
            go.addEventListener('click', function () { setTimeout(function () { var n = $('#task-' + next.id), c = n && $('.CodeMirror', n); c && c.CodeMirror.focus(); }, 400); });
            verdict.appendChild(go);
          }
          render();
          updateProgress(wasDone);
        } else {
          verdict.className = 'verdict fail';
          verdict.appendChild(el('b', '', 'Пока не так. '));
          if (!examOpen()) verdict.appendChild(el('span', '', res.check.msg));
          else verdict.appendChild(el('span', '', 'Проверьте условие и попробуйте ещё раз.'));
          if ((e.att || 0) + 1 >= 2 && hintsShown < t.hints.length) verdict.appendChild(el('span', 'muted', ' Возьмите подсказку — это нормально.'));
        }
      });

      var isParsons = card.dataset.kind === 'parsons';
      if (isParsons) { cm = ParsonsEditor(host, t.parsons, LESSON.lesson + '/' + t.id); cm.setValue(saved || ''); }
      else cm = mountEditor(host, saved != null ? saved : t.starter, { run: run, check: check });
      var saveT;
      function saveCode() {
        clearTimeout(saveT);
        var e = P.task(k) || {};
        if (e.code !== cm.getValue()) P.updateTask(k, { code: cm.getValue() });
      }
      cm.on('change', function () {
        clearTimeout(saveT);
        saveT = setTimeout(saveCode, isParsons ? 0 : 600);
      });
      P.flushers.push(saveCode);

      var bar = el('div', 'bar');
      var bRun = btn('', '', 'Запустить без проверки'); bRun.innerHTML = ICON_PLAY + 'Запустить'; bRun.onclick = run;
      var bCheck = btn('Проверить', 'primary'); bCheck.onclick = check;
      var bHint = btn('', 'ghost');
      function hintLabel() {
        bHint.textContent = t.hints.length ? (hintsShown < t.hints.length ? 'Подсказка ' + (hintsShown + 1) + ' из ' + t.hints.length : 'Подсказки открыты') : '';
        bHint.hidden = !t.hints.length; bHint.disabled = hintsShown >= t.hints.length;
      }
      bHint.onclick = function () {
        var e = P.task(k) || {};
        if (hintsShown >= (e.ah || 0)) P.updateTask(k, { ah: hintsShown + 1, hints: Math.max(e.hints || 0, hintsShown + 1) });
        showHint();
      };
      var bSol = btn('Решение', 'ghost'), armed = false;
      bSol.onclick = function () {
        var e = P.task(k) || {};
        var ready = (e.att || 0) > 0 || hintsShown >= t.hints.length || (e.solved && !e.retry);
        if (!ready && !armed) { armed = true; bSol.textContent = 'Точно показать?'; toast('Сначала попробуйте проверить или возьмите подсказку. Нажмите ещё раз, чтобы открыть решение.', 4000); return; }
        if (!(e.solved && !e.retry)) P.updateTask(k, { as: true });
        showSolution();
      };
      var bAsk = btn('Спросить', 'ghost', 'Скопировать вопрос для ИИ-репетитора');
      bAsk.onclick = function () { u.copyText(askPrompt(t, cm.getValue(), out.innerText)).then(function () { toast('Вопрос скопирован — вставьте его в чат с ИИ.'); }); };
      var bReset = btn('↺', 'ghost', 'Вернуть заготовку');
      bReset.onclick = function () {
        if (!isParsons && cm.getValue() === t.starter) return;
        if (bReset.dataset.armed) { cm.setValue(t.starter); delete bReset.dataset.armed; bReset.textContent = '↺'; return; }
        bReset.dataset.armed = '1'; bReset.textContent = 'Стереть мой код?';
        setTimeout(function () { delete bReset.dataset.armed; bReset.textContent = '↺'; }, 3000);
      };
      var bSteps = btn('По шагам', 'ghost', 'Выполнить свой код построчно и посмотреть переменные');
      if (isParsons) bSteps.hidden = true;
      var stepper = el('div', 'stepper'); stepper.hidden = true;
      bSteps.onclick = function () { stepper.hidden ? openStepper(cm, stepper, LESSON.files, bSteps) : closeStepper(cm, stepper, bSteps); };
      [bRun, bCheck, el('span', 'grow'), bSteps, bHint, bSol, bAsk, bReset].forEach(function (b) { bar.appendChild(b); });

      // полоса для решённой задачи: перерешать / в повтор
      var solvedBar = el('div', 'solved-bar');
      var bRetry = btn('Перерешать с нуля', 'ghost', 'Стереть код и решить заново — без подсказок');
      var bFlag = btn('', 'ghost');
      bRetry.onclick = function () {
        if (!bRetry.dataset.armed) {
          bRetry.dataset.armed = '1'; bRetry.textContent = 'Стереть код и начать заново?';
          setTimeout(function () { delete bRetry.dataset.armed; bRetry.textContent = 'Перерешать с нуля'; }, 3500);
          return;
        }
        delete bRetry.dataset.armed; bRetry.textContent = 'Перерешать с нуля';
        P.updateTask(k, { retry: true, ah: 0, as: false, code: t.starter });
        cm.setValue(t.starter); extras.textContent = ''; verdict.textContent = ''; verdict.className = 'verdict'; out.textContent = '';
        hintsShown = 0; hintLabel(); bSol.disabled = false; bSol.textContent = 'Решение'; armed = false;
        render(); cm.focus();
      };
      bFlag.onclick = function () {
        var e = P.task(k) || {};
        if (P.isDue(e)) { P.updateTask(k, { due: null }); toast('Убрано из повторения.'); }
        else { P.updateTask(k, { due: u.dayStr(), ivl: e.ivl || 1 }); toast('Задача в списке «Повторить» на главной.'); }
        render();
      };
      solvedBar.appendChild(el('span', 'solved-text'));
      solvedBar.appendChild(el('span', 'grow'));
      solvedBar.appendChild(bRetry); solvedBar.appendChild(bFlag);

      ui.appendChild(host); ui.appendChild(bar); ui.appendChild(stepper); ui.appendChild(solvedBar); ui.appendChild(out); ui.appendChild(verdict); ui.appendChild(extras);

      function render() {
        var e = P.task(k) || {};
        var solved = !!e.solved;
        if (solved) card.dataset.solved = ''; else delete card.dataset.solved;
        card.dataset.help = solved ? String(e.help || 0) : '';
        card.toggleAttribute('data-retry', !!e.retry);
        var due = P.isDue(e);
        badge.textContent = e.retry ? 'перерешиваю' : due ? 'повторить' : solved && e.help === 2 ? 'по решению' : solved && e.help === 1 ? 'с подсказкой' : '';
        badge.className = 'task-badge' + (due || e.retry ? ' due' : '');
        solvedBar.hidden = !solved || !!e.retry || EXAM;
        [bHint, bSol, bAsk].forEach(function (b) { if (examOpen()) b.hidden = true; });
        if (!examOpen()) hintLabel();
        var when = e.solved ? new Date(e.solved).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }) : '';
        $('.solved-text', solvedBar).textContent = solved ? 'Решено ' + when + (e.reviews ? ' · повторений: ' + e.reviews : '') +
          (e.due && !due ? ' · повтор ' + new Date(e.due + 'T00:00').toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }) : '') : '';
        bFlag.textContent = due ? 'Убрать из повтора' : 'В повтор';
      }
      // восстановить открытые в этой попытке подсказки и решение
      var e0 = P.task(k) || {};
      for (var i = 0; i < Math.min(e0.ah || 0, t.hints.length); i++) showHint();
      if (e0.as) showSolution();
      hintLabel(); render();
      cards[t.id] = { render: render, cm: cm };
    });
  }

  // ---------- прогресс урока и главы ----------
  var lastComplete = null;   // null — ещё не считали (без поздравления при открытии урока)
  function progressNow() { return D.lessonProgress(prefix(), LESSON.tasks); }
  function updateProgress(wasDone) {
    var p = progressNow();
    var m = $('#lesson-meter');
    var theory = LESSON.mode === 'lesson' && p.secs;
    if (m) {
      var parts = (theory ? 'Теория ' + p.read + ' из ' + p.secs + ' · задачи ' : '') + p.done + ' из ' + p.total + (theory ? '' : ' задач');
      $('i', m).style.width = ((p.total + (theory ? p.secs : 0)) ? 100 * (p.done + (theory ? p.read : 0)) / (p.total + (theory ? p.secs : 0)) : 0) + '%';
      $('span', m).textContent = parts + ((theory ? p.complete : p.done >= p.total) ? ' — урок пройден' : '');
    }
    var e = D.lessonEntry(LESSON.lesson);
    if (e) {
      var chDone = 0, chTotal = 0;
      e.ch.lessons.forEach(function (ls) { var q = D.lessonProgress(e.ch.id + '/' + ls.id, ls.tasks); chDone += q.done + q.read; chTotal += q.total + q.secs; });
      var cm = $('#chapter-meter i'); if (cm) cm.style.width = (chTotal ? 100 * chDone / chTotal : 0) + '%';
    }
    D.markDots(document);
    var next = $('.pager .next');
    if (next) next.classList.toggle('ready', p.done >= p.total);
    var nowComplete = LESSON.mode === 'lesson' ? p.complete : p.done >= p.total;
    if (lastComplete === false && nowComplete && (p.total || p.secs)) toast('Урок пройден! Задачи со звёздочкой — по желанию.', 3500);
    lastComplete = nowComplete;
  }

  // ---------- заметки ----------
  function initNotes() {
    var ta = $('#notes-text'); if (!ta) return;
    var stateEl = $('#notes-state');
    function fit() { ta.style.height = 'auto'; ta.style.height = Math.max(120, ta.scrollHeight + 4) + 'px'; }
    function load() { var n = P.state.notes[LESSON.lesson]; if (document.activeElement !== ta) { ta.value = n ? n.text : ''; fit(); } }
    load();
    var tmr;
    ta.addEventListener('input', function () {
      fit(); stateEl.textContent = '…';
      clearTimeout(tmr);
      tmr = setTimeout(function () {
        P.state.notes[LESSON.lesson] = { text: ta.value, t: u.now() };
        P.save(); stateEl.textContent = 'Сохранено';
      }, 600);
    });
    P.onChange(load);
  }

  // ---------- оглавление и «где остановился» ----------
  function initToc() {
    var links = $$('.toc a');
    var map = {}; links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var sections = Object.keys(map).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var spots = sections.concat($$('.task')).sort(function (a, b) { return a.compareDocumentPosition(b) & 2 ? 1 : -1; });
    var lastSaved = '', saveT;
    function update() {
      var curSec = sections[0], spot = null;
      sections.forEach(function (s) { if (s.getBoundingClientRect().top < 140) curSec = s; });
      spots.forEach(function (s) { if (s.getBoundingClientRect().top < 160) spot = s; });
      links.forEach(function (a) { a.classList.toggle('active', curSec && map[curSec.id] === a); });
      if (Pages) return;   // в режиме разделов место сохраняет переход по разделам
      var anchor = spot && window.scrollY > 200 ? spot.id : '';
      if (anchor !== lastSaved) {
        lastSaved = anchor; clearTimeout(saveT);
        saveT = setTimeout(function () { P.state.last = { lesson: LESSON.lesson, anchor: anchor, t: u.now() }; P.save(); }, 1200);
      }
    }
    var raf; window.addEventListener('scroll', function () { cancelAnimationFrame(raf); raf = requestAnimationFrame(update); }, { passive: true });
    update();
  }


  // ---------- «Понятно объяснено?» ----------
  function initFeedback() {
    $$('.fb').forEach(function (box) {
      var k = LESSON.lesson + '#' + box.dataset.sec;
      var note = el('div', 'fb-more'); note.hidden = true;
      var inp = el('input'); inp.type = 'text'; inp.placeholder = 'Что именно непонятно? (необязательно — поможет поправить урок)';
      var ask = el('button', 'linklike', 'спросить ИИ-репетитора'); ask.type = 'button';
      note.appendChild(inp); note.appendChild(el('span', 'muted small', ' или ')); note.appendChild(ask);
      box.appendChild(note);
      var heading = $('#' + box.dataset.sec);
      ask.onclick = function () {
        u.copyText('Я прохожу курс «Data Science для аналитиков», урок «' + LESSON.title + '», раздел «' + (heading ? heading.textContent : '') + '». ' +
          'Мне непонятно: ' + (inp.value || '…') + '\nОбъясни простыми словами, с маленьким примером на Python.').then(function () { toast('Вопрос скопирован.'); });
      };
      function show() {
        var f = P.state.fb[k];
        $$('.fb-btn', box).forEach(function (b) { b.classList.toggle('on', !!f && String(f.v) === b.dataset.v); });
        note.hidden = !(f && f.v < 0);
        if (f && f.c && document.activeElement !== inp) inp.value = f.c;
      }
      $$('.fb-btn', box).forEach(function (b) {
        b.onclick = function () {
          var f = P.state.fb[k] || {};
          P.state.fb[k] = { v: +b.dataset.v, c: f.c || '', h: heading ? heading.textContent : '', t: u.now() }; P.save(); show();
          if (+b.dataset.v < 0) inp.focus(); else toast('Спасибо!');
        };
      });
      var tmr;
      inp.addEventListener('input', function () {
        clearTimeout(tmr);
        tmr = setTimeout(function () { P.state.fb[k] = { v: -1, c: inp.value, h: heading ? heading.textContent : '', t: u.now() }; P.save(); }, 600);
      });
      show();
    });
  }

  // ---------- контрольная ----------
  function renderExam() {
    var box = $('#exam-finish'); if (!EXAM || !box) return;
    var st = examState(), tasks = LESSON.tasks;
    var solved = tasks.filter(function (t) { return P.isSolved(key(t.id)); });
    box.textContent = '';
    if (!st.done) {
      box.appendChild(el('p', '', 'Решено ' + solved.length + ' из ' + tasks.length + '. Нерешённые задачи засчитаются как ошибки.'));
      var fin = btn('Завершить контрольную', 'primary');
      fin.onclick = function () {
        if (!fin.dataset.armed && solved.length < tasks.length) { fin.dataset.armed = '1'; fin.textContent = 'Точно завершить? Решено не всё'; return; }
        var best = Math.max(st.best || 0, Math.round(100 * solved.length / tasks.length));
        P.state.exam[LESSON.lesson] = { n: st.n || 1, done: true, solved: solved.length, total: tasks.length,
          score: Math.round(100 * solved.length / tasks.length), best: best, t: u.now(), history: (st.history || []).concat([{ n: st.n || 1, score: Math.round(100 * solved.length / tasks.length), t: u.now() }]) };
        P.save(); P.push();
        setTimeout(function () { location.hash = 'exam-finish'; location.reload(); }, 300);
      };
      box.appendChild(fin);
      return;
    }
    var score = st.score;
    var head = el('div', 'exam-score ' + (score >= 80 ? 'good' : score >= 50 ? 'mid' : 'low'));
    head.innerHTML = '<b>' + score + '%</b><span>решено ' + st.solved + ' из ' + st.total + (st.history && st.history.length > 1 ? ' · лучший результат ' + st.best + '%' : '') + '</span>';
    box.appendChild(head);
    box.appendChild(el('p', '', score >= 80 ? 'Отлично: можно идти дальше.' : score >= 50 ? 'Неплохо. Перед тем как идти дальше, повторите темы ниже.' : 'Стоит вернуться к урокам ниже и пройти контрольную ещё раз.'));
    var miss = tasks.filter(function (t) { return !P.isSolved(key(t.id)); });
    if (miss.length) {
      var byTopic = {};
      miss.forEach(function (t) { var tp = (LESSON.topics || {})[t.id] || ''; (byTopic[tp] = byTopic[tp] || []).push(t); });
      box.appendChild(el('h3', '', 'Что повторить'));
      var ul = el('ul', 'exam-miss');
      Object.keys(byTopic).forEach(function (tp) {
        var e = D.lessonEntry(LESSON.lesson.split('/')[0] + '/' + tp);
        var li = el('li');
        li.innerHTML = (e ? '<a href="' + e.ls.id + '.html">Урок ' + e.ls.n + '. ' + u.esc(e.ls.title) + '</a>' : 'Разное') + ' — ' +
          byTopic[tp].map(function (t) { return '<a href="#task-' + t.id + '">«' + u.esc(t.title) + '»</a>'; }).join(', ');
        ul.appendChild(li);
      });
      box.appendChild(ul);
    }
    box.appendChild(el('p', 'muted small', 'Подсказки и решения теперь открыты в каждой задаче.'));
    var again = btn('Пройти заново', '');
    again.onclick = function () {
      if (!again.dataset.armed) { again.dataset.armed = '1'; again.textContent = 'Начать новую попытку? Код задач очистится'; return; }
      P.state.exam[LESSON.lesson] = { n: (st.n || 1) + 1, done: false, best: st.best, history: st.history || [], t: u.now() };
      P.save(); P.push();
      setTimeout(function () { location.hash = ''; location.reload(); }, 300);
    };
    box.appendChild(again);
  }


  // ---------- урок по разделам: слева — разделы и задачи урока, по центру — один раздел ----------
  var Pages = null;
  function initPaged() {
    if (LESSON.mode !== 'lesson') return;
    var main = $('#main'), theory = $('.theory', main), practice = $('#practice'), side = $('#sidebar');
    if (!main || !theory || !side) return;
    var pages = [], byId = {}, firstTask = null, cur = null;
    function add(id, title, kind, extra) { var pg = { id: id, title: title, kind: kind, extra: extra || {} }; pages.push(pg); byId[id] = pg; return pg; }
    function clean(t) { return (t || '').replace(/[¶#]\s*$/, '').trim(); }
    // теория: страница = раздел h2; то, что до первого h2, — в первый раздел
    var pg = null, pre = [];
    Array.prototype.slice.call(theory.children).forEach(function (n) {
      if (n.tagName === 'H2') { pg = add(n.id || ('sec' + pages.length), clean(n.textContent), 'theory'); if (!n.id) n.id = pg.id; pre.forEach(function (x) { x.dataset.pg = pg.id; }); pre = []; }
      if (pg) n.dataset.pg = pg.id; else pre.push(n);
    });
    if (pre.length) { pg = add('theory', 'Теория', 'theory'); pre.forEach(function (x) { x.dataset.pg = pg.id; }); }
    // практика: страница = задача; заголовок и легенда — над каждой задачей
    if (practice) {
      practice.dataset.pg = '@practice';
      $$('.task', practice).forEach(function (t, i) {
        var title = $('.task-title', t), lvl = t.dataset.level;
        var p = add(t.id, clean(title ? title.textContent : 'Задача ' + (i + 1)), 'task', { task: t.dataset.task, level: lvl, n: i + 1 });
        t.dataset.pg = p.id; if (!firstTask) firstTask = p.id;
      });
    }
    var recap = $('#recap'), notes = $('#notes');
    if (recap || notes) { var r = add('recap', 'Итоги и заметки', 'recap'); [recap, notes].forEach(function (x) { if (x) x.dataset.pg = r.id; }); }
    if (pages.length < 2) return;

    // левая панель: разделы урока; дерево курса — по кнопке
    var course = el('div', 'side-course');
    while (side.children.length > 1) course.appendChild(side.children[1]);
    var nav = el('div', 'lnav');
    var toCourse = el('button', 'linklike lnav-switch', 'Все главы курса →'); toCourse.type = 'button';
    var toLesson = el('button', 'linklike lnav-switch', '← Разделы урока'); toLesson.type = 'button';
    course.insertBefore(toLesson, course.firstChild);
    nav.appendChild(el('div', 'lnav-title', LESSON.title));
    var list = el('ol', 'lnav-list'), links = {};
    function item(p, parent, numText) {
      var li = el('li'), a = el('a'); a.href = '#' + p.id; a.dataset.pg = p.id;
      a.appendChild(el('span', 'dot')); a.appendChild(el('span', 'num', numText)); a.appendChild(el('span', 't', p.title));
      if (p.kind === 'task' && p.extra.level === 'star') { var tag = el('span', 'lnav-star', '★'); tag.title = 'со звёздочкой — по желанию'; a.appendChild(tag); }
      li.appendChild(a); parent.appendChild(li); links[p.id] = a;
    }
    var th = 0, taskBox = null;
    pages.forEach(function (p) {
      if (p.kind === 'theory') item(p, list, String(++th));
      else if (p.kind === 'task') {
        if (!taskBox) { var li = el('li', 'lnav-group'); li.appendChild(el('div', 'lnav-gt', 'Практика')); taskBox = el('ol', 'lnav-list lnav-tasks'); li.appendChild(taskBox); list.appendChild(li); }
        item(p, taskBox, String(p.extra.n));
      } else item(p, list, '✓');
    });
    nav.appendChild(list);
    var one = el('button', 'linklike lnav-one'); one.type = 'button';
    nav.appendChild(one); nav.appendChild(toCourse);
    side.appendChild(nav); side.appendChild(course);
    function showCourse(on) { document.body.classList.toggle('side-course-on', on); }
    toCourse.onclick = function () {
      showCourse(true);
      var curA = $('.side-course a[aria-current]', side);
      side.scrollTop = curA ? Math.max(0, curA.offsetTop - side.clientHeight / 3) : 0;
    };
    toLesson.onclick = function () { showCourse(false); };

    // нижняя навигация между разделами
    var secPager = el('nav', 'sec-pager'), lessonPager = $('.pager', main);
    main.insertBefore(secPager, lessonPager || null);

    var onePage = false;
    try { onePage = localStorage.getItem('dsc-onepage') === '1'; } catch (e) { /* без хранилища — по разделам */ }
    function applyMode() {
      main.classList.toggle('paged', !onePage);
      one.textContent = onePage ? 'Показывать по разделам' : 'Весь урок на одной странице';
      if (!onePage && cur) show(cur.id);
      else $$('[data-pg]', main).forEach(function (n) { n.classList.add('pg-on'); });
      refreshEditors(main);
    }
    one.onclick = function () {
      onePage = !onePage;
      try { localStorage.setItem('dsc-onepage', onePage ? '1' : '0'); } catch (e) { /* не страшно */ }
      applyMode(); go(cur ? cur.id : pages[0].id, null, true);
    };

    function refreshEditors(root) { $$('.CodeMirror', root).forEach(function (c) { if (c.CodeMirror) c.CodeMirror.refresh(); }); }
    function show(id) {
      var p = byId[id] || pages[0]; cur = p;
      if (!onePage) {
        $$('[data-pg]', main).forEach(function (n) {
          var on = n.dataset.pg === p.id || (n.dataset.pg === '@practice' && p.kind === 'task');
          n.classList.toggle('pg-on', on);
        });
      }
      main.classList.toggle('pg-rest', !onePage && p !== pages[0]);
      Object.keys(links).forEach(function (k) { if (k === p.id) links[k].setAttribute('aria-current', 'step'); else links[k].removeAttribute('aria-current'); });
      var i = pages.indexOf(p), prev = pages[i - 1], next = pages[i + 1];
      secPager.textContent = ''; secPager.hidden = onePage;
      if (prev) { var a = el('a', 'prev'); a.href = '#' + prev.id; a.appendChild(el('span', 'pl', '← Назад')); a.appendChild(el('span', 'pt', prev.title)); secPager.appendChild(a); }
      else secPager.appendChild(el('span'));
      if (next) { var b = el('a', 'next'); b.href = '#' + next.id; b.appendChild(el('span', 'pl', (next.kind === 'task' && p.kind !== 'task' ? 'К задачам' : 'Дальше') + ' →')); b.appendChild(el('span', 'pt', next.title)); secPager.appendChild(b); }
      if (lessonPager) lessonPager.hidden = !onePage && !!next;
      if (p.kind === 'recap') markRecap();
      if (!onePage) setTimeout(function () { refreshEditors(main); }, 0);
    }
    function pageOf(node) {
      var n = node && node.closest ? node.closest('[data-pg]') : null; if (!n) return null;
      if (n.dataset.pg === '@practice') { var t = node.closest('.task'); return t ? t.dataset.pg : firstTask; }
      return n.dataset.pg;
    }
    function go(target, anchorEl, replace) {
      var id = byId[target] ? target : pageOf(anchorEl || document.getElementById(target));
      if (!id) return false;
      show(id);
      var h = '#' + (anchorEl && anchorEl.id && !byId[anchorEl.id] ? anchorEl.id : id);
      if (location.hash !== h) { if (replace) history.replaceState(null, '', h); else history.pushState(null, '', h); }
      if (anchorEl && !byId[anchorEl.id]) setTimeout(function () { anchorEl.scrollIntoView(); }, 30);
      else if (onePage) { var e = document.getElementById(id); if (e) e.scrollIntoView(); }
      else window.scrollTo(0, 0);
      document.body.classList.remove('menu-open'); showCourse(false);
      if (P.state) { P.state.last = { lesson: LESSON.lesson, anchor: id === pages[0].id ? '' : id, t: u.now() }; P.save(); }
      return true;
    }
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href*="#"]');
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
      var url = new URL(a.getAttribute('href'), location.href);
      if (url.pathname !== location.pathname || !url.hash) return;
      var id = decodeURIComponent(url.hash.slice(1)), node = document.getElementById(id);
      if (!byId[id] && !node) return;
      if (go(id, byId[id] ? null : node)) e.preventDefault();
    });
    window.addEventListener('popstate', function () {
      var id = decodeURIComponent(location.hash.slice(1));
      if (!id) return show(pages[0].id);
      if (byId[id]) { show(id); window.scrollTo(0, 0); } else { var n = document.getElementById(id); var pid = pageOf(n); if (pid) { show(pid); n.scrollIntoView(); } }
    });
    // старт: якорь из адреса или первый раздел
    var h0 = decodeURIComponent(location.hash.slice(1)), n0 = h0 && document.getElementById(h0);
    show((byId[h0] && h0) || (n0 && pageOf(n0)) || pages[0].id);
    document.body.classList.add('has-lnav');
    applyMode();
    // панель могла быть прокручена к уроку в дереве курса — показать разделы урока с начала
    side.scrollTop = 0;
    if (links[cur.id] && links[cur.id].getBoundingClientRect().bottom > window.innerHeight) links[cur.id].scrollIntoView({ block: 'center' });

    // ---- отметка «раздел прочитан»: дошли до конца раздела и ответили на «Проверьте себя» в нём ----
    var endSeen = {};
    function quizOk(pid) {
      return $$('.quiz-c', main).filter(function (q) { return pageOf(q) === pid; })
        .every(function (q) { return P.state && P.state.quiz[LESSON.lesson + '#' + q.dataset.q]; });
    }
    function tryRead(pid) {
      var p = byId[pid]; if (!p || p.kind !== 'theory' || !P.state || !P.state.read) return;
      var k = LESSON.lesson + '#' + pid;
      if (P.state.read[k] || !endSeen[pid] || !quizOk(pid)) return;
      P.state.read[k] = { t: u.now() }; P.save(); updateProgress(); marks();
    }
    // «Итоги и заметки» — отметка «просмотрено», как только страницу открыли (или прокрутили до неё)
    function markRecap() {
      if (!P.state) return;
      P.state.read = P.state.read || {};
      var k = LESSON.lesson + '#recap';
      if (P.state.read[k]) return;
      P.state.read[k] = { t: u.now() }; P.save(); marks();
    }
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (ents) {
        ents.forEach(function (en) { if (en.isIntersecting) { var pid = en.target.dataset.pg; endSeen[pid] = true; tryRead(pid); } });
      }, { rootMargin: '0px 0px -40px 0px' });
      var recapIo = new IntersectionObserver(function (ents) { ents.forEach(function (en) { if (en.isIntersecting && onePage) markRecap(); }); });
      $$('[data-pg="recap"]', main).forEach(function (n) { recapIo.observe(n); });
      pages.forEach(function (p) {
        if (p.kind !== 'theory') return;
        var nodes = $$('.theory > [data-pg="' + p.id + '"]', main); if (nodes.length) io.observe(nodes[nodes.length - 1]);
      });
    }
    secPager.addEventListener('click', function (ev) { if (ev.target.closest('a.next') && cur && cur.kind === 'theory') { endSeen[cur.id] = true; tryRead(cur.id); } }, true);
    function marks() {
      if (cur && cur.kind === 'recap' && !onePage && P.state && !(P.state.read && P.state.read[LESSON.lesson + '#recap'])) return markRecap();
      if (links.recap) {
        if (P.state && P.state.read && P.state.read[LESSON.lesson + '#recap']) { links.recap.dataset.done = 'all'; links.recap.title = 'Просмотрено'; }
        else { delete links.recap.dataset.done; links.recap.removeAttribute('title'); }
      }
      Object.keys(endSeen).forEach(function (pid) { if (P.state && P.state.read && !P.state.read[LESSON.lesson + '#' + pid]) tryRead(pid); });
      pages.forEach(function (p) {
        if (p.kind === 'theory' && links[p.id]) {
          if (P.state && P.state.read && P.state.read[LESSON.lesson + '#' + p.id]) { links[p.id].dataset.done = 'all'; links[p.id].title = 'Прочитано'; }
          else { delete links[p.id].dataset.done; links[p.id].removeAttribute('title'); }
        }
        if (p.kind !== 'task' || !links[p.id]) return;
        var e = (P.state && P.state.tasks[key(p.extra.task)]) || {};
        if (e.solved) links[p.id].dataset.done = 'all'; else if (e.att) links[p.id].dataset.done = 'part'; else delete links[p.id].dataset.done;
      });
    }
    Pages = { marks: marks, active: function () { return true; } };
  }

  // ---------- старт ----------
  initPaged();
  initCells();
  var askL = $('#ask-lesson');
  if (askL) askL.onclick = function () {
    u.copyText('Я прохожу курс «Data Science для аналитиков», урок «' + LESSON.title + '». Мне непонятно вот что: …\nОбъясни простыми словами, с маленьким примером на Python.')
      .then(function () { toast('Шаблон вопроса скопирован.'); });
  };
  P.init().then(function () {
    if (LESSON.mode !== 'test') {
      P.state.last = { lesson: LESSON.lesson, anchor: (P.state.last && P.state.last.lesson === LESSON.lesson && P.state.last.anchor) || '', t: u.now() };
      P.save();
    }
    initTasks(); initPredicts(); initQuizzes(); initNotes(); initFeedback(); updateProgress(); initToc(); renderExam();
    P.onChange(function () { Object.keys(cards).forEach(function (id) { cards[id].render(); }); updateProgress(); if (Pages) Pages.marks(); });
    if (Pages) Pages.marks();
    // после монтирования редакторов высота страницы меняется — довести до якоря
    if (location.hash) { var target = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (target) setTimeout(function () { target.scrollIntoView(); }, 60); }
  });
  // Python загружаем заранее, пока человек читает теорию
  var warm = function () { if (LESSON.mode !== 'test') Py.start().catch(function () {}); };
  if ('requestIdleCallback' in window) requestIdleCallback(warm, { timeout: 2500 }); else setTimeout(warm, 1200);
})();
