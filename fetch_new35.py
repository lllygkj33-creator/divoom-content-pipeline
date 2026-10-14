#!/usr/bin/env python3
"""抓取 GPT 分析里新增的 35 篇 Momcozy 正文，按分析给出的栏目归类到 work/bodies/<栏目>/。"""
from __future__ import annotations
import concurrent.futures as cf, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).parent
ANALYSIS = pathlib.Path.home()/'Downloads'/'Divoom-Momcozy-扩样与正文节奏分析.md'
DST = ROOT/'work'/'bodies'
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

def slug(u: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", u.rsplit("/",1)[-1].lower()).strip("-")[:60]

def parse() -> dict[str, list[str]]:
    """从分析文档的「新增 35 篇 URL」分节里解析 栏目 -> URL 列表"""
    txt = ANALYSIS.read_text(encoding='utf-8')
    out = {}
    cur = None
    for line in txt.split('\n'):
        m = re.match(r'^###\s+(科技与信息|帮助与提示|产品对比|购买指南|设置与使用)', line)
        if m:
            cur = m.group(1); out[cur] = []
        elif cur and line.strip().startswith('- http'):
            out[cur].append(line.strip()[2:].strip())
    return out

def get(u: str):
    return subprocess.run(["curl","-sS","-L","--max-time","60","--compressed","-A",UA,u],
                          capture_output=True, text=True).stdout

def main() -> None:
    import sys; sys.path.insert(0, str(ROOT))
    from fetch_bodies import body_html, to_md
    jobs = []
    for col, urls in parse().items():
        d = DST/col; d.mkdir(parents=True, exist_ok=True)
        for u in urls:
            # 编号接在现有序号之后
            n = len(list(d.glob('*.md'))) + len([j for j in jobs if j[0]==col]) + 1
            jobs.append((col, n, u, d/f"{n:02d}-{slug(u)}.md"))
    print(f"待抓 {len(jobs)} 篇")
    def work(job):
        col, n, u, dest = job
        for attempt in range(3):
            doc = get(u)
            if doc and len(doc) > 5000:
                md, imgs = to_md(body_html(doc))
                if len(md) > 800:
                    dest.write_text(f"<!-- 来源URL: {u} -->\n\n{md}\n", encoding='utf-8')
                    return (col, u, "ok", len(md))
            import time; time.sleep(3+3*attempt)
        # 回落 fcrawl
        p = subprocess.run(["fcrawl", u], capture_output=True, text=True, timeout=300)
        if p.returncode == 0 and len(p.stdout) > 1500:
            dest.write_text(f"<!-- 来源URL: {u} -->\n<!-- 抓取方式: fcrawl -->\n\n{p.stdout.strip()}\n", encoding='utf-8')
            return (col, u, "ok-fcrawl", len(p.stdout))
        return (col, u, "FAIL", 0)
    ok = fail = 0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for col, u, st, ln in ex.map(work, jobs):
            if st.startswith("ok"): ok += 1
            else: fail += 1; print(f"  ! {st} {col} {u}")
    print(f"完成 ok={ok} fail={fail}")

if __name__ == "__main__":
    main()
