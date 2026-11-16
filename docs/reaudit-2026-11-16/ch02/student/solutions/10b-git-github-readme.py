autumn = {
    "title": "Итоги осени сети «Зерно»",
    "question": "За счёт чего выросла выручка ноября?",
    "data": "2089 заказов 6 кофеен за сентябрь–ноябрь; файлы — в папке data/, в репозиторий не входят.",
    "findings": ["Выручка ноября +9.6 % к октябрю.", "Заказов +5.4 %, средний чек +4.0 %."],
    "run": ["uv sync", "uv run jupyter lab"],
}

def make_readme(info):
    lines=["# "+info["title"],"","## Вопрос",info["question"],"","## Данные",info["data"],"","## Главное"]
    lines += ["- "+s for s in info["findings"]]
    lines += ["","## Как запустить"]+["    "+s for s in info["run"]]
    return "\n".join(lines)
readme=make_readme(autumn)
