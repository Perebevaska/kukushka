import copy
import difflib
import json
def strip(nb):
    clean=copy.deepcopy(nb)
    for c in clean["cells"]:
        if c["cell_type"]=="code":
            c["outputs"]=[]
            c["execution_count"]=None
    return clean
def changed_lines(a,b):
    return sum(l[:1] in ["+","-"] and not l.startswith(("+++","---")) for l in difflib.unified_diff(a.splitlines(),b.splitlines()))
old=open("zerno_draft.ipynb",encoding="utf-8").read()
new=open("zerno_rerun.ipynb",encoding="utf-8").read()
raw_changed=changed_lines(old,new)
clean_changed=changed_lines(json.dumps(strip(json.loads(old)),ensure_ascii=False,indent=1),json.dumps(strip(json.loads(new)),ensure_ascii=False,indent=1))
