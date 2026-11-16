from pathlib import Path
import subprocess
p=Path('/private/tmp/kuch02round/student/work/git-practice');p.mkdir(exist_ok=True)
def git(*args):
 r=subprocess.run(['git',*args],cwd=p,check=True,capture_output=True,text=True)
 print(r.stdout)
 return r.stdout
if not (p/'.git').exists():
 git('init','-b','main')
 git('config','user.name','Course Student')
 git('config','user.email','student@example.invalid')
 (p/'README.md').write_text('# Итоги осени\n')
 (p/'.gitignore').write_text('.venv/\ndata/\n.env\n.ipynb_checkpoints/\n')
 git('add','README.md','.gitignore')
 git('commit','-m','Структура отчёта и правила исключения данных')
 (p/'README.md').write_text('# Итоги осени\n\nВыручка ноября +9.6%, проверена чистым запуском.\n')
 git('diff')
 git('add','README.md')
 git('commit','-m','Добавлены основной результат и способ проверки')
 git('switch','-c','codex/check-loyalty')
 (p/'loyalty.md').write_text('Порог 5% описывает разницу заказов, причинность требует эксперимента.\n')
 git('add','loyalty.md');git('commit','-m','Разделены описание и эффект карты')
 git('switch','main');git('merge','codex/check-loyalty')
log=git('log','--oneline','--no-decorate')
Path('/private/tmp/kuch02round/student/work/my_git_log.txt').write_text(log)
git('status','--short')
