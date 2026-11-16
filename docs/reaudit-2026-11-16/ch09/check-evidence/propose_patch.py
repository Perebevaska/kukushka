"""Prepare a reviewable patch; only --apply mutates content. Coordinator owns application.
Timer changes explicitly migrate vectorize/nearest-shop from handwritten clocks to
provided registered measurements. All original programs/expectations stay frozen.
"""
import argparse,difflib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
changes={}
def section(file,task,fn):
    p=ROOT/'content/ch09'/file
    text=changes.get(p,p.read_text())
    start=text.index('## task: '+task+' |')
    end=text.find('\n## task:',start+1)
    if end<0:end=len(text)
    changes[p]=text[:start]+fn(text[start:end])+text[end:]
def check_append(block,code):
    start=block.index('### check\n```python\n')+len('### check\n```python\n')
    end=block.index('\n```',start)
    return block[:end]+'\n'+code.rstrip()+block[end:]
def replace_once(s,a,b):
    assert a in s,a
    return s.replace(a,b,1)

section('01-vectors.md','neighbors-scale',lambda b:check_append(b.replace('Для первого гостя найдите 5 ближайших', 'Напишите функцию `nearest(A, i, k=5)`, возвращающую k ближайших к строке i номеров в A, исключая саму i. Используйте её и для других i и k. Для первого гостя найдите 5 ближайших'),"""
_f = need('nearest')
for _A,_i,_k in [(_np.array([[0.,0.],[2.,0.],[5.,0.],[10.,0.]]),2,1),(_np.array([[1.,2.],[8.,4.],[3.,1.],[2.,7.],[11.,5.]]),1,3)]:
    _dist=_np.linalg.norm(_A-_A[_i],axis=1); _dist[_i]=_np.inf
    _indices=[int(j) for j in _f(_A,_i,_k)]
    assert len(_indices)==_k and len(set(_indices))==_k and all(0<=j<len(_A) for j in _indices) and _i not in _indices, 'nearest(A, i, k): верните k разных индексов, исключив i.'
    assert _np.allclose(_dist[_indices],_np.sort(_dist)[:_k]), 'nearest должна использовать переданные A, i и k и сортировать по расстоянию.'
"""))
def predict_df(b):
    b=b.replace('Сохраните `manual` (массив)', 'Сохраните обученную модель в `model`: проверка вызывает её predict на исходных и новых строках. Сохраните `manual` (массив)')
    b=re.sub(r"^assert need\('max_diff'\) < 1e-9 and.*\n",'',b,flags=re.M)
    return check_append(b,"""
_student_model=need('model')
_student_pred=_np.asarray(_student_model.predict(X0),dtype=float)
assert _student_pred.shape==mm.shape and _np.allclose(_student_pred,mm,rtol=1e-8,atol=1e-8), 'Переданная model должна прогнозировать исходные строки так же, как обученная линейная регрессия.'
_new=_pd.DataFrame([[2.5,1.,0.],[9.,3.,1.]],columns=X0.columns)
_new_pred=_np.asarray(_student_model.predict(_new),dtype=float)
assert _new_pred.shape==(2,) and _np.allclose(_new_pred,m.predict(_new),rtol=1e-8,atol=1e-8), 'model.predict должна работать на новых строках с тем же порядком признаков.'
_diff=float(_np.abs(man-_student_pred).max())
_value=float(need('max_diff'))
assert _np.isfinite(_value) and _value>=0 and _np.isclose(_value,_diff,rtol=0,atol=1e-10), 'max_diff — вычисленный максимум абсолютных разностей manual и переданной model.predict, конечное неотрицательное число.'
assert bool(need('same')) == bool(_diff<1e-9), 'same сравнивает вычисленную максимальную разность с 1e-9.'
""")
section('02-matrices.md','predict-df',predict_df)
section('03b-own-model.md','my-class',lambda b:check_append(b.replace('Готовый `LinearRegression` не используйте.', 'Готовый `LinearRegression` не используйте. Класс должен получать число признаков из X и переобучаться при новом вызове fit.'),"""
_X=_np.array([[0.,0.],[1.,0.],[0.,1.],[1.,1.],[2.,-1.]])
_y=2+3*_X[:,0]-4*_X[:,1]
_m=C(); assert _m.fit(_X,_y) is _m, 'fit возвращает self и при другом числе признаков.'
assert _np.allclose(_m.predict(_np.array([[2.,3.],[-1.,2.]])),[-4.,-9.]), 'После fit на новых данных predict использует все выученные веса и свободный член.'
_m.fit(_X,10-_X[:,0]+2*_X[:,1])
assert _np.allclose(_m.predict(_np.array([[2.,3.],[-1.,2.]])),[14.,15.]), 'Повторный fit должен заменить сохранённые веса.'
"""))
section('04-transform.md','attack',lambda b:check_append(b,"""
_actual=float(_np.abs(_np.asarray(need('restored'),dtype=float)-X0).max())
_claim=float(need('max_err'))
assert _np.isfinite(_claim) and _claim>=0 and _np.isclose(_claim,_actual,rtol=0,atol=1e-10), 'max_err — максимум модулей ошибок restored относительно X, конечный и неотрицательный.'
assert bool(need('leaked'))==bool(_actual<1e-6), 'leaked сравнивает max_err с 1e-6.'
"""))
def same_quality(b):
    b=b.replace('Сохраните `r2_x`, `r2_p` (4 знака) и `max_pred_diff` — наибольшую разницу прогнозов двух моделей.', 'Сохраните `pred_x` — массив прогнозов обученной на X модели для X, и `pred_p` — массив прогнозов обученной на X @ P модели для X @ P (в исходном порядке строк). По этим массивам посчитайте `r2_x`, `r2_p` (4 знака) и `max_pred_diff` — максимальную абсолютную разницу. Максимальная абсолютная разница — конечное неотрицательное число.')
    return check_append(b,"""
_submitted_x=_np.asarray(need('pred_x'),dtype=float)
_submitted_p=_np.asarray(need('pred_p'),dtype=float)
assert _submitted_x.shape==y0.shape and _submitted_p.shape==y0.shape, 'pred_x и pred_p — по одному прогнозу на каждую исходную строку X.'
assert _np.allclose(_submitted_x,a,rtol=1e-8,atol=1e-8) and _np.allclose(_submitted_p,b,rtol=1e-8,atol=1e-8), 'pred_x и pred_p должны содержать прогнозы двух обученных моделей на X и X @ P в исходном порядке строк.'
_actual=float(_np.abs(_submitted_x-_submitted_p).max()); _claim=float(need('max_pred_diff'))
assert _np.isfinite(_claim) and _claim>=0 and _np.isclose(_claim,_actual,rtol=0,atol=1e-9), 'max_pred_diff — максимальная абсолютная разница переданных pred_x и pred_p, конечное неотрицательное число.'
assert close(need('r2_x'),round(_r2(y0,_submitted_x),4)) and close(need('r2_p'),round(_r2(y0,_submitted_p),4)), 'r2_x и r2_p пересчитываются по переданным массивам прогнозов.'
""")
section('04-transform.md','same-quality',same_quality)
def hidden_quality(b):
    b=b.replace('Сохраните `hidden_model`', 'Напишите функцию `quality_equal(base, hidden, tol=1e-9)`: она возвращает True, если абсолютная разность двух исходных оценок не превышает tol. Не округляйте оценки внутри функции; она должна работать в обоих порядках аргументов и с другим tol. Затем сохраните `hidden_model`',1)
    b=b.replace('В `same` сохраните результат проверки, что разность по модулю не превышает 1e−9.', 'В `same` сохраните `quality_equal(r2_base, r2_full)`, где `r2_full` — исходный R² спрятанной модели до округления.')
    start=b.index('### starter\n```python\n')+len('### starter\n```python\n')
    end=b.index('\n```',start)
    b=b[:end]+'\n\ndef quality_equal(base, hidden, tol=1e-9):\n    ...\n'+b[end:]
    b=b.replace('abs(r2 - r2_base) < 1e-9','abs(r2 - r2_base) <= 1e-9')
    b=b.replace('Для `same` сравнивайте с `r2_base` неокруглённый R² спрятанной модели, а не `r2_hidden`:', 'В quality_equal верните `bool(abs(hidden - base) <= tol)`. Для `same` передайте `r2_base` и неокруглённый R² спрятанной модели, а не `r2_hidden`:')
    marker='### solution\n```python\n'
    start=b.index(marker)+len(marker)
    b=b[:start]+'def quality_equal(base, hidden, tol=1e-9):\n    return bool(abs(hidden - base) <= tol)\n\n'+b[start:]
    b=b.replace('same = bool(abs(r2_full - r2_base) < 1e-9)', 'same = quality_equal(r2_base, r2_full)')
    b=b.replace('r2_hidden = round(r2_full, 4)\nsame = quality_equal(r2_base, r2_full)', 'same = quality_equal(r2_base, r2_full)\nr2_hidden = round(r2_full, 4)')
    return check_append(b,"""
_equal=need('quality_equal')
_pairs=[(0.,0.,True),(0.,1e-9,True),(0.,_np.nextafter(1e-9,_np.inf),False),(.81234561,.8123456103,True),(.81234499,.81234501,False)]
for _a,_b,_expected in _pairs:
    assert bool(_equal(_a,_b)) is _expected and bool(_equal(_b,_a)) is _expected, 'quality_equal сравнивает исходную абсолютную разность с включённой границей tol; не округляйте R².'
for _a,_b,_tol,_expected in [(0.,5e-10,1e-12,False),(.2,.2000001,1e-5,True),(1.,1.,0.,True)]:
    assert bool(_equal(_a,_b,_tol)) is _expected and bool(_equal(_b,_a,tol=_tol)) is _expected, 'quality_equal должна использовать переданный tol, в том числе по имени.'
""")
section('05-project.md','hidden-quality',hidden_quality)

def clock_alias_check(b):
    start=b.index('_original_clock = _t.perf_counter')
    end=b.index('\n```',start)
    code="""def _check_clock_minimum(_candidate):
    # Originals stay in locals; rebinding a learner global cannot replace them.
    _original = _t.perf_counter
    _globals = getattr(_candidate, '__globals__', {})
    _aliases = {name:value for name,value in list(_globals.items()) if value is _original}
    try:
        for _durations,_expected in [([.004,0,.002,.003],0.0),([.004,.001,.002,.003],.001)]:
            _ticks=iter([tick for i,duration in enumerate(_durations) for tick in (float(i),float(i)+duration)])
            def _clock():
                return next(_ticks)
            _t.perf_counter=_clock
            for _name in _aliases:
                _globals[_name]=_clock
            _count=[]
            _measured=_candidate(lambda:_count.append(1),4)
            assert len(_count)==4 and close(_measured,_expected,1e-10), 'best_time должен вернуть реальный минимум; нулевой минимум допустим, постоянный ноль не подходит.'
    finally:
        _t.perf_counter=_original
        _globals.update(_aliases)
_check_clock_minimum(f)
"""
    return b[:start]+code+b[end:]
section('02b-vectorize.md','best-of',clock_alias_check)

# A supplied clock hook permits deterministic coarse/slow-clock acceptance tests.
TIMER='''import time as _timer_time
import copy as _timing_copy
_measurement_clock = lambda: _timer_time.perf_counter()
_timing_records = []

def timed_call(label, function, *args):
    # Copying is outside the measured interval: only the actual call is timed.
    inputs = _timing_copy.deepcopy(args)
    start = _measurement_clock()
    result = function(*args)
    elapsed = float(_measurement_clock() - start)
    snapshot = _timing_copy.deepcopy(result)
    _timing_records.append(dict(label=label, seconds=elapsed, inputs=inputs, result=snapshot))
    return result, elapsed
'''
TIMER_CHECK='''
import pandas as _timing_pd
def _timing_equal(actual, expected):
    if isinstance(expected, (_timing_pd.DataFrame, _timing_pd.Series)):
        return isinstance(actual, type(expected)) and actual.equals(expected)
    actual, expected = _np.asarray(actual), _np.asarray(expected)
    return actual.shape == expected.shape and _np.array_equal(actual, expected)
def _timing_matches(label, seconds, inputs, output):
    for record in _timing_records:
        if record['label'] != label or not close(record['seconds'], seconds, 1e-12):
            continue
        if len(record['inputs']) != len(inputs) or not all(_timing_equal(got,want) for got,want in zip(record['inputs'],inputs)):
            continue
        got, want = _np.asarray(record['result']), _np.asarray(output)
        if got.shape == want.shape and _np.allclose(got, want):
            return True
    return False
for _label,_seconds,_inputs,_output in TIMING_OPERATIONS:
    assert _timing_matches(_label,_seconds,_inputs,_output), 'Измерьте требуемую операцию на полном входе через timed_call: вход, результат и сохранённое время должны относиться к одному реальному вызову.'
'''
def timed_task(b,loop,vec):
    title='Замерьте обе функции'
    # Preserve original prose except the measuring API and zero-case rule.
    if vec=='pay_vec':
        b=b.replace('Замерьте обе функции через `time.perf_counter()`:', 'Выданный `timed_call(label, function, *args)` вызывает функцию на переданном полном входе, измеряет её через `time.perf_counter()` и возвращает `(результат, секунды)`. Он сохраняет вход и результат для проверки операции; их копирование выполняется вне измеряемого интервала. Собственная обёртка может вызывать этот помощник и выбирать минимум повторов. Замерьте `a, t_loop = timed_call("loop", pay_loop, km, rain)` и `b, t_vec = timed_call("vec", pay_vec, km, rain)`:')
        b=b.replace('`t_loop / t_vec`)', '`t_loop / t_vec`, а при нулевом `t_vec` — `None`)')
    else:
        b=b.replace('Замерьте обе функции (`t_loop`, `t_vec`, секунды) и сохраните `speedup`.', 'Выданный `timed_call(label, function, *args)` вызывает функцию на переданном полном входе, измеряет её через `time.perf_counter()` и возвращает `(результат, секунды)`. Он сохраняет вход и результат для проверки операции; их копирование выполняется вне измеряемого интервала. Собственная обёртка может вызывать этот помощник и выбирать минимум повторов. Вызовите `a, t_loop = timed_call("loop", nearest_loop, orders, shops)` и `b, t_vec = timed_call("vec", nearest_vec, orders, shops)`. Сохраните `speedup = t_loop / t_vec`, а при нулевом `t_vec` — `None`.')
    if vec=='nearest_vec':
        b=b.replace('Функция возвращает номер ближайшей кофейни для каждого заказа.', 'Функция возвращает номер ближайшей кофейни для каждого заказа. При равной дистанции выбирайте кофейню с меньшим номером.')
    b=b.replace('### starter\n','### setup\n```python\n'+TIMER+'```\n\n### starter\n',1)
    pattern=r't0 = time.perf_counter\(\)\na = '+loop+r'\(([^\n]*)\)\nt_loop = time.perf_counter\(\) - t0\n\nt0 = time.perf_counter\(\)\nb = '+vec+r'\(([^\n]*)\)\nt_vec = time.perf_counter\(\) - t0'
    b,n=re.subn(pattern,lambda m:f'a, t_loop = timed_call("loop", {loop}, {m[1]})\nb, t_vec = timed_call("vec", {vec}, {m[2]})',b)
    assert n==1,(vec,n)
    b=b.replace('speedup = t_loop / t_vec\n','speedup = t_loop / t_vec if t_vec > 0 else None\n')
    b=b.replace('{speedup:.0f}','{speedup}')
    b=b.replace("assert calls('perf_counter') >= 4, 'Замерьте реальные вызовы обеих функций через perf_counter; ускорение диагностическое.'",'')
    b=b.replace("assert tl > 0 and tv > 0, 't_loop и t_vec — положительные длительности в секундах.'","assert _np.isfinite(tl) and _np.isfinite(tv) and tl >= 0 and tv >= 0, 'Длительности конечные и неотрицательные; ноль возможен у короткого вызова.'")
    b=b.replace("assert tl >= 0 and tv >= 0, 't_loop и t_vec — положительные длительности в секундах: perf_counter() после минус perf_counter() до.'","assert _np.isfinite(tl) and _np.isfinite(tv) and tl>=0 and tv>=0, 'Длительности конечные и неотрицательные.'")
    b=b.replace("assert close(need('speedup'), tl / tv, max(0.02 * tl / tv, 0.6)), f'speedup = {need(\"speedup\")}, а t_loop / t_vec = {tl / tv:.1f}.'", "assert (close(need('speedup'),tl/tv,max(.02*tl/tv,.6)) if tv>0 else need('speedup') is None), 'speedup — отношение времен, при нулевом t_vec None.'")
    b=re.sub(r'^assert tl / tv > 2,.*\n','',b,flags=re.M)
    if vec=='pay_vec':
        b=b.replace('Замер: `t0 = time.perf_counter()`, затем `a = pay_loop(km, rain)`, затем `t_loop = time.perf_counter() - t0`. То же для `pay_vec`.', 'Замеры: `a, t_loop = timed_call("loop", pay_loop, km, rain)` и `b, t_vec = timed_call("vec", pay_vec, km, rain)`. При `t_vec == 0` запишите `speedup = None`. Фиксированного ускорения на любой машине нет.')
    else:
        # Check on changed arrays/shop count, preserving Manhattan ties by argmin first index.
        b=check_append(b,"""
for _orders,_shops in [(_np.array([[0.,0.],[1.,2.],[8.,3.]]),_np.array([[0.,1.],[7.,2.]])),(_np.array([[3.,4.]]),_np.array([[2.,4.],[4.,4.],[10.,10.]]))]:
    _want=_np.abs(_orders[:,None,:]-_shops[None,:,:]).sum(axis=2).argmin(axis=1)
    assert _np.array_equal(need('nearest_vec')(_orders,_shops),_want), 'nearest_vec должна работать на новых заказах и другом числе кофеен.'
""")
    operations = "[('loop',need('t_loop'),(_km,_rain),_p),('vec',need('t_vec'),(_km,_rain),_p)]" if vec=='pay_vec' else "[('loop',need('t_loop'),(_o,_s),_w),('vec',need('t_vec'),(_o,_s),_w)]"
    return check_append(b,TIMER_CHECK.replace('TIMING_OPERATIONS',operations))
section('02b-vectorize.md','vectorize',lambda b:timed_task(b,'pay_loop','pay_vec'))
section('02b-vectorize.md','nearest-shop',lambda b:timed_task(b,'nearest_loop','nearest_vec'))

def apply_col(b):
    b=b.replace('Замерьте обе версии через `best_time`: `t_apply`, `t_col`; сохраните `speedup = t_apply / t_col`', 'Для контрольного замера используйте выданный `timed_call(label, function, *args)`: он возвращает `(результат, секунды)` и сохраняет полный вход и результат вызова. Копирование выполняется вне измеряемого интервала. Вызовите `a, t_apply = timed_call("apply", lambda table: table.apply(fee_apply, axis=1), d)` и `b, t_col = timed_call("col", fee_col, d)`. Собственная обёртка может повторять такие вызовы и выбирать минимум. Функция best_time остаётся для самостоятельных последующих замеров. Сохраните `speedup = t_apply / t_col` (при нулевом `t_col` — `None`; фиксированного ускорения на любой машине нет)')
    marker='### setup\n```python\n'
    start=b.index(marker)+len(marker); end=b.index('\n```',start)
    b=b[:end]+'\n'+TIMER+b[end:]
    b=b.replace('t_apply = best_time(lambda: d.apply(fee_apply, axis=1))','a, t_apply = timed_call("apply", lambda table: table.apply(fee_apply, axis=1), d)').replace('t_col = best_time(lambda: fee_col(d))','b, t_col = timed_call("col", fee_col, d)')
    b=b.replace('speedup = t_apply / t_col\n','speedup = t_apply / t_col if t_col > 0 else None\n').replace('{speedup:.0f}','{speedup}')
    b=b.replace("assert ta > 0 and tc > 0, 't_apply и t_col — положительные времена в секундах от best_time.'", "assert _np.isfinite(ta) and _np.isfinite(tc) and ta>=0 and tc>=0, 't_apply и t_col — конечные неотрицательные времена; нулевой отсчёт допустим.'")
    b=b.replace("assert close(need('speedup'), ta / tc, max(0.02 * ta / tc, 0.6)), f'speedup = {need(\"speedup\")}, а t_apply / t_col = {ta / tc:.1f}.'", "assert (close(need('speedup'),ta/tc,max(.02*ta/tc,.6)) if tc>0 else need('speedup') is None), 'speedup — отношение времен, при нулевом t_col None.'")
    b=re.sub(r'^assert ta / tc > 2,.*\n','',b,flags=re.M)
    b=check_append(b,TIMER_CHECK.replace('TIMING_OPERATIONS',"[('apply',need('t_apply'),(d0,),_f),('col',need('t_col'),(d0,),_f)]"))
    b=check_append(b,"""
import pandas as _pd
_test=_pd.DataFrame({'items':[1,4,5,3], 'amount':[1500,1501,300,2000]},index=[7,2,9,5])
assert _np.array_equal(_np.asarray(need('fee_col')(_test)),[15,0,60,0]), 'fee_col должна считать на новой таблице и границе 1500 рублей.'
""")
    # The hint must name the same measurement interface as the public contract.
    b=b.replace('Замерьте оба варианта через `best_time`', 'Замерьте оба варианта через выданный `timed_call`')
    return b
section('02b-vectorize.md','apply-col',apply_col)

p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
patch=''
for path,new in changes.items():
    old=path.read_text()
    patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(path.relative_to(ROOT)),tofile=str(path.relative_to(ROOT))))
(HERE/'proposal.patch').write_text(patch)
if a.apply:
    for path,text in changes.items():path.write_text(text)
    print('Applied proposal to',len(changes),'files; coordinator must export after-tasks and migrate timer API tests.')
else: print('Prepared proposal.patch only:',len(changes),'files; no content writes.')
