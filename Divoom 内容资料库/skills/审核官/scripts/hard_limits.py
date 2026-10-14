#!/usr/bin/env python3
"""审核官的机械复核层 —— 移植自 seo_quality_analyzer/core/analyzer.py 的硬限制算法层。

原项目的封顶规则靠 Python 强制，所以 AI 打分再宽松也会被压住。这里保留同一套做法，
把词表与域名按 Divoom 改写：

  | 检查 | 触发 | 封顶 |
  | --- | --- | --- |
  | 绝对化营销词 | 命中即压 | 7.5 |
  | 内链密度 | >1.5 个/百词 | 7.5 |
  | 无源硬数值 | ≥3 个精确数值且无来源引用 | 7.0 |
  | 安全边界缺失 | 涉电气/安装/防水/儿童/隐私且无边界措辞 | 5.5 |
  | 型号名 | 出现具体型号 | 记硬伤（不得 pass） |

用法：
    python3 hard_limits.py 稿件.md
    python3 hard_limits.py 稿件.md --json

退出码：0 = 无命中；1 = 有降级命中；2 = 有硬伤。
"""
from __future__ import annotations
import argparse, json, re, sys

# ── 词表（Divoom 改写）────────────────────────────────────────────────────

# 1. 绝对化营销词：与 Zima 项目同一批，科技品类通用
MARKETING = ["game-changer", "game changer", "unprecedented", "revolutionary",
             "the ultimate", "gold standard", "best-in-class", "world's first"]

# 4a. 安全敏感话题（Divoom 的四类红线，替换原项目的 PT/DRM 词表）
RISK_TOPICS = {
    "电气与电池": ["charger", "charging", "battery", "power adapter", "watt", "overheat",
                   "发热", "电池", "充电", "功率"],
    "安装与坠落": ["wall mount", "mounting", "bracket", "hang", "weight limit", "fall",
                   "挂墙", "支架", "承重", "坠落"],
    "防水与进水": ["waterproof", "water-resistant", "splash", "wash", "wet", "submerge",
                   "防水", "泼溅", "清洗", "进水"],
    "儿童与隐私": ["kid", "child", "children", "microphone", "privacy", "permission",
                   "儿童", "孩子", "麦克风", "隐私", "权限"],
}

# 4b. 安全边界措辞：出现任一即认为有边界说明
BOUNDARY = ["do not", "avoid", "warning", "caution", "risk", "not suitable",
            "requires", "check with", "consult", "disclaimer", "safety",
            "不要", "避免", "警告", "注意", "风险", "不适用", "建议咨询", "安全", "免责"]

# 5. 型号名
# 口径已变更：过去「产品型号」为空、没有权威来源，所以任何型号名都算硬伤。
# 现在 `品牌资料库/产品/` 提供了官方产品名（抓自 divoom.com PDP 与官方手册），
# 所以规则改为——**型号名必须与官方命名一致**；自创/拼错的型号名仍是硬伤。
MODEL_PATTERNS = [
    r"\bDivoom\s+[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b",   # Divoom Dipow-65W
    r"\b(?:Pixoo|Ditoo|Timebox|Songbird|SongBird|Spark|Tiivoo|MiniToo|FlowToo|"
    r"Lovelock|Itour|K-StarSpark|Fairy-OK|Cyberbag|Backpack-[MS]|Sling\s?Bag-?[VM]?|"
    r"Astrotoo|Emoto|Emodo|DinerPal|Dipow|Times\s?Frame|Times\s?Gate|CyberBag)\b",
]

_HERE = __import__("pathlib").Path(__file__).resolve()
_VAULT = _HERE.parents[3]   # skills/审核官/scripts → 审核官 → skills → 资料库根
# 注意层级：parents[2] 是 skills/，不是资料库根；写错会读不到 品牌资料库/产品/，
# 从而误报「官方产品名库缺失」并把分压到 8.0（2026.09 审核官实测发现）。
_OFFICIAL: set[str] | None = None


def official_names() -> set[str]:
    """官方产品名与短名（来自 品牌资料库/产品/*.md 的 frontmatter）。"""
    global _OFFICIAL
    if _OFFICIAL is not None:
        return _OFFICIAL
    names: set[str] = set()
    d = _VAULT / "品牌资料库" / "产品"
    if d.is_dir():
        for f in d.glob("*.md"):
            try:
                head = f.read_text(encoding="utf-8", errors="replace")[:1200]
            except OSError:
                continue
            for m in re.finditer(r'^(?:产品名|短名):\s*"?(.+?)"?\s*$', head, re.M):
                v = m.group(1).strip().strip('"')
                if v:
                    names.add(v.lower())
    _OFFICIAL = names
    return names


def model_verdict(text: str) -> tuple[list[dict], list[str]]:
    """返回 (硬伤, 已核对的官方型号名)。

    命中型号模式后，再与官方命名比对：一致 → 放行（记下来供报告）；不一致 → 硬伤。
    """
    official = official_names()
    found: set[str] = set()
    for pat in MODEL_PATTERNS:
        for m in re.finditer(pat, text):
            found.add(m.group(0).strip())
    bad, good = [], []
    for h in sorted(found):
        low = h.lower()
        # 官方全名里包含该短名，或该名本身就是官方登记项 → 视为一致
        ok = (low in official) or any(low in n for n in official)
        if ok:
            good.append(h)
        else:
            bad.append({"rule": "型号名",
                        "detail": f"出现型号「{h}」，但品牌资料库的官方产品名里没有它；"
                                  f"自创或拼错的型号名属硬伤。"})
    return bad, good

# 数值断言：除原有单位外，补上「宽×高」分辨率形态（64×64 / 16x16）、mm/cm、以及中文单位。
# 2026.10 审核官实测：原正则不认 `64×64` 与 `mm`，导致 numeric_claims 恒为 0、数值类封顶形同虚设。
NUM = re.compile(
    r"(?:\d+(?:\.\d+)?\s*[×xX*]\s*\d+(?:\.\d+)?)"          # 64×64 / 16x16
    r"|(?:\d+(?:\.\d+)?\s*(?:%|W\b|watt|mAh|hours?|hrs?|mm|cm|inch|inches|in\b|colors?|colours?|px|pixels?|Hz|dB|GB|MB))",
    re.I)
LINK_MD = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def hits(terms: list[str], low: str) -> list[str]:
    """按词边界命中词表。

    不能用 `term in low` 做子串匹配：`hang` 会命中 `c-hang-er`（game-changer），
    `kid` 会命中 `kidney`，凭空造出「安装与坠落」「儿童与隐私」这类假红线。
    含中文的词条没有 \\b 概念，退回子串匹配。
    """
    out = []
    for t in terms:
        if re.search(r"[a-z]", t, re.I):
            if re.search(r"\b" + re.escape(t) + r"\b", low):
                out.append(t)
        elif t in low:
            out.append(t)
    return sorted(set(out))


def check(text: str) -> dict:
    low = text.lower()
    caps: list[dict] = []
    hard: list[dict] = []

    # 1 营销词
    hit_mk = hits(MARKETING, low)
    if hit_mk:
        caps.append({"cap": 7.5, "rule": "绝对化营销词",
                     "detail": f"检测到 {hit_mk}，分数锁定 7.5 及以下。"})

    # 2 内链密度
    links = LINK_MD.findall(text)
    words = len(text.split())
    if words:
        density = len(links) / (words / 100)
        if density > 1.5:
            caps.append({"cap": 7.5, "rule": "内链密度",
                         "detail": f"内链密度 {density:.1f} 个/百词，判定为 SEO 堆砌。"})

    # 3 无源硬数值
    nums = NUM.findall(text)
    sources = [l for l in links if "divoom.com" not in l.lower()]
    if len(nums) >= 3 and not sources:
        caps.append({"cap": 7.0, "rule": "无源硬数值",
                     "detail": f"提取到 {len(nums)} 个精确数值断言（如 {nums[:2]}）却无来源引用，"
                               f"判定为无源主张。"})

    # 4 安全边界缺失
    if not hits(BOUNDARY, low):
        for label, terms in RISK_TOPICS.items():
            hit = hits(terms, low)
            if hit:
                caps.append({"cap": 5.5, "rule": f"安全边界缺失（{label}）",
                             "detail": f"涉及「{label}」话题（{hit[:3]}）但全文无安全边界说明。"})
                break

    # 5 型号名：与官方命名一致则放行，自创/拼错才是硬伤
    bad_models, good_models = model_verdict(text)
    hard.extend(bad_models)
    if bad_models and not official_names():
        # 官方名库缺失时无法区分「自创型号」与「官方型号」，此时按最严处理，
        # 但必须说出来——否则会静默拒掉合法稿。
        caps.append({"cap": 8.0, "rule": "官方产品名库缺失",
                     "detail": "读不到 `品牌资料库/产品/`，无法核对型号名是否官方；"
                               "本轮所有型号名均按未登记处理。请先跑 build_brand_library.py。"})

    return {"caps": caps, "hard_issues": hard, "stats": {
        "words": words, "links": len(links), "numeric_claims": len(nums),
        "external_links": len(sources),
        "official_models": good_models,
        "effective_cap": min([c["cap"] for c in caps], default=None),
    }}


def _selftest() -> None:
    """每条封顶规则都要有一次「确实打得中」的验证；否则规则坏了也看不出来。"""
    # 1 营销词
    r = check("This pixel speaker is a real game-changer for your desk.")
    assert any(c["rule"] == "绝对化营销词" and c["cap"] == 7.5 for c in r["caps"]), r
    # 1b 回归：`hang` 不能命中 `c-hang-er`，否则 game-changer 会假触发「安装与坠落」
    assert not any("安装与坠落" in c["rule"] for c in r["caps"]), r
    # 1c 回归：`kid` 不能命中 `kidney`
    r = check("Talk to your doctor about kidney health.")
    assert not any("儿童与隐私" in c["rule"] for c in r["caps"]), r
    # 2 内链密度（100 词里塞 5 条 divoom 内链 = 5 个/百词）
    filler = " ".join(["desk"] * 95)
    r = check(filler + " [a](https://divoom.com/a) [b](https://divoom.com/b) "
                      "[c](https://divoom.com/c) [d](https://divoom.com/d) "
                      "[e](https://divoom.com/e)")
    assert any(c["rule"] == "内链密度" and c["cap"] == 7.5 for c in r["caps"]), r
    # 3 无源硬数值：3 个精确数值 + 零外部引用
    r = check("It shows 16 colors on a 32 inch panel and draws 50W.")
    assert any(c["rule"] == "无源硬数值" and c["cap"] == 7.0 for c in r["caps"]), r
    # 4 安全边界缺失：谈到电池却全文无边界措辞
    r = check("The battery lasts all day. Charge it fully before use.")
    assert any(c["cap"] == 5.5 and "电气与电池" in c["rule"] for c in r["caps"]), r
    # 4b 有边界措辞就不该压
    r = check("The battery lasts all day. Do not charge it unattended.")
    assert not any(c["cap"] == 5.5 for c in r["caps"]), r
    # 5 型号名：自创/未登记的型号 = 硬伤
    r = check("Compare the Divoom Zyxq-99 with a plain photo frame.")
    assert r["hard_issues"] and "Zyxq-99" in r["hard_issues"][0]["detail"], r
    # 5b 回归：官方登记过的型号名必须放行（品牌资料库已提供官方命名）
    if official_names():
        r = check("The Pixoo works as a pixel art display.")
        assert not r["hard_issues"], r
        r = check("MiniToo is a palm-sized retro pixel speaker.")
        assert not r["hard_issues"], r
    # 有效上限取最严的一条
    r = check("A game-changer. It shows 16 colors on a 32 inch panel and draws 50W.")
    assert r["stats"]["effective_cap"] == 7.0, r
    print("selftest ok：5 条封顶 + 边界反例 + 有效上限")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selftest()
        return 0
    if not a.path:
        ap.error("需要稿件路径，或用 --selftest")
    text = open(a.path, encoding="utf-8", errors="replace").read()
    # 若输入是稿件 JSON（含 body_markdown），只审正文——否则 search_demand/URL 里的
    # 杂串（如 r/PixelArt）会被型号名规则误命中，造成假阳性硬伤。
    if text.lstrip().startswith("{"):
        try:
            doc = json.loads(text)
            body = doc.get("body_markdown")
            if isinstance(body, str) and body.strip():
                text = body
        except json.JSONDecodeError:
            pass
    r = check(text)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        s = r["stats"]
        print(f"词数 {s['words']}｜内链 {s['links']}｜外部引用 {s['external_links']}｜"
              f"数值断言 {s['numeric_claims']}")
        if r["caps"]:
            print(f"\n触发 {len(r['caps'])} 条封顶，最终上限 {s['effective_cap']}：")
            for c in r["caps"]:
                print(f"  [系统强制降级] 压 {c['cap']}｜{c['rule']}：{c['detail']}")
        else:
            print("\n封顶：无命中")
        if s.get("official_models"):
            print(f"\n已核对官方型号名 {len(s['official_models'])} 个：{s['official_models']}")
        if r["hard_issues"]:
            print(f"\n硬伤 {len(r['hard_issues'])} 条（不得 pass）：")
            for h in r["hard_issues"]:
                print(f"  [{h['rule']}] {h['detail']}")
    return 2 if r["hard_issues"] else (1 if r["caps"] else 0)


if __name__ == "__main__":
    sys.exit(main())
