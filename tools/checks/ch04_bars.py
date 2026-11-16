# Shared by chapter 4 chart checks through include-check; no student-code execution here.
def _check_category_bars(ax, expected, *, horizontal=False):
    import numpy as _np

    ax.figure.canvas.draw()
    patches = list(ax.patches)
    ticks = ax.get_yticks() if horizontal else ax.get_xticks()
    texts = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    labels = [(float(position), text.get_text()) for position, text in zip(ticks, texts) if text.get_visible()]
    assert len(patches) == len(expected), f'Столбцов {len(patches)}, а категорий {len(expected)}: нужен столбец для каждой категории.'
    assert len(labels) == len(expected) and {name for _, name in labels} == set(expected), 'Подпишите каждую категорию ровно один раз; названия должны соответствовать данным.'
    result = []
    seen = set()
    for patch in patches:
        position = (patch.get_y() + patch.get_height() / 2 if horizontal
                    else patch.get_x() + patch.get_width() / 2)
        matching = [name for tick, name in labels if _np.isclose(tick, position, rtol=0, atol=1e-7)]
        assert len(matching) == 1, 'Подпись категории должна стоять напротив своего столбца.'
        name = matching[0]
        assert name not in seen, f'Для категории «{name}» нарисовано несколько столбцов.'
        seen.add(name)
        origin = patch.get_x() if horizontal else patch.get_y()
        assert _np.isclose(origin, 0, rtol=0, atol=1e-7), f'«{name}»: количественный столбец должен начинаться от 0, а не от {origin:g}.'
        value = patch.get_width() if horizontal else patch.get_height()
        assert _np.isfinite(value) and _np.isclose(value, expected[name], rtol=1e-9, atol=1e-6), f'«{name}»: на графике {value:g}, а по данным нужно {expected[name]:g}. Проверьте пару «подпись — значение».'
        screen = ax.transData.transform((0, position) if horizontal else (position, 0))
        # Read the chart as the viewer sees it: top to bottom, or left to right.
        visual_position = -float(screen[1]) if horizontal else float(screen[0])
        result.append((visual_position, name, float(value)))
    return [(name, value) for _, name, value in sorted(result)]
