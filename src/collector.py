# -*- coding: utf-8 -*-
"""
네이버 부동산 매물 수집 모듈
curl_cffi 기반 경량·고속 API 수집기
"""

import time
import re
from curl_cffi import requests
from .config import TARGET_COMPLEXES, ALLOWED_TRADE_TYPES, MIN_EXCLUSIVE_AREA

HEADERS = {
    'Referer': 'https://fin.land.naver.com/',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
}

def parse_floor_info(floor_str):
    """
    층 정보 파싱 (예: '1/20', '저/20', '고/25', '14/27')
    (target_floor_str, total_floor, is_low_floor)
    """
    if not floor_str:
        return "-", 0, False
        
    parts = str(floor_str).split('/')
    target = parts[0].strip()
    total = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
    
    is_low = False
    if target in ['1', '2', '3', '저', '1층', '2층', '3층']:
        is_low = True
    elif target.isdigit() and int(target) <= 3:
        is_low = True
        
    return target, total, is_low

def collect_complex_articles(complex_info):
    """
    단일 단지의 전세/월세 매물 수집
    """
    cid = complex_info['id']
    cname = complex_info['name']
    articles = []
    
    seed = None
    last_info = None
    page = 1
    
    while True:
        payload = {"complexNumber": cid, "size": 20}
        if seed and last_info:
            payload["seed"] = seed
            payload["lastInfo"] = last_info
            
        success = False
        r = None
        for attempt in range(1, 4):
            try:
                r = requests.post(
                    "https://fin.land.naver.com/front-api/v1/complex/article/list",
                    json=payload,
                    headers=HEADERS,
                    impersonate='chrome120',
                    timeout=20
                )
                if r.status_code == 200:
                    success = True
                    break
                else:
                    print(f"[{cname}] 수집 응답 코드 {r.status_code} -> 재시도 ({attempt}/3)")
                    time.sleep(2)
            except Exception as e:
                print(f"[{cname}] 수집 중 통신 오류 -> 재시도 ({attempt}/3): {e}")
                time.sleep(2)
                
        if not success or r is None:
            print(f"[{cname}] 3회 시도 후에도 수집 실패, 단지 수집을 중단합니다.")
            break
            
        try:
            res = r.json().get('result', {})
            items = res.get('list', [])
            if not items:
                break
                
            for it in items:
                rep = it.get('representativeArticleInfo', {})
                dup = it.get('duplicatedArticleInfo', {})
                trade_type = rep.get('tradeType')
                space = rep.get('spaceInfo', {})
                exclusive = space.get('exclusiveSpace', 0.0)
                
                # 거래 유형 및 전용면적 필터 (80㎡ 이상)
                if trade_type in ALLOWED_TRADE_TYPES and exclusive >= MIN_EXCLUSIVE_AREA:
                    price = rep.get('priceInfo', {})
                    deposit = price.get('warrantyPrice', 0)
                    monthly = price.get('rentPrice', 0)
                    mgt_fee = price.get('managementFeeAmount', 0)
                    raw_floor = rep.get('articleDetail', {}).get('floorInfo', '')
                    target_floor, total_floor, is_low = parse_floor_info(raw_floor)
                    
                    dong = rep.get('dongName', '')
                    art_no = rep.get('articleNumber', '')
                    realtor = rep.get('brokerInfo', {}).get('brokerageName', '')
                    realtor_count = dup.get('realtorCount', 1)
                    feature = rep.get('articleDetail', {}).get('articleFeatureDescription', '')
                    confirm_date = rep.get('verificationInfo', {}).get('articleConfirmDate', '')
                    trade_name = "전세" if trade_type == 'B1' else "월세"
                    
                    # 중복 매물 목록 파싱
                    dup_list = []
                    for d in dup.get('articleInfoList', []):
                        d_no = d.get('articleNumber')
                        d_realtor = d.get('brokerInfo', {}).get('brokerageName', '')
                        d_feature = d.get('articleDetail', {}).get('articleFeatureDescription', '')
                        dup_list.append({
                            "articleNo": d_no,
                            "realtor": d_realtor,
                            "feature": d_feature,
                            "link": f"https://fin.land.naver.com/articles/{d_no}"
                        })
                        
                    # 대표 매물 링크
                    direct_url = f"https://fin.land.naver.com/articles/{art_no}"
                    
                    articles.append({
                        "articleNo": str(art_no),
                        "complexName": cname,
                        "complexId": cid,
                        "shortName": complex_info.get('short_name', cname),
                        "tradeType": trade_type,
                        "tradeName": trade_name,
                        "dong": dong,
                        "floorInfo": raw_floor,
                        "targetFloor": target_floor,
                        "totalFloor": total_floor,
                        "isLowFloor": is_low,
                        "exclusiveArea": round(exclusive, 2),
                        "supplyName": space.get('supplySpaceName', ''),
                        "deposit": deposit,
                        "monthlyRent": monthly,
                        "managementFee": mgt_fee,
                        "realtor": realtor,
                        "realtorCount": realtor_count,
                        "feature": feature,
                        "confirmDate": confirm_date,
                        "directUrl": direct_url,
                        "duplicates": dup_list
                    })
                    
            has_next = res.get('hasNextPage', False)
            seed = res.get('seed')
            last_info = res.get('lastInfo')
            if not has_next or not last_info:
                break
                
            page += 1
            time.sleep(0.2)  # 자연스러운 요청 간격
            
        except Exception as e:
            print(f"[{cname}] 수집 중 예외 발생: {e}")
            break
            
    return articles

def fetch_article_detail_info(article_no):
    """
    네이버 매물 상세 페이지에서 입주가능일 및 융자금(근저당) 정보를 정밀 추출합니다.
    """
    url = f"https://fin.land.naver.com/articles/{article_no}"
    try:
        r = requests.get(url, headers=HEADERS, impersonate='chrome120', timeout=6)
        if r.status_code == 200:
            html = r.text
            # 입주가능일 매칭
            m_move = re.search(r'term">입주가능일</div><div[^>]*definition">([^<]+)</div>', html)
            move_in = m_move.group(1).strip() if m_move else "협의 가능"
            
            # 융자금 / 근저당 매칭
            m_loan = re.search(r'term">융자금</div><div[^>]*definition">([^<]+)</div>', html)
            loan_info = m_loan.group(1).strip() if m_loan else "정보 없음"
            return move_in, loan_info
    except Exception:
        pass
    return "협의 가능", "정보 없음"

def collect_all():
    """
    모든 대상 단지 수집 및 입주가능일/융자금 상세 보강 후 반환
    """
    all_articles = []
    for comp in TARGET_COMPLEXES:
        items = collect_complex_articles(comp)
        all_articles.extend(items)
        
    print(f"[*] 총 {len(all_articles)}개 매물의 입주가능일 및 융자금(근저당) 상세 조회 중...")
    for item in all_articles:
        move_in, loan_info = fetch_article_detail_info(item['articleNo'])
        item['moveInDate'] = move_in
        item['loanInfo'] = loan_info
        time.sleep(0.1)
        
    return all_articles
