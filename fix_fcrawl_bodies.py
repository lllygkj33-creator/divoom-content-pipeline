#!/usr/bin/env python3
"""修复 fcrawl 来源正文：(1) 已有的按「文章 H1（其后有长段落）」截断；
(2) 内容已被切没的重新用 fcrawl 抓一次再截断。"""
from __future__ import annotations
import pathlib, re, subprocess, sys, time
sys.path.insert(0,'.')
from clean_bodies import clean
FC=pathlib.Path.home()/'.local'/'bin'/'fcrawl'
DST=pathlib.Path('work/bodies')

def article_start(lines):
    for i,l in enumerate(lines):
        if re.match(r'^#\s+\S', l):
            if max((len(x.strip()) for x in lines[i:]), default=0) > 300:
                return i
    return None

def cut(lines):
    i=article_start(lines)
    return "\n".join(lines[i:]) if i is not None else None

def main():
    refetched=fixed=0
    for f in sorted(DST.rglob('*.md')):
        t=f.read_text(encoding='utf-8',errors='replace')
        if '抓取方式: fcrawl' not in t: continue
        m=re.search(r'<!--\s*来源URL:\s*(\S+?)\s*-->',t); u=m.group(1) if m else None
        lines=t.split('\n')
        body=cut(lines)
        if body is not None and len(body)>1500:
            f.write_text(f"<!-- 来源URL: {u} -->\n\n{body.strip()}\n",encoding='utf-8')
            fixed+=1; print(f'  截断 ok  {f.name[:40]} -> {len(body):,}', flush=True); continue
        # 内容不足：重抓
        if not u: continue
        got=None
        for a in range(3):
            p=subprocess.run([str(FC),u],capture_output=True,text=True,timeout=300)
            if p.returncode==0 and len(p.stdout)>1500:
                got=clean(p.stdout); break
            time.sleep(4+4*a)
        if got:
            body=cut(got.split('\n')) or got
            f.write_text(f"<!-- 来源URL: {u} -->\n\n{body.strip()}\n",encoding='utf-8')
            refetched+=1; print(f'  重抓 ok  {f.name[:40]} -> {len(body):,}', flush=True)
        else:
            print(f'  重抓 FAIL {f.name[:40]}', flush=True)
    print(f'截断修复 {fixed} 篇｜重抓修复 {refetched} 篇')

if __name__=='__main__': main()
