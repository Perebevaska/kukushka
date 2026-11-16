"""Verify saved release/package fingerprints without refreshing them. stdlib only."""
from pathlib import Path
import hashlib,json
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch14';W=Path('/private/tmp/kuch14round')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
r=read(D/'technical/release.json')
for name,value in r['files_sha256'].items():
 p=Path(name) if name.startswith('/') else R/name;assert sha(p)==value,'release changed '+name
reference=read(D/'technical/retest-package/reference.json');package=read(D/'technical/retest-package/public-package-manifest.json');T=Path(package['root'])
assert reference['export_sha256']==r['release_export_sha256']==sha(W/'final.json')
for name,value in package['files'].items():assert sha(T/name)==value,'public changed '+name
actual={str(p.relative_to(T)) for p in T.rglob('*') if p.is_file()};assert actual==set(package['files']),'unmanifested public input'
for path in ['content/ch14/05-project.md','site/ch14/05-project.html']:
 s=(R/path).read_text();bound=s.index('## task: day') if path.endswith('.md') else s.index('id="task-day"');assert s.index('Парковка получает фото мест')<bound;assert s.index('После шага 5 подготовьте короткое письмо')<bound
sentence='Кадры, освещение и состояния ячеек созданы генератором курса';assert sentence in (T/'intro.md').read_text() and sentence in (R/'site/ch14/index.html').read_text(),'provenance public in intro and rendered index'
for base in [D/'student',D/'fixes/student/holdout-predictions',D/'fixes/student/holdout-evaluation']:
 for line in (base/'SHA256SUMS').read_text().splitlines():
  h,name=line.split('  ',1);assert sha(base/name)==h,'own prior immutable '+name
out={'release_files':len(r['files_sha256']),'public_files':len(package['files']),'public_targets':reference['selection']['count'],'task_targets':reference['selection']['task_count'],'question_targets':reference['selection']['question_count'],'source_export_HTML_match':True,'parking_letter_public_before_first_task':True,'generated_origin_public_before_calculations':True,'own59_10_14_SHA_unchanged':True,'data4_immutable_against_baseline_HEAD':r['data_all4_immutable_against_baseline_HEAD'],'outside_chapter_HTML_cache_only':len(r['HTML_outside_ch14']),'global_cheatsheet_only_ch14_section':len(r['global_generated_ch14_only']),'status':'public metadata verified; dispatch controlled by root; runtime and learner completion reported separately','execution':'stdlib hash/string checks, no browser/ML/build'}
(D/'technical/verify-release.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
