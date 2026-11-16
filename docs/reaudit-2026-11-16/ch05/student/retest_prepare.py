import json
from pathlib import Path
root=Path(__file__).parent
ids=json.loads((root.parent/'technical/retest-targets.json').read_text())
answers={}
for p in root.glob('*.jsonl'):
 if 'feedback' in p.name or p.name.startswith('retest'): continue
 for line in p.read_text().splitlines():
  r=json.loads(line)
  id=r.get('question') or f'{r["lesson"]}/{r["task"]}'
  answers[id]=r
out=[]
for id in ids:
 r=answers[id].copy()
 r['expect']='Повтор после чтения обновлённого задания. '+r['expect']
 if id=='02-distributions/binom-hand':
  r['expect']='Шесть способов; one округляется отдельно, p_hand считается из полной вероятности .24**2*.76**2. p_hand и p_scipy должны совпасть до четырех знаков.'
 if id=='07-ab/per-buyer':
  r['expect']='ARPU равна конверсии, умноженной на выручку на покупателя. Сравнение покупателей описательное: состав заказавших мог измениться. p_buyer не доказывает равенство и не измеряет изменение среднего чека заказа.'
 if id=='09-project/decision':
  r['expect']='Полные границы используются до округления. На всей выгрузке ожидаю «неопределённо»; функция отдельно проверяется по всем городам после проверки наличия нужных групп.'
  r['code'] += '\ncity_reports={}\nfor city,x in ab.groupby("city"):\n    assert set(x.group)=={"A","B"}\n    assert set(x.loc[x.ordered.eq(1),"group"])=={"A","B"}\n    assert set(x.loc[x.distance_km<2,"group"])=={"A","B"}\n    city_reports[city]=promise_report(x)\n'
 if id=='test/quiz/5': r['expect']='На тех же данных и тем же методом больший уровень доверия требует более широкого интервала; выбран вариант 2.'
 out.append(r)
(root/'retest-answers.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out))
print(len(out),'ответов с expect записаны до отправки')
