"""Independent user programs for published chapter-eight contracts.

Each factory returns (name, public exercise id, expected grade, user code).
The starter is the learner's published starter. No reference solution is read.
"""
from textwrap import dedent

PROFIT = """def profit(send, y, gain=400, cost=200):
    return sum(gain if bought else -cost for sent,bought in zip(send,y) if sent)
"""
MONTH = """def month_report(p, threshold=.3):
    return dict(leads=len(p),mean_pred=round(sum(p)/len(p),3),above=round(sum(v>threshold for v in p)/len(p),3))
"""
PD = """def partial(model,X,col,grid):
    return [round(model.predict_proba(X.assign(**{col:k}))[:,1].mean(),3) for k in grid]
"""
GAINS = """import matplotlib.pyplot as plt
import numpy as np
order = np.argsort(-risk)
y = y_test.to_numpy()[order]
x = np.linspace(1/len(y),1,len(y))
fraction = y.cumsum() / y.sum()
at10 = round(float(fraction[len(y)//10-1]),3)
fig,ax = plt.subplots()
ax.set(xlabel="доля гостей с бонусом",ylabel="доля пойманных уходящих")
{series}
{baseline}
"""
MONEY = """
import numpy as np
from sklearn.model_selection import cross_val_predict
oof = cross_val_predict(best, X_train, y_train, cv=cv, method="predict_proba")[:,1]
best.fit(X_train,y_train)
ctrl = pilot.query("group_name == 'контроль'").merge(data,on="guest_id")
cp = best.predict_proba(ctrl[num+cat])[:,1]
curve_rows, effect_rows = [], []
for t in GRID:
    pick = oof > t
    n, b = int(pick.sum()),int(y_train.iloc[pick].sum())
    gross = 1600*b - 150*n
    group = ctrl.bought[cp>t]
    curve_rows.append(dict(threshold=t,buyers=b,sent=n,profit=gross))
    effect_rows.append(dict(threshold=t,organic_share=group.mean(),control_n=len(group),margin=gross - 1600*n*group.mean()))
curve = pd.DataFrame(curve_rows[::-1])
incr = pd.DataFrame(effect_rows).sample(frac=1,random_state=73)
best_t = THRESHOLD
test_pick=best.predict_proba(X_test)[:,1] > best_t
test_sent, test_buyers = int(test_pick.sum()), int(y_test.iloc[test_pick].sum())
test_profit, all_profit = 1600*test_buyers-150*test_sent,1600*y_test.sum()-150*len(y_test)
print(float(best_t),test_sent,test_buyers,test_profit,float(incr.loc[incr.threshold.sub(best_t).abs().idxmin(),'margin']))
"""
HONEST = """
best_t = best_t_incr = THRESHOLD
rest = rest.sort_values("guest_id",ascending=False)
rest["send"] = rest.p.gt(best_t)
n_send = int(rest.send.sum())
purchases = rest.loc[rest.send,"p"].sum()
hi = final.predict_proba(ctrl[num+cat])[:,1]>best_t
share = ctrl.bought[hi].mean()
organic = round(float(share),3)
exp_buyers = round(float(purchases),1)
naive_profit=round(1600*purchases-150*n_send)
honest_profit=round(1600*(purchases-n_send*share)-150*n_send)
honest_all=round(1600*(rest.p.sum()-len(rest)*ctrl.bought.mean())-150*len(rest))
print(float(best_t),len(rest),n_send,int(hi.sum()),int(ctrl.bought[hi].sum()),honest_profit,honest_all)
"""
def cases(tasks):
    def program(id_, tail):
        return tasks[id_].get('starter','')+'\n'+dedent(tail)
    for name,key,code,error in [
        ('cost','p-profit',PROFIT,PROFIT.replace('else -cost','else -200')),
        ('month-limit','p-monitor',MONTH,MONTH.replace('v>threshold','v>.3')),
        ('month-equality','p-monitor',MONTH,MONTH.replace('v>threshold','v>=threshold')),
        ('partial-column','p-pd',PD,PD.replace('{col:k}',"{'a':k}"))]:
        yield name+'-ok',key,True,code
        yield name+'-bad',key,False,error
    line='ax.plot(x,fraction)'
    dots='ax.plot(x,fraction,ls="none",marker="o",ms=2)'
    baseline='ax.plot([0,1],[0,1])'
    examples=[
        ('reverse',True,'ax.plot(x[::-1],fraction[::-1])',baseline),
        ('hidden-axes',False,line,baseline+'\nax.set_visible(False)'),
        ('transparent-label',False,line,baseline+'\nax.xaxis.label.set_alpha(0)'),
        ('markers',True,dots,baseline),
        ('scatter-reversed',True,'ax.scatter(x[::-1],fraction[::-1],s=4)',baseline),
        ('diagonal-step-wrong',False,line,'ax.step([0,1],[0,1],where="post")'),
        ('markers-one-only',False,'ax.plot(x,fraction,ls="none",marker="o",markevery=[0])',baseline),
        ('wrong-interior',False,'t=fraction.copy(); t[160]=.01; ax.plot(x,t)',baseline)]
    for name,ok,series,diag in examples:
        yield 'gains-'+name,'gains-plot',ok,GAINS.format(series=series,baseline=diag)
    eda = """
from sklearn.model_selection import train_test_split
all_offered=pilot[pilot.group_name.eq('предложение')].merge(data,on='guest_id',validate='one_to_one')
off, heldout=train_test_split(all_offered,test_size=.25,random_state=42,stratify=all_offered.bought)
BUCKET_FRAME
bucket=pd.cut(off.morning_share,[0,.2,.5,1],include_lowest=True,labels=['до 0.2','0.2–0.5','выше 0.5'])
by_morning=off.bought.groupby(bucket,observed=True).mean().round(3)
by_city=off.groupby('city').bought.mean().round(3)
by_source=off.groupby('source').bought.mean().round(3)
pick=bucket.eq('выше 0.5')
n_top=int(pick.sum())
lift_top=round(float(off.loc[pick,'bought'].mean()/off.bought.mean()),2)
print(len(off),int(off.bought.sum()),int(off.loc[pick,'bought'].sum()),n_top,lift_top)
"""
    for name,replace,ok in [('train','',True),('leaked','off=all_offered',False)]:
        yield 'eda-'+name,'fp-eda',ok,program('fp-eda',eda.replace('BUCKET_FRAME',replace))
    lines = """
import matplotlib.pyplot as plt
segments={'новички':X_test.loc[X_test.tenure_months<=3],'остальные':X_test.loc[X_test.tenure_months>3]}
curves={k:[round(forest.predict_proba(df.assign(days_since_last=v))[:,1].mean(),3) for v in grid] for k,df in segments.items()}
pd_new,pd_old=curves['новички'],curves['остальные']
max_gap_day=max(zip(grid,pd_new,pd_old),key=lambda r:r[1]-r[2])[0]
fig,ax=plt.subplots()
for label in ['остальные','новички']:
    ax.plot(grid,curves[label],label=label)
ax.set_xlabel('дней с последнего визита')
ax.legend()
"""
    yield 'pd-reversed-legend','pd-two',True,program('pd-two',lines)
    yield 'pd-lines-at-zero','pd-two',False,program('pd-two',lines.replace('ax.plot(grid,curves[label],','ax.plot(grid,[0]*len(grid),'))
    for th in [.1,.22]:
        code=program('fp-money',MONEY.replace('GRID','[k/100 for k in range(2,41,2)]').replace('THRESHOLD',str(th)))
        yield f'money-{th}-rows','fp-money',True,code
        if th==.22:
            yield 'money-gross-key','fp-money',False,code+'\ncurve["threshold"]=curve.threshold.iloc[::-1].to_numpy()'
            yield 'money-incr-key','fp-money',False,code+'\nincr["margin"]=incr.margin.iloc[::-1].to_numpy()'
            yield 'money-equivalent-grid','fp-money',True,code.replace('[k/100 for k in range(2,41,2)]','np.cumsum(np.full(20,.02))')
        code=program('fp-honest',HONEST.replace('THRESHOLD',str(th)))
        yield f'honest-{th}-rows','fp-honest',True,code
        if th==.22:
            yield 'honest-mismatched-id','fp-honest',False,code+'\nrest["guest_id"]=rest.guest_id.iloc[::-1].to_numpy()'
            yield 'honest-swapped-decisions','fp-honest',False,code+'\nrest["send"]=rest.send.shift(1,fill_value=bool(rest.send.iloc[-1]))'
            yield 'honest-extra-guest','fp-honest',False,code+'\nr=rest.iloc[[0]].copy(); r["guest_id"]="F00174"; r["send"]=False; rest=pd.concat([rest,r])'
            yield 'honest-overwrite-threshold','fp-honest',False,code+'\nbest_t=.10'
