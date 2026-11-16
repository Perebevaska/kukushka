# Все контракты программных заданий главы 7

Инвентарь: 93 программных задания, 13 уроков с кодом. `intro` не содержит сдаваемого кода, итоговый тест проверяется отдельным критиком. Это сверка состава видимого результата, setup, проверки и эталона; значок «да» означает отдельный новый контрпример в этом пакете, а не выполнение учеником. Штатные эталоны и заготовки имеют свой знаменатель в общей технической ведомости координатора. Обязательные имена выходов заданы в условии; новые проверки не требуют написания конкретного выражения или имени промежуточной переменной.

| ID | Выходы, явно потребляемые проверкой | Что сравнивается | Новый ручной код |
|---|---|---|---|
| `03b-money-threshold/warm-profit` | `profit`, `loss` | независимый fit/пересчёт | да |
| `03b-money-threshold/profit` | `profits`, `best_t`, `best_profit` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | да |
| `03b-money-threshold/budget` | `t100`, `n_bonus`, `prec`, `rec` | независимый fit/пересчёт, фактический прогноз | нет |
| `03b-money-threshold/honest-t` | `t_val`, `profit_test`, `profit_05` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `01-confusion/count-four` | `acc` | скалярный результат/категория | да |
| `01-confusion/p-dummy` |  | скалярный результат/категория | нет |
| `01-confusion/dummy-acc` | `churn_test`, `acc_dummy`, `found` | скалярный результат/категория | нет |
| `01-confusion/forest-cm` | `cm` | независимый fit/пересчёт, форма, фактический прогноз | нет |
| `01-confusion/rule-cm` | `rule_cm`, `rule_missed`, `rule_extra` | форма | нет |
| `01-confusion/shares` | `missed_share`, `extra_share`, `error_rate` | независимый fit/пересчёт, фактический прогноз | нет |
| `01-confusion/two-trees` | `more_found` | независимый fit/пересчёт, фактический прогноз | нет |
| `01-confusion/cost` | `costs`, `cheapest` | независимый fit/пересчёт, фактический прогноз | нет |
| `01-confusion/missed-who` |  | независимый fit/пересчёт, фактический прогноз | нет |
| `04-imbalance/w-hand` | `w0`, `w1` | скалярный результат/категория | да |
| `04-imbalance/share-pred` | `share_true`, `share_pred` | независимый fit/пересчёт, фактический прогноз | нет |
| `04-imbalance/p-down` |  | скалярный результат/категория | нет |
| `04-imbalance/lr-bal` | `rec`, `prec`, `f1`, `auc`, `auc_plain` | независимый fit/пересчёт, фактический прогноз | нет |
| `04-imbalance/upsample` | `train_up`, `rec_up`, `prec_up` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `04-imbalance/forest-bal` |  | независимый fit/пересчёт, фактический прогноз | нет |
| `04-imbalance/leak` | `f1_leak`, `share_copies`, `f1_honest` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `04-imbalance/thr-match` | `rec_bal`, `prec_bal`, `t_match`, `prec_match` | независимый fit/пересчёт, фактический прогноз | нет |
| `04-imbalance/cv-up` | `f1_wrong`, `f1_right` | независимый fit/пересчёт, фактический прогноз | нет |
| `05b-regularization/c-two` | `sum_small`, `sum_big`, `bigger` | независимый fit/пересчёт | да |
| `05b-regularization/c-sweep` | `res`, `best_c` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `05b-regularization/lasso` | `kept`, `auc_l1`, `auc_l2` | независимый fit/пересчёт, фактический прогноз | нет |
| `02-precision-recall/by-hand` | `prec`, `rec`, `f1` | скалярный результат/категория | да |
| `02-precision-recall/p-f1` | `f1` | скалярный результат/категория | нет |
| `02-precision-recall/perfect-prec` | `prec`, `rec`, `f1` | скалярный результат/категория | нет |
| `02-precision-recall/forest-prf` | `prec`, `bonuses` | независимый fit/пересчёт, фактический прогноз | нет |
| `02-precision-recall/three-models` | `scores`, `best_f1`, `best_cost` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `02-precision-recall/all-bonus` | `rec_all`, `prec_all`, `mean_all`, `f1_all` | скалярный результат/категория | нет |
| `02-precision-recall/report` | `rec1`, `rec0`, `support1`, `macro_f1` | независимый fit/пересчёт, фактический прогноз | нет |
| `02-precision-recall/recall-plan` | `trees`, `best_depth` | независимый fit/пересчёт, ключи/индекс, фактический прогноз | да |
| `02-precision-recall/newcomers` |  | независимый fit/пересчёт, ключи/индекс, фактический прогноз | нет |
| `02-precision-recall/f-beta` | `d_f2`, `d_f05` | независимый fit/пересчёт, фактический прогноз | да |
| `09-project/look` | `d`, `conv_rate`, `n_contracts`, `budget_na`, `size_na`, `contract_match` | скалярный результат/категория | да |
| `09-project/groups` | `by_channel`, `repeat_rate`, `new_rate`, `fast_rate`, `slow_rate` | ключи/индекс | да |
| `09-project/missing` | `size_na_rate`, `size_ok_rate`, `budget_na_rate`, `budget_ok_rate`, `budget_high`, `budget_low` | скалярный результат/категория | да |
| `09-project/time` | `d`, `evening_share`, `evening_rate`, `day_rate`, `evening_wait`, `day_wait` | скалярный результат/категория | да |
| `09-project/pipe` | `X`, `X_test`, `y_train`, `pipe`, `n_features`, `cv_auc` | независимый fit/пересчёт, форма, ключи/индекс, значения массива, повтор функции, фактический прогноз | да |
| `09-project/trap` | `dummy_acc`, `forest_acc`, `forest_f1`, `balanced_f1` | скалярный результат/категория | да |
| `09-project/metric` | `catch_rate`, `rule_share`, `rule_catch`, `random_catch` | ключи/индекс, повтор функции | да |
| `09-project/grid` | `grid`, `best_params`, `best_auc`, `res`, `spread` | независимый fit/пересчёт | да |
| `09-project/final` | `test_auc`, `model_catch`, `rule_share_test`, `rule_catch_test`, `model_same`, `best`, `model_ids`, `rule_ids` | независимый fit/пересчёт, ключи/индекс, значения массива, фактический прогноз | да |
| `09-project/speed` | `catch_now`, `oleg_wait`, `others_wait`, `oleg_fast`, `others_fast` | независимый fit/пересчёт, фактический прогноз | да |
| `06-features/is-new` | `g`, `n_new`, `rate_new`, `rate_old` | скалярный результат/категория | да |
| `06-features/cxd` | `g`, `n_hi`, `rate_hi`, `rate_zero` | скалярный результат/категория | нет |
| `06-features/gain` | `auc_base`, `auc_vpm`, `auc_new` | скалярный результат/категория | нет |
| `06-features/both` | `test_auc`, `test_f1` | независимый fit/пересчёт, фактический прогноз | нет |
| `06-features/pairs` | `gains`, `best` | ключи/индекс | нет |
| `06b-feature-check/p-recency` | `rates` | ключи/индекс | нет |
| `06b-feature-check/bins` | `n_cols`, `auc_bins` | независимый fit/пересчёт, форма | да |
| `06b-feature-check/combo` | `auc_all`, `f1_all`, `f1_gain` | скалярный результат/категория | нет |
| `06b-feature-check/rf-gain` | `lr_gain`, `rf_gain`, `rf_std` | скалярный результат/категория | нет |
| `06b-feature-check/perm` | `pi_s`, `top3`, `check_pi`, `check_place` | независимый fit/пересчёт, ключи/индекс | нет |
| `06b-feature-check/noise-rank` | `noise_fi`, `noise_pi`, `below_noise` | независимый fit/пересчёт, ключи/индекс | нет |
| `07-pipeline/median-imp` | `med`, `test_filled` | независимый fit/пересчёт, значения массива | да |
| `07-pipeline/ohe-new` | `names`, `codes`, `unknown_rows` | форма | нет |
| `07-pipeline/p-pipe` |  | независимый fit/пересчёт | нет |
| `07-pipeline/prep-shape` | `n_cols`, `names`, `Xt_test`, `test_mean` | независимый fit/пересчёт, форма, ключи/индекс, значения массива | нет |
| `07-pipeline/pipe-metrics` | `test_f1`, `test_auc`, `top_feature` | независимый fit/пересчёт, фактический прогноз | нет |
| `07-pipeline/new-guests` | `new`, `risk`, `flag`, `riskiest` | фактический прогноз | нет |
| `07-pipeline/cv-models` | `cv_auc`, `best_model` | скалярный результат/категория | нет |
| `05-scaling/scale-fit` | `Xs_train`, `Xs_test`, `days_mean`, `test_mean` | независимый fit/пересчёт, форма, значения массива | нет |
| `05-scaling/p-knn` |  | независимый fit/пересчёт, фактический прогноз | нет |
| `05-scaling/zscore` | `mu`, `sd`, `z_test` | независимый fit/пересчёт, значения массива | да |
| `05-scaling/knn-scale` | `f1_raw`, `auc_raw`, `f1_sc`, `auc_sc` | независимый fit/пересчёт, фактический прогноз | нет |
| `05-scaling/iters` | `it_raw`, `it_sc`, `diff_auc` | независимый fit/пересчёт, фактический прогноз | нет |
| `05-scaling/coef-rank` | `imp`, `top3`, `raw_place` | независимый fit/пересчёт, ключи/индекс | нет |
| `05-scaling/who-cares` | `same_tree`, `same_knn` | независимый fit/пересчёт, фактический прогноз | нет |
| `05-scaling/knn-hand` | `hand`, `model_p` | независимый fit/пересчёт, фактический прогноз | нет |
| `03-threshold/thr-30` | `n_bonus`, `prec`, `rec` | независимый fit/пересчёт, фактический прогноз | нет |
| `03-threshold/p-auc` |  | независимый fit/пересчёт, фактический прогноз | нет |
| `03-threshold/rates` | `tpr`, `fpr` | независимый fit/пересчёт, фактический прогноз | нет |
| `03-threshold/recall80` | `curve`, `best_t`, `best_prec` | независимый fit/пересчёт, ключи/индекс, значения массива, фактический прогноз | да |
| `03-threshold/roc-plot` | `auc` | независимый fit/пересчёт, форма, значения массива, фактический прогноз, геометрия/видимость | да |
| `03-threshold/three-auc` | `auc_dummy`, `auc_lr`, `auc_rf`, `best` | независимый fit/пересчёт, фактический прогноз | да |
| `03-threshold/pairs` | `n_pairs`, `auc_sk`, `auc_pairs` | независимый fit/пересчёт, фактический прогноз | нет |
| `07b-own-steps/class-warm` | `CoffeeMachine`, `left`, `cups` | скалярный результат/категория | да |
| `07b-own-steps/ord-tier` | `enc`, `codes`, `rate_by_code`, `new_code` | независимый fit/пересчёт | нет |
| `07b-own-steps/p-transformer` | `clip`, `X_train`, `X_test` | независимый fit/пересчёт | нет |
| `07b-own-steps/feat-step` | `add_features`, `f1_base`, `f1_feat`, `pipe` | повтор функции | нет |
| `07b-own-steps/group-ratio` | `t`, `out` | независимый fit/пересчёт, ключи/индекс | нет |
| `07b-own-steps/own-feature` | `add_more`, `auc_more` | повтор функции | нет |
| `08-tuning/grid-keys` | `param_grid`, `n_fits` | независимый fit/пересчёт | нет |
| `08-tuning/p-grid` |  | независимый fit/пересчёт | нет |
| `08-tuning/save-load` | `model2`, `same`, `n_flag` | фактический прогноз, содержимое файла | да |
| `08-tuning/grid-lr` | `search`, `best_params`, `best_f1`, `gain` | независимый fit/пересчёт | нет |
| `08-tuning/cv-table` | `table`, `n_close`, `cw_close` | значения массива | да |
| `08-tuning/final-test` | `final`, `test_f1`, `test_auc`, `cv_gap` | фактический прогноз | нет |
| `08-tuning/prep-params` | `imp_key`, `search`, `best_params`, `delta` | независимый fit/пересчёт | нет |
| `08-tuning/random-forest` | `rs`, `best_params`, `best_f1`, `beats_lr` | независимый fit/пересчёт | нет |
| `08-tuning/top30` | `top30_recall`, `search`, `best_params`, `best_top30` | независимый fit/пересчёт, повтор функции, фактический прогноз | нет |
