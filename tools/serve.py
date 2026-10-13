#!/usr/bin/env python3
"""Локальный сервер курса: http://127.0.0.1:8000

- отдаёт site/ (Python в браузере не работает из file://);
- хранит прогресс в progress/progress.json: GET/PUT /api/progress.
  PUT сливает присланное состояние с файлом (ничего не теряется при двух вкладках)
  и возвращает итог. Раз в день — копия progress/backup-ГГГГ-ММ-ДД.json, хранятся последние 14.

Порт фиксированный (localStorage браузера привязан к адресу с портом): DSC_PORT или 8000.
"""
from __future__ import annotations

import datetime as dt
import functools
import http.server
import json
import os
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
PROG_DIR = ROOT / 'progress'
PROG = PROG_DIR / 'progress.json'
PORT = int(os.environ.get('DSC_PORT', '8000'))
LOCK = threading.Lock()
KEEP_BACKUPS = 14


# ---------- слияние: те же правила, что в app.js (mergeState) ----------

MAPS = ('notes', 'quiz', 'fb', 'exam', 'read')


def _ts(x) -> str:
    return (x or {}).get('t') or ''


def merge(a: dict, b: dict) -> dict:
    """Объединить два состояния. Каждая запись берётся из более свежей версии (поле t),
    но отметка «решено» не теряется никогда: остаётся самая ранняя."""
    a = a if isinstance(a, dict) else {}
    b = b if isinstance(b, dict) else {}
    out = {'v': 2, 'tasks': {}, 'last': None}
    for key in set(a.get('tasks', {})) | set(b.get('tasks', {})):
        x, y = a.get('tasks', {}).get(key), b.get('tasks', {}).get(key)
        if not isinstance(x, dict) or not isinstance(y, dict):
            out['tasks'][key] = x if isinstance(x, dict) else y
            continue
        newer = dict(y if _ts(y) >= _ts(x) else x)
        solved = [s for s in (x.get('solved'), y.get('solved')) if s]
        newer['solved'] = min(solved) if solved else None
        out['tasks'][key] = newer
    for m in MAPS:   # словари «ключ → {…, t}»
        out[m] = {}
        for key in set(a.get(m) or {}) | set(b.get(m) or {}):
            x, y = (a.get(m) or {}).get(key), (b.get(m) or {}).get(key)
            out[m][key] = y if _ts(y) >= _ts(x) else x
    la, lb = a.get('last'), b.get('last')
    out['last'] = lb if _ts(lb) >= _ts(la) else la
    out['t'] = max(_ts(a), _ts(b)) or dt.datetime.now(dt.timezone.utc).isoformat()
    return out


def read_progress() -> dict:
    try:
        return json.loads(PROG.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_progress(state: dict) -> None:
    PROG_DIR.mkdir(exist_ok=True)
    tmp = PROG.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(tmp, PROG)
    backup = PROG_DIR / f'backup-{dt.date.today().isoformat()}.json'
    if not backup.exists():
        backup.write_text(PROG.read_text(encoding='utf-8'), encoding='utf-8')
        for old in sorted(PROG_DIR.glob('backup-*.json'))[:-KEEP_BACKUPS]:
            try:
                old.unlink()
            except OSError:
                pass


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript', '.wasm': 'application/wasm',
                      '.py': 'text/plain; charset=utf-8', '.json': 'application/json',
                      # на Windows типы берутся из реестра и бывают неверными — задаём явно
                      '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.svg': 'image/svg+xml',
                      '.png': 'image/png', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
                      '.csv': 'text/csv; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
                      '.zip': 'application/zip', '.whl': 'application/zip', '.tar': 'application/x-tar'}

    def log_message(self, *args):
        pass

    def end_headers(self):
        # страницы и скрипты курса меняются при пересборке — не кэшируем их
        if not self.path.startswith('/assets/vendor/'):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/ping':
            return self._json(200, {'app': 'ds-course'})
        if self.path == '/api/progress':
            with LOCK:
                return self._json(200, read_progress())
        return super().do_GET()

    def do_PUT(self):
        if self.path != '/api/progress':
            return self._json(404, {'error': 'not found'})
        try:
            n = int(self.headers.get('Content-Length', '0'))
            incoming = json.loads(self.rfile.read(n) or b'{}')
            if not isinstance(incoming, dict):
                raise ValueError('ожидался объект')
        except (ValueError, json.JSONDecodeError) as e:
            return self._json(400, {'error': str(e)})
        with LOCK:
            state = merge(read_progress(), incoming)
            write_progress(state)
        return self._json(200, state)


    do_POST = do_PUT   # navigator.sendBeacon при закрытии страницы


def already_running() -> bool:
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/ping', timeout=1) as r:
            return json.load(r).get('app') == 'ds-course'
    except Exception:  # noqa: BLE001
        return False


if __name__ == '__main__':
    url = f'http://127.0.0.1:{PORT}/index.html'
    no_browser = '--no-browser' in sys.argv
    try:
        srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Handler, directory=str(SITE)))
    except OSError:
        if already_running():
            print(f'Курс уже запущен: {url}')
            if not no_browser:
                webbrowser.open(url)
            sys.exit(0)
        sys.exit(f'Порт {PORT} занят другой программой. Закройте её или запустите с другим портом:\n'
                 f'  Mac/Linux: DSC_PORT=8010 ./Курс.command (или ./Курс-Linux.sh)\n'
                 f'  Windows:   set DSC_PORT=8010 и снова «Курс-Windows.bat» в том же окне\n'
                 f'(прогресс в браузере привязан к порту, но файл progress/progress.json общий)')
    print(f'Курс открыт: {url}\nПрогресс сохраняется в {PROG.relative_to(ROOT)}\n'
          f'Остановить — Ctrl+C или закрыть это окно.')
    if not no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
