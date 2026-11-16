"""Check the actual static site's embedded execution packets, notebook tasks and export."""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[4]

class Packet(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading = False
        self.data = ""
    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "lesson-data":
            self.reading = True
    def handle_endtag(self, tag):
        if tag == "script":
            self.reading = False
    def handle_data(self, data):
        if self.reading:
            self.data += data

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

export_path = Path(sys.argv[1])
site = root / "site"
notebook_tasks = json.loads((site/"notebooks/tasks/ch12.json").read_text())["tasks"]
export = {t["lesson"]+"/"+t["id"]:t for t in json.loads(export_path.read_text()) if t["kind"]=="task" and t["lesson"].startswith("ch12/")}
visible = {}
for k in sorted({x["lesson"] for x in export.values()}):
    page = site / (k+".html")
    packet = Packet()
    packet.feed(page.read_text())
    for row in json.loads(packet.data)["tasks"]:
        visible[k+"/"+row["id"]] = row
assert set(visible)==set(notebook_tasks)==set(export)
for k in export:
    for field in ("setup","check","solution"):
        assert visible[k][field]==notebook_tasks[k][field]==export[k][field],(k,field)
    for field in ("starter","level"):
        assert visible[k][field]==notebook_tasks[k][field],(k,field)
assets=[*sorted((site/"ch12").glob("*.html")),site/"notebooks/tasks/ch12.json",site/"notebooks/ch12-practice.ipynb",site/"assets/harness.py",site/"data/app_orders.csv"]
version=json.loads((site/"assets/vendor/pyodide/pyodide-lock.json").read_text())["info"]
log=dict(export_sha=sha(export_path),tasks=len(visible),execution_fields=["setup","check","solution"],browser_notebook_fields=["starter","level"],files={str(p.relative_to(root)):sha(p) for p in assets},runtime=version)
(here/"release-parity.json").write_text(json.dumps(log,ensure_ascii=False,indent=2)+"\n")
