repos = {
    "zerno-analytics": ["README.md", ".gitignore", "pyproject.toml", "uv.lock", "report.ipynb"],
    "zerno-cleaning": ["README.md", "cleaning.ipynb", "data/clients_raw.csv", ".env"],
    "zerno-sql": [".gitignore", "README.md", "queries/top_shops.sql", "config/.env"],
}

def review(repos):
    result={}
    for name,files in repos.items():
        p=[]
        if "README.md" not in files:p.append("no_readme")
        if ".gitignore" not in files:p.append("no_gitignore")
        if not any(f.endswith(".ipynb") for f in files):p.append("no_notebook")
        if any(f.split("/")[-1]==".env" for f in files):p.append("secrets")
        if any(f.startswith("data/") for f in files):p.append("data")
        if p:result[name]=p
    return result
problems=review(repos)
