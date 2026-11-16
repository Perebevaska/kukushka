"""Exercise the published fine-tuning snippet, supplying its two training batches."""
import hashlib
import json
import os
from pathlib import Path
import re

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[key] = "1"

import numpy as np
import scipy.ndimage as ndi
import torch
import torchvision
from torch import nn

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.manual_seed(20261117)
repo = Path(__file__).resolve().parents[4]
lesson = repo / "content/ch14/04b-transfer.md"
chapter = lesson.read_text()
block = next(b for b in re.findall(r"^```python static\n(.*?)^```", chapter, re.S | re.M)
             if "model.layer4.train()" in b)
cached = Path(torch.hub.get_dir()) / "checkpoints/resnet18-f37072fd.pth"
assert cached.exists()
print(json.dumps(dict(block_sha256=hashlib.sha256(block.encode()).hexdigest(),
                      block_convention="fenced source code, trailing newline included",
                      torch=str(torch.__version__), torchvision=str(torchvision.__version__),
                      torch_threads=[torch.get_num_threads(), torch.get_num_interop_threads()],
                      weight_sha256=hashlib.sha256(cached.read_bytes()).hexdigest())))
labels = torch.arange(4)
batch = torch.randn(4, 3, 64, 64)
control = torch.randn(2, 3, 64, 64)

def group(name):
    if name.startswith("fc."):
        return "head"
    if name.startswith("layer4."):
        return "layer4"
    return "lower"

def snapshot(entries):
    return {name: value.detach().clone() for name,value in entries}

def deltas(entries,before):
    changed = {"lower":0, "layer4":0, "head":0}
    for name,value in entries:
        changed[group(name)] += int(not torch.equal(value,before[name]))
    return changed

def control_features(net):
    # Use exactly the module flags under test, preserving the head-training mode.
    seen = []
    hook = net.fc.register_forward_pre_hook(lambda _module, args: seen.append(args[0].detach().clone()))
    with torch.no_grad():
        net(control)
    hook.remove()
    return seen[0]

def one_batch(net, opt, phase):
    assert net.fc.training and net.layer4.training == (phase == 3)
    assert all(not m.training for n,m in net.named_modules() if n and group(n+".")=="lower")
    active = {"head"} if phase==2 else {"head","layer4"}
    assert all(v.requires_grad == (group(n) in active) for n,v in net.named_parameters())
    before_params = snapshot(net.named_parameters())
    before_buffers = snapshot(net.named_buffers())
    if phase == 2:
        embedding = control_features(net)
    opt.zero_grad()
    loss = nn.functional.cross_entropy(net(batch),labels)
    loss.backward()
    opt.step()
    params = deltas(net.named_parameters(), before_params)
    buffers = deltas(net.named_buffers(), before_buffers)
    assert {k for k,v in params.items() if v}==active
    assert {k for k,v in buffers.items() if v}==({"layer4"} if phase==3 else set())
    evidence=dict(phase=phase,loss=float(loss.detach()),params_changed=params,buffers_changed=buffers)
    if phase==2:
        error = (control_features(net)-embedding).abs().max().item()
        assert error==0
        evidence["control_embedding_max_abs_delta"]=error
    print(json.dumps(evidence))

def verify_eval(net,phase):
    assert all(not mod.training for mod in net.modules())
    print(json.dumps(dict(full_eval_after=phase,training_modules=0)))

static_markers = ["# … обучение головы на батчах …", "# … обучение верхнего блока и головы на батчах …"]
tested=block
for stage, marker in zip((2,3), static_markers):
    assert tested.count(marker)==1
    tested=tested.replace(marker,marker+f"\none_batch(model, opt, {stage})")
    val = "model.eval()                                            # перед оценкой на валидации"
    i=tested.index(val,tested.index(marker))
    tested=tested[:i]+tested[i:].replace(val,val+f"\nverify_eval(model, {stage})",1)
exec(compile(tested,str(lesson), "exec"), globals())

# Match the actual 04/layer operation and same weights, using a constant image
# and kernels that expose a boundary. ReLU, bias and max-pool are included.
source=(repo/"content/ch14/04-cnn.md").read_text().split("## task: layer |")[1].split("## task:")[0]
solution=re.search(r"### solution\n```python\n(.*?)\n```",source,re.S).group(1)
card_source=solution[:solution.index("out =")]
scope={"np":np,"ndi":ndi}
exec(card_source, scope)
img=np.full((8,8),.8, dtype=np.float64)
weights=np.array([[[1,0,-1],[2,0,-2],[1,0,-1]],np.ones((3,3))])
bias=np.array([.5,.3])
expected=scope["pool2"](scope["conv_layer"](img,weights,bias))
deltas_by_padding={}
for padding_mode in ["replicate","zeros"]:
    conv=nn.Conv2d(1,2,3,padding=1,padding_mode=padding_mode,dtype=torch.float64)
    with torch.no_grad():
        conv.weight.copy_(torch.from_numpy(weights[:,None]))
        conv.bias.copy_(torch.from_numpy(bias))
        output=nn.MaxPool2d(2)(nn.ReLU()(conv(torch.from_numpy(img)[None,None])))[0].numpy()
    deltas_by_padding[padding_mode]=float(np.max(np.abs(output-expected)))
assert deltas_by_padding["replicate"] < 1e-12 and deltas_by_padding["zeros"]>.1
print(json.dumps(dict(layer_padding_max_abs_delta=deltas_by_padding)))
