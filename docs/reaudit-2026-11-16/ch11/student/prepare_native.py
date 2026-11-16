import json
from pathlib import Path
D=Path(__file__).parent;S=Path('/private/tmp/kuch11round/student')
n=json.loads((S/'extra/ch11-pytorch-tabular.ipynb').read_text())
for c in n['cells']:
 if c['cell_type']=='code':
  c['outputs']=[];c['execution_count']=None
  s=''.join(c['source'])
  if 'import torch' in s:
   s=s.replace('import torch','import torch\ntorch.set_num_threads(1)\ntorch.set_num_interop_threads(1)')
   begin=s.index('DATA = next');end=s.index('print("pandas"',begin)
   s=s[:begin]+"DATA = Path('/private/tmp/kuch11round/student/data')\ndevice = 'cpu'\n"+s[end:]
  if 'experiments = {' in s:s=s.replace('experiments = {','experiments = {\n    "student 16": dict(hidden=(16,)),')
  c['source']=s
n['cells'].insert(0,{'cell_type':'markdown','metadata':{},'source':'# Собственный прогон extra\nДо запуска: Q1 пройти цикл на PyTorch и проверить передачу. Q2 использую выданный extra, заменяю выбор GPU на CPU и путь только на входной CSV. Q3 ожидаю smoke около1→почти0, выбор по validation,16 одинаковых прогнозов после загрузки; свой эксперимент hidden16. Авторские текстовые числа сохранены как входная теория, фактические результаты в outputs.'})
def code(s):return dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None)
n['cells'].append(code('''# Дополнительные упражнения урока 04: autograd, накопление, память, сохранение.
w=torch.tensor(5.,requires_grad=True)
km=torch.tensor([1.,2.,3.,4.5,6.]);minutes=torch.tensor([18.,25.,34.,44.,55.])
((w*km-minutes)**2).mean().backward();g1=w.grad.item()
((w*km-minutes)**2).mean().backward();g2=w.grad.item()
w9=torch.tensor(9.,requires_grad=True);((w9*km-minutes)**2).mean().backward()
a=np.array([1.5,2.,3.]);shared=torch.from_numpy(a);copied=torch.tensor(a,dtype=torch.float32);a[0]=100.
print({'grad5':g1,'grad_twice':g2,'grad9':w9.grad.item(),'shared':shared[0].item(),'copied':copied[0].item()})
from sklearn.datasets import make_moons
mx,my=make_moons(400,noise=.2,random_state=0);mx=torch.tensor(mx,dtype=torch.float32);my=torch.tensor(my,dtype=torch.float32)
torch.manual_seed(0)
moons=nn.Sequential(nn.Linear(2,16),nn.ReLU(),nn.Linear(16,1));opt=torch.optim.SGD(moons.parameters(),lr=.5)
for _ in range(2000):
    opt.zero_grad();loss=nn.BCEWithLogitsLoss()(moons(mx).squeeze(1),my);loss.backward();opt.step()
torch.save(moons.state_dict(),'moons_student.pt')
moons2=nn.Sequential(nn.Linear(2,16),nn.ReLU(),nn.Linear(16,1));moons2.load_state_dict(torch.load('moons_student.pt',weights_only=True))
print('moons',loss.item(),torch.equal(moons(mx),moons2(mx)),sum(t.numel() for t in moons.state_dict().values()))
try:
    nn.Sequential(nn.Linear(2,32),nn.ReLU(),nn.Linear(32,1)).load_state_dict(torch.load('moons_student.pt',weights_only=True))
except RuntimeError as e: print('expected wrong architecture:',str(e).splitlines()[0])
'''))
n['cells'].append(code('''# Передача фактически выбранной сети без нового fit.
import joblib,json
Path('native_transfer').mkdir(exist_ok=True)
torch.save(models[best_name].state_dict(),'native_transfer/delivery_state.pt')
joblib.dump(scaler,'native_transfer/scaler.joblib')
metadata={'best_name':best_name,'architecture':architecture,'columns':X.columns.tolist(),'y_mean':float(y_mean),'y_std':float(y_std),'unit':'minutes','n_in':int(Xt_train.shape[1]),'device':'cpu','torch':torch.__version__}
Path('native_transfer/metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
X_val.iloc[:16].to_csv('native_transfer/control_features.csv',index=False)
pd.DataFrame({'prediction_minutes':before}).to_csv('native_transfer/control_predictions.csv',index=False)
log.to_csv('native_experiments.csv',index=False);summary.to_csv('native_summary.csv',index=False)
for name,hist in histories.items():hist.to_csv('native_history_'+name.replace('/','_')+'.csv',index=False)
print('SAVED',metadata,'control maxdiff',float(abs(before-after).max()))
'''))
(D/'native-extra.ipynb').write_text(json.dumps(n,ensure_ascii=False,indent=1))
