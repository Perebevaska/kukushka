"""Narrow one-time refinement of the current published chapter; no changes without --apply."""
import argparse,difflib,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
changes={}
def section(file,task,fn):
    path=ROOT/'content/ch09'/file;text=changes.get(path,path.read_text())
    start=text.index('## task: '+task+' |');end=text.find('\n## task:',start+1)
    if end<0:end=len(text)
    changes[path]=text[:start]+fn(text[start:end])+text[end:]
def append_check(block,code):
    start=block.index('### check\n```python\n')+len('### check\n```python\n');end=block.index('\n```',start)
    return block[:end]+'\n'+code.rstrip()+block[end:]
def model(block):
    block=block.replace('Класс должен получать число признаков из X и переобучаться при новом вызове fit.', 'Класс должен получать число признаков из X и переобучаться при новом вызове fit. Решение должно сохранять точность на почти постоянном признаке и работать при точно дублирующихся столбцах: в таких случаях проверяется прогноз, а не конкретный выбор неоднозначных коэффициентов.')
    return append_check(block,"""
# The public direct-least-squares contract includes small variation and rank deficiency.
for _train,_target,_new,_expected in [(_np.array([[1.],[1.+1e-8],[1.-1e-8]]),1.-_np.array([1.,1.+1e-8,1.-1e-8]),_np.array([[2.]]),_np.array([-1.])),(_np.array([[0.,0.],[1.,1.],[2.,2.]]),_np.array([0.,1.,2.]),_np.array([[3.,3.]]),_np.array([3.]))]:
    try:
        _stable=C().fit(_train,_target)
        _forecast=_np.asarray(_stable.predict(_new),dtype=float)
    except Exception as _error:
        raise AssertionError('fit должен находить решение МНК и при почти постоянном признаке или дублирующихся столбцах; используйте устойчивое решение на расширенной матрице.') from _error
    assert _forecast.shape==_expected.shape and _np.allclose(_forecast,_expected,rtol=0,atol=1e-6), 'Проверьте прогноз при малом изменении признака и при точном дублировании; нормальные уравнения могут потерять точность.'
""")
section('03b-own-model.md','my-class',model)

def timer(block,kind):
    block=block.replace('Собственная обёртка может', 'Переданная функция должна рассчитывать результат и на другом наборе аргументов той же структуры; проверка вызывает её отдельно вне измеренного интервала. Собственная обёртка может',1)
    old='_timing_records.append(dict(label=label, seconds=elapsed, inputs=inputs, result=snapshot))'
    assert old in block
    block=block.replace(old,'_timing_records.append(dict(label=label, function=function, seconds=elapsed, inputs=inputs, result=snapshot))',1)
    if kind=='vectorize':
        probe="_probe_inputs=(_np.array([0.,8.,8.1,12.5]),_np.array([True,False,True,False]))\n_probe_km,_probe_rain=_probe_inputs\n_probe_output=(60+14*_probe_km+_np.where(_probe_km>8,100,0))*_np.where(_probe_rain,1.3,1.)\n"
    elif kind=='nearest-shop':
        probe="_probe_inputs=(_np.array([[3.,4.],[0.,0.],[5.,5.]]),_np.array([[2.,4.],[4.,4.],[10.,10.]]))\n_probe_orders,_probe_shops=_probe_inputs\n_probe_output=_np.abs(_probe_orders[:,None,:]-_probe_shops[None,:,:]).sum(axis=2).argmin(axis=1)\n"
    else:
        probe="_probe_inputs=(_timing_pd.DataFrame({'items':[2,4,5,3], 'amount':[1500,1501,300,2000]},index=[10,8,2,7]),)\n_probe_output=_np.array([30,0,60,0])\n"
        # Current public/solution already use one-argument callbacks; retain this explicit API.
        assert 'lambda table: table.apply(fee_apply, axis=1), d)' in block
        assert 'timed_call("col", fee_col, d)' in block
        block=block.replace('# готово, как в теории: d, best_time','# готово, как в теории: d, timed_call, best_time')
    marker='def _timing_matches(label, seconds, inputs, output):'
    assert marker in block
    block=block.replace(marker,probe+marker,1)
    old='''        if got.shape == want.shape and _np.allclose(got, want):
            return True'''
    new='''        if got.shape == want.shape and _np.allclose(got, want):
            try:
                probe_result = _np.asarray(record['function'](*_timing_copy.deepcopy(_probe_inputs)))
            except Exception:
                continue
            if probe_result.shape == _probe_output.shape and _np.allclose(probe_result,_probe_output):
                return True'''
    assert old in block;block=block.replace(old,new,1)
    block=block.replace('for record in _timing_records:', 'for record in list(_timing_records):',1)
    block=block.replace('вход, результат и сохранённое время должны относиться к одному реальному вызову.', 'вход, результат и сохранённое время должны относиться к одному реальному вызову; переданная функция должна считать и на новом входе.')
    return block
for task in ['vectorize','nearest-shop','apply-col']:
    section('02b-vectorize.md',task,lambda block,kind=task:timer(block,kind))
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
patch=''
for path,new in changes.items():
    for m in re.finditer(r'(?m)^### (setup|check|solution)\n```python\n(.*?)\n```',new,re.S):compile(m[2],str(path)+':'+m[1],'exec')
    patch+=''.join(difflib.unified_diff(path.read_text().splitlines(True),new.splitlines(True),fromfile=str(path.relative_to(ROOT)),tofile=str(path.relative_to(ROOT))))
(HERE/'refine.patch').write_text(patch)
if args.apply:
    for path,new in changes.items():path.write_text(new)
    print('Applied narrow refinement:',len(changes),'files')
else:print('Prepared refine.patch:',len(changes),'files; content unchanged')
