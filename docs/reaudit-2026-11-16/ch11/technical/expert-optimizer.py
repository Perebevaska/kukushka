"""Expectation: an all-unregistered network gives Adam an empty parameter sequence."""
import torch
from torch import nn

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
for registered in (False, True):
    model = nn.Module()
    layers = [nn.Linear(2, 4), nn.Linear(4, 1)]
    model.layers = nn.ModuleList(layers) if registered else layers
    print(torch.__version__, registered, sum(p.numel() for p in model.parameters()))
    try:
        torch.optim.Adam(model.parameters())
        print('Adam constructed')
    except ValueError as exc:
        print(type(exc).__name__, exc)
