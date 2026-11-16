import pandas as pd
plan=pd.DataFrame({"shop_id":["KZN-1","KZN-2","PRM-1","PRM-2","TMN-1","UFA-1"],"2026-09":[60000,30000,60000,25000,30000,20000],"2026-10":[62000,32000,62000,26000,31000,24000],"2026-11":[65000,34000,65000,27000,33000,26000]})
plan_long=plan.melt(id_vars="shop_id",var_name="month",value_name="plan")
plan_by_month=plan_long.groupby("month")["plan"].sum().to_dict()
