#!/usr/bin/env python3
"""Verify the imported anchor samples against the source CSVs, row by row."""
import csv, pathlib, re, sys

LIB = pathlib.Path('Divoom 内容资料库'); S = pathlib.Path('work/samples/五类CSV')
DEAD = {
 "https://momcozy.com/blogs/babycare/how-often-to-change-newborn-diaper",
 "https://momcozy.com/blogs/baby/home-playard-vs-travel-crib",
 "https://momcozy.com/blogs/babycare/pumping-breast-milk-at-work-checklist",
 "https://momcozy.com/products/s12-pro-double-wearable-breast-pump-and-4-in-1-hands-free-pumping-bra",
 "https://momcozy.com/products/momcozy-screw-on-breastmilk-storage-bags48pcs",
 "https://momcozy.com/products/water-wipes-higher-level-of-purity",
 "https://momcozy.com/blogs/babycare/tracking-baby-pee-poop-tips-for-parents",
}
SPEC = {"科技与信息": (119, 26), "帮助与提示": (150, 44), "产品对比": (116, 60),
        "购买指南": (194, 93), "设置与使用": (166, 76)}


def parse(line: str) -> list[str]:
    body = line.strip()[1:-1]
    out, cur, esc = [], '', False
    for ch in body:
        if esc:
            cur += ch; esc = False
        elif ch == '\\':
            esc = True
        elif ch == '|':
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return [c.strip() for c in out]


def main() -> int:
    tot = link = dead = bad = 0
    for cat, (srows, slinks) in SPEC.items():
        with (S / f'{cat}.csv').open(encoding='utf-8-sig', newline='') as f:
            src = list(csv.DictReader(f))
        md = (LIB / cat / '锚文本规范.md').read_text(encoding='utf-8')
        sec = md[md.index('## 三、真实文章样本'):md.index('<!-- 真实文章样本：end -->')]
        rendered = []
        for line in sec.splitlines():
            if not line.startswith('| ') or '---' in line or line.startswith('| H2'):
                continue
            cs = parse(line)
            if len(cs) != 3:
                continue
            h2, a, u = cs
            h2 = '' if h2 == '（空）' else h2.replace('\\|', '|')
            a = '' if a == '（无内链）' else a.replace('\\|', '|')
            if u == '（无内链）':
                u = ''
            else:
                m = re.match(r'^⚠️ 原文失效链接（404）／勿作为推荐：`(.*)`$', u)
                u = (m.group(1) if m else u.strip('`')).replace('\\|', '|')
            rendered.append((h2, a, u))
        want = [(r['H2'].strip(), r['锚文本'].strip(), r['内链URL'].strip()) for r in src]
        diffs = [(w, g) for w, g in zip(want, rendered) if w != g]
        n = sum(1 for r in want if r[2]); nd = sum(1 for r in want if r[2] in DEAD)
        tot += len(want); link += n; dead += nd; bad += len(diffs)
        ok = (len(want), n) == (srows, slinks) and not diffs
        print(f'{cat:8} 行 {len(want):3}/{len(rendered):3} 带链接 {n:3} 失效 {nd} 差异 {len(diffs)}  '
              f'{"✓" if ok else "✗"}')
        for w, g in diffs[:2]:
            print('    源:', w); print('    渲:', g)
    print(f'\n合计 行 {tot} 带链接 {link} 失效 {dead} 差异 {bad}')
    ok = (tot, link, dead, bad) == (745, 299, 9, 0)
    print('对照规格 745 / 299 / 9:', '通过' if ok else '不通过')
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
