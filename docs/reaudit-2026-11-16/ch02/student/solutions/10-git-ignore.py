from fnmatch import fnmatch

patterns = [".venv/", "data/", ".ipynb_checkpoints/", "*.csv", ".env"]
files = ["README.md", "report.ipynb", "data/orders_3m.csv", ".env", "pyproject.toml",
         ".ipynb_checkpoints/report-checkpoint.ipynb", "export/kpi.csv", "notes/.env.example",
         ".venv/lib/pandas/__init__.py", "src/zerno_utils.py"]

def is_ignored(path,patterns):
    parts=path.split("/")
    return any((pat[:-1] in parts[:-1]) if pat.endswith("/") else fnmatch(parts[-1],pat) for pat in patterns)
tracked=[path for path in files if not is_ignored(path,patterns)]
