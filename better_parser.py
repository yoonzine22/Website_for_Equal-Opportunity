import json
import re

with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r"저작권자 Ⓒ 한국대학교육협의회\s*무단전재 및 재배포 금지\s*-\s*\d+\s*-", "", text)
text = re.sub(r"--- Page \d+ ---", "", text)

sections = re.split(r"(□\d[^□]*)", text)

results = []
regions = ["서울", "경기", "인천", "강원", "대전", "충남", "충북", "세종", "광주", "전남", "전북", "대구", "경북", "부산", "울산", "경남", "제주"]

for section in sections:
    if not section.strip() or not section.startswith("□"):
        continue
        
    lines = section.strip().split("\n")
    header = lines[0].strip()
    
    period = "수시" if "수시" in header else "정시"
    
    track = "일반계열"
    if "제외" not in header and "의치약한수계열" in header:
        track = "의치약한수계열"
    elif "제외" not in header and ("실기" in header or "예체능" in header):
        track = "실기/예체능"
        
    content = "\n".join(lines[1:])
    parts = re.split(r"지역\s+대학\s*(?:모집군|전형유형|모집 군)\s*전형유형\s*전형명\s*(?:모집 군\s*)?모집인원\s*전형방법\s*(?:수능최저학력 기준|비고|수능최저학력\s*기준)?", content)
    
    if len(parts) == 1:
        parts = re.split(r"지역\s+대학.*?전형방법.*?(?:\n|$)", content)
        
    for part in parts[1:]:
        raw_lines = [l.strip() for l in part.split("\n") if l.strip()]
        
        rows = []
        current_row = ""
        for line in raw_lines:
            if line.startswith("❙") or "지원자격" in line or "해당하는 사람" in line or line.startswith("라.") or line.startswith("1)") or line.startswith("2)") or line.startswith("3)") or "검정고시 출신자" in line:
                continue
                
            is_start = False
            for r in regions:
                if line.startswith(r) and "대" in line[:15]:
                    is_start = True
                    break
            if not is_start and re.match(r"^[가-힣]{2,10}(대학교|대|교대|여대)\s", line):
                is_start = True
            if not is_start and re.match(r"^[가-힣]{2,10}(대학교|대|교대|여대)$", line):
                is_start = True
                
            if is_start:
                if current_row:
                    rows.append(current_row)
                current_row = line
            else:
                if current_row:
                    current_row += " " + line
                else:
                    current_row = line
        if current_row:
            rows.append(current_row)

        current_region = "미상"
        
        for row in rows:
            row = re.sub(r'\s+', ' ', row).strip()
            
            for r in regions:
                if row.startswith(r):
                    current_region = r
                    row = row[len(r):].strip()
                    break
                    
            row = re.sub(r'(교과|종합|수능|실기/실적|실기)(기초|기회|저소득|사회적|고른기회|교육|사회배려|농어촌)', r'\1 \2', row)
            
            branch_match = re.match(r"^\([가-힣]+\)(교과|종합|수능|실기)", row)
            if branch_match:
                 row = row.replace(branch_match.group(0), branch_match.group(1))
                 
            uni_match = re.match(r"^([가-힣]+(대학교|대|교대|여대|과기대)(\([가-힣]+\))?)", row)
            if uni_match:
                uni = uni_match.group(1)
                row = row[len(uni_match.group(1)):].strip()
            else:
                if row.startswith("대 "):
                    uni = current_region + "대"
                    row = row[2:].strip()
                else:
                    uni = "미상"
                    
            type_match = re.match(r"^(교과|종합|수능|실기/실적|실기|기타)\s*", row)
            if type_match:
                type_ = type_match.group(1)
                row = row[len(type_match.group(0)):].strip()
            else:
                type_ = ""
                
            m = re.search(r"^(.*?)(?:\s+)?(\d+|\(\d+\))\s+(서류|학생부|교과|면접|실기|수능|1단계|일괄)(.*)$", row)
            
            if m:
                name = m.group(1).strip()
                num = m.group(2).strip()
                method_and_note = (m.group(3) + m.group(4)).strip()
                
                note_match = re.search(r"(국,수|국어|수학|탐|합|등급|수능최저.*|수능 최저.*)", method_and_note)
                if note_match:
                    idx = method_and_note.find(note_match.group(1))
                    if idx > 5:  
                        note = method_and_note[idx:].strip()
                        method = method_and_note[:idx].strip()
                    else:
                        method = method_and_note
                        note = ""
                else:
                    method = method_and_note
                    note = ""
                    
            else:
                m2 = re.search(r"^(.*?)(\d+)\s*(학생부|서류|교과|면접|실기|수능|1단계|일괄)(.*)$", row)
                if m2:
                    name = m2.group(1).strip()
                    num = m2.group(2).strip()
                    method = (m2.group(3) + m2.group(4)).strip()
                    note = ""
                else:
                    name = row
                    num = ""
                    method = ""
                    note = ""

            # PDF 구조상의 계열 정보를 우선 적용하고, 의치약한수계열 블록 내에서는 학과명으로 재분류
            sub_track = track
            full_text = uni + " " + name + " " + method + " " + note
            
            # 수시/정시 상관없이 의약계열 블록에서 나온 데이터이거나, 이름에 학과가 있는 경우 매핑
            if "의치약한수" in track or "의예" in full_text or "치의" in full_text or "약학" in full_text or "한의" in full_text or "수의" in full_text:
                if "의예" in full_text: sub_track = "의예과"
                elif "치의" in full_text: sub_track = "치의예과"
                elif "약학" in full_text: sub_track = "약학과"
                elif "한의" in full_text: sub_track = "한의예과"
                elif "수의" in full_text: sub_track = "수의예과"
                else: sub_track = "의치약한수계열" # 학과 명시가 없는 경우 보존
            
            results.append({
                "period": period,
                "track": sub_track,
                "region": current_region,
                "university": uni,
                "type": type_,
                "name": name if name else row.replace(method, "").replace(note, "").replace(num, "").strip(),
                "recruitNum": num,
                "method": method,
                "note": note
            })

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(results)} rows.")
