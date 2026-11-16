import inspect
import pandas as pd
asc_default=inspect.signature(pd.DataFrame.sort_values).parameters["ascending"].default
norm_default=inspect.signature(pd.Series.value_counts).parameters["normalize"].default
dropna_default=inspect.signature(pd.Series.value_counts).parameters["dropna"].default
