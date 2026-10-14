#!/usr/bin/env python3
"""每个栏目生成一份「实例正文.md」：汇总表 + 每篇实例的完整正文（md，含图片链接）。
与 实例数据表.csv 同源；正文取自 work/bodies/<栏目>/*.md。"""
from __future__ import annotations
import csv, pathlib, re

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
BODIES = ROOT / "work" / "bodies"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]


def anchor(i: str) -> str:
    return "实例" + re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", i)


def read_notes(cat: str):
    """从实例笔记读取：实例ID / FX编号 / 标题 / 实例URL / 正文。"""
    import json, re
    out = []
    for f in sorted((LIB / cat / "实例").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", t, re.S)
        props = {}
        for line in m.group(1).split("\n"):
            if line.strip():
                k, v = line.split(":", 1)
                props[k] = json.loads(v.strip())
        body = t[m.end():].strip()
        out.append((props, body))
    return out


def main() -> None:
    for cat in CATS:
        notes = read_notes(cat)
        parts = [f"""---
栏目: {cat}
文件类型: 实例汇总
状态: 由 build_instance_views.py 从 实例/*.md 生成
---

# {cat}｜实例汇总

本栏目共 **{len(notes)} 篇实例文章**（竞品样本，仅作结构参考）。每篇含来源 URL、FX 编号与正文（markdown，图片保留原始链接）。

- 表格视图见同目录 `实例.base`；单篇见 `实例/`
- FX 编号取自本栏目 `标题与大纲规范.md` 的 FX 主表；「待归类」表示未出现在 FX 主表的原题样本里
- **竞品正文不得写进 Divoom 成稿**（产品事实、医疗建议、目标链接都不能照搬）

## 汇总

| 实例ID | FX编号 | 标题 | 来源 URL |
| --- | --- | --- | --- |"""]
        for p, _b in notes:
            ttl = p['标题'].replace('|', '\\|')
            parts.append(f"| {p['实例ID']} | {p['FX编号']} | {ttl} | `{p['实例URL']}` |")
        for p, body in notes:
            parts += ["", "---", "",
                      f"## {p['实例ID']}　{p['标题']}", "",
                      f"- FX 编号：**{p['FX编号']}**",
                      f"- 来源 URL：`{p['实例URL']}`",
                      f"- 图片数：{p.get('图片数', 0)}　·　正文字数：{p.get('正文字数', 0)}", ""]
            parts += [body.split("\n", 1)[1].strip() if body.startswith("#") else body, ""]
        out = LIB / cat / "实例汇总.md"
        out.write_text("\n".join(parts), encoding="utf-8")
        (LIB / cat / "实例正文.md").unlink(missing_ok=True)     # 旧名清理
        print(f"{cat:8} 汇总 {len(notes):2} 篇 -> {out.name} {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
