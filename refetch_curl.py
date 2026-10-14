#!/usr/bin/env python3
"""把 fcrawl 抓来的正文改用 curl + 容器抽取重抓（fcrawl 会带回整页导航）。
只处理 work/bodies 里带「抓取方式: fcrawl」标记的文件；带缓存的优先用缓存。"""
from __future__ import annotations
import csv, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))
from fetch_bodies import S, DST, slug, body_html, to_md, get   # noqa: E402

CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]
todo = []
for cat in CATS:
    with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
        urls = sorted({r["来源URL"].strip() for r in csv.DictReader(f)})
    for f in sorted((DST / cat).glob("*.md")):
        if "抓取方式: fcrawl" not in f.read_text(encoding="utf-8"):
            continue
        n = int(f.name.split("-", 1)[0])
        todo.append((cat, urls[n - 1], f))
print(f"待重抓 {len(todo)} 篇（curl）", flush=True)
ok = fail = 0
for i, (cat, u, dest) in enumerate(todo, 1):
    doc = None
    for attempt in range(3):
        doc = get(u)
        if doc: break
        time.sleep(3 + 3 * attempt)
    if not doc:
        fail += 1; print(f"[{i}/{len(todo)}] FAIL(fetch) {dest.name}", flush=True); continue
    md, imgs = to_md(body_html(doc))
    if len(md) < 800:
        fail += 1; print(f"[{i}/{len(todo)}] FAIL(empty {len(md)}) {dest.name}", flush=True); continue
    dest.write_text(f"<!-- 来源URL: {u} -->\n\n{md}\n", encoding="utf-8")
    ok += 1
    print(f"[{i}/{len(todo)}] ok {len(md)//1000}K {dest.name}", flush=True)
    time.sleep(1.0)
print(f"\n完成 ok={ok} fail={fail}", flush=True)
