"""Small native runner for explicit content counterexamples; no site/notebook generation."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'site/assets')]
import build
import harness


class Chapter:
    def __init__(self, chapter):
        self.chapter = chapter
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.previous = Path.cwd()
        lessons = {}
        build.CH_DISPLAY[chapter] = True
        for source in (ROOT / 'content' / chapter).glob('*.md'):
            if source.stem not in ('intro', 'test'):
                lessons[chapter, source.stem] = build.parse_lesson(source)
        path = self.folder / 'tasks.json'
        build.export(lessons, path)
        self.tasks = {(t['lesson'].split('/')[-1], t['id']): t for t in json.loads(path.read_text()) if t.get('kind') == 'task'}

    def __enter__(self):
        os.chdir(self.folder)
        return self

    def __exit__(self, *exc):
        os.chdir(self.previous)
        self.temp.cleanup()

    def probe(self, lesson, task, suffix='', *, code=None, expected=False, prepare=None):
        item = self.tasks[lesson, task]
        for filename in item.get('files', []):
            shutil.copy(ROOT / 'site/data' / filename, filename)
        if prepare:
            prepare()
        result = harness.run(code if code is not None else item['solution'] + '\n' + suffix, item['check'], item.get('setup'), False)
        assert result.get('ok'), ('Counterexample itself failed to run', lesson, task, result)
        passed = bool(result.get('check', {}).get('passed'))
        assert passed == expected, (lesson, task, result)
        print(f'OK {lesson}/{task}: {"accepted" if passed else "rejected"}; {result.get("check",{}).get("msg", "")}')
        return result
