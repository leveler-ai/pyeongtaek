# -*- coding: utf-8 -*-
"""
평택 아파트 매물 모니터링 시스템 설정
"""

# 모니터링 대상 단지 목록 (네이버 부동산 고유 번호)
TARGET_COMPLEXES = [
    {
        "id": 127109,
        "name": "고덕국제신도시리슈빌레이크파크",
        "short_name": "리슈빌레이크파크",
        "sector": "고덕동",
        "total_households": 730
    },
    {
        "id": 160783,
        "name": "평택고덕국제신도시디에트르리비에르",
        "short_name": "디에트르리비에르",
        "sector": "고덕동",
        "total_households": 726
    },
    {
        "id": 115018,
        "name": "더샵지제역센트럴파크(1BL)",
        "short_name": "더샵지제역 1BL",
        "sector": "동삭동",
        "total_households": 2124
    }
]

# 거래 유형 (B1: 전세, B2: 월세)
ALLOWED_TRADE_TYPES = ["B1", "B2"]

# 최소 전용면적 기준 (㎡)
MIN_EXCLUSIVE_AREA = 80.0

# 금융 계산 기본값
DEFAULT_CURRENT_DEPOSIT = 800000000  # 현재 전세보증금: 8억 원 (80,000만 원)
DEFAULT_ANNUAL_YIELD = 10.0         # 목표 연 수익률: 10%
