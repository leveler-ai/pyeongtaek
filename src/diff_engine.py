# -*- coding: utf-8 -*-
"""
매물 변동 감지(Diff) 엔진
직전 수집 스냅샷과 비교하여 신규 매물, 가격 변동, 삭제(거래완료) 매물을 식별
"""

import os
import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def analyze_diff(current_articles, history_path):
    """
    이전 기록과 비교하여 변동 사항을 계산하고 이력을 갱신합니다.
    """
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    
    prev_snapshot = {}
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                prev_data = json.load(f)
                # 이전 스냅샷의 매물들을 딕셔너리로 맵핑
                for item in prev_data.get('articles', []):
                    prev_snapshot[item['articleNo']] = item
        except Exception as e:
            print(f"이전 이력 로드 실패 (새로 시작): {e}")
            
    current_map = {item['articleNo']: item for item in current_articles}
    
    events = []
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    
    # 1. 신규 매물 및 가격 변동 매물 검사
    for art_no, cur in current_map.items():
        if art_no not in prev_snapshot:
            # 신규 등록
            cur['changeStatus'] = 'NEW'
            cur['changeText'] = '신규 등록'
            events.append({
                "type": "NEW",
                "time": now_str,
                "complexName": cur['complexName'],
                "tradeName": cur['tradeName'],
                "dong": cur['dong'],
                "floorInfo": cur['floorInfo'],
                "exclusiveArea": cur['exclusiveArea'],
                "deposit": cur['deposit'],
                "monthlyRent": cur['monthlyRent'],
                "articleNo": art_no,
                "directUrl": cur['directUrl'],
                "desc": f"새로운 {cur['tradeName']} 매물이 등록되었습니다."
            })
        else:
            prev = prev_snapshot[art_no]
            # 가격 변동 검사
            dep_diff = cur['deposit'] - prev.get('deposit', 0)
            rent_diff = cur['monthlyRent'] - prev.get('monthlyRent', 0)
            
            if dep_diff != 0 or rent_diff != 0:
                cur['changeStatus'] = 'PRICE_CHANGED'
                cur['prevDeposit'] = prev.get('deposit', 0)
                cur['prevMonthlyRent'] = prev.get('monthlyRent', 0)
                
                diff_desc = []
                if dep_diff < 0:
                    diff_desc.append(f"보증금 {abs(dep_diff)//10000:,}만 인하")
                elif dep_diff > 0:
                    diff_desc.append(f"보증금 {dep_diff//10000:,}만 인상")
                    
                if rent_diff < 0:
                    diff_desc.append(f"월세 {abs(rent_diff)//10000:,}만 인하")
                elif rent_diff > 0:
                    diff_desc.append(f"월세 {rent_diff//10000:,}만 인상")
                    
                cur['changeText'] = ", ".join(diff_desc)
                events.append({
                    "type": "PRICE_CHANGED",
                    "time": now_str,
                    "complexName": cur['complexName'],
                    "tradeName": cur['tradeName'],
                    "dong": cur['dong'],
                    "floorInfo": cur['floorInfo'],
                    "exclusiveArea": cur['exclusiveArea'],
                    "deposit": cur['deposit'],
                    "monthlyRent": cur['monthlyRent'],
                    "prevDeposit": cur['prevDeposit'],
                    "prevMonthlyRent": cur['prevMonthlyRent'],
                    "articleNo": art_no,
                    "directUrl": cur['directUrl'],
                    "desc": ", ".join(diff_desc)
                })
            else:
                cur['changeStatus'] = 'MAINTAINED'
                cur['changeText'] = '유지'
                
    # 2. 거래완료 / 삭제 매물 검사
    removed_items = []
    for art_no, prev in prev_snapshot.items():
        if art_no not in current_map:
            removed_items.append(prev)
            events.append({
                "type": "REMOVED",
                "time": now_str,
                "complexName": prev['complexName'],
                "tradeName": prev['tradeName'],
                "dong": prev['dong'],
                "floorInfo": prev['floorInfo'],
                "exclusiveArea": prev['exclusiveArea'],
                "deposit": prev['deposit'],
                "monthlyRent": prev['monthlyRent'],
                "articleNo": art_no,
                "directUrl": prev.get('directUrl', f"https://fin.land.naver.com/articles/{art_no}"),
                "desc": "목록에서 삭제됨 (거래 완료 추정)"
            })
            
    # 새 이력 파일 저장
    snapshot_to_save = {
        "updatedAt": now_str,
        "articles": current_articles,
        "lastEvents": events
    }
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot_to_save, f, ensure_ascii=False, indent=2)
        
    return {
        "events": events,
        "newCount": sum(1 for e in events if e['type'] == 'NEW'),
        "priceChangeCount": sum(1 for e in events if e['type'] == 'PRICE_CHANGED'),
        "removedCount": len(removed_items)
    }
