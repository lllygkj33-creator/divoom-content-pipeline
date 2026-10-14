#!/usr/bin/env python3
"""Strip raw/pdp/*.html down to the visible copy -> pdp_text/<handle>.txt
Keeps: headings, paragraphs, list items, FAQ Q&A, spec tables.
Drops: scripts, styles, nav, footer, header chrome, prices, image alt text."""
import html, pathlib, re

ROOT = pathlib.Path(__file__).parent
SRC, DST = ROOT / "raw" / "pdp", ROOT / "pdp_text"
NOISE = re.compile(r"^(add to cart|buy it now|sold out|regular price|sale price|\$|"
                   r"choosing a selection|share|pin it|save \$|early bird|"
                   r"british indian|french southern|south georgia|"
                   r"\d+% off|unit price|tax included|checkout|returns policy|"
                   r"availability depends|payment options)", re.I)

def blocks(s: str) -> list[str]:
    s = re.sub(r"(?is)<(script|style|noscript|svg|template|nav|footer|header|form|select|button)\b.*?</\1>", " ", s)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    i = s.find("xo-main-product")
    if i > 0:
        s = s[i:]
    # mark block-level boundaries so paragraphs do not run together
    s = re.sub(r"(?i)</(p|div|li|h[1-6]|td|tr|section)>", "\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", s))
    out, seen = [], set()
    for line in txt.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 22 or NOISE.match(line):
            continue
        if line.casefold() in seen:
            continue
        seen.add(line.casefold())
        out.append(line)
    return out

def main():
    DST.mkdir(exist_ok=True)
    for f in sorted(SRC.glob("*.html")):
        b = blocks(f.read_text(encoding="utf-8", errors="replace"))
        (DST / f"{f.stem}.txt").write_text("\n".join(b) + "\n", encoding="utf-8")
        print(f"{f.stem:56} {len(b):4} blocks {sum(len(x) for x in b)//1000:4}K chars")

if __name__ == "__main__":
    main()
