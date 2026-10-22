# -*- coding: utf-8 -*-
"""
평택 부동산 매물 모니터링 & 대시보드 메인 오케스트레이터
실행 시 네이버 부동산 최신 매물 수집 -> 변동(Diff) 분석 -> Neo-Brutalism HTML 갱신
"""

import os
import sys
import json
import shutil
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# src 경로 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.config import TARGET_COMPLEXES, DEFAULT_CURRENT_DEPOSIT, DEFAULT_ANNUAL_YIELD
from src.collector import collect_all
from src.diff_engine import analyze_diff
from src.generator import generate_dashboard_html

def run_pipeline():
    print("=" * 60)
    print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] 평택 매물 모니터링 파이프라인 시작")
    print("=" * 60)
    
    # 1. 데이터 수집
    print("1. 네이버 부동산 실시간 매물 수집 중...")
    articles = collect_all()
    print(f"-> 총 {len(articles)}개 타깃 매물 수집 완료 (전용 80㎡ 이상 전·월세)")
    
    # 2. 변동(Diff) 분석
    print("\n2. 이전 스냅샷 대조 및 변동 내역 분석 중...")
    history_file = os.path.join(BASE_DIR, "data", "history.json")
    diff_info = analyze_diff(articles, history_file)
    print(f"-> 변동 이벤트: 신규 {diff_info['newCount']}건, 가격변동 {diff_info['priceChangeCount']}건, 삭제 {diff_info['removedCount']}건")
    
    # 3. 최신 데이터 JSON 백업
    latest_data_path = os.path.join(BASE_DIR, "data", "latest_articles.json")
    with open(latest_data_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
        
    # 4. Neo-Brutalism HTML 대시보드 생성 (고정 경로)
    print("\n3. 고정 경로 Neo-Brutalism HTML 대시보드 갱신 중...")
    dashboard_path = os.path.join(BASE_DIR, "pyeongtaek_dashboard.html")
    index_path = os.path.join(BASE_DIR, "index.html")
    generate_dashboard_html(
        articles=articles,
        diff_info=diff_info,
        output_path=dashboard_path,
        default_deposit=DEFAULT_CURRENT_DEPOSIT,
        default_yield=DEFAULT_ANNUAL_YIELD
    )
    
    # index.html로 복사
    import shutil
    shutil.copyfile(dashboard_path, index_path)
    
    # 5. GitHub Pages 저장소 자동 Push
    try:
        from src.uploader import upload_file_to_github
        print("\n4. GitHub Pages (leveler-ai.github.io) 자동 배포 동기화 중...")
        upload_file_to_github(index_path, "index.html", f"Auto-update: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")
        upload_file_to_github(history_file, "data/history.json", f"Update history: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        print(f"[!] GitHub 자동 동기화 건너뜀: {e}")
    
    print("\n" + "=" * 60)
    print("모든 작업 완료!")
    print(f"로컬 대시보드: {dashboard_path}")
    print("GitHub Pages URL: https://leveler-ai.github.io/pyeongtaek/")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
