"""Hash/chronology reconciliation only; independent ML replay belongs to business role."""
from pathlib import Path
import datetime,hashlib,json
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def time(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
o={'scope':'stdlib SHA and disclosed chronology only; full pixel/model replay independently performed by business role','freezes':{}}
for name,root in [('initial',D/'student'),('predictions',D/'fixes/student/holdout-predictions'),('evaluation',D/'fixes/student/holdout-evaluation')]:
 m={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (root/'SHA256SUMS').read_text().splitlines() if s.strip()};assert all(sha(root/n)==v for n,v in m.items());o['freezes'][name]={'files':len(m),'manifest_sha256':sha(root/'SHA256SUMS'),'all_match':True}
pred=D/'fixes/student/holdout-predictions';dis=read(D/'technical/audit-holdout-private/labels-disclosure.json');f=read(pred/'freeze.json');pol=read(D/'student/freeze-before-day2.json');gen=read(D/'technical/audit-holdout-private/generation.json');b=read(D/'fixes/business-independent.json')
assert time(pol['utc'])<time(f['utc'])<time(dis['released_at']);assert not f['labels_available'];assert dis['frames_only_before_predictions'];assert dis['prediction_manifest_sha256']==sha(pred/'SHA256SUMS');assert gen['seed']==14016;assert b['matching_predictions']==732 and b['matching_signals']==21
assert o['freezes']['initial']['files']==59 and o['freezes']['predictions']['files']==10 and o['freezes']['evaluation']['files']==14
o.update({'seed':14016,'chronology':{'policy':pol['utc'],'prediction_freeze':f['utc'],'label_release':dis['released_at'],'strictly_ordered':True},'business_independent_replay':{'source':'fixes/business-independent.json','sha256':sha(D/'fixes/business-independent.json'),'prediction_matches':b['matching_predictions'],'signal_matches':b['matching_signals'],'holdout':b['holdout'],'limitation':'one new realization of same synthetic camera generator, not a new physical camera'},'published_NPZ_sha_match':b['published_npz_match']})
(D/'coordination-holdout.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(json.dumps(o,ensure_ascii=False))
