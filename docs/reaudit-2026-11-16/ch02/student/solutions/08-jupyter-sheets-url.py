def sheet_csv_url(link):
    sid=link.split("/d/")[1].split("/")[0]
    gid=link.rsplit("gid=",1)[1].split("&")[0].split("#")[0] if "gid=" in link else "0"
    return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
