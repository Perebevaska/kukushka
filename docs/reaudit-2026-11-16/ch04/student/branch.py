import pandas as pd,math
from pathlib import Path
raw=pd.read_csv('data/deliveries_branch.csv',parse_dates=['created'])
ok=raw[raw.actual_min.between(1,299)].copy();ok['late']=ok.actual_min>ok.promised_min
shares=ok.groupby('courier').late.agg(['sum','size','mean']).sort_values('mean',ascending=False)
print(shares)
c=shares.index[0]
t=ok.groupby(['promised_min','courier']).late.agg(['sum','size','mean']);print(t)
promise=int(ok[ok.courier==c].promised_min.mode().iloc[0]);s=ok[(ok.courier==c)&(ok.promised_min==promise)];p80=s.actual_min.quantile(.8);fair=math.ceil(p80/5)*5
r=ok[(ok.courier!=c)&(ok.promised_min==promise)]
print(c,promise,p80,fair,(s.actual_min<=fair).sum(),len(s))
text=f'''# Самостоятельный перенос на другой состав доставок

Источник: deliveries_branch.csv, отдельная синтетическая выгрузка; всего {len(raw)}, пригодных {len(ok)}. Название целевой группы не переносил из первого проекта.

Выбрал по максимальной наблюдаемой доле опозданий группу **{c}**: {int(shares.loc[c,'sum'])}/{int(shares.loc[c,'size'])} = {shares.loc[c,'mean']:.1%}. Остальные группы:

{shares.to_string()}

При одном обещании **{promise} минут** выбранная группа имеет {s.late.sum()}/{len(s)} опозданий ({s.late.mean():.1%}); остальные типы вместе {r.late.sum()}/{len(r)} ({r.late.mean():.1%}). Значит, общий разрыв не снимается одним сравнением обещания. Срез с числителями и знаменателями:

{t.to_string()}

Для подгруппы {c}, обещание {promise}, п80 факта {p80:.1f} мин; округление вверх до пяти — **{fair} мин**. На исходных маршрутах в этот срок уложились бы {(s.actual_min<=fair).sum()}/{len(s)} ({(s.actual_min<=fair).mean():.1%}). Это сценарий изменения честности обещания, а не ускорение доставки и не прогноз выручки.

Предлагаю пилот {fair}-минутного обещания в сопоставимых маршрутах этой группы, распределив предложение случайно внутри обещания, расстояния и часа. Главная мера — своевременность ≥80%; одновременно измерять конверсию, отказы и маржу. Если в пилоте доля своевременных ниже 80%, либо конверсия и маржа ухудшаются настолько, что бизнес-результат отрицателен, предложение не масштабировать. Нужны интервалы неопределённости, размер и срок пилота из следующей главы.

Ограничение: synthetic данные другого состава, прежние названия не гарантируют прежние процессы. Курьер, час, погода и маршрут могут смешиваться; выбор по максимальной доле оптимистично выделяет крайность. При одинаковом обещании ещё не одинаковые маршруты. Нельзя обвинять тип курьера причинно.
'''
Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch04/student/branch.md').write_text(text)
