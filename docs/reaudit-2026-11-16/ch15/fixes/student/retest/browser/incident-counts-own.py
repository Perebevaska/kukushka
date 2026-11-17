"""Own light raw-log arithmetic; no model fitting or grading."""
import json
from collections import Counter
from pathlib import Path
path=Path('/private/tmp/kuch15round/student-retest/data/service_log.jsonl')
rows=[json.loads(s) for s in path.read_text().splitlines()]
daily={}
for r in rows:
 d=r['ts'][:10];daily.setdefault(d,Counter());daily[d]['all']+=1;daily[d][str(r['status'])]+=1
success32=[r for r in rows if r['client']=='app 3.2' and r['status']==200]
web_after=[r for r in rows if r['client']=='web' and r['ts']>='2026-11-07T18:02']
out={'daily':{d:dict(c) for d,c in daily.items()},'n_success32':len(success32),'success32_check_over3000':sum((r['payload'].get('avg_check') or 0)>3000 for r in success32),'web_after_n':len(web_after),'web_after_500':sum(r['status']==500 for r in web_after),'all_requests':len(rows)}
print(json.dumps(out,ensure_ascii=False,indent=2))
