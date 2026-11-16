"""Build a reviewable candidate task export; never edits course sources.

Run after make_probes.py. The coordinator may move the minimal checks into
the corresponding Markdown blocks after independent review.
"""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
tasks=json.loads((HERE/'tasks-original.json').read_text())
patches={
'01-value/p-profit': '''
assert f(s,y,cost=50)==300, 'Используйте переданный cost: один TP по +400 и два FP по −50 дают 300.'
assert f(s,y,gain=1000,cost=50)==900, 'Параметры gain и cost должны работать вместе.'
assert f(_pd.Series([False]*len(y)),y,cost=50)==0, 'Без отправленных бонусов прибыль равна нулю.'
''',
'04-monitoring/p-monitor': '''
for _p,_t in [(_np.array([.3,.5,.2,.4]),.3),(_np.array([.1,.5,.2,.4]),.45)]:
    _r=f(_p,threshold=_t)
    _w=dict(leads=len(_p),mean_pred=round(float(_p.mean()),3),above=round(float((_p>_t).mean()),3))
    assert _r==_w, f'При threshold={_t} сводка {_r}, ожидалось {_w}. Выше порога означает строго >.'
''',
'05-explain/p-pd': '''
class _Other:
    def predict_proba(self,X):
        import numpy as np
        p=(X['b'].values/20).clip(0,1)
        return np.c_[1-p,p]
_other=_pd.DataFrame({'a':[2,8],'b':[3,15]},index=[31,10])
_before=_other.copy(deep=True)
assert f(_Other(),_other,'b',[0,10,20])==[0.,.5,1.], 'Используйте переданные col, grid и модель; функция должна работать с другим признаком.'
_pd.testing.assert_frame_equal(_other,_before)
''',
'07-final-project/fp-money': '''
_curve=need('curve',_pd.DataFrame)
assert {'threshold','sent','buyers','profit'}<=set(_curve), 'В curve нужны threshold, sent, buyers, profit.'
assert len(_curve)==len(_ts) and not _curve['threshold'].duplicated().any(), 'В curve нужна одна строка на каждый порог сетки.'
_sorted_curve=_curve.sort_values('threshold').reset_index(drop=True)
assert _np.allclose(_sorted_curve['threshold'],_ts,rtol=0,atol=1e-8), 'Пороги curve должны совпадать с сеткой.'
for _j,_t in enumerate(_ts):
    _row=_sorted_curve.iloc[_j]
    _send=_oof>_t
    _buyers=int((_send&(_ytr==1)).sum())
    assert _row['sent']==int(_send.sum()) and _row['buyers']==_buyers and close(_row['profit'],1600*_buyers-150*int(_send.sum()),1), f'curve: проверьте число отправок, покупателей и маржу для порога {_t}.'
'''
}
for t in tasks:
    key=t['lesson'].split('/')[-1]+'/'+t['id']
    if key in patches:t['check']+='\n'+patches[key]
    if key=='02-budget/gains-plot':
        t['check']=t['check'].split('ax = ax_of(0)')[0]+(HERE/'gains-candidate.py').read_text()
(HERE/'tasks-proposed.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
(HERE/'probes-proposed.json').write_text((HERE/'probes-original.json').read_text())
(HERE/'candidate-check-additions.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2)+'\n')
print('Prepared candidate export; course sources unchanged.')
