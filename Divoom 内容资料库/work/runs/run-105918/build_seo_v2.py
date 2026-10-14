#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run-105918 第 2 轮 SEO：在 01-draft-v2.json 的正文上就地插入已核实内链，写 03-seo-v2.json。
不覆盖 03-seo.json；不改 html（保持无链接版）。"""
import json, re, pathlib

RUN = pathlib.Path(__file__).resolve().parent
draft = json.loads((RUN / "01-draft-v2.json").read_text(encoding="utf-8"))
body = draft["body_markdown"]

# (锚文本, URL, h2, 类型, verified)
LINKS = [
    ("pixel-art canvas range", "https://divoom.com/blogs/pixel-art/pixel-art-canvas-size-guide",
     "The Canvas Is Big Enough, and That Is Not a Statement About a Single Letter", "相邻意图"),
    ("published tiny-font experiments", "https://divoom.com/blogs/setup-ideas/how-to-design-pixel-art-font-divoom-displays",
     "How Many Pixels Does One Recognizable Letter Need?", "相邻意图"),
    ("Readability at a desk", "https://divoom.com/blogs/desk-setup/pixel-display-viewing-distance-guide",
     "Why More Pixels on the Panel Does Not Mean More Pixels in the Letter", "术语"),
    ("the scrolling-text capability", "https://divoom.com/blogs/app-guide/keep-scrolling-text-readable-pixel-display",
     "Which Variable Is Actually Doing the Work", "术语"),
    ("specifications vary by model", "https://divoom.com/blogs/product-compare/divoom-product-specs-that-matter-most-smart-display",
     "Where This Explanation Stops", "兼容与规格"),
]

out_body = body
internal = []
for anchor, url, h2, typ in LINKS:
    hits = out_body.count(anchor)
    assert hits == 1, f"anchor {anchor!r} count={hits}"
    assert f"[{anchor}]" not in out_body
    out_body = out_body.replace(anchor, f"[{anchor}]({url})", 1)
    internal.append({"anchor": anchor, "url": url, "h2": h2, "type": typ, "verified": 200})

assert draft["html"] and "](" not in draft["html"]

# 外链锚文本必须与内链锚文本不同（同一句相邻位置，避免同一词组两个目标）
for _a, _u, _h, _t in LINKS:
    assert _u != "https://moonbench.xyz/projects/tiny-pixel-art-fonts/"
_ext_anchor = "on one-bit letterforms"
assert out_body.count(_ext_anchor) == 1, out_body.count(_ext_anchor)
out_body = out_body.replace(_ext_anchor, f"[{_ext_anchor}](https://moonbench.xyz/projects/tiny-pixel-art-fonts/)", 1)

external = [{
    "anchor": _ext_anchor,
    "url": "https://moonbench.xyz/projects/tiny-pixel-art-fonts/",
    "why": "该页逐尺寸枚举 1-bit 字形空间（2×2 与 3×2 均太小、3×3 需挑字形、3×4 出现取舍、3×5「Quite Clear」、5×5 让 M/W/G/B 不再歧义），逐句支撑正文的像素预算阶梯；已实测 HTTP 200，是文章本体而非搜索摘要页。",
}]

pending = [
    {"anchor_candidate": "character-pair legibility test",
     "topic": "桌面像素屏上的字对辨识自测（O/0、S/5、G/6、B/8 的临界距离）",
     "h2": "How to Test It on Your Own Desk",
     "reason": "正文「Pick the most easily confused character pairs」处是天然待补链位；台账 256 篇无「可读性字对自测」类文章，最近的 keep-scrolling-text-readable-pixel-display 只讲字重/速度/对比/长度四变量，不覆盖字对临界距离测试，故只登记不插链。"},
    {"anchor_candidate": "garbled glyph troubleshooting",
     "topic": "像素屏字形错乱/渲染异常的单机排查（区别于本解释覆盖的可读性限制）",
     "h2": "Where This Explanation Stops",
     "reason": "正文「if a glyph is garbled rather than merely dotty」处是天然待补链位；台账 troubleshooting 仅覆盖设备连接与离线模式，无「字形错乱/渲染异常」排查目标，故只登记不插链。"},
]

out = dict(draft)
out.update({
    "title": "Why a 64×64 Pixel Canvas Still Fails at Small Text on a Desk",
    "meta_description": "A 64×64 grid packs 4,096 points, but that total is shared canvas-wide. See why per-letter budget, 1-bit pixels and desk viewing distance keep small text dotty.",
    "summary": "A 64×64 pixel canvas can still make small text hard to read because canvas capacity and per-character allocation are different budgets. The grid holds 4,096 points, but one legible glyph needs roughly 3×5 to 5×5 of them, and each point is only on or off, so no antialiasing softens a stroke. At desk distance the eye resolves the emitter grid itself, so letterforms break into dots. The limit is a content decision, not a setting: clocks, icons and short scrolling messages work, paragraphs do not.",
    "slug": "why-a-64x64-pixel-art-canvas-can-still-make-small-text-hard-to-read-on-a-desk-display",
    "url": "",
    "body_markdown": out_body,
    "internal_links": internal,
    "external_links": external,
    "pending_links": pending,
    "revision_notes": [
        "链接按 01-draft-v2.json 的新正文重新定位：上一轮 5 条内链中 4 条语义仍相符（画布档位 / 像素字体设计 / 观看距离 / 滚动文字）予以保留，1 条（no official minimum font size → product-specs-that-matter-most-smart-display）因所挂段落改写而改锚为「specifications vary by model」，类型由「相邻意图」改为「兼容与规格」；本轮重新实测定位，未沿用旧锚点。",
        "内链数量仍为 5 条；每条只用 curl 实测 HTTP 200 后采用（结果写入 internal_links[].verified）。无非 200 目标被降级到 pending_links。",
        "外部链接 1 条（moonbench tiny-pixel-art-fonts，HTTP 200）逐句支撑「2×2/3×2 不足 → 3×3、3×4 需取舍 → 3×5 fairly clear → 5×5 分辨 M/W」这一阶梯；锚文本取「on one-bit letterforms」，与同句内链锚文本「published tiny-font experiments」相邻但不重叠。",
        "pending_links 2 条与上一轮相同（已在 待补内链.md 登记，未重复登记）；正文无空链、无占位符、无 pending URL。",
        "html 字段保持 01-draft-v2.json 的无链接版，未编辑；GEO/编排器须由本卡 body_markdown 重建带链 HTML。",
    ],
})

(RUN / "03-seo-v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# ---- 自检 ----
print("title chars:", len(out["title"]))
print("meta chars:", len(out["meta_description"]))
print("summary words:", len(out["summary"].split()))
print("slug:", out["slug"])
print("md internal links:", len(re.findall(r"\]\(https://divoom\.com/", out_body)))
print("md external links:", len(re.findall(r"\]\(https://(?!divoom\.com)", out_body)))
for it in internal:
    assert out_body.count(it["url"]) == 1, it
print("inherited keys ok:", all(k in out for k in draft))
print("html unchanged:", out["html"] == draft["html"])
print("pending not in body:", all(p["anchor_candidate"] not in out_body for p in pending))
print("H2 set unchanged:", [l for l in out_body.splitlines() if l.startswith("## ")] == [l for l in body.splitlines() if l.startswith("## ")])
strip = lambda s: re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
print("text unchanged after link strip:", strip(out_body) == body)
