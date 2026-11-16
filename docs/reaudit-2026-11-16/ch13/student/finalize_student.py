from pathlib import Path
import json,hashlib
D=Path(__file__).parent
order=['01-text-prep','01b-lemmas','02-tfidf','03-classify','03b-labels','04-embeddings','04b-transformers','04c-llm','05-project','test']
out=['# Полный Cognitive Walkthrough\n\nАгент-ученик, SQL/Excel-аналитик после 12 глав. Инспекционное прохождение, не наблюдение за человеком. Q1–Q3 сохранены до отправки в input.jsonl; Q4 ниже воспроизводит полную фактическую реакцию из feedback.jsonl. Никаких скрытых решений и чужих отчётов не читал.\n']
pairs=[]
for lesson in order:
 pairs.append((D/(lesson+'.input.jsonl'),D/(lesson+'.feedback.jsonl')))
 if lesson=='03-classify':
  for s in ['hint','parsons-retry','recall95-retry','recall95-retry2']:pairs.append((D/(lesson+'.'+s+'.input.jsonl'),D/(lesson+'.'+s+'.feedback.jsonl')))
 if lesson=='04c-llm':pairs.append((D/(lesson+'.retry.input.jsonl'),D/(lesson+'.retry.feedback.jsonl')))
for inp,fb in pairs:
 inputs=[json.loads(x) for x in inp.read_text().splitlines()];feedback=[json.loads(x) for x in fb.read_text().splitlines()]
 assert len(inputs)==len(feedback),(inp,len(inputs),len(feedback))
 for r,f in zip(inputs,feedback):
  id=f.get('id',r.get('question',r.get('task')))
  out.append(f'\n## {id} — {inp.name}\n\n')
  for q in ['Q1','Q2','Q3']:out.append(f'**{q}.** {r.get(q,r.get("expect",""))}\n\n')
  out.append('**Q4 — полная фактическая реакция.**\n\n```json\n'+json.dumps(f,ensure_ascii=False,indent=2)+'\n```\n\n')
  if f.get('passed') is True:nxt='Принято; перейти к следующему действию. Для weekly PNG действительно открыт; он показывает рост KZN-2 после недели5октября и сохранение повышенного уровня.' if id=='05-project/weekly' else 'Принято; перейти к следующему действию.'
  elif 'hint' in f:nxt='Подсказка прочитана после своей попытки, помощь учтена. Для recall95 сохраняю настройку порога на валидации и оцениваю тест после фиксации.'
  elif 'browserError' in f:nxt='Ошибка транспорта: собрать дословные опубликованные строки Parsons; это ещё не оценённая попытка.'
  else:nxt='Сохранить эту неудачную попытку и исправить по обратной связи; следующие inputs записаны отдельно.'
  out.append('**Следующий шаг.** '+nxt+'\n')
out.append('\n## Проверка собственных предсказаний\n\nВ исходном Q3 bag я написал 3×7, но в трёх данных фразах шесть разных слов: вкусный, горький, дорого, кофе, но, холодный. Код сам строит vocab и корректную3×6матрицу, принят; исходное ошибочное предсказание не переписано. В clean вывод None перед нормализованной строкой появился из моего временного pass в сохранённой стартовой функции; переопределённая функция затем вернула верную строку. Это мои артефакты исполнения, не дефекты урока.\n')
(D/'walkthrough.md').write_text(''.join(out))
# Add concrete conclusions to the already executed independent notebook, without changing code or outputs.
p=D/'project-template.ipynb';n=json.loads(p.read_text());n['cells'].append(dict(cell_type='markdown',metadata={},source=['### Проверенные результаты и чтение цитат\n\n2400 старых/4800 новых отзывов, отсутствующих значений и дублей ID нет; повторов текстов249/773, они не удалены. Тест accuracy тональности0.943 против baseline0.538, тем0.820 против0.293; macro-F1тем0.794. У повторяющихся тестовых текстов F1тем1.000, у новых0.761; групповой контроль592отзыва даёт0.794. Это полезный контроль, но не независимая оценка живого источника.\n\nПо календарным месяцам KZN-2 имеет рост0.371→0.564 (+19.3п.п.), TMN-1 имеет максимальный уровень0.609. Граница KZN-2 —5октября: недельная доля0.347→0.596 при89отзывах в неделю скачка; следующие недели0.620,0.555,0.643. До/после выбранной даты440/372отзыва, модельный сигнал162/222, то есть36.8%/59.7%. Среди сигналов доставка24.1%→58.1%, у остальных точек18.1%→16.3%.\n\nВсе пять цитат упоминают адрес/курьера, пролитый кофе в пакете или неверный заказ. N-54090 также жалуется на капучино, N-53971 на приветствие, N-54719 на волос в салате; одна основная тема не исчерпывает содержание. Трасса N-54090:23октября,KZN-2,p=.9546,neg1,доставка,неделя19октября,письмо с тем же исходнымID.\n\nСтарые TPR=.917/FPR=.034 дают условные доли.378/.637. На синтетических complaint до161/440=.3659,после222/372=.5968; совпадение новой поправки на тех же строках не является проверкой будущего потока. 3октября относится к после при границе1октября и к до при границе5октября. Нужны независимо размеченные новые отзывы обоих периодов; о количестве уникальных гостей и доле посетителей данных нет.']))
p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
for name,result in [('ch13-pymorphy3.ipynb','Все code-ячейки исполнены. Получены19257токенов/491слово/450лемм, совпадение review_lemmas1.0. Слова,леммы,основы дали F1=.940±.015. Измеренные времена только машинные, не время ученика. Дополнительно реально проверены чай матча/после матча: оба дают матч, knownTrue. Текстовые задания Попробуйте сами отдельно не выполнены.'),('ch13-transformers.ipynb','Все code-ячейки исполнены на2400отзывах, исходная модель cointegrated/rubert-tiny2 взята локально offline без обучения и скачивания. E2400×312, masked/naive cosine.925; разница alone/batch5.96e-8;F1emb.930±.016 противTFIDF.940±.015. Все5поисковых запросов исполнены: курьер опоздал находит доставку опоздала; долго везли заказ путает заказ; не дорого находит слишком дорого. Повторное чтение кэша и изменение fingerprint проверены отдельным extra-verification.py. Текстовые задания CLS,unmasked повтор,KMeans4800 не выполнены.')]:
 p=D/name;n=json.loads(p.read_text());n['cells'].append(dict(cell_type='markdown',metadata={},source=['## Собственный фактический итог\n\n'+result]));p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
