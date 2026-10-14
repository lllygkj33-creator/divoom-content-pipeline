#!/usr/bin/env python3
"""从 divoom.com 官方 blog sitemap 生成 `发布与链接记录/已发布文章.md` 台账。

只做一件事：把「官方已发布、可访问」的文章 URL 记下来，供后续补内链时查表。
标题由 URL slug 推导（未逐页核对 H1），发布时间 sitemap 未提供，留 `待补`。
"""
from __future__ import annotations
import pathlib, re, subprocess, sys, urllib.parse

SITEMAP = "https://divoom.com/sitemap_blogs_1.xml"
ROOT = pathlib.Path(__file__).parent
DST = ROOT / "Divoom 内容资料库" / "发布与链接记录" / "已发布文章.md"

SMALL = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}


def fetch(url: str) -> str:
    p = subprocess.run(["curl", "-sS", "-L", "--max-time", "30", "--compressed",
                        "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36",
                        url], capture_output=True, text=True)
    if p.returncode != 0 or "<loc>" not in p.stdout:
        sys.exit(f"抓取 sitemap 失败: {url}")
    return p.stdout


def title_of(slug: str) -> str:
    words = [w for w in slug.split("-") if w]
    out = []
    for i, w in enumerate(words):
        out.append(w if (i and w.lower() in SMALL) else w[:1].upper() + w[1:])
    t = " ".join(out)
    return t[:1].upper() + t[1:]


def main() -> None:
    xml = fetch(SITEMAP)
    entries = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>(?:\s*<lastmod>\s*([^<\s]+)\s*</lastmod>)?", xml)
    arts = []
    for loc, lastmod in entries:
        m = re.match(r"^https://divoom\.com/blogs/([^/]+)/([^/?#]+)$", loc)
        if not m:
            continue                      # 只收文章页，跳过 /blogs/<分类> 索引页
        cat, slug = m.group(1), urllib.parse.unquote(m.group(2))
        arts.append((cat, slug, loc, (lastmod or "")[:10]))
    arts.sort(key=lambda r: (r[0], r[1]))
    print(f"收录 {len(arts)} 篇官方已发布文章（来自 {len(set(a[0] for a in arts))} 个官方分类）")

    rows = []
    for i, (cat, slug, url, lastmod) in enumerate(arts, 1):
        rows.append(f"| D{i:03d} | {cat} | 待归类 | {title_of(slug)} | {url} | 待补 | {lastmod or '待补'} | 已发布 |")

    DST.write_text(
        "---\n"
        "文件类型: 发布台账\n"
        "状态: 已由官方 sitemap 回填\n"
        "来源: https://divoom.com/sitemap_blogs_1.xml\n"
        f"文章数: {len(arts)}\n"
        "---\n\n"
        "# 已发布文章\n\n"
        f"一行一篇 Divoom 已发布文章。本表由 `build_published_ledger.py` 从官方 sitemap 自动生成，共 **{len(arts)}** 篇。\n"
        "补内链时**只从本表找真实已发布且可访问的 Divoom URL**。\n\n"
        "> 说明：`标题` 由 URL slug 推导，**未逐页核对 H1**；`发布时间` 官方 sitemap 未提供，留 `待补`；\n"
        "> `栏目` 用的是 **Divoom 官方博客分类**，不是本库的五栏目分类法，`FX编号` 因此统一留 `待归类`。\n\n"
        "| 文章编号 | 栏目 | FX编号 | 标题 | 发布URL | 发布时间 | 更新时间 | 状态 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n",
        encoding="utf-8")
    print(f"已写出 {DST}")


if __name__ == "__main__":
    main()
