"""Preview the chapter 8 editorial patch. Use --apply to edit the specified checkout."""
import argparse
import ast
import difflib
import re
from pathlib import Path


def replace(text, before, after):
    if before not in text:
        raise ValueError(f"Missing source anchor: {before[:100]}")
    return text.replace(before, after)


def paragraph(text, beginning, revised):
    pattern = r"^" + re.escape(beginning) + r"[^\n]*$"
    text, n = re.subn(pattern, lambda _: revised, text, flags=re.M)
    if n != 1:
        raise ValueError(f"Expected one paragraph beginning {beginning}, found {n}")
    return text


def intro(card, instruction):
    return card.split('\n', 1)[0] + '\n\n' + instruction.strip() + '\n\n### ' + card.split('\n### ',1)[1]


def section(card, heading, body):
    before, rest = card.split('### '+heading+'\n',1)
    next_heading = rest.find('\n### ')
    tail = rest[next_heading+1:] if next_heading != -1 else ''
    return before+'### '+heading+'\n'+body.strip()+'\n\n'+tail


def hints(card, body):
    a, rest = card.split('### hint\n',1)
    return a+'### hint\n'+body.strip()+'\n\n### solution\n'+rest.split('### solution\n',1)[1]


def fenced(code):
    return '```python\n'+code.strip()+'\n```'


def fields(card, heading):
    return card.split('### '+heading+'\n```python\n',1)[1].split('\n```',1)[0]


def lesson_chapter(src):
    head,*cards = src.split('## task: ')
    head=replace(head, 'Пилот с контрольной группой показывает настоящий эффект предложения', 'Рандомизированный пилот даёт оценку среднего эффекта предложения')
    head=replace(head, '1 800 случайно выбранным гостям с картой пришло предложение', 'Из гостей с заказом до 1 июля и регистрацией до 1 июня случайно выбрали участников. 1 800 из них случайно назначили предложение')
    head=replace(head, 'Ещё 600 гостей, тоже выбранных случайно, предложения не получили', 'Ещё 600 участников предложения не получили')
    head=replace(head, '(оценка финслужбы с учётом скидки).', '(учебное допущение финслужбы для покупок с предложением и без него, до затрат на контакт). Общий лимит расходов директор пока не задал. Если предлагаете лимит, укажите его до выбора правила, а в письме покажите фактический расход 150 ₽ × число получателей.')
    head=replace(head, 'для осенней рассылки.', 'в историческом сценарии на 1 июля.')
    head=replace(head, 'А осенью, на гостях, которые абонемента ещё не покупали, этих следов не будет.', 'На дату решения эти события ещё не произошли.')
    head=paragraph(head, '**Шаг 2. Разведка (EDA).**', '''**Шаг 2. Разведка (EDA).** До просмотра связи с покупкой разделите группу «предложение» один раз через `train_test_split(off, test_size=0.25, random_state=42, stratify=off["bought"])`. Сохраните ID обучения и теста. На обучении 1 350 гостей, на тесте 450. Разрезы конверсии, квартильные границы и графики «купили / не купили» стройте только на обучении. Тест откроете после фиксации модели и правила отправки. Проверьте:''')
    head=paragraph(head,'**Ориентиры шага 2**', '''**Ориентиры шага 2** на обучении. Купили 149 из 1 350 (11,0%). По доле утренних заказов конверсия составляет 3,4%, 8,7% и 26,3% от младшей группы к старшей. По квартилям частоты — от 7,0% в первом до 16,5% в четвёртом. У зарегистрированных в приложении 13,9%, у кассы 9,0%. В Тюмени 6,0%, в остальных городах 11,2–12,8%.''')
    head=paragraph(head, 'Что получилось: абонемент', 'У гостей с высокой долей утренних заказов конверсия в обучающей группе выше. Для портрета адресатов повторите описательные расчёты по фактически выбранным ID.')
    head=replace(head,'но при оценке остальных гостей они появятся.', 'кандидаты для основного списка тоже должны иметь хотя бы один заказ.')
    head=replace(head,'До моделей ответьте на три вопроса', 'По заранее заданному сравнению двух рандомизированных групп опишите весь пилот. Эта сводка с фиксированным знаменателем не участвует в поиске признаков или порога. Ответьте на три вопроса')
    head=replace(head,'Предложение добавляет **8.5 п. п.**','Оценка прироста составляет **8.5 п. п.**')
    head=replace(head,'Рассылка всем подряд в лучшем случае выходит в ноль.', 'На 1 800 контактов оценка равна −25 200 ₽. Приблизительный 95%-й интервал по разности двух долей составляет от −47 до +15 ₽ на контакт при фиксированных V и C.')
    head=paragraph(head, '**Бизнес-метрика проекта**', '''**Бизнес-метрика проекта** — дополнительная маржа по сравнению с отказом от контакта. Маржа получателей после расходов равна `V × покупки − C × контакты`. Для решения вычтите `V × ожидаемые покупки без контакта`. Если финансовая служба даёт разные маржи покупки, используйте `V₁ × покупки с предложением − V₀ × ожидаемые органические покупки − C × контакты`. ROC-AUC помогает сравнивать модели.''')
    head=paragraph(head,'1. **Отложите тест**','1. **Возьмите сохранённое разбиение шага 2**. При упомянутой сортировке гостей и стратификации в тесте 450 гостей, 49 покупателей. До фиксации модели и порога тест остаётся закрытым.')
    head=replace(head, 'Выберите порог по дополнительной марже и ограничению бюджета, запишите правило выбора.', 'Пороги с пустым контролем исключите: органическая доля для них неизвестна. Выберите допустимое правило по дополнительной марже, заранее объявите лимит, если он есть, и зафиксируйте порог. Только затем один раз откройте тест. Для письма сообщите число адресатов и проверьте расход по этому же правилу на кандидатах. Если допустимые предложения проигрывают отказу с 0 ₽, отложите запуск.')
    head=replace(head,'СтратегияА', 'Стратегия А').replace('СтратегияБ','Стратегия Б').replace('дополнительный−','дополнительный −')
    head=replace(head,'к гостям вне пилота с покупками до среза.', 'к гостям вне пилота с заказом до 1 июля и регистрацией до 1 июня 2026 года. Это критерии включения в пилот. Июньские регистрации проверьте в отдельном пилоте.')
    head=replace(head,'{{practice: fp-portrait, fp-groups}}','{{practice: fp-portrait}}')
    head=replace(head,'{{practice: fp-honest}}','{{practice: fp-honest, fp-groups}}')
    head=replace(head,'Сравните с рассылкой всем и с отказом от рассылки.', 'Сравните с рассылкой всем подходящим кандидатам и с отказом от рассылки (0 ₽ дополнительной маржи). Укажите число покупок и размер контрольного сегмента. Использованный при выборе порога контроль даёт предварительную оценку: неопределённость модели, выбора правила и переноса на новую дату требует независимого пилота.')
    head=replace(head,'Порог выбран по прибыли без теста и проверен по дополнительной марже;', 'Порог зафиксирован по дополнительной марже на обучении и поддержан контрольными наблюдениями;')
    head=replace(head,'Разведка: минимум три разреза конверсии и выводы по ним','Разведка: минимум три разреза конверсии только на обучающих ID и выводы по ним')
    head=replace(head,'ROC-AUC моделей около 0.8, а не 0.9+', 'перечень признаков и даты исходных событий')
    head=replace(head,'Модель выбрана с учётом разброса, а не только третьего знака.', 'Модель и единый порог зафиксированы до открытия теста. В портрете, проверке групп и письме использовано то же правило.')
    head=head.replace('На прогнозах вне фолда отдельно посчитайте', 'После фиксации порога на прогнозах вне фолда отдельно посчитайте')
    blocks={}
    for block in cards:
        key=block.split(' | ',1)[0]
        blocks[key]=block
    ed=blocks['fp-eda']
    ed=intro(ed,'''Признаки на 1 июля и таблица участников пилота уже загружены. В заготовке `off` содержит только 1 350 обучающих гостей с предложением из разбиения шага 2. Сохраните три Series конверсии с округлением до трёх знаков: `by_morning` по интервалам доли утренних заказов [0, 0.2], (0.2, 0.5], (0.5, 1] с подписями «до 0.2», «0.2–0.5», «выше 0.5»; `by_source` по source; `by_city` по city. Сохраните в `n_top` размер верхней утренней группы, в `lift_top` отношение её конверсии к средней на обучении (два знака).''')
    split_code='''from sklearn.model_selection import train_test_split

offered = pilot.loc[pilot["group_name"] == "предложение"].merge(data, on="guest_id", validate="one_to_one")
off, _ = train_test_split(offered, test_size=0.25, random_state=42, stratify=offered["bought"])'''
    ed=replace(ed, 'off = pilot[pilot["group_name"] == "предложение"].merge(data, on="guest_id", validate="one_to_one")',split_code)
    ed=replace(ed,'_lab = ["до 0.2", "0.2–0.5", "выше 0.5"]','from sklearn.model_selection import train_test_split as _split\n_o, _ = _split(_o, test_size=0.25, random_state=42, stratify=_o["bought"])\n_lab = ["до 0.2", "0.2–0.5", "выше 0.5"]')
    ed=section(ed,'explain','На обучении в верхней утренней группе купили 87 из 331 гостя (26,3%). Это в 2,38 раза выше среднего обучения (149/1350). У гостей с долей до 0,2 купили 17 из 501 (3,4%). Сравнение описывает покупки при предложении. Об эффекте контакта судите по сопоставимому контролю.')
    blocks['fp-eda']=ed
    blocks['fp-metric']=paragraph(blocks['fp-metric'],'С предложением купили 11.0 %','Среди получателей купили 198/1800, в контроле 15/600. При расходе 270 000 ₽ маржа покупок получателей после затрат равна +46 800 ₽. По контрольной доле без контакта ожидаются 45 покупок. Оценка дополнительной маржи равна −25 200 ₽, или −14 ₽ за контакт. Эта оценка по выборке допускает неопределённость. Сегмент с высокой конверсией при предложении тоже требует проверки органических покупок.')
    blocks['fp-money'], blocks['fp-portrait'], blocks['fp-groups'], blocks['fp-honest'] = policy_cards(
        blocks['fp-money'],blocks['fp-portrait'],blocks['fp-groups'],blocks['fp-honest'])
    return head+''.join('## task: '+s.rstrip()+'\n\n' for s in blocks.values()).rstrip()+'\n'

# Published practice cards run in separate namespaces. The starter in every downstream
# card asks for the learner's frozen threshold. The worked example uses the threshold
# from the published fp-money solution on these dated data.
ELIGIBILITY = '(data["orders_n"] > 0) & (data["reg_date"] < "2026-06-01")'
ELIGIBILITY_REF = '(_d["orders_n"] > 0) & (_d["reg_date"] < "2026-06-01")'
CONTROL = '''ctrl = pilot.loc[pilot["group_name"] == "контроль"].merge(data, on="guest_id", validate="one_to_one")'''
POLICY_CURVE = '''ctrl_p = best.predict_proba(ctrl[num + cat])[:, 1]
incr = curve.copy()
incr["control_n"] = [(ctrl_p > t).sum() for t in incr["threshold"]]
incr["organic_share"] = [ctrl.loc[ctrl_p > t, "bought"].mean() for t in incr["threshold"]]
incr["margin"] = incr["profit"] - 1600 * incr["sent"] * incr["organic_share"]
supported = incr.loc[(incr["control_n"] > 0) & (incr["margin"] >= 0)]
best_t = supported.loc[supported["margin"].idxmax(), "threshold"]'''
REF_CURVE = '''_ct = pilot.loc[pilot["group_name"] == "контроль"].merge(_d, on="guest_id")
_model = _mp(_scaled, _LR(max_iter=1000)).fit(_Xtr, _ytr)
_pc = _model.predict_proba(_ct[_num + _cat])[:, 1]
_rows = []
for _t in _ts:
    _mask = _oof > _t
    _n = int(_mask.sum())
    _buy = int(_ytr[_mask].sum())
    _control = _ct.loc[_pc > _t, "bought"]
    _gross = 1600 * _buy - 150 * _n
    _rate = _control.mean()
    _rows.append((_t, _n, _buy, _gross, len(_control), _rate, _gross - 1600 * _n * _rate))
_ref = _pd.DataFrame(_rows, columns=["threshold", "sent", "buyers", "profit", "control_n", "organic_share", "margin"]).set_index("threshold")
for _name, _cols in [("curve", ["sent","buyers","profit"]), ("incr", ["control_n","organic_share","margin"])]:
    _frame = need(_name, _pd.DataFrame)
    assert {"threshold", *_cols}.issubset(_frame.columns), f"{_name}: проверьте названия столбцов."
    _frame = _frame.set_index("threshold")
    assert _frame.index.is_unique and set(_frame.index) == set(_ref.index), f"{_name}: нужна одна строка на каждый порог сетки."
    for _col in _cols:
        assert _np.allclose(_frame.loc[_ref.index, _col], _ref[_col], rtol=1e-8, atol=1e-8, equal_nan=True), f"{_name}: проверьте {_col} у соответствующего порога."
_bt = float(need("best_t"))
assert _bt in _ref.index, "Выберите порог сетки и зафиксируйте его до открытия теста."
assert _ref.at[_bt, "control_n"] > 0, "В контроле нет гостей выше порога, органическую долю оценить нельзя."
assert _ref.at[_bt, "margin"] >= 0, "По этой кривой порог проигрывает отказу от рассылки (0 ₽). Для расчёта выберите допустимый вариант, а в письме можно предложить отказ."
_pt = _model.predict_proba(_Xte)[:, 1]
'''


def policy_cards(money, portrait, groups, honest):
    money=intro(money, '''На ценах V = 1 600 ₽ и C = 150 ₽ сначала получите прогнозы вне фолда `oof` на `X_train`. Функция `profit_curve` строит `curve` с полями threshold, sent, buyers, profit. Это маржа среди получателей после контактов. Обучите `best` только на обучающей части и получите прогнозы для сопоставимой группы `ctrl`. Для каждого порога посчитайте в таблице `incr` столбцы `threshold`, `control_n` (сколько гостей контроля выше порога), `organic_share` (доля их покупок) и `margin` (дополнительная маржа). Если нет отобранного контроля, доля и маржа неизвестны (NaN). Формула для строки: `profit − V × sent × organic_share`.

Зафиксируйте в `best_t` порог сетки с наблюдаемым контролем и неотрицательной дополнительной маржой. Обоснуйте его и ваш лимит контактов, если он есть. Для учебного примера можно взять максимальную дополнительную маржу. На этой базе допустимых порогов несколько. Если в другом пилоте все варианты убыточны или не имеют контроля, решение о запуске откладывают. Только после выбора единожды примените модель к `X_test`: сохраните число получателей `test_sent`, число купивших `test_buyers`, маржу получателей после расходов `test_profit` и аналогичный ориентир при рассылке всем в тесте `all_profit`. Без органической поправки это показатели группы получателей.''')
    money=money.replace('fp-money | Маржа среди получателей предложения', 'fp-money | Порог по дополнительной марже')
    starter=fields(money,'starter')+'\n'+CONTROL+'\n'
    money=section(money,'starter',fenced(starter))
    code=fields(money,'solution')
    first=code.index('oof = cross_val_predict')
    solution=starter+'\noof = cross_val_predict(best, X_train, y_train, cv=cv, method="predict_proba")[:, 1]\ncurve = profit_curve(oof, y_train)\nbest.fit(X_train, y_train)\n'+POLICY_CURVE+'\n'+code[code.index('send = best.predict_proba',first):]
    money=section(money,'solution',fenced(solution))
    check=fields(money,'check')
    check=check[:check.index('_pr = ')] + REF_CURVE + check[check.index('_s = _pt > _bt'):]
    money=section(money,'check',fenced(check))
    money=hints(money, '''В `curve` маржа получателей равна `1600 * buyers - 150 * sent`. Для `incr` используйте прогнозы на гостях контроля от модели, обученной на train. Для каждого порога вычтите `1600 * sent * organic_share`.

### hint
После расчёта кривых сравните поддержанные контролем пороги с нулевым результатом отказа. Пустая группа даёт неизвестную долю. Если есть лимит, сохраните подходящий порог до просмотра теста.

### hint
'''+fenced('''oof = cross_val_predict(best, X_train, y_train, cv=cv, method="predict_proba")[:, 1]
curve = profit_curve(oof, y_train)
best.fit(X_train, y_train)
ctrl_p = best.predict_proba(ctrl[num + cat])[:, 1]
# Пройдите по строкам curve. В каждой найдите число и долю покупок в контроле с ctrl_p > t.
# После выбора best_t посчитайте:
send = best.predict_proba(X_test)[:, 1] > best_t
test_sent = int(send.sum())
test_buyers = int(y_test[send].sum())'''))
    money=section(money,'explain','При правиле максимальной дополнительной маржи на этой выгрузке получаем порог 0,08. На обучении по прогнозам вне фолда это около 72,5 тыс. ₽ против 68,4 тыс. ₽ при 0,10. Для оценки маржи на тесте группа получателей даёт число купивших, но не показывает, сколько из них купили бы без контакта. В следующие шаги перенесите именно свой зафиксированный порог.')

    portrait=replace(portrait, 'свой порог `best_t` из предыдущего шага.', 'используется тот же порог дополнительной маржи `best_t`, что в fp-money.')
    portrait=replace(portrait,'гостей **не из пилота**, у которых до 1 июля были заказы', 'гостей **вне пилота** с регистрацией до 1 июня и заказом до 1 июля')
    portrait=portrait.replace('(data["orders_n"] > 0)',ELIGIBILITY).replace('(_d["orders_n"] > 0)',ELIGIBILITY_REF)
    portrait=portrait.replace('не в пилоте и orders_n > 0.', 'вне пилота, регистрация до 1 июня, есть заказы до 1 июля.')
    pc=fields(portrait,'solution')
    a=pc.index('from sklearn.model_selection import cross_val_predict')
    end=pc.index('cols = ',a)
    pc=pc[:a]+'best_t = 0.08  # зафиксировано в разобранном варианте fp-money\n'+pc[end:]
    portrait=section(portrait,'solution',fenced(pc))
    portrait=section(portrait,'explain','После ограничения по регистрации среди гостей вне пилота остаются 1 886 кандидатов. При пороге 0,08 выбраны 736. При своём пороге заново посчитайте долю утренних заказов и число гостей с давностью визита до семи дней. После 1 июля изменения активности или подписки могут изменить список.')

    groups=replace(groups, 'перенесите в `best_t` свой порог.', 'перенесите в `best_t` порог дополнительной маржи из fp-money. Это диагностика уже зафиксированной политики после её проверки на тесте.')
    groups=replace(groups, 'best_t = 0.08','best_t = 0.08  # зафиксировано в разобранном варианте fp-money')
    groups=section(groups,'explain','Сопоставьте полноту и долю отобранных по городам и возрасту при своём пороге. Назовите в каждом сравнении число гостей и купивших. Малое число покупателей оставляет широкий диапазон значений полноты. Причины различий потребуют отдельной проверки.')

    honest=intro(honest,'''В отдельную карточку перенесите `best_t` из fp-money. В блокноте продолжайте с той же переменной. Для совместимости с денежным отчётом сохраните `best_t_incr = best_t`. Модель `final` обучена на всех 1 800 гостях с предложением после проверки зафиксированного правила на тесте. Примените правило к `rest` (регистрация до 1 июня, заказ до 1 июля, вне пилота) и к сопоставимому контролю `ctrl`.

Из десяти получателей купили двое. В сопоставимом контроле доля покупок — 20%. До кода объясните, почему маржа получателей после расходов составляет +1 700 ₽, а дополнительная маржа −1 500 ₽.

Сохраните булев столбец `rest["send"]`, его сумму `n_send`, в `organic` — долю покупок в выбранном моделью final контроле (3 знака), в `exp_buyers` — сумму p по выбранным кандидатам (1 знак). По неокруглённым величинам посчитайте `naive_profit` (1 600 × сумма p − 150 × n_send) и `honest_profit` (ещё вычесть 1 600 × органическая доля × n_send). Для всех подходящих кандидатов без отбора аналогично получите `honest_all` с общей органической долей в контроле. Все три суммы в целых рублях. В письме сравните три политики, включая отказ с 0 ₽. Покажите отдельно количество покупок и знаменатель контроля. Если выбранный контроль пуст, оценка органики неизвестна. Повторный подбор порога после просмотра итогов меняет оцениваемую политику.''')
    hc=fields(honest,'solution')
    hs=hc[:hc.index('import numpy as np\nfrom sklearn.model_selection import cross_val_predict')]+'''\n'''+CONTROL+'''
final = make_pipeline(scaled, LogisticRegression(max_iter=1000)).fit(X, y)
rest = data[~data["guest_id"].isin(pilot["guest_id"]) & '''+ELIGIBILITY+'''].copy()
rest["p"] = final.predict_proba(rest[num + cat])[:, 1]
'''
    honest=section(honest,'starter',fenced(hs+'\nbest_t = None  # перенесите зафиксированный порог из fp-money'))
    honest=section(honest,'solution',fenced(hs+'\nbest_t = 0.08  # зафиксирован в разобранном варианте fp-money\nbest_t_incr = best_t\n'+hc[hc.index('rest["send"] = rest["p"] > best_t_incr'):]))
    check=fields(honest,'check')
    start=check.index('_oof = _cvp')
    end=check.index('_ns = ',start)
    check=check[:start]+'''_f = _mp(_scaled, _LR(max_iter=1000)).fit(_X, _y)
_bti = need("best_t_incr")
assert _bti == need("best_t") and _bti in _np.arange(0.02,0.41,0.02).round(2), "Перенесите тот же best_t из шага выбора по дополнительной марже."
'''+check[end:]
    check=check.replace('(_d["orders_n"] > 0)', ELIGIBILITY_REF)
    check=replace(check,'_org = _ct.loc[_hi, "bought"].mean()','assert _hi.any(), "В выбранном контроле нет наблюдений: органическую долю оценить нельзя."\n_org = _ct.loc[_hi, "bought"].mean()')
    check=replace(check,'_s = _p > _bti','''_s = _p > _bti
_got = need("rest", _pd.DataFrame)
assert {"guest_id","p","send"}.issubset(_got.columns) and _got["guest_id"].is_unique and set(_got["guest_id"]) == set(_r["guest_id"]), "В rest нужны ID изученной когорты и её решения."
_actual = _got.set_index("guest_id").loc[_r["guest_id"]]
assert _np.allclose(_actual["p"], _p) and _np.array_equal(_actual["send"], _s), "Каждые вероятность и решение должны соответствовать своему guest_id."''')
    honest=section(honest,'check',fenced(check))
    honest=hints(honest, '''Перенесите единственный порог из fp-money. Для контроля получите вероятности от final, затем долю покупок среди гостей выше этого порога. Для кандидатов используйте такой же строгий знак.

### hint
'''+fenced('''best_t_incr = best_t
rest["send"] = rest["p"] > best_t_incr
n_send = int(rest["send"].sum())
hi = final.predict_proba(ctrl[num + cat])[:, 1] > best_t_incr
org = ctrl.loc[hi, "bought"].mean()
eb = rest.loc[rest["send"], "p"].sum()
# Считайте деньги по eb и org, округлите только ответы для вывода.'''))
    honest=section(honest,'explain','При пороге 0,08 среди отобранного контроля купили 14 из 246 (5,7%). В исторической изученной когорте модель выбрала 736 получателей. Долю контроля, стоимость всех контактов и сумму прогнозов применяют к этим же ID. Порог подбирали с помощью этой контрольной группы, поэтому результат предварительный и может быть завышен. Интервал только для органической доли при фиксированных прогнозах не учитывает неопределённость модели, выбор лучшего порога и перенос во времени. Новый рандомизированный пилот с заранее зафиксированным правилом проверит экономику независимо.')
    return money,portrait,groups,honest


def revise(name, src):
    if name=='07-final-project.md':
        result = lesson_chapter(src)
        return result.replace('{{practice: fp-features, fp-leak}}','{{practice: fp-features}}').replace('{{practice: fp-honest, fp-groups}}','{{practice: fp-honest, fp-groups, fp-leak}}')
    if name=='06-project.md':
        src=replace(src,'Чем хуже модель предсказывает (ниже R², выше RMSE), тем шире разброс итоговой прибыли и выше риск.', 'Риск проверяют по фактической прибыли адресов, выбранных по рангу. Сдвиг всех прогнозов на одну константу меняет RMSE, но сохраняет top-40 и результаты каждого обследования.')
        src=replace(src,'Нужен бутстрэп.', 'Смоделируем выбор 300 разных адресов из реестра.')
        return replace(src,'Бутстрэп по всему городу вместо теста.', 'Сценарии обследования по всему городу вместо отложенных адресов.')
    return replace(src,'Риск оценивают бутстрэпом, а не сравнением.', 'В этом проекте частоту убытка оценивают повторными обследованиями по 300 уникальных адресов из отложенного реестра.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('chapter',type=Path,help='content/ch08 directory')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    changes={}
    for name in ('06-project.md','07-final-project.md','test.md'):
        path=args.chapter/name
        old=path.read_text()
        new=revise(name,old)
        for source in re.findall(r'^```python\n(.*?)^```',new,flags=re.M|re.S):
            ast.parse(source)
        changes[path]=new
        if not args.apply:
            print(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name,tofile=name)),end='')
    if args.apply:
        for path,new in changes.items():
            path.write_text(new)
