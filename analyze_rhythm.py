#!/usr/bin/env python3
"""统计五个栏目竞品正文的「段落推进节奏」，作为各栏目 `正文写作规范.md` 的证据基础。

只读 `work/bodies/<栏目>/*.md`，输出每个栏目的：

  开头   H1 到首个 H2 之间的段落数、词数，以及首段是「直接回答」还是「铺垫」
  推进   每个 H2 的段落数、词数、是否含列表/表格，以及 H2 之间靠什么衔接
  证据   外链数、数值断言数、产品提及数

用法： python3 analyze_rhythm.py [栏目]
"""
from __future__ import annotations

import pathlib
import re
import statistics as st
import sys

ROOT = pathlib.Path(__file__).parent
BODIES = ROOT / "work" / "bodies"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]

NUM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:W|mAh|h|hrs?|hours?|%|inch|inches|Hz|dB|GB|MB|px|k)\b", re.I)
EXT = re.compile(r"\]\((https?://(?!momcozy\.com|www\.momcozy\.com|cdn\.shopify)[^)]+)\)")
PROD = re.compile(r"\b(?:Momcozy|KTC|Divoom)\b", re.I)


def blocks(body: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """切成 (H1 后的开头段, [(H2 标题, 该节正文行)])"""
    lines = body.split("\n")
    intro: list[str] = []
    secs: list[tuple[str, list[str]]] = []
    cur: list[str] | None = None
    for l in lines:
        if re.match(r"^##\s+\S", l):
            secs.append((l.strip("# ").strip(), cur if cur is not None else intro))
            cur = []
        elif re.match(r"^#\s+\S", l):
            continue
        elif cur is None:
            intro.append(l)
        else:
            cur.append(l)
    if cur is not None:
        secs.append(("", cur))
    return intro, secs


def paras(lines: list[str]) -> list[str]:
    out, buf = [], []
    for l in lines:
        s = l.strip()
        if not s:
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        if s.startswith(("![", "|", ">")) or re.match(r"^[-*+]\s", s) or re.match(r"^\d+[.)]\s", s):
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        buf.append(s)
    if buf:
        out.append(" ".join(buf))
    return out


def wc(s: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", s))


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for cat in CATS:
        if only and only != cat:
            continue
        files = sorted((BODIES / cat).glob("*.md"))
        o_pn, o_wc, sec_pn, sec_wc = [], [], [], []
        has_list = has_table = 0
        ext, nums, prod = [], [], []
        openings: list[tuple[str, str]] = []
        for f in files:
            body = re.sub(r"^<!--.*?-->\s*", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
            intro, secs = blocks(body)
            ip = paras(intro)
            if ip:
                o_pn.append(len(ip))
                o_wc.append(wc(" ".join(ip)))
                if len(openings) < 3:
                    openings.append((f.name[:40], ip[0][:260]))
            for title, lines in secs:
                if not title:
                    continue
                p = paras(lines)
                if p:
                    sec_pn.append(len(p))
                    sec_wc.append(wc(" ".join(p)))
                if any(re.match(r"^[-*+]\s", l.strip()) for l in lines):
                    has_list += 1
                if any(l.strip().startswith("|") for l in lines):
                    has_table += 1
            ext.append(len(EXT.findall(body)))
            nums.append(len(NUM.findall(body)))
            prod.append(len(PROD.findall(body)))

        n = len(files)
        print(f"\n{'='*72}\n{cat}   n={n} 篇")
        print(f"  开头（H1→首个 H2）：段落 中位 {st.median(o_pn):.0f}　词数 中位 {st.median(o_wc):.0f}　"
              f"P10–P90 词数 {sorted(o_wc)[len(o_wc)//10]}–{sorted(o_wc)[len(o_wc)*9//10]}")
        print(f"  H2 节：段落 中位 {st.median(sec_pn):.0f}　词数 中位 {st.median(sec_wc):.0f}　"
              f"含列表 {has_list} 节　含表格 {has_table} 节")
        print(f"  外链 中位 {st.median(ext):.0f}（{sum(1 for e in ext if e==0)}/{n} 篇为 0）　"
              f"数值断言 中位 {st.median(nums):.0f}　品牌提及 中位 {st.median(prod):.0f}")
        for name, o in openings:
            print(f"    · {name}\n      {o}…")


if __name__ == "__main__":
    main()
