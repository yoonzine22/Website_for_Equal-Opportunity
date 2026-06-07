import json
import re

def parse_data():
    with open("data.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Clean up page headers and footers
    text = re.sub(r'저작권자 Ⓒ 한국대학교육협의회\s*무단전재 및 재배포 금지\s*-\s*\d+\s*-', '', text)
    
    # Split by period (수시모집, 정시모집)
    sections = re.split(r'□\d\s*(수시모집|정시모집)[^\n]*', text)
    
    results = []
    
    for i in range(1, len(sections), 2):
        period = "수시" if "수시" in sections[i] else "정시"
        content = sections[i+1]
        
        # Split by table headers
        parts = re.split(r'지역\s*대학\s*전형유형\s*전형명\s*(?:모집 군\s*)?모집인원\s*전형방법\s*비고', content)
        for part in parts[1:]:
            lines = [l.strip() for l in part.split('\n') if l.strip()]
            
            # Reconstruct merged rows
            rows = []
            current_row = ""
            for line in lines:
                if re.match(r'^[가-힣]{2,}', line) and len(current_row) > 10: # Start of a new row (region + uni or uni)
                    if not re.search(r'\d+$', current_row) and not re.search(r'면접|서류|학생부|수능|실기', current_row):
                        current_row += " " + line
                    else:
                        rows.append(current_row)
                        current_row = line
                else:
                    current_row += " " + line if current_row else line
            if current_row:
                rows.append(current_row)
                
            for row in rows:
                if not row or "❙" in row or "지원자격" in row: continue
                # We will extract it cleanly by grouping using LLM.
                # Actually, given the messy nature of PDF text extraction, I will send the text to a local LLM or just use simple regex to extract structured JSON. Let's do it via python regex first.
                pass
