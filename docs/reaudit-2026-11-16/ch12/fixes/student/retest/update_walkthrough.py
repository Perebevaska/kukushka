from pathlib import Path
import json
D=Path(__file__).parent
for feedback_path in D.glob('*.feedback.jsonl'):
    input_path=feedback_path.with_name(feedback_path.name.replace('.feedback.','.input.'))
    if not input_path.exists():continue
    inputs=[json.loads(x) for x in input_path.read_text().splitlines() if x.strip()]
    feedbacks=[json.loads(x) for x in feedback_path.read_text().splitlines() if x.strip()]
    result=[]
    for inp,feedback in zip(inputs,feedbacks):
        result.append({'input':inp,'Q4_raw':feedback,'Q4_meaning':'Проверка приняла собственное решение; следующий шаг — следующая целевая карточка.' if feedback.get('passed') else 'Фактический отказ/служебная реакция сохранены; следующий шаг — разобраться по видимому сообщению отдельной попыткой.','source_input':input_path.name,'source_feedback':feedback_path.name})
    target=feedback_path.with_name(feedback_path.name.replace('.feedback.','.walkthrough.'))
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
