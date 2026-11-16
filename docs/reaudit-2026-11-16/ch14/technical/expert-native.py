"""Run with the native course environment, from any working directory."""
import hashlib
import importlib.util
import os
import re
from pathlib import Path

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
import torch
import torchvision
from torch import nn
from importlib.metadata import version

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
repo = Path(__file__).resolve().parents[4]
data = repo / "site/data"
print("python", os.sys.version.split()[0], "packages", {p: version(p) for p in
      ("torch", "torchvision", "numpy", "pandas", "scipy", "scikit-learn", "pillow")}, flush=True)
weight = Path(torch.hub.get_dir()) / "checkpoints/resnet18-f37072fd.pth"
assert weight.is_file(), "Fetch ImageNet weights separately before running."
print("cached weight sha256", hashlib.sha256(weight.read_bytes()).hexdigest(), flush=True)
spec = importlib.util.spec_from_file_location("features", repo / "site/notebooks/compare_showcase_features.py")
features = importlib.util.module_from_spec(spec)
spec.loader.exec_module(features)
# The published function sets Torch to two threads. Its numerical code runs unmodified.
original = torch.set_num_threads
torch.set_num_threads = lambda requested: original(1)
try:
    features.main(data)
finally:
    torch.set_num_threads = original

torch.manual_seed(9)
net = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
net.fc = nn.Identity()
net.requires_grad_(False)
head = nn.Linear(512, 4)
batch = torch.randn(4, 3, 64, 64)
control = torch.randn(2, 3, 64, 64)
net.eval()
before = net(control).clone()
params = {k: v.clone() for k, v in net.named_parameters()}
buffers = {k: v.clone() for k, v in net.named_buffers()}
saved_head = head.weight.detach().clone()
opt = torch.optim.SGD(head.parameters(), lr=.01)
loss = nn.CrossEntropyLoss()(head(net(batch)), torch.arange(4))
loss.backward()
opt.step()
assert not torch.equal(head.weight, saved_head)
assert torch.equal(net(control), before)
assert all(torch.equal(v, buffers[k]) for k,v in net.named_buffers())
net.train()
with torch.inference_mode():
    net(batch)
net.eval()
changes = sum(not torch.equal(v,buffers[k]) for k,v in net.named_buffers())
delta = (net(control) - before).abs().max().item()
assert changes and delta and all(torch.equal(v, params[k]) for k,v in net.named_parameters())
print("fixed eval: unchanged weights, buffers, embeddings; head learned. frozen train:",
      changes, "buffers changed, held-out eval embedding max delta", delta, flush=True)

md = (repo / "content/ch14/04-cnn.md").read_text()
code = next(code for code in re.findall(r"```python static\n(.*?)\n```", md, re.S)
            if "for epoch in range(25)" in code)
os.chdir(data)
exec(compile(code, "ch14/04-cnn.md", "exec"), {})
