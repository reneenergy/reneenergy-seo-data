import os, json, csv

OUT_DIR = "out"
ACTIONS_FILE = os.path.join(OUT_DIR, "wix_actions.csv")
SCHEMA_FILE = os.path.join(OUT_DIR, "wix_schema.jsonl")
OUTPUT_FILE = os.path.join(OUT_DIR, "wix_actions.json")

def read_actions(path):
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            out.append({
                "url": row.get("url",""),
                "title": row.get("new_title",""),
                "description": row.get("new_meta_description",""),
                "h1": row.get("new_h1",""),
            })
    return out

def read_schema_map(path):
    m = {}
    if not os.path.exists(path): return m
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                it = json.loads(line)
                m[it["url"]] = it.get("jsonld","{}")
            except Exception:
                pass
    return m

def main():
    if not os.path.exists(ACTIONS_FILE):
        raise SystemExit(f"Missing {ACTIONS_FILE}. Run your crawl/rewrites first.")
    os.makedirs(OUT_DIR, exist_ok=True)

    actions = read_actions(ACTIONS_FILE)
    schema_map = read_schema_map(SCHEMA_FILE)

    merged = []
    for r in actions:
        url = r["url"]
        merged.append({
            "url": url,
            "title": r["title"],
            "description": r["description"],
            "h1": r["h1"],
            "jsonLd": schema_map.get(url, "{}"),
            "indexable": True
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Wix JSON saved to {OUTPUT_FILE} with {len(merged)} entries.")

if __name__ == "__main__":
    main()

