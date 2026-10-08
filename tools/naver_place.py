"""네이버 통합검색의 장소 결과(상호·업종·도로명주소·지번·영업상태)를 출력한다.
사용: python3 tools/naver_place.py "지역 상호"   예: "사당 미소네"
결과가 없으면 검색어를 바꿔(동네명 추가·삭제) 다시 시도한다."""
import json, re, subprocess, sys, urllib.parse
u = "https://search.naver.com/search.naver?query=" + urllib.parse.quote(sys.argv[1])
h = subprocess.run(["curl", "-sSL", "--max-time", "20", "-A", "Mozilla/5.0", u], capture_output=True).stdout.decode("utf-8", "ignore")
m = re.search(r"__APOLLO_STATE__ = (\{.*?\});\s*\n", h, re.S)
if not m:
    print("(장소 결과 없음)"); sys.exit()
seen = set()
for k, v in json.loads(m.group(1)).items():
    if isinstance(v, dict) and v.get("roadAddress") is not None and v.get("name"):
        key = (v["name"], v["roadAddress"])
        if key in seen: continue
        seen.add(key)
        st = (v.get("newBusinessHours") or {}).get("status", "") if isinstance(v.get("newBusinessHours"), dict) else ""
        name = re.sub("</?mark>", "", v["name"])
        print(f"{k.split(':')[0]} | {name} | {v.get('category','')} | {v.get('roadAddress','')} | {v.get('address','') or v.get('commonAddress','')} | {st}")
