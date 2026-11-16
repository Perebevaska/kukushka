"""Verify the chapter 2 download and the IDs collected via the published trainer."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href', ''))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    frozen = json.loads((AUDIT / 'technical/baseline.json').read_text())
    template = SITE / 'notebooks/ch02-project-template.ipynb'
    notebook = json.loads(template.read_text())
    source = '\n'.join(''.join(cell['source']) for cell in notebook['cells'])
    assert 'sklearn' not in source and 'daily_sales' not in source
    assert all(x in source for x in ('autumn.ipynb', 'loyalty.ipynb', 'Restart Kernel'))
    links = {}
    for page in ('ch02/index.html', 'ch02/09-project.html', 'ch02/11-sql-project.html'):
        file = SITE / page
        parser = Links()
        parser.feed(file.read_text())
        matches = [href for href in parser.hrefs if href.endswith('project-template.ipynb')]
        assert matches and all((file.parent / href).resolve() == template for href in matches), (page, matches)
        links[page] = matches
    for path in (ROOT / 'content/ch02/test.md', SITE / 'ch02/test.html'):
        assert 'Воспроизводимая ведомость длин' not in path.read_text()
    original = [json.loads(line) for line in (AUDIT / 'student/initial-attempts.jsonl').read_text().splitlines()]
    expected = set(frozen['expected_ids'])
    assert {row['id'] for row in original if row.get('passed')} == expected
    retest = [json.loads(line) for line in (AUDIT / 'student/retest-attempts.jsonl').read_text().splitlines()]
    retest_ids = {row['id'] for row in retest if row.get('passed')}
    expected_retest = {
        '03-columns/map', '04-groupby/shares', '04-groupby/two-keys', '04b-pivot/wide',
        '05-merge/city', '05-merge/all-shops', '05-merge/per-seat', '05-merge/margin',
        '06-dates/mom-net', '06-dates/hours', '06-dates/floor', '07a-sql-python/sqlite-read',
        '07b-sql-windows/w-lag', '07c-sql-frames/w-running', '04a-guest-metrics/conversion',
        '05b-join-index/join', '05b-join-index/anti', '08-jupyter/ipynb-json',
        '09-project/shops', '09-project/margin', '09-project/verdicts', '11-sql-project/p-ghosts',
        '11-sql-project/p-second', '11-sql-project/p-promo', '11-sql-project/p-cohort-source', '08b-jupyter-keys/p-keys',
        '01-dataframe/p-sum', '07b-sql-windows/w-share', '06b-timezones/quiz/1',
        *(f'test/quiz/{n}' for n in (5, 6, 9, 10, 15, 16, 18, 19, 22))
    }
    assert expected_retest <= retest_ids <= expected
    declines = [row for row in retest if row.get('passed') is False]
    assert any(row['id'] == '11-sql-project/p-promo' for row in declines)
    snapshots = [SITE / 'notebooks/ch02-practice.ipynb', SITE / 'notebooks/tasks/ch02.json', template]
    snapshots += sorted((SITE / 'ch02').glob('*.html')) + sorted((ROOT / 'content/ch02').glob('*.md'))
    snapshots += [ROOT / 'content/figures/cohort-edge.svg', ROOT / 'tools/checks/ch02_csv_replay.py']
    output = dict(initial_distinct_ids=len(expected), initial_attempts=len(original), retest_unique=len(retest_ids),
                  retest_submissions=len(retest), retest_declines=[r['id'] for r in declines], retest_ids=sorted(retest_ids), template_links=links,
                  export_sha256=digest(Path(sys.argv[1])), files={str(p.relative_to(ROOT)): digest(p) for p in snapshots})
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    verify()
