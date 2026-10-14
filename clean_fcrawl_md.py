#!/usr/bin/env python3
"""把 fcrawl 抓来的 markdown 裁成正文：去掉顶部导航/促销轮播/页脚，
保留标题、H2、段落、列表、图片与表格占位。"""
from __future__ import annotations
import pathlib, re

NOISE_LINE = re.compile(
    r"^(recomsale|skip to content|switch to your local store|go$|\d+% off|"
    r"add to cart|shop now|new$|hot$|best seller|sale price|regular price|"
    r"special offers|\[\!\[|!\[)", re.I)
# 邮件订阅/轮播等装饰图
PROMO_IMG = re.compile(r"yg-blog-email-subscribe|/cdn/shop/t/|Special Offers", re.I)


def clean(md: str) -> str:
    md = re.sub(r"\r\n", "\n", md)
    lines = md.split("\n")
    # 1) 从正文标题开始：优先第一个 # 标题；否则第一个出现的长段落
    start = 0
    for i, l in enumerate(lines):
        if re.match(r"^#\s+\S", l):
            start = i
            break
    lines = lines[start:]
    # 2) 去掉顶部商品卡轮播：连续的图片/链接/短商品行
    keep, i = [], 0
    seen_heading = False
    for l in lines:
        st = l.strip()
        if re.match(r"^#{2,4}\s+\S", st):
            seen_heading = True
        if not seen_heading:
            # 标题区：只保留标题行与真正的长段落
            if re.match(r"^#\s+\S", st) or len(st) > 220:
                keep.append(l)
            continue
        keep.append(l)
    lines = keep
    # 3) 去掉明显的导航/页脚行
    out = []
    for l in lines:
        st = l.strip()
        if st and NOISE_LINE.match(st) and len(st) < 160:
            continue
        if re.match(r"^\[.*\]\(.*\)\s*$", st) and len(st) < 90:      # 纯链接行
            continue
        if re.match(r"^\\+\s*$", st):
            continue
        if PROMO_IMG.search(st) and len(st) < 400:
            continue
        out.append(l)
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"^\s*\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)\s*$", "", md, flags=re.M)
    return md.strip()


def main() -> None:
    n = 0
    for f in sorted(pathlib.Path("work/bodies").rglob("*.md")):
        t = f.read_text(encoding="utf-8")
        if "抓取方式: fcrawl" not in t:
            continue
        head, _, body = t.partition("\n\n")
        c = clean(body)
        if len(c) > 800:
            f.write_text(head + "\n\n" + c + "\n", encoding="utf-8")
            n += 1
    print(f"清洗 fcrawl 正文 {n} 篇")


if __name__ == "__main__":
    main()
