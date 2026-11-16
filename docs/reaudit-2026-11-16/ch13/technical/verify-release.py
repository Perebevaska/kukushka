"""Read-only verification of the frozen chapter release and generated scope."""
import json
import re
import subprocess
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
release = json.loads((D / 'technical/release.json').read_text())
changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
issues, normalized, asset_changes = [], [], {}

for name, expected in release['files'].items():
    if sha256((ROOT / name).read_bytes()).hexdigest() != expected:
        issues.append('release hash mismatch: ' + name)
for name, expected in release['data'].items():
    if sha256((ROOT / 'site/data' / name).read_bytes()).hexdigest() != expected:
        issues.append('data hash mismatch: ' + name)
    if (ROOT / 'site/data' / name).read_bytes() != (D / 'technical/data-baseline' / name).read_bytes():
        issues.append('data differs from baseline: ' + name)

def old(name):
    return subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT).decode()

def no_version(text):
    text = re.sub(r'\?v=[0-9a-f]{10}', '?v=VERSION', text)
    return re.sub(r'data-v="[0-9a-f]{10}"', 'data-v="VERSION"', text)

def no_ch13_cheatsheet(text):
    pattern = r'(<h2 class="cs-ch">Глава 13\..*?)(?=<h2 class="cs-ch">Глава 14\.)'
    text, count = re.subn(pattern, 'CHAPTER_13', text, flags=re.S)
    assert count == 1
    return text

for name in changed:
    chapter_figure = name.startswith('content/figures/') and name in release['files']
    if name.startswith('content/') and not name.startswith('content/ch13/') and not chapter_figure:
        issues.append('source outside chapter 13: ' + name)
    if name.startswith('site/') and name.endswith('.html') and not name.startswith('site/ch13/'):
        a, b = no_version(old(name)), no_version((ROOT / name).read_text())
        if name == 'site/cheatsheet.html':
            a, b = no_ch13_cheatsheet(a), no_ch13_cheatsheet(b)
        if a != b:
            issues.append('HTML content outside chapter 13: ' + name)
        else:
            normalized.append(name)

def assignments(text):
    result = {}
    for line in text.splitlines():
        key, value = line.split(' = ', 1)
        result[key] = json.loads(value.removesuffix(';'))
    return result

for name in ['site/assets/course.js', 'site/assets/search.js']:
    before, after = assignments(old(name)), assignments((ROOT / name).read_text())
    counts = {}
    for key, a in before.items():
        b = after[key]
        if key == 'window.DSC_COURSE':
            a, b = [r for r in a if r['id'] != 'ch13'], [r for r in b if r['id'] != 'ch13']
        elif key == 'window.DSC_SEARCH':
            # Every search record has a URL; only chapter 13 records may change.
            a, b = [r for r in a if not r['u'].startswith('ch13/')], [r for r in b if not r['u'].startswith('ch13/')]
        if a != b:
            issues.append('global asset changed outside chapter 13: ' + key)
        counts[key] = len(a)
    asset_changes[name] = counts

result = {'release_files_verified': len(release['files']), 'data_files_verified': len(release['data']),
          'other_html_only_cache_token': [n for n in normalized if n != 'site/cheatsheet.html'],
          'cheatsheet_changes_confined_to_ch13': 'site/cheatsheet.html' in normalized, 'asset_scope': asset_changes,
          'source_changes': [n for n in changed if n.startswith('content/')], 'issues': issues}
(D / 'technical/release-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v if not isinstance(v, list) else len(v) for k, v in result.items()}, ensure_ascii=False))
if issues:
    print('\n'.join(issues))
    raise SystemExit(1)
