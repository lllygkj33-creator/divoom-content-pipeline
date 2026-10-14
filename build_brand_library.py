#!/usr/bin/env python3
"""把 work/brand-raw.json + work/raw_brand/ 组装成 `Divoom 内容资料库/品牌资料库/`。

结构（给产品经理 agent 扫描用）：
    品牌资料库/
    ├── README.md              用法与字段说明
    ├── 产品.base              ★ 扫描入口：一行一产品
    ├── 集合.base
    ├── 产品/<handle>.md       ★ 单产品全量信息
    ├── 集合/<handle>.md
    ├── 场景/<slug>.md
    └── 手册/<key>.md          英文（或多语种含英文）手册正文

不产生 CSV。
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
LIB = ROOT / "Divoom 内容资料库" / "品牌资料库"
WORK = ROOT / "work"
RAW = WORK / "raw_brand"
DATA = WORK / "brand-raw.json"
SITE = "https://divoom.com"

# manuals.json 的分类 → 英文品类锚文本种子
CAT_ZH = {
    "pixel-displays": "像素显示屏",
    "pixel-speakers": "像素音箱",
    "karaoke-speakers": "卡拉OK音箱",
    "chargers": "充电器",
    "desk-setup": "桌面布置",
    "pixel-bags": "像素背包",
    "speakers": "蓝牙音箱",
    "other": "其他",
}

CAT_ANCHOR = {
    "pixel-displays": "pixel art display",
    "pixel-speakers": "pixel art speaker",
    "karaoke-speakers": "karaoke speaker",
    "chargers": "pixel display charger",
    "desk-setup": "desk setup display",
    "pixel-bags": "pixel art backpack",
    "speakers": "Bluetooth speaker",
    "other": "",
}


def jq(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def jarr(xs) -> str:
    return "[" + ", ".join(jq(x) for x in xs) + "]"


def strip_tags(h: str) -> str:
    h = re.sub(r"<br\s*/?>|</p>", "\n", h or "")
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#39;", "'")
    h = h.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\n{2,}", "\n", h).strip()


# Shopify 的 product_type 是自由文本，口径很乱（"Bundle" / "SEEL-WFP" / "Bluetooth speaker display"），
# 这里统一归一到本库的分类词；手册有官方分类的优先用手册的。
TYPE_MAP = {
    "bluetooth speaker display": "像素音箱",
    "pixel art display": "像素显示屏",
    "backpack": "像素背包",
    "bundle": "套装",
    "seel-wfp": "服务",
    "bluetooth speaker": "蓝牙音箱",
    "speaker": "蓝牙音箱",
    "karaoke": "卡拉OK音箱",
}


def classify(title: str, handle: str, tags: list, manual_cat: str, product_type: str) -> str:
    if manual_cat in CAT_ZH:
        return CAT_ZH[manual_cat]
    pt = (product_type or "").strip().lower()
    if pt in TYPE_MAP:
        return TYPE_MAP[pt]
    blob = (title + " " + " ".join(tags)).lower()
    if "backpack" in blob or "sling bag" in blob:
        return "像素背包"
    if "charger" in blob or "power cord" in blob or "charging cable" in blob:
        return "充电器"
    if "karaoke" in blob or "singing" in blob or "microphone" in blob:
        return "卡拉OK音箱"
    if any(k in blob for k in ("pixoo", "times frame", "times gate", "pixel display",
                               "photo frame", "pixel art display", "smart display")):
        return "像素显示屏"
    if "speaker" in blob or "sound" in blob:
        return "像素音箱"
    if "gift card" in blob:
        return "礼品卡"
    return "未分类"


def kind_of(title: str, handle: str, product_type: str = "") -> str:
    """单品 vs 套装。

    不能用「标题含 &」判套装：那是产品名的一部分——
    `Divoom Pixoo-64Ⅱ WiFi 64x64 Pixel Art LED Display & Social Media Counter`
    是**单品**，却被误判成套装配偶，产品经理第一步「过滤非单品」就会把最匹配的产品筛掉。
    真套装的标志是 Bundle / Gift Pack / 用「 + 」连接两个产品名，或 Shopify 的 product_type=Bundle。
    """
    t = title.lower()
    if handle in ("worry-free-purchase",):
        return "服务"
    if "gift card" in t or handle == "price-spread":
        return "礼品卡"
    if "surprise gift" in t or "mascot" in t:
        return "礼品"
    if ("bundle" in t or "gift pack" in t or " + " in title
            or (product_type or "").strip().lower() == "bundle"):
        return "套装"
    return "单品"


def anchors(title: str, short: str, cat: str) -> list[str]:
    """锚文本种子：全部来自官方命名，不发明词。最终选择仍按 `锚文本总规范.md`。"""
    out = []
    core = re.sub(r"\s+(?:with|for|–|-|—)\s+.*$", "", title).strip(" -–—")
    debrand = re.sub(r"^Divoom\s+", "", title).strip()
    for a in (title, core, debrand, short,
              f"Divoom {short}" if short and short.lower() not in title.lower() else "",
              CAT_ANCHOR.get(cat, "")):
        a = a.strip()
        if a and a.lower() not in {x.lower() for x in out}:
            out.append(a)
    return out


def in_the_box(manual_md: str) -> list[str]:
    """从手册里抽「包装清单」。官方手册有两种排法：
    Pixoo 式（项目符号 + 空行分隔）与 Pixoo-Max 式（连续纯文本行），两种都要吃。"""
    if not manual_md:
        return []
    lines = manual_md.split("\n")
    for i, l in enumerate(lines):
        # 注意弯引号：官方手册写的是 What’s included?，只匹配直引号会整段漏掉
        if re.search(r"in the box|what['\u2019]?s included|package contents|配件|包装清单", l, re.I):
            got, blanks = [], 0
            for x in lines[i + 1: i + 22]:
                s = x.strip()
                if not s:
                    blanks += 1
                    if blanks >= 2 and got:
                        break
                    continue
                if s.startswith("#"):
                    break
                blanks = 0
                s = re.sub("^[-*+•]\\s*", "", s).strip("*_ ")
                if re.match(r"^(Thank you|Due to|If you have|Please read)", s, re.I):
                    if got:
                        break
                    continue
                if 2 <= len(s) <= 70 and not s.startswith(("![", "[")):
                    got.append(s)
            if got:
                return got[:12]
    return []


def manual_headings(md: str, limit: int = 18) -> list[str]:
    """手册的功能小节标题 —— 产品能力的证据来源。"""
    if not md:
        return []
    hs = re.findall(r"^#{2,3}\s+(.+)$", md, re.M)
    # 这些不是「能力小节」，是手册的寒暄与装箱说明，剔掉以免污染话题匹配
    DROP = re.compile(r"^(?:nice to meet you|i'?\u2019?m\s|what'?\u2019?s included|"
                      r"thank you|in the box|package contents|warning|caution|"
                      r"product details|specifications?|troubleshoot)", re.I)
    out = []
    for h in hs:
        h = re.sub(r"[*_`]", "", h).strip()
        h = re.sub(r"[\u4e00-\u9fff]+", "", h).strip(" -–—:：")
        if 3 <= len(h) <= 60 and not DROP.match(h) and h.lower() not in {x.lower() for x in out}:
            out.append(h)
    return out[:limit]


def main() -> None:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    prods = {p["handle"]: p for p in d["products"]}
    members = d["members"]
    man_by_handle = {}
    for m in d["manuals"]["products"]:
        if m.get("productHandle"):
            man_by_handle[m["productHandle"]] = m
    scenes = d.get("scenes", [])

    # 反向：handle → 所属集合
    in_cols: dict[str, list[str]] = {}
    for c, hs in members.items():
        if c == "all":
            continue
        for h in hs:
            in_cols.setdefault(h, []).append(c)

    for sub in ("产品", "集合", "场景", "手册"):
        (LIB / sub).mkdir(parents=True, exist_ok=True)

    # ── 产品 ────────────────────────────────────────────────────────────
    rows = []
    handles = sorted(set(prods) | set(man_by_handle))
    for h in handles:
        p = prods.get(h, {})
        m = man_by_handle.get(h, {})
        title = p.get("title") or m.get("name") or h
        short = m.get("name") or (title.split()[1] if len(title.split()) > 1 else title)
        cat = m.get("category", "")
        catlabel = m.get("categoryLabel", "") or p.get("product_type", "")
        prices = [float(v["price"]) for v in p.get("variants", []) if v.get("price")]
        avail = any(v.get("available") for v in p.get("variants", []))
        tags = p.get("tags", [])
        cols = sorted(in_cols.get(h, []))
        manual_md = ""
        mf = RAW / "manual" / f"{m.get('key','')}.md"
        if mf.exists():
            manual_md = mf.read_text(encoding="utf-8", errors="replace")
        pdp = ""
        pf = RAW / "pdp" / f"{h}.md"
        if pf.exists():
            pdp = pf.read_text(encoding="utf-8", errors="replace")
        kd = kind_of(title, h, p.get("product_type", ""))
        box = in_the_box(manual_md)
        heads = manual_headings(manual_md)
        # 话题关键词：官方标签 + 分类 + 手册小节标题
        kws = []
        selfnames = {str(short).lower(), str(h).lower(), str(m.get("key") or "").lower()}
        for k in list(tags) + [catlabel] + heads[:8]:
            k = str(k).strip()
            if not k or k.lower() in selfnames:
                continue          # 产品自己的名字不是「话题关键词」
            if k.lower() not in {x.lower() for x in kws}:
                kws.append(k)
        fm = [
            "---",
            f"产品名: {jq(title)}",
            f"短名: {jq(short)}",
            f"产品键: {jq(m.get('key') or h)}",
            f"分类: {jq(classify(title, h, tags, cat, p.get('product_type', '')))}",
            f"官方分类: {jq(catlabel)}",
            f"商品类型: {jq(kd)}",
            f"PDP_URL: {jq(SITE + '/products/' + h)}",
            f"价格: {min(prices) if prices else ''}",
            f"在售: {'true' if avail else 'false'}",
            f"标签: {jarr(tags)}",
            f"所属集合: {jarr(cols)}",
            f"手册: {jq('手册/' + (m.get('key') or h) + '.md') if manual_md else ''}",
            f"手册文件: {jq((m.get('manuals') or [{}])[0].get('filename',''))}",
            f"包装清单: {jarr(box)}",
            f"能力小节: {jarr(heads)}",
            f"话题关键词: {jarr(kws[:14])}",
            f"锚文本候选: {jarr(anchors(title, short, cat))}",
            "---",
        ]
        body = [f"# {title}", "",
                f"> PDP：<{SITE}/products/{h}>　·　商品类型：**{kd}**　·　分类：{catlabel or '—'}",
                ""]
        if p.get("body_html"):
            body += ["## PDP 描述（官方商品描述）", "", strip_tags(p["body_html"]), ""]
        if box:
            body += ["## 包装清单（来自官方手册）", ""] + [f"- {x}" for x in box] + [""]
        if heads:
            body += ["## 手册功能小节（官方手册目录）", ""] + [f"- {x}" for x in heads] + [""]
        if pdp:
            body += ["## PDP 正文（firecrawl 抓取，已去噪）", "", pdp, ""]
        if manual_md:
            body += ["## 产品手册正文", "", f"完整手册见 `手册/{(m.get('key') or h)}.md`", ""]
        (LIB / "产品" / f"{h}.md").write_text("\n".join(fm) + "\n\n" + "\n".join(body), encoding="utf-8")
        rows.append((h, title, kd, catlabel, min(prices) if prices else 0, avail, cols, len(kws)))

    # ── 集合 ────────────────────────────────────────────────────────────
    for c in d["collections"]:
        f = RAW / "collection" / f"{c}.md"
        body = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        hs = members.get(c, [])
        names = [prods.get(x, {}).get("title", x) for x in hs]
        fm = ["---", f"集合名: {jq(c)}",
              f"集合URL: {jq(SITE + '/collections/' + c)}",
              f"产品数: {len(hs)}",
              f"成员: {jarr(hs)}", "---"]
        out = [f"# 集合 {c}", "", f"> <{SITE}/collections/{c}>　·　{len(hs)} 个产品", "",
               "## 成员产品", ""] + [f"- {n}" for n in names] + [""]
        if body:
            out += ["## 集合页正文", "", body, ""]
        (LIB / "集合" / f"{c}.md").write_text("\n".join(fm) + "\n\n" + "\n".join(out), encoding="utf-8")

    # ── 场景页 ──────────────────────────────────────────────────────────
    for s in scenes:
        f = RAW / "scene" / f"{s}.md"
        body = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        fm = ["---", f"场景页: {jq(s)}", f"页面URL: {jq(SITE + '/pages/' + s)}", "---"]
        out = [f"# 场景页 {s}", "", f"> <{SITE}/pages/{s}>", "", body or "（未抓到）", ""]
        (LIB / "场景" / f"{s}.md").write_text("\n".join(fm) + "\n\n" + "\n".join(out), encoding="utf-8")

    # ── 手册 ────────────────────────────────────────────────────────────
    for m in d["manuals"]["products"]:
        key = m.get("key") or ""
        f = RAW / "manual" / f"{key}.md"
        if not f.exists():
            continue
        md = f.read_text(encoding="utf-8", errors="replace")
        pick = next((x for x in m["manuals"] if x.get("languageCode") in ("en", "multi", "zh-en")), {})
        fm = ["---", f"产品: {jq(m['name'])}", f"产品键: {jq(key)}",
              f"手册文件: {jq(pick.get('filename',''))}",
              f"手册语种: {jq(pick.get('languageCode',''))}",
              f"手册URL: {jq(pick.get('url',''))}",
              f"页数: {pick.get('pages') if pick.get('pages') is not None else ''}", "---"]
        (LIB / "手册" / f"{key}.md").write_text(
            "\n".join(fm) + f"\n\n# {m['name']} 产品手册\n\n{md}\n", encoding="utf-8")

    # ── .base 视图 ──────────────────────────────────────────────────────
    (LIB / "产品.base").write_text(
        "properties:\n"
        "  产品名:\n    displayName: 产品名\n"
        "  短名:\n    displayName: 短名\n"
        "  分类:\n    displayName: 分类\n"
        "  商品类型:\n    displayName: 类型\n"
        "  PDP_URL:\n    displayName: PDP\n"
        "  价格:\n    displayName: 价格\n"
        "  在售:\n    displayName: 在售\n"
        "  所属集合:\n    displayName: 所属集合\n"
        "  话题关键词:\n    displayName: 话题关键词\n"
        "  锚文本候选:\n    displayName: 锚文本候选\n"
        "views:\n  - type: table\n    name: 产品总表\n    filters:\n      and:\n"
        '        - \'file.inFolder("产品")\'\n'
        "    order:\n      - 分类\n      - 短名\n      - 商品类型\n      - 价格\n"
        "      - 在售\n      - 所属集合\n      - 话题关键词\n      - 锚文本候选\n", encoding="utf-8")

    (LIB / "集合.base").write_text(
        "properties:\n"
        "  集合名:\n    displayName: 集合\n"
        "  产品数:\n    displayName: 产品数\n"
        "  集合URL:\n    displayName: URL\n"
        "views:\n  - type: table\n    name: 集合总表\n    filters:\n      and:\n"
        '        - \'file.inFolder("集合")\'\n'
        "    order:\n      - 集合名\n      - 产品数\n", encoding="utf-8")

    print(f"产品 {len(rows)} 篇 / 集合 {len(d['collections'])} 篇 / 场景 {len(scenes)} 篇 / "
          f"手册 {len(list((LIB/'手册').glob('*.md')))} 篇")


if __name__ == "__main__":
    main()
