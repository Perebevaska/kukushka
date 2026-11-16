// Run from the repository root. Cards and checks come from the served HTML payload.
import {readFileSync, writeFileSync, readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const read = p => readFileSync(p,'utf8');
const hash = s => createHash('sha256').update(s).digest('hex');
const pages = readdirSync('site/ch05').filter(f=>/^\d/.test(f)).map(f=>JSON.parse(read('site/ch05/'+f).match(/id="lesson-data">([\s\S]+?)<\/script>/)[1]));
const notebook=process.argv.includes('--notebook') ? JSON.parse(read('site/notebooks/tasks/ch05.json')).tasks : null;
const cases = [];
function add(lesson,id,name,expected,transform) {
  const page=pages.find(p=>p.lesson.endsWith('/'+lesson));
  const card=notebook ? notebook['ch05/'+lesson+'/'+id] : page.tasks.find(t=>t.id===id);
  const code=typeof transform === 'function' ? transform(card.solution) : transform;
  cases.push({lesson,id,name,expected,code,card,page});
}
function pair(lesson,id,code,error) {
  add(lesson,id,'alternative',true,code);
  add(lesson,id,'error',false,code+'\n'+error);
}
pair('01-probability','two-late', `from math import comb
p=.24
out=[comb(2,k)*p**k*(1-p)**(2-k) for k in range(3)]
none,exactly_one,both=map(lambda v: round(v,3),out)`, 'exactly_one=round(exactly_one/2,3)');
pair('02-distributions','tail', `from scipy.stats import binom
p_bad=round(sum(binom.pmf(range(8,21),20,.24)),4)`,'p_bad=round(sum(binom.pmf(range(9,21),20,.24)),4)');
pair('02b-normal','norm-approx', `from scipy.stats import norm,binom
n,p,k=500,.24,140
e=1-binom.cdf(k-1,n,p)
scale=(n*p*(1-p))**.5
a=1-norm.cdf((k-.5-n*p)/scale)
exact,approx=round(e,4),round(a,4)
rel_err=round(abs(a/e-1),3)
rule_ok=min(n*p,n*(1-p))>=10`, 'approx=round(1-norm.cdf((k-n*p)/scale),4)');
pair('03-sampling','se-fn', `def se(sigma,n):
    return (sigma**2/n)**.5
ses=[round(se(11, sample),2) for sample in [25,100,400]]`, 'def se(sigma,n): return sigma/n');
add('04-confidence','errorbars','numeric-x-with-labels',true,s=>s.replace('g.index, g["mean"]','range(len(g)), g["mean"]')+'\nax.set_xticks(range(len(g)),g.index)');
add('04-confidence','errorbars','reassigned-shop-labels',false,s=>s+'\nax.set_xticks(range(len(g)), g.index[::-1])');
pair('05-hypotheses','observed', `import pandas as pd
df=pd.read_csv('deliveries.csv').query('1 <= actual_min <= 299')
g=df.assign(is_late=df.actual_min.gt(df.promised_min)).groupby(df.weather.eq('снег')).is_late.mean()
observed=round(100*(g[True]-g[False]),1)`, 'observed=-observed');
pair('06-tests','paired', `import pandas as pd
from scipy.stats import ttest_1samp
df=pd.read_csv('deliveries.csv',parse_dates=['created']).query('1 <= actual_min <= 299')
tab=df.actual_min.gt(df.promised_min).groupby([df.shop_id,df.created.dt.month]).mean().unstack()
change=tab[11]-tab[10]
mean_change=round(change.mean()*100,1)
p_value=round(ttest_1samp(change,0).pvalue,3)`, 'from scipy.stats import ttest_ind\np_value=round(ttest_ind(tab[11],tab[10],equal_var=False).pvalue,3)');
pair('07-ab','srm', `import pandas as pd
from scipy.stats import chi2
x=pd.read_csv('ab_push.csv')
sizes=x.groupby('group').size().sort_index(ascending=False)
expected=len(x)/len(sizes)
srm_p=chi2.sf(((sizes-expected)**2/expected).sum(),len(sizes)-1)
srm_ok=srm_p>=.01`,'sizes.index=sizes.index[::-1]');
pair('08-pitfalls','practical', `from scipy.stats import chi2_contingency
n=2_000_000
a,b=400_000,402_400
p_value=chi2_contingency([[a,n-a],[b,n-b]],correction=False).pvalue
diff_pp=round((b-a)/n*100,2)
rel_pct=round((b-a)/a*100,1)
worth_it=bool(p_value<.05 and rel_pct>=2)`, 'worth_it=bool(p_value<.05)');
add('09-project','chart','valid-reversed-display',true,s=>s.replace('.agg(["sum", "size", "mean"])','.agg(["sum", "size", "mean"]).sort_index(ascending=False)'));
add('09-project','chart','swapped-tick-labels',false,s=>s+'\nfor ax in axes: ax.set_xticks([0,1],["B","A"])');
add('09-project','chart','invisible-whiskers',false,s=>s+'\nfor ax in axes:\n    for col in ax.collections: col.set_visible(False)\n    for line in ax.lines: line.set_visible(False)');

if(process.argv.includes('--historical')) {
  cases.length=0;
  add('05-hypotheses','perm-snow','all-null-permutations',false,s=>s+'\ndiffs=np.zeros(3000);p_value=0.0');
  add('05-hypotheses','perm-fn','wrong-reported-difference',false,s=>s+'\nres=(999.,.47)');
  add('05-hypotheses','perm-fn','monte-carlo-positive-at-zero-exceedances',true,s=>s+'\nassert perm_test(np.arange(12),np.arange(100,112),2000,0)[1] > 0, "Ноль при 2000 случайных перестановках"');
  add('05-hypotheses','perm-fn','finite-monte-carlo-correction',true,s=>s.replace('count / n_perm','(count+1)/(n_perm+1)'));
  add('09-project','late','negative-p',false,s=>s+'\np_late=-0.00001');
  add('09-project','cities','unadjusted-p-replaced',false,s=>s+'\nby_city["p"]=1.');
  add('07-ab','ztest','unrounded-pooled-p',true,s=>s+'\nfrom statsmodels.stats.proportion import proportions_ztest\nimport pandas as pd\ndf=pd.read_csv("ab_push.csv")\ng=df.groupby("group").ordered.agg(["sum","size"])\np_value=proportions_ztest(g["sum"],g["size"])[1]');
}
const dir=resolve('site/assets/vendor/pyodide')+'/';
const {loadPyodide}=await import(pathToFileURL(dir+'pyodide.mjs'));
const py=await loadPyodide({indexURL:dir,stdout(){},stderr(){}});
await py.loadPackage(['numpy','pandas','scipy','matplotlib','statsmodels'],{messageCallback(){},errorCallback(){}});
py.FS.writeFile('harness.py',read('site/assets/harness.py'));
py.runPython('import sys;sys.path.insert(0,"/home/pyodide")');
const run=py.pyimport('harness').run;
const rows=[];
for(const {lesson,id,name,expected,code,card,page} of cases) {
  for(const file of page.files) py.FS.writeFile(file,readFileSync('site/data/'+file));
  const result=run(code,card.check,card.setup||null,false);
  const {ok,check,error}=result.toJs({dict_converter:Object.fromEntries});
  result.destroy();
  rows.push({lesson,id,name,expected,actual:!!(ok&&check?.passed),response:check?.msg||error?.message||null,check_sha256:hash(card.check),code});
}
writeFileSync(process.argv[2],JSON.stringify({version:py.version,source:notebook?'notebook catalog':'published HTML',rows},null,2)+'\n');
console.log(rows.filter(x=>x.actual!==x.expected).map(x=>[x.lesson,x.id,x.name,x.actual,x.response]));
