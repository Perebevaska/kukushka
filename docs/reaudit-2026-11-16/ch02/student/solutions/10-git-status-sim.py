from fnmatch import fnmatch

committed = {"README.md": "# Итоги осени", "report.py": "print(1)", "old.ipynb": "{}"}
working = {"README.md": "# Итоги осени", "report.py": "print(2)", "notes.md": "черновик",
           "data/orders_3m.csv": "...", ".env": "PASSWORD=..."}
ignore = ["*.csv", ".env"]

def status(committed,working,ignore):
    return {"new":sorted(p for p in working if p not in committed and not any(fnmatch(p.split("/")[-1],pat) for pat in ignore)),"modified":sorted(p for p in working if p in committed and working[p]!=committed[p]),"deleted":sorted(p for p in committed if p not in working)}
status(committed,working,ignore)
