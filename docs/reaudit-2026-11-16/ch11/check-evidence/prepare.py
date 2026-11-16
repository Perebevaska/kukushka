"""Freeze literal programs before executing any of them. Does not alter course sources."""
import json,hashlib,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
items=json.loads((HERE/'before-tasks.json').read_text()); tasks={i['lesson']+'/'+i['id']:i for i in items};rows=[]
def sol(l,t):return tasks[l+'/'+t]['solution']
def add(l,t,desc,code,expected,group='new',**extra):
 rows.append(dict(id=f'C{len(rows)+1:02}',lesson=l,task=t,description=desc,code=code,expected=expected,group=group,code_sha256=hashlib.sha256(code.encode()).hexdigest(),**extra))
for r in map(json.loads,(ROOT/'tools/checks/fixtures/reaudit_20261115.jsonl').read_text().splitlines()):
 if r['lesson'].startswith('ch11/'):add(r['lesson'],r['task'],r['description'],r['code'],r['expected'],'historical-original',migration='none; visible contract unchanged')
l='ch11/04b-softmax';s=sol(l,'batches')
# Exact historical additional code, checked against the old evidence hashes below.
add(l,'batches','no shuffle',s.replace('rng.permutation(len(y))','np.arange(len(y))'),False,'historical-additional')
for r in json.loads((ROOT/'tools/checks/fixtures/batches_20261115_refinement.json').read_text())['programs']:
 add(r['lesson'],r['task'],r['description'],r['code'],r['expected'],'historical-additional')
add(l,'batches','labels shifted independently of feature rows',s.replace('yield X[idx], y[idx]','yield X[idx], y[np.roll(idx, 1)]'),False)
add(l,'batches','last incomplete batch dropped',s.replace('range(0, len(y), size)','range(0, len(y)-size+1, size)'),False)
oracle='''
for nf in (1,5):
 for n, size in ((13,6),(7,1)):
  a=np.arange(n*nf).reshape(n,nf);b=np.arange(n)*11-4
  r=np.random.default_rng(29);ref=np.random.default_rng(29)
  for epoch in range(2):
   got=list(batches(a,b,size,r));order=ref.permutation(n)
   assert np.array_equal(np.concatenate([z[0] for z in got]),a[order])
   assert np.array_equal(np.concatenate([z[1] for z in got]),b[order])
'''
add(l,'batches','alternative np.take, 1/5 features, sizes1/6, 2 epochs',s.replace('yield X[idx], y[idx]','yield np.take(X, idx, axis=0), np.take(y, idx, axis=0)')+oracle,True)
l='ch11/05-project';s=sol(l,'blur-transfer')
# Include a concrete omitted error, using only labels returned by the public reveal.
outside='''
outside=np.flatnonzero(errors & ~np.isin(np.arange(len(errors)),queue))
missed_example_position=int(outside[0]) if len(outside) else None
print("missed_example_position",missed_example_position)
'''
s+=outside
add(l,'blur-transfer','margin, Russian caption, concrete missed error',s,True)
eng=s.replace('))[0])', '))[1])').replace('Позиция {i}; истина', 'position={i}; truth=').replace('; прогноз','; prediction=').replace('; p=', '; confidence=')
eng=eng.replace('две наиболее вероятные цифры близки','максимальная вероятность мала').replace('rule_name="margin"','rule_name="confidence"').replace('score=top[:,-1]-top[:,-2]','score=top[:,-1]')
add(l,'blur-transfer','confidence, English caption, another confident error',eng,True)
add(l,'blur-transfer','different validation image shown',s.replace('ax.imshow(validation["images"][i]', 'ax.imshow(validation["images"][(i+1)%len(p)]'),False)
add(l,'blur-transfer','selected image overwritten by another before drawing',s.replace('fig,ax=plt.subplots()','validation["images"][i]=validation["images"][(i+1)%len(p)]\nfig,ax=plt.subplots()'),False)
add(l,'blur-transfer','blind probabilities accidentally overwritten before selection',s.replace('top=np.sort(blind["proba"],axis=1)','blind["proba"][:]=np.eye(10)[np.zeros(len(blind["proba"]),dtype=int)]\ntop=np.sort(blind["proba"],axis=1)'),False)
add(l,'blur-transfer','caption truth and prediction swapped',s.replace("истина {example['truth']}; прогноз {example['prediction']}","истина {example['prediction']}; прогноз {example['truth']}"),False)
add(l,'blur-transfer','queue reversed after reveal',s+'\nqueue=queue[::-1]',False)
add(l,'blur-transfer','reveal before image shown',s.replace('ax.imshow(validation["images"][i],cmap="gray")',''),False,expected_error=True)
add(l,'blur-transfer','wrong caught count',s+'\ncaught_errors += 1',False)
add(l,'blur-transfer','wrong truth in example',s.replace('fig,ax=plt.subplots()','example["truth"]=(example["truth"]+1)%10\nfig,ax=plt.subplots()'),False,expected_error=True)
add(l,'blur-transfer','reported missed position actually belongs to queue',s.replace('int(outside[0]) if len(outside) else None','int(queue[0])'),False)
add(l,'blur-transfer','validation target overwritten to match fabricated example',s.replace('fig,ax=plt.subplots()','validation["target"][i]=next(k for k in range(10) if k not in (example["truth"],example["prediction"]))\nexample["truth"]=int(validation["target"][i])\nfig,ax=plt.subplots()'),False)
# Ordinary cards: all requested numerical arrays/fields/figures below have a positive and negative case.
l='ch11/04-pytorch';s=sol(l,'float32')
add(l,'float32','correct float32 cast',s,True)
add(l,'float32','one X32 cell corrupted after summaries',s+'\nX32[0,0]+=10',False)
l='ch11/03-mlp';s=sol(l,'loss-curve')
add(l,'loss-curve','actual loss curve and summary scalars',s,True)
add(l,'loss-curve','loss curve one interior value wrong, summaries unchanged',s+'\ncurve[10]+=10',False)
s=sol(l,'epoch-gap')
add(l,'epoch-gap','actual train and validation AUC series',s,True)
add(l,'epoch-gap','train AUC series one interior epoch wrong',s+'\nauc_train[50]=0.0',False)
l='ch11/02b-graph';s=sol(l,'clip-norm')
add(l,'clip-norm','norm-preserving clip vector and scalars',s,True)
add(l,'clip-norm','clipped vector direction wrong with same norm',s+'\nc=-c',False)
l='ch11/01-neuron';s=sol(l,'collapse')
add(l,'collapse','both linear-layer array results correct',s,True)
add(l,'collapse','two_layers corrupted, equivalent W and booleans unchanged',s+'\ntwo_layers[0,0]+=10',False)
l='ch11/05-project';s=sol(l,'look')
add(l,'look','mean images via normalized imshow',s.replace('ax.imshow(mean_imgs[k]', 'ax.imshow(mean_imgs[k]/16'),True)
add(l,'look','one required mean image corrupted after drawing',s+'\nmean_imgs[4,2,2]+=1',False)
s=sol(l,'errors')
add(l,'errors','actual confusion matrix and stable queues',s,True)
add(l,'errors','one confusion-matrix cell wrong, summaries correct',s+'\ncm[0,0]+=1',False)
assert len(rows)==34,len(rows)
old=[json.loads(x) for x in (ROOT/'docs/course-improvements/reaudit/fixes/technical-results.jsonl').read_text().splitlines()]
sha={x['code_sha256'] for x in old if x['task'].startswith('ch11/')}
assert all(x['code_sha256'] in sha for x in rows[:5])
(HERE/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'expected-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in rows],ensure_ascii=False,indent=2))
(HERE/'frozen.sha256').write_text(''.join(hashlib.sha256((HERE/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in ['programs.jsonl','expected-before-execution.json','before-tasks.json','visible-contracts.json']))
data=HERE/'data-baseline';data.mkdir(exist_ok=True)
for name in {f for i in items for f in i['files']}:shutil.copyfile(ROOT/'site/data'/name,data/name)
print('Frozen',len(rows),'programs; five exact historical code hashes, no migrations')
