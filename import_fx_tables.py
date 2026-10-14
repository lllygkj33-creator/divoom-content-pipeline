#!/usr/bin/env python3
"""把《标题公式与 H2 逻辑合并表》导入五份 标题与大纲规范.md。

结构（每个栏目一份）：
  一、FX 主表        —— 59 类完整 FX（+1 候选），逐字迁移公式/H2 箭头/状态
  二、正文结构抽样   —— 上一轮 29 篇的 H1→H2 补充观察
  三、单篇使用与检查 —— 路由与限定词检查清单
样本状态列原样保留；推演/未核实/跨栏目的行不得当作已验证写法。
"""
from __future__ import annotations
import pathlib, sys

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "fx"))
import data as D          # noqa: E402
import data2 as D2        # noqa: E402

LIB = ROOT / "Divoom 内容资料库"

CATS = {
 "科技与信息": (D.INFO,  D2.INFO_OBS,    "F",  "F1–F14",  "Technology Hub"),
 "帮助与提示": (D.SUPPORT, D2.SUPPORT_OBS, "S",  "S1–S12",  "Support & Tips"),
 "产品对比":   (D.COMPARE, D2.COMPARE_OBS, "PC", "PC1–PC10", "Product Comparisons"),
 "购买指南":   (D.BUYING,  D2.BUYING_OBS,  "BG", "BG1–BG11", "Buying Guides"),
 "设置与使用": (D.SETUP,   D2.SETUP_OBS,   "SU", "SU1–SU13", "Desk Setups"),
}
DELIVER = {
 "科技与信息": "读完这一篇，用户要能解释根因、机制与边界。",
 "帮助与提示": "读完这一篇，用户要能恢复故障、确认是否修好。",
 "产品对比": "读完这一篇，用户要能在同一比较轴上选出条件赢家。",
 "购买指南": "读完这一篇，用户要能做出购买判断（允许得出「不需要买」）。",
 "设置与使用": "读完这一篇，用户要能完成现场配置并验收。",
}
SPACE_NOTE = {
 "科技与信息": "信息类用 `F1–F14`；设置与使用用 `SU1–SU13`。两者**不是**同一命名空间，引用时必须带栏目路径。",
 "设置与使用": "设置与使用用 `SU1–SU13`；信息类用 `F1–F14`。两者**不是**同一命名空间，引用时必须带栏目路径。",
}
DEFAULT_SPACE = ("信息类用 `F1–F14`；设置与使用用 `SU1–SU13`。两者**不是**同一命名空间，"
                 "引用时必须带栏目路径（例如本栏目 `{p}3` 与另一命名空间的 `F3` 是两条不同规则）。")


def esc(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ").strip()


def fx_table(rows, pref: str) -> str:
    out = ["| FX／意图 | 原题样本（能核实才给链接） | 可迁移 H1 公式 | H2 箭头逻辑 | 样本与逻辑状态 |",
           "| --- | --- | --- | --- | --- |"]
    for r in rows:
        if pref == "SU":                      # setup rows carry an extra 命名空间备注
            name, note, sample, formula, arrow, status = r
            label = f"**{esc(name)}**" + (f"（{esc(note)}）" if note else "")
        else:
            name, sample, formula, arrow, status = r
            label = f"**{esc(name)}**"
        out.append(f"| {label} | {esc(sample)} | {esc(formula)} | {esc(arrow)} | {esc(status)} |")
    return "\n".join(out)


def obs_table(rows) -> str:
    out = ["| 原文样本 | 补充 H1 公式 | 样本 H2 的中文归纳 | H1→H2 检查点 |",
           "| --- | --- | --- | --- |"]
    for sample, formula, h2, chk in rows:
        out.append(f"| {esc(sample)} | {esc(formula)} | {esc(h2)} | {esc(chk)} |")
    return "\n".join(out)


def doc(cat: str, fx, obs, pref, rng, ktc) -> str:
    space = SPACE_NOTE.get(cat) or DEFAULT_SPACE.format(p=pref)
    checks = "\n".join(f"{i}. {c}" for i, c in enumerate(D2.CHECKS, 1))
    return f"""---
栏目: {cat}
文件类型: 标题与大纲规范
状态: FX 主表 + 结构抽样已导入
---

# {cat}｜标题与大纲规范

**本栏目的交付结果：** {DELIVER[cat]}

**FX 覆盖：** {rng}（共 {len(fx)} 行）。KTC 对应栏目：{ktc}。

**代入规则：** {D.SUBST}

**命名空间提醒：** {space}

## 一、FX 主表

本表是把「{len(fx)} 条完整 FX 对照」与「{len(obs)} 篇结构抽样」合并后的主表；后者另见第二节。
**`样本与逻辑状态` 列原样保留**：标注「推演」「正文未核实」「跨栏目」「截图候选」的行只作候选结构，不得对外声称是已验证写法。

{fx_table(fx, pref)}

## 二、正文结构抽样（H1→H2 补充观察）

{len(obs)} 篇逐篇读正文形成的补充表，保留不同样本和对 H1 限定词的检查。H2 列是中文归纳，**不是原文逐字 H2**；已删去 H3 内容。
与第一节 FX 主表重复的文章用于交叉检查，**不重复计数**。部分原文混入购买、排障或操作段，迁移时以本篇的主意图为准。

{obs_table(obs)}

## 三、单篇使用与检查

{checks}
"""


def main() -> None:
    for cat, (fx, obs, pref, rng, ktc) in CATS.items():
        f = LIB / cat / "标题与大纲规范.md"
        f.write_text(doc(cat, fx, obs, pref, rng, ktc), encoding="utf-8")
        print(f"{cat:8} FX {len(fx):2} 行 + 抽样 {len(obs)} 行 -> {f.name}")


if __name__ == "__main__":
    main()
