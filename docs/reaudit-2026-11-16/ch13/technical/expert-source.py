"""Read only. Run from the repository root with Python's standard library."""
import ast
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
DATA = Path(__file__).resolve().parent / 'data-baseline'
chapter = ROOT / 'content/ch13'
def read(name):
    with (DATA / (name + '.csv')).open() as handle:
        return list(csv.DictReader(handle))
def unique(rows, field):
    mapping = {row[field]: row for row in rows}
    assert len(mapping) == len(rows)
    return mapping
def summary(rows):
    return {'rows': len(rows), 'missing': dict(Counter(k for r in rows for k,v in r.items() if not v))}
def run_case(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        return f'{type(exc).__name__}: {exc}'

train, new, gold, labels, anchors, lemmas = (read(f) for f in ('reviews_text','reviews_new','reviews_new_gold','review_labels','review_gold','review_lemmas'))
training, reviews = unique(train,'review_id'), unique(new,'review_id')
random.Random(41).shuffle(gold)
n_gold = unique(gold, 'review_id')
assert set(reviews) == set(n_gold)
summary_rows = {}
for boundary in ('2026-10-01', '2026-10-05'):
    periods = defaultdict(lambda:[0,0])
    for rid,r in reviews.items():
        if r['shop_id'] == 'KZN-2':
            target = int(n_gold[rid]['complaint'])
            period = 'после' if r['date'] >= boundary else 'до'
            periods[period][0] += 1
            periods[period][1] += target
    summary_rows[boundary] = periods
wide = defaultdict(dict)
for r in labels:
    assert r['annotator'] not in wide[r['review_id']]
    wide[r['review_id']][r['annotator']] = r['label']
assert all(len(r)==3 for r in wide.values())
anchor = {r['review_id']:r['label'] for r in anchors}
matches = {who: sum(wide[rid][who] == v for rid,v in anchor.items()) for who in ('аня','борис','вика')}
agreement = {}
for a,b in [('аня','борис'),('аня','вика'),('борис','вика')]:
    x, y = (Counter(r[who] for r in wide.values()) for who in (a,b))
    po = sum(r[a]==r[b] for r in wide.values())/len(wide)
    pe = sum(x[k]*y[k] for k in x)/len(wide)**2
    agreement[a+'−'+b] = {'po':po, 'kappa':(po-pe)/(1-pe)}
vocab = Counter(w for r in train for w in re.findall('[а-яё]+', r['text'].lower()))
assert vocab == {r['word']:int(r['count']) for r in lemmas}
lesson = (chapter / '04c-llm.md').read_text()
prompt = re.search(r'PROMPT = """(.*?)"""',lesson,re.S)[1]
n = len(new)
tokens_in = (len(prompt)*n+sum(len(row['text']) for row in new))/3
price = .3*tokens_in/1000 + 1.5*n*20/1000
diff = (38-24)/200
se = math.sqrt((38+24-200*diff**2)/(200*199))
sdk = {}
harness = ast.parse((ROOT / 'site/assets/harness.py').read_text())
src = next(st.value.value for st in harness.body if isinstance(st,ast.Assign) and getattr(st.targets[0], 'id', '')=='_LOCAL_LLM_SRC')
scope = {}
exec(src,scope)
sample = '{"sentiment":"negative","topic":"еда"}'
for label,payload in [('complete',{'choices':[{'finish_reason':'stop','message':{'content':sample}}]}),('empty_choices',{'choices':[]}),('length',{'choices':[{'finish_reason':'length','message':{'content':sample}}]})]:
    scope['_request'] = lambda *args: payload
    sdk['browser_'+label] = run_case(scope['ask'],'отзыв',model='fixture')
fn = re.search(r'(def label\(text\):.*?)(?=\nprint\()',lesson,re.S)[1]
parser = re.search(r'(def parse\(answer\):\n    bad = .*?)(?=\nparsed =)',lesson,re.S)[1]
namespace = {'PROMPT':prompt,'MODEL':'fixture','json':json,'TOPICS':['кофе','еда','обслуживание','доставка','цена','атмосфера']}
exec(fn,namespace)
exec(parser,namespace)
for label, blocks, reason in [('complete',[SimpleNamespace(type='text',text=sample)],'end_turn'),('empty',[],'end_turn'),('length',[SimpleNamespace(type='text',text=sample)],'max_tokens')]:
    fake = SimpleNamespace(content=blocks, stop_reason=reason)
    namespace['client'] = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs:fake))
    raw = namespace['label']('отзыв')
    sdk['cloud_'+label]=[raw,run_case(namespace['parse'],raw)]
local_predicate = next(s for s in lesson.splitlines() if s.startswith('    ok = isinstance')).strip()[5:]
sdk['widget_nonstring_topic'] = run_case(lambda:eval(local_predicate,{'ans':{'topic':['еда'],'sentiment':'negative'}, 'TOPICS':set(namespace['TOPICS'])}))
result = {
 'source_stats': {name:summary(rows) for name,rows in [('train',train),('new',new),('new_gold',gold),('labels',labels),('anchors',anchors),('lemmas',lemmas)]},
 'new_dates':sorted({r['date'] for r in new})[::60], 'repeated_text_rows':{k:len(rows)-len({r['text'] for r in rows}) for k,rows in [('train',train),('new',new)]},
 'KZN-2_by_id':summary_rows,'source':dict(Counter(r['label_source'] for r in gold)),
 'anchor_copies':sum(training[k]['topic']==v for k,v in anchor.items()),'anchor_hits_out_of_50':matches,
 'label_agreement':agreement,'no_majority':sum(len(set(r.values()))==3 for r in wide.values()),
 'vocabulary':len(vocab),'tokens':vocab.total(), 'review_topic':dict(Counter(r['topic'] for r in train)),
 'cost':{'tokens_in':round(tokens_in),'tokens_out':20*n,'rubles':round(price,1),'prompt_share':round(len(prompt)*n/(3*tokens_in),3)},
 'paired_from_disagreements':{'delta':diff,'lower':diff-1.96*se,'upper':diff+1.96*se},
 'offline_fixture_results':sdk}
print(json.dumps(result,indent=2,ensure_ascii=False))
