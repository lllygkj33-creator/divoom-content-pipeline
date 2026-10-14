#!/usr/bin/env python3
"""重建锚文本规范：一份总规范 + 五份栏目精简版。

栏目版结构（用户要求）：
  1) 锚文本总规范（三条摘要 + 链接到 总规范/锚文本总规范.md）
  2) 本栏目锚文本类型（总规范类型的子集，含词数标准）
  3) 锚文本对应链接（实例 URL + 锚文本 + 类型）
完整 745 行样本保留在文末附录，避免数据丢失。
类型是从真实实例按词形与上下文信号**反推的建议值**；上下文字段缺失，一律标注「待核实」。
"""
from __future__ import annotations
import csv, pathlib, re

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
S = ROOT / "work" / "samples" / "五类CSV"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]
NOISE = ("add to cart", "next article", "previous article", "shop now", "learn more",
         "read more", "click here", "buy now", "view all")
BRAND = re.compile(r"momcozy|ktc|^bm\d|\bm\d{2}[a-z]?\d?\b|\bs\d{2}\b|\bw1\b|eufy|dinerpal|changego|tuckgo", re.I)

# 类型：名称 -> (定义, 词数标准, 词形信号)
TYPES = {
 "术语": ("展开一个术语的基础含义（名词短语，指一个概念或物件）", "1–3 词", "光名词短语，无动词"),
 "专业定义": ("定义有专业边界的概念，让读者知道边界在哪", "2–6 词", "名词短语 + 边界词（meaning/scope/definition）"),
 "机制": ("延伸解释原因、组件或处理链；常与动作共用 how 句式，机制类说的是「为什么会这样」", "3–8 词", "why/how … work、because、produces"),
 "动作": ("读者现在要做的具体操作，或指向提供步骤的页面", "3–8 词", "动词开头或 how to + 动词"),
 "判别／排障": ("分辨异常或进入修复路径", "2–6 词", "troubleshoot/fix/not working/how to tell if"),
 "主张": ("支撑文中的可核查断言", "6–16 词", "完整句子或对句（常以 and/only when 连接）"),
 "原始证据": ("指向标准、测试、研究或官方说明（通常外部引用）", "2–8 词", "标准编号、机构名、study/test/report"),
 "比较轴": ("展开两个方案共同的评估维度", "1–4 词", "A vs B、-er than、维度名"),
 "选择条件": ("进一步帮助用户选方案", "3–8 词", "best/choose/how to choose/picking"),
 "兼容与规格": ("核查型号、接口、使用条件", "2–6 词", "compatibility/fit/size/works with/规格词"),
 "品类": ("从问题引向确有关系的品类页", "1–3 词", "复数品类名词，目标为集合页"),
 "型号": ("在明确适配条件后落到具体型号", "1–6 词", "品牌或型号代号"),
 "前置条件": ("操作前必须完成的准备", "2–6 词", "before/before you/check first/requires"),
 "结果验证": ("配置或恢复后确认成功", "3–8 词", "confirm/verify/test/check if it works"),
 "相邻意图": ("同一问题的互补文章（为什么／怎么修）", "3–10 词", "同类问题的另一种问法"),
 "待核实": ("词形不足以判定类型，须回原文读上下文", "—", "—"),
}
ORDER = list(TYPES)


def classify(anchor: str) -> str:
    """从词形与目标地址反推锚文本类型。这是**建议值**：样本没有原句上下文，
    无法确认的落到「待核实」，不硬猜。"""
    a = anchor.strip()
    low = re.sub(r"\s+", " ", a.lower()).strip()
    if (low in NOISE or low.startswith(("add to cart", "next article", "previous article",
                                        "ajouter au panier", "achetez", "toggle tax"))
            or low in ("product page", "product support page", "all monitors", "all-mini-led monitors")):
        return "噪声"
    if BRAND.search(a):
        return "型号"
    if re.search(r"collection\b|\brange\b", low):
        return "品类"
    if re.search(r"\bvs\.?\b|\bversus\b|\bdiffer(s|ence)?\b|\bthan\b", low):
        return "比较轴"
    if re.search(r"compatib|\bfit\b|\bfits\b|\bsize chart|dimension|\bworks with\b|"
                 r"what'?s included|\bmm\b|\binch|\blb\b|\boz\b", low):
        return "兼容与规格"
    if re.search(r"\b(upf|iso|iec|ipx?\d|standard|tested|study|report|midwife-reviewed|"
                 r"certificat)\b", low):
        return "原始证据"
    if re.search(r"^(what is|what are)\b|\bmeaning\b|\bscope\b|\bdefinition\b", low):
        return "专业定义"
    if re.search(r"\bbest\b|\bchoos(e|ing)\b|\bbuying guide\b|\bultimate guide\b|\bguide to\b|"
                 r"\bwhich\b|\bpicking\b|\bselection\b", low):
        return "选择条件"
    if re.search(r"\b(troubleshoot|how to tell|not working|no signal|fix(es|ing)?|symptom|"
                 r"clean a|prevent|repair)\b", low):
        return "判别／排障"
    if re.search(r"^(how to|how do|how does)\b", low):
        return "机制"
    if re.search(r"\b(work|works|happen|cause|affect|behaviou?r|produce)\b", low) and \
       re.search(r"^(why|how)\b", low):
        return "机制"
    if re.search(r"\b(before|prior to|ahead of|first)\b", low):
        return "前置条件"
    if re.search(r"\b(verify|confirm|validate|check (if|whether|that))\b", low):
        return "结果验证"
    if re.search(r"^(is|are|can|do|does|should|whether|when to|what to know|why|what|when|where)\b", low) \
       or low.endswith("?"):
        return "相邻意图"
    wc = len([w for w in re.split(r"\s+", a) if w])
    # 完整句子式断言：含连接词、逗号或明显不完整从句
    if wc >= 7 or ("," in a and wc >= 5) or re.search(r"\b(only when|but with|valuable|"
                                                     r"will stay|leaves room|keep(s)? used)\b", low):
        return "主张"
    if re.search(r"^(use|place|position|install|set|adjust|pack|attach|connect|pair|"
                 r"choose a|wear|store|carry|mount)\b", low):
        return "动作"
    if re.search(r"\b(care|maintenance|setup|storing|storage|charging|use|use of)\b", low) and wc >= 2:
        return "动作"
    if wc >= 3 and not re.match(r"^[a-z0-9 ]+$", low):
        return "术语"
    if wc >= 4:
        return "术语"
    if wc <= 3:
        # 1–3 词的纯名词短语多为品类名；无法确认的留待核实
        if re.match(r"^[a-z][a-z0-9 ’'&-]*$", low):
            return "品类"
        return "待核实"
    return "待核实"


def confidence(anchor: str) -> str:
    t = classify(anchor)
    if t in ("噪声", "待核实"):
        return "待核实"
    return "反推"


def load(cat: str) -> list[dict]:
    with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        rs = list(csv.DictReader(f))
    for r in rs:
        for k in ("来源URL", "H1", "H2", "锚文本", "内链URL"):
            r[k] = (r.get(k) or "").strip()
        r["建议类型"] = classify(r["锚文本"]) if r["锚文本"] else ""
    return rs


def esc(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ").strip()


def wc(s: str) -> int:
    return len([w for w in re.split(r"\s+", s.strip()) if w])


MASTER_INTRO = """# 锚文本总规范

本文件是五个栏目共用的锚文本规则：**类型定义**、**词数标准**、**选链规则**。各栏目的 `锚文本规范.md` 只保留本栏目用到的类型子集和实例，不重复这张总表。

## 一、锚文本类型（总表）

类型是从 299 条真实正文锚文本里**按词形与上下文反推**的建议分类；样本只提供锚文本与目标 URL，没有原句上下文，因此类型是**建议值**，不能当作已验证结论。

| 锚文本类型 | 类型定义 | 锚文本单词数 | 词形信号 | 五类中的侧重 |
| --- | --- | --- | --- | --- |
"""

MASTER_TAIL = """
## 二、词数标准（来自 299 条真实锚文本）

- 中位数 **4 词**，均值 4.6 词，范围 **1–16 词**。
- 分布：1 词 12 条、2 词 43 条、3 词 59 条、4 词 63 条、5 词 44 条、6 词 20 条、7 词以上 58 条。
- **主用区间 3–6 词**（占 186/299）。1–2 词多为品类名或型号名，7 词以上多为「主张」类或产品全名。
- 建议：**优先 3–5 词**；需要写清条件时才到 6–8 词；超过 8 词只在「主张」类成立，且要确认它读起来仍像锚文本而不是句子。

## 三、选链规则

1. 先从 `发布与链接记录/已发布文章.csv` 找与当前句子子问题相符、URL 已发布且可访问的 Divoom 页面。
2. 再选精确、自然、长度适中的锚文本；没有合适目标就不强行添加。
3. 正文自然引出了未来应写的文章时，只在 `发布与链接记录/待补内链.csv` 登记锚文本候选、上下文与期望目标；**正文不要留空链接或占位标记**。
4. 目标发布后回访来源文章补链，并回填台账的最终锚文本与目标 URL。
5. **「原始证据」通常是外部引用**，不能为了内链数量硬换成本站文章。

## 四、已核实的格式参考

| 项 | 值 |
| --- | --- |
| 来源文章 | `https://momcozy.com/blogs/babycare/high-weight-limit-too-small-high-chair-fit-check` |
| 原文锚文本 | `correctly routed and adjusted` |
| 实际目标 | `https://momcozy.com/products/momcozy-dinerpal-high-chair?variant=44659101925574` |
| 能说明什么 | 原文正文里确实存在这条链接 |
| 不能说明什么 | 它是否适合作为 Divoom 的「兼容／型号」写法，要看它所在段落的任务，**不能照搬其商业链接策略** |

## 五、竞品链接的使用边界

样本里的 Momcozy／KTC 目标 URL 是**分析样本，不是 Divoom 成稿的内链候选**。Codex 给 Divoom 补内链时只从本地已发布台账取 URL；不存在就登记到待补内链。

口径：**类型不明就留「待核实」，不根据锚文本文字猜类型。**
"""


def master_doc() -> str:
    rows = "\n".join(
        f"| {k} | {TYPES[k][0]} | {TYPES[k][1]} | {TYPES[k][2]} | "
        f"{'定义／解释页' if k in ('术语','专业定义') else '见栏目侧重'} |"
        for k in ORDER)
    return MASTER_INTRO + rows + "\n" + MASTER_TAIL


def cat_doc(cat: str, rows: list[dict]) -> str:
    links = [r for r in rows if r["锚文本"]]
    clean = [r for r in links if not classify(r["锚文本"]).startswith("噪声")]
    used = [t for t in ORDER if any(classify(r["锚文本"]) == t for r in clean)]
    wcs = [wc(r["锚文本"]) for r in clean] or [0]
    med = sorted(wcs)[len(wcs) // 2]
    type_rows = "\n".join(
        f"| {t} | {TYPES[t][0]} | {TYPES[t][1]} | {sum(1 for r in clean if classify(r['锚文本']) == t)} |"
        for t in used)
    # 实例表：每种类型最多 5 条，去重锚文本
    picks, seen = [], set()
    for t in used:
        n = 0
        for r in clean:
            if classify(r["锚文本"]) != t or r["锚文本"].lower() in seen:
                continue
            seen.add(r["锚文本"].lower()); n += 1
            picks.append((t, r))
            if n >= 3:
                break
    pick_rows = "\n".join(
        f"| {t} | `{esc(r['锚文本'])}` | {wc(r['锚文本'])} | `{r['内链URL']}` |"
        for t, r in picks)
    # 附录：完整样本，只列锚文本与目标链接的总览（不建 H2 关系）
    # 附录总览：锚文本 → 锚文本类型 → 目标链接（类型为反推建议值）
    def key(t: str) -> int:
        return ORDER.index(t) if t in ORDER else len(ORDER)
    app_rows, seen_pair = [], set()
    for r in rows:
        if not (r["锚文本"] and r["内链URL"]):
            continue
        pair = (r["锚文本"].lower(), r["内链URL"])
        if pair in seen_pair:               # 同一锚文本指向同一目标只留一行
            continue
        seen_pair.add(pair)
        app_rows.append((classify(r["锚文本"]) or "待核实", r))
    app_rows.sort(key=lambda x: (key(x[0]), x[1]["锚文本"].lower()))
    app = "\n".join(
        f"| `{esc(r['锚文本'])}` | {t} | `{r['内链URL']}` |" for t, r in app_rows)
    n_unique = len(app_rows)
    return f"""---
栏目: {cat}
文件类型: 锚文本规范
状态: 总规范已分离；类型由实例反推（建议值）
---

# {cat}｜锚文本规范

遵循 [[锚文本总规范]]。本栏目共 **{len(rows)} 行样本**，其中 **{len(clean)} 行有正文锚文本**（另有 {len(links)-len(clean)} 行为导航／加购噪声，不作范例）。

## 1. 锚文本总规范（摘要）

1. **类型**：{len(ORDER)} 类，见总表；本栏目实际用到 {len(used)} 类（下表）。
2. **单词数**：全库中位 **4 词**，主用区间 **3–6 词**；本栏目中位 **{med} 词**。
3. **选链**：只用 `../发布与链接记录/已发布文章.csv` 里已发布且可访问的 Divoom URL；没有合适目标就不加，改登记到 `../发布与链接记录/待补内链.csv`。竞品 URL 是分析样本，**不是内链候选**。

## 2. 本栏目锚文本类型

类型是**从实例反推的建议值**：样本只有锚文本与目标 URL，没有原句上下文，类型不明的一律留「待核实」。

| 锚文本类型 | 类型定义 | 单词数 | 本栏目条数 |
| --- | --- | --- | --- |
{type_rows}

## 3. 锚文本对应链接（实例）

每种类型最多列 3 条，仅展示部分 URL；完整样本见文末附录。
「类型」是从词形与目标地址**反推的建议值**（样本无原句上下文），无法确认的归「待核实」。

| 锚文本类型 | 锚文本 | 单词数 | 实例 URL |
| --- | --- | --- | --- |
{pick_rows}

## 附录：本栏目锚文本—链接总览（{n_unique} 条）

三段总览：**锚文本 → 锚文本类型 → 目标链接**。**不建立 H2 对应关系**；无正文内链的 H2 行不出现在本表。
类型与第 3 节同一套反推口径（建议值），按类型集中排列，便于按类型比对写法；同一「锚文本＋目标」组合只留一行。

| 锚文本 | 锚文本类型 | 内链URL |
| --- | --- | --- |
{app}
"""


def main() -> None:
    (LIB / "锚文本总规范.md").write_text(master_doc(), encoding="utf-8")
    print("锚文本总规范.md 已写入")
    for cat in CATS:
        rows = load(cat)
        (LIB / cat / "锚文本规范.md").write_text(cat_doc(cat, rows), encoding="utf-8")
        clean = [r for r in rows if r["锚文本"] and not classify(r["锚文本"]).startswith("噪声")]
        from collections import Counter
        c = Counter(classify(r["锚文本"]) for r in clean)
        print(f"{cat:8} 样本 {len(rows):3} 有效锚文本 {len(clean):3} 类型 {len(c)} 种: "
              + ", ".join(f"{k}×{v}" for k, v in c.most_common()))


if __name__ == "__main__":
    main()
