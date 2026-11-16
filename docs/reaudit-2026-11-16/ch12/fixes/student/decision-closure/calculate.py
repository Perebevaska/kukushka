from pathlib import Path
import json,csv,math,hashlib
D=Path(__file__).parent
PREV=D.parent/'retest'
rows=list(csv.DictReader((PREV/'native-august-predictions.csv').open()))
work=[r for r in rows if r['work']=='True']
assert len(rows)==744 and len(work)==496
summary={'rmse_denominator_hours':len(rows),'staffing_denominator_work_hours':len(work),'work_window':'07:00–22:00 включительно','plans':{}}
for name,column in [('модель','model'),('ориентир','baseline'),('квантиль','quantile')]:
    rmse=math.sqrt(sum((float(r['fact'])-float(r[column]))**2 for r in rows)/len(rows))
    deficit=extra=short=covered=0
    for r in work:
        y=float(r['fact']);p=float(r[column])
        need=max(1,math.ceil(y/6));plan=max(1,math.ceil(p/6))
        deficit+=max(need-plan,0);extra+=max(plan-need,0)
        short+=plan<need;covered+=p>=y
    summary['plans'][name]={'rmse_all744':rmse,'deficit_barista_hours':deficit,'extra_barista_hours':extra,'short_work_hours':short,'short_share_work':short/len(work),'coverage_work_hours':covered,'coverage_share_work':covered/len(work),'cost_3_1':3*deficit+extra}
transfer=[]
for capacity in [6,5]:
    needed=[max(1,math.ceil(y/capacity)) for y in [13,0,11]]
    for count in [2,3]:
        deficit=sum(max(n-count,0) for n in needed)
        extra=sum(max(count-n,0) for n in needed)
        transfer.append({'capacity':capacity,'plan_each_hour':count,'needed':needed,'deficit_barista_hours':deficit,'extra_barista_hours':extra,'deficit_price':180,'extra_price':100,'total_cost':180*deficit+100*extra})
(D/'csv-denominators.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(D/'capacity-calculation.json').write_text(json.dumps(transfer,ensure_ascii=False,indent=2))
# Проверка сохранности обеих прежних заморозок без их изменения
preserve=[]
for root in [Path('docs/reaudit-2026-11-16/ch12/student'),PREV]:
    manifest=json.loads((root/'SHA256SUMS.json').read_text())
    bad=[name for name,h in manifest.items() if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h]
    preserve.append({'directory':str(root),'files':len(manifest),'mismatches':bad})
(D/'previous-freezes-check.json').write_text(json.dumps(preserve,ensure_ascii=False,indent=2))
print(json.dumps({'csv':summary,'transfer':transfer,'preservation':preserve},ensure_ascii=False,indent=2))
