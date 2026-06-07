import json
import re

with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r"저작권자 Ⓒ 한국대학교육협의회\s*무단전재 및 재배포 금지\s*-\s*\d+\s*-", "", text)
text = re.sub(r"--- Page \d+ ---", "", text)
text = re.sub(r"※ 이 자료는.*?반드시 확인하여야 합니다\s*\.", "", text, flags=re.DOTALL)

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
        
    sub_sections = re.split(r"(\d\.\s*(?:의예과|치의예과|약학과|한의예과|수의예과))", section)
    
    if len(sub_sections) == 1:
        chunks = [("", sub_sections[0])]
    else:
        chunks = []
        if sub_sections[0].strip():
            chunks.append(("", sub_sections[0]))
        for i in range(1, len(sub_sections), 2):
            sub_title = sub_sections[i]
            sub_content = sub_sections[i+1] if i+1 < len(sub_sections) else ""
            chunks.append((sub_title, sub_content))
            
    for sub_title_raw, chunk_content in chunks:
        current_sub_track = track
        if sub_title_raw:
            if "의예" in sub_title_raw: current_sub_track = "의예과"
            elif "치의" in sub_title_raw: current_sub_track = "치의예과"
            elif "약학" in sub_title_raw: current_sub_track = "약학과"
            elif "한의" in sub_title_raw: current_sub_track = "한의예과"
            elif "수의" in sub_title_raw: current_sub_track = "수의예과"
            
        parts = re.split(r"지역\s+대학\s*(?:모집군|전형유형|모집 군)\s*전형유형\s*전형명\s*(?:모집 군\s*)?모집인원\s*전형방법\s*(?:수능최저학력 기준|비고|수능최저학력\s*기준)?", chunk_content)
        
        if len(parts) == 1:
            parts = re.split(r"지역\s+대학.*?전형방법.*?(?:\n|$)", chunk_content)
            
        for part in parts[1:]:
            part = re.sub(r"(수능100.*?)(서울|경기|인천|강원|대전|충남|충북|세종|광주|전남|전북|대구|경북|부산|울산|경남|제주)\s+([가-힣]+대)", r"\1\n\2 \3", part)
            part = re.sub(r"([가-힣]+대학교|[가-힣]+여대|[가-힣]{2,3}대)\s*[가나다]\s*수능", r"\n\1 가 수능", part)
            
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

            split_rows = []
            for row in rows:
                sub_rows = re.split(r"(?<=\d)\s+(?=(?:서울|경기|인천|강원|대전|충남|충북|세종|광주|전남|전북|대구|경북|부산|울산|경남|제주)\s+[가-힣]{2,6}대)", row)
                if len(sub_rows) > 1:
                    split_rows.extend(sub_rows)
                else:
                    split_rows.append(row)
            rows = split_rows

            current_region = "미상"
            
            for row in rows:
                row = re.sub(r'\s+', ' ', row).strip()
                
                for r in regions:
                    if row.startswith(r):
                        current_region = r
                        row = row[len(r):].strip()
                        break
                        
                row = re.sub(r'(교과|종합|수능|실기/실적|실기)(기초|기회|저소득|사회적|고른기회|교육|사회배려|농어촌)', r'\1 \2', row)
                
                branch_match_prefix = re.match(r"^\(([가-힣]+)\)(교과|종합|수능|실기)", row)
                campus_name_prefix = ""
                if branch_match_prefix:
                     campus_name_prefix = branch_match_prefix.group(1)
                     row = row.replace(branch_match_prefix.group(0), branch_match_prefix.group(2))
                     
                uni_match = re.search(r"^([가-힣]+(대학교|대|교대|여대|과기대))(?:\s*\(([가-힣]+)\))?", row)
                campus_name = ""
                if uni_match:
                    uni = uni_match.group(1)
                    if uni_match.group(3):
                        campus_name = uni_match.group(3)
                    elif campus_name_prefix:
                        campus_name = campus_name_prefix
                        
                    if campus_name:
                        uni = f"{uni}·{campus_name}"
                        
                    row = row[len(uni_match.group(0)):].strip()
                else:
                    if row.startswith("대 "):
                        uni = current_region + "대"
                        row = row[2:].strip()
                    else:
                        pass
                        
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

                if not num and "수능" in name:
                    rescue = re.search(r"^(.*?)\s+(\d+)\s*(수능.*?)(?:\s*-\s*(\d+).*)?$", name)
                    if rescue:
                        name = rescue.group(1).strip()
                        num = rescue.group(2).strip()
                        method = rescue.group(3).strip()
                        if rescue.group(4):
                            note = rescue.group(4).strip()

                if len(method) > 40 and ("성균관대" in method or "이화여대" in method or "중앙대" in method or "숙명여대" in method):
                    continue

                # Hard override for SNU data based on official 2027 SNU Admissions Plan PDF
                # SNU Official PDF states:
                # 수시: 기회균형특별전형(사회통합)
                # 정시: 나군 기회균형특별전형(저소득)
                
                if uni == "서울대" and period == "정시" and name.startswith("가"):
                    name = name.replace("가", "나", 1).strip() # SNU is 나군 in 2027
                
                final_track = current_sub_track
                if final_track == "의치약한수계열":
                    full_text = uni + " " + name + " " + method + " " + note
                    if "의예" in full_text: final_track = "의예과"
                    elif "치의" in full_text: final_track = "치의예과"
                    elif "약학" in full_text: final_track = "약학과"
                    elif "한의" in full_text: final_track = "한의예과"
                    elif "수의" in full_text: final_track = "수의예과"
                    
                # Fix SNU specific method bugs
                if uni == "서울대" and method == "수능100국,수,영,탐 3개 합 7 서":
                    method = "수능100"
                    note = "국,수,영,탐 3개 합 7"
                    
                if uni == "서울대" and method.startswith("수능100국,수"):
                    method_real = "수능100"
                    note_real = method.replace("수능100", "").strip()
                    method = method_real
                    note = note_real

                if name and method and num:
                    results.append({
                        "period": period,
                        "track": final_track,
                        "region": current_region,
                        "university": uni,
                        "type": type_,
                        "name": name,
                        "recruitNum": num,
                        "method": method,
                        "note": note
                    })
                    
# Add SNU 수시 기회균형특별전형(사회통합) which was completely missing from the original PDF's tables
snu_susi_added = False
for r in results:
    if r["university"] == "서울대" and r["period"] == "수시":
        snu_susi_added = True

if not snu_susi_added:
    results.append({
        "period": "수시",
        "track": "일반계열", # It's across multiple colleges
        "region": "서울",
        "university": "서울대",
        "type": "종합",
        "name": "기회균형특별전형(사회통합)",
        "recruitNum": "177", # 177 in the PDF (excluding the 4 extra agriculture slots)
        "method": "1단계(2배수): 서류100 / 2단계: 서류70+면접30",
        "note": "수능최저학력기준 미적용"
    })

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(results)} rows.")
