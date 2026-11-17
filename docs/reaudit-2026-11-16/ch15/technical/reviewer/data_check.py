"""Independent, read-only inspection. Report anomalies at ID grain and their window footprint."""
import hashlib
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

here=Path(__file__).resolve().parent
repo=here.parents[4]
data=here.parent/"data-baseline"
db=data/"office.db"
con=sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)
query="""
WITH distinct_tickets AS (
 SELECT DISTINCT ticket_id, client_id, created_at, category FROM tickets
), joined AS (
 SELECT t.*, cl.created_at crm, ct.start_date start, ct.end_date end, cl.is_test FROM distinct_tickets t
 JOIN clients cl USING(client_id) JOIN contracts ct USING(client_id)
)
SELECT * FROM joined ORDER BY ticket_id
"""
con.row_factory=sqlite3.Row
rows=list(map(dict,con.execute(query)))
assert len(rows)==len({x['ticket_id'] for x in rows})
groups={'pre_crm':[],'crm_to_contract':[]}
for r in rows:
    if r["created_at"]<r["crm"]:groups["pre_crm"].append(r)
    elif r["created_at"]<r["start"]:groups["crm_to_contract"].append(r)
report={"office_sha":hashlib.sha256(db.read_bytes()).hexdigest(),"generator_sha":hashlib.sha256((repo/'tools/gen_final2.py').read_bytes()).hexdigest()}
for group,found in groups.items():
    result={"unique_tickets":len(found),"unique_clients":len({r['client_id'] for r in found}),"first":found[0],"impact":{}}
    for cut in ["2025-09-30","2025-12-31","2026-03-31","2026-06-30","2026-09-30"]:
        window=[r for r in found if not r["is_test"] and r["start"]<=cut and (not r["end"] or cut<r["end"]) and 0<=(date.fromisoformat(cut)-date.fromisoformat(r["created_at"])).days<90]
        result["impact"][cut]={"tickets":len(window),"offices":len({r["client_id"] for r in window}),"bill":sum(r["category"]=="счёт" for r in window)}
    report[group]=result
log=list(map(json.loads,(data/"service_log.jsonl").read_text().splitlines()))
d=defaultdict(Counter)
for r in log:d[r['ts'][:10]][r['status']]+=1
report["service"]={"first500":min(r['ts'] for r in log if r['status']==500),"first500_over_2pct":min(day for day,c in d.items() if c[500]/c.total()>.02),"first_any_error_over_2pct":min(day for day,c in d.items() if (c[422]+c[500])/c.total()>.02)}
shared=here.parent.parent/"judge/shared-input.csv"
report["judge_shared_sha"]=hashlib.sha256(shared.read_bytes()).hexdigest()
print(json.dumps(report,ensure_ascii=False,indent=2))
