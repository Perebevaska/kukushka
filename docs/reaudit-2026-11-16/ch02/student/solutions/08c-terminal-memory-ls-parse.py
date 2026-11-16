listing = """total 1076
-rw-r--r--  1 anya  staff  257933 Nov 20 09:15 daily_sales.csv
-rw-r--r--  1 anya  staff     379 Nov 20 09:15 menu.csv
-rw-r--r--  1 anya  staff  144308 Nov 20 09:15 orders_3m.csv
-rw-r--r--  1 anya  staff   11646 Nov 20 09:15 reviews.csv
-rw-r--r--  1 anya  staff  673576 Nov 20 09:15 service_log.jsonl
-rw-r--r--  1 anya  staff     387 Nov 20 09:15 shops.csv"""

rows=[l.split() for l in listing.splitlines() if not l.startswith("total")]
sizes={r[-1]:int(r[4]) for r in rows}
biggest=max(sizes,key=sizes.get)
total_kb=round(sum(sizes.values())/1024)
