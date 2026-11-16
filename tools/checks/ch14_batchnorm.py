"""Executable frozen-backbone/BatchNorm probe; no pretrained download is needed."""
import torch
from torch import nn

torch.manual_seed(42)
body=nn.Sequential(nn.Linear(4,4),nn.BatchNorm1d(4),nn.ReLU())
head=nn.Linear(4,2)
model=nn.Sequential(body,head)
for p in body.parameters():p.requires_grad=False
weights={k:v.clone() for k,v in body.named_parameters()}
buffers={k:v.clone() for k,v in body.named_buffers()}
head_before=head.weight.clone()
optimizer=torch.optim.SGD(head.parameters(),lr=.1)
model.train();body.eval()  # after every global train(), restore the frozen body's mode
loss=nn.CrossEntropyLoss()(model(torch.randn(8,4)),torch.randint(0,2,(8,)))
loss.backward();optimizer.step()
assert all(torch.equal(v,weights[k]) for k,v in body.named_parameters())
assert all(torch.equal(v,buffers[k]) for k,v in body.named_buffers())
assert not torch.equal(head.weight,head_before)
model.train();model(torch.randn(8,4))
assert any(not torch.equal(v,buffers[k]) for k,v in body.named_buffers())
print('OK frozen body eval preserves weights+BatchNorm buffers; head learns; global train alone changes buffers')
