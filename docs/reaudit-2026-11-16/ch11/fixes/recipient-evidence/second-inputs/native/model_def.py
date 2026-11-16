import torch
from torch import nn
class DeliveryNet(nn.Module):
    def __init__(self, n_in, hidden=(64, 32), p_drop=0.0, batchnorm=False):
        super().__init__()
        layers, prev = [], n_in
        for h in hidden:
            layers.append(nn.Linear(prev, h))
            if batchnorm:
                layers.append(nn.BatchNorm1d(h))
            layers.append(nn.ReLU())
            if p_drop > 0:
                layers.append(nn.Dropout(p_drop))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.body = nn.Sequential(*layers)
        for m in self.body[:-1]:
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                nn.init.zeros_(m.bias)

    def forward(self, x):
        return self.body(x).squeeze(1)

