"""Fetch the Golf Bunch targets sheet and write targets.json for the scorecard app."""
import json, re, sys, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

URL = "https://gdwilder.linkpro.net/GolfBunchTargets_files/sheet001.htm"

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag=="tr": self.row=[]
        elif tag=="td" and self.row is not None: self.cell=[]
    def handle_endtag(self, tag):
        if tag=="td" and self.cell is not None:
            self.row.append(re.sub(r"\s+"," ","".join(self.cell)).strip()); self.cell=None
        elif tag=="tr" and self.row is not None:
            self.rows.append(self.row); self.row=None
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

def parse(html):
    p=Rows(); p.feed(html); out=[]
    for c in p.rows:
        if len(c)<3 or "," not in c[0]: continue
        last, first = [s.strip() for s in c[0].split(",",1)]
        try: t=float(c[2]); t=int(t) if t.is_integer() else t
        except ValueError: t=None
        out.append([f"{first} {last}".strip(), t])
    return out

if __name__=="__main__":
    src = sys.argv[1] if len(sys.argv)>1 else None
    def status(msg):
        open("targets-status.txt","w").write(f"{datetime.now(timezone.utc).isoformat(timespec='minutes')}  {msg}\n")
        print(msg)
    try:
        if src: html=open(src,encoding="utf-8",errors="replace").read()
        else:
            req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15","Accept":"text/html,*/*"})
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read(); code=r.status
            html=raw.decode("windows-1252",errors="replace")
    except Exception as e:
        status(f"FETCH FAILED: {type(e).__name__}: {e}"); sys.exit(1)
    players=parse(html)
    if len(players)<5:
        status(f"PARSE FAILED: found {len(players)} players in {len(html)} chars. Start: {html[:300]!r}"); sys.exit(1)
    try: old=json.load(open("targets.json"))
    except Exception: old={}
    if old.get("list")==players: status(f"OK: {len(players)} players, no change"); sys.exit(0)
    json.dump({"updated":datetime.now(timezone.utc).isoformat(timespec="minutes"),"source":URL,"list":players},open("targets.json","w"),indent=1)
    status(f"OK: wrote {len(players)} players")
