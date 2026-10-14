#!/usr/bin/env python3
"""Fetch Divoom PDP (product detail) pages read-only -> raw/pdp/<handle>.html"""
import pathlib, subprocess, time

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "raw" / "pdp"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    handles = [l.strip() for l in (ROOT / "pdp_urls.txt").read_text().split() if l.strip()]
    ok = fail = 0
    for url in handles:
        h = url.rsplit("/", 1)[-1]
        dest = OUT / f"{h}.html"
        if dest.exists() and dest.stat().st_size > 50000:
            print(f"  = {h} (cached)"); ok += 1; continue
        for attempt in range(3):
            p = subprocess.run(["curl", "-sS", "-L", "--max-time", "90", "--compressed",
                                "-A", UA, "-o", str(dest), "-w", "%{http_code}", url],
                               capture_output=True, text=True)
            code = p.stdout.strip()
            if p.returncode == 0 and code == "200" and dest.stat().st_size > 50000:
                print(f"  + {h} {code} {dest.stat().st_size // 1024}KB"); ok += 1; break
            print(f"  ! {h} attempt {attempt+1}: code={code} {p.stderr.strip()[:80]}")
            time.sleep(2 + 2 * attempt)
        else:
            fail += 1
        time.sleep(0.3)
    print(f"\ndone: {ok} ok, {fail} failed")

if __name__ == "__main__":
    main()
