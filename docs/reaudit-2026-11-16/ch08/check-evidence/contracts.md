# Прочитанные программные контракты главы 8

91 task; 11 уроков. Инвентарь не означает выполнение всех авторских решений. Для каждого урока новая пара есть в первоначальных 40 пробах; followup пока не запускался.

| ID | Явно потребляемые выходы | Сверка | Новые пробы |
|---|---|---|---|
| `01-value/cost-matrix` | `fp`, `profit` | скаляр/функция/вывод | 0 |
| `01-value/break-even` | `gain`, `threshold` | скаляр/функция/вывод | 0 |
| `01-value/toy-guests` | `profit_50`, `profit_33`, `extra` | скаляр/функция/вывод | 0 |
| `01-value/p-profit` | `profit` | скаляр/функция/вывод | 3 |
| `01-value/rule-vs-model` | `p50`, `p30`, `rule30`, `best` | независимый пересчёт | 0 |
| `01-value/margin` | `roi_50`, `roi_35`, `n_extra`, `tp_extra`, `profit_extra` | независимый пересчёт | 0 |
| `01-value/best-threshold` | `curve`, `best_t`, `best_profit` | независимый пересчёт | 0 |
| `01-value/sensitivity` | `sens` | независимый пересчёт | 0 |
| `01-value/calib` | `n_near`, `mean_p`, `fact`, `gap` | независимый пересчёт, ключи/индекс | 0 |
| `01-value/per-guest` | `n_value`, `profit_value`, `share_low` | независимый пересчёт | 0 |
| `01a-pilot/pilot-delta` | `delta`, `online` | скаляр/функция/вывод | 2 |
| `01a-pilot/pilot-extra` | `stayed_bonus`, `stayed_anyway`, `extra` | скаляр/функция/вывод | 0 |
| `01a-pilot/pilot-pnl` | `offline`, `pnl` | скаляр/функция/вывод | 0 |
| `01a-pilot/pnl-range` | `total_est`, `total_low`, `total_high`, `safe` | скаляр/функция/вывод | 0 |
| `01a-pilot/min-effect` | `delta_min`, `z_gap` | скаляр/функция/вывод | 0 |
| `01b-metric-tree/tree-calc` | `rev_aug`, `rev_sep`, `d_guests`, `d_conv`, `d_check` | скаляр/функция/вывод | 0 |
| `01b-metric-tree/p-net-conv` |  | скаляр/функция/вывод | 2 |
| `01b-metric-tree/order-swap` | `d_guests`, `d_check`, `d_conv`, `total` | скаляр/функция/вывод | 0 |
| `01b-metric-tree/tree-shift` | `parts`, `worst_shop`, `worst_drop` | ключи/индекс | 0 |
| `01b-metric-tree/check-pct` | `check_pct`, `worst_check` | ключи/индекс | 0 |
| `01b-metric-tree/tree-no-kzn` | `parts_wo`, `total_wo` | ключи/индекс | 0 |
| `02-budget/top-mask` | `send` | ключи/индекс | 0 |
| `02-budget/p-gains` |  | скаляр/функция/вывод | 0 |
| `02-budget/at-k` | `prec_k`, `rec_k` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/profit-k` | `by_k`, `best_k` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/random-base` | `rnd_60`, `gain_60` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/lift` | `base`, `lift_60`, `lift_150`, `lift_rule_60` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/gains-plot` | `at10` | независимый пересчёт, график (границы охвата в отчёте) | 5 |
| `02-budget/budget-cap` | `n_above`, `k_use`, `profit_all`, `profit_cap`, `saved` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/two-offers` | `calls_profit`, `bonus_profit`, `better` | независимый пересчёт, ключи/индекс | 0 |
| `02-budget/rule-gains` | `cmp`, `gap_grows` | независимый пересчёт, ключи/индекс | 0 |
| `03-risk/resample` | `idx`, `n_unique` | локальный RNG | 0 |
| `03-risk/p-boot` |  | локальный RNG | 0 |
| `03-risk/binom` | `p_low` | локальный RNG | 3 |
| `03-risk/boot-profit` | `profits`, `low`, `high`, `p_loss` | независимый пересчёт, локальный RNG | 2 |
| `03-risk/broken-pairs` | `mean_ok`, `mean_broken`, `p_loss_broken` | независимый пересчёт, локальный RNG | 0 |
| `03-risk/pilot` | `mean_pilot`, `p_loss` | независимый пересчёт, локальный RNG | 0 |
| `03-risk/binom-sd` | `sd_sim`, `sd_formula`, `sd_rub` | локальный RNG | 0 |
| `03-risk/compare-risk` | `risk`, `safest` | независимый пересчёт, локальный RNG | 0 |
| `03-risk/unsure-retain` | `p_loss`, `launch` | независимый пересчёт, локальный RNG | 0 |
| `03-risk/break-retain` | `min_retain` | независимый пересчёт, локальный RNG | 0 |
| `04-monitoring/month-col` | `d`, `per_month` | ключи/индекс | 0 |
| `04-monitoring/p-monitor` | `month_report` | скаляр/функция/вывод | 3 |
| `04-monitoring/miss-share` | `miss`, `max_month` | ключи/индекс | 0 |
| `04-monitoring/monthly-auc` | `quality`, `worst_month` | скаляр/функция/вывод | 0 |
| `04-monitoring/new-category` | `new_cats`, `n_renamed`, `pred_before`, `pred_after` | ключи/индекс | 0 |
| `04-monitoring/median-alarm` | `ratio`, `alarms` | ключи/индекс | 0 |
| `04-monitoring/auc-blind` |  | скаляр/функция/вывод | 0 |
| `04-monitoring/output-alarm` | `train_share`, `above`, `alarm_months` | ключи/индекс | 0 |
| `04-monitoring/fix-retrain` | `auc_old`, `auc_new`, `use_new` | независимый пересчёт | 0 |
| `04-monitoring/psi` | `psi_by_month`, `serious` | ключи/индекс | 0 |
| `04b-segments/seg-table` | `live`, `by_city`, `gap_city`, `gap` | ключи/индекс | 0 |
| `04b-segments/metric-report` | `metric_report`, `live`, `wider` | ключи/индекс, локальный RNG | 0 |
| `04b-segments/seg-toy` | `auc_all`, `auc_seg`, `higher` | ключи/индекс | 0 |
| `04b-segments/rule-base` | `rule_auc`, `gain`, `least` | ключи/индекс | 0 |
| `04b-segments/report-text` | `report`, `report_metrics` | локальный RNG | 4 |
| `05-explain/pd-one` | `X_test`, `risk_30` | независимый пересчёт | 0 |
| `05-explain/contrib-hand` | `z`, `contrib`, `direction` | скаляр/функция/вывод | 0 |
| `05-explain/p-pd` | `partial` | скаляр/функция/вывод | 2 |
| `05-explain/pd-tenure` | `pd_tenure`, `newbie_ratio` | независимый пересчёт | 0 |
| `05-explain/coefs` | `w`, `top_up`, `top_down` | независимый пересчёт, ключи/индекс | 0 |
| `05-explain/guest-card` | `contrib`, `card` | независимый пересчёт, ключи/индекс | 0 |
| `05-explain/top-guest` | `top_idx`, `top_risk`, `top3`, `days_contrib` | независимый пересчёт, ключи/индекс | 0 |
| `05-explain/sum-check` | `z`, `p_manual`, `p_model` | независимый пересчёт, ключи/индекс | 0 |
| `05-explain/what-if-app` | `n_group`, `before`, `after`, `drop_pp` | независимый пересчёт, ключи/индекс | 0 |
| `05-explain/pd-two` | `pd_new`, `pd_old`, `max_gap_day` | независимый пересчёт, ключи/индекс, график (границы охвата в отчёте) | 0 |
| `05b-fairness/fair-recall` | `g`, `p`, `fair25`, `gap25`, `extra_bonuses`, `fixes_gap` | ключи/индекс | 0 |
| `05b-fairness/proxy-check` | `single`, `top_proxy`, `auc_without`, `auc_with` | ключи/индекс | 0 |
| `05b-fairness/fair-toy` |  | ключи/индекс | 2 |
| `05b-fairness/missed` | `missed_n`, `missed_share`, `base_old` | ключи/индекс | 0 |
| `05b-fairness/quiet-churn` | `quiet`, `quietest` | ключи/индекс | 0 |
| `06-project/look` | `overview`, `best_avg_city` | ключи/индекс | 0 |
| `06-project/prep` | `prep`, `X_perm` | скаляр/функция/вывод | 0 |
| `06-project/models` | `quality`, `most_predictable` | независимый пересчёт, ключи/индекс | 0 |
| `06-project/top40` | `top` | ключи/индекс | 0 |
| `06-project/promise` | `promise`, `overpromised` | ключи/индекс | 0 |
| `06-project/boot` | `boot_city`, `risk` | ключи/индекс, локальный RNG | 0 |
| `06-project/decision` |  | ключи/индекс | 5 |
| `06-project/profile` |  | ключи/индекс | 0 |
| `06-project/forest` | `rf_risk`, `same_choice` | независимый пересчёт, ключи/индекс, локальный RNG | 0 |
| `07-final-project/fp-tables` | `counts`, `n_offer`, `n_july` | скаляр/функция/вывод | 0 |
| `07-final-project/fp-curve` | `profit_curve` | ключи/индекс | 0 |
| `07-final-project/fp-features` | `agg` | ключи/индекс | 0 |
| `07-final-project/fp-eda` | `by_morning`, `n_top`, `lift_top` | независимый пересчёт, ключи/индекс | 0 |
| `07-final-project/fp-leak` | `auc_leak`, `auc_clean`, `n_sub_nonbuyers` | независимый пересчёт | 0 |
| `07-final-project/fp-metric` | `conv_offer`, `conv_ctrl`, `uplift_pp`, `breakeven`, `profit_all`, `honest_per_offer` | скаляр/функция/вывод | 0 |
| `07-final-project/fp-models` | `cv_table`, `best_name` | независимый пересчёт | 0 |
| `07-final-project/fp-money` | `best_t`, `test_profit`, `all_profit`, `test_sent`, `test_buyers` | независимый пересчёт | 4 |
| `07-final-project/fp-portrait` | `rest`, `portrait`, `app_share`, `best_t`, `n_rest`, `n_send` | независимый пересчёт, ключи/индекс | 0 |
| `07-final-project/fp-groups` | `best_t`, `weak_city`, `recall_by_age` | независимый пересчёт, ключи/индекс | 0 |
| `07-final-project/fp-honest` | `best_t_incr`, `organic`, `honest_profit`, `honest_all`, `n_send`, `exp_buyers`, `naive_profit` | независимый пересчёт, ключи/индекс | 3 |
