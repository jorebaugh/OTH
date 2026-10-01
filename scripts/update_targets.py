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
    if src: html=open(src,encoding="utf-8",errors="replace").read()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 scorecard-updater"})
        html=urllib.request.urlopen(req,timeout=30).read().decode("windows-1252",errors="replace")
    players=parse(html)
    if len(players)<5: sys.exit(f"Only found {len(players)} players; sheet layout may have changed. Keeping old targets.json.")
    try: old=json.load(open("targets.json"))
    except Exception: old={}
    if old.get("list")==players: print("No change"); sys.exit(0)
    json.dump({"updated":datetime.now(timezone.utc).isoformat(timespec="minutes"),"source":URL,"list":players},open("targets.json","w"),indent=1)
    print(f"Wrote {len(players)} players")
