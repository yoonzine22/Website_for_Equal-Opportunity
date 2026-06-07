import json
import re

with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Clean up headers/footers
text = re.sub(r"저작권자 Ⓒ 한국대학교육협의회\s*무단전재 및 재배포 금지\s*-\s*\d+\s*-", "", text)
text = re.sub(r"--- Page \d+ ---", "", text)

sections = re.split(r"□\d\s*(수시모집|정시모집)[^\n]*", text)

results = []

regions = ["서울", "경기", "인천", "강원", "대전", "충남", "충북", "세종", "광주", "전남", "전북", "대구", "경북", "부산", "울산", "경남", "제주"]

for i in range(1, len(sections), 2):
    period = "수시" if "수시" in sections[i] else "정시"
    content = sections[i+1]
    
    parts = re.split(r"지역\s+대학\s+전형유형\s+전형명\s*(?:모집 군\s*)?모집인원\s+전형방법\s+비고", content)
    for part in parts[1:]:
        lines = [l.strip() for l in part.split("\n") if l.strip()]
        
        # Combine lines properly
        entries = []
        current_entry = ""
        
        for line in lines:
            if line.startswith("❙") or "지원자격" in line or "해당하는 사람" in line or line.startswith("라.") or line.startswith("1)") or line.startswith("2)") or line.startswith("3)") or "검정고시 출신자" in line:
                continue
                
            is_start = False
            for r in regions:
                if line.startswith(r) and "대" in line[:15]:
                    is_start = True
                    break
            
            if not is_start and re.match(r"^[가-힣]{2,10}(대학교|대|교대|여대)\s", line):
                is_start = True
                
            if is_start:
                if current_entry:
                    entries.append(current_entry)
                current_entry = line
            else:
                if current_entry:
                    current_entry += " " + line
                else:
                    current_row = line # this should be current_entry
                    current_entry = line
                    
        if current_entry:
            entries.append(current_entry)

        for entry in entries:
            entry = re.sub(r'\s+', ' ', entry).strip()
            
            region = ""
            for r in regions:
                if entry.startswith(r):
                    region = r
                    entry = entry[len(r):].strip()
                    break
                    
            uni_match = re.match(r"^([가-힣]+대(학교|학)?(\([가-힣]+\))?)\s+", entry)
            if uni_match:
                uni = uni_match.group(1)
                entry = entry[len(uni_match.group(0)):].strip()
            else:
                uni = ""
                
            # Now we look for Type: 교과, 종합, 실기, 수능 등
            # Fix glued text
            entry = re.sub(r'^(교과|종합|수능|실기/실적|실기)(기초|기회|저소득|사회적|고른기회)', r'\1 \2', entry)

            type_match = re.match(r"^(교과|종합|실기/실적|실기|수능|기타)\s+", entry)
            if type_match:
                type_ = type_match.group(1)
                entry = entry[len(type_match.group(0)):].strip()
            else:
                type_ = ""
                
            match = re.search(r"([가-힣0-9A-Za-z+(), ]+)\s+(\d+|\(\d+\))\s+(.+)", entry)
            if match:
                name = match.group(1).strip()
                num = match.group(2).strip()
                method_and_note = match.group(3).strip()
                
                note_match = re.search(r"(수능최저.*|수능 최저.*)$", method_and_note)
                if note_match:
                    note = note_match.group(1)
                    method = method_and_note[:note_match.start()].strip()
                else:
                    method = method_and_note
                    note = ""

                results.append({
                    "period": period,
                    "region": region,
                    "university": uni,
                    "type": type_,
                    "name": name,
                    "recruitNum": num,
                    "method": method,
                    "note": note
                })
            else:
                results.append({
                    "period": period,
                    "region": region,
                    "university": uni,
                    "type": type_,
                    "name": entry,
                    "recruitNum": "",
                    "method": "",
                    "note": ""
                })

# Fix empty regions by carrying forward
current_reg = "미분류"
for r in results:
    if r["region"]:
        current_reg = r["region"]
    else:
        r["region"] = current_reg

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
    
print(f"Successfully processed {len(results)} records.")
