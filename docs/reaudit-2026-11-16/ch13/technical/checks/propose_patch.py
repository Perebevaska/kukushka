from pathlib import Path
import json,re,difflib,hashlib
p=Path('/private/tmp/kuch13round/checks');w=p.parent;ts=json.loads((p/'tasks.json').read_text());base={(t['lesson'].split('/')[-1],t['id']):t for t in ts};changes={};texts={};setups={};solutions={}
def add(lesson,id,code):changes[lesson,id]=base[lesson,id]['check']+'\n'+code.strip()+'\n'
add('01-text-prep','tokenize', '''
assert f('Ёж, ёлка и ABC не-кофе 3!') == ['ёж', 'ёлка', 'и', 'не', 'кофе'], 'tokenize: включите ё, отделяйте нерусские символы и сохраняйте порядок слов.'
assert f('') == [], 'Для пустой строки tokenize возвращает пустой список.'
''')
add('01b-lemmas','stem', '''
assert f('капучино', 3) == 'кап' and f('кофе', 7) == 'кофе', 'Параметр n задаёт длину основы; короткое слово сохраняется.'
''')
s=base['01-text-prep','bigrams']['check'];s=s.replace("assert set(got) == set(w) or got[:3] == w[:3], f'top_bad = {got}, а нужно {w}.'",'''assert len(set(got)) == 5 and all(k in d for k in got), 'top_bad — пять разных биграмм из отзывов.'
assert all(d[got[i]] >= d[got[i+1]] - 1e-12 for i in range(4)), 'Расположите биграммы по убыванию разности долей.'
assert min(d[k] for k in got) >= d[w[-1]] - 1e-12, 'Все пять биграмм должны входить в лидеры по разности долей; при равенстве подойдёт любая.' ''')
changes['01-text-prep','bigrams']=s
s=base['02-tfidf','keywords']['check'];start=s.index("f = need('keywords')");end=s.index("w = _np.mean",start)
s=s[:start]+'''f = need('keywords')
def _verify_words(words, i, k):
    got = list(words)
    row = T0[i].toarray()[0]
    expected_n = min(k, int((row > 0).sum()))
    assert len(got) == expected_n and len(set(got)) == len(got), f'keywords({i}, {k}): верните нужное число разных слов отзыва.'
    indices = {str(word):j for j,word in enumerate(nm)}
    assert all(word in indices and row[indices[word]] > 0 for word in got), 'Ключевые слова должны встречаться в этом отзыве.'
    weights = [row[indices[word]] for word in got]
    assert all(a >= b - 1e-12 for a,b in zip(weights,weights[1:])), 'Ключевые слова расположите по убыванию TF-IDF.'
    if got:
        cutoff = sorted(row[row>0], reverse=True)[expected_n-1]
        assert min(weights) >= cutoff - 1e-12, 'Возьмите слова с наибольшими весами TF-IDF.'
for _i,_k in [(i,3) for i in range(5)] + [(10,2),(199,4)]:
    _verify_words(f(_i,_k),_i,_k)
g = need('kw', dict)
assert set(g) == set(range(5)), 'kw — словарь для отзывов 0…4.'
for _i in range(5):
    _verify_words(g[_i],_i,3)
''' +s[end:];changes['02-tfidf','keywords']=s
add('03-classify','top-words','''
import numpy as _np
assert wt.index.is_unique and _np.allclose(wt.reindex(w0.index).to_numpy(),w0.to_numpy(),atol=1e-7,rtol=0), 'Каждому слову в weights должен соответствовать его коэффициент модели.'
''')
add('03-classify','topics','''
import numpy as _np
_cm = need('cm')
_expected_cm = _pd.crosstab(d,p)
assert _cm.index.is_unique and _cm.columns.is_unique, 'Темы в строках и столбцах cm не должны повторяться.'
assert set(_cm.index)==set(_expected_cm.index) and set(_cm.columns)==set(_expected_cm.columns), 'Строки cm — настоящие темы, столбцы — предсказанные.'
assert _np.array_equal(_cm.reindex(index=_expected_cm.index,columns=_expected_cm.columns).to_numpy(),_expected_cm.to_numpy()), 'Проверьте число отзывов в каждой ячейке cm по паре настоящая/предсказанная тема.'
''')
s=base['03-classify','compare']['check'].replace("close(got[k], v, 0.002)","close(got[k], v, 0.00051)");changes['03-classify','compare']=s
# Explicit final-test outputs: this is the only additional numeric-output contract migration.
texts['03-classify','recall95']='\n\nПосле выбора порога на валидации зафиксируйте его. Для отдельного финального теста получите новые вероятности `p_test = model.predict_proba(X_test)[:, 1]`. Сохраните `test_recall` — фактическую полноту при `thr` (3 знака) и `test_flagged` — число отзывов теста в очереди. Сравнивайте `p` с `y_validation`, а `p_test` с `y_test`: даже одинаковая длина массивов не означает, что в них одни и те же отзывы.\n'
add('04-embeddings','lsa','''
_anchor = _np.linspace(0,len(Z0)-1,64,dtype=int)
assert _np.allclose(Zs @ Zs[_anchor].T, Z0 @ Z0[_anchor].T, atol=1e-5,rtol=1e-5), 'Строка Zn должна описывать свой отзыв: проверьте порядок текстов и соответствие эмбеддингов. Знаки осей SVD могут различаться.'
''')
add('04-embeddings','char-search','''
f = need('search')
for _vec,_query,_k in [(_TF().fit(r0['text']), 'цены адекватные', 3),(_TF(analyzer='char_wb',ngram_range=(3,4)).fit(r0['text']), 'не советую', 7)]:
    _matrix = _vec.transform(r0['text'])
    assert list(f(_vec,_matrix,_query,_k)) == _s(_vec,_query,_k), f'search: пересчитайте запрос {_query!r} и верните {_k} текстов в порядке сходства.'
''')
add('04-embeddings','skipgram','''
for _tokens,_window in [(['кофе','кофе'],1),(['а','б','а','в'],2),([],2),(['кофе'],0)]:
    assert list(f(_tokens,window=_window)) == _p(_tokens,_window), 'Соседи задаются позициями: два одинаковых слова в разных позициях тоже образуют пары.'
''')
# Pooling references are deep, private copies taken in setup before learner code.
setups['04b-transformers','masked-pool']=base['04b-transformers','masked-pool']['setup']+'\n_pool_reference_H = H.copy()\n_pool_reference_mask = attention_mask.copy()\n'
s=base['04b-transformers','masked-pool']['check'].replace('ref = (H * attention_mask[:, :, None]).sum(1) / attention_mask.sum(1, keepdims=True)','_source_H = need("_pool_reference_H").copy()\n_source_mask = need("_pool_reference_mask").copy()\nref = (_source_H * _source_mask[:, :, None]).sum(1) / _source_mask.sum(1, keepdims=True)').replace('H.mean(axis=1)','_source_H.mean(axis=1)')
s+='''
_pool_gold = _np.array([[[2.,4.,6.],[4.,2.,0.],[91.,-53.,22.]],[[3.,6.,9.],[-99.,20.,50.],[40.,80.,70.]]])
_pool_mask = _np.array([[1,1,0],[1,0,0]])
_pool_expected = _np.array([[3.,3.,3.],[3.,6.,9.]])
_pool_result = _np.asarray(f(_pool_gold.copy(),_pool_mask.copy()))
assert _pool_result.shape==(2,3) and _np.allclose(_pool_result,_pool_expected), 'mean_pool должен учитывать маску и работать с новым числом текстов, токенов и признаков.'
_pool_extended = _np.concatenate([_pool_gold,_np.full((2,4,3),71.)],axis=1)
_mask_extended = _np.concatenate([_pool_mask,_np.zeros((2,4),dtype=int)],axis=1)
assert _np.allclose(f(_pool_extended.copy(),_mask_extended.copy()),_pool_expected), 'Добавление заполнителей не меняет среднее настоящих токенов.'
''';changes['04b-transformers','masked-pool']=s
# Benchmark reference is keyed by original review_id, separate from mutable ok_llm.
s=base['04c-llm','llm-same']['check'];pos=s.index('rest = r0[')
s=s[:pos]+'''_original = _pd.read_csv('reviews_text.csv')
_original_check = _original.sample(200,random_state=5).reset_index(drop=True)
assert c0.review_id.is_unique and set(c0.review_id)==set(_original_check.review_id), 'Сравнивайте обе модели на тех же 200 review_id.'
_truth = _original_check.set_index('review_id')
for _key in ['text','topic']:
    assert c0[_key].tolist()==_truth.loc[c0.review_id,_key].tolist(), f'{_key}: сохраните принадлежность исходному review_id.'
_llm_topics = _pd.Series(need('llm_topic'),index=_original_check.review_id)
_expected_ol = c0.review_id.map(_llm_topics).isin(['кофе','еда','обслуживание','доставка','цена','атмосфера']) & c0.review_id.map(_llm_topics).eq(c0.topic)
if isinstance(ol,_pd.Series):
    assert ol.index.is_unique and set(ol.index)==set(c0.index), 'Индикаторы ok_llm должны соответствовать строкам check.'
    ol=ol.reindex(c0.index)
assert list(ol)==list(_expected_ol), 'Не переставляйте отдельно ответы LLM: обе системы сравниваются по одним review_id.'
''' +s[pos:];s='import pandas as _pd\n'+s;changes['04c-llm','llm-same']=s
# Weekly table accepts keyed permutations; plot evidence is checked by dates, values, units, and focus label.
s=base['05-project','weekly']['check'];s=s.replace("assert ((got[w.columns].values - w.values) ** 2).max() < 1e-12, 'Доли по неделям не совпадают.'",'''assert got.index.is_unique and got.columns.is_unique and set(got.index)==set(w.index) and set(got.columns)==set(w.columns), 'weekly: сохраните уникальные даты недель и точки.'
assert ((got.reindex(index=w.index,columns=w.columns).values-w.values)**2).max()<1e-12, 'Доли должны соответствовать своей неделе и точке.' ''');s=s.replace("assert got.index.equals(w.index), 'Недельные даты weekly должны соответствовать реальным датам отзывов, не только числам в ячейках.'",'')
s+='''
import numpy as _np
import matplotlib.dates as _md
from matplotlib.container import BarContainer as _BarContainer
_expected_dates = list(w.index)
_expected_values = w[_shop].to_numpy()
def _calendar_values(x):
    values=list(x)
    if not values: return None
    candidates=[]
    try: candidates.append([_pd.Timestamp(v.end_time).normalize() if isinstance(v,_pd.Period) else _pd.Timestamp(v).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    try: candidates.append([_pd.Timestamp(_md.num2date(float(v))).tz_localize(None).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    for dates in candidates:
        if len(dates)==len(_expected_dates) and set(dates)==set(_expected_dates): return dates
    return None
def _matches_plot(x,y):
    dates=_calendar_values(x)
    if dates is None: return False
    try:
        values=_pd.Series(_np.asarray(y,dtype=float),index=dates).reindex(w.index).to_numpy()
        return _np.allclose(values,_expected_values,atol=1e-6,rtol=0)
    except (ValueError,TypeError): return False
_plot_ok=False
for _fig in figs:
    for _ax in _fig.axes:
        _labels=' '.join([_ax.get_title(),*[_t.get_text() for _t in (_ax.get_legend().texts if _ax.get_legend() else [])]])
        _units=_ax.get_ylabel().lower()
        if _shop not in _labels or not any(_unit in _units for _unit in ['дол','share','fraction']): continue
        for _line in _ax.lines:
            if _matches_plot(_line.get_xdata(orig=True),_line.get_ydata()): _plot_ok=True
        for _container in _ax.containers:
            if isinstance(_container,_BarContainer):
                if _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches]): _plot_ok=True
assert _plot_ok, 'Покажите недельные доли выбранной точки по реальным датам, подпишите ось Y как долю и обозначьте точку в легенде или заголовке. Подойдёт линия или столбцы.'
''';changes['05-project','weekly']=s
texts['05-project','weekly']='\n\nНа графике по оси X покажите даты недель, по оси Y — долю сигналов модели. Обозначьте выбранную точку в легенде или заголовке; можно использовать линию или столбцы. Порядок строк таблицы произвольный, если значения сохраняют свои даты и точки.\n'
solutions['05-project','weekly']=base['05-project','weekly']['solution'].replace('доля недовольных','доля сигналов модели')
# Immutable source rows and period boundary, strict output structure, then behavioral join test.
s=base['05-project','adjust']['check'];pos=s.index("obs = n0[")
s=s[:pos]+'''_source_n = _pd.read_csv('reviews_new.csv',parse_dates=['date'])
assert n0.review_id.is_unique and set(n0.review_id)==set(_source_n.review_id), 'n должна содержать все исходные review_id без пропусков и дублей.'
_aligned_n=n0.set_index('review_id').reindex(_source_n.review_id)
for _key in ['shop_id','date','text']:
    assert _aligned_n[_key].tolist()==_source_n[_key].tolist(), f'n/{_key}: сохраните исходное значение по review_id.'
_expected_period = __import__('numpy').where(_source_n.date>='2026-10-05','после','до')
assert _aligned_n.period.tolist()==list(_expected_period), 'В готовой n граница — 5 октября включительно.'
''' +s[pos:];s=s.replace("_gold=_pd.read_csv('reviews_new_gold.csv')","_gold=_pd.read_csv('reviews_new_gold.csv').copy(deep=True)")
pos=s.index('for _period,_part');s=s[:pos]+'''assert _audit.index.is_unique and set(_audit.index)=={'до','после'}, 'audit: ровно два уникальных периода — до и после.'
assert _audit.columns.is_unique and set(_audit.columns)=={'n','complaints','tpr','fpr','observed','manual','adjusted'}, 'audit: сохраните семь показателей из условия без дублей.'
_expected_audit={}
''' +s[pos:];s=s.replace("    for _key,_value in _want.items():","    _expected_audit[_period] = _want.copy()\n    for _key,_value in _want.items():")
s+='''
# Source copies prevent aliasing with learner variables while reordering input only in memory.
_join_input = n0.copy(deep=True)
_join_gold = _gold.copy(deep=True)
_read_csv_original = _pd.read_csv
def _reordered_gold_reader(filename,*args,**kwargs):
    if str(filename).replace('\\\\','/').rsplit('/',1)[-1]=='reviews_new_gold.csv':
        return _join_gold.sample(frac=1,random_state=29).reset_index(drop=True).copy(deep=True)
    return _read_csv_original(filename,*args,**kwargs)
try:
    _pd.read_csv = _reordered_gold_reader
    _rerun = rerun_with(n=_join_input.copy(deep=True),sent=need('sent'))
finally:
    _pd.read_csv = _read_csv_original
_rerun_audit=_rerun.get('audit')
assert isinstance(_rerun_audit,_pd.DataFrame) and _rerun_audit.index.is_unique and set(_rerun_audit.index)=={'до','после'}, 'На переставленных строках разметки audit сохраняет оба периода.'
for _period,_values in _expected_audit.items():
    for _key,_value in _values.items():
        assert close(_rerun_audit.loc[_period,_key],_value), 'Соединяйте разметку по review_id: порядок строк gold не должен менять audit.'
''';changes['05-project','adjust']=s
texts['05-project','rare']='\n\nПри расчёте F1 передавайте полный список шести тем через `labels=sorted(r["topic"].unique())` и `zero_division=0`. Тема без верных прогнозов получает F1 = 0; в macro-F1 она сохраняет тот же вес, что остальные.\n'
s=base['05-project','rare']['solution'];s=s.replace('f1_score(t_test, pred, average=None, labels=labels)','f1_score(t_test, pred, average=None, labels=labels, zero_division=0)').replace('f1_score(t_test, pred, average="macro")','f1_score(t_test, pred, average="macro", labels=labels, zero_division=0)').replace('f1_score(t_test, pred_b, labels=[rarest], average=None)','f1_score(t_test, pred_b, labels=[rarest], average=None, zero_division=0)');solutions['05-project','rare']=s
# Build private candidate Markdown and export by replacing only named blocks.
private=p/'proposal';(private/'content/ch13').mkdir(parents=True,exist_ok=True)
output=[];diff=[]
for f in sorted((w/'original/content/ch13').glob('*.md')):
 old=f.read_text();parts=re.split(r'(?m)(?=^## task: )',old);new=parts[0]
 for segment in parts[1:]:
  id=segment.split(' |',1)[0].split('## task: ')[1];key=f.stem,id
  for field,collection in [('check',changes),('setup',setups),('solution',solutions)]:
   if key in collection:
    pattern=r'(?ms)(^### '+field+r'\s*\n```python[^\n]*\n)(.*?)(\n```\s*(?=\n### |\Z))'
    segment,n=re.subn(pattern,lambda m:m[1]+collection[key].rstrip()+m[3],segment,count=1);assert n,(key,field)
  if key in texts:
   i=segment.index('\n### ');segment=segment[:i]+texts[key]+segment[i:]
  if key==('03-classify','recall95'):
   segment=segment.replace('`recall_score(y_test, (p >= t).astype(int))`','`recall_score(y_validation, (p >= t).astype(int))`').replace('if recall_score(y_test, (p >= t).astype(int)) >= 0.95','if recall_score(y_validation, (p >= t).astype(int)) >= 0.95')
  new+=segment
 if new!=old:
  (private/'content/ch13'/f.name).write_text(new);diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/content/ch13/'+f.name,tofile='b/content/ch13/'+f.name))
for t in ts:
 t=t.copy();key=t['lesson'].split('/')[-1],t['id']
 for field,collection in [('check',changes),('setup',setups),('solution',solutions)]:
  if key in collection:t[field]=collection[key]
 output.append(t)
(private/'tasks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2));(private/'cards.patch').write_text(''.join(diff));(private/'manifest.json').write_text(json.dumps({'changed_checks':[list(k) for k in changes],'changed_public_contracts':[list(k) for k in texts],'changed_setup':[list(k) for k in setups],'changed_solutions':[list(k) for k in solutions],'files':{str(f.relative_to(private)):hashlib.sha256(f.read_bytes()).hexdigest() for f in private.rglob('*') if f.is_file()}},indent=2));print(len(changes),'checks',len(texts),'public clarifications')
