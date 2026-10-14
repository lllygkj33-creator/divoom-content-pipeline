#!/usr/bin/env python3
"""验证「竞品文章的标题是不是本身就带搜索需求」。

方法：拿实例笔记 frontmatter 里的 H1 当查询词，跑真实 SERP，看两个信号：

  1. 精确标题查询 → 这篇文章自己的 URL 在不在榜上（说明它是否靠这个措辞被找到）
  2. 去品牌核心短语 → SERP 有多少个不同域名（域越多说明越像一个被广泛竞争的查询）

用法：
    python3 analyze_title_demand.py --sample 25      # 分层抽样（默认）
    python3 analyze_title_demand.py --all            # 全量 109 篇（约 109*2 次搜索）
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import statistics as st
import subprocess
import sys
import time
import urllib.parse

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库"
CATS = ["科技与信息", "帮助与提示", "产品对比", "购买指南", "设置与使用"]
BRAND = re.compile(r"\b(Momcozy|KTC|Divoom|ChangeGo|TuckGo|CocoSway|DinerPal|BM08)\b", re.I)
KEY = None


def api_key() -> str:
    env = pathlib.Path.home() / ".opencli" / "firecrawl.env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("FIRECRAWL_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("未找到 FIRECRAWL_API_KEY")


def search(query: str, limit: int = 10) -> list[dict]:
    body = json.dumps({"query": query, "limit": limit, "location": "us", "lang": "en"})
    for attempt in range(3):
        p = subprocess.run(
            ["curl", "-sS", "--max-time", "90", "-X", "POST",
             "https://api.firecrawl.dev/v2/search",
             "-H", f"Authorization: Bearer {KEY}",
             "-H", "Content-Type: application/json", "-d", body],
            capture_output=True, text=True)
        try:
            r = json.loads(p.stdout)
        except json.JSONDecodeError:
            time.sleep(4)
            continue
        if r.get("success"):
            d = r.get("data", {})
            return (d.get("web") if isinstance(d, dict) else d) or []
        time.sleep(4)
    return []


def load_titles() -> list[dict]:
    out = []
    for c in CATS:
        for f in sorted((LIB / c / "实例").glob("*.md")):
            t = f.read_text(encoding="utf-8", errors="replace")
            iid = re.search(r"^实例ID:\s*\"?([^\"\n]+)", t, re.M)
            ti = re.search(r"^标题:\s*\"(.+?)\"\s*$", t, re.M)
            ur = re.search(r"^实例URL:\s*\"(.+?)\"\s*$", t, re.M)
            if ti and ur:
                out.append({"col": c, "id": iid.group(1) if iid else "",
                            "title": ti.group(1).strip(), "url": ur.group(1).strip(),
                            "site": "KTC" if "ktcplay" in ur.group(1) else "Momcozy"})
    return out


def core_phrase(title: str) -> str:
    """去掉品牌/型号名，保留问句形态，截到 9 个词。"""
    t = BRAND.sub(" ", title)
    t = re.sub(r"[—–|:：]\s*$", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -–—:|")
    return " ".join(t.split()[:9])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    global KEY
    KEY = api_key()

    rows = load_titles()
    print(f"实例标题 {len(rows)} 条（Momcozy {sum(1 for r in rows if r['site']=='Momcozy')} / "
          f"KTC {sum(1 for r in rows if r['site']=='KTC')}）")

    if not a.all:
        random.seed(42)
        per = max(1, a.sample // len(CATS))
        pick = []
        for c in CATS:
            grp = [r for r in rows if r["col"] == c]
            pick += random.sample(grp, min(per, len(grp)))
        rows = sorted(pick, key=lambda r: (r["col"], r["id"]))
    print(f"本次测 {len(rows)} 条（每条 2 次搜索，约 {len(rows)*2*2} credits）\n", flush=True)

    result = []
    for i, r in enumerate(rows, 1):
        slug = urllib.parse.urlparse(r["url"]).path.rstrip("/").split("/")[-1]
        exact = search(r["title"], limit=10)
        time.sleep(0.6)
        core = search(core_phrase(r["title"]), limit=10)
        time.sleep(0.6)

        def covers(rs):
            for x in rs:
                u = x.get("url", "")
                if r["url"].split("?")[0].rstrip("/") in u or (slug and slug in u):
                    return x.get("position", 0)
            return None

        pos_exact = covers(exact)
        pos_core = covers(core)
        dom_exact = len({urllib.parse.urlparse(x.get("url", "")).netloc for x in exact})
        dom_core = len({urllib.parse.urlparse(x.get("url", "")).netloc for x in core})
        rec = {**r, "slug": slug, "n_exact": len(exact), "n_core": len(core),
               "dom_exact": dom_exact, "dom_core": dom_core,
               "pos_exact": pos_exact, "pos_core": pos_core,
               "core_query": core_phrase(r["title"])}
        result.append(rec)
        flag = "✓" if pos_exact else "✗"
        print(f"[{i:2}/{len(rows)}] {flag} 自身在榜={str(pos_exact):>4}  "
              f"精确 {len(exact):>2}条/{dom_exact}域  核心 {len(core):>2}条/{dom_core}域  "
              f"{r['title'][:52]}", flush=True)

    json.dump(result, open("/tmp/title_demand.json", "w"), ensure_ascii=False, indent=1)

    n = len(result)
    in_exact = [r for r in result if r["pos_exact"]]
    in_core = [r for r in result if r["pos_core"]]
    print(f"\n{'='*72}\n汇总（{n} 条，来源 momcozy.com / us.ktcplay.com）\n{'='*72}")
    print(f"  精确标题查询：自身 URL 在榜 {len(in_exact)}/{n}（{len(in_exact)*100//n}%）"
          f"　位次中位 {st.median([r['pos_exact'] for r in in_exact]) if in_exact else '-'}")
    print(f"  核心短语查询：自身 URL 在榜 {len(in_core)}/{n}（{len(in_core)*100//n}%）")
    de = sorted(r["dom_exact"] for r in result)
    dc = sorted(r["dom_core"] for r in result)
    print(f"  精确标题的 SERP 域名数：中位 {st.median(de):.0f}　最小 {de[0]}　最大 {de[-1]}")
    print(f"  核心短语的 SERP 域名数：中位 {st.median(dc):.0f}　最小 {dc[0]}　最大 {dc[-1]}")
    only_self = [r for r in result if r["n_exact"] <= 2]
    print(f"  精确标题只返回 ≤2 条结果（说明该措辞几乎没人搜）：{len(only_self)}/{n}")
    print(f"  精确标题返回 ≥8 条且有 ≥5 个域名（像真查询）："
          f"{sum(1 for r in result if r['n_exact']>=8 and r['dom_exact']>=5)}/{n}")


if __name__ == "__main__":
    main()
