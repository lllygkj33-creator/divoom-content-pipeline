#!/usr/bin/env python3
"""补齐正文：对 curl 被 429 拦下的文章改用 fcrawl（浏览器路径）。
只处理 work/bodies/<栏目>/ 里尚缺的文件；fcrawl 结果经同一套 HTML->MD 转换。"""
from __future__ import annotations
import csv, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))
from fetch_bodies import CATS, S, DST, to_md, slug, body_html   # noqa: E402


def main() -> None:
    todo = []
    for cat in CATS:
        with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
            urls = sorted({r["来源URL"].strip() for r in csv.DictReader(f)})
        d = DST / cat
        d.mkdir(parents=True, exist_ok=True)
        for n, u in enumerate(urls, 1):
            dest = d / f"{n:02d}-{slug(u)}.md"
            if dest.exists() and dest.stat().st_size > 700:
                continue
            todo.append((cat, n, u, dest))
    print(f"待补 {len(todo)} 篇（fcrawl）", flush=True)
    ok = fail = 0
    for i, (cat, n, u, dest) in enumerate(todo, 1):
        got = None
        for attempt in range(3):
            p = subprocess.run(["fcrawl", u], capture_output=True, text=True, timeout=300)
            md = (p.stdout or "").strip()
            if p.returncode == 0 and len(md) > 1200:
                got = md
                break
            time.sleep(4 + 4 * attempt)
        if got:
            dest.write_text(f"<!-- 来源URL: {u} -->\n<!-- 抓取方式: fcrawl -->\n\n{got}\n", encoding="utf-8")
            ok += 1
            print(f"[{i}/{len(todo)}] ok {len(got)//1000}K {cat} {u}", flush=True)
        else:
            fail += 1
            print(f"[{i}/{len(todo)}] FAIL {cat} {u}", flush=True)
        time.sleep(1.0)
    print(f"\n完成 ok={ok} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
