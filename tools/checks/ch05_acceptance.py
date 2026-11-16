from acceptance_runner import Chapter
import pandas as pd

with Chapter('ch05') as c:
    source=c.tasks['04-confidence','bootstrap']['solution']
    c.probe('04-confidence','bootstrap',code=source.replace('rng.choice(t, size=len(t), replace=True)', 't[rng.integers(0,len(t),size=len(t))]'),expected=True)
    c.probe('04-confidence','bootstrap','lo,hi=31.99,32.01')
    for lesson,task in [('04-confidence','errorbars'),('09-project','chart')]:
        source=c.tasks[lesson,task]['solution']
        start=source.find('yerr=[')
        # Replace balanced [] expression with zero; the surrounding bar/errorbar still executes.
        level=0; end=start+5
        for i in range(start+5,len(source)):
            if source[i]=='[': level+=1
            elif source[i]==']':
                level-=1
                if level==0: end=i+1; break
        c.probe(lesson,task,code=source[:start]+'yerr=0'+source[end:])
    def swap_promises():
        a=pd.read_csv('ab_promise.csv')
        mask=(a.group=='B') & (a.distance_km>=2)
        a.loc[mask,'promise_min']=a.loc[mask,'promise_min'].map({45:60,60:45})
        a.to_csv('ab_promise.csv',index=False)
    c.probe('09-project','design',prepare=swap_promises,expected=True)
    old=c.tasks['09-project','design']['solution'].replace('far_same = bool((far["promise_min"] == far["distance_km"].map(lambda x: 45 if x < 5 else 60)).all())', 'far_same = set(far.loc[far.group=="A","promise_min"]) == set(far.loc[far.group=="B","promise_min"])')
    c.probe('09-project','design',prepare=swap_promises,code=old)
    c.probe('09-project','decision',expected=True)

    c.probe('06-tests','agree',expected=True)
    source=c.tasks['06-tests','agree']['solution']
    c.probe('06-tests','agree',code=source+'\np_perm=p_z')
    c.probe('06-tests','agree',code=source+'\np_perm=round(p_z,4)')
    old_student=c.tasks['06-tests','agree']['starter']+'''
a,b=late[grp],late[~grp]
p_z=proportions_ztest([sum(a),sum(b)],[len(a),len(b)])[1]
obs=a.mean()-b.mean()
diff_pp=round(100*obs,1)
hits=0
for _ in range(4000):
    sh=rng.permutation(grp)
    hits+=abs(late[sh].mean()-late[~sh].mean())>=abs(obs)
p_perm=hits/4000
'''
    c.probe('06-tests','agree',code=old_student,expected=True)
    in_place=old_student.replace('a,b=late[grp],late[~grp]', 'grp=grp.copy()\na,b=late[grp],late[~grp]').replace('sh=rng.permutation(grp)','rng.shuffle(grp)\n    sh=grp')
    c.probe('06-tests','agree',code=in_place,expected=True)
    c.probe('06-tests','agree',code=in_place.replace('p_perm=hits/4000','p_perm=(hits+1)/4001'),expected=True)
    outcomes=old_student.replace('sh=rng.permutation(grp)\n    hits+=abs(late[sh].mean()-late[~sh].mean())>=abs(obs)', 'permuted=rng.permutation(late)\n    hits+=abs(permuted[grp].mean()-permuted[~grp].mean())>=abs(obs)-1e-12')
    c.probe('06-tests','agree',code=outcomes,expected=True)
    hypergeom=old_student[:old_student.index('hits=0')]+'''
n_b=int(grp.sum());n_a=int((~grp).sum());total=int(late.sum())
counts=rng.hypergeometric(total,len(late)-total,n_b,size=4000)
permuted=counts/n_b-(total-counts)/n_a
p_perm=(np.abs(permuted)>=abs(obs)-1e-12).mean()
'''
    c.probe('06-tests','agree',code=hypergeom,expected=True)
    exact=old_student[:old_student.index('hits=0')]+'''
from scipy.stats import hypergeom
n_b=int(grp.sum());n_a=int((~grp).sum());total=int(late.sum())
counts=np.arange(max(0,total-n_a),min(n_b,total)+1)
permuted=counts/n_b-(total-counts)/n_a
p_perm=hypergeom.pmf(counts,len(late),total,n_b)[np.abs(permuted)>=abs(obs)-1e-12].sum()
'''
    c.probe('06-tests','agree',code=exact,expected=True)
    # Assert restoration around both a passing and a failing isolated CSV replay.
    import os
    original_cwd=os.getcwd()
    c.probe('06-tests','agree',code=old_student,expected=True)
    assert os.getcwd()==original_cwd
    c.probe('06-tests','agree',code=source+'\np_perm=p_z')
    assert os.getcwd()==original_cwd

    c.probe('01-probability','running',expected=True)
    c.probe('01-probability','running','ax.lines[1].set_ydata([.4,.4])')
    c.probe('01-probability','running','ax.lines[0].set_ydata(np.zeros(5000))')
    source=c.tasks['01-probability','running']['solution']
    swapped=source.replace('ax.plot(running)\nax.axhline(0.24, color="tab:red", linestyle="--")', 'ax.axhline(.24)\nax.plot(np.arange(1,5001),running)')
    c.probe('01-probability','running',code=swapped,expected=True)
    hlines=source.replace('ax.axhline(0.24, color="tab:red", linestyle="--")', 'ax.hlines(.24,0,4999)')
    c.probe('01-probability','running',code=hlines,expected=True)
    reversed_pairs=source.replace('ax.plot(running)', 'ax.plot(np.arange(4999,-1,-1),running[::-1])')
    c.probe('01-probability','running',code=reversed_pairs,expected=True)
    c.probe('01-probability','running',code=source.replace('ax.plot(running)', 'idx=rng.permutation(5000)\nax.plot(idx,running[idx])'))
    c.probe('01-probability','running','ax.set_ylim(.25,.32)')
    transparent=source.replace('ax.axhline(0.24, color="tab:red", linestyle="--")', 'ax.hlines([.24,.34],0,4999,colors=[(1,0,0,0),(0,0,1,1)])')
    c.probe('01-probability','running',code=transparent)
    c.probe('01-probability','running','ax.lines[0].set_visible(False)\nax.plot(np.ones(5000)*.3)')
    c.probe('01-probability','running','ax.lines[1].set_alpha(0)\nax.axhline(.4)')
    c.probe('01-probability','running',code=source.replace('ax.axhline(0.24, color="tab:red", linestyle="--")', 'ax.plot([0,1],[.24,.24])'))

    c.probe('07-ab','ab-report',expected=True)
    source=c.tasks['07-ab','ab-report']['solution']
    c.probe('07-ab','ab-report',code=source.replace('def ab_report(df, metric):','def ab_report(df, metric):\n    metric="ordered"'))
    c.probe('07-ab','ab-report','report={}')
    c.probe('07-ab','ab-report','report["diff_pp"]=0')
    c.probe('07-ab','ab-report',code=source.replace('"p": round(p, 4)','"p": p'),expected=True)
    c.probe('07-ab','ab-report',code=source.replace('"srm_p": srm_p','"srm_p": round(srm_p,4)'),expected=True)
    c.probe('07-ab','ab-report',code=source.replace('p < 0.05 and srm_p >= 0.01','p < 0.05'))
