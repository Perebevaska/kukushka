from pathlib import Path
import json
import numpy as np
import pymorphy3
D=Path(__file__).parent.resolve()
n=json.loads((D/'ch13-transformers.ipynb').read_text())
ns={'np':np,'Path':Path,'json':json}
import hashlib,time
ns.update(hashlib=hashlib,time=time,CACHE=D/'extra-cache',BATCH_SIZE=32)
c=next(c for c in n['cells'] if c['cell_type']=='code' and 'def fingerprint' in ''.join(c['source']))
exec(''.join(c['source']),ns)
import pandas as pd
texts=pd.read_csv(D/'data/reviews_text.csv').text.tolist()
def must_not_encode(texts):raise RuntimeError('Cache miss: unexpected encoding')
E=ns['embed_cached'](texts,must_not_encode,model='cointegrated/rubert-tiny2',max_length=128,pooling='mean')
print('Second cache read shape',E.shape,'finite',np.isfinite(E).all())
a=ns['fingerprint'](texts,model='cointegrated/rubert-tiny2');b=ns['fingerprint']([texts[0]+'!',*texts[1:]],model='cointegrated/rubert-tiny2');print('Fingerprint changes after text edit',a!=b)
m=pymorphy3.MorphAnalyzer()
for t in ['чай матча','после матча']:
 print(t,'->',' '.join(m.parse(w)[0].normal_form for w in t.split()))
print('Both match surface known?',m.word_is_known('матча'),'global replacement матч→матча would damage sports context')
