from bs4 import BeautifulSoup
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE.parents[4]
html=BeautifulSoup((root/"site/ch06/test.html").read_text(),"html.parser")
rows=[]
for q in html.select(".quiz-c"):
    texts=[]
    correct=[]
    for li in q.select("li"):
        explanation=li.select_one("blockquote")
        assert explanation and explanation.get_text(strip=True)
        explanation.extract()
        text=li.get_text().strip()
        correct.append(text.startswith("[x]"))
        texts.append(text[3:].strip())
    assert len(texts)==4 and sum(correct)==1
    lengths=list(map(len,texts))
    max_length=max(lengths)
    key=lengths[correct.index(True)]
    rows.append({"id":q["data-q"],"longest":key==max_length,"unique_longest":key==max_length and lengths.count(max_length)==1})
assert [r["id"] for r in rows]==[f"c{i}" for i in range(1,16)]
pairs=[]
for overlap in (364,274):
    only_a,only_b=364-overlap,371-overlap
    pairs.append({"total":461,"correct_a":364,"correct_b":371,"both_correct":overlap,"discordant":only_a+only_b,"accuracy_gain":(only_b-only_a)/461})
out={"questions":len(rows),"options_with_explanations":len(rows)*4,"rows":rows,"correct_longest":sum(r["longest"] for r in rows),"correct_unique_longest":sum(r["unique_longest"] for r in rows),"c2_counterexample":pairs}
(HERE/"quiz.json").write_text(json.dumps(out,indent=2)+"\n")
print(len(rows),out["correct_longest"],out["correct_unique_longest"])
