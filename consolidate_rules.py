#!/usr/bin/env python3
"""Consolidate the five 栏目 after the sample import.

- 锚文本规范.md  : 锚文本类型表（from 导入需求 4.5）+ 发布时选链规则 + 真实文章样本(生成)
- 标题与大纲规范.md : FX 表骨架（待迁公式）+ 真实样本观察表（H1 / 来源URL / H2 箭头序列）
Sample sections are generated from work/samples/五类CSV and are idempotent.
"""
from __future__ import annotations
import csv, pathlib, re

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
S = ROOT / "work" / "samples"
B, E = "<!-- 真实文章样本：begin", "<!-- 真实文章样本：end -->"

CATS = {
    "科技与信息": ("F", 13, "Technology Hub"),
    "帮助与提示": ("S", 12, "Support & Tips"),
    "产品对比": ("PC", 10, "Product Comparisons"),
    "购买指南": ("BG", 11, "Buying Guides"),
    "设置与使用": ("SU", 13, "Desk Setups"),
}
DEAD = {
 "https://momcozy.com/blogs/babycare/how-often-to-change-newborn-diaper",
 "https://momcozy.com/blogs/baby/home-playard-vs-travel-crib",
 "https://momcozy.com/blogs/babycare/pumping-breast-milk-at-work-checklist",
 "https://momcozy.com/products/s12-pro-double-wearable-breast-pump-and-4-in-1-hands-free-pumping-bra",
 "https://momcozy.com/products/momcozy-screw-on-breastmilk-storage-bags48pcs",
 "https://momcozy.com/products/water-wipes-higher-level-of-purity",
 "https://momcozy.com/blogs/babycare/tracking-baby-pee-poop-tips-for-parents",
}
# 锚文本类型表：来自《导入需求.md》4.5 的起始类型，逐类侧重见第 4.1 节
TYPES = [
 ("术语", "展开一个术语的基础含义", "句子首次出现该术语时", "用读者会搜的说法直接写该术语", "定义／解释页", "目标只是产品宣传页时不适用"),
 ("专业定义", "定义有专业边界的概念", "需要区分近义概念的句子后", "概念的完整叫法", "能给出边界的定义页", "不能用产品页冒充定义"),
 ("机制", "延伸解释原因、组件或处理链", "给出现象解释之后的下一句", "机制本身的名称", "更深入的机制说明", "目标只是重复现象描述时不用"),
 ("动作", "读者现在要做的具体操作", "步骤段落的起点", "动词短语（如何做）", "提供步骤的页面", "没有步骤可给时不用"),
 ("判别／排障", "分辨异常或进入修复路径", "症状描述之后", "症状或检查动作", "可执行的检查路径", "目标页只讲原理时不用"),
 ("主张", "支撑文中的可核查断言", "断言句结尾", "断言的关键词", "更完整的解释页", "站内无对应解释时改用外部原始证据"),
 ("原始证据", "指向标准、测试、研究或官方说明", "需要外部可信度时", "规范／测试名称", "外部规范、测试或官方文档", "不能为内链数量硬换成本站文章"),
 ("比较轴", "展开两个方案共同的评估维度", "对比句提出维度时", "维度名称", "不宣传单方的维度说明", "目标偏袒一方时不适用"),
 ("选择条件", "进一步帮助用户选方案", "给出候选之后的判断句", "条件短语（什么情况下选谁）", "真正做决策的页面", "只罗列参数不帮助决策的页面不用"),
 ("兼容与规格", "核查型号、接口、使用条件", "提到型号或接口适配时", "型号＋接口／条件", "以具体型号为准的参数页", "只用系列名泛指时不用"),
 ("品类", "从问题引向确有关系的品类页", "需要说明所属品类时", "品类名", "服务于购买判断的品类页", "与当前问题无关的品类不引"),
 ("型号", "在明确适配条件后落到具体型号", "适配条件已经写清之后", "型号名", "该型号的页面", "不能以型号替换原来的信息问题"),
 ("前置条件", "操作前必须完成的准备", "步骤开始之前", "准备工作名称", "解释如何满足依赖的页面", "条件已在同段写完时不必引"),
 ("结果验证", "配置或恢复后确认成功", "操作步骤之后", "可观察的成功状态", "说明可观察状态的页面", "无验收标准时不引"),
 ("相邻意图", "同一问题的互补文章（为什么／怎么修）", "文章收尾或转折处", "互补问题的问法", "提供不同答案的相邻文章", "两篇答案相同则不互链"),
 ("待核实", "本包样本的锚文本上下文未读，类型未判定", "—", "—", "—", "读不到上下文时留在此类，不得凭词面猜类型"),
]


def rows_of(cat: str) -> list[dict]:
    with (S / "五类CSV" / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        rs = list(csv.DictReader(f))
    for r in rs:
        for k in ("来源URL", "H1", "H2", "锚文本", "内链URL"):
            r[k] = (r.get(k) or "").strip()
    return rs


def esc(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ").strip()


def order(rs, pred):
    return list(dict.fromkeys(r["来源URL"] for r in rs if pred(r["来源URL"])))


def anchor_samples(cat: str, rs: list[dict]) -> str:
    mom, ktc = [r for r in rs if "momcozy" in r["来源URL"]], [r for r in rs if "ktc" in r["来源URL"]]
    L = [B + "（由 consolidate_rules.py 生成，勿手改） -->", "",
         "## 三、真实文章样本（Momcozy / KTC）", "",
         f"本栏目样本 **{len(rs)} 行**，其中 **{sum(1 for r in rs if r['内链URL'])} 行带正文内链**；"
         f"来自 Momcozy {len(order(rs, lambda u: 'momcozy' in u))} 篇、KTC {len(order(rs, lambda u: 'ktc' in u))} 篇。"
         "五列一一对应；**H2 没有内链的行也保留**，用来观察哪些 H2 本来就不需要链接。", "",
         "> **竞品目标 URL 是分析样本，不是 Divoom 成稿的内链候选。** Codex 给 Divoom 补内链时，"
         "只从 `../发布与链接记录/已发布文章.csv` 找真实已发布的 Divoom URL；不存在就登记到 "
         "`../发布与链接记录/待补内链.csv`。", ""]
    for label, subset in (("Momcozy", mom), ("KTC", ktc)):
        L += [f"### {label}", ""]
        for u in order(subset, lambda _u: True):
            art = [r for r in subset if r["来源URL"] == u]
            L += [f"#### {esc(art[0]['H1']) if art[0]['H1'] else '（H1 未在提取文本中单独出现，待人工核对）'}", "",
                  f"- 来源 URL：`{u}`",
                  f"- {len(art)} 行，带内链 {sum(1 for r in art if r['内链URL'])} 行", "",
                  "| H2 | 锚文本 | 内链URL |", "| --- | --- | --- |"]
            for r in art:
                lk = r["内链URL"]
                lk = (f"⚠️ 原文失效链接（404）／勿作为推荐：`{lk}`" if lk in DEAD
                      else (f"`{lk}`" if lk else "（无内链）"))
                L.append(f"| {esc(r['H2']) or '（空）'} | {esc(r['锚文本']) or '（无内链）'} | {lk} |")
            L += ["", "上表 H2 顺序：" + " → ".join(esc(h) or "（空）" for h in dict.fromkeys(r["H2"] for r in art)), ""]
    dead = sum(1 for r in rs if r["内链URL"] in DEAD)
    L += ["### 使用限制（来自数据说明与复核.md）", "",
          f"1. 本栏目有 **{dead} 行**指向本次核对已 404 的目标 URL，已在表中显著标注「原文失效链接／勿作为推荐」，"
          "保留原始映射仅供研究，**不得推荐给 Divoom 文章**。",
          "2. Momcozy 共 34 篇在提取文本中未单独输出 `# H1`；缺失处标注「待人工核对」，"
          "**不得宣称这些标题是页面 HTML H1 已验证**。",
          "3. 四篇 Momcozy 的根路径未返回正文，CSV 使用同站其他语言路径读取；跨地区链接不能直接作为"
          " Divoom 内链目的地。",
          "4. 锚文本类型**不能只从这五列推断**。上表不写类型；要归类必须回到来源文章读锚文本前后的句子，"
          "读不到上下文的留在「待核实」。",
          "5. 同站链接并不都适合 Divoom 复制；本表只记录竞品怎么写，不预先给它们打「好锚文本」标签。", "",
          E + " -->"]
    return "\n".join(L)


def anchor_doc(cat: str, focus: str, rs: list[dict]) -> str:
    tt = "\n".join(f"| {esc(a)} | {esc(b)} | {esc(c)} | {esc(d)} | {esc(e)} | {esc(f)} |" for a, b, c, d, e, f in TYPES)
    return f"""---
栏目: {cat}
文件类型: 锚文本规范
状态: 类型表已建（待用上下文校准），真实样本已导入
---

# {cat}｜锚文本规范

本栏目链接分两层：**规则层**（下方锚文本类型表）说明什么位置该用哪类锚文本；**实证层**（第三节真实文章样本）只登记能在原文正文里核对到的真实链接。两层都不能用页眉导航、商品卡、编辑推荐模块或页脚链接冒充正文锚文本。

**本栏目侧重：** {focus}

## 一、锚文本类型表（规则层）

| 锚文本类型 | 类型定义 | 适用的正文句子／位置 | 锚文本写法 | 目标页应回答什么 | 不适用／避免情形 |
| --- | --- | --- | --- | --- | --- |
{tt}

> 「待核实」一类用于：样本的锚文本上下文还没读，类型不能判定。**不得只凭锚文本文字猜类型。**

## 二、发布时的 Divoom 内链选择

1. 先从 `../发布与链接记录/已发布文章.csv` 找与当前句子子问题相符、URL 已发布且可访问的 Divoom 页面。
2. 再选精确、自然、长度适中的锚文本；没有合适目标就不强行添加。
3. 正文自然引出了未来应写的文章时，只在 `../发布与链接记录/待补内链.csv` 记录锚文本候选、上下文与期望目标；**发布正文中不要留下空链接或占位标记**。
4. 目标文章发布后，回访来源文章补链，并回填「待补内链」台账的最终锚文本与目标 URL。

> 「原始证据」通常是**外部引用**，不能为了内链数量硬换成本站文章。

{anchor_samples(cat, rs)}
"""


def title_doc(cat: str, pref: str, n: int, ktc_cat: str, rs: list[dict]) -> str:
    fx = "\n".join(
        f"| {pref}{i}／待命名 | 待补 | 待补 | 见下方 KTC／Momcozy 观察表 | 见下方观察表 | 见下方观察表 | 待补 | 待迁入公式与命名 |"
        for i in range(1, n + 1))
    obs = [B + "（由 consolidate_rules.py 生成，勿手改） -->", "",
           "## 真实样本观察表", "",
           f"来自样本包：Momcozy {len(order(rs, lambda u: 'momcozy' in u))} 篇 + "
           f"KTC {len(order(rs, lambda u: 'ktc' in u))} 篇（KTC 对应栏目：{ktc_cat}）。"
           "只登记**已读到的** H1 与 H2 顺序，不做 FX 归类：样本不足以判定每条公式，"
           "需要人工读正文后再回填上表。", ""]
    for label, pred in (("Momcozy", lambda u: "momcozy" in u), ("KTC", lambda u: "ktc" in u)):
        obs += [f"### {label}", "", "| H1 | 来源 URL | H2 箭头序列 | 行数 | 带内链 |", "| --- | --- | --- | --- | --- |"]
        for u in order(rs, pred):
            art = [r for r in rs if r["来源URL"] == u]
            h1 = esc(art[0]["H1"]) if art[0]["H1"] else "（H1 未在提取文本中单独出现，待人工核对）"
            seq = " → ".join(esc(h) or "（空）" for h in dict.fromkeys(r["H2"] for r in art))
            obs.append(f"| {h1} | `{u}` | {seq} | {len(art)} | {sum(1 for r in art if r['内链URL'])} |")
        obs.append("")
    obs += [E + " -->"]
    return f"""---
栏目: {cat}
文件类型: 标题与大纲规范
状态: FX 表待迁公式；真实样本观察表已导入
---

# {cat}｜标题与大纲规范

**本栏目的交付结果：** {DELIVER[cat]}

**路由边界：** 先按文章最终交付路由 —— 解释根因进科技与信息；恢复故障进帮助与提示；同轴决胜进产品对比；购买决策进购买指南；现场配置并验收进设置与使用。一个原始问题可以拆成两篇，但每篇只有一个主路由。

**本表用法：** 每行一个 FX 子类型。「H1 可迁移公式」是变量槽位，不是强制字面句式；原始问题里的限定词（`after`、`even when`、`without`、`vs`、`for [role]`）必须在 H2 推进里得到回应。「H2 箭头逻辑」只写 H2 的问题顺序，用 `→` 串联，不写 H3、不抄原文段落。

**命名空间提醒：** 信息类是 `F1–F13`；设置与使用是 `SU1–SU13`。两者**不是**同一命名空间，引用时必须带栏目路径。

## FX 对照表

| FX 编号／名称 | 适用问题与排除条件 | H1 可迁移公式 | 已核实范例 H1 | 范例文章 URL | H2 箭头逻辑 | H1→H2 检查点 | 样本状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
{fx}

{chr(10).join(obs)}
"""


DELIVER = {
 "科技与信息": "读完这一篇，用户要能解释根因、机制与边界。",
 "帮助与提示": "读完这一篇，用户要能恢复故障、确认是否修好。",
 "产品对比": "读完这一篇，用户要能在同一比较轴上选出条件赢家。",
 "购买指南": "读完这一篇，用户要能做出购买判断（允许得出「不需要买」）。",
 "设置与使用": "读完这一篇，用户要能完成现场配置并验收。",
}

FOCUS = {
 "科技与信息": "读完必须让用户**理解**：知道现象背后的机制、关键变量，以及解释在什么范围内成立。",
 "帮助与提示": "读完必须让用户**恢复**：能按症状分流、做可逆检查、确认是否修好。",
 "产品对比": "读完必须让用户**选出赢家**：在同一任务、同一比较轴上判断哪个方案更适合自己的条件。",
 "购买指南": "读完必须让用户**做出购买判断**：知道是否需要买、按什么标准选、哪些候选该淘汰。",
 "设置与使用": "读完必须让用户**完成配置并验收**：知道前置条件、按步骤配置、能观察到成功状态。",
}


def main() -> None:
    for cat, (pref, n, ktc) in CATS.items():
        rs = rows_of(cat)
        (LIB / cat / "锚文本规范.md").write_text(anchor_doc(cat, FOCUS[cat], rs), encoding="utf-8")
        (LIB / cat / "标题与大纲规范.md").write_text(title_doc(cat, pref, n, ktc, rs), encoding="utf-8")
        print(f"{cat:8} 锚文本规范.md / 标题与大纲规范.md 已重建（样本 {len(rs)} 行）")


if __name__ == "__main__":
    main()
