#!/usr/bin/env python3
"""Validate candidate vocabulary against the actual page text. A candidate survives only
if every English term in its "(...)" tag occurs literally in the PDP corpus or the
collection-page corpus, and nothing in it is a brand or model name."""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
COLL = ["all", "smart-pixel-speaker", "bluetooth-speakers", "karaoke", "pixel-display",
        "digital-photo-frames-1", "charger", "pixel-backpack", "new-product"]
# brand or model names only: generic phrases such as "regular sling bag" are fine
BAN = re.compile(r"\b(?:divoom|minitoo|pixoo|ditoo|cyberbag|dipow|songbird|times\s?frame|times\s?gate|"
                 r"emodo|emoto|astrotoo|fairy-?ok|itour|k-?starspark|lovelock|spark-?pro|tiivoo|"
                 r"timebox|flowtoo|backpack-?[ms]\b|sling\s?bag-?[vm]\b|ditoo-?mic|pixoo-?64|pixoo-?max)\b", re.I)
CJK = re.compile(r"[\u4e00-\u9fff]")

def norm(t: str) -> str:
    """Lower-case, unify Wi-Fi spellings and quote marks, collapse whitespace."""
    t = t.lower().replace("wi-fi", "wifi").replace("wi‑fi", "wifi")
    for q in ("\u2019", "\u2018", "'", "\u2033", "\u201d", "\u201c", '"'):
        t = t.replace(q, "")
    return re.sub(r"\s+", " ", t)

def collection_text() -> str:
    parts = []
    for h in COLL:
        s = (RAW / "pages" / f"{h}.html").read_text(encoding="utf-8", errors="replace")
        s = re.sub(r"(?is)<(script|style|noscript|svg|template|nav|footer|form|select)\b.*?</\1>", " ", s)
        i = s.find("xo-main-collection"); s = s[i:] if i > 0 else s
        parts.append(html.unescape(re.sub(r"<[^>]+>", " ", s)))
    for c in json.loads((RAW / "collections.json").read_text())["collections"]:
        parts.append(html.unescape(re.sub(r"<[^>]+>", " ", c.get("description") or "")))
    for h in COLL:
        for p in json.loads((RAW / f"products__{h}.json").read_text())["products"]:
            parts.append(p["title"])
    return norm(" ".join(parts))

def pdp_text() -> str:
    return norm(" ".join(f.read_text(encoding="utf-8") for f in sorted((ROOT / "pdp_text").glob("*.txt"))))

def terms(value: str) -> list[str] | None:
    m = re.search(r"\(([^)]+)\)\s*$", value)
    if not m:
        return None
    out = []
    for t in re.split(r"\s*/\s*", m.group(1)):
        t = t.strip().lower()
        t = re.sub(r"^\d+(?:\.\d+)?\s*(?:w|v|g)\s+", "", t)
        t = t.replace('"', "").strip()
        t = re.sub(r"\s+", " ", t)
        if t:
            out.append(t)
    return out or None

def main() -> None:
    cands = json.loads((ROOT / "work" / "candidates.json").read_text(encoding="utf-8"))
    coll, pdp = collection_text(), pdp_text()
    keep, drop = {}, {}
    for group, values in cands.items():
        k, d = [], []
        for v in values:
            if BAN.search(v):
                d.append((v, "brand/model name")); continue
            ts = terms(v)
            if not ts or not re.search(r"[a-z]", " ".join(ts)):
                d.append((v, "no (english) tag")); continue
            if not CJK.search(v):
                d.append((v, "no chinese name")); continue
            def hit(term: str) -> bool:
                for variant in re.split(r"\s*支持\s*", term):
                    if variant.strip() and variant.strip() in pdp or (variant.strip() and variant.strip() in coll):
                        return True
                return False
            where = ("pdp" if all(hit(t) for t in ts) else
                     "collection" if all(hit(t) for t in ts) else None)
            if where:
                k.append(v)
            else:
                miss = [t for t in ts if not hit(t)]
                d.append((v, "not on page: " + "; ".join(miss)))
        keep[group], drop[group] = k, d
    (ROOT / "work" / "verified.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "work" / "rejected.json").write_text(json.dumps(drop, ensure_ascii=False, indent=1), encoding="utf-8")
    tot_k = sum(len(v) for v in keep.values()); tot_d = sum(len(v) for v in drop.values())
    print(f"可保留 {tot_k} / 丢弃 {tot_d}（候选 {tot_k + tot_d}）\n")
    for g in cands:
        print(f"  {g:8} 保留 {len(keep[g]):3}  丢弃 {len(drop[g]):3}")

if __name__ == "__main__":
    main()
