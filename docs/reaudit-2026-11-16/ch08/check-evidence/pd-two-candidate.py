# Proposed replacement from ax_of onward. wn, wo, G are independent references above.
import numpy as _np
from matplotlib.colors import to_rgba as _rgba
ax=ax_of(0)
assert ax.get_visible() and ax.figure.get_visible() and ax.axison, 'Покажите график двух частичных зависимостей.'
assert ax.get_xlabel()=='дней с последнего визита', 'Подпишите ось X: «дней с последнего визита».'
legend=ax.get_legend()
labels=[t.get_text() for t in legend.get_texts()] if legend else []
assert legend and legend.get_visible() and 'новички' in labels and 'остальные' in labels, 'Нужна видимая легенда «новички» и «остальные».'
expected={'новички':_np.c_[G,wn], 'остальные':_np.c_[G,wo]}
found=set()
named=any(line.get_label() in expected for line in ax.lines)
for pos,line in enumerate(ax.lines):
    name=line.get_label() if named else (labels[pos] if pos<len(labels) else None)
    if name not in expected or not line.get_visible():continue
    if line.get_linestyle() in ('None','none','',' ') or line.get_linewidth()<=0 or _rgba(line.get_color(),alpha=line.get_alpha())[3]<=0:continue
    xy=_np.c_[line.get_xdata(),line.get_ydata()].astype(float)
    xy=ax.transData.inverted().transform(line.get_transform().transform(xy))
    if len(xy) and xy[0,0]>xy[-1,0]:xy=xy[::-1]
    if xy.shape==expected[name].shape and _np.allclose(xy,expected[name],rtol=0,atol=1e-8):found.add(name)
assert found==set(expected), 'Для каждой группы проверьте фактическую линию: все пары grid и частичной зависимости должны совпадать с её расчётом. Порядок отрисовки можно менять.'
