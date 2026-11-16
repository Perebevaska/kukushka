"""Run the native lesson CNN or the lesson's ResNet-18 extractor and frozen buffers."""
from contextlib import chdir
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
import torch
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/"site/data"
torch.set_num_threads(1)
if sys.argv[1]=="cnn":
    lesson=(ROOT/"content/ch14/04-cnn.md").read_text().split("## Сеть на PyTorch",1)[1]
    block=re.search(r"```python static\n(.*?)\n```",lesson,re.S).group(1)
    with chdir(DATA):
        exec(compile(block,"native-lesson-CNN","exec"),{})
else:
    import torchvision
    print("torch",torch.__version__,"torchvision",torchvision.__version__)
    lesson=(ROOT/"content/ch14/04b-transfer.md").read_text()
    block=re.search(r"```python static\n(.*?)\n```",lesson,re.S).group(1)
    ns={}
    exec(compile(block,"lesson-extractor","exec"),ns)
    model=ns["resnet"]
    sample=np.load(DATA/"showcase.npz")
    with tempfile.TemporaryDirectory() as folder:
        paths=[]
        for j,img in enumerate(sample["X"][:4]):
            path=Path(folder)/f"{j}.png"
            Image.fromarray(img).save(path)
            paths.append(path)
        print("actual embed",ns["embed"](paths).shape)
        xb=torch.stack([ns["prep"](Image.open(p).convert("RGB")) for p in paths])
    for par in model.parameters(): par.requires_grad_(False)
    model.fc=torch.nn.Linear(512,4)
    bn=model.bn1
    trainable=sum(p.numel() for p in model.parameters() if p.requires_grad)
    for mode in [True,False]:
        model.train(mode)
        before=bn.running_mean.clone()
        w=bn.weight.clone()
        model(xb)
        print("mode, trainable, max delta BN weight and running_mean",mode,trainable,
              (bn.weight-w).abs().max().item(),(bn.running_mean-before).abs().max().item())
    # Test the textbook's extrapolation from random filters to pretrained features.
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    model=ns["models"].resnet18(weights=ns["weights"])
    model.fc=torch.nn.Identity()
    model.eval()
    embeddings=[]
    with torch.no_grad():
        for start in range(0,len(sample["X"]),16):
            batch=torch.stack([ns["prep"](Image.fromarray(img).convert("RGB")) for img in sample["X"][start:start+16]])
            embeddings.extend(model(batch).numpy())
    emb=np.asarray(embeddings)
    labels=sample["y"]
    tr,te=train_test_split(np.arange(len(labels)),test_size=.25,stratify=labels,random_state=42)
    for n in (10,25,50,100,200):
        ids=np.concatenate([tr[labels[tr]==k][:n] for k in range(4)])
        lr=make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000)).fit(emb[ids],labels[ids])
        print("ImageNet features, examples per class and accuracy",n,lr.score(emb[te],labels[te]))
