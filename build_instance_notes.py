#!/usr/bin/env python3
"""把实例数据做成 Obsidian 原生格式：一篇实例 = 一篇笔记（frontmatter 属性 + 正文）。

输出（每个栏目）：
  实例/<序号>-<slug>.md   每篇实例：frontmatter 带 栏目/FX编号/实例URL/标题/图片数，正文是完整 markdown
  实例.base                Bases 表格视图，列出本栏目全部实例的属性
不产生任何 CSV。
"""
from __future__ import annotations
import csv, json, pathlib, re

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
BODIES = ROOT / "work" / "bodies"
S = ROOT / "work" / "samples" / "五类CSV"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]
PREFIX = {"科技与信息": "科技", "帮助与提示": "帮助", "产品对比": "对比",
          "购买指南": "购买", "设置与使用": "设置"}


def slug(u: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", u.rsplit("/", 1)[-1].lower()).strip("-")[:60]


def j(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def fx_map() -> dict[str, str]:
    """实例 URL -> FX 编号，取自各栏目「标题与大纲规范.md」FX 主表的原题样本链接。"""
    out = {}
    for cat in CATS:
        t = (LIB / cat / "标题与大纲规范.md").read_text(encoding="utf-8")
        sec = t[t.index("## 一、FX 主表"): t.index("## 二、")]
        for line in sec.splitlines():
            m = re.search(r"\*\*\s*([A-Z]{1,2}\d+)\b", line)   # 允许 ** 内嵌套括号说明
            u = re.search(r"\((https?://[^)]+)\)", line)
            if m and u:
                out.setdefault(u.group(1), m.group(1))
    return out


def main() -> None:
    fxm = fx_map()
    for cat in CATS:
        # 标题：优先取样本 CSV，缺失时用正文首个 H1
        titles = {}
        if (S / f"{cat}.csv").exists():
            with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    if (r.get("来源URL") or "").strip() and (r.get("H1") or "").strip():
                        titles.setdefault(r["来源URL"].strip(), r["H1"].strip())
        # H1 补丁：正文容器不含 H1，缺标题的文章从 work/h1-map.json 取
        h1map = {}
        hm = ROOT / "work" / "h1-map.json"
        if hm.exists():
            h1map = json.loads(hm.read_text(encoding="utf-8"))
        for u, t in h1map.items():
            if t:
                titles.setdefault(u, t)
        # URL 列表与正文：以 work/bodies/<栏目>/ 为准（正文注释里带来源 URL），
        # 这样扩样后新增的文章自动并入，不依赖样本 CSV 是否更新。
        d = LIB / cat / "实例"
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.md"):
            old.unlink()
        ent = []
        for bf in sorted((BODIES / cat).glob("*.md")):
            t = bf.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"<!--\s*来源URL:\s*(\S+?)\s*-->", t)
            if not m:
                continue
            u = m.group(1)
            body = re.sub(r"^<!--.*?-->\s*", "", t, flags=re.S).strip()
            if not titles.get(u):
                h = re.search(r"^#\s+(.+)$", body, re.M)
                titles[u] = h.group(1).strip() if h else ""
            ent.append((u, slug(u), body))
        urls = sorted({u for u, _s, _b in ent})
        made = 0
        for n, u in enumerate(urls, 1):
            title = titles.get(u, "")
            body = next((b for uu, _s, b in ent if uu == u), "")
            f = BODIES / cat / f"{n:02d}-{slug(u)}.md"
            imgs = body.count("![")
            iid = f"{PREFIX[cat]}-{n:02d}"
            name = f"{n:02d}-{slug(u)}.md"
            fm = ["---", f"实例ID: {j(iid)}", f"栏目: {j(cat)}",
                  f"FX编号: {j(fxm.get(u, '待归类'))}", f"标题: {j(title)}",
                  f"实例URL: {j(u)}", f"来源站点: {j('KTC' if 'ktcplay' in u else 'Momcozy')}",
                  f"图片数: {imgs}", f"正文字数: {len(body)}",
                  # 正文同时写进属性，供 Bases 表格直接取出，与笔记正文一一对应
                  "正文: " + json.dumps(body, ensure_ascii=False), "---"]
            (d / name).write_text("\n".join(fm) + f"\n\n# {title or '（标题缺失）'}\n\n"
                                  f"> 来源：<{u}>　·　FX 编号：**{fxm.get(u, '待归类')}**　·　竞品样本，仅作结构参考\n\n"
                                  + (body or "（正文未抓到）") + "\n", encoding="utf-8")
            made += 1
        base = ["properties:", "  栏目:", "    displayName: 栏目",
                "  FX编号:", "    displayName: FX 编号",
                "  标题:", "    displayName: 标题",
                "  实例URL:", "    displayName: 实例 URL",
                "  来源站点:", "    displayName: 来源",
                "  图片数:", "    displayName: 图片",
                "  正文字数:", "    displayName: 正文字数",
                "  正文:", "    displayName: 正文（全文属性）",
                "  formula.正文摘要:", "    displayName: 正文摘要",
                "formulas:", '  正文摘要: \'正文.slice(0, 220) + "…"\'',
                "views:", "  - type: table", f"    name: {cat}实例",
                "    filters:", "      and:",
                f"        - 'file.inFolder(\"{cat}/实例\")'",
                "    order:", "      - FX编号", "      - 标题", "      - 来源站点",
                "      - 图片数", "      - 正文字数", "      - formula.正文摘要"]
        (LIB / cat / "实例.base").write_text("\n".join(base) + "\n", encoding="utf-8")
        print(f"{cat:8} 实例笔记 {made:2} 篇 + 实例.base")


if __name__ == "__main__":
    main()
