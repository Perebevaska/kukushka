import json
with open("zerno_draft.ipynb",encoding="utf-8") as f:
    nb=json.load(f)
n_md=sum(c["cell_type"]=="markdown" for c in nb["cells"])
n_code=sum(c["cell_type"]=="code" for c in nb["cells"])
counts=[c["execution_count"] for c in nb["cells"] if c["cell_type"]=="code"]
ran=[n for n in counts if n is not None]
in_order=all(a<b for a,b in zip(ran,ran[1:]))
