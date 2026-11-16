from pathlib import Path
import json, shutil
import nbformat as nbf
root=Path(__file__).parent
shutil.copy('/private/tmp/kuch05round/student/data/ab_promise.csv',root/'ab_promise.csv')
answers=[json.loads(x) for x in (root/'09-project.jsonl').read_text().splitlines()]
code={r['task']:r['code'] for r in answers if 'task' in r}
nb=nbf.v4.new_notebook()
cells=[]
def md(s): cells.append(nbf.v4.new_markdown_cell(s))
def py(s): cells.append(nbf.v4.new_code_cell(s))
md('# Новое обещание доставки: анализ эксперимента\n\nСамостоятельный проект студента, глава 5. Источник — выданный ab_promise.csv, сессии 1–21 декабря. Текст плана расположен до расчётов; выводы относятся к назначенным сессиям.')
md((root/'project-plan.md').read_text())
md('## 1. Проверка данных и дизайна\nОжидаю уникальные сессии, две группы, полный экспериментальный период и построчное совпадение обещаний. SRM — необходимая проверка, которая сама по себе не доказывает независимость наблюдений.')
py(code['design']+'\nfrom IPython.display import display, Markdown\nprint("Форма:",ab.shape,"Дубликаты session_id:",ab.session_id.duplicated().sum())\nprint("Период:",ab.ts.min(),ab.ts.max())\ndisplay(ab.isna().sum().rename("missing").to_frame())\ndisplay(sizes.rename("sessions").to_frame())\nprint("SRM p:",srm_p,"promise_ok:",promise_ok,"far_same:",far_same)\nassert ab.session_id.is_unique\nassert set(ab.group)=={"A","B"}\nassert promise_ok and far_same\nprint("Флаги заказов:",sorted(ab.ordered.unique()))\nprint("Сумма без заказа:",ab.loc[ab.ordered.eq(0),"amount"].sum())')
md('## 2. Главная метрика\nЗнаменатель — число заказов; это доля нарушенных обещаний, а не скорость одной и той же доставки. Отбор в заказ может измениться при новом обещании. Привожу интервал разницы B−A отдельно от интервалов отдельных долей.')
py(code['late']+'\ng=orders.groupby("group").late.agg(["sum","size","mean"])\ndisplay(g)\nprint("Разница B-A, п.п.:",diff_pp,"95% ДИ:",ci,"p:",p_late)')
md('## 3. Конверсия\nВсе сессии сохраняются в знаменателе. Зоны заданы заранее и используют строгую границу <2 км.')
py(code['conversion']+'\nconversion_rows=[]\nfor label,x in [("все",ab),("<2 км",ab[ab.distance_km<2]),(">=2 км",ab[ab.distance_km>=2])]:\n    a,b,d,lo,hi,p=share_result(x,"ordered")\n    conversion_rows.append({"zone":label,"A":a,"B":b,"diff_pp":d*100,"lo_pp":lo*100,"hi_pp":hi*100,"p":p})\nconv_table=pd.DataFrame(conversion_rows).set_index("zone")\ndisplay(conv_table)')
md('## 4. Оценки гостей\nМанна–Уитни проверяет распределения по рангам; средние ниже описательные. Пропуски оценок не заменяю пятёрками. Данные описывают мнение оценивших заказчиков.')
py(code['ratings']+'\ndisplay(pd.DataFrame({"rating_mean":[rating_a,rating_b],"share_not_5":[low_a,low_b]},index=["A","B"]))\nprint("Манна–Уитни p:",p_rating)\ndisplay(orders.groupby("group").rating.apply(lambda x:x.notna().mean()).rename("rated_share").to_frame())')
md('## 5. Выручка на назначенную сессию\nСохраняю нули у незаказавших. Проверяемый параметр — средняя выручка: Уэлч и заранее выбранная нормальная аппроксимация интервала. Важна граница допустимой потери −10 ₽. Решение предшествует округлению.')
py(code['money']+'\nrev_diff_full=b.mean()-a.mean()\nrev_lo_full,rev_hi_full=rev_lo,rev_hi\ndisplay(ab.groupby("group").amount.agg(["size","mean","std"]))\nprint("B-A:",rev_diff_full,"95% ДИ:",(rev_lo_full,rev_hi_full),"Уэлч p:",p_rev)\nprint("Нижняя > -10:",rev_lo_full>-10,"Верхняя < -10:",rev_hi_full<-10)')
md('## 6. Устойчивость по городам\nСчитаю все городские проверки и поправку Холма; p и p_holm не округляю. Отсутствие значимости в одном городе не доказывает отсутствия эффекта.')
py(code['cities']+'\ndisplay(by_city)\nprint("Значимое снижение во всех городах после Холма:",all_cities)')
md('## 7. График для руководителя\nУсы относятся к отдельным долям. Интервалы разниц приведены в таблице конверсии и в разделе главной метрики.')
py(code['chart']+'\nfig.savefig("promise-chart.png",dpi=160,bbox_inches="tight")\nplt.show()')
md('## 8. Решение по правилу и ограничения\nФункция также применима к отдельному городу; сравнение с −10 выполняется на полной точности.')
py(code['decision']+'\ndisplay(pd.Series(report).rename("итог").to_frame())\ndisplay(pd.DataFrame({city:promise_report(x) for city,x in ab.groupby("city")}).T)\ndisplay(Markdown(f"**Три предложения руководителю.** Решение по заранее записанному правилу — **{report[\"decision\"]}**: до исключения недопустимой потери новый формат массово не запускаем. Доля опозданий среди заказов изменилась на {report[\"late_diff_pp\"]:.1f} п.п. (95% ДИ {ci[0]:.1f}…{ci[1]:.1f}), а выручка на сессию — на {rev_diff_full:.1f} ₽ (95% ДИ {rev_lo_full:.1f}…{rev_hi_full:.1f} ₽), поэтому сравниваем именно этот интервал с −10 ₽. Постоянного ID гостя нет: нельзя проверить повторные назначения и зависимость его сессий, удержание или долгосрочный эффект; новый этап требует заранее заданных объёма и даты анализа."))')
md('### Перенос на образовательную платформу\nЕсли программу назначают целым классам, независимой единицей назначения является класс. Ученики одного класса разделяют преподавателя, программу и среду, поэтому считать их независимыми строками в обычном тесте нельзя: это занизит SE. Для первого анализа сравню средний результат по классам; при цели «средний эффект на ученика» заранее уточню веса и применю метод, учитывающий кластеризацию по классу. Размер эксперимента определяется прежде всего числом классов, не только числом учеников.')
nb.cells=cells
nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}}
nbf.write(nb,root/'promise.ipynb')
