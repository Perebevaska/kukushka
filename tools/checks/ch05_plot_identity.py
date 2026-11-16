"""Match displayed categories to rendered artists, independently of insertion order."""
import numpy as _np
from matplotlib.collections import LineCollection as _LineCollection
from matplotlib.colors import to_rgba as _to_rgba


def _artist_visible(artist):
    alpha = artist.get_alpha()
    return artist.get_visible() and (alpha is None or _np.all(_np.asarray(alpha) > 0))


def _color_visible(color, fallback='black'):
    if isinstance(color, str) and color == 'auto':
        color = fallback
    return _to_rgba(color)[3] > 0


def _category_ticks(ax, names):
    ax.figure.canvas.draw()
    ticks = []
    for tick in ax.xaxis.get_major_ticks():
        x = float(ax.transData.transform((tick.get_loc(), 0))[0])
        if not ax.bbox.xmin <= x <= ax.bbox.xmax:
            continue
        labels = [t for t in (tick.label1, tick.label2) if _artist_visible(t) and t.get_text().strip()]
        for label in labels:
            ticks.append((x, label.get_text().strip()))
    ticks.sort()
    assert len(ticks) == len(names) and {name for _, name in ticks} == set(names), 'На оси X нужны видимые подписи каждой группы; числовые позиции без названий не заменяют группы.'
    assert len({x for x, _ in ticks}) == len(ticks), 'Каждой группе нужна отдельная позиция X.'
    return ticks


def _visible_interval_segments(ax):
    segments = []
    for collection in ax.collections:
        if not isinstance(collection, _LineCollection) or not collection.get_visible():
            continue
        colors, widths = collection.get_colors(), collection.get_linewidths()
        alpha = collection.get_alpha()
        for i, segment in enumerate(collection.get_segments()):
            opacity = 1 if alpha is None else _np.atleast_1d(alpha)[i % _np.size(alpha)]
            if opacity <= 0 or (len(colors) and colors[i % len(colors), 3] <= 0) or (len(widths) and widths[i % len(widths)] <= 0):
                continue
            points = collection.get_transform().transform(segment)
            segments.extend(zip(points[:-1], points[1:]))
    for line in ax.lines:
        if not _artist_visible(line) or line.get_linewidth() <= 0 or line.get_linestyle() in ('None', 'none', '', ' ') or not _color_visible(line.get_color()):
            continue
        points = line.get_transform().transform(line.get_xydata())
        segments.extend(zip(points[:-1], points[1:]))
    visible = []
    for left, right in segments:
        if not _np.isfinite([left, right]).all() or abs(left[0] - right[0]) > 1e-5:
            continue
        if min(left[1], right[1]) < ax.bbox.ymin - 1e-5 or max(left[1], right[1]) > ax.bbox.ymax + 1e-5:
            continue
        if not ax.bbox.xmin <= left[0] <= ax.bbox.xmax:
            continue
        visible.append((float(left[0]), float(min(left[1], right[1])), float(max(left[1], right[1]))))
    return visible


def _has_interval(ax, segments, x, lo, hi):
    endpoints = ax.transData.transform([[0, lo], [0, hi]])[:, 1]
    low, high = sorted(endpoints)
    return any(abs(px - x) <= 1e-5 and abs(pl - low) <= 1e-5 and abs(ph - high) <= 1e-5 for px, pl, ph in segments)


def _visible_marker_points(ax):
    points = []
    for line in ax.lines:
        if not _artist_visible(line) or line.get_marker() in (None, 'None', 'none', '', ' ') or line.get_markersize() <= 0:
            continue
        if not (_color_visible(line.get_markerfacecolor(), line.get_color()) or (_color_visible(line.get_markeredgecolor(), line.get_color()) and line.get_markeredgewidth() > 0)):
            continue
        points.extend(line.get_transform().transform(line.get_xydata()))
    return _np.asarray(points)


def _text_group(text, ticks):
    box = text.get_window_extent()
    center = (box.xmin + box.xmax) / 2
    nearest = min(ticks, key=lambda item: abs(item[0] - center))
    gap = min(abs(x - nearest[0]) for x, _ in ticks if x != nearest[0])
    assert abs(center - nearest[0]) < gap * .45, 'Подпись значения должна находиться у своего столбца.'
    return nearest[1]
