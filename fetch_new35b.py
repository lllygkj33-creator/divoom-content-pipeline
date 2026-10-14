#!/usr/bin/env python3
"""只走 curl 抓取新增 35 篇；幂等：已存在（按 URL 前缀匹配）就跳过。"""
from __future__ import annotations
import concurrent.futures as cf, pathlib, re, subprocess, sys, time
sys.path.insert(0, '.')
from fetch_bodies import body_html, to_md

ROOT = pathlib.Path('.'); DST = ROOT/'work'/'bodies'
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
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
        existing="\n".join(f.read_text(encoding='utf-8', errors='replace')[:200] for f in d.glob('*.md'))
        for u in urls:
            if u in existing:   # 幂等：已抓过
                continue
            todo.append((col,u,d))
    print(f"待抓 {len(todo)} 篇（已跳过已存在的）")
    if not todo:
        print("全部已存在"); return
    def work(job):
        col,u,d=job
        for a in range(3):
            p=subprocess.run(["curl","-sS","-L","--max-time","60","--compressed","-A",UA,u],
                             capture_output=True,text=True)
            if p.returncode==0 and len(p.stdout)>5000:
                md,_=to_md(body_html(p.stdout))
                if len(md)>800:
                    # 临时名，稍后统一编号
                    (d/f"_new-{slug(u)}.md").write_text(f"<!-- 来源URL: {u} -->\n\n{md}\n",encoding='utf-8')
                    return (col,u,"ok",len(md))
            time.sleep(2+2*a)
        return (col,u,"FAIL",0)
    ok=fail=0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for col,u,st,ln in ex.map(work,todo):
            if st=="ok": ok+=1
            else: fail+=1; print(f"  ! {st} {col} {u}")
    print(f"完成 ok={ok} fail={fail}")
    # 统一重编号（去掉 _new- 前缀并排序）
    for col in parse():
        d=DST/col
        fs=sorted(d.glob('*.md'), key=lambda f:(f.name.startswith('_new-'), f.name))
        for i,f in enumerate(fs,1):
            base=f.name.split('-',1)[1] if '-' in f.name else f.name
            tgt=d/f"{i:02d}-{base}"
            if f!=tgt: f.rename(tgt)
        print(f"  {col}: {len(list(d.glob('*.md')))} 篇")

if __name__=="__main__": main()
