from pathlib import Path
import json,subprocess,os
OUT=Path(__file__).parent
knowledge={
'01-vectors':('Векторная строка обязана совпадать порядком с весами. Евклидова норма — корень суммы квадратов; L1 — сумма модулей. Косинус сравнивает направление, масштаб влияет на соседей.','2/5: новые обозначения понятны через взвешенную сумму; восстановил G из указанного CSV. Это моя работа по сборке окружения, не доказанный дефект: тренажёр предоставляет G.'),
'02-matrices':('Внутренние размеры совпадают, внешние дают форму результата. Клетка — строка на столбец; X.T@X собирает суммы, центрированная версия даёт ковариацию. Единицы превращают intercept в общий вес.','2/5: восстановил sales по примеру и X по доставкам. SQL JOIN+SUM помогает читать произведение.'),
'02b-vectorize':('np.where заменяет условия по строкам; ветви вычисляются целиком. Сначала сверяю ответы, затем измеряю реальные повторные вызовы perf_counter. Нулевой таймер означает None, отношение не определено. Короткий цикл допустим вокруг векторизованного длинного.','3/5: надо внимательно держать границы >2,>5,>8 и дождевой множитель после надбавки. Тайминги — агента в браузерной среде, не человеческое время прохождения.'),
'03-normal-equation':('Нормальное уравнение собирает все строки в систему по числу весов. Ранг проверяю до solve; флаги+единицы зависимы. Остатки МНК ортогональны столбцам. При зависимости lstsq даёт один минимум нормы, коэффициенты неоднозначны.','3/5: формула компактна, труднее удержать порядок столбцов и смысл суммарного эффекта почти-копии.'),
'03b-own-model':('fit сохраняет self.intercept_/coef_ и возвращает self; predict читает состояние конкретного объекта. RegressorMixin первым,BaseEstimator последним дают score/get_params и копирование. Правила бизнеса проверяются теми же фолдами.','3/5: состояние объекта и родители требуют внимания, но карточка предыдущих знаний и раздел класса дают основу.'),
'04-transform':('XP — новые столбцы-смеси. Обратимый P сохраняет достижимые МНК-прогнозы на обучении; явный перенос P^-1w сохраняет любой прогноз. Независимые fit на новых строках требуют единственности расширенной системы. Ridge штраф и геометрия kNN/деревьев чувствительны. Известные пары вскрывают P.','3/5: отличие сохранённой информации от приватности и отличие переноса весов от повторного fit принципиальны.'),
'05-project':('Один split и один ключ для train/test/новой анкеты. Сравнение R² до округления. Полный ранг и cond контролируют обратимость и численную точность; member_id исключён. Четыре независимые пары раскрывают4×4ключ, цель тоже персональная.','3/5: последовательные шаги ясны; самостоятельный протокол передачи дополнительно проверю ноутбуком.')}
for lesson in knowledge:
    p=OUT/lesson
    for name in ['attempt','choices']:
        src=p/(name+'-01.jsonl')
        dst=p/('feedback-01.jsonl' if name=='attempt' else 'choices-feedback-01.jsonl')
        if not dst.exists():
            with dst.open('w') as out:
                cp=subprocess.run(['python3','/private/tmp/kuch09round/student/submit.py',str(src)],stdout=out,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
            if cp.returncode: raise SystemExit(f'{lesson} process exit {cp.returncode}')
        feedback=[json.loads(line) for line in dst.read_text().splitlines() if line.strip()]
        before=[json.loads(line) for line in src.read_text().splitlines() if line.strip()]
        if len(feedback)!=len(before): raise SystemExit(f'{lesson}: incomplete feedback')
        (p/(name+'-Q4.md')).write_text('\n\n'.join(f"## {r['id']}\nРеальный вердикт: {r['feedback']}\nСледующий шаг {'понятен: задача принята; перейду к следующей.' if r['passed'] else 'требует разбора фактического отказа перед новой попыткой.'}\nПомощь: 0; подсказки и решения не открыты." for r in feedback))
        if any(not r['passed'] and not (lesson=='03b-own-model' and r['id']=='03b-own-model/group-mean' and json.loads((p/'feedback-02.jsonl').read_text())['passed']) and not (lesson=='02b-vectorize' and r['id']=='02b-vectorize/vectorize' and json.loads((p/'feedback-03.jsonl').read_text())['passed']) for r in feedback):
            print('FAIL',lesson,name,flush=True)
            raise SystemExit(2)
    k,d=knowledge[lesson]
    (p/'knowledge.md').write_text(k+'\n')
    (p/'difficulty.md').write_text(d+'\n')
    (p/'progress.md').write_text('Все практики и вопросы урока приняты фактическими сдачами; raw и Q4 рядом.\n')
    print('COMPLETE',lesson,flush=True)
