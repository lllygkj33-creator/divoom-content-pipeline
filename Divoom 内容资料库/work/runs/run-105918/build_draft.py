#!/usr/bin/env python3
"""Build 01-draft-v1.json for run-105918 (编辑 first-round body, no links)."""

import json
import os
import re

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(RUN_DIR, "..", "..", ".."))

BRIEF_KEYS = [
    "topic",
    "column",
    "fx",
    "polished_title",
    "search_demand",
    "outline_logic",
    "reference_urls",
]

H1 = "Why a 64×64 Pixel Art Canvas Can Still Make Small Text Hard to Read on a Desk Display"

BODY = """# {h1}

A 64×64 pixel canvas can still make small text hard to read on a desk display because canvas size and the per-character pixel budget are two different quantities. The grid sets how much picture fits on the panel; legibility is set by how many points one glyph can claim, how wide the gap is between adjacent pixels, and how close your eye is to the panel. At desk distance the eye resolves individual lit points before it resolves the letterforms they should form, so a sentence arrives as a field of dots. The same short word can sit legibly in a clock face and fail as a caption.

That holds while the message is short enough to read in a glance. It stops holding once the panel sits close enough that the dots fuse into smooth shapes, or once the display is a different panel type rather than a coarser grid. What follows separates the variables people usually merge into one complaint.

## The Canvas Is Big Enough, and That Is Not a Statement About a Single Letter

The first confusion is that "64×64" sounds like a small number and therefore sounds like the whole answer. It is the top of the range: pixel-art canvases across these displays are described as 16×16, 32×32 or 64×64, and 64×64 is recorded as the largest pixel-art canvas class, with a 64x64 pixel resolution appearing alongside a 128×128 panel and a 480 × 480 screen in the wider product family. A 64×64 grid is 4,096 addressable points — four times the points of a 32×32 grid and sixteen times those of a 16×16 one, and the step up in detail is why the catalog also lists finer canvas detail as a capability rather than a limitation.

Read that as a statement about total picture area and the confusion dissolves. A canvas is a fixed budget of points that everything on screen shares: the background, the border, the icons, the row of numbers and the text. Text is a demand on the same budget with a different shape — it needs points concentrated into small, repeating, highly differentiated shapes arranged in a horizontal run. Four thousand points spread across a picture is a rich picture. Four thousand points is not what a single word gets.

The useful separation is between canvas capacity and allocation. Capacity answers "how much can this panel show at once." Allocation answers "how much did this particular thing get." A clock face, a weather icon or a small widget is a low-allocation element and looks excellent. A sentence is a high-allocation element and does not, even though both are drawn from the same 4,096 points.

## How Many Pixels Does One Recognizable Letter Need?

The second variable comes from outside the hardware: pixel letterforms have a minimum usable pixel budget. Enumerations of very small pixel fonts — including the tiny-font experiments published by moonbench and the small-font threads that circulate in pixel-art and game-development communities — describe the same ladder. In a 2×2 or 3×2 space the number of distinct shapes available is too small to cover an alphabet, so no font exists there. At 3×3 and 3×4, useful sets exist but the designer has to choose which characters to include and which to sacrifice. At 3×5 the result is described as fairly clear. By 5×5, letters that are otherwise ambiguous — M and W, G and B, and similar pairs — separate cleanly, and some designers deliberately use more pixels per character rather than fewer, because a larger glyph can be less ambiguous than a squeezed one.

This is a property of glyph forms, not a Divoom specification, and the distinction matters twice over. It is not a supported minimum font size for any particular display, and it is not a claim about which font a given device ships with. It is the reason a text row is expensive: a 5-pixel-wide glyph plus a one-pixel gap uses 6 of the canvas's 64 columns, so a single line holds roughly a dozen characters at a comfortable bit size. That is a label, a temperature and a time, a stock ticker, a name, or a very short message. It is not a paragraph.

The compression is also unforgiving in a way that ordinary screen text is not. These are one-bit pixels: each point is on or off. There is no intermediate tint inside the grid for edge pixels, so there is no antialiasing to soften a diagonal or to suggest where one stroke ends and the next begins. A rendered letter at 5 pixels high is not a small version of a large letter; it is a different object with fewer decision points, and every stroke you add costs the width of the line.

## Why More Pixels on the Panel Does Not Mean More Pixels in the Letter

The third variable is the one that explains the title. Readability at a desk is not set by the count of points; it is set by the angle each point subtends at your eye, which depends on the physical size of one pixel and on your viewing distance. The panel resolves the ambiguity in an unusual direction, because a pixel-art display is designed to be seen at a distance where the individual emitter grid is still visible — that is what makes an animation read as pixel art rather than as a soft photograph. At typical desk viewing distance, an eye that is resolving the grid is being asked to read letterforms built out of elements it can individually see. The letters therefore break into their component dots precisely when you lean in to read them.

Two consequences follow. First, distance is a legibility control in the same way that font size is: the same caption that fails at arm's length can become readable from across the room, not because anything improved but because the dots fused. Second, physical pixel pitch is the other half of the ratio, and it is a per-product number rather than a general one. Where an official manual gives a panel's physical dimensions, an approximate pitch can be worked out as that dimension divided by the pixel count — a roughly 10-inch panel carrying 64 pixels across works out to a pitch on the order of a few millimetres — but that is an arithmetic estimate from the published size, not a quoted device parameter, and no display in this family publishes an official pixel-pitch or minimum-font-size figure.

The on-or-off structure adds a second, quieter part of the answer. Because every lit point is at full intensity for its color, a small glyph has no mid-tones with which to imply a stroke. At a distance the eye averages neighbouring points and a suggestion of grey appears where the pattern is sparse, which is exactly the effect that makes a well-made small font legible on a coarse grid — and exactly the effect you destroy by moving closer. Anyone who assumes a brighter or higher-color-count panel will fix the text will be disappointed: color vocabulary governs mood and artwork, not letterform recognition. Much the same is true of brightness and color settings, which change how comfortable the panel is to look at, not how many decisions the eye has to make to classify a shape.

## What Actually Decides Whether This Specific Sentence Is Readable

Once the three variables are separated, the practical question becomes which one is doing the work in front of you, and the useful move is to keep two of them fixed while you move the third. Hold the viewing distance and the sentence, and change only the canvas: the same line on a 32×32 or 16×16 grid breaks down sooner, because the per-character budget shrinks and the pitch gets coarser at the same time. That comparison isolates the canvas-side variable, and its direction is always the same — the smaller grid is never the friendlier reading surface.

Hold the canvas and the sentence, and change only the distance. Short labels survive close viewing because a label is a handful of large-shape characters and often benefits from being seen as glyphs; whole sentences survive far viewing, where the grid disappears, but at that range you are reading a sign rather than reading text. If a sentence is only comfortable when you are two steps back, the panel is not failing — the geometry is simply telling you which content class it supports.

Hold both and change the message. A fixed caption that fits the character budget behaves completely differently from a message that must be delivered in full, and that is where the scrolling-text capability earns its place: a short message can be moved across the canvas so it is read a few characters at a time, which removes the length limit without removing the resolution limit. Scrolling does not make small text sharp; it makes a longer message possible inside the same per-character budget, and the reader still has to catch letterforms that are only a handful of pixels wide.

Finally, separate legibility from dislike. A font you find ugly, a color you would have chosen differently, a panel that is brighter or dimmer than you prefer, and a glyph you genuinely cannot identify are four different problems with four different answers. Only the last one is the mechanism described here.

## How to Test It on Your Own Desk

Each check below isolates one variable, and none of them needs instruments. Pick the most easily confused character pairs — O and 0, S and 5, G and 6, B and 8 — and display them together, then move slowly toward and away from the panel. Note the distance at which each pair stops being two different shapes and becomes two similar clusters of dots. That threshold is your viewing distance for this content, and it will differ between pairs, which is itself informative: the pairs that fail first are the ones your font's pixel budget cannot afford.

Then watch the transition from static to scrolling. Type or paste a sentence that plainly exceeds the character budget and let it move. If the message becomes followable while individual characters remain only partly identifiable, you have confirmed that the limit is per-character resolution and not message length. If you cannot follow it at the scroll speed even from a distance where the dots fuse, the character budget is smaller than the speed allows and the content is out of scope for the format.

Repeat the character-pair test on a smaller canvas. The same text on a 32×32 or 16×16 grid should fail sooner; if it does, the canvas-side variable is confirmed. Then check brightness and color settings at the fixed distance where the pairs already fail. If adjusting them changes comfort but not which characters you can tell apart, those controls are not the cause and should not be treated as a fix.

## Where This Explanation Stops

The mechanism describes a reading limit, not a defect. If text is illegible at every distance and every canvas size, if a glyph is garbled rather than merely dotty, if it changes when nothing about the panel has changed, or if the image is uneven in ways that track hardware rather than content, this explanation does not cover it — that is a question about the individual unit and its official product documentation.

It also does not transfer numbers. There is no official minimum font size and no official pixel-pitch figure for these displays to quote, so a specific character ceiling computed for one panel does not carry to another. Features and specifications vary by model, and the arithmetic pitch approximation above is an estimate from a published physical dimension rather than a device parameter.

It is scoped to the panel type that produced it. A pixel grid that switches each point on or off is not the same reading surface as a finer-graded LCD panel, where per-point tonal steps can shape a stroke and the same viewing distance supports smaller letterforms; that difference is a panel-technology difference, not evidence that one font is better than another. Compare like with like before concluding that small text is simply unreadable on desk displays.

Most importantly, the right conclusion is usually a content decision rather than a settings hunt. A 64×64 canvas in a work-desk setting is a strong surface for clocks, icons, small widgets, status indicators, and short scrolling messages, and a poor one for paragraphs. If what you need is a reading surface for long text, the answer is not a cleverer font on the same grid — it is a different medium. A 16×16 or 32×32 canvas will hit the same wall earlier. Within this format, the honest reading of the limit is that it is the price of the aesthetic, not a problem waiting for the right setting.""".format(h1=H1)


def to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    para = []

    def flush():
        if para:
            out.append("<p>" + " ".join(para).strip() + "</p>")
            para.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith("### "):
            flush()
            out.append("<h3>" + s[4:].strip() + "</h3>")
        elif s.startswith("## "):
            flush()
            out.append("<h2>" + s[3:].strip() + "</h2>")
        elif s.startswith("# "):
            flush()
            out.append("<h1>" + s[2:].strip() + "</h1>")
        else:
            para.append(s)
    flush()
    return "\n".join(out)


def body_words(md: str) -> int:
    """Word count of English body text, excluding HTML tags and heading lines' markdown marks."""
    text = md
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"<[^>]+>", " ", text)
    return len([w for w in re.split(r"\s+", text.strip()) if re.search(r"[A-Za-z0-9]", w)])


def main():
    brief = json.load(open(os.path.join(RUN_DIR, "00-brief.json"), encoding="utf-8"))
    product = json.load(open(os.path.join(RUN_DIR, "01b-product-v1.json"), encoding="utf-8"))
    assert product.get("植入") is False, "产品卡结论不是不植入，需复核"

    html = to_html(BODY)
    words = body_words(BODY)
    h2s = re.findall(r"^## (.+)$", BODY, flags=re.M)
    h3s = re.findall(r"^### ", BODY, flags=re.M)
    assert not re.search(r"<a\b|https?://|\]\(|^\s*\[[^\]]+\]:", BODY), "正文含链接或占位符"
    assert not h3s, "不得写 H3"
    assert 1200 <= words <= 2200, f"词数越界: {words}"
    assert len(re.findall(r"^# ", BODY, flags=re.M)) == 1, "H1 必须且只出现一次"

    doc = {k: brief[k] for k in BRIEF_KEYS}
    doc["h1"] = H1
    doc["body_markdown"] = BODY
    doc["html"] = html

    # markdown/HTML 同步性：结构序列必须一一对应，正文文本必须一致
    seq_html = [(t, re.sub(r"<[^>]+>", "", s)) for t, s in re.findall(r"<(h1|h2|p)>(.*?)</\1>", html, flags=re.S)]
    seq_md = []
    for block in [b for b in BODY.split("\n\n") if b.strip()]:
        if block.startswith("## "):
            seq_md.append(("h2", block[3:].strip()))
        elif block.startswith("# "):
            seq_md.append(("h1", block[2:].strip()))
        else:
            seq_md.append(("p", block.strip()))
    assert len(seq_html) == len(seq_md), f"结构块数不一致 {len(seq_html)} vs {len(seq_md)}"
    for (th, sh), (tm, sm) in zip(seq_html, seq_md):
        assert th == tm and sh == sm, f"结构或文本不一致: {th}/{tm} :: {sh[:40]!r} vs {sm[:40]!r}"

    out_path = os.path.join(RUN_DIR, "01-draft-v1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"wrote {out_path}")
    print(f"words={words} h2={len(h2s)} h3={len(h3s)} h1_count={BODY.count(chr(10) + '# ')}")
    for i, h in enumerate(h2s, 1):
        print(f"  H2-{i}: {h}")


if __name__ == "__main__":
    main()
