#!/usr/bin/env python3
"""把 `品牌资料库/` + `发布与链接记录/` 压成给 agent 用的内链索引（JSON）。

输出 `Divoom 内容资料库/内链索引/`：
  博客.json   256 篇已发布文章：URL + 标题 + 官方栏目     ← 内链主要目标
  产品.json   62 个 PDP：URL + 官方名 + 锚文本候选 + 话题
  页面.json   16 个集合 + 5 个场景页（类目级内链目标）

三条设计约束：
  · 只搬运官方已有信息，不发明词——锚文本候选全部来自官方命名（`锚文本总规范.md`）
  · 按类型拆文件：加内链时主要读 `博客.json`，不必把 62 个 PDP 一起塞进上下文
  · 纯标准库。frontmatter 的值构建时就是 JSON，直接 json.loads，不需要 yaml

用法：
  python3 build_link_index.py            # 生成
  python3 build_link_index.py --selftest # 只校验现有产出
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from build_brand_library import CAT_ANCHOR  # 复用同一份类目锚文本映射

HERE = pathlib.Path(__file__).parent
VAULT = HERE / "Divoom 内容资料库"
LIB = VAULT / "品牌资料库"
OUT = VAULT / "内链索引"

# 类目锚文本（"pixel art speaker"）指向集合页，产品名锚文本指向 PDP——两者不能混
CAT_VALUES = {v for v in CAT_ANCHOR.values() if v}

# 品类集合 vs 促销集合：写科技文章时链到「Christmas Gift」是错的，这些句柄要挡掉
PROMO = ("all", "sale", "gift", "christmas", "new-product", "featured", "kol-",
         "price", "worry-free", "bundle-sale")

# 虚词不能单独当锚文本——`短名` 回退成 title.split()[1] 时切出来的正是这类垃圾（"the"）
STOPWORDS = {"the", "a", "an", "and", "or", "of", "for", "with", "to", "in", "on",
             "at", "by", "from", "your", "our", "this", "that", "purchase"}


def frontmatter(p: pathlib.Path) -> dict:
    """YAML frontmatter → dict。值是构建时 json.dumps 写的，所以直接 loads。"""
    m = re.match(r"^---\n(.*?)\n---\n",
                 p.read_text(encoding="utf-8", errors="replace"), re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).split("\n"):
        k, sep, v = line.partition(":")
        if not sep:
            continue
        v = v.strip()
        try:
            out[k.strip()] = json.loads(v) if v else ""
        except json.JSONDecodeError:
            out[k.strip()] = v.strip('"')
    return out


def dehandle(h: str) -> str:
    """`pixel-display` → `Pixel Display`。句柄本身就是官方命名，不算发明词。"""
    return " ".join(w.capitalize() for w in re.split(r"[-_]", h) if w)


def products() -> list:
    out = []
    for f in sorted((LIB / "产品").glob("*.md")):
        d = frontmatter(f)
        if not d.get("PDP_URL"):
            continue
        cands = d.get("锚文本候选", [])
        cat = [a for a in cands if a in CAT_VALUES]
        out.append({
            "名称": d.get("产品名", ""),
            "短名": d.get("短名", ""),
            "分类": d.get("分类", "") or d.get("官方分类", ""),
            "URL": d["PDP_URL"],
            "在售": bool(d.get("在售")),
            "锚文本候选": cands,
            "类目锚文本": cat[0] if cat else "",
            "话题": d.get("话题关键词", []),
            "所属集合": d.get("所属集合", []),
        })
    return out


def pages() -> list:
    out = []
    for f in sorted((LIB / "集合").glob("*.md")):
        d = frontmatter(f)
        if not d.get("集合URL"):
            continue
        name = d.get("集合名", "")
        out.append({
            "类型": "集合",
            "名称": name,
            "用途": "促销" if any(k in name.lower() for k in PROMO) else "品类",
            "URL": d["集合URL"],
            "产品数": d.get("产品数", 0),
            "锚文本候选": [dehandle(name)] if name else [],
        })
    for f in sorted((LIB / "场景").glob("*.md")):
        d = frontmatter(f)
        if not d.get("页面URL"):
            continue
        name = d.get("场景页", "")
        out.append({
            "类型": "场景页",
            "名称": name,
            "用途": "品类",
            "URL": d["页面URL"],
            "产品数": None,
            "锚文本候选": [dehandle(name)] if name else [],
        })
    return out


def blogs() -> tuple:
    """返回 (条目, 列数异常的行)。表格列序见 `已发布文章.md` 表头。"""
    p = VAULT / "发布与链接记录" / "已发布文章.md"
    out, bad = [], []
    for line in p.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("| D"):
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) != 8:
            bad.append(line[:70])
            continue
        out.append({"编号": c[0], "标题": c[3], "URL": c[4], "官方栏目": c[1]})
    return out, bad


def build() -> dict:
    data = {"博客.json": blogs()[0], "产品.json": products(), "页面.json": pages()}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        (OUT / name).write_text(
            json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  {name:12s} {len(rows):4d} 条  {(OUT / name).stat().st_size / 1024:6.1f} KB")
    return data


def selftest() -> None:
    for name in ("博客.json", "产品.json", "页面.json"):
        assert (OUT / name).exists(), f"缺 {name}，先跑不带参数生成一次"
    bl = json.loads((OUT / "博客.json").read_text(encoding="utf-8"))
    pr = json.loads((OUT / "产品.json").read_text(encoding="utf-8"))
    pg = json.loads((OUT / "页面.json").read_text(encoding="utf-8"))

    assert len(bl) == 256, f"博客应为 256 篇，实为 {len(bl)}"
    assert len(pr) == 62, f"产品应为 62 个，实为 {len(pr)}"
    assert len(pg) == 21, f"页面应为 16 集合 + 5 场景 = 21，实为 {len(pg)}"

    for row in bl + pr + pg:
        assert row["URL"].startswith("https://divoom.com"), f"非官方 URL: {row['URL']}"
    for row in bl:
        assert row["标题"] and row["官方栏目"], f"博客字段缺失: {row['编号']}"
    for row in pr:
        assert row["名称"] and row["锚文本候选"], f"产品锚文本为空: {row['名称']}"
        # ① 不发明词：每个候选都要能从官方名或官方短名推出
        # ② 虚词不能单独成锚：守的就是 short 回退成 title.split()[1] 切出 "the" 的那个 bug
        name, short = row["名称"].strip(), row["短名"].strip()
        for a in row["锚文本候选"]:
            a = a.strip()
            assert (a.lower() in name.lower() or a.lower() == short.lower()
                    or a.lower() == f"divoom {short}".lower()
                    or a in CAT_VALUES), \
                f"锚文本候选 {a!r} 无法从官方名 {name!r} 或类目映射推出（发明词）"
            assert not (len(a.split()) == 1 and a.lower() in STOPWORDS), \
                f"锚文本候选是虚词 {a!r}（{name}）"

    assert len({r["URL"] for r in bl}) == 256, "博客 URL 有重复"
    assert len({r["URL"] for r in pr}) == 62, "产品 URL 有重复"
    assert sum(1 for r in pg if r["用途"] == "品类") >= 5, "品类集合太少，促销过滤可能过宽"
    print("  ✓ selftest 通过：256 博客 / 62 产品 / 21 页面，URL 无重复，无垃圾锚文本")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        _, bad = blogs()
        if bad:
            print(f"  ⚠ {len(bad)} 行博客表格列数异常，已跳过：")
            for b in bad[:5]:
                print("    " + b)
        build()
        selftest()
