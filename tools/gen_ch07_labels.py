"""Explicit synthetic contract maturity dates for catering leads (30-day target)."""
import csv
from datetime import datetime, timedelta
from pathlib import Path


def write_label_dates(directory):
    directory=Path(directory)
    with (directory/'catering_leads.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    with (directory/'catering_labels.csv').open('w') as stream:
        writer=csv.writer(stream)
        writer.writerow(['lead_id','created','target_end_exclusive','label_available_at','evaluation_date'])
        for row in rows:
            end=(datetime.fromisoformat(row['created'])+timedelta(days=30)).isoformat(sep=' ')
            writer.writerow([row['lead_id'],row['created'],end,end,'2026-10-26'])


if __name__=='__main__':
    write_label_dates(Path(__file__).resolve().parents[1]/'site/data')
