"""고슐랭 빌드: data/ 안의 식당 파일을 읽어 검증하고 index.html을 만든다.
실행: python3 build.py   (외부 패키지 필요 없음)
"""
import csv, datetime, html, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

KEYS = ["상호", "상태", "등급", "등급제안", "시도", "시군구", "동네", "주소", "장르",
        "대표메뉴", "태그", "분위기유형", "가점", "감점", "진입근거", "개업연도",
        "출처수", "최종확인일"]
STATUS = ["선정", "답사 예정", "후보", "보류", "탈락", "폐업 확인"]
TAGS = {"술술": "🍶", "한방": "🎯", "이것저것": "🍱", "푸짐": "🥘", "사주기좋은": "💰",
        "해장": "🍲", "현지그대로": "🗾", "분위기": "🏮", "노포": "⏳", "인생기준": "⭐"}
GRADE_LABEL = {"1": "근처면 가볼 만하다", "2": "이거 먹으러 가볼 만하다", "3": "맛집 중의 맛집"}


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError("머리말(--- ... ---)이 없음")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    sections, cur = {}, None
    for line in m.group(2).splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    meta["_sections"] = {k: "\n".join(v).strip() for k, v in sections.items()}
    meta["_file"] = str(path.relative_to(ROOT))
    return meta


def validate(items):
    errors, warns = [], []
    seen = Counter()
    for it in items:
        f = it["_file"]
        for k in KEYS:
            if k not in it:
                errors.append(f"{f}: '{k}' 칸 없음")
        if not it.get("상호"):
            errors.append(f"{f}: 상호 비어 있음")
        if it.get("상태") not in STATUS:
            errors.append(f"{f}: 상태 '{it.get('상태')}' 는 허용값이 아님 ({', '.join(STATUS)})")
        g = it.get("등급", "")
        if g and g not in GRADE_LABEL:
            errors.append(f"{f}: 등급 '{g}' 는 1·2·3 중 하나여야 함")
        if g and it.get("상태") != "선정":
            errors.append(f"{f}: 선정되지 않은 곳에 등급이 있음")
        for t in it["_tags"]:
            if t not in TAGS:
                errors.append(f"{f}: 태그 '{t}' 는 criteria.md에 없는 태그")
        y = it.get("개업연도", "")
        if y and y != "확인 필요" and not re.fullmatch(r"\d{4}", y):
            errors.append(f"{f}: 개업연도는 4자리 연도 또는 '확인 필요'여야 함")
        src = it.get("출처수", "0")
        if not src.isdigit():
            errors.append(f"{f}: 출처수는 숫자여야 함")
        elif it.get("상태") == "후보" and int(src) < 2:
            warns.append(f"{f}: 후보인데 출처가 {src}곳 (2곳 이상 필요)")
        seen[(it.get("시도"), it.get("상호"))] += 1
    for (sido, name), c in seen.items():
        if c > 1:
            errors.append(f"중복: {sido} {name} ({c}개 파일)")
    return errors, warns


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"(?<![\"'>])(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_block(s):
    out, ul = [], False
    for line in s.splitlines():
        if line.startswith("- "):
            if not ul:
                out.append("<ul>"); ul = True
            out.append(f"<li>{md_inline(line[2:])}</li>")
        else:
            if ul:
                out.append("</ul>"); ul = False
            if line.strip():
                out.append(f"<p>{md_inline(line)}</p>")
    if ul:
        out.append("</ul>")
    return "".join(out)


def main():
    files = sorted(p for p in DATA.rglob("*.md"))
    items, errors = [], []
    for p in files:
        try:
            it = parse(p)
        except ValueError as e:
            errors.append(f"{p.relative_to(ROOT)}: {e}")
            continue
        it["_tags"] = [t.strip() for t in it.get("태그", "").split(",") if t.strip()]
        items.append(it)
    e2, warns = validate(items)
    errors += e2

    this_year = datetime.date.today().year

    def age_band(y):
        if re.fullmatch(r"\d{4}", y or ""):
            age = this_year - int(y)
            if age >= 30:
                return f"{age // 10 * 10}년+"
        return ""

    records = []
    for it in items:
        sec = it["_sections"]
        records.append({
            "name": it.get("상호", ""), "status": it.get("상태", ""),
            "grade": it.get("등급", ""), "gradeSug": it.get("등급제안", ""),
            "sido": it.get("시도", ""), "sgg": it.get("시군구", ""), "dong": it.get("동네", ""),
            "addr": it.get("주소", ""), "genre": it.get("장르", ""), "menu": it.get("대표메뉴", ""),
            "tags": it["_tags"], "mood": it.get("분위기유형", ""),
            "plus": it.get("가점", ""), "minus": it.get("감점", ""),
            "basis": it.get("진입근거", ""), "year": it.get("개업연도", ""),
            "src": it.get("출처수", ""), "age": age_band(it.get("개업연도", "")), "checked": it.get("최종확인일", ""),
            "note": md_block(sec.get("고민수 한줄평", "")),
            "memo": md_block(sec.get("조사 메모", "")),
            "sources": md_block(sec.get("출처", "")),
        })

    tpl = (ROOT / "page_template.html").read_text(encoding="utf-8")
    page = (tpl.replace("{{DATA}}", json.dumps(records, ensure_ascii=False).replace("</", "<\\/"))
               .replace("{{TAGS}}", json.dumps(TAGS, ensure_ascii=False))
               .replace("{{STATUS}}", json.dumps(STATUS, ensure_ascii=False))
               .replace("{{GRADES}}", json.dumps(GRADE_LABEL, ensure_ascii=False)))
    (ROOT / "index.html").write_text(page, encoding="utf-8")

    # 지도용 CSV (구글 내 지도 가져오기용): 주소가 확인된 곳만, 탈락·폐업 확인 제외
    rows = sorted((r["name"], r["addr"]) for r in records
                  if r["addr"] and r["addr"] != "확인 필요" and r["status"] not in ("탈락", "폐업 확인"))
    with open(ROOT / "map.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["상호", "주소"])
        w.writerows(rows)

    c = Counter(r["status"] for r in records)
    print(f"식당 {len(records)}곳 | " + " · ".join(f"{s} {c[s]}" for s in STATUS if c[s]))
    for w in warns:
        print("경고:", w)
    if errors:
        for e in errors:
            print("오류:", e)
        print(f"검증 실패: 오류 {len(errors)}건")
        sys.exit(1)
    print(f"검증 통과: 오류 0건 → index.html · map.csv({len(rows)}곳) 생성 완료")


if __name__ == "__main__":
    main()
