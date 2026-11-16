"""Check the displayed group curves, including their visible legend association."""
from pathlib import Path
D=Path(__file__).resolve().parents[1];p=D.parents[2]/'content/ch08/05-explain.md';s=p.read_text()
a,tail=s.split('## task: pd-two |',1);body,sep,end=tail.partition('\n## task: ')
before,rest=body.split('### check\n```python\n',1);check,after=rest.split('\n```',1)
start=check.index('ax = ax_of(0)')
new='''import numpy as _np
from matplotlib.colors import to_rgba as _rgba
ax=ax_of(0)
ax.figure.canvas.draw()
assert ax.get_visible() and ax.figure.get_visible() and ax.axison, 'Покажите график двух частичных зависимостей.'
assert ax.get_xlabel()=='дней с последнего визита', 'Подпишите ось X: «дней с последнего визита».'
assert ax.xaxis.label.get_visible() and _rgba(ax.xaxis.label.get_color(),alpha=ax.xaxis.label.get_alpha())[3]>0, 'Подпись оси X должна быть видна.'
legend=ax.get_legend()
texts=list(legend.get_texts()) if legend else []
labels=[t.get_text() for t in texts]
assert legend and legend.get_visible() and 'новички' in labels and 'остальные' in labels, 'Нужна видимая легенда «новички» и «остальные».'
assert all(t.get_visible() and _rgba(t.get_color(),alpha=t.get_alpha())[3]>0 for t in texts), 'Покажите подписи групп в легенде.'
expected={'новички':_np.c_[G,wn], 'остальные':_np.c_[G,wo]}
handles=getattr(legend,'legend_handles',getattr(legend,'legendHandles',[]))
found=set()
for pos,line in enumerate(ax.lines):
    if not line.get_visible() or line.get_linestyle() in ('None','none','',' ') or line.get_linewidth()<=0 or _rgba(line.get_color(),alpha=line.get_alpha())[3]<=0:continue
    matches=[label for handle,label in zip(handles,labels) if handle.get_label()==line.get_label()]
    if len(matches)!=1:
        matches=[label for handle,label in zip(handles,labels) if hasattr(handle,'get_color') and _np.allclose(_rgba(handle.get_color()),_rgba(line.get_color())) and handle.get_linestyle()==line.get_linestyle()]
    name=matches[0] if len(matches)==1 else (labels[pos] if pos<len(labels) else None)
    if name not in expected:continue
    xy=_np.c_[line.get_xdata(),line.get_ydata()].astype(float)
    xy=ax.transData.inverted().transform(line.get_transform().transform(xy))
    if len(xy) and xy[0,0]>xy[-1,0]:xy=xy[::-1]
    if xy.shape==expected[name].shape and _np.allclose(xy,expected[name],rtol=0,atol=1e-8):found.add(name)
assert found==set(expected), 'Для каждой группы проверьте фактическую линию: пары grid и частичной зависимости должны совпадать с её расчётом. Порядок отрисовки можно менять.'
assert min(ax.get_xlim())<=G[0]+1e-8 and max(ax.get_xlim())>=G[-1]-1e-8, 'Вся сетка давности должна быть видна.'
assert min(ax.get_ylim())<=min(wn+wo)+1e-8 and max(ax.get_ylim())>=max(wn+wo)-1e-8, 'Покажите диапазон обеих частичных зависимостей.'
'''
p.write_text(a+'## task: pd-two |'+before+'### check\n```python\n'+check[:start]+new.rstrip()+'\n```'+after+sep+end)
