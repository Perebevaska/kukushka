"""Run against the current NMS card; no dependencies beyond Python."""
import math
import re
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
card = (repo / "content/ch14/04c-detection.md").read_text().split("## task: nms |")[1]
def section(name):
    return re.search(rf"### {name}\n```python\n(.*?)\n```", card, re.S).group(1)

for variant in ("author", "alternative", "threshold-equality"):
    scope = {}
    exec(section("setup"), scope)
    source = section("solution")
    if variant != "author":
        start = source.index("def nms(")
        end = source.index("\n\n", start)
        op = ">=" if variant == "threshold-equality" else ">"
        alternate = f"""def nms(dets, thr=0.5):
    ordered = sorted(dets, key=lambda item: item[1], reverse=True)
    kept = []
    for candidate in ordered:
        if not any(iou(candidate[0], old[0]) {op} thr for old in kept):
            kept.append(candidate)
    return kept"""
        source = source[:start] + alternate + source[end:]
    exec(source, scope)
    scope["need"] = lambda name, *types: scope[name]
    scope["close"] = lambda a, b, tol=1e-6: math.isclose(a,b,rel_tol=0,abs_tol=tol)
    pair = [((0,0,10,10),.9), ((0,0,5,10),.8)]
    print(variant, "equal", scope["nms"](pair), "above", scope["nms"](pair,.49))
    try:
        exec(section("check"), scope)
        print("verdict PASS")
    except AssertionError as exc:
        print("verdict FAIL", str(exc))
