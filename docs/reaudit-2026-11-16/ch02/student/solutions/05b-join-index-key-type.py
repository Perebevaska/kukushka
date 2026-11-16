import pandas as pd
visits=pd.DataFrame({"guest":["0101","0102","0103","0104","0105"],"visits":[5,2,7,1,3]})
bonus=pd.DataFrame({"guest":[101,102,104,106],"bonus":[150,0,300,50]})
bonus["guest"]=bonus["guest"].astype(str).str.zfill(4)
full=visits.merge(bonus,on="guest",how="left",validate="one_to_one")
matched=full["bonus"].notna().sum()
