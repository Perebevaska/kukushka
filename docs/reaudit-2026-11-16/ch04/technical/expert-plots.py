"""Run plotted examples and reference solutions; write a compact inventory and contact sheets."""
import base64
from contextlib import chdir
from io import BytesIO
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "site/assets"))
import harness

items = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
thumbs = []
inventory = []
with chdir(ROOT / "site/data"):
    for t in items:
        if not t["lesson"].startswith("ch04/") or t["kind"] not in ("task","cell"):
            continue
        source = t.get("solution") or t.get("code") or ""
        if not any(word in source for word in ("plt.",".plot", "boxplot", "scatter_matrix")):
            continue
        result = harness.run(source, setup=t.get("setup"), show_last=bool(t.get("display")))
        assert result["ok"], (t["lesson"],t["id"],result.get("error"))
        for i, data in enumerate(result["figs"]):
            im = Image.open(BytesIO(base64.b64decode(data))).convert("RGB")
            name = f'{t["lesson"].split("/")[1]} {t["kind"]} {t["id"]}'
            axes = harness._LAST_FIGS[i].axes
            inventory.append(dict(label=name, size=im.size, axes=len(axes), titles=[a.get_title() for a in axes]))
            im.thumbnail((325,177))
            thumbs.append((name, im))
for offset in range(0,len(thumbs),12):
    contact = Image.new("RGB",(990,800),"white")
    draw = ImageDraw.Draw(contact)
    for j,(name,img) in enumerate(thumbs[offset:offset+12]):
        x,y=(j%3)*330,(j//3)*200
        draw.text((x+5,y+1),name,fill="black")
        contact.paste(img,(x+2,y+18))
    contact.save(out / f'plots-{offset//12+1}.png')
print(json.dumps(inventory,ensure_ascii=False,indent=2))
