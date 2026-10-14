#!/usr/bin/env python3
"""Fetch Divoom collection data from divoom.com read-only endpoints -> raw/*.json
   The static collection HTML only server-renders a few cards; these endpoints
   carry the full, same-source collection/product data (titles, card links, copy)."""
import json, pathlib, subprocess, time

BASE = "https://divoom.com"
RAW = pathlib.Path(__file__).with_name("raw")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

def get(path):
    # python's stdlib SSL trust store is unusable here; curl works -> shell out
    for attempt in range(3):
        p = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", "-A", UA, BASE + path],
                           capture_output=True, text=True)
        if p.returncode == 0 and p.stdout.strip():
            try:
                return json.loads(p.stdout)
            except json.JSONDecodeError as e:
                print(f"  ! {path} attempt {attempt+1}: bad json: {e}")
        else:
            print(f"  ! {path} attempt {attempt+1}: curl {p.returncode} {p.stderr.strip()[:120]}")
        time.sleep(2 + 3 * attempt)
    return None

def save(name, obj):
    (RAW / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

def main():
    RAW.mkdir(exist_ok=True)
    colls = get("/collections.json?limit=250")
    if not colls:
        raise SystemExit("fatal: could not read collections.json")
    save("collections.json", colls)
    handles = [c["handle"] for c in colls["collections"]]
    print(f"collections: {len(handles)}")
    index = {}
    for h in handles:
        data = get(f"/collections/{h}/products.json?limit=250")
        if data is None:
            print(f"  {h}: FAILED")
            continue
        prods = data.get("products", [])
        save(f"products__{h}.json", data)
        index[h] = [{"handle": p["handle"], "id": p["id"], "title": p["title"],
                     "product_type": p.get("product_type", ""), "tags": p.get("tags", []),
                     "variants": [v.get("title") for v in p.get("variants", [])]}
                    for p in prods]
        print(f"  {h}: {len(prods)} products")
        time.sleep(0.4)
    save("_index.json", index)

if __name__ == "__main__":
    main()
