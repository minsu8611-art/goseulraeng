"""네이버 뉴스 검색 결과(제목·요약·링크)를 출력한다. 사용: python3 tools/naver_news.py "검색어" [--latest]"""
import html, re, subprocess, sys, urllib.parse
q = sys.argv[1]
sort = "&sort=1" if "--latest" in sys.argv else ""
u = f"https://search.naver.com/search.naver?where=news{sort}&query=" + urllib.parse.quote(q)
h = subprocess.run(["curl", "-sSL", "--max-time", "20", "-A", "Mozilla/5.0", u], capture_output=True).stdout.decode("utf-8", "ignore")
skip = ("naver.com/search", "pstatic", "help.naver", "mkt.naver", "channelPromotion")
for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S):
    link = html.unescape(m.group(1))
    t = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.group(2)))).strip()
    if len(t) > 25 and not any(s in link for s in skip):
        print("-", t[:300], "\n ", link)
