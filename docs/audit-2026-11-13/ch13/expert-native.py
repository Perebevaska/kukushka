"""Execute unmodified cells with a clean writable notebook cache and ordinary relative DATA paths."""
from contextlib import chdir
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
name = sys.argv[1]
notebook = ROOT / f"site/notebooks/extra/ch13-{name}.ipynb"
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)
    (path/"data").symlink_to(ROOT/"site/data",target_is_directory=True)
    notebook_dir = path/"notebooks/extra"
    notebook_dir.mkdir(parents=True)
    ns = {"display":print}
    with chdir(notebook_dir):
        for i, cell in enumerate(json.loads(notebook.read_text())["cells"]):
            if cell["cell_type"]=="code":
                source = "".join(cell["source"])
                exec(compile(source,f"cell-{i}","exec"),ns)
    for key in ["f1_emb","f1_tfidf"]:
        if key in ns: print(key,ns[key])

if name=="transformers":
    import numpy as np
    import torch
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    tok, model = ns["tok"], ns["model"]
    report = "Кофе еда цена курьер доставка атмосфера"
    for length in (64,5):
        print("right truncation",length,tok.tokenize(report),
              tok.convert_ids_to_tokens(tok(report,truncation=True,max_length=length)["input_ids"]))
    from huggingface_hub import try_to_load_from_cache
    print("model revision",Path(try_to_load_from_cache(ns["MODEL_NAME"],"config.json")).parent.name)
    cls_embeddings = []
    texts = ns["reviews"]["text"].tolist()
    for i in range(0,len(texts),32):
        enc=tok(texts[i:i+32],padding=True,truncation=True,max_length=128,return_tensors="pt")
        with torch.no_grad():
            cls_embeddings.extend(torch.nn.functional.normalize(model(**enc).last_hidden_state[:,0,:],dim=1).numpy())
    cls=cross_val_score(LogisticRegression(max_iter=1000),np.array(cls_embeddings),ns["y"],cv=ns["cv"],scoring="f1")
    print("model card CLS pooling F1",cls,cls.mean())
