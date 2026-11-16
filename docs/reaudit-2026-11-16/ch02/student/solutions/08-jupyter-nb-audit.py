import json
import re
def audit(nb):
    problems=[]
    maximum=0
    for i,c in enumerate(nb["cells"]):
        if c["cell_type"]!="code":
            continue
        n=c.get("execution_count")
        if n is not None:
            if n<maximum:
                problems.append((i,"order"))
            maximum=max(maximum,n)
        source="".join(c["source"])
        for j,ch in enumerate(source):
            if ch in ['"',"'"]:
                after=source[j+1:]
                if after.startswith("/") or (len(after)>=2 and after[0].isalpha() and after[1]==":"):
                    problems.append((i,"abs_path"))
                    break
        if any(o.get("output_type")=="error" for o in c.get("outputs",[])):
            problems.append((i,"error"))
        lines=[x.strip() for x in source.splitlines() if x.strip()]
        if lines and all(x.startswith("#") for x in lines):
            problems.append((i,"commented"))
    return problems
nb=json.load(open("zerno_draft.ipynb",encoding="utf-8"))
audit(nb)
