#!/usr/bin/env python3
"""用 firecrawl (fcrawl) 抓取样本文章正文 -> work/articles/<slug>.md
每个文件首行写入来源 URL，便于后续生成实例表时对上。"""
import hashlib, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "work" / "articles"
URLS = [u.strip() for u in (ROOT / "work" / "article_urls.txt").read_text().split() if u.strip()]

def slug(u: str) -> str:
    s = re.sub(r"^https?://", "", u)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:90] + "-" + hashlib.md5(u.encode()).hexdigest()[:6]

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ok = fail = skip = 0
    for i, u in enumerate(URLS, 1):
        dest = OUT / f"{slug(u)}.md"
        if dest.exists() and dest.stat().st_size > 800:
            skip += 1
            continue
        for attempt in range(3):
            p = subprocess.run(["fcrawl", u], capture_output=True, text=True, timeout=180)
            body = p.stdout.strip()
            if p.returncode == 0 and len(body) > 500:
                dest.write_text(f"<!-- 来源URL: {u} -->\n\n{body}\n", encoding="utf-8")
                print(f"[{i}/{len(URLS)}] ok   {len(body)//1000}K  {u}")
                ok += 1
                break
            print(f"[{i}/{len(URLS)}] retry{attempt+1} rc={p.returncode} len={len(body)} {u} {p.stderr.strip()[:90]}")
            time.sleep(3 + 3 * attempt)
        else:
            fail += 1
            print(f"[{i}/{len(URLS)}] FAIL {u}")
        time.sleep(0.5)
    print(f"\ndone: ok={ok} skip={skip} fail={fail} total={len(URLS)}")

if __name__ == "__main__":
    main()
