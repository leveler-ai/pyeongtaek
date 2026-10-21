# -*- coding: utf-8 -*-
"""
주거비 차액 투자금 및 예상 수익 계산 모듈
현재 보증금(기본 8억) - 새 보증금 = 투자금
예상수익금 = 투자금 * 연 수익률(기본 10%) - (월세 * 12)
"""

def format_krw(amount):
    """원 단위를 억/만원 친화적으로 포맷팅"""
    if amount == 0:
        return "0원"
    abs_amt = abs(amount)
    eok = abs_amt // 100000000
    man = (abs_amt % 100000000) // 10000
    
    parts = []
    if eok > 0:
        parts.append(f"{eok}억")
    if man > 0:
        parts.append(f"{man:,}만")
    res = " ".join(parts) + "원"
    return f"-{res}" if amount < 0 else res

def calculate_finance_for_item(deposit, monthly_rent, current_deposit=800000000, annual_yield=10.0):
    """
    단일 매물에 대한 재무 계산
    """
    investable = current_deposit - deposit
    is_deficit = investable < 0
    deficit_amount = abs(investable) if is_deficit else 0
    actual_investment = max(0, investable)
    
    # 연 예상 순수익 = (실제 투자금 * 연 수익률) - (월세 * 12)
    gross_annual_gain = int(actual_investment * (annual_yield / 100.0))
    annual_rent_cost = int(monthly_rent * 12)
    net_annual_gain = gross_annual_gain - annual_rent_cost
    monthly_net_gain = int(net_annual_gain / 12.0)
    
    return {
        "investableAmount": actual_investment,
        "investableStr": format_krw(actual_investment),
        "isDeficit": is_deficit,
        "deficitAmount": deficit_amount,
        "deficitStr": format_krw(deficit_amount),
        "grossAnnualGain": gross_annual_gain,
        "annualRentCost": annual_rent_cost,
        "netAnnualGain": net_annual_gain,
        "netAnnualStr": f"{'+' if net_annual_gain >= 0 else ''}{format_krw(net_annual_gain)}",
        "monthlyNetGain": monthly_net_gain,
        "monthlyNetStr": f"{'+' if monthly_net_gain >= 0 else ''}{format_krw(monthly_net_gain)}/월"
    }
