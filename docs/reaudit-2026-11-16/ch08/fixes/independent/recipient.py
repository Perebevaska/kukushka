"""Read colleague-facing outputs and recompute ID, policy and cash identities.

Invoke with the delivered project directory, public data directory, and output JSON.
This uses only the Python standard library. It never opens a course answer key.
"""
import csv,hashlib,json,math,sqlite3,sys
from pathlib import Path
from statistics import median,NormalDist
folder,data,target=map(Path,sys.argv[1:])
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))
def read(path):
    return json.loads(path.read_text())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
db=sqlite3.connect(data/'final1.db')
sites={r['site_id']:r for r in rows(data/'sites.csv')}
directory=folder/'sites-artifacts'
chosen=rows(directory/'chosen-sites.csv')
site_summary=read(directory/'summary.json')
risk=rows(directory/'risk.csv')
col_city=next(iter(risk[0]))
passing=[r for r in risk if float(r['p_loss'])<=.025]
choice=max(passing,key=lambda r:float(r['mean']))[col_city] if passing else None
site_checks={'choice_by_risk_csv':choice,'choice_in_summary':site_summary['choice'],
             'chosen_sites':len(chosen),'unique_chosen':len({r['site_id'] for r in chosen}),
             'wrong_city_or_estimate':sum(sites[r['site_id']]['city']!=choice or
                 float(sites[r['site_id']]['profit_k'])!=float(r['profit_k']) for r in chosen),
             'sum_estimates_minus_install_k':sum(float(r['profit_k'])-140 for r in chosen),
             'choice_with_risk_toy':max(((-1,.025,'A'),(200,.02501,'B'),(-3,.02,'C')),key=lambda r:(r[1]<=.025,r[0]))[2]}
subscription=folder/'subscription-artifacts'
decision=rows(subscription/'candidate-decisions.csv')
selected=[r for r in decision if r['send'].lower()=='true']
summary=read(subscription/'summary.json')
curve=rows(subscription/'policy-curve.csv')
t=summary['threshold']
guests={r[0]:r[1:] for r in db.execute("""select g.guest_id,g.reg_date,s.city,g.source,
  julianday('2026-07-01')-julianday(max(o.ordered_at)),count(o.order_id)
  from guests g join orders o using(guest_id) join shops s on s.shop_id=g.home_shop_id
  where o.ordered_at<'2026-07-01' and g.guest_id not in (select guest_id from pilot)
  group by g.guest_id""")}
ids={i for i,row in guests.items() if row[0]<'2026-06-01'}
returned={r['guest_id'] for r in decision}
policy=max((r for r in curve if int(r['sent'])<=300 and int(r['control_n'])>=20 and float(r['incremental'])>=0),key=lambda r:(float(r['incremental']),-float(r['threshold'])))
n=len(selected)
expected_buyers=sum(float(r['p']) for r in selected)
organic_buyers=summary['organic_buyers']
wrong_send=[r['guest_id'] for r in decision if (float(r['p'])>t)!=(r['send'].lower()=='true')]
cohort={'expected':len(ids),'received':len(decision),'missing':len(ids-returned),
        'extra':len(returned-ids),'repeated':len(decision)-len(returned),
        'wrong_selected':sorted(r['guest_id'] for r in selected if r['guest_id'] not in ids),
        'incorrect_city':sum(guests[r['guest_id']][1]!=r['city'] for r in decision),
        'cuts':sorted(set(r['cutoff'] for r in decision))}
subscription_checks=dict(t_from_training_under_original_bound=float(policy['threshold']),
    threshold=t,capacity=summary['capacity'],cap_binds=n==summary['capacity'],
    selected=n,decisions_disagree_with_proba=wrong_send,
    purchases_from_scores=expected_buyers,observed_rate_organic_in_summary=organic_buyers/n,
    forecast_margin_from_scores_and_reported_organic=1600*(expected_buyers-organic_buyers)-150*n,
    forecast_all_from_scores_and_control=1600*(sum(float(r['p']) for r in decision)-len(decision)*15/600)-150*len(decision),
    contacts_cost=150*n,app_share=sum(guests[r['guest_id']][2]=='приложение' for r in selected)/n,
    recent7=sum(guests[r['guest_id']][3]<=7 for r in selected),
    median_recency=median(guests[r['guest_id']][3] for r in selected))
db_facts={'pilot':[list(r) for r in db.execute("select group_name,count(distinct guest_id),sum(bought),max(reg_date) from pilot join guests using(guest_id) group by group_name")],
    'last_order':db.execute("select max(ordered_at) from orders").fetchone()[0],
    'multiple_redemptions':db.execute("""select count(*) from (select 1 from order_items i join orders o using(order_id)
       where i.price=0 group by o.guest_id,date(o.ordered_at) having sum(i.qty)>1)""").fetchone()[0],
    'pre_registration_complaints':db.execute("select count(*) from complaints c join guests g using(guest_id) where date(c.created_at)<g.reg_date").fetchone()[0]}
def newcombe(n1,b1,n0,b0):
    z=NormalDist().inv_cdf(.975)
    def interval(n,b):
        p=b/n
        mid=(p+z*z/(2*n))/(1+z*z/n)
        dist=z/(1+z*z/n)*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
        return mid-dist,mid+dist
    p,q=b1/n1,b0/n0
    l1,h1=interval(n1,b1)
    l0,h0=interval(n0,b0)
    return [n1*(1600*(p-q-math.hypot(p-l1,h0-q))-150),n1*(1600*(p-q+math.hypot(h1-p,q-l0))-150)]
letters={}
for tag,n,b,m,f in [('A',100,18,80,4),('B',200,42,100,10),('B_changed',200,42,100,9),('mass',1800,198,600,15)]:
    letters[tag]=dict(gross=1600*b-150*n,effect=(b-n*f/m)*1600-150*n,interval=newcombe(n,b,m,f))
letters['B_switch_rate']=(letters['B']['gross']-letters['A']['effect'])/(1600*200)
notebooks={}
for path in sorted(folder.glob('*-project.ipynb')):
    nb=read(path); cells=[c for c in nb['cells'] if c['cell_type']=='code']
    notebooks[path.name]={'sha256':digest(path),'counts':[c['execution_count'] for c in cells],
        'errors':[o['ename'] for c in cells for o in c['outputs'] if o.get('output_type')=='error']}
target.write_text(json.dumps(dict(cohort=cohort,subscription=subscription_checks,sites=site_checks,summary=summary,
      notebooks=notebooks,db=db_facts,letters=letters,data_sha256={n:digest(data/n) for n in ('final1.db','sites.csv')},
      deliverable_sha256={str(p.relative_to(folder)):digest(p) for p in sorted(folder.glob('*artifacts/*')) if p.is_file()}),ensure_ascii=False,indent=2)+'\n')
