import json, re, os
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from seo_schema import website_schema, article_schema

CONFIG = json.load(open("config/seo.config.json","r",encoding="utf-8"))
BASE   = CONFIG["site"]["canonicalBase"].rstrip("/")
SITE   = CONFIG["site"]["sitemap"]
SUFFIX = CONFIG["site"]["brandSuffix"]
OG_DEF = CONFIG["site"]["defaultOgImage"]
TITLE_MAX = CONFIG["rules"]["titleMax"]
DESC_MIN  = CONFIG["rules"]["descMin"]
DESC_MAX  = CONFIG["rules"]["descMax"]
NOINDEX   = set(CONFIG["rules"]["noindexPaths"])
BLOG_PREF = CONFIG["sections"].get("blogPrefix","/blog/")

OUT_PATH = os.path.join("out","wix_actions.json")
os.makedirs("out", exist_ok=True)

def fetch(url, timeout=20):
    try:
        r = requests.get(url, headers={"User-Agent":"ReneEnergy-SEO-Bot/1.0"}, timeout=timeout)
        if r.status_code == 200: return r.text
    except Exception: pass
    return None

def get_sitemap_urls():
    html = fetch(SITE)
    if not html: return [BASE + "/"]
    locs = re.findall(r"<loc>(.*?)</loc>", html, flags=re.I)
    host = urlparse(BASE).netloc
    urls = [u for u in locs if urlparse(u).netloc == host]
    return urls or [BASE + "/"]

def to_path(url):
    p = urlparse(url).path or "/"
    if p != "/" and p.endswith("/"): p = p[:-1]
    return p or "/"

def clamp(s, n): return s if len(s) <= n else s[:n-1] + ""

def gen_title(h1, existing_title):
    base = (h1 or existing_title or "ReneEnergy").strip()
    cand = base if base.endswith(SUFFIX) else base + SUFFIX
    return clamp(cand, TITLE_MAX)

def gen_desc(text, existing_desc):
    src = (existing_desc or "").strip()
    if len(src) >= DESC_MIN: return clamp(src, DESC_MAX)
    body = re.sub(r"\s+"," ",(text or "")).strip()
    if not body:
        return "Learn about green hydrogen development, financing, and clean tech insights at ReneEnergy."
    snippet = body[:DESC_MAX]
    cut = max(snippet.rfind(". "), snippet.rfind("! "), snippet.rfind("? "))
    if cut > 50: snippet = snippet[:cut+1]
    return clamp(snippet, DESC_MAX)

def detect_type(path):
    if path == "/": return "home"
    if path.startswith(BLOG_PREF): return "article"
    return "page"

def propose_row(url, soup):
    path = to_path(url)
    h1 = soup.select_one("h1")
    h1 = h1.get_text(strip=True) if h1 else None

    meta_desc = None
    m = soup.find("meta", attrs={"name":"description"})
    if m and m.get("content"): meta_desc = m["content"].strip()

    title = gen_title(h1, None)
    desc  = gen_desc(soup.get_text(" ", strip=True), meta_desc)

    robots = "noindex, nofollow" if path in NOINDEX else "index, follow"
    og_tag = soup.find("meta", property="og:image")
    og_image = og_tag["content"].strip() if og_tag and og_tag.get("content") else OG_DEF

    typ = detect_type(path)
    jsonld = article_schema(BASE, path, title, desc) if typ=="article" else (website_schema(BASE) if typ=="home" else None)

    row = {
        "url": path,
        "title": title,
        "description": desc,
        "indexable": (robots == "index, follow"),
        "canonical": path or "/",
        "ogImage": og_image
    }
    if jsonld: row["jsonLd"] = jsonld
    return row

def load_existing():
    try:
        data = open(OUT_PATH,"r",encoding="utf-8").read().lstrip("\ufeff")
        js = json.loads(data)
        return js if isinstance(js,list) else []
    except Exception: return []

def merge_rows(existing, new_rows):
    by_path = { (e.get("url") or e.get("path")): e for e in existing if e.get("url") or e.get("path") }
    for r in new_rows:
        p = r.get("url") or r.get("path")
        if not p: continue
        if p in by_path:
            cur = by_path[p]
            for k,v in r.items():
                if v not in (None,"",[]): cur[k] = v
        else:
            by_path[p] = r
    def sort_key(k):
        if k == "/": return "0"
        if "*" in k: return "2"+k
        return "1"+k
    return [by_path[k] for k in sorted(by_path.keys(), key=sort_key)]

def main():
    urls = get_sitemap_urls()
    new_rows = []
    for u in urls:
        html = fetch(u)
        if not html: continue
        soup = BeautifulSoup(html, "lxml")
        new_rows.append(propose_row(u, soup))
    merged = merge_rows(load_existing(), new_rows)
    with open(OUT_PATH,"w",encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PATH} with {len(merged)} rows")

if __name__ == "__main__":
    main()
