import json
import copy
nb=json.load(open("zerno_draft.ipynb",encoding="utf-8"))
def strip(nb):
    clean=copy.deepcopy(nb)
    for c in clean["cells"]:
        if c["cell_type"]=="code":
            c["outputs"]=[]
            c["execution_count"]=None
    return clean
n_removed=sum(len(c.get("outputs",[])) for c in nb["cells"] if c["cell_type"]=="code")
clean=strip(nb)
