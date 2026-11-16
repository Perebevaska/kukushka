import numpy as np
import torch
from torch import nn
from sklearn.model_selection import train_test_split

torch.set_num_threads(2)
torch.manual_seed(0)
d = np.load("site/data/showcase.npz")
X = torch.tensor(d["X"] / 255, dtype=torch.float32).unsqueeze(1)   # (2000, 1, 32, 32): канал — второе измерение
y = torch.tensor(d["y"])
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=d["y"])

net = nn.Sequential(
    nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 16 × 16 × 16
    nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 32 × 8 × 8
    nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
    nn.AdaptiveMaxPool2d(1), nn.Flatten(),                                    # глобальный пулинг → 64 числа
    nn.Linear(64, 4),
)
print("параметров:", sum(p.numel() for p in net.parameters()))

opt = torch.optim.Adam(net.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()
for epoch in range(25):
    net.train()
    for idx in torch.tensor(tr)[torch.randperm(len(tr))].split(64):   # мини-батчи по 64
        xb = X[idx]
        if torch.rand(1) < 0.5:
            xb = xb.flip(-1)                                          # аугментация: отражение
        loss = loss_fn(net(xb), y[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        acc = (net(X[te]).argmax(1) == y[te]).float().mean().item()
    print(f"эпоха {epoch + 1}: точность на тесте {acc:.3f}")

with torch.no_grad():                                                 # стресс-тест, как в уроке «Модели на пикселях»
    for name, Z in {"сдвиг на 4": torch.roll(X[te], 4, dims=3), "тусклее на 30 %": X[te] * 0.7}.items():
        print(name, round((net(Z).argmax(1) == y[te]).float().mean().item(), 3))