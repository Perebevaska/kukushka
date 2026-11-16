"""Narrow source editor: re-read the file before replacing only a task's check block."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def edit(lesson,task,fn):
 p=ROOT/'content/ch04'/f'{lesson}.md'
 s=p.read_text()
 pattern=re.compile(r'(^## task: '+re.escape(task)+r' \|.*?^### check\n```python\n)(.*?)(\n```)',re.M|re.S)
 m=pattern.search(s);assert m,(lesson,task)
 new=fn(m[2]);assert new!=m[2],(lesson,task,'no change')
 p.write_text(s[:m.start(2)]+new+s[m.end(2):])

edit('01-plots','labeled',lambda s:s.replace('import pandas as _pd','# include-check: ch04_bars.py\nimport pandas as _pd',1)+'''
visible = _check_category_bars(ax, rev.to_dict())
assert [v for _, v in visible] == sorted(rev.values, reverse=True), 'Выручка каналов должна убывать слева направо; сохраняйте пары подпись — значение.'
'''.rstrip())
edit('02-histograms','five-min',lambda s:s+'''
import numpy as _np
_counts, _edges = _np.histogram(t, bins=24, range=(0,120))
_bars = sorted(ax.patches, key=lambda p:p.get_x())
assert all(close(p.get_x(),x) and close(p.get_width(),w) and close(p.get_y(),0) and close(p.get_height(),n) for p,x,w,n in zip(_bars,_edges[:-1],_np.diff(_edges),_counts)), 'Каждая корзина шириной 5 минут должна показывать своё число доставок; нельзя переставлять частоты между интервалами.'
'''.rstrip())

edit('02b-shape','ufa-empty',lambda s:s.replace("assert len(s) == len(days) and [int(x) for x in s.values] == [int(x) for x in pdw.values],", "assert s.index.is_unique and set(s.index) == set(days) and [int(x) for x in s.reindex(days).values] == [int(x) for x in pdw.values],"))
edit('03-boxplots','slow',lambda s:s.replace("assert (okk['slow'].values == slow.values).all(), 'slow не совпадает: границу нужно считать внутри каждой группы курьеров.'",'''assert 'delivery_id' in okk.columns and okk['delivery_id'].is_unique, 'Сохраните уникальный delivery_id каждой доставки.'
assert set(okk['delivery_id']) == set(o['delivery_id']), 'В ok должны остаться исходные доставки со временем 1–299 минут.'
want_slow = _pd.Series(slow.values,index=o['delivery_id'])
got_slow = okk.set_index('delivery_id')['slow'].reindex(want_slow.index)
assert (got_slow.values == want_slow.values).all(), 'slow не совпадает по delivery_id: границу нужно считать внутри каждой группы курьеров.' '''.rstrip()))
edit('04-slices','share-snow',lambda s:s+'''
assert c.index.is_unique and c.columns.is_unique and set(c.index)==set(want.index) and set(c.columns)==set(want.columns), 'Сохраните все подписи courier и weather в ct.'
assert all(close(c.loc[row,col],want.loc[row,col],1e-9) for row in want.index for col in want.columns), 'В ct неверна пара курьер — погода: нужны доли разных курьеров внутри каждой погоды.'
'''.rstrip())
edit('05-time','rolling',lambda s:s+'''
assert got.index.is_unique and set(got.index)==set(s.index), 'Индекс smooth — исходные календарные даты.'
_got = got.reindex(s.index)
assert (_got.isna()==s.isna()).all() and all(close(a,b,1e-6) for a,b in zip(_got.dropna(),s.dropna())), 'В smooth проверьте каждое среднее по семи дням, включая середину периода; первые шесть значений — NaN.'
'''.rstrip())
edit('05b-cohorts','age',lambda s:s.replace("assert (a.values == w.values).all(),", "assert a.index.is_unique and a.columns.is_unique and set(a.index)==set(w.index) and set(a.columns)==set(w.columns), 'Сохраните подписи когорт и месяцев жизни.'\nassert (a.loc[w.index,w.columns].values == w.values).all(),"))
edit('05c-dau-mau','sticky-city',lambda s:s.replace("t = j.pivot_table(index='date', columns='city', values='guest_id', aggfunc='nunique')", "t = j.pivot_table(index='date', columns='city', values='guest_id', aggfunc='nunique').reindex(_pd.date_range('2026-06-01','2026-06-30')).fillna(0)").replace("s = need('city_sticky', _pd.Series)","s = need('city_sticky', _pd.Series)\nassert s.index.is_unique, 'Каждый город должен встречаться в city_sticky ровно один раз.'"))
edit('06-correlation','spearman',lambda s:s.replace("dropna(subset=['actual_min'])","dropna(subset=['distance_km','actual_min'])"))

def no_pie(s):
 a=s.index('w = [p.get_width()');b=s.index("assert ax.get_xlabel()",a)
 return s[:a]+'''visible = _check_category_bars(ax, share.to_dict(), horizontal=True)
assert [v for _,v in visible] == sorted(share.values,reverse=True), 'Доли выручки должны убывать сверху вниз: лидер наверху, сохраняйте подписи напитков.'
'''+s[b:]
edit('07-readable','no-pie',lambda s:no_pie(s).replace('import pandas as _pd','# include-check: ch04_bars.py\nimport pandas as _pd',1))
def title(s):
 s=s.replace('import pandas as _pd','# include-check: ch04_bars.py\nimport pandas as _pd',1)
 s='\n'.join(line for line in s.splitlines() if not line.startswith('assert uses_fstring()'))
 a=s.index('h = [p.get_height()');b=s.index("assert ax.get_ylabel()",a)
 return s[:a]+'''visible = _check_category_bars(ax, m.to_dict())
assert [v for _,v in visible] == sorted(m.values,reverse=True), 'Медианы должны убывать в видимом порядке слева направо; при обратном порядке данных допустима invert_xaxis().'
'''+s[b:]
edit('07-readable','title',title)
edit('07c-metrics','funnel-platform',lambda s:s.replace("assert int(need('lost')) == int(lw)","assert close(need('lost'), lw, 1e-9)"))
edit('08-eda','slice-fn',lambda s:s+'''
want = t.groupby('g')['v'].agg(n='size',mean='mean').sort_values('mean',ascending=False)
assert r.index.is_unique and set(r.index)==set(want.index) and all(close(r.loc[k,c],want.loc[k,c],1e-9) for k in want.index for c in ['n','mean']), 'Проверьте n и mean в каждой группе, а не только порядок.'
other = _pd.DataFrame({'category':['z','y','z','x'],'metric':[2,8,4,0]})
answer = f(other.copy(),'category','metric')
expected = other.groupby('category')['metric'].agg(n='size',mean='mean').sort_values('mean',ascending=False)
assert isinstance(answer,_pd.DataFrame) and list(answer.columns)==['n','mean'] and list(answer.index)==list(expected.index), 'Функция должна работать с переданными df, by и col на другой таблице.'
assert all(close(answer.loc[k,c],expected.loc[k,c],1e-9) for k in expected.index for c in ['n','mean']), 'На другой таблице n — размер группы, mean — среднее переданного столбца.'
'''.rstrip())
edit('09-project','clean',lambda s:s+'''
_want = d[d['actual_min'].between(1,299)].copy()
assert 'delivery_id' in o.columns and o['delivery_id'].is_unique, 'Сохраните уникальный delivery_id каждой доставки.'
assert set(o['delivery_id'])==set(_want['delivery_id']), 'В ok нужны все исходные доставки со временем 1–299 минут.'
_got = o.set_index('delivery_id').reindex(_want['delivery_id'])
_ref = _want.set_index('delivery_id')
for _col in _ref.columns:
    assert _col in _got.columns, f'Из ok пропал исходный столбец {_col}.'
    _a, _b = _got[_col], _ref[_col]
    assert ((_a == _b) | (_a.isna() & _b.isna())).all(), f'Исходные значения {_col} изменились. В этом шаге отбираем строки, затем добавляем late, delay и hour.'
'''.rstrip())

def compare(s):
 a=s.index('area = sum(');b=s.index('want = ',a)
 return s[:a]+'''import numpy as _np
from matplotlib.container import BarContainer as _BarContainer
_groups = {}
for _container in ax.containers:
    if not isinstance(_container,_BarContainer):
        continue
    _label = _container.get_label()
    # hist attaches its legend label to the first rectangle rather than the container.
    if _label not in ('вело','авто'):
        _label = next((p.get_label() for p in _container.patches if p.get_label() in ('вело','авто')),None)
    assert _label in ('вело','авто') and _label not in _groups, 'Каждую гистограмму подпишите своим типом курьера: label=... .'
    _groups[_label] = list(_container.patches)
assert set(_groups)=={'вело','авто'}, 'Нужны две гистограммы с подписями вело и авто.'
for _label,_bars in _groups.items():
    _values = ok.loc[ok['courier']==_label,'actual_min']
    _heights,_edges = _np.histogram(_values,bins=30,range=(0,90),density=True)
    _bars = sorted(_bars,key=lambda p:p.get_x())
    assert len(_bars)==30 and all(close(p.get_x(),x) and close(p.get_width(),w) and close(p.get_y(),0) and close(p.get_height(),h,1e-7) for p,x,w,h in zip(_bars,_edges[:-1],_np.diff(_edges),_heights)), f'{_label}: сверьте каждую плотность и границы корзины. Нужны bins=30, range=(0,90), density=True; площадь каждой гистограммы равна 1.'
    assert all(close(p.get_alpha(),.5) for p in _bars), 'Полупрозрачность обеих гистограмм — alpha=0.5.'
'''+s[b:]
edit('02-histograms','compare',compare)
