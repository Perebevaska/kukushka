# Один адресный native-повтор

validation-retest.ipynb содержит собственные выполненные outputs. Протокол до fit — protocol-before-fit.json. Только два заранее заданных learning_rate LightGBM0.02/0.1 сравниваются на апреле–июне с погодным сценарием апрельского выпуска. Выбор0.1/595деревьев записан в selection-before-final.json до единственного финального fit на истории доиюля. Финальный test не меняет правило.

Все операции последовательно одним потоком. Версии в первой output-ячейке:Python3.12.14,pandas3.0.6,sklearn1.8.0,LightGBM4.7.0. Для выполнения нужны numpy,pandas,lightgbm,scikit-learn,nbformat,nbclient,ipykernel и ядро этого окружения. Данные по относительному пути ../project/data/daily_sales.csv. validation.csv и final.json содержат реальные качества/интервалы. Остальные13обучений первого прохода не повторялись.
