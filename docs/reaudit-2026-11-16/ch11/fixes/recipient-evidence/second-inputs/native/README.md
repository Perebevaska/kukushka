# Передача сети времени доставки

Это фактически выбранная по validation сеть моего native-extra.ipynb, состояние после лучшей эпохи. `metadata.json` хранит архитектуру, порядок one-hot столбцов, y_mean/y_std и версии. `scaler.joblib` обучен только на train. `delivery_state.pt` — веса.

Запуск без обучения: `python predict.py` сверяет 16 контрольных строк; `python predict.py encoded_features.csv` выдаёт минуты. Нужны numpy,pandas,scikit-learn,torch,joblib из указанной в metadata среды. УстройствоCPU,1 поток.

Вход — уже подготовленные 16 числовых/one-hot столбцов с именами вmetadata. Для исходных доставок: created→час, distance_km/items/hour/courier/weather/shop_id→get_dummies, затем reindex(columns=metadata columns,fill_value=0). Передавайте типы courier/weather/shop_id как при обучении и сообщайте неизвестные категории; не подгоняйте scaler заново. Обучение отфильтровало actual_min1..299; actual_min для прогноза не нужен.

Контрольные прогнозы сохранены до загрузки нового объекта, в исходных минутах. Рецепт и состояние не выбираются по финальномуtest. Файлы ytest в передачу не входят.
