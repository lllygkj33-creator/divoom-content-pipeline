#!/usr/bin/env python3
"""抓取每个栏目样本文章的正文（含图片），转成 markdown。
输出：work/bodies/<栏目>/<序号>-<slug>.md  首行写 URL / FX / 标题
并发 4，纯 curl，比 fcrawl 快很多。"""
from __future__ import annotations
import concurrent.futures as cf, csv, html, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).parent
S = ROOT / "work" / "samples" / "五类CSV"
DST = ROOT / "work" / "bodies"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]


def slug(u: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", u.rsplit("/", 1)[-1].lower()).strip("-")[:60]


def get(url: str) -> str | None:
    p = subprocess.run(["curl", "-sS", "-L", "--max-time", "45", "--compressed", "-A", UA, url],
                       capture_output=True, text=True)
    return p.stdout if p.returncode == 0 and len(p.stdout) > 5000 else None


def body_html(doc: str) -> str:
    """取文章正文容器；返回的是容器**内部** HTML（不含容器自身的开标签）。"""
    for pat in (r"""<[a-z]+[^>]*class=['"][^'"]*yg-blog-article-main__content[^'"]*['"][^>]*>""",
                r"""<[a-z]+[^>]*class=['"][^'"]*article-template__content[^'"]*['"][^>]*>""",
                r"""<[a-z]+[^>]*class=['"][^'"]*article__content[^'"]*['"][^>]*>""",
                r"""<[a-z]+[^>]*class=['"][^'"]*post-content[^'"]*['"][^>]*>""",
                r"<article[^>]*>"):
        m = re.search(pat, doc)
        if not m:
            continue
        rest = doc[m.end():]
        # 容器结束：优先找 article 收尾，否则截取一段足够长的正文
        end = re.search(r'(?is)</div>\s*</div>\s*</article>', rest)
        seg = rest[: end.start()] if end else rest[:120000]
        if len(re.sub(r"<[^>]+>", " ", seg)) > 800:
            return seg
    return ""


def to_md(seg: str) -> tuple[str, int]:
    seg = re.sub(r"(?is)<(script|style|noscript|svg|form|button|iframe)\b.*?</\1>", " ", seg)
    imgs = 0

    def img_sub(m):
        nonlocal imgs
        src = re.search(r'src="([^"]+)"', m.group(0))
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        if not src:
            return ""
        u = html.unescape(src.group(1)).split("?")[0]
        imgs += 1
        return f"\n\n![{html.unescape(alt.group(1)) if alt else ''}]({u})\n\n"

    seg = re.sub(r"(?is)<img\b[^>]*>", img_sub, seg)
    seg = re.sub(r"(?i)<h([1-4])[^>]*>(.*?)</h\1>",
                 lambda m: "\n\n" + "#" * int(m.group(1)) + " " + re.sub(r"<[^>]+>", "", m.group(2)).strip() + "\n\n", seg, flags=re.S)
    seg = re.sub(r"(?is)<li[^>]*>(.*?)</li>", lambda m: "\n- " + re.sub(r"<[^>]+>", "", m.group(1)).strip(), seg)
    seg = re.sub(r"(?i)</(p|div|section|tr)>", "\n\n", seg)
    seg = re.sub(r"(?i)<br\s*/?>", "\n", seg)
    def table_md(m):
        rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", m.group(0))
        out = []
        for r_i, row in enumerate(rows):
            cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
                     for c in re.findall(r"(?is)<t[hd][^>]*>(.*?)</t[hd]>", row)]
            if not cells:
                continue
            out.append("| " + " | ".join(cells) + " |")
            if r_i == 0:
                out.append("| " + " | ".join("---" for _ in cells) + " |")
        return "\n\n" + "\n".join(out) + "\n\n" if out else ""
    seg = re.sub(r"(?is)<table\b.*?</table>", table_md, seg)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", seg))
    txt = re.sub(r"[ \t\u00a0]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    lines = [l.strip() for l in txt.split("\n")]
    out, blank = [], False
    for l in lines:
        if not l:
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(l); blank = False
    return "\n".join(out).strip(), imgs


def main() -> None:
    jobs = []
    for cat in CATS:
        with (S / f"{cat}.csv").open(encoding="utf-8-sig", newline="") as f:
            urls = sorted({r["来源URL"].strip() for r in csv.DictReader(f)})
        d = DST / cat
        d.mkdir(parents=True, exist_ok=True)
        for n, u in enumerate(urls, 1):
            dest = d / f"{n:02d}-{slug(u)}.md"
            if dest.exists() and dest.stat().st_size > 700:
                continue
            jobs.append((cat, n, u, dest))

    CACHE = ROOT / "work" / "html"

    def work(job):
        cat, n, u, dest = job
        cached = CACHE / f"{slug(u)}.html"
        doc = cached.read_text(encoding="utf-8", errors="replace") if cached.exists() else None
        if not doc:
            doc = get(u)
            if doc:
                CACHE.mkdir(parents=True, exist_ok=True)
                cached.write_text(doc, encoding="utf-8")
        if not doc:
            return (cat, u, "fetch-fail", 0, 0)
        md, imgs = to_md(body_html(doc))
        if len(md) < 500:
            return (cat, u, "empty-body", len(md), 0)
        dest.write_text(f"<!-- 来源URL: {u} -->\n\n{md}\n", encoding="utf-8")
        return (cat, u, "ok", len(md), imgs)

    print(f"待抓 {len(jobs)} 篇")
    ok = fail = 0
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for cat, u, st, ln, imgs in ex.map(work, jobs):
            if st == "ok":
                ok += 1
            else:
                fail += 1
                print(f"  ! {st:12} {cat} {u}")
    print(f"完成 ok={ok} fail={fail}")
    for cat in CATS:
        fs = sorted((DST / cat).glob("*.md"))
        print(f"  {cat:8} {len(fs):2} 篇, 合计 {sum(f.stat().st_size for f in fs)//1024} KB")


if __name__ == "__main__":
    main()
