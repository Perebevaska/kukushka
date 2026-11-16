cmds = []
cmds.append("git init")
cmds.append("git status")
cmds.append("git add README.md .gitignore report.ipynb")
cmds.append('git commit -m "Первая версия отчёта"')
cmds.append("git remote add origin https://github.com/anya/zerno-analytics.git")
cmds.append("git push -u origin main")
print(len(cmds))
