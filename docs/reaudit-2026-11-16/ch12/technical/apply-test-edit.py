"""Reproduce only the agreed quiz edit from repository root; idempotent."""
from pathlib import Path
import hashlib,json,re
spec=json.loads(Path(__file__).with_name('test-edit-spec.json').read_text())
p=Path(spec['source']); s=p.read_text(); digest=lambda t:hashlib.sha256(t.encode()).hexdigest()
if digest(s)==spec['after_sha256']:
    print('ALREADY APPLIED')
else:
    assert digest(s)==spec['before_sha256'], 'Unexpected source revision; inspect before applying'
    for old,new in spec['changes'].items():
        assert s.count(old)==1; s=s.replace(old,new)
    for i in spec['revisions']:
        s,n=re.subn(rf'c{i}: [^,}}]+',f'c{i}: reaudit-20261117-v5',s); assert n==1
    assert digest(s)==spec['after_sha256']; p.write_text(s); print('APPLIED')
