"""Prepare explicit migrations and extra cases without running any course code."""
import ast,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
R=H.parents[3]
export=Path(sys.argv[1] if len(sys.argv)>1 else '/private/tmp/kuch08round/final.json')
tasks=[t for t in json.loads(export.read_text()) if t['lesson'].startswith('ch08/') and t['kind']=='task']
T={t['lesson'].removeprefix('ch08/')+'/'+t['id']:t for t in tasks}
assert len(tasks)==len(T)==91
old=json.loads((H/'probes-original.json').read_text())
follow=json.loads((H/'probes-followup.json').read_text())
assert len(old)==40 and len(follow)==16
def replace(source,before,after):
    assert source.count(before)==1, (before,source.count(before))
    out=source.replace(before,after)
    assert out!=source
    return out
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
migrated=[];current=[]
money=T['07-final-project/fp-money']['solution']
honest=T['07-final-project/fp-honest']['solution']
M={
    'money-alt':replace(money,'best_t = supported.loc[supported["margin"].idxmax(), "threshold"]','best_t = 0.10'),
    'money-units':money+'\ntest_profit=1600*test_buyers-.150*test_sent',
    'money-curve-key':money+'\ncurve["threshold"]=curve["threshold"].values[::-1]',
    'money-curve-reorder':money+'\ncurve=curve.iloc[::-1]',
    'honest-alt':replace(honest,'best_t = 0.08','best_t = 0.10'),
    'honest-ignore-organic':honest+'\nhonest_profit=naive_profit',
    'honest-round-organic':honest+'\nhonest_profit=round(1600*(eb-organic*n_send)-150*n_send)',
}
for p in old+follow:
    q=dict(p)
    if p['id'] in M:
        q['code']=M[p['id']]
        q['migration']='Новая политика требует incr в fp-money, eligibility reg<2026-06-01 и единый заранее выбранный best_t в fp-honest. Содержательная мутация сохранена; базовая программа адаптирована явно.'
        migrated.append(dict(id=p['id'],key=p['key'],before_sha256=digest(p['code']),after_sha256=digest(q['code']),reason=q['migration']))
    current.append(q)
assert len(current)==56 and len(migrated)==7
extra=[]
def add(id,key,expected,reason,code,**kw):
    ast.parse(code)
    extra.append(dict(id=id,key=key,expected=expected,reason=reason,code=code,**kw))
key='07-final-project/fp-money'
for name in ['sent','buyers','profit']:
    add('curve-'+name+'-mismatch',key,False,'Только значения '+name+' приписаны другим порогам.',money+f'\ncurve["{name}"]=curve["{name}"].values[::-1]')
for name in ['threshold','control_n','organic_share','margin']:
    add('incr-'+name+'-mismatch',key,False,'Потеря связи '+name+' со своим порогом.',money+f'\nincr["{name}"]=incr["{name}"].values[::-1]')
add('incr-whole-reorder',key,True,'Перестановка целых строк сохраняет соответствие порогу.',money+'\nincr=incr.iloc[::-1]')
add('incr-minimal-columns',key,True,'Условие требует только четыре столбца incr.',money+'\nincr=incr[["threshold","control_n","organic_share","margin"]]')
for name in ['sent','profit']:
    add('incr-optional-'+name+'-mismatch',key,None,'Ненормативная диагностика дополнительных столбцов: видимое условие требует только threshold/control_n/organic_share/margin. Эти случаи не входят в знаменатель успешности.',money+f'\nincr["{name}"]=incr["{name}"].values[::-1]',classification='optional-field-diagnostic')
# The fixture filters only control IDs. Offer training IDs/labels are unchanged.
# An independent model with the same train-only fit chooses a nonempty control
# subset whose predictions do not exceed .40. The threshold .40 then has zero
# comparable controls, while lower thresholds still have observed controls.
prefix=money[:money.index('oof = cross_val_predict')]
fixture=prefix+'''
best.fit(X_train,y_train)
_fixture_p=best.predict_proba(ctrl[num+cat])[:,1]
_fixture_ids=set(ctrl.loc[_fixture_p<=.40,'guest_id'])
assert _fixture_ids, 'Fixture must retain observed controls.'
pilot=pilot.loc[(pilot.group_name!='контроль')|pilot.guest_id.isin(_fixture_ids)].copy()
'''
add('money-emptycontrol-unknown',key,True,'На пороге .40 нет контрольных наблюдений: NaN допустим в кривой, выбор — только среди поддержанных порогов.',money,setup_append=fixture)
emptyzero=replace(money,'best_t = supported.loc[supported["margin"].idxmax(), "threshold"]','''assert int(incr.loc[incr.threshold==.40,'control_n'].iloc[0])==0, 'Fixture did not create empty selected control.'
incr['organic_share']=incr.organic_share.fillna(0.)
incr['margin']=incr['profit']-1600*incr['sent']*incr['organic_share']
best_t=.40''')
add('money-emptycontrol-zero',key,False,'Неизвестная доля пустого контроля подменена нулём и выбран неподдержанный порог.',emptyzero,setup_append=fixture)
key='07-final-project/fp-portrait'
add('portrait-alt-010',key,True,'Реальное изменение best_t на .10, остальной портрет пересчитан.',replace(T[key]['solution'],'best_t = 0.08','best_t = 0.10'))
key='07-final-project/fp-honest'
add('honest-moved-threshold',key,False,'Совместимое имя best_t_incr должно сохранять переданное правило best_t.',replace(honest,'best_t_incr = best_t','best_t_incr = .10'))
key='02-budget/gains-plot'
base=next(p['code'] for p in current if p['id']=='gains-markers')
normal=replace(base,'ax.plot(share,caught,".",label="модель")','ax.plot(share, caught, label="модель")')
diag='ax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")'
add('gains-diagonal-scatter-endpoints',key,False,'Две отдельные конечные точки не образуют видимую диагональ.',replace(normal,diag,'ax.scatter([0,1],[0,1],label="случайно")'))
add('gains-diagonal-step-geometry',key,False,'drawstyle=steps-post отображает угловую линию вместо диагонали.',replace(normal,diag,'ax.plot([0,1],[0,1],drawstyle="steps-post",label="случайно")'))
add('gains-markevery-one',key,False,'У маркерной кривой markevery=[0] скрывает остальные 599 узлов.',replace(base,'ax.plot(share,caught,".",label="модель")','ax.plot(share,caught,".",markevery=[0],label="модель")'))
key='07-final-project/fp-money'
add('money-floating-grid',key,True,'Те же математические точки сетки без промежуточного округления float.',replace(money,'for t in np.arange(0.02, 0.41, 0.02).round(2):','for t in np.arange(0.02, 0.41, 0.02):'))
add('money-cumsum-grid',key,True,'Те же двадцать порогов сетки, полученные накоплением .02; float-погрешность не меняет отборы.',replace(money,'for t in np.arange(0.02, 0.41, 0.02).round(2):','for t in np.cumsum(np.full(20,.02)):'))
# Verify the advertised historical alternate probes actually change the final
# authored programs. No execution or import of ch08_acceptance.py is needed.
acceptance=(R/'tools/checks/ch08_acceptance.py').read_text()
alternate_checks=[]
for task,anchor in [('fp-money','best_t = supported.loc[supported["margin"].idxmax(), "threshold"]'),('fp-honest','best_t = 0.08'),('fp-portrait','best_t = 0.08')]:
    source=T['07-final-project/'+task]['solution']
    changed=replace(source,anchor,'best_t = 0.10')
    assert repr(anchor) in acceptance
    alternate_checks.append(dict(task=task,anchor=anchor,before_sha256=digest(source),after_sha256=digest(changed),changed=True))
for label,probes in [('current',current),('extra-current',extra)]:
    (H/f'tasks-{label}.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
    (H/f'probes-{label}.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2)+'\n')
(H/'migrations-current.json').write_text(json.dumps(migrated,ensure_ascii=False,indent=2)+'\n')
(H/'manifest-current.json').write_text(json.dumps(dict(export=str(export),export_sha256=hashlib.sha256(export.read_bytes()).hexdigest(),tasks=len(tasks),lessons=len(set(t['lesson']for t in tasks)),core_probes=len(current),extra_probes=len(extra),migrations=migrated,acceptance_alternates=alternate_checks,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'content/ch08').glob('*.md'))},note='Prepared before execution. Original 40 programs and original logs remain unchanged.'),ensure_ascii=False,indent=2)+'\n')
print('Prepared',len(current),'core +',len(extra),'extra; explicit migrations',len(migrated))
