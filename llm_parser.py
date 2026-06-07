import json
import re
import os
import requests

with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Clean up
text = re.sub(r"저작권자 Ⓒ 한국대학교육협의회\s*무단전재 및 재배포 금지\s*-\s*\d+\s*-", "", text)
text = re.sub(r"--- Page \d+ ---", "", text)

sections = re.split(r"□\d\s*(수시모집|정시모집)[^\n]*", text)
results = []

for i in range(1, len(sections), 2):
    period = "수시" if "수시" in sections[i] else "정시"
    content = sections[i+1]
    
    parts = re.split(r"지역\s+대학\s+전형유형\s+전형명\s*(?:모집 군\s*)?모집인원\s+전형방법\s+비고", content)
    for part in parts[1:]:
        # Prompting a local Hermes completion API since OpenAI API key isn't provided directly and the environment allows local Python processing.
        # But wait, we can just write an advanced text parsing logic based on standard PDF column alignment.

        lines = [l.strip() for l in part.split("\n") if l.strip()]
        
        current_region = ""
        current_uni = ""
        
        for line in lines:
            if line.startswith("❙") or "지원자격" in line or "해당하는 사람" in line or line.startswith("라.") or line.startswith("1)") or line.startswith("2)") or line.startswith("3)") or "검정고시 출신자" in line:
                continue

            # Skip header
            if "전형유형" in line: continue

            match = re.match(r'^(?:(서울|경기|인천|강원|대전|충남|충북|세종|광주|전남|전북|대구|경북|부산|울산|경남|제주)\s*)?([가-힣]+대(?:\([^)]+\))?)?(.*?)$', line)
            if match:
                reg = match.group(1)
                uni = match.group(2)
                rest = match.group(3).strip()
                
                if reg: current_region = reg
                if uni: current_uni = uni
                
                # Now parsing rest: 전형유형, 전형명, 모집인원, 전형방법, 비고
                # Usually: [Type] [Name] [Num] [Method] [Note]
                type_match = re.match(r"^(교과|종합|수능|실기/실적|실기)\s*(.*)$", rest)
                if type_match:
                    type_ = type_match.group(1)
                    rest2 = type_match.group(2).strip()
                    
                    # Extract RecruitNum (digits or (digits)) and the rest
                    # Using reverse search to find the last occurrence of digit before method
                    # Method usually contains (학생부, 서류, 면접, 수능, 단계)
                    m = re.search(r'\s+(\d+|\(\d+\))\s+([가-힣0-9+.,% :()]+(?:학생부|면접|서류|수능|실기|단계|일괄|1단계|2단계)[가-힣0-9+.,% :()]*)(?:\s+(.*))?$', rest2)
                    if m:
                        name = rest2[:m.start()].strip()
                        num = m.group(1)
                        method = m.group(2).strip()
                        note = m.group(3) if m.group(3) else ""
                    else:
                        name = rest2
                        num = ""
                        method = ""
                        note = ""
                        
                    results.append({
                        "period": period,
                        "region": current_region,
                        "university": current_uni,
                        "type": type_,
                        "name": name,
                        "recruitNum": num,
                        "method": method,
                        "note": note
                    })
                else:
                    # If it's a continuation line for Name/Method/Note of the previous item
                    if results:
                        results[-1]["name"] += " " + rest

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Parsed {len(results)} structured rows using heuristic logic.")
