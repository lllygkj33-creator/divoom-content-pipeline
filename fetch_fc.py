#!/usr/bin/env python3
"""正文抓取统一走 firecrawl（不用本地 IP 直连）。

为什么：momcozy.com 对本地 IP 有机器人校验，curl 会被 429（"Verifying your connection"）
拦住，而且 fcrawl 会把整页导航一起带回来。firecrawl 走浏览器路径稳定，所以：

  抓取 = firecrawl（fcrawl）
  清洗 = 本脚本的 clean_article()：按「文章 H1（其后有长段落）」定位正文起点，
         砍掉页脚区（推荐位 / 相关阅读 / 购物车 / 版权 / 支付图标 / 分享 / 标签）

用法：
    python3 fetch_fc.py                 # 全量重抓 work/bodies 下已有的 URL
    python3 fetch_fc.py --only-dirty    # 只重抓「含表格占位 / 一级标题重复」的
    python3 fetch_fc.py --reclean       # 不联网：用 work/raw_fc/ 里缓存的原始输出重新清洗
"""
from __future__ import annotations
import argparse, pathlib, re, subprocess, sys, time

FCRAWL = pathlib.Path.home() / ".local" / "bin" / "fcrawl"
ROOT = pathlib.Path(__file__).parent
DST = ROOT / "work" / "bodies"
RAW = ROOT / "work" / "raw_fc"      # firecrawl 原始输出缓存：改清洗规则时不用再联网抓一遍

# ── 噪音清洗 ──────────────────────────────────────────────────────────────

# 命中即从该行起丢弃后面全部（页脚区起始标志）
FOOTER = re.compile(
    r"^(?:"
    r"##\s*(?:Related articles|Recommended products|You may also|Editor['’]?s Recommendation"
    r"|Customers Also|You Might Also Like|Disclaimer)"
    r"|Disclaimer\s*[:：]"
    r"|Copyright ©"
    r"|Cookie policy"
    r"|Enable cookies to use the shopping cart"
    r"|Choosing a selection results in a full page refresh"
    r"|Your CART|WISHLISTVISITEDCART"
    r"|You don't have any (?:liked|visited) products"
    r"|\[Share on (?:Twitter|Pinterest|Facebook|WhatsApp)"
    r"|###\s*About the author"
    r"|^#\s+shop\.app is blocked"
    r"|^×$"
    r")", re.I)

# 单行噪音
NOISE = re.compile(
    r"(?:Enable cookies to use the shopping cart|Cookie policy"
    r"|We use cookies and similar technologies|New product arrivals|Special Offers For You"
    r"|recomsale|Skip to content|Switch to your local store|Opens external website"
    r"|Opens in a new window|^\s*Share\s*$|^\s*Pin it\s*$|^\s*Tweet\s*$|^\s*Copy link\s*$"
    r"|^\s*All articles\s*$|^\s*Table of contents\s*$|^\s*\[[^\]]*\]\([^)]*\)\s*$"
    # 栏头 byline（紧跟 H1，和页脚作者简介同形，但不是正文）
    r"|^\s*(?:MEDICALLY REVIEWED BY|WRITTEN BY|REVIEWED BY)\b.*$"
    r"|^\s*(?:Updated on|Last updated|By)\s*:?.*\d{4}\s*$"
    r"|^\s*By\s*:\s*\w.*$"
    r"|^\s*Show (?:more|less|all)\s*$"
    r"|^\s*Add to Cart\s*$"
    r")", re.I)

AUTHOR_LINK = re.compile(r"\]\([^)]*/pages/author/")
PRICE = re.compile(r"^(?:~~)?\$\d|\d+% off$|^Add to Cart$", re.I)

# 装饰/占位/商品卡图
NOISE_IMG = re.compile(
    r"(shopifycloud/storefront|/assets/|/cdn/shop/t/|payment|paypal|visa|master|maestro|"
    r"american express|apple pay|google pay|discover|Translation missing|"
    r"yg-blog-|email-subscribe|placeholder|/logo|KTC\.jp|data:image/gif;base64)", re.I)

PRODUCT_CARD = re.compile(
    r"^(?:##\s*\[|\$\d|~~\$|Rated \d|-\d+%$|\d+\.\d$|\d+$|"
    r"\[Quick view\]|\[Compare\]|\[Add to Wishlist\]|Fast Sterilize|RoseTeal)", re.I)

BIO = re.compile(
    r"^(?:Reviewed by|Medically reviewed by|Written by"
    r"|(?:Mary Bicknell|Shelly Umstot|Una Qian|Zola Zhang)[,\s]"
    r"|[A-Z][a-z]+ [A-Z][a-z]+, (?:MSN|BSN|RN|RNC|IBCLC|ANLC|MD|RD)[,\s])", re.I)


def article_start(lines: list[str]) -> int | None:
    """文章 H1 = 其后存在长段落的一级标题。导航区与页脚区都只有短行。"""
    for i, l in enumerate(lines):
        if re.match(r"^#\s+\S", l):
            if max((len(x.strip()) for x in lines[i:]), default=0) > 300:
                return i
    return None


def clean_article(md: str) -> str:
    md = re.sub(r"\r\n", "\n", md)
    md = re.sub(r"^<!--.*?-->\s*", "", md, flags=re.S)
    md = re.sub(r"^\s*<!--\s*抓取方式:.*?-->\s*$", "", md, flags=re.M)
    lines = md.split("\n")

    # 1) 定位文章起点
    i = article_start(lines)
    if i:
        lines = lines[i:]

    # 2) 砍页脚区
    # 「正文已开始」= 出现过 >300 字的**散文**行。图片行（`![…](…)`）的 URL 很长，
    # 若把它也算作正文，栏头的 `MEDICALLY REVIEWED BY` / `Written by …` 会被当成
    # 页脚作者简介，把整篇砍成几百字。
    started = False
    cut = len(lines)
    for n, l in enumerate(lines):
        st = l.strip()
        if len(st) > 300:
            if not st.startswith(("![", "[![")):
                started = True
            continue
        if not started:
            continue
        bare = re.sub(r"^[-*+]\s+", "", st)
        if FOOTER.match(st) or FOOTER.match(bare) or (BIO.match(st) and len(st) < 90):
            cut = n
            break
    lines = lines[:cut]

    # 2.5) 正文只允许一个 H1：firecrawl 会把正文里带 emoji 的 H2 也输出成 `# `
    seen_h1 = False
    for n, l in enumerate(lines):
        if re.match(r"^#\s+\S", l):
            if seen_h1:
                lines[n] = "#" + l
            else:
                seen_h1 = True

    # 3) 去掉栏头家具块（作者署名块 / 商品卡）
    drop: set[int] = set()
    for n, l in enumerate(lines):
        st = l.strip()
        # 作者块：作者主页链接 → 其前的头像图 → 直到 `Show more/less`
        if AUTHOR_LINK.search(st):
            k = n - 1
            while k >= 0 and (not lines[k].strip() or lines[k].strip().startswith("![")):
                drop.add(k); k -= 1
            for m in range(n, min(n + 12, len(lines))):
                drop.add(m)
                if re.match(r"^\s*Show (?:more|less|all)\s*$", lines[m], re.I):
                    break
        # 商品卡：`Add to Cart` 往回吃掉紧跟其上的图 / 链接 / 价格 / 短行
        if re.match(r"^\s*Add to Cart\s*$", st, re.I):
            drop.add(n)
            k = n - 1
            while k >= 0 and n - k <= 8:
                pk = lines[k].strip()
                if (not pk) or pk.startswith(("![", "[![")) or PRICE.match(pk) \
                        or len(pk) <= 60 or NOISE.match(pk):
                    drop.add(k); k -= 1
                else:
                    break

    # 4) 逐行过滤
    out = []
    for n, l in enumerate(lines):
        if n in drop:
            continue
        st = l.strip()
        if not st:
            out.append("")
            continue
        if NOISE_IMG.search(st) and st.startswith(("![", "[![")):
            continue
        if "Translation missing" in st or "data:image/gif;base64" in st:
            continue
        if NOISE.search(st) and len(st) < 220:
            continue
        if PRODUCT_CARD.match(st) and len(st) < 160:
            continue
        if re.match(r"^[×✕✖]$", st):
            continue
        out.append(l)
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


# ── 抓取 ──────────────────────────────────────────────────────────────────

def get(url: str, tries: int = 3) -> str | None:
    for a in range(tries):
        try:
            p = subprocess.run([str(FCRAWL), url], capture_output=True, text=True, timeout=300)
        except Exception as e:
            print(f"    exec {e}", flush=True); time.sleep(5); continue
        if p.returncode == 0 and len(p.stdout) > 1500:
            return p.stdout
        time.sleep(4 + 4 * a)
    return None


def dirty(t: str) -> bool:
    return ("原文此处为表格" in t) or (len(re.findall(r"^#\s+\S", t, re.M)) > 1) \
        or ("抓取方式: fcrawl" in t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-dirty", action="store_true")
    ap.add_argument("--reclean", action="store_true",
                    help="不联网，用 work/raw_fc/ 缓存的原始输出重新清洗")
    a = ap.parse_args()

    jobs = []
    for f in sorted(DST.rglob("*.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        if a.only_dirty and not dirty(t):
            continue
        m = re.search(r"<!--\s*来源URL:\s*(\S+?)\s*-->", t)
        if m:
            jobs.append((f, m.group(1)))
    print(f"{'重新清洗' if a.reclean else 'firecrawl 抓取'} {len(jobs)} 篇", flush=True)

    ok = fail = 0
    for n, (f, u) in enumerate(jobs, 1):
        cache = RAW / f.parent.name / f.name
        if a.reclean:
            if not cache.exists():
                fail += 1; print(f"[{n}/{len(jobs)}] 无缓存 {u[-40:]}", flush=True); continue
            raw = cache.read_text(encoding="utf-8", errors="replace")
        else:
            raw = get(u)
            if not raw:
                fail += 1; print(f"[{n}/{len(jobs)}] FAIL {u[-48:]}", flush=True); continue
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(raw, encoding="utf-8")
        body = clean_article(raw)
        if len(body) < 800:
            fail += 1; print(f"[{n}/{len(jobs)}] 清洗后过短 {len(body)} {u[-40:]}", flush=True); continue
        f.write_text(f"<!-- 来源URL: {u} -->\n\n{body}\n", encoding="utf-8")
        ok += 1
        print(f"[{n}/{len(jobs)}] ok {len(body):7,}  {f.name[:42]}", flush=True)
        if not a.reclean:
            time.sleep(0.8)
    print(f"\n完成 ok={ok} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
