#!/usr/bin/env python3
"""补抓两篇仍缺失的正文（按文件名索引在栏目 CSV 里的位置取 URL）。"""
from __future__ import annotations
import csv, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))
from fetch_bodies import S, DST  # noqa: E402

TARGETS = [("购买指南", "06-bottle-warmer-compatibility-widths-shapes-silicone-fit-guide.md"),
           ("设置与使用", "07-using-swing-bouncer-together.md")]

ok = fail = 0
for cat, fname in TARGETS:
    with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        urls = sorted({r["来源URL"].strip() for r in csv.DictReader(f)})
    n = int(fname.split("-", 1)[0])
    u = urls[n - 1]
    dest = DST / cat / fname
    got = None
    for attempt in range(4):
        p = subprocess.run(["fcrawl", u], capture_output=True, text=True, timeout=300)
        md = (p.stdout or "").strip()
        if p.returncode == 0 and len(md) > 1500:
            got = md
            break
        print(f"  retry{attempt+1} rc={p.returncode} len={len(md)} {u}", flush=True)
        time.sleep(5 + 5 * attempt)
    if got:
        dest.write_text(f"<!-- 来源URL: {u} -->\n<!-- 抓取方式: fcrawl -->\n\n{got}\n", encoding="utf-8")
        ok += 1
        print(f"ok {len(got)//1000}K {dest.name}", flush=True)
    else:
        fail += 1
        print(f"FAIL {u}", flush=True)
print(f"完成 ok={ok} fail={fail}")
