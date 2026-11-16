"""Independent arithmetic, temporal split and acceptance checks using the named source files."""
from pathlib import Path
import csv
import json
from datetime import datetime, timedelta
from statistics import mean, pstdev

root=Path(__file__).resolve().parent.parent
def read_csv(path):
    with path.open() as f: return list(csv.DictReader(f))
d=read_csv(root/'technical/data-baseline/catering_leads.csv')
d.sort(key=lambda r:(r['created'],r['lead_id']))
dates=[datetime.fromisoformat(r['created']) for r in d]
cut=dates[-750]
train=[r for r,dt in zip(d,dates) if dt+timedelta(days=30)<cut]
hold=d[-750:]
truth={r['lead_id']:int(r['converted']) for r in hold}
ranking=read_csv(root/'student/final_ranking.csv')
ranked=[r['lead_id'] for r in sorted(ranking,key=lambda r:(-float(r['score']),r['lead_id']))]
rule=sorted(r['lead_id'] for r in hold if int(r['repeat_client'])==1 or r['channel']=='рекомендация')
model=ranked[:len(rule)]
m,r=set(model),set(rule)
summary={'rows':len(d),'unique_ids':len(set(x['lead_id'] for x in d)),'split':[len(train),len(d)-len(train)-len(hold),len(hold)],'first_final':str(cut),'all_final_ready':str(max(dates)+timedelta(days=30)),'fin_contracts':sum(truth.values()),'budget':len(rule),'recovered_rounded_budget':int(round(len(rule)/len(hold),3)*len(hold)),'model_hits':sum(truth[i] for i in m),'rule_hits':sum(truth[i] for i in r),'overlap':[len(m&r),sum(truth[i] for i in m&r)],'only_model':[len(m-r),sum(truth[i] for i in m-r)],'only_rule':[len(r-m),sum(truth[i] for i in r-m)],'last_ids':[model[-1],rule[-1],ranked[224]],'model_top30_hits':sum(truth[i] for i in ranked[:225]),'mean_leaf_p':mean([.4,.4,.9]),'hard_vote_share':1/3,'half_tie_predict_first_class':0,'half_tie_threshold':int(.5>=.5),'bonus_margin_1000_then_500':[.3*1000-200,.3*500-200],'break_even':300/1200,'incremental_ev_at_03':.3*1200-300}
summary['mixed_leaves_equal_by_chance']={'probabilities':[.2,.8], 'mean':mean([.2,.8]), 'hard_vote_share':mean([0,1])}
summary['finite_random_scores']={'positive_score':.7,'negative_score':.3,'threshold':.5,'TPR':int(.7>=.5),'FPR':int(.3>=.5)}
dev=[.78,.84,.81,.87]; a=[v+.002 for v in dev];b=a[::-1]
summary['paired_sd_example']={'baseline_sd':pstdev(dev),'candidate_sd_both': [pstdev(a),pstdev(b)],'means':[mean(a),mean(b)],'paired_deltas':[list(map(lambda x:round(x[0]-x[1],3),zip(a,dev))),list(map(lambda x:round(x[0]-x[1],3),zip(b,dev)))]}
devices=[('D01',.95,.10,1),('D02',.90,.40,0),('D03',.80,.40,1),('D04',.70,.40,0),('D05',.60,.50,1),('D06',.50,.60,0),('D07',.40,.70,1),('D08',.40,.80,0),('D09',.40,.90,0),('D10',.20,1.,1)]
summary['repair']=[[(rank:=(sorted(devices,key=lambda x:(-x[i],x[0]))[:7]))[-1][0],sum(x[-1] for x in rank)] for i in [1,2]]
summary['repair_total_faults']=sum(x[-1] for x in devices)
assert summary['split']==[1869,381,750] and summary['model_hits']==64 and summary['rule_hits']==57 and summary['fin_contracts']==94
assert summary['overlap']==[93,47] and summary['repair']==[['D07',4],['D02',3]]
(root/'fixes/review-facts.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
