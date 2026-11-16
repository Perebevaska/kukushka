"""Generate a second, labelled training extract without renaming courier groups."""
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]


def make_extract(destination):
    with (ROOT / 'site/data/deliveries.csv').open(newline='') as source, destination.open('w', newline='') as out:
        records = csv.DictReader(source)
        writer = csv.DictWriter(out, fieldnames=records.fieldnames)
        writer.writeheader()
        for index, row in enumerate(records):
            # A different training branch has fewer pedestrian trips and a changed travel time.
            if row['courier'] == 'пеший' and index % 3 == 0:
                continue
            value = row['actual_min']
            if value and 1 <= float(value) <= 299:
                shift = {'авто': 25, 'пеший': -8, 'вело': 0}[row['courier']]
                row['actual_min'] = str(max(1, min(299, int(float(value)) + shift)))
            writer.writerow(row)


if __name__ == '__main__':
    make_extract(Path(sys.argv[1]))
