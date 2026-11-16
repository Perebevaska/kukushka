import nbformat as nbf
from pathlib import Path
root=Path(__file__).parent
p=root/'promise.ipynb'
nb=nbf.read(p,as_version=4)
# Repeated run should update the added cells, not duplicate them.
nb.cells=[c for c in nb.cells if 'retest_boundary' not in c.metadata.get('tags',[])]
def tagged(c):
 c.metadata['tags']=['retest_boundary'];return c
nb.cells.insert(-1,tagged(nbf.v4.new_markdown_cell('''## Повтор: полная точность и показанные границы

План уже зафиксировал δ=10 ₽. В X и Y исправный SRM (p=0.42), снижение опозданий −8.1 п.п. при p=0.003. До вычисления ожидаю X «внедрять», Y «неопределённо»: −9.96 > −10, а −10.04 < −10 при верхней границе выше порога. Округлённая подпись нижней границы в обоих случаях −10.0 ₽ и не подходит для сравнения.''')))
nb.cells.insert(-1,tagged(nbf.v4.new_code_cell('''def decide_from_full_bounds(srm_p, late_diff_pp, late_p, rev_lo, rev_hi, delta=10):
    if srm_p < .01 or not (late_diff_pp < 0 and late_p < .05) or rev_hi < -delta:
        return "не внедрять"
    if rev_lo > -delta:
        return "внедрять"
    return "неопределённо"

boundary_rows = []
for name, lo_full, hi_full in [("X", -9.96, 7.84), ("Y", -10.04, 7.76)]:
    boundary_rows.append({
        "пример": name, "delta": 10, "srm_p": .42,
        "late_diff_pp": -8.1, "late_p": .003,
        "rev_lo_full": lo_full, "rev_hi_full": hi_full,
        "решение": decide_from_full_bounds(.42, -8.1, .003, lo_full, hi_full),
        "нижняя_для_отчёта": f"{lo_full:.1f}",
        "верхняя_для_отчёта": f"{hi_full:.1f}"
    })
boundary_decisions = pd.DataFrame(boundary_rows).set_index("пример")
display(boundary_decisions)
assert boundary_decisions.loc["X", "решение"] == "внедрять"
assert boundary_decisions.loc["Y", "решение"] == "неопределённо"
boundary_decisions.to_json("boundary-decisions.json", orient="index", force_ascii=False, indent=2)
''')))
nb.cells.insert(-1,tagged(nbf.v4.new_markdown_cell('''### Проверка сохранённых границ по городам

Вызов функции отчёта по срезу допустим после проверки наличия A/B среди всех сессий, заказов и ближней зоны. Полные границы ниже сохраняются рядом с решением и отдельно от округлённого итогового словаря.''')))
nb.cells.insert(-1,tagged(nbf.v4.new_code_cell('''full_report_rows = []
for name, x in [("вся выгрузка", ab), *list(ab.groupby("city"))]:
    assert set(x.group) == {"A", "B"}
    assert set(x.loc[x.ordered.eq(1), "group"]) == {"A", "B"}
    assert set(x.loc[x.distance_km < 2, "group"]) == {"A", "B"}
    a_full = x.loc[x.group.eq("A"), "amount"]
    b_full = x.loc[x.group.eq("B"), "amount"]
    difference_full = b_full.mean() - a_full.mean()
    error_full = np.sqrt(a_full.var(ddof=1)/len(a_full) + b_full.var(ddof=1)/len(b_full))
    lower_full, upper_full = difference_full - 1.96*error_full, difference_full + 1.96*error_full
    r = promise_report(x)
    full_report_rows.append({"срез": name, "rev_diff_full": difference_full,
                             "rev_lo_full": lower_full, "rev_hi_full": upper_full,
                             "decision": r["decision"], "shown_lo": f"{lower_full:.1f}",
                             "shown_hi": f"{upper_full:.1f}"})
full_decisions = pd.DataFrame(full_report_rows).set_index("срез")
display(full_decisions)
full_decisions.to_json("promise-full-decisions.json", orient="index", force_ascii=False, indent=2)
''')))
nb.cells.append(tagged(nbf.v4.new_markdown_cell('''### Уточнения после повторного чтения

Симуляция подтверждает согласованность вычислений в принятой модели, но не независимость реальных доставок. Доверительный интервал относится к параметру и процедуре; не присваиваю фиксированному среднему вероятность 95%. Для пуша интервал прироста 0.52…3.56 п.п. выше нуля, однако не подтверждает достижение полезного порога 2 п.п.; без данных об отписках полного основания для массового запуска нет. MDE характеризует обнаружение эффекта с заданной мощностью, а бизнес-порог — его полезность.

Выручка на покупателя — условная описательная метрика: состав покупателей мог измениться при назначении варианта. Нельзя по незначимому p объявить её неизменной и доказать, что весь причинный эффект ARPU вызван одной конверсией. В проекте доля опозданий также относится к заказам после назначения; изменение отбора заказов и отсутствие постоянного ID ограничивают перенос результата на тех же людей и долгосрочное удержание.
''')))
for c in nb.cells:
 if c.cell_type=='code': c.outputs=[];c.execution_count=None
nbf.write(nb,p)
