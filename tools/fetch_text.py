"""기사 원문을 텍스트로 받아 출력한다. 사용: python3 tools/fetch_text.py URL
http:// 주소는 https://로 바꿔 요청한다(이 환경은 http 접속이 막혀 있음)."""
import re, subprocess, sys
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.out = []; s.skip = 0
    def handle_starttag(s, t, a):
        if t in ("script", "style", "noscript"): s.skip += 1
        if t in ("p", "br", "div", "li", "tr", "h1", "h2", "h3"): s.out.append("\n")
    def handle_endtag(s, t):
        if t in ("script", "style", "noscript"): s.skip -= 1
    def handle_data(s, d):
        if not s.skip: s.out.append(d)

url = re.sub(r"^http://", "https://", sys.argv[1])
raw = subprocess.run(["curl", "-sSL", "--max-time", "25", "-A", "Mozilla/5.0", url], capture_output=True).stdout
for enc in ("utf-8", "euc-kr", "cp949"):
    try: text = raw.decode(enc); break
    except UnicodeDecodeError: pass
else:
    text = raw.decode("utf-8", "ignore")
p = P(); p.feed(text)
print("\n".join(l.strip() for l in "".join(p.out).splitlines() if l.strip()))
