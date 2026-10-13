/* Интерактивные виджеты курса: ползунок меняет параметр — график и числа пересчитываются сразу.
   Блок в уроке: ::: widget имя … :::  Данные (если нужны) — content/widgets/имя.json. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, cls, anchor) {
    var t = svgEl('text', { x: x, y: y, 'class': cls || 'ink sm', 'text-anchor': anchor || 'middle' }, parent);
    t.textContent = s; return t;
  }
  function h(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function pct(v, d) { return (100 * v).toFixed(d == null ? 1 : d).replace('.', ',') + '\u00a0%'; }
  function num(v, d) { return v.toFixed(d).replace('.', ',').replace(/^-/, '−'); }
  function slider(body, label, min, max, step, value, fmt, onInput) {
    var row = h('label', 'w-ctrl');
    row.appendChild(h('span', 'w-lab', label));
    var inp = h('input'); inp.type = 'range'; inp.min = min; inp.max = max; inp.step = step; inp.value = value;
    var out = h('b', 'w-val', fmt(+value));
    inp.addEventListener('input', function () { out.textContent = fmt(+inp.value); onInput(+inp.value); });
    row.appendChild(inp); row.appendChild(out); body.appendChild(row);
    return inp;
  }

  var W = {};

  // ---------- 1. Шаг градиентного спуска ----------
  W['gd-lr'] = function (body) {
    var km = [1, 2, 3, 4.5, 6], mi = [18, 25, 34, 44, 55], n = km.length;
    function L(w) { var s = 0; for (var i = 0; i < n; i++) { var e = w * km[i] - mi[i]; s += e * e; } return s / n; }
    function G(w) { var s = 0; for (var i = 0; i < n; i++) s += 2 * (w * km[i] - mi[i]) * km[i]; return s / n; }
    var sxx = 0, sxy = 0; for (var i = 0; i < n; i++) { sxx += km[i] * km[i]; sxy += km[i] * mi[i]; }
    var wOpt = sxy / sxx, crit = 2 / (2 * sxx / n);
    var LRS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.068, 0.074, 0.08, 0.1];
    var svg = svgEl('svg', { viewBox: '0 0 680 250', role: 'img' });
    var info = h('p', 'w-info');
    slider(body, 'Шаг обучения lr', 0, LRS.length - 1, 1, 3, function (k) { return String(LRS[k]).replace('.', ','); }, function (k) { draw(LRS[k]); });
    body.appendChild(svg); body.appendChild(info);
    var X = function (w) { return 50 + w * 28; }, Y = function (l) { return 210 - l / 1500 * 190; };
    function draw(lr) {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      var defs = svgEl('defs', {}, svg), m = svgEl('marker', { id: 'w-ah', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' }, defs);
      svgEl('path', { d: 'M0,0 L10,5 L0,10 z', 'class': 'ah-acc' }, m);
      svgEl('line', { x1: X(0), y1: 210, x2: X(21.5), y2: 210, 'class': 'ln' }, svg);
      for (var t = 0; t <= 20; t += 5) text(svg, X(t), 228, String(t), 'mut sm');
      text(svg, X(10.5), 246, 'вес w, минут на км', 'mut sm');
      var d = '', first = true;
      for (var w = 0; w <= 20.01; w += 0.1) { var l = L(w); if (l > 1500) { first = true; continue; } d += (first ? 'M' : 'L') + X(w).toFixed(1) + ',' + Y(l).toFixed(1) + ' '; first = false; }
      svgEl('path', { d: d, 'class': 'ln' }, svg);
      svgEl('circle', { cx: X(wOpt), cy: Y(L(wOpt)), r: 4, 'class': 'box-ok' }, svg);
      var w0 = 0, pts = [w0], out = false;
      for (var s = 0; s < 12; s++) { w0 = w0 - lr * G(w0); pts.push(w0); if (!isFinite(w0) || Math.abs(w0) > 1e6) { out = true; break; } }
      for (var j = 0; j + 1 < pts.length; j++) {
        var a = pts[j], b = pts[j + 1];
        if (a < -1 || a > 21.5 || b < -1 || b > 21.5 || L(a) > 1500 || L(b) > 1500) { out = true; break; }
        svgEl('path', { d: 'M' + X(a) + ',' + Y(L(a)) + ' L' + X(b) + ',' + Y(L(b)), 'class': 'ln-acc', 'marker-end': 'url(#w-ah)' }, svg);
        svgEl('circle', { cx: X(a), cy: Y(L(a)), r: 3.5, 'class': 'box-acc' }, svg);
      }
      var last = pts[pts.length - 1], lastL = L(last);
      var verdict;
      if (out || !isFinite(lastL) || lastL > L(0)) verdict = 'спуск <b>расходится</b>: каждый шаг перепрыгивает дно и уносит дальше. Для этих данных шаги больше ≈ ' + num(crit, 3) + ' всегда взрываются.';
      else if (lastL - L(wOpt) < 0.03 * L(wOpt)) verdict = 'спуск <b>сошёлся</b>: за 12 шагов w ≈ ' + num(last, 2) + ', MSE ≈ ' + num(lastL, 1) + ' — это дно (w* ≈ ' + num(wOpt, 2) + ').';
      else if ((pts[1] - wOpt) * (pts[2] - wOpt) < 0) verdict = 'спуск <b>качается</b> через дно: шаг великоват, но пока сходится. После 12 шагов w ≈ ' + num(last, 2) + ', MSE ≈ ' + num(lastL, 1) + '.';
      else verdict = 'спуск <b>ползёт</b>: шаг маленький, за 12 шагов дошли только до w ≈ ' + num(last, 2) + ' (MSE ≈ ' + num(lastL, 1) + ', дно — ' + num(L(wOpt), 1) + ').';
      text(svg, X(wOpt), Y(L(wOpt)) - 10, 'дно', 'ok sm b');
      info.innerHTML = 'Старт w = 0, 12 шагов. При lr = ' + String(lr).replace('.', ',') + ' ' + verdict;
    }
    draw(LRS[2]);
  };

  // ---------- 2. Порог классификации ----------
  W['threshold'] = function (body, data) {
    var p = data.p || [], y = data.y || [], N = p.length, P = y.reduce(function (a, b) { return a + b; }, 0);
    var box = h('div', 'w-cm'), info = h('p', 'w-info');
    slider(body, 'Порог', 0.05, 0.95, 0.05, 0.5, function (v) { return num(v, 2); }, draw);
    body.appendChild(box); body.appendChild(info);
    function cell(cls, big, small) { var c = h('div', 'w-cell ' + cls); c.appendChild(h('b', '', big)); c.appendChild(h('span', '', small)); return c; }
    function draw(t) {
      var tp = 0, fp = 0, fn = 0, tn = 0;
      for (var i = 0; i < N; i++) { var hit = p[i] >= t; if (hit && y[i]) tp++; else if (hit) fp++; else if (y[i]) fn++; else tn++; }
      box.textContent = '';
      box.appendChild(h('span', 'w-cm-h', '')); box.appendChild(h('span', 'w-cm-h', 'модель: уйдёт')); box.appendChild(h('span', 'w-cm-h', 'модель: останется'));
      box.appendChild(h('span', 'w-cm-r', 'ушёл')); box.appendChild(cell('ok', tp, 'TP — нашли')); box.appendChild(cell('err', fn, 'FN — пропустили'));
      box.appendChild(h('span', 'w-cm-r', 'остался')); box.appendChild(cell('warn', fp, 'FP — зря')); box.appendChild(cell('', tn, 'TN — верно'));
      var prec = tp + fp ? tp / (tp + fp) : 0, rec = P ? tp / P : 0;
      info.innerHTML = 'Отмечено ' + (tp + fp) + ' гостей из ' + N + '. Точность <b>' + pct(prec) + '</b> (из отмеченных ушли), полнота <b>' + pct(rec) + '</b> (из ' + P + ' ушедших нашли). ' +
        (t <= 0.25 ? 'Низкий порог: ловим почти всех, но много лишних бонусов.' : t >= 0.7 ? 'Высокий порог: почти без ошибок в списке, но многих уходящих пропускаем.' : 'Двигайте ползунок: точность и полнота меняются в разные стороны.');
    }
    draw(0.5);
  };

  // ---------- 3. Глубина дерева ----------
  W['tree-depth'] = function (body, data) {
    var rows = data.rows || [], base = data.base;
    var svg = svgEl('svg', { viewBox: '0 0 680 240', role: 'img' }), info = h('p', 'w-info');
    slider(body, 'Глубина дерева', 1, rows.length, 1, 3, function (v) { return String(v); }, draw);
    body.appendChild(svg); body.appendChild(info);
    var lo = 0.7, hi = 1.0;
    var X = function (d) { return 60 + (d - 1) * (580 / (rows.length - 1)); }, Y = function (v) { return 200 - (v - lo) / (hi - lo) * 180; };
    function line(key, cls) { return rows.map(function (r, i) { return (i ? 'L' : 'M') + X(r.depth) + ',' + Y(r[key]); }).join(' '); }
    function draw(dep) {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      [0.7, 0.8, 0.9, 1.0].forEach(function (v) { svgEl('line', { x1: 60, y1: Y(v), x2: 640, y2: Y(v), 'class': 'ln-mut' }, svg); text(svg, 52, Y(v) + 4, Math.round(v * 100) + ' %', 'mut sm', 'end'); });
      rows.forEach(function (r) { text(svg, X(r.depth), 220, String(r.depth), 'mut sm'); });
      text(svg, 350, 237, 'глубина дерева', 'mut sm');
      if (base) { svgEl('line', { x1: 60, y1: Y(base), x2: 640, y2: Y(base), 'class': 'ln-err dash' }, svg); text(svg, 636, Y(base) - 6, '«всегда вовремя» ' + pct(base), 'err sm', 'end'); }
      svgEl('path', { d: line('train'), 'class': 'ln' }, svg);
      svgEl('path', { d: line('test'), 'class': 'ln-acc' }, svg);
      text(svg, X(rows.length) - 4, Y(rows[rows.length - 1].train) - 8, 'обучение', 'ink2 sm', 'end');
      text(svg, X(rows.length) - 4, Y(rows[rows.length - 1].test) + 16, 'тест', 'acc sm b', 'end');
      var r = rows[dep - 1];
      svgEl('line', { x1: X(dep), y1: 20, x2: X(dep), y2: 200, 'class': 'ln-mut dash' }, svg);
      svgEl('circle', { cx: X(dep), cy: Y(r.train), r: 5, 'class': 'box' }, svg);
      svgEl('circle', { cx: X(dep), cy: Y(r.test), r: 5, 'class': 'box-acc' }, svg);
      var gap = r.train - r.test, best = rows.reduce(function (a, b) { return b.test > a.test ? b : a; });
      info.innerHTML = 'Глубина ' + dep + ': обучение <b>' + pct(r.train) + '</b>, тест <b>' + pct(r.test) + '</b>, разрыв ' + num(gap * 100, 1) + ' п.п. ' +
        (gap <= 0.03 && r.test < base + 0.005 ? 'Дерево слишком простое: на тесте не лучше правила «всегда вовремя» — это недообучение.' :
         r.test < base ? 'На тесте хуже простого правила «всегда вовремя» — дерево запомнило шум.' :
         gap > 0.06 ? 'Разрыв растёт — дерево начинает запоминать обучающие строки.' :
         dep === best.depth ? 'Это лучшая глубина по тесту.' : 'Обучение и тест близко — дереву можно верить.') +
        ' Лучший тест — на глубине ' + best.depth + ' (' + pct(best.test) + ').';
    }
    draw(3);
  };

  // ---------- LM Studio: подключена ли своя языковая модель ----------
  W['lm-studio'] = function (body) {
    var URL = 'http://localhost:1234/v1';
    var row = h('div', 'lm-status'), dot = h('i'), msg = h('span', 'lm-msg', 'Проверяю LM Studio…');
    row.appendChild(dot); row.appendChild(msg);
    var again = h('button', 'btn ghost', 'Проверить снова'); again.type = 'button';
    var models = h('p', 'w-info lm-models');
    body.appendChild(row); body.appendChild(models); body.appendChild(again);
    // тот же статус — индикатором в шапке страницы, рядом с Python
    var pill = document.getElementById('lm-pill'), py = document.getElementById('py-pill');
    if (!pill && py) {
      pill = h('a', 'py-pill lm-pill'); pill.id = 'lm-pill';
      pill.appendChild(h('i')); pill.appendChild(h('span', '', 'LM Studio'));
      py.parentNode.insertBefore(pill, py.nextSibling);
      var fig = body.closest('figure');
      pill.href = '#' + (fig ? fig.id : '');
    }
    function set(state, text, title) {
      row.dataset.state = state; msg.textContent = text;
      if (pill) { pill.dataset.state = state === 'ok' ? 'ready' : state === 'checking' ? 'checking' : 'error'; pill.title = title || text;
        pill.lastElementChild.textContent = state === 'ok' ? 'LM Studio подключён' : state === 'checking' ? 'LM Studio…' : 'LM Studio не подключён'; }
    }
    function timed(url, opts, ms) {
      var c = new AbortController(), t = setTimeout(function () { c.abort(); }, ms);
      opts = opts || {}; opts.signal = c.signal;
      return fetch(url, opts).finally(function () { clearTimeout(t); });
    }
    function check() {
      set('checking', 'Проверяю LM Studio…'); models.textContent = '';
      timed(URL + '/models', { cache: 'no-store' }, 3000).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).then(function (d) {
        var names = (d.data || []).map(function (m) { return m.id; }).filter(function (n) { return !/embed/i.test(n); });
        if (!names.length) { set('warn', 'Сервер LM Studio работает, но модели нет — скачайте и загрузите модель (шаг 2).'); return; }
        set('ok', 'Подключено: сервер LM Studio отвечает на localhost:1234.');
        models.textContent = 'Модели: ' + names.join(', ') + '. По умолчанию local_llm.ask() берёт первую.';
      }).catch(function () {
        // без CORS браузер не покажет ответ, но запрос «вслепую» пройдёт, если сервер запущен
        timed(URL + '/models', { mode: 'no-cors', cache: 'no-store' }, 3000).then(function () {
          set('warn', 'Сервер LM Studio запущен, но не разрешает запросы со страницы — включите CORS (шаг 3).');
        }).catch(function () {
          set('err', 'Не подключено: LM Studio не отвечает на localhost:1234 — запустите сервер (шаги 1–3).');
        });
      });
    }
    again.onclick = check;
    check();
  };

  document.querySelectorAll('[data-widget]').forEach(function (fig) {
    var name = fig.getAttribute('data-widget'), body = fig.querySelector('.widget-body'), data = {};
    try { data = JSON.parse(fig.querySelector('.widget-data').textContent || '{}'); } catch (e) { /* без данных */ }
    if (W[name] && body) W[name](body, data);
  });
})();
