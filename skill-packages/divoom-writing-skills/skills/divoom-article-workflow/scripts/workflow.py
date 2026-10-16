#!/usr/bin/env python3
"""Offline contracts, stale-review detection, and deterministic publisher export.

No model calls, HTTP requests, credentials, Shopify mutations, or scheduling.
Semantic review is supplied by the executing skill, never fabricated here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "site.json"
STAGES = ("outline", "draft", "links", "review")
TYPE_FX = {"technology": ("F", 14), "buying-guide": ("BG", 11),
           "comparison": ("PC", 10), "setup": ("SU", 13), "support": ("S", 12)}
DIMENSIONS = ("experience", "expertise", "authoritativeness", "trustworthiness",
              "hcu", "infogain", "ymyl")
CHECKS = ("title_promise", "type_logic", "facts", "scope", "product_policy",
          "links", "metadata", "risk_boundaries", "no_duplication")
REQUIRED = ("blog title", "url", "meta title", "meta description", "summary",
            "author", "tags", "blog", "html代码")
OPTIONAL = ("reviewer", "template", "related_products")
VOID = {"img", "br", "hr"}
BLOCK = {"article", "div", "p", "h2", "ul", "ol", "li", "blockquote", "table",
         "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "figure", "figcaption", "br", "hr", "pre"}
ALLOWED = {"article", "div", "span", "p", "h2", "ul", "ol", "li", "strong",
           "em", "b", "i", "blockquote", "table", "thead", "tbody", "tfoot", "tr",
           "th", "td", "caption", "figure", "figcaption", "img", "a", "br", "hr",
           "code", "pre", "sup", "sub", "s", "del"}
PLACEHOLDER = re.compile(r"\$\{[^}]+\}|\[\[(?!related_products_\d+\]\])[^\]]+\]\]|\b(?:YOUTUBE_URL_|BLOG_URL_|PLACEHOLDER)\b", re.I)


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    """Atomic replacement within the chosen directory, without partial deliverables."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".divoom-", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def now():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_time(value):
    if not nonempty(value):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def utf16_length(value):
    return len(value.encode("utf-16-le")) // 2


def word_count(text):
    return len(re.findall(r"\b[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*\b", text))


def is_internal(href, profile):
    if href.startswith("//"):
        return False
    if href.startswith(("/", "#")):
        return True
    host = (urlsplit(href).hostname or "").lower().rstrip(".")
    return any(host == suffix or host.endswith("." + suffix)
               for suffix in profile["first_party_suffixes"])


def valid_url(href, allow_anchor=True):
    if not nonempty(href) or re.search(r"[\s\x00-\x1f\\]", href) or PLACEHOLDER.search(href):
        return False
    if href.startswith("//"):
        return False
    if href.startswith("#"):
        return allow_anchor and len(href) > 1
    if href.startswith("/"):
        return True
    try:
        parts = urlsplit(href)
        _ = parts.port
        return parts.scheme in ("http", "https") and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        return False


class BodyParser(HTMLParser):
    def __init__(self, profile):
        super().__init__(convert_charrefs=True)
        self.profile = profile
        self.errors = []
        self.stack = []
        self.text_parts = []
        self.semantic = []
        self.links = []
        self.ids = set()
        self.h2_ids = []
        self.h2_texts = []
        self.h2_buffer = None
        self.current_section = "intro"
        self.intro_paragraphs = 0
        self.seen_h2 = False
        self.current_link = None

    def handle_starttag(self, tag, attr_list):
        attrs = dict(attr_list)
        if tag in BLOCK:
            self.text_parts.append(" ")
        if tag not in ALLOWED:
            self.errors.append(f"HTML tag not allowed: {tag}")
        if len(attr_list) != len(attrs):
            self.errors.append(f"Duplicate attributes on {tag}")
        if any(k.startswith("on") or k in ("style", "srcdoc") for k in attrs):
            self.errors.append(f"Executable or theme-changing attribute on {tag}")
        for key in ("href", "src"):
            if key in attrs and not valid_url(attrs[key] or "", allow_anchor=key == "href"):
                self.errors.append(f"Invalid {key}: {attrs[key]}")
        if attrs.get("id") is not None:
            if not nonempty(attrs["id"]) or attrs["id"] in self.ids:
                self.errors.append("Blank or duplicate HTML id")
            self.ids.add(attrs["id"])
        if tag == "h2":
            self.seen_h2 = True
            self.current_section = attrs.get("id", "")
            self.h2_ids.append(self.current_section)
            self.h2_buffer = []
        if tag == "p" and not self.seen_h2:
            self.intro_paragraphs += 1
        if tag == "a":
            if self.current_link is not None:
                self.errors.append("Nested anchor")
            if not nonempty(attrs.get("href")) or not nonempty(attrs.get("title")):
                self.errors.append("Every a requires nonempty href/title")
            href = attrs.get("href") or ""
            if valid_url(href) and not is_internal(href, self.profile):
                rel = set((attrs.get("rel") or "").lower().split())
                if (attrs.get("target") or "").lower() != "_blank" or not {"noopener", "noreferrer", "nofollow"} <= rel:
                    self.errors.append("External a requires _blank and noopener noreferrer nofollow")
            self.current_link = {"href": href, "anchor": "", "section": self.current_section}
        else:
            self.semantic.append("<" + tag + json.dumps(sorted(attrs.items()), ensure_ascii=False) + ">")
        if tag == "img" and any(not nonempty(attrs.get(k)) for k in ("src", "alt", "title")):
            self.errors.append("Every img requires nonempty src/alt/title")
        if tag == "th" and attrs.get("scope") not in ("col", "row", "colgroup", "rowgroup"):
            self.errors.append("Every th requires a valid scope")
        if tag not in VOID:
            if tag == "p" and "p" in self.stack:
                self.errors.append("Nested p is invalid HTML")
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in BLOCK:
            self.text_parts.append(" ")
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"Mismatched closing tag: {tag}")
        else:
            self.stack.pop()
        if tag == "a":
            if self.current_link is not None:
                self.current_link["anchor"] = normalize(self.current_link["anchor"])
                if not self.current_link["anchor"]:
                    self.errors.append("Empty anchor text")
                self.links.append(self.current_link)
                self.current_link = None
        else:
            self.semantic.append("</" + tag + ">")
        if tag == "h2" and self.h2_buffer is not None:
            self.h2_texts.append(normalize("".join(self.h2_buffer)))
            self.h2_buffer = None

    def handle_data(self, data):
        self.text_parts.append(data)
        self.semantic.append(data)
        if self.h2_buffer is not None:
            self.h2_buffer.append(data)
        if self.current_link is not None:
            self.current_link["anchor"] += data

    def handle_comment(self, data):
        self.errors.append("HTML comments are not article content")

    def handle_decl(self, decl):
        self.errors.append("HTML document declarations are not body fragments")

    def finish(self):
        self.close()
        if self.stack:
            self.errors.append("Unclosed HTML tags")
        for link in self.links:
            if link["href"].startswith("#") and link["href"][1:] not in self.ids:
                self.errors.append("Broken in-page anchor")
        self.text = normalize("".join(self.text_parts))
        self.semantic_text = normalize("".join(self.semantic))
        return self


def normalize(text):
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_body(body, profile):
    parser = BodyParser(profile)
    parser.feed(body)
    return parser.finish()


def validate_article(article, profile=None, editorial=True):
    profile = profile or load(CONFIG)
    errors = []
    if not isinstance(article, dict):
        return ["Article must be an object"]
    missing = [k for k in REQUIRED if k not in article]
    errors.extend("Missing field: " + k for k in missing)
    errors.extend("Unexpected output field: " + k for k in article if k not in REQUIRED + OPTIONAL)
    for key in REQUIRED:
        if key != "tags" and not nonempty(article.get(key)):
            errors.append(f"Nonempty string required: {key}")
    if missing or any(not isinstance(article.get(k), str) for k in REQUIRED if k != "tags"):
        return errors
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", article["url"]):
        errors.append("url must be a lowercase hyphenated slug")
    for key in ("meta description", "summary"):
        if utf16_length(article[key]) > 160:
            errors.append(f"{key} exceeds 160 UTF-16 characters")
    if article["blog"] not in set(profile["blogs"].values()):
        errors.append("Unknown blog name")
    if article["author"] != profile["author"]:
        errors.append("Unexpected author")
    tags = article.get("tags")
    allowed_tags = {row["tag"] for row in profile["categories"]}
    if not isinstance(tags, list) or not tags or any(not isinstance(x, str) or x not in allowed_tags for x in tags):
        errors.append("tags must contain registered category tags")
    elif len(tags) != len(set(tags)):
        errors.append("Duplicate tags")
    for key in ("template", "reviewer"):
        if key in article and not nonempty(article[key]):
            errors.append(f"Nonempty optional field required: {key}")
    if "related_products" in article and (not isinstance(article["related_products"], list) or any(not nonempty(x) for x in article["related_products"])):
        errors.append("related_products must be a string array")
    body = article["html代码"]
    if PLACEHOLDER.search(json.dumps(article, ensure_ascii=False)):
        errors.append("Unresolved content placeholder")
    if re.search(r"preview_theme_id=|preview_key=", body, re.I):
        errors.append("Preview URL in content")
    try:
        parsed = parse_body(body, profile)
        errors.extend(parsed.errors)
        if len(parsed.h2_ids) < 4:
            errors.append("At least four substantive H2 sections required")
        if any(not h for h in parsed.h2_texts):
            errors.append("Empty H2")
        if any(not h for h in parsed.h2_ids):
            errors.append("H2 requires section id")
        if editorial:
            words = word_count(parsed.text)
            if not profile["word_count"]["min"] <= words <= profile["word_count"]["max"]:
                errors.append(f"English word count {words} outside configured range")
            # An image-only first paragraph is an optional banner, not an introduction.
            intro = re.split(r"<h2\b", body, flags=re.I)[0]
            meaningful = sum(bool(normalize(re.sub(r"<[^>]*>", " ", p)))
                             for p in re.findall(r"<p\b[^>]*>(.*?)</p>", intro, re.I | re.S))
            if meaningful != 2:
                errors.append("Exactly two substantive introduction paragraphs required")
        own_path = "/" + article["url"]
        for link in parsed.links:
            if is_internal(link["href"], profile) and urlsplit(link["href"]).path.rstrip("/").endswith(own_path):
                errors.append("Self-link to current article")
    except (ValueError, TypeError) as exc:
        errors.append(f"HTML parse failed: {exc}")
    return errors


def validate_outline(outline, profile):
    require(isinstance(outline, dict), "outline must be an object")
    for key in ("title", "type", "fx", "blog", "core_term", "answer", "scope"):
        require(nonempty(outline.get(key)), f"outline missing {key}")
    typ = outline["type"]
    require(typ in TYPE_FX, "Unknown content type")
    prefix, count = TYPE_FX[typ]
    require(outline["fx"] in {prefix + str(i) for i in range(1, count + 1)}, "FX/type namespace mismatch")
    require(outline["blog"] == profile["blogs"][typ], "Type/blog mismatch")
    tags = outline.get("tags")
    registered = {x["tag"] for x in profile["categories"]}
    require(isinstance(tags, list) and tags and all(isinstance(x, str) and x in registered for x in tags), "Invalid outline tags")
    require(len(tags) == len(set(tags)), "Duplicate outline tags")
    sections = outline.get("sections")
    require(isinstance(sections, list) and len(sections) >= 4, "Outline needs at least four sections")
    ids = []
    for section in sections:
        require(isinstance(section, dict), "Section must be an object")
        for key in ("id", "h2", "question", "new_information", "boundary"):
            require(nonempty(section.get(key)), f"Section missing {key}")
        require(re.fullmatch(r"[a-z][a-z0-9-]*", section["id"]), "Invalid section id")
        require(isinstance(section.get("claim_ids"), list) and all(nonempty(x) for x in section["claim_ids"]), "claim_ids must be strings")
        ids.append(section["id"])
    require(len(ids) == len(set(ids)), "Duplicate section ids")


def validate_evidence(evidence, body=None, outline=None):
    require(isinstance(evidence, list) and evidence, "Evidence ledger must be a nonempty array")
    ids = []
    for row in evidence:
        require(isinstance(row, dict), "Claim must be an object")
        for key in ("id", "claim", "reason"):
            require(nonempty(row.get(key)), f"Claim missing {key}")
        ids.append(row["id"])
        if body is None:
            require(row.get("status") in ("supported", "pending"), "Invalid planning claim status")
            continue
        require(row.get("status") == "supported", f"Unsupported claim: {row['id']}")
        require(nonempty(row.get("body_excerpt")) and normalize(row["body_excerpt"]) in normalize(body), "Claim excerpt not found in current body")
        require(isinstance(row.get("sources"), list) and row["sources"], "Supported claim needs sources")
        for source in row["sources"]:
            require(isinstance(source, dict), "Source must be an object")
            require(nonempty(source.get("path")) or (valid_url(source.get("url", ""), False) and source.get("url", "").startswith(("http://", "https://"))), "Source requires real URL or snapshot path")
            for key in ("locator", "supports"):
                require(nonempty(source.get(key)), "Source needs locator and claim-specific support")
            require(valid_time(source.get("checked_at")), "Source requires timezone-aware checked_at")
    require(len(ids) == len(set(ids)), "Duplicate claim ids")
    if outline:
        require(all(cid in ids for sec in outline["sections"] for cid in sec["claim_ids"]), "Outline references missing claim")


def validate_links(ledger, parsed, profile):
    require(isinstance(ledger, list), "links must be an array")
    available = []
    for row in ledger:
        require(isinstance(row, dict), "Link entry must be an object")
        require(row.get("kind") in ("internal", "external", "pending"), "Invalid link kind")
        for key in ("anchor", "section", "purpose"):
            require(nonempty(row.get(key)), "Link entry missing " + key)
        if row["kind"] == "pending":
            require(row.get("href") == "", "Pending link must have empty href")
            continue
        require(valid_url(row.get("href", "")), "Invalid link href")
        require(row.get("verification") == "verified" and valid_time(row.get("checked_at")), "Unverified HTML link")
        require(nonempty(row.get("source_locator")), "Link needs actual inspected target location")
        expected = "internal" if is_internal(row["href"], profile) else "external"
        require(row["kind"] == expected, "Link kind/host mismatch")
        available.append((row["href"], normalize(row["anchor"]), row["section"]))
    for link in parsed.links:
        key = (link["href"], normalize(link["anchor"]), link["section"])
        require(key in available, "HTML link missing verified ledger entry: " + link["href"])
        available.remove(key)
    require(not available, "Ledger contains links not present in final HTML")


def validate_review(review):
    require(isinstance(review, dict), "review must be an object")
    require(review.get("decision") == "pass", "Final review has not passed")
    require(nonempty(review.get("reviewer")), "Review identity required")
    require(review.get("hard_issues") == [], "Hard issues must be explicitly empty")
    scores = review.get("scores", {})
    rationales = review.get("rationales", {})
    for dim in DIMENSIONS:
        val = scores.get(dim)
        require(type(val) in (int, float) and math.isfinite(val) and 7 <= val <= 10, "Missing/low/nonfinite review score: " + dim)
        require(nonempty(rationales.get(dim)), "Missing score rationale: " + dim)
    require(sum(scores[d] for d in DIMENSIONS[:4]) / 4 >= 8, "Aggregate E-E-A-T below 8")
    coverage = review.get("claim_coverage", {})
    require(coverage.get("complete") is True and nonempty(coverage.get("reason")), "Semantic claim coverage review required")
    require(all(review.get("checks", {}).get(k) is True for k in CHECKS), "Final semantic checks incomplete")


def read_run(run_dir):
    run_dir = Path(run_dir)
    state = load(run_dir / "run.json")
    require(state.get("schema_version") == 1, "Unsupported run version")
    require(isinstance(state.get("stages"), dict), "Malformed stage state")
    return run_dir, state


def article_from_run(run_dir):
    metadata = load(run_dir / "metadata.json")
    require(isinstance(metadata, dict) and "html代码" not in metadata, "metadata must not duplicate body")
    article = copy.deepcopy(metadata)
    article["html代码"] = (run_dir / "body.html").read_text(encoding="utf-8-sig")
    return article


def digest(run_dir, stage, profile):
    files = {"outline": ("outline.json",),
             "draft": ("outline.json", "metadata.json", "evidence.json", "body.html"),
             "links": ("outline.json", "metadata.json", "evidence.json", "body.html", "links.json"),
             "review": ("outline.json", "metadata.json", "evidence.json", "body.html", "links.json", "review.json")}[stage]
    chunks = [("config", json.dumps(profile, sort_keys=True, ensure_ascii=False))]
    for name in files:
        text = (run_dir / name).read_text(encoding="utf-8-sig")
        if stage == "draft" and name == "body.html":
            text = parse_body(text, profile).semantic_text
        elif name.endswith(".json"):
            text = json.dumps(json.loads(text), sort_keys=True, ensure_ascii=False, allow_nan=False)
        chunks.append((name, text))
    return hashlib.sha256(json.dumps(chunks, ensure_ascii=False).encode("utf-8")).hexdigest()


def fresh(run_dir, state, stage, profile):
    record = state["stages"].get(stage)
    if not record:
        return False
    try:
        return record["digest"] == digest(run_dir, stage, profile)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def check_files(run_dir, stage, profile):
    outline = load(run_dir / "outline.json")
    validate_outline(outline, profile)
    evidence = load(run_dir / "evidence.json")
    if stage == "outline":
        validate_evidence(evidence, outline=outline)
        return
    article = article_from_run(run_dir)
    errors = validate_article(article, profile)
    require(not errors, "; ".join(errors))
    require(article["blog title"] == outline["title"] and article["blog"] == outline["blog"] and article["tags"] == outline["tags"], "Metadata/outline mismatch")
    parsed = parse_body(article["html代码"], profile)
    require(parsed.h2_ids == [x["id"] for x in outline["sections"]], "Body H2 order differs from outline")
    require(parsed.h2_texts == [x["h2"] for x in outline["sections"]], "Body H2 text differs from outline")
    validate_evidence(evidence, parsed.text, outline)
    if stage in ("links", "review"):
        validate_links(load(run_dir / "links.json"), parsed, profile)
    if stage == "review":
        validate_review(load(run_dir / "review.json"))


def init_run(run_dir, title):
    run_dir = Path(run_dir)
    require(nonempty(title), "Title must be nonempty")
    require(not (run_dir / "run.json").exists(), "Run already exists; use status to resume")
    write_json(run_dir / "run.json", {"schema_version": 1, "input": {"title": title},
               "created_at": now(), "content_revisions": 0, "stages": {}})


def seal(run_dir, stage, profile):
    run_dir, state = read_run(run_dir)
    index = STAGES.index(stage)
    for prior in STAGES[:index]:
        require(fresh(run_dir, state, prior, profile), f"Stale/missing {prior}; reseal from responsible stage")
    check_files(run_dir, stage, profile)
    current_digest = digest(run_dir, stage, profile)
    last_draft = state.get("last_draft_digest")
    if stage == "draft" and last_draft and last_draft != current_digest:
        revisions = state.get("content_revisions", 0) + 1
        require(revisions <= profile["max_content_revisions"], "Content revision budget exhausted; report blocker")
        state["content_revisions"] = revisions
    # Idempotent reseals should not destroy downstream valid review.
    if state["stages"].get(stage, {}).get("digest") == current_digest:
        return
    if stage == "draft":
        state["last_draft_digest"] = current_digest
    for downstream in STAGES[index + 1:]:
        state["stages"].pop(downstream, None)
    state["stages"][stage] = {"digest": current_digest, "sealed_at": now()}
    write_json(run_dir / "run.json", state)


def export_run(run_dir, out, profile):
    run_dir, state = read_run(run_dir)
    require(all(fresh(run_dir, state, s, profile) for s in STAGES), "Cannot export stale/unreviewed content")
    check_files(run_dir, "review", profile)
    destination = Path(out).resolve()
    protected = {run_dir.resolve() / f for f in ("run.json", "outline.json", "metadata.json", "evidence.json", "body.html", "links.json", "review.json")}
    require(destination not in protected, "Export must not overwrite internal artifacts")
    write_json(destination, [article_from_run(run_dir)])
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--title", required=True)
    init.add_argument("--run-dir", required=True, type=Path)
    sealer = sub.add_parser("seal")
    sealer.add_argument("run_dir", type=Path)
    sealer.add_argument("stage", choices=STAGES)
    status = sub.add_parser("status")
    status.add_argument("run_dir", type=Path)
    exporter = sub.add_parser("export")
    exporter.add_argument("run_dir", type=Path)
    exporter.add_argument("--out", type=Path, required=True)
    validator = sub.add_parser("validate")
    validator.add_argument("json_file", type=Path)
    args = parser.parse_args(argv)
    try:
        profile = load(args.profile)
        if args.command == "init":
            init_run(args.run_dir, args.title)
        elif args.command == "seal":
            seal(args.run_dir, args.stage, profile)
        elif args.command == "status":
            directory, state = read_run(args.run_dir)
            print(json.dumps({s: fresh(directory, state, s, profile) for s in STAGES}))
        elif args.command == "export":
            print(str(export_run(args.run_dir, args.out, profile)))
        else:
            data = load(args.json_file)
            require(isinstance(data, list) and data, "Publisher output must be a nonempty array")
            all_errors = [f"[{i}] {err}" for i, article in enumerate(data) for err in validate_article(article, profile)]
            require(not all_errors, "\n".join(all_errors))
            print("Publisher content contract passed; semantic evidence is checked separately during run export.")
        return 0
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
