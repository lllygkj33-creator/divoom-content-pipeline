#!/usr/bin/env python3
"""HTML 同步闸门：由 `body_markdown` 确定性重建带链正文 HTML。

流程契约第三节半要求：SEO 只改 body_markdown，不改 html；编排器在交给 GEO 前
必须用本脚本从 SEO 稿的 body_markdown 重建 HTML，否则 GEO 会拿到无链接的旧 html。

确定性：纯函数，无时间戳、无随机、无外部依赖（只用标准库）。
支持子集：H1–H4、段落、无序/有序列表、表格、引用、`[文本](链接)`、`**粗体**`、`*斜体*`。

用法：
    python3 html_sync.py <body.md> [-o out.html]   # 不给 -o 则打印到 stdout
    python3 html_sync.py --selftest
"""
from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
ULI = re.compile(r"^[-*+]\s+(.*)$")
OLI = re.compile(r"^\d+[.)]\s+(.*)$")
TSEP = re.compile(r"^\|[\s:|-]+\|$")


def _esc(s: str) -> str:
    return html.escape(s, quote=False)


def _attr(s: str) -> str:
    return html.escape(s, quote=True)


def inline(s: str) -> str:
    """行内标记。先切出链接再转义文字，避免 URL 里的 & 被二次转义。"""
    out, pos = [], 0
    for m in LINK.finditer(s):
        out.append(_esc(s[pos:m.start()]))
        out.append(f'<a href="{_attr(m.group(2))}">{_esc(m.group(1))}</a>')
        pos = m.end()
    out.append(_esc(s[pos:]))
    t = "".join(out)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _aligns(sep: str) -> list[str]:
    out = []
    for c in _cells(sep):
        c = c.strip()
        out.append("center" if c.startswith(":") and c.endswith(":")
                   else "right" if c.endswith(":")
                   else "left" if c.startswith(":")
                   else "")
    return out


def _table(rows: list[str]) -> str:
    head, align, body = _cells(rows[0]), _aligns(rows[1]), [_cells(r) for r in rows[2:]]
    align += [""] * (len(head) - len(align))

    def cell(tag: str, txt: str, a: str) -> str:
        style = f" style='text-align:{a}'" if a else ""
        return f"<{tag}{style}>{inline(txt)}</{tag}>"

    th = "".join(cell("th", t, a) for t, a in zip(head, align))
    trs = "".join(
        "<tr>" + "".join(cell("td", t, a) for t, a in zip(r + [""] * len(align), align)) + "</tr>"
        for r in body
    )
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def _is_block(s: str) -> bool:
    return bool(s) and (s[0] in "#|>" or HEAD.match(s) or ULI.match(s) or OLI.match(s))


def to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        m = HEAD.match(s)
        if m:
            lv = len(m.group(1))
            blocks.append(f"<h{lv}>{inline(m.group(2).strip())}</h{lv}>")
            i += 1
            continue

        if s.startswith("|") and i + 1 < n and TSEP.match(lines[i + 1].strip()):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            blocks.append(_table(rows))
            continue

        ordered = bool(OLI.match(s))
        if ordered or ULI.match(s):
            pat = OLI if ordered else ULI
            items = []
            while i < n:
                mm = pat.match(lines[i].strip())
                if not mm:
                    break
                items.append(f"<li>{inline(mm.group(1))}</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            blocks.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            continue

        para = []
        while i < n and lines[i].strip() and not _is_block(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        blocks.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(blocks)


TAG = re.compile(r"<[^>]+>")
# 行内标签直接删除；只有块级标签才当分隔符补空格，否则 `粗体</strong>。` 会变成 `粗体 。`
INLINE_TAG = re.compile(r"</?(?:strong|em|b|i|a|span|code|sub|sup)(?:\s[^>]*)?>", re.I)


def visible_text(fragment: str) -> str:
    """剥标签取可见文字，用于「重建前后可见文字不变」校验。"""
    t = TAG.sub(" ", INLINE_TAG.sub("", fragment))
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def md_visible_text(md: str) -> str:
    """Markdown 的可见文字：去标记、留文字与链接文本。"""
    t = LINK.sub(r"\1", md)
    t = re.sub(r"^\s*#{1,4}\s+", "", t, flags=re.M)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"^\s*\d+[.)]\s+", "", t, flags=re.M)
    t = t.replace("**", "").replace("*", "").replace("|", " ").replace(">", " ")
    t = re.sub(r"^\s*[\s:|-]+\s*$", " ", t, flags=re.M)
    return re.sub(r"\s+", " ", t).strip()


def sync(body_markdown: str) -> str:
    """闸门入口：确定性重建。失败即抛错，不静默降级。"""
    html_frag = to_html(body_markdown)
    a, b = md_visible_text(body_markdown), visible_text(html_frag)
    if a != b:
        raise ValueError("可见文字在 Markdown→HTML 转换中发生变化，拒绝输出")
    if len(re.findall(r"<h1[ >]", html_frag)) != len(re.findall(r"^#\s+\S", body_markdown, re.M)):
        raise ValueError("H1 数量不一致")
    if len(re.findall(r"<h2[ >]", html_frag)) != len(re.findall(r"^##\s+\S", body_markdown, re.M)):
        raise ValueError("H2 数量不一致")
    if body_markdown.count("](") != html_frag.count("<a "):
        raise ValueError("链接数量不一致")
    return html_frag


def _selftest() -> None:
    md = (
        "# 标题 T\n\n"
        "第一段有 [锚文本](https://example.com/a?x=1&y=2) 和 **粗体**。\n"
        "同一段第二行。\n\n"
        "## 小节\n\n"
        "- 项目一\n- 项目二\n\n"
        "1. 步骤一\n2. 步骤二\n\n"
        "| 变量 | 取值 |\n| --- | :---: |\n| 分辨率 | 32×32 |\n"
    )
    out = sync(md)
    assert "<h1>标题 T</h1>" in out, out
    assert '<a href="https://example.com/a?x=1&amp;y=2">锚文本</a>' in out, out
    assert "<strong>粗体</strong>" in out, out
    assert "<h2>小节</h2>" in out, out
    assert "<ul><li>项目一</li><li>项目二</li></ul>" in out, out
    assert "<ol><li>步骤一</li><li>步骤二</li></ol>" in out, out
    assert "<th>变量</th>" in out and ">32×32</td>" in out, out
    assert "&amp;amp;" not in out, "URL 被二次转义"
    # 链接变动必须被同步检出：这正是闸门存在的理由
    md2 = md.replace("第一段有 ", "第一段有 ")
    assert sync(md2) == out, "同输入必须同输出"
    try:
        sync("# 标题\n\n段落 [a](u) 文字\n")
    except ValueError:
        raise AssertionError("正常稿不应报错")
    print("selftest ok")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("body", nargs="?", help="body_markdown 文件路径；省略则读 stdin")
    ap.add_argument("-o", "--out", help="输出 HTML 文件路径；省略则打印到 stdout")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        _selftest()
        return

    md = pathlib.Path(a.body).read_text(encoding="utf-8") if a.body else sys.stdin.read()
    frag = sync(md)
    if a.out:
        pathlib.Path(a.out).write_text(frag + "\n", encoding="utf-8")
        print(f"已写出 {a.out}（{len(frag):,} 字符）")
    else:
        print(frag)


if __name__ == "__main__":
    main()
