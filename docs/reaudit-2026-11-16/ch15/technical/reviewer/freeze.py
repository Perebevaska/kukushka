"""Serialize programs and semantic verdicts before entering either runtime."""
import json
from pathlib import Path

directory = Path(__file__).resolve().parent
chapter = directory.parent.parent
tasks = json.loads((chapter / "technical/baseline-export.json").read_text())
lookup = {t["id"]: t for t in tasks if t["kind"] == "task"}
cases = []

def case(task, name, code, should_pass, reason, check=None):
    source = lookup[task]
    cases.append(dict(name=name, task=task, setup=source["setup"], code=code,
                      check=source["check"] if check is None else check,
                      files=source.get("files", []), should_pass=should_pass, reason=reason))

def student_handler(stage):
    rows = (chapter / f"student/02-{stage}-input.jsonl").read_text().splitlines()
    return next(row["code"] for row in map(json.loads, rows) if row.get("task") == "handler")

case("handler", "literal_invalid", student_handler("first"), False, "SyntaxError в print; сначала назвать ошибку ученика")
case("handler", "literal_fixed", student_handler("retry"), True, "должно быть принято и при первом запуске урока")
gold = lookup["golden"]["solution"]
case("golden", "control_roundtrip", gold.replace('golden = X_test.head(20).copy()', 'golden = X_test.iloc[:20, :].copy()'), True, "те же записи; независимая загрузка")
bad = gold.replace('golden.to_csv("golden.csv", index=False)', '''golden.loc[:, X_test.columns] = golden[X_test.columns].iloc[::-1].to_numpy()
golden.to_csv("golden.csv", index=False)''').replace('loaded.predict_proba(gold.drop(columns=["expected"]))','loaded.predict_proba(X_test.iloc[:20])')
case("golden", "control_unpaired", bad, False, "контрольный CSV связывает признаки с чужими вероятностями, а самопроверка использует память")
runs = lookup["log-csv"]["solution"]
case("log-csv","journal_header_schema",runs,True,"три обычных словаря действительны")
csv_contract = """
import pandas as pd
f = need('append_run')
row1 = {'run_id':'x', 'classifier':'forest', 'metric':0.125}
row2 = {'metric':0.625, 'classifier':'lr', 'run_id':'y'}
f(row1, 'other.csv')
f(row2, 'other.csv')
got = pd.read_csv('other.csv').to_dict('records')
assert got == [row1, row2], str(got)
"""
case("log-csv","journal_reverse_source",runs,True,"публичная функция должна сохранять смысл параметров независимо от порядка полей",csv_contract)
dict_writer = runs.replace('pd.DataFrame([run]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)', '''import csv
    exists = os.path.exists(path)
    fields = list(run)
    if exists:
        with open(path, newline="", encoding="utf8") as old:
            fields = next(csv.reader(old))
    with open(path, "a", newline="", encoding="utf8") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(run)''')
case("log-csv","journal_reverse_correct",dict_writer,True,"новый путь с другим порядком ключей",csv_contract)
guard = lookup["guard"]["solution"]
case("guard","guard_all",guard,True,"0, минус один и сочетания ошибок по фиксированному числовому контракту")
case("guard","guard_zero",guard.replace('if row["visits_90d"] < 0:', 'if row["visits_90d"] <= 0:'),False,"ноль визитов разрешён")
case("guard","guard_single",guard.replace('return problems','return problems[:1]'),False,"два ошибочных значения требуют оба названия")
base = lookup["package"]["solution"]
case("package","target_observed",'''y = build_target("2026-06-30")
assert len(y) == 965 and y.index.is_unique and y.sum() == 131''',True,"закрытый квартал","assert True")
case("package","target_unobserved",'''y = build_target("2026-09-30")
assert len(y) == 1027 and y.index.is_unique and y.isna().all(), (int(y.notna().sum()), int(y.sum()))
assert "churn" not in snapshot("2026-09-30")''',True,"неизвестные цели не кодируются нулями","assert True")
case("package","trend_refund_boundary",'''cid = active_at("2026-09-30").client_id.iloc[0]
orders = orders.iloc[:1].copy()
orders.loc[:, "client_id"] = cid
orders.loc[:, "order_date"] = pd.Timestamp("2026-09-29")
orders.loc[:, "status"] = "возврат"
orders.loc[:, "amount"] = -1.
value = build_features("2026-09-30").loc[cid, "revenue_trend"]
assert np.isfinite(value) and value == 0, float(value)''',True,"правило нуля соответствует модели в соседней карточке","assert True")
cap = base.replace('.head(150)', '.head(3)').replace('"n_calls": int', '"call_limit": 3, "n_calls": int')
case("package","capacity_three",cap,True,"лимит паспорта три с полной точностью")
case("package","wrong_city",cap + '\nout.loc[out.index[0],"city"]="Другой"\nout.to_csv("call_list.csv",index=False)',False,"вероятность правильна, город другого офиса")
case("package","wrong_control_id",cap + '\ngolden.loc[golden.index[0],"client_id"]=golden.client_id.iloc[1]\ngolden.to_csv("golden.csv",index=False)',False,"сломана идентичность контроля")
case("package","wrong_passport_sum",cap + '\npassport["expected_profit"]+=1\nopen("passport.json","w").write(json.dumps(passport))',False,"сумма не согласуется с неокруглённым отбором")
(directory / "frozen.json").write_text(json.dumps(cases,ensure_ascii=False,indent=2)+"\n")

# Дополнение после выявления пересечения одной пробы с AC15-05, до исполнения.
release = lookup["release"]["solution"]
wrong_path = release.replace('pd.read_csv(golden_path)', 'pd.read_csv("golden.csv")')
assert wrong_path != release
split = len(cases)
case("release","release_ignores_path",wrong_path,False,"аргумент golden_path явно задан; в релизе должен читаться указанный файл")
path_contract = """
from pathlib import Path
import pandas as pd
control = pd.read_csv('golden.csv')
control.to_csv('different-name.csv', index=False)
actual = need('release_check')(need('good'), need('card'), 'different-name.csv', need('X_test'), need('y_test'))
assert actual['golden'], str(actual)
control.loc[0,'expected'] += 0.05
control.to_csv('different-name.csv', index=False)
actual = need('release_check')(need('good'), need('card'), 'different-name.csv', need('X_test'), need('y_test'))
assert not actual['golden'], 'Переданный контроль изменён, но модель допущена: '+str(actual)
"""
case("release","release_named_file",release,True,"новое имя того же файла и повреждение одной вероятности",path_contract)
case("release","release_wrong_named_file",wrong_path,False,"функция должна увидеть изменение переданного файла",path_contract)
(directory/"supplement.json").write_text(json.dumps(cases[split:],ensure_ascii=False,indent=2)+"\n")
