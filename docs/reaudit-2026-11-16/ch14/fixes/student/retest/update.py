from pathlib import Path
import json
D=Path(__file__).resolve().parent
out=[]
for f in sorted(D.glob('*-feedback.jsonl')):
    inp=D/f.name.replace('-feedback.jsonl','-input.jsonl')
    inputs=[json.loads(l) for l in inp.read_text().splitlines() if l.strip()] if inp.exists() else []
    for i,line in enumerate(f.read_text().splitlines()):
        if not line.strip():continue
        r=json.loads(line)
        after='Получено подтверждение. Сохраняю полный вывод и перехожу к следующей разрешённой цели.' if r.get('passed') else 'Сохраняю реальную реакцию; следующий шаг определю по сообщению, без стирания этой попытки.'
        if f.name.startswith('diagnostic-wrong'):after='Получен ожидаемый диагностический отказ: это намеренный повтор старого вызова. Читаю конкретное новое сообщение и отдельно выполню предлагаемое действие.'
        out.append(dict(source=f.name,input=inputs[i] if i<len(inputs) else None,Q4=after,actual=r))
(D/'walkthrough.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out))
print('Walkthrough events',len(out))
