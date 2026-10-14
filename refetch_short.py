#!/usr/bin/env python3
"""重抓被误截断的 fcrawl 正文（work/refetch.txt 列出），覆盖 work/bodies 对应文件。"""
from __future__ import annotations
import csv, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))
from fetch_bodies import CATS, S, DST, slug, body_html, to_md   # noqa: E402

want = [l.strip() for l in (ROOT / "work" / "refetch.txt").read_text().split("\n") if l.strip()]
todo = []
for item in want:
    cat, fname = item.split("/", 1)
    with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        urls = sorted({r["来源URL"].strip() for r in csv.DictReader(f)})
    n = int(fname.split("-", 1)[0])
    todo.append((cat, urls[n - 1], DST / cat / fname))

print(f"重抓 {len(todo)} 篇", flush=True)
ok = fail = 0
for i, (cat, u, dest) in enumerate(todo, 1):
    got = None
    for attempt in range(3):
        p = subprocess.run(["fcrawl", u], capture_output=True, text=True, timeout=300)
        md = (p.stdout or "").strip()
        if p.returncode == 0 and len(md) > 1500:
            got = md
            break
        time.sleep(4 + 4 * attempt)
    if got:
        dest.write_text(f"<!-- 来源URL: {u} -->\n<!-- 抓取方式: fcrawl -->\n\n{got}\n", encoding="utf-8")
        ok += 1
        print(f"[{i}/{len(todo)}] ok {len(got)//1000}K {dest.name}", flush=True)
    else:
        fail += 1
        print(f"[{i}/{len(todo)}] FAIL {dest.name}", flush=True)
    time.sleep(1.0)
print(f"\n完成 ok={ok} fail={fail}", flush=True)
