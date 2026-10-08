"""Fetch the Golf Bunch targets sheet and write targets.json for the scorecard app."""
import json, re, sys, time, urllib.request
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

def short_names(rows):
    """First name + the fewest letters of the last name needed to tell people apart."""
    out=[]
    for first,last,t in rows:
        others=[l for f,l,_ in rows if f.lower()==first.lower() and l.lower()!=last.lower()]
        k=1
        while k<len(last) and any(o.lower().startswith(last[:k].lower()) for o in others): k+=1
        out.append([f"{first} {last[:k]}." if last else first, t])
    return out

def parse(html):
    p=Rows(); p.feed(html); rows=[]
    for c in p.rows:
        if len(c)<3 or "," not in c[0]: continue
        last, first = [s.strip() for s in c[0].split(",",1)]
        if not first or re.search(r"\d", c[0]): continue          # skip date/heading rows
        if any("qualif" in x.lower() for x in c[1:4]): t=None      # still qualifying: no target yet
        else:
            try: t=float(c[2]); t=int(t) if t.is_integer() else t
            except ValueError: t=None
        rows.append((first,last,t))
    return short_names(rows)

if __name__=="__main__":
    src = sys.argv[1] if len(sys.argv)>1 else None
    def status(msg):
        open("targets-status.txt","w").write(f"{datetime.now(timezone.utc).isoformat(timespec='minutes')}  {msg}\n")
        print(msg)
    modified=None
    try:
        if src: html=open(src,encoding="utf-8",errors="replace").read()
        else:
            # The host sometimes answers with a bot-check page instead of the sheet; wait and retry.
            for attempt in range(6):
                req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15","Accept":"text/html,*/*","Cache-Control":"no-cache"})
                with urllib.request.urlopen(req,timeout=30) as r:
                    html=r.read().decode("windows-1252",errors="replace")
                    modified=r.headers.get("Last-Modified")
                if "sgcaptcha" not in html and len(parse(html))>=5: break
                print(f"Attempt {attempt+1}: got a bot-check page, retrying"); time.sleep(30*(attempt+1))
    except Exception as e:
        status(f"FETCH FAILED: {type(e).__name__}: {e}"); sys.exit(1)
    players=parse(html)
    if len(players)<5:
        status(f"PARSE FAILED: found {len(players)} players in {len(html)} chars. Start: {html[:300]!r}"); sys.exit(1)
    try: old=json.load(open("targets.json"))
    except Exception: old={}
    from email.utils import parsedate_to_datetime
    sheet_mod=parsedate_to_datetime(modified).isoformat(timespec="minutes") if modified else None
    now=datetime.now(timezone.utc).isoformat(timespec="minutes")
    out={"updated":now,"sheet_modified":sheet_mod,"list":players}
    if old.get("list")==players and old.get("sheet_modified")==sheet_mod and old.get("updated","")[:13]==now[:13]:
        print(f"OK: {len(players)} players, no change"); sys.exit(0)
    json.dump(out,open("targets.json","w"),indent=1)
    status(f"OK: wrote {len(players)} players")
