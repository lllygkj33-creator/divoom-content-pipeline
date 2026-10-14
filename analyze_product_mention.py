#!/usr/bin/env python3
"""分析竞品（Momcozy / KTC）正文里「产品是怎么被提及的」——为《产品植入规范》提供实证。

回答四个问题：
  1. 多少篇文章真的提到了自家产品？
  2. 提在哪个位置？（第几个 H2、全篇前/后半段）
  3. 用什么方式提？（产品级 H2 / 段内自然句 / 商品卡 / 链接锚文本）
  4. 锚文本长什么样，多少词？（对照 `锚文本总规范.md` 的中位 4 词）

用法：python3 analyze_product_mention.py
"""
from __future__ import annotations

import collections
import pathlib
import re
import statistics as st

ROOT = pathlib.Path(__file__).parent
BODIES = ROOT / "work" / "bodies"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]

BRAND = re.compile(r"\b(Momcozy|KTC)\b", re.I)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# 自家商品页 / 集合页链接
OWN_LINK = re.compile(r"https?://(?:www\.)?(?:momcozy\.com|ktcplay\.com|us\.ktcplay\.com)/"
                      r"(products|collections)/", re.I)
# 产品级 H2：标题里带品牌名，或像型号名（大写字母+数字/连字符）
PROD_H2 = re.compile(r"\b(?:Momcozy|KTC)\b|\b[A-Z][A-Za-z]*[- ]?(?:Pro|Plus|Max|Mini|SE|HQ|Ultra|\d{1,3})\b")


def sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    lines = body.split("\n")
    h1 = ""
    secs: list[tuple[str, str]] = []
    cur_title, cur = None, []
    for l in lines:
        if re.match(r"^##\s+\S", l):
            if cur_title is not None:
                secs.append((cur_title, "\n".join(cur)))
            cur_title, cur = l.strip("# ").strip(), []
        elif re.match(r"^#\s+\S", l):
            h1 = l.strip("# ").strip()
        elif cur_title is not None:
            cur.append(l)
    if cur_title is not None:
        secs.append((cur_title, "\n".join(cur)))
    return h1, secs


def main() -> None:
    n_art = 0
    n_mention = 0
    prod_h2_articles = 0
    pos_ratio: list[float] = []
    mention_kinds = collections.Counter()
    anchors: list[tuple[str, str]] = []
    sec_index: list[int] = []
    n_secs: list[int] = []
    per_site = collections.Counter()
    cat_density: dict[str, list[float]] = collections.defaultdict(list)

    for cat in CATS:
        for f in sorted((BODIES / cat).glob("*.md")):
            body = re.sub(r"^<!--.*?-->\s*", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
            n_art += 1
            site = "KTC" if ("ktcplay" in body[:400] or "ecomsend" in body[:400]) else "Momcozy"
            per_site[site] += 1
            _, secs = sections(body)
            if not secs:
                continue
            n_secs.append(len(secs))
            hit_any = False
            first_idx = None
            # 每节：统计品牌/型号提及与链接
            for i, (title, txt) in enumerate(secs):
                brands = BRAND.findall(title) + BRAND.findall(txt)
                own = OWN_LINK.findall(txt) + OWN_LINK.findall(title)
                if brands or own:
                    hit_any = True
                    if first_idx is None:
                        first_idx = i
                    mention_kinds["段内自然提及"] += 1 if brands else 0
                    mention_kinds["含自家商品/集合链接"] += 1 if own else 0
                if brands and PROD_H2.search(title) and BRAND.search(title):
                    mention_kinds["产品级 H2"] += 1
            # 全篇锚文本
            for a, u in LINK.findall(body):
                if OWN_LINK.search(u):
                    anchors.append((a.strip(), u))
            if hit_any:
                n_mention += 1
                if first_idx is not None:
                    pos_ratio.append(first_idx / max(1, len(secs) - 1))
                    sec_index.append(first_idx)
                    cat_density[cat].append(first_idx / max(1, len(secs) - 1))
            if any(BRAND.search(t) and PROD_H2.search(t) for t, _ in secs):
                prod_h2_articles += 1

    print(f"{'='*74}\n竞品产品提及分析（{n_art} 篇：Momcozy {per_site['Momcozy']} / KTC {per_site['KTC']}）\n{'='*74}")
    print(f"\n① 覆盖率")
    print(f"   提到自家产品的文章：{n_mention}/{n_art}（{n_mention*100//n_art}%）")
    print(f"   含「产品级 H2」的文章：{prod_h2_articles}/{n_art}（{prod_h2_articles*100//n_art}%）")
    print(f"   篇均 H2 节数：中位 {st.median(n_secs):.0f}")

    print(f"\n② 首次提及的位置（按 H2 序号归一化，0=最前 1=最后）")
    if pos_ratio:
        print(f"   中位 {st.median(pos_ratio):.2f}　均值 {sum(pos_ratio)/len(pos_ratio):.2f}"
              f"　n={len(pos_ratio)}")
        buckets = collections.Counter()
        for r in pos_ratio:
            buckets["前 1/3" if r < 1/3 else "中 1/3" if r < 2/3 else "后 1/3"] += 1
        for k in ("前 1/3", "中 1/3", "后 1/3"):
            print(f"     {k:<6} {buckets[k]:>3} 篇（{buckets[k]*100//len(pos_ratio)}%）")
    for c in CATS:
        if cat_density[c]:
            print(f"   {c:<8} 首次提及中位位置 {st.median(cat_density[c]):.2f}　n={len(cat_density[c])}")

    print(f"\n③ 提及方式（按「节」计数，可叠加）")
    for k, v in mention_kinds.most_common():
        print(f"   {k:<22} {v} 节")

    print(f"\n④ 自家链接的锚文本（n={len(anchors)}）")
    if anchors:
        wc = [len(re.findall(r"[A-Za-z0-9']+", a)) for a, _ in anchors]
        print(f"   词数：中位 {st.median(wc):.0f}　均值 {sum(wc)/len(wc):.1f}"
              f"　区间 {min(wc)}–{max(wc)}")
        b = collections.Counter()
        for w in wc:
            b["1–2 词" if w <= 2 else "3–6 词" if w <= 6 else "7–10 词" if w <= 10 else "11+ 词"] += 1
        for k in ("1–2 词", "3–6 词", "7–10 词", "11+ 词"):
            print(f"     {k:<8} {b[k]:>4} （{b[k]*100//len(wc)}%）")
        print(f"\n   去重锚文本示例（前 18 条）：")
        seen = set()
        for a, u in anchors:
            k = a.lower()
            if k in seen:
                continue
            seen.add(k)
            kind = "→ 商品页" if "/products/" in u else "→ 集合页"
            nw = len(re.findall(r"[A-Za-z0-9']+", a))
            print(f"     {nw} 词  {a[:52]:<54}{kind}")
            if len(seen) >= 18:
                break


if __name__ == "__main__":
    main()
