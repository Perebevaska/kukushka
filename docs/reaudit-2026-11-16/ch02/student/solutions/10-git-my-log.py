my_log='63161c4 Разделены описание и эффект карты\n58ddc7d Добавлены основной результат и способ проверки\n1095710 Структура отчёта и правила исключения данных\n'
rows=my_log.strip().splitlines()
n_mine=len(rows)
messages=[row.split(" ",1)[1] for row in rows]
