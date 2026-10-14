#!/usr/bin/env python3
"""抓取 divoom.com 品牌资料：PDP / 集合页 / 场景页 / 英文产品手册。

数据源与分工：
  结构化（curl，快且完整）  products.json、/collections/<h>/products.json、product-manuals.json
  页面正文（firecrawl）     PDP、集合页、场景页、手册 PDF
  原始输出缓存              work/raw_brand/ —— 改清洗规则时不用重新联网

用法：
    python3 fetch_brand.py --phase struct     # 只拉结构化数据
    python3 fetch_brand.py --phase pdp        # 只抓 PDP
    python3 fetch_brand.py --phase collection
    python3 fetch_brand.py --phase scene
    python3 fetch_brand.py --phase manual
    python3 fetch_brand.py --phase all        # 全部（已有缓存的跳过）
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch_fc import clean_article, get as fc_get  # noqa: E402

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"
RAW = WORK / "raw_brand"          # 清洗后的成品
SRC = WORK / "raw_brand_src"      # firecrawl 原始输出（改清洗规则时不用重新联网）
DATA = WORK / "brand-raw.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/124 Safari/537.36")

COLLECTIONS = ["smart-pixel-speaker", "pixel-display", "pixel-backpack", "christmas-gift",
               "bundle-sale", "karaoke", "divoom-sale", "new-product", "charger", "all",
               "digital-photo-frames-1", "featured-products", "bluetooth-speakers",
               "big-summer-sale", "kol-single-products", "kol-bundles"]

# pages sitemap 里的场景页
SCENES = ["sleep-relaxation-essentials", "gaming-streaming-setup", "gifts-for-every-moment",
          "desk-setup-essentials", "shop-divoom-by-scene"]

MANUALS_JSON = "https://cdn.shopify.com/s/files/1/0082/4105/3814/t/130/assets/product-manuals.json"


def curl(url: str) -> str:
    p = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", "--compressed",
                        "-A", UA, url], capture_output=True, text=True)
    return p.stdout


def save(kind: str, name: str, text: str) -> None:
    d = RAW / kind
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(text, encoding="utf-8")


def cached(kind: str, name: str) -> str | None:
    f = RAW / kind / f"{name}.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


# ── PDP 专用清洗 ──────────────────────────────────────────────────────────
# blog 用的 clean_article 不适用 PDP：PDP 的页脚是「评价表单 + 交叉销售」，
# 而且正文里混着大量图片-链接行。
PDP_FOOTER = re.compile(
    r"^(?:"
    r"\s*\+Add photo"
    r"|\s*Your (?:name|email)\s*$"
    r"|\s*Submit review\s*$"
    r"|\s*StripeM-"
    r"|\s*Continue shopping\s*$"
    r"|##\s*(?:Customer Reviews|Reviews|You may also like|Related products|Recently viewed)"
    r"|##\s*(?:divoom\.com|shop\.app) is blocked"
    r"|\s*Thanks!\s*$"
    r")", re.I)

# PDP 里的价格 / 分期 / 促销控件。价格另有结构化字段（products.json），这里只去噪。
PDP_NOISE = re.compile(
    r"^(?:"
    r"\s*As low as \$[\d.]+ ?/ ?month.*"
    r"|\s*Regular price\s*$|\s*Sale price\s*$|\s*Unit price/?\s*$|\s*per\s*$"
    r"|\s*Read more\s*$|\s*Add to (?:cart|Cart)\s*$|\s*Buy it now\s*$"
    r"|\s*Sold out\s*$|\s*In stock\s*$|\s*Save \$?[\d.]+.*"
    r"|\s*-?\d+%\s*(?:off)?\s*$|\s*\$\s?[\d,]+(?:\.\d+)?\s*(?:USD|usd)?\s*$"
    r"|\s*Translation missing.*"
    # 运费 / 支付 / 促销块（常被加粗，故先去掉强调符再匹配）
    r"|\s*Free (?:Standard )?Shipping\s*$|\s*to United States\.\s*$"
    r"|\s*Express Shipping\s*$|\s*available for US\$.*"
    r"|\s*Rates can vary.*|\s*24-Hour Dispatch\s*$|\s*30-Day Money Back\s*$"
    r"|\s*Buy with\s*$|\s*More payment options\s*$"
    r"|\s*Pay in \d+ interest-free.*|\s*Learn more\s*$"
    r"|\s*Save\s*$|\s*on Divoom .*|\s*Buy \d+ get.*|\s*Add to Wishlist\s*$"
    r")", re.I)

BLOCKED = re.compile(r"ERR_BLOCKED_BY_CLIENT|has been blocked by an extension", re.I)


def is_blocked(raw: str) -> bool:
    """Firecrawl 的浏览器偶尔会被扩展拦成 ERR_BLOCKED_BY_CLIENT，那不是内容。"""
    return bool(BLOCKED.search(raw[:4000]))


def clean_pdp(md: str) -> str:
    md = re.sub(r"\r\n", "\n", md)
    lines = md.split("\n")
    # 从第一个 H1 开始
    start = 0
    for i, l in enumerate(lines):
        if re.match(r"^#\s+\S", l):
            start = i
            break
    lines = lines[start:]
    # 砍页脚：出现过一段正文之后再允许截断（PDP 顶部也有图片行）
    started = False
    for i, l in enumerate(lines):
        if len(l.strip()) > 200:
            started = True
        if started and PDP_FOOTER.match(l):
            lines = lines[:i]
            break
    out = []
    for l in lines:
        st = l.strip()
        if not st:
            out.append("")
            continue
        # 纯图片行、纯链接行、评分/数量小控件
        if st.startswith(("![", "[![")):
            continue
        if re.match(r"^\[\]\(|^\[\s*\]", st):
            continue
        if re.match(r"^[\d.]+$|^★|^\d+\s*Reviews?$|^\+\s*$", st):
            continue
        plain = re.sub(r"^[*_\s]+|[*_\s]+$", "", st)
        if PDP_NOISE.match(st) or PDP_NOISE.match(plain):
            continue
        out.append(l)
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


# ── 阶段 1：结构化数据 ────────────────────────────────────────────────────
def phase_struct() -> None:
    prods = json.loads(curl("https://divoom.com/products.json?limit=250"))["products"]
    print(f"products.json: {len(prods)} 个产品", flush=True)
    members = {}
    for c in COLLECTIONS:
        try:
            d = json.loads(curl(f"https://divoom.com/collections/{c}/products.json?limit=250"))
            members[c] = [x["handle"] for x in d.get("products", [])]
        except Exception:
            members[c] = []
        print(f"  /collections/{c:<24} {len(members[c]):>3} 个", flush=True)
    mans = json.loads(curl(MANUALS_JSON))
    DATA.write_text(json.dumps({"products": prods, "collections": COLLECTIONS,
                                "members": members, "scenes": SCENES, "manuals": mans},
                               ensure_ascii=False), encoding="utf-8")
    print(f"手册: {mans['totals']['products']} 产品 / {mans['totals']['manuals']} 份"
          f" → {DATA}", flush=True)


# ── 阶段 2：firecrawl 抓页面 ──────────────────────────────────────────────
def clean_manual(raw: str) -> str:
    """手册 PDF 经 firecrawl 解析后本身就是正文，没有导航/页脚要砍。
    用 blog 的 clean_article 会把「What's included」这类小节整段切掉（它按 `# H1` 定位正文起点，
    而手册常以 `##` 开头），所以手册只做最轻的规整。"""
    md = re.sub(r"\r\n", "\n", raw)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def _clean(kind: str, raw: str) -> str:
    if kind == "pdp":
        return clean_pdp(raw)
    if kind == "manual":
        return clean_manual(raw)
    return clean_article(raw)


def fc_fetch(kind: str, name: str, url: str, min_len: int = 800) -> str:
    """抓取 → 原样缓存 → 清洗 → 成品缓存。raw 与 cleaned 分开存，改规则可 --reclean。"""
    hit = cached(kind, name)
    if hit and len(hit) >= min_len:
        return hit
    src = SRC / kind / f"{name}.md"
    if src.exists():
        raw = src.read_text(encoding="utf-8")
    else:
        raw = ""
        for attempt in range(3):
            got = fc_get(url)
            if got and not is_blocked(got):
                raw = got
                break
            print(f"    {'被拦' if got else '空'}，第 {attempt+1} 次重试 {url}", flush=True)
            time.sleep(6 + 6 * attempt)
        if not raw:
            print(f"    FAIL {url}", flush=True)
            return ""
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text(raw, encoding="utf-8")
    body = _clean(kind, raw)
    if len(body) < min_len:
        print(f"    清洗后过短 {len(body)} {url}", flush=True)
        return ""
    save(kind, name, body)
    return body


def phase_reclean() -> None:
    """不联网：用 work/raw_brand_src/ 里的原始输出重新清洗。"""
    n = 0
    for kind in ("pdp", "collection", "scene", "manual"):
        d = SRC / kind
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            raw = f.read_text(encoding="utf-8", errors="replace")
            body = _clean(kind, raw)
            if len(body) >= 300:
                save(kind, f.name[:-3], body)
                n += 1
    print(f"重新清洗 {n} 份", flush=True)


def phase_pdp() -> None:
    p = json.loads(DATA.read_text(encoding="utf-8"))
    items = [(x["handle"], f"https://divoom.com/products/{x['handle']}") for x in p["products"]]
    # 手册里有但 products.json 已下架的，也补抓
    known = {h for h, _ in items}
    for m in p["manuals"]["products"]:
        h = m.get("productHandle")
        if h and h not in known:
            items.append((h, f"https://divoom.com/products/{h}"))
    print(f"PDP 待抓 {len(items)} 个", flush=True)
    for i, (h, u) in enumerate(items, 1):
        b = fc_fetch("pdp", h, u)
        print(f"[{i}/{len(items)}] {'ok ' if b else 'FAIL'} {len(b):>7,}  {h[:52]}", flush=True)
        time.sleep(0.6)


def phase_collection() -> None:
    print(f"集合页待抓 {len(COLLECTIONS)}", flush=True)
    for i, c in enumerate(COLLECTIONS, 1):
        b = fc_fetch("collection", c, f"https://divoom.com/collections/{c}")
        print(f"[{i}/{len(COLLECTIONS)}] {'ok ' if b else 'FAIL'} {len(b):>7,}  {c}", flush=True)
        time.sleep(0.6)


def phase_scene() -> None:
    print(f"场景页待抓 {len(SCENES)}", flush=True)
    for i, s in enumerate(SCENES, 1):
        b = fc_fetch("scene", s, f"https://divoom.com/pages/{s}")
        print(f"[{i}/{len(SCENES)}] {'ok ' if b else 'FAIL'} {len(b):>7,}  {s}", flush=True)
        time.sleep(0.6)


def pick_manual(product: dict) -> dict | None:
    """优先英文；没有就用多语种（内含英文）或 zh-en。"""
    ms = product.get("manuals") or []
    for code in ("en", "multi", "zh-en"):
        for m in ms:
            if m.get("languageCode") == code and m.get("url"):
                return m
    return None


def phase_manual() -> None:
    p = json.loads(DATA.read_text(encoding="utf-8"))
    items = []
    for prod in p["manuals"]["products"]:
        m = pick_manual(prod)
        if m:
            items.append((prod["key"], prod["name"], m))
    print(f"手册待抓 {len(items)} 份", flush=True)
    for i, (key, name, m) in enumerate(items, 1):
        b = fc_fetch("manual", key, m["url"], min_len=300)
        print(f"[{i}/{len(items)}] {'ok ' if b else 'FAIL'} {len(b):>7,}  "
              f"{name[:24]:<26} {m['languageCode']:<6} {m['filename'][:40]}", flush=True)
        time.sleep(0.6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all",
                    choices=["struct", "pdp", "collection", "scene", "manual",
                             "reclean", "all"])
    a = ap.parse_args()
    if a.phase in ("struct", "all"):
        phase_struct()
    if a.phase in ("pdp", "all"):
        phase_pdp()
    if a.phase in ("collection", "all"):
        phase_collection()
    if a.phase in ("scene", "all"):
        phase_scene()
    if a.phase in ("manual", "all"):
        phase_manual()
    if a.phase == "reclean":
        phase_reclean()
    n = sum(1 for _ in RAW.rglob("*.md")) if RAW.exists() else 0
    print(f"\n原始缓存共 {n} 份 → {RAW}", flush=True)


if __name__ == "__main__":
    main()
