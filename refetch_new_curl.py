#!/usr/bin/env python3
"""把 fcrawl 来源的正文改用 curl 容器抽取重抓（fcrawl 带回整页）。幂等。"""
from __future__ import annotations
import concurrent.futures as cf, pathlib, re, subprocess, sys, time
sys.path.insert(0,'.')
from fetch_bodies import body_html, to_md
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
ROOT=pathlib.Path('.'); DST=ROOT/'work'/'bodies'
def main():
    todo=[]
    for f in sorted(DST.rglob('*.md')):
        t=f.read_text(encoding='utf-8',errors='replace')
        if '抓取方式: fcrawl' not in t: continue
        m=re.search(r'<!--\s*来源URL:\s*(\S+?)\s*-->',t)
        if m: todo.append((f,m.group(1)))
    print(f'待重抓 {len(todo)} 篇（curl）',flush=True)
    def work(job):
        f,u=job
        for a in range(3):
            p=subprocess.run(["curl","-sS","-L","--max-time","60","--compressed","-A",UA,u],
                             capture_output=True,text=True)
            if p.returncode==0 and len(p.stdout)>5000:
                md,_=to_md(body_html(p.stdout))
                if len(md)>800:
                    f.write_text(f"<!-- 来源URL: {u} -->\n\n{md}\n",encoding='utf-8')
                    return (u,"ok",len(md))
            time.sleep(2+2*a)
        return (u,"FAIL",0)
    ok=fail=0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for u,st,n in ex.map(work,todo):
            if st=="ok": ok+=1
            else: fail+=1; print(f'  ! {st} {u[-50:]}')
    print(f'完成 ok={ok} fail={fail}')
if __name__=="__main__": main()
