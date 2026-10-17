#!/usr/bin/env python3
"""Portable integrity checks; no inference about writing quality."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT.parent


def main():
    errors = []
    skills = ['divoom-article-workflow', 'divoom-outline', 'divoom-draft', 'divoom-links']
    for name in skills:
        file = SKILLS / name / 'SKILL.md'
        if not file.exists():
            errors.append('Missing skill: ' + name)
            continue
        text = file.read_text(encoding='utf-8')
        if not text.startswith('---\n') or f'name: {name}\n' not in text or not re.search(r'^description: .+', text, re.M):
            errors.append('Invalid frontmatter: ' + name)
        if not (file.parent / 'agents/openai.yaml').exists():
            errors.append('Missing UI metadata: ' + name)
    for path in (file for name in skills for file in (SKILLS / name).rglob('*.md')):
        if 'source' in path.parts:
            continue  # archived examples use original Obsidian paths, not current instruction links
        text = path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', '#')) or '<' in target:
                continue
            destination = (path.parent / target.split('#')[0]).resolve()
            if not destination.exists():
                errors.append(f'Broken instruction reference: {path.name} -> {target}')
    manifest = json.loads((ROOT / 'references/source-manifest.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        file = ROOT / row['file']
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != row['sha256']:
            errors.append('Snapshot mismatch: ' + row['file'])
    for file in ROOT.rglob('*.json'):
        try:
            json.loads(file.read_text(encoding='utf-8'))
        except ValueError as exc:
            errors.append(f'Invalid JSON {file}: {exc}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'PASS: {len(skills)} skills; {len(manifest["files"])} snapshot files; references and JSON intact')
    return 0


if __name__ == '__main__':
    sys.exit(main())
