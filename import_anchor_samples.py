#!/usr/bin/env python3
"""Import the Momcozy/KTC anchor-text sample pack into the five 锚文本规范.md files.

For each category it keeps the existing rule text (type table + link-selection rules) and
regenerates a "真实文章样本" section from work/samples/五类CSV/<栏目>.csv, preserving the
source order of every row (including H2 rows that carry no link).
"""
from __future__ import annotations
import csv, json, pathlib

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
SAMPLES = ROOT / "work" / "samples"
SPEC = SAMPLES / "数据说明与复核.md"
MARK = "<!-- 真实文章样本：begin（由 import_anchor_samples.py 生成，勿手改） -->"
MARK_END = "<!-- 真实文章样本：end -->"

CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]

# the 7 dead targets listed in 数据说明与复核.md
DEAD = {
    "https://momcozy.com/blogs/babycare/how-often-to-change-newborn-diaper",
    "https://momcozy.com/blogs/baby/home-playard-vs-travel-crib",
    "https://momcozy.com/blogs/babycare/pumping-breast-milk-at-work-checklist",
    "https://momcozy.com/products/s12-pro-double-wearable-breast-pump-and-4-in-1-hands-free-pumping-bra",
    "https://momcozy.com/products/momcozy-screw-on-breastmilk-storage-bags48pcs",
    "https://momcozy.com/products/water-wipes-higher-level-of-purity",
    "https://momcozy.com/blogs/babycare/tracking-baby-pee-poop-tips-for-parents",
}

# anchor types the brief asks us to keep, with their routing focus
TYPES = [
    ("术语", "展开一个术语的基础含义", "科技与信息较常用", "定义／解释页"),
    ("专业定义", "定义有专业边界的概念", "科技与信息、设置与使用", "定义页，不能是产品页"),
    ("机制", "延伸解释原因、组件或处理链", "科技与信息", "更深一层的机制说明"),
    ("动作", "读者现在要做的具体操作", "帮助与提示、设置与使用", "提供步骤的页面"),
    ("判别／排障", "分辨异常或进入修复路径", "帮助与提示", "可执行的检查路径"),
    ("主张", "支撑文中的可核查断言", "五类通用", "更完整的解释或外部原始证据"),
    ("原始证据", "指向标准、测试、研究或官方说明", "通常为外部引用", "规范／测试／官方文档"),
    ("比较轴", "展开两个方案共同的评估维度", "产品对比", "不宣传单方的维度说明"),
    ("选择条件", "进一步帮助用户选方案", "产品对比、购买指南", "真正做决策的页面"),
    ("兼容与规格", "核查型号、接口、使用条件", "购买指南、设置与使用、帮助与提示", "以具体型号为准的参数页"),
    ("品类", "从问题引向确有关系的品类页", "购买指南", "服务于购买判断的品类页"),
    ("型号", "在明确适配条件后落到具体型号", "购买指南、产品对比", "明确型号页"),
    ("前置条件", "操作前必须完成的准备", "设置与使用", "解释如何满足依赖的页面"),
    ("结果验证", "配置或恢复后确认成功", "设置与使用、帮助与提示", "可观察的成功状态"),
    ("相邻意图", "同一问题的互补文章（为什么／怎么修）", "五类互链", "提供不同答案的文章"),
    ("待核实", "样本锚文本的上下文未读，类型未判定", "—", "—"),
]


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def load(cat: str) -> list[dict]:
    with (SAMPLES / "五类CSV" / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("来源URL", "H1", "H2", "锚文本", "内链URL"):
            r[k] = (r.get(k) or "").strip()
    return rows


def article_order(rows: list[dict]) -> list[str]:
    seen, out = set(), []
    for r in rows:
        if r["来源URL"] not in seen:
            seen.add(r["来源URL"]); out.append(r["来源URL"])
    return out


def render(cat: str, rows: list[dict]) -> tuple[str, dict]:
    mom = [r for r in rows if "momcozy" in r["来源URL"]]
    ktc = [r for r in rows if "ktc" in r["来源URL"]]
    dead_rows = [r for r in rows if r["内链URL"] in DEAD]
    stats = {"rows": len(rows), "links": sum(1 for r in rows if r["内链URL"]),
             "mom": len(article_order(mom)), "ktc": len(article_order(ktc)),
             "dead": len(dead_rows)}
    L = [MARK, "", "## 三、真实文章样本（Momcozy / KTC）", "",
         f"本栏目样本共 **{stats['rows']} 行 / {stats['links']} 行带正文内链**，"
         f"来自 Momcozy {stats['mom']} 篇、KTC {stats['ktc']} 篇。五列一一对应，"
         "**H2 没有内链的行也保留**（锚文本与目标 URL 为空），这样能看到哪些 H2 本来就不需要链接。", "",
         "> **竞品目标 URL 是分析样本，不是 Divoom 成稿的内链候选。** Codex 给 Divoom 补内链时，"
         "只从 `../发布与链接记录/已发布文章.csv` 找真实已发布的 Divoom URL；不存在就登记到 "
         "`../发布与链接记录/待补内链.csv`。", ""]
    for label, subset in (("Momcozy", mom), ("KTC", ktc)):
        L += [f"### {label}", ""]
        for url in article_order(subset):
            art = [r for r in subset if r["来源URL"] == url]
            h1 = art[0]["H1"] or "（H1 未在提取文本中单独出现，待人工核对）"
            L += [f"#### {esc(h1)}", "", f"- 来源 URL：`{url}`",
                  f"- 行数：{len(art)}（其中带内链 {sum(1 for r in art if r['内链URL'])}）", "",
                  "| H2 | 锚文本 | 内链URL |", "| --- | --- | --- |"]
            for r in art:
                link = r["内链URL"]
                if link in DEAD:
                    link = f"⚠️ 原文失效链接（404）／勿作为推荐：`{link}`"
                elif link:
                    link = f"`{link}`"
                L.append(f"| {esc(r['H2']) or '（空）'} | {esc(r['锚文本']) or '（无内链）'} | {link or '（无内链）'} |")
            L.append("")
    L += ["### 使用限制（来自数据说明与复核.md）", "",
          f"1. 本栏目样本含 **{stats['dead']} 行**指向本次核对已 404 的目标 URL，已在表中标注"
          "「原文失效链接／勿作为推荐」，保留原始映射仅供研究。",
          "2. Momcozy 共 34 篇在提取文本中未单独输出 `# H1`，表中标注「H1 未在提取文本中单独出现，"
          "待人工核对」；**不得宣称这些标题是页面 HTML H1 已验证**。",
          "3. 四篇 Momcozy 的根路径未返回正文，CSV 使用同站其他语言路径读取；跨地区链接不能直接作为"
          " Divoom 内链目的地。",
          "4. 锚文本类型**不能只从这五列推断**。上表不标注类型；需要归类时必须回到来源文章阅读锚文本"
          "前后的句子，读不到上下文的留在「待核实」。",
          "5. 同站链接并不都适合 Divoom 复制；本表只记录竞品怎么写，不预先给它们打「好锚文本」标签。", "",
          MARK_END]
    return "\n".join(L), stats


def main() -> None:
    grand = {"rows": 0, "links": 0, "dead": 0}
    for cat in CATS:
        rows = load(cat)
        section, st = render(cat, rows)
        f = LIB / cat / "锚文本规范.md"
        text = f.read_text(encoding="utf-8")
        if MARK in text:                       # idempotent: replace the previous import
            text = text[:text.index(MARK)].rstrip() + "\n"
        body = text.rstrip() + "\n\n" + section + "\n"
        f.write_text(body, encoding="utf-8")
        grand = {k: grand[k] + st[k] for k in grand}
        print(f"{cat:8} 行 {st['rows']:4} 带链接 {st['links']:3} | Momcozy {st['mom']:2} 篇 "
              f"KTC {st['ktc']} 篇 | 失效链接行 {st['dead']}")
    print(f"\n合计: 行 {grand['rows']} | 带链接 {grand['links']} | 失效链接行 {grand['dead']}")


if __name__ == "__main__":
    main()
