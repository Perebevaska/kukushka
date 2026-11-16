import numpy as _np
from matplotlib.container import BarContainer as _BarContainer
from matplotlib.patches import Polygon as _Polygon, StepPatch as _StepPatch
from matplotlib.colors import to_rgba as _rgba


def _histogram_series(axis, edges):
    """Recover the displayed bin heights from rectangles or a stepped outline."""
    series = []
    used = set()
    for container in axis.containers:
        if not isinstance(container, _BarContainer):
            continue
        bars = sorted(container.patches, key=lambda bar: bar.get_x())
        assert len(bars) == len(edges) - 1, 'Проверьте число корзин каждого распределения.'
        assert all(_np.isclose(b.get_x(), lo) and _np.isclose(b.get_width(), hi-lo) and _np.isclose(b.get_y(), 0)
                   for b, lo, hi in zip(bars, edges, edges[1:])), 'Проверьте границы интервалов и нулевое начало столбцов.'
        used.update(bars)
        series.append((bars, _np.array([bar.get_height() for bar in bars])))
    for patch in axis.patches:
        if patch in used:
            continue
        if isinstance(patch, _StepPatch):
            data = patch.get_data()
            assert _np.array_equal(data.edges, edges), 'Проверьте границы ступенчатой гистограммы.'
            assert data.baseline is None or _np.allclose(data.baseline, 0), 'Начало отсчёта частот — ноль.'
            series.append(([patch], _np.asarray(data.values)))
            continue
        assert isinstance(patch, _Polygon), 'Постройте гистограмму с указанными корзинами.'
        vertices = patch.get_xy()
        top = vertices[1:2*len(edges)-1]
        assert len(top) == 2*(len(edges)-1), 'Проверьте число и границы ступеней.'
        assert _np.allclose(top[::2,0], edges[:-1]) and _np.allclose(top[1::2,0], edges[1:]), 'Границы корзин не совпадают с заданными.'
        assert _np.allclose(top[::2,1], top[1::2,1]) and _np.isclose(vertices[0,1],0) and _np.allclose(vertices[2*len(edges)-1:,1],0), 'Высота постоянна внутри корзины, начало отсчёта — ноль.'
        series.append(([patch], top[::2,1]))
    return series


def _histogram_style(artist):
    if hasattr(artist, 'get_facecolor'):
        face = artist.get_facecolor()
        color = face if face[-1] > 0 else artist.get_edgecolor()
        return _rgba(color)[:3], artist.get_hatch() or ''
    return _rgba(artist.get_color())[:3], ''
