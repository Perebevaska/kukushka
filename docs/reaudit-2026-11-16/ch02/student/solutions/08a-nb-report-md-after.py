outline=[("markdown","# Итоги осени"),("code","import pandas as pd"),("markdown","## Данные"),("code","df = pd.read_csv('data/orders_3m.csv')"),("markdown","Вывод: 2089 заказов, пропусков в сумме нет."),("markdown","## Выручка по месяцам"),("code","monthly = ..."),("markdown","## Кофейни"),("code","by_shop = ..."),("markdown","Вывод: лидер — PRM-1."),("markdown","## Часы пик"),("code","load = ...")]
def missing_conclusions(cells):
    missing=[]
    section=None
    last=None
    for typ,text in cells:
        if typ=="markdown" and text.startswith("## "):
            if section is not None and (last is None or last[0]!="markdown" or last[1].startswith("#")):
                missing.append(section)
            section=text[3:]
            last=(typ,text)
        elif section is not None:
            last=(typ,text)
    if section is not None and (last is None or last[0]!="markdown" or last[1].startswith("#")):
        missing.append(section)
    return missing
bad=missing_conclusions(outline)
