// Python в отдельном потоке (Web Worker): страница не «замирает», зависший код можно остановить.
// Сообщения: {type:'init', indexURL, harnessURL} → {type:'ready'} | {type:'error'}
//            {type:'run', id, code, check, setup, files} → {type:'result', id, result}
// pandas подключает openpyxl лениво, внутри read_excel/to_excel — сами import-а в коде нет
const withHidden = (code) => /read_excel|to_excel|ExcelFile|ExcelWriter/.test(code || '') ? code + '\nimport openpyxl' : code;
let py = null;
let ready = null;
let dataBase = '';
const loadedFiles = new Set();

async function init(indexURL, harnessURL, dataURL) {
  dataBase = dataURL;
  const mod = await import(indexURL + 'pyodide.mjs');
  py = await mod.loadPyodide({ indexURL, env: { MPLBACKEND: 'agg', HOME: '/home/pyodide' } });
  const src = await (await fetch(harnessURL)).text();
  py.FS.writeFile('/home/pyodide/_dsc_harness.py', src);
  py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import _dsc_harness');
}

async function putFiles(files) {
  for (const name of files || []) {
    if (loadedFiles.has(name)) continue;
    const r = await fetch(dataBase + name);
    if (!r.ok) throw new Error('Не загрузился файл данных ' + name);
    py.FS.writeFile('/home/pyodide/' + name, new Uint8Array(await r.arrayBuffer()));
    loadedFiles.add(name);
  }
}

self.onmessage = async (e) => {
  const m = e.data;
  if (m.type === 'init') {
    ready = init(m.indexURL, m.harnessURL, m.dataURL);
    try { await ready; self.postMessage({ type: 'ready' }); }
    catch (err) { self.postMessage({ type: 'error', message: String(err && err.message || err) }); }
    return;
  }
  if (m.type === 'warm') {
    // заранее загрузить и импортировать тяжёлые библиотеки урока, пока ученик читает теорию
    try {
      await ready;
      await py.loadPackagesFromImports(withHidden(m.code), { messageCallback() {}, errorCallback() {} });
      py.runPython(m.code);
    } catch (err) { /* не страшно: загрузится при первом запуске */ }
    return;
  }
  if (m.type === 'trace') {
    try {
      await ready;
      await putFiles(m.files);
      await py.loadPackagesFromImports(withHidden(m.code), { messageCallback() {}, errorCallback() {} });
      const r = py.pyimport('_dsc_harness').trace(m.code);
      const result = r.toJs({ dict_converter: Object.fromEntries });
      r.destroy();
      self.postMessage({ type: 'result', id: m.id, result });
    } catch (err) {
      self.postMessage({ type: 'result', id: m.id, result: { steps: [], error: { text: 'Не удалось выполнить по шагам: ' + String(err && err.message || err) } } });
    }
    return;
  }
  if (m.type === 'run') {
    try {
      await ready;
      await putFiles(m.files);
      const all = [m.setup || '', m.code, m.check || ''].join('\n');
      self.postMessage({ type: 'status', id: m.id, text: 'Загружаю библиотеки…' });
      await py.loadPackagesFromImports(withHidden(all), { messageCallback() {}, errorCallback() {} });
      self.postMessage({ type: 'status', id: m.id, text: 'Выполняю…' });
      const fn = py.pyimport('_dsc_harness').run;
      const r = fn(m.code, m.check ?? null, m.setup ?? null, !!m.display);
      const result = r.toJs({ dict_converter: Object.fromEntries });
      r.destroy();
      self.postMessage({ type: 'result', id: m.id, result });
    } catch (err) {
      self.postMessage({ type: 'result', id: m.id, result: {
        ok: false, out: '', figs: [], check: m.check ? { passed: false, msg: 'Среда Python не ответила.' } : null,
        error: { type: 'Internal', text: 'Не удалось выполнить код: ' + String(err && err.message || err) } } });
    }
  }
};
