"""Serve the current shipped site only for the four actual editor submissions."""
import functools, http.server, subprocess, threading
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[4]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
handler=functools.partial(Quiet,directory=str(root/'site'))
with http.server.ThreadingHTTPServer(('127.0.0.1',0),handler) as httpd:
    thread=threading.Thread(target=httpd.serve_forever,daemon=True)
    thread.start()
    try:
        subprocess.run(['node',str(here/'cold-ui.cjs'),'after',f'http://127.0.0.1:{httpd.server_port}/ch15/02-service.html','matrix'],check=True)
    finally:
        httpd.shutdown()
        thread.join()
