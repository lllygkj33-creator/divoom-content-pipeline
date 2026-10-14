#!/usr/bin/env python3
"""为五个栏目各建一份实例数据表，记录：实例 URL → FX 编号 → 正文（markdown/html，含图片）。

CSV 的单元格无法承载带图片的 markdown，因此：
  <栏目>/实例数据表.csv   索引：实例ID,实例URL,FX编号,标题,正文文件
  work/bodies/<栏目>/*.md  正文本身（fetch_bodies.py 抓取，含图片链接）
Codex 先查 CSV 找到 FX 与正文文件，再读正文。
"""
from __future__ import annotations
import csv, pathlib, re, sys

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "fx"))
import data as D          # noqa: E402
import data2 as D2        # noqa: E402

LIB = ROOT / "Divoom 内容资料库"
S = ROOT / "work" / "samples" / "五类CSV"
BODIES = ROOT / "work" / "bodies"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]


def fx_map(cat: str) -> dict[str, str]:
    """实例 URL -> FX 编号，取自 FX 主表的「原题样本」链接。"""
    out: dict[str, str] = {}
    tables = {"科技与信息": D.INFO, "帮助与提示": D.SUPPORT, "产品对比": D.COMPARE,
              "购买指南": D.BUYING, "设置与使用": D.SETUP}
    for r in tables[cat]:
        code = re.match(r"[A-Z]+\d+", r[0].split()[0])
        m = next((re.search(r"\((https?://[^)]+)\)", x) for x in r if isinstance(x, str)
                  and re.search(r"\((https?://[^)]+)\)", x)), None)
        if code and m:
            out.setdefault(m.group(1), code.group(0))
    return out


def main() -> None:
    for cat in CATS:
        with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        fx = fx_map(cat)
        urls = sorted({(r["来源URL"] or "").strip() for r in rows if (r["来源URL"] or "").strip()})
        body_dir = BODIES / cat
        files = {f.name.split("-", 1)[1][:-3]: f for f in sorted(body_dir.glob("*.md"))} if body_dir.exists() else {}
        idx = []
        for n, u in enumerate(urls, 1):
            title = next((r["H1"] for r in rows if r["来源URL"].strip() == u and r["H1"].strip()), "")
            slug = re.sub(r"[^a-z0-9]+", "-", u.rsplit("/", 1)[-1].lower()).strip("-")[:60]
            f = next((v for k, v in files.items() if k == slug), None)
            idx.append([f"{cat[:2]}-{n:02d}", u, fx.get(u, "待归类"), title,
                        f.name if f else "（正文未抓到）"])
        out = LIB / cat / "实例数据表.csv"
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["实例ID", "实例URL", "FX编号", "标题", "正文文件"])
            w.writerows(idx)
        have = sum(1 for r in idx if r[2] != "待归类")
        body = sum(1 for r in idx if not r[4].startswith("（"))
        print(f"{cat:8} 实例 {len(idx):2} | 有 FX 编号 {have:2} | 有正文 {body:2} -> {out.name}")


if __name__ == "__main__":
    main()
