"""From the course root print a checked preview, or pass --apply to edit current files."""
import argparse
import re
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
root = Path.cwd()
patch = Path(__file__).resolve().with_name('expert-lesson.patch')
patches = [str(patch), str(patch.with_name('expert-figures.patch'))]
figures = [Path('content/figures') / f'{name}.svg' for name in ('nn-alpha', 'nn-overfit-epochs')]
chapter = Path('content/ch11')
task = re.compile(r'^## task:\s*([^|]+)\|', re.MULTILINE)
blocks = re.compile(r'^\x60\x60\x60python[^\n]*\n(.*?)^\x60\x60\x60[ \t]*$', re.MULTILINE | re.DOTALL)
subprocess.run(['git','apply','--check',*patches], check=True, cwd=root)

def inspect(folder):
    ids, counts, uncompiled = [],Counter(),[]
    for page in sorted(folder.glob('*.md')):
        source = page.read_text()
        ids += [(page.stem,'task',t.strip()) for t in task.findall(source)]
        quiz_predict = re.findall(r'^::: (quiz|predict)\b', source, re.MULTILINE)
        for kind, count in Counter(quiz_predict).items():
            ids += [(page.stem,kind,i+1) for i in range(count)]
        for number, block in enumerate(blocks.findall(source),1):
            try:
                compile(block, f'{page.stem}:{number}', 'exec')
            except SyntaxError as exc:
                uncompiled.append((page.stem,number,exc.msg))
            counts[page.name] += 1
    return ids, counts, uncompiled

with tempfile.TemporaryDirectory() as temp:
    preview = Path(temp)
    shutil.copytree(root/chapter,preview/chapter)
    for figure in figures:
        (preview/figure).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/figure,preview/figure)
    before = inspect(preview/chapter)
    subprocess.run(['git','apply',*patches], check=True,cwd=preview)
    after = inspect(preview/chapter)
    for figure in figures:
        original_svg = ElementTree.parse(root/figure)
        updated_svg = ElementTree.parse(preview/figure)
        assert [(node.tag,node.attrib) for node in original_svg.iter()] == [(node.tag,node.attrib) for node in updated_svg.iter()]
        assert 'тест' not in ''.join(updated_svg.getroot().itertext()).casefold()
    print('Figure geometry and IDs preserved, legends use validation:', len(figures))
    assert before[0] == after[0], 'Lesson/task/quiz/predict IDs differ'
    assert before[1:] == after[1:], 'Number or syntax of Python blocks changed'
    print('Preserved IDs:', dict(Counter(kind for _,kind,_ in after[0])))
    print('Python blocks compiled:',sum(after[1].values())-len(after[2]),'of', sum(after[1].values()))
    if after[2]:
        print('Unchanged original syntax exceptions:',after[2])
    if args.apply:
        subprocess.run(['git','apply',*patches],check=True,cwd=root)
        print('Applied chapter 11 lesson patch.')
