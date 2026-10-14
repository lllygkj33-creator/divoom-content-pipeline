#!/usr/bin/env python3
"""用 fcrawl（浏览器路径）补齐剩余新增文章；fcrawl 输出经 clean_fcrawl 规则清洗。"""
from __future__ import annotations
import pathlib, re, subprocess, sys, time
sys.path.insert(0,'.')
from clean_bodies import clean

FCRAWL = str(pathlib.Path.home()/'.local'/'bin'/'fcrawl')
ROOT=pathlib.Path('.'); DST=ROOT/'work'/'bodies'
ANALYSIS = pathlib.Path.home()/'Downloads'/'Divoom-Momcozy-扩样与正文节奏分析.md'

def slug(u): return re.sub(r"[^a-z0-9]+","-",u.rsplit("/",1)[-1].lower()).strip("-")[:60]
def parse():
    out={}; cur=None
    for line in ANALYSIS.read_text(encoding='utf-8').split('\n'):
        m=re.match(r'^###\s+(科技与信息|帮助与提示|产品对比|购买指南|设置与使用)', line)
        if m: cur=m.group(1); out[cur]=[]
        elif cur and line.strip().startswith('- http'): out[cur].append(line.strip()[2:].strip())
    return out

def main():
    todo=[]
    for col,urls in parse().items():
        d=DST/col; d.mkdir(parents=True,exist_ok=True)
        existing=" ".join(f.read_text(encoding='utf-8',errors='replace')[:300] for f in d.glob('*.md'))
        for u in urls:
            if u in existing: continue
            todo.append((col,u,d))
    print(f"待抓 {len(todo)} 篇（fcrawl）", flush=True)
    ok=fail=0
    for i,(col,u,d) in enumerate(todo,1):
        got=None
        for a in range(3):
            try:
                p=subprocess.run([FCRAWL,u],capture_output=True,text=True,timeout=300)
            except Exception as e:
                print(f"  exec err {e}", flush=True); time.sleep(5); continue
            if p.returncode==0 and len(p.stdout)>1500:
                got=clean(p.stdout); break
            time.sleep(4+4*a)
        if got and len(got)>800:
            (d/f"_new-{slug(u)}.md").write_text(f"<!-- 来源URL: {u} -->\n<!-- 抓取方式: fcrawl -->\n\n{got}\n",encoding='utf-8')
            ok+=1; print(f"[{i}/{len(todo)}] ok {len(got)//1000}K {col} {u.rsplit('/',1)[-1][:40]}", flush=True)
        else:
            fail+=1; print(f"[{i}/{len(todo)}] FAIL {col} {u}", flush=True)
        time.sleep(1)
    print(f"完成 ok={ok} fail={fail}", flush=True)
    for col in parse():
        d=DST/col
        fs=sorted(d.glob('*.md'), key=lambda f:(f.name.startswith('_new-'), f.name))
        for i,f in enumerate(fs,1):
            base=f.name.split('-',1)[1] if '-' in f.name else f.name
            tgt=d/f"{i:02d}-{base}"
            if f!=tgt: f.rename(tgt)
    for col in parse():
        print(f"  {col}: {len(list((DST/col).glob('*.md')))} 篇")

if __name__=="__main__": main()
