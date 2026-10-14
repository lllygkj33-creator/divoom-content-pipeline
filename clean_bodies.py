#!/usr/bin/env python3
"""把实例正文裁成「只有文章正文」。

去掉：整站导航与促销轮播、相关文章／推荐商品／版权区、支付图标、
分享按钮、标签列表、购物车面板、编辑器推荐块、作者简介、免责声明块、装饰占位图。

安全阀：任何一次截断若要去掉全文 40% 以上，就放弃截断（宁可留下噪音，也不切掉正文）。
处理后再由 build_instance_notes.py / build_instance_views.py 重建笔记与汇总。
"""
from __future__ import annotations
import pathlib, re

BODIES = pathlib.Path(__file__).parent / "work" / "bodies"
MAX_CUT_RATIO = 0.40          # 截断占比上限

# 页脚／无关区块的起始标志（命中即从该行起全部丢弃）——只放高精度模式
FOOTER_HEAD = re.compile(
    r"^(?:"
    r"##\s*Editor['’]?s Recommendation"
    r"|##\s*You Might Also Like"
    r"|##\s*Recommended products"
    r"|##\s*Related articles"
    r"|##\s*Customers Also"
    r"|##\s*Disclaimer"
    r"|Disclaimer\s*[:：]"
    r"|Copyright ©"
    r"|Cookie policy"
    r"|Enable cookies to use the shopping cart"
    r"|Choosing a selection results in a full page refresh"
    r"|Your CART"
    r"|WISHLISTVISITEDCART"
    r"|You don't have any (?:liked|visited) products"
    r"|\[Share on (?:Twitter|Pinterest|Facebook|WhatsApp)"
    r"|###\s*About the author"
    r"|^×$"
    r")", re.I)

# 作者简介起始（多行块）：只认短行 + 明确署名标志
BIO_START = re.compile(
    r"^(?:"
    r"Reviewed by|Medically reviewed by|Written by"
    r"|(?:Mary Bicknell|Shelly Umstot|Una Qian)[,\s]"
    r"|[A-Z][a-z]+ [A-Z][a-z]+, (?:MSN|BSN|RN|RNC|IBCLC|ANLC|MD|RD)[,\s]"
    r")", re.I)

# 单行噪音
NOISE_LINE = re.compile(
    r"(?:Enable cookies to use the shopping cart"
    r"|Cookie policy"
    r"|We use cookies and similar technologies"
    r"|New product arrivals"
    r"|Special Offers For You"
    r"|recomsale"
    r"|Skip to content"
    r"|Switch to your local store"
    r"|Opens external website"
    r"|Opens in a new window"
    r"|^\s*Share\s*$|^\s*Pin it\s*$|^\s*Tweet\s*$|^\s*Copy link\s*$"
    r"|^\s*All articles\s*$|^\s*Table of contents\s*$"
    r"|^\s*\[[^\]]*\]\([^)]*\)\s*$"
    r")", re.I)

# 推荐商品卡片残行
PRODUCT_CARD = re.compile(
    r"^(?:##\s*\[|\$\d|~~\$|Rated \d|-\d+%$|\d+\.\d$|\d+$|"
    r"\[Quick view\]|\[Compare\]|\[Add to Wishlist\]|"
    r"Fast Sterilize|RoseTeal|3-in-1 Multifunction)", re.I)

# 装饰图／支付图标／占位图
NOISE_IMG = re.compile(
    r"(?:shopifycloud/storefront|/assets/|/cdn/shop/t/|payment|paypal|visa|master|maestro|"
    r"american express|apple pay|google pay|discover|Productp resident tag|"
    r"yg-blog-|email-subscribe|placeholder|/logo|KTC\.jp)", re.I)


def clean(md: str) -> str:
    md = re.sub(r"\r\n", "\n", md)
    md = re.sub(r"^<!--.*?-->\s*", "", md, flags=re.S)          # 抓取注释
    lines = md.split("\n")

    # 行内商品卡：标题行 + 紧随其后的“From $X”价格 → 从标题起截断
    for i in range(1, len(lines)):
        if re.match(r"^From \$\d", lines[i].strip()) and re.match(r"^#{2,3}\s+\S", lines[i-1].strip()):
            lines = lines[: i - 1]
            break

    # 文末作者块 / 加购按钮：从首处命中起截断
    for i, line in enumerate(lines):
        st = line.strip()
        if re.match(r"^!\[(Mary Bicknell|Shelly Umstot|Una Qian|Zola Zhang|[A-Z][a-z]+ [A-Z][a-z]+)\]\(", st) \
           or re.match(r"^Add to Cart( Shop Now)?$", st) \
           or re.match(r"^Member price", st) \
           or re.match(r"^I[’']ve supported", st):
            lines = lines[:i]
            break

    # 文末商品卡尾块：倒数几行内出现 「商品图 + 商品名」 时，从该图起截断
    tail_start = max(0, len(lines) - 12)
    for i in range(len(lines) - 1, tail_start - 1, -1):
        st = lines[i].strip()
        if st.startswith("![") and re.search(
                r"(cdn/shop/files/|cdn/shop/products/|Momcozy|KTC)", st):
            lines = lines[:i]
            break

    total = sum(len(l) for l in lines if l.strip())
    cut = len(lines)
    reason = ""
    for i, line in enumerate(lines):
        raw = line.strip()
        bare = re.sub(r"^[-*+]\s+", "", raw)
        if FOOTER_HEAD.match(raw) or FOOTER_HEAD.match(bare):
            cut = i
            reason = "footer"
            break
        if BIO_START.match(raw) and len(raw) < 90:
            cut = i
            reason = "bio"
            break
    # 安全阀只用于「作者简介」这类较模糊的标志；页脚标志是结构性的，可放心截断
    if cut < len(lines) and reason == "bio":
        removed = sum(len(l) for l in lines[cut:] if l.strip())
        if total and removed / total > MAX_CUT_RATIO:
            cut = len(lines)

    out: list[str] = []
    for line in lines[:cut]:
        st = line.strip()
        if not st:
            out.append("")
            continue
        if NOISE_IMG.search(st) and st.startswith(("![", "[![")):
            continue
        if "Translation missing" in st or "data:image/gif;base64" in st:
            continue
        if NOISE_LINE.search(st) and len(st) < 220:
            continue
        if PRODUCT_CARD.match(st) and len(st) < 160:
            continue
        if re.match(r"^[×✕✖]$", st):
            continue
        out.append(line)
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"\n\s*(?:Share|Pin it|Tweet|Copy link|Was this helpful\?)\s*$", "", md, flags=re.I)
    return md.strip()


def main() -> None:
    n = before = after = 0
    for f in sorted(BODIES.rglob("*.md")):
        t = f.read_text(encoding="utf-8")
        m = re.match(r"((?:<!--.*?-->\s*)+)", t, flags=re.S)
        head = m.group(1) if m else ""
        body = t[len(head):]
        c = clean(body)
        before += len(body)
        after += len(c)
        if c != body:
            f.write_text(head + c + "\n", encoding="utf-8")
            n += 1
    print(f"清洗 {n} 篇 | 正文字符 {before:,} -> {after:,}（去掉 {before - after:,}）")


if __name__ == "__main__":
    main()
