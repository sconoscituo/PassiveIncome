"""
수익 계산 서비스
월/연간 환산, 세금 추정, FIRE 달성 예측 등 수치 계산 담당
"""
from typing import Optional
from app.models.income import IncomeSource, IncomeType, Frequency

# 환율 기준 (실제 서비스에서는 환율 API 연동 권장)
EXCHANGE_RATES = {
    "KRW": 1.0,
    "USD": 1350.0,
    "EUR": 1450.0,
    "JPY": 9.0,
    "GBP": 1700.0,
}

# FIRE 목표 월 수입 기본값 (원화)
FIRE_TARGET_MONTHLY_KRW = 3_000_000  # 월 300만원

# 국내 금융소득 세율 (이자/배당 소득세)
TAX_RATE_FINANCIAL = 0.154  # 15.4% (소득세 14% + 지방소득세 1.4%)
TAX_RATE_RENTAL = 0.042     # 임대소득세 간이 추정 (분리과세 기준)


def to_monthly_krw(source: IncomeSource) -> float:
    """
    수입원 하나를 원화 기준 월 환산 금액으로 변환
    - 분기별: ÷ 3
    - 연간: ÷ 12
    """
    rate = EXCHANGE_RATES.get(source.currency.upper(), 1.0)
    amount_krw = source.amount * rate

    if source.frequency == Frequency.MONTHLY:
        return amount_krw
    elif source.frequency == Frequency.QUARTERLY:
        return amount_krw / 3
    elif source.frequency == Frequency.ANNUALLY:
        return amount_krw / 12
    return amount_krw


def calculate_portfolio(sources: list[IncomeSource]) -> dict:
    """
    전체 포트폴리오 요약 계산
    반환: 월 총수입, 연 총수입, 유형별 분류, 최대 수입원
    """
    if not sources:
        return {
            "total_monthly_krw": 0.0,
            "total_annually_krw": 0.0,
            "by_type": {},
            "top_source": None,
        }

    # 유형별 월 수입 집계
    by_type: dict[str, float] = {}
    monthly_per_source: dict[str, float] = {}

    for source in sources:
        monthly = to_monthly_krw(source)
        type_key = source.type.value
        by_type[type_key] = by_type.get(type_key, 0.0) + monthly
        monthly_per_source[source.name] = monthly_per_source.get(source.name, 0.0) + monthly

    total_monthly = sum(by_type.values())
    total_annually = total_monthly * 12
    top_source = max(monthly_per_source, key=monthly_per_source.get) if monthly_per_source else None

    return {
        "total_monthly_krw": round(total_monthly, 0),
        "total_annually_krw": round(total_annually, 0),
        "by_type": {k: round(v, 0) for k, v in by_type.items()},
        "top_source": top_source,
    }


def estimate_tax(sources: list[IncomeSource]) -> float:
    """
    연간 세금 추정 (프리미엄 기능)
    - 배당/예금/리츠: 금융소득세 15.4%
    - 임대: 분리과세 4.2% 간이 추정
    - 부업/기타: 종합소득세 간이 추정 (20%)
    """
    annual_tax = 0.0

    for source in sources:
        monthly = to_monthly_krw(source)
        annual = monthly * 12

        if source.type in (IncomeType.DIVIDEND, IncomeType.SAVINGS, IncomeType.REITS):
            annual_tax += annual * TAX_RATE_FINANCIAL
        elif source.type == IncomeType.RENTAL:
            annual_tax += annual * TAX_RATE_RENTAL
        else:
            # 부업/기타는 종합소득세 20% 간이 추정
            annual_tax += annual * 0.20

    return round(annual_tax, 0)


def calculate_fire_years(
    total_monthly_krw: float,
    fire_target_monthly: float = FIRE_TARGET_MONTHLY_KRW,
    current_savings_krw: float = 0.0,
    monthly_investment_krw: float = 500_000,
    annual_return_rate: float = 0.07,
) -> Optional[float]:
    """
    FIRE(Financial Independence, Retire Early) 달성 예측
    - 현재 패시브 인컴이 목표에 도달하는 데 걸리는 연수 계산
    - 단순 복리 성장 모델 사용
    """
    if total_monthly_krw >= fire_target_monthly:
        return 0.0  # 이미 FIRE 달성

    # 부족한 월 수입
    gap = fire_target_monthly - total_monthly_krw

    # 연간 투자 원금 × 복리로 갭을 메우는 연수 추정 (이분 탐색)
    monthly_rate = annual_return_rate / 12
    if monthly_rate <= 0 or monthly_investment_krw <= 0:
        return None

    # 미래가치로 역산: FV = PMT × [(1+r)^n - 1] / r
    # 목표 자산 = gap / (annual_return_rate) × 12  (4% 룰 역산)
    target_asset = (gap * 12) / annual_return_rate

    # 월 투자로 목표 자산 도달 월수 계산
    months = 0
    accumulated = current_savings_krw
    while accumulated < target_asset and months < 600:  # 최대 50년
        accumulated = accumulated * (1 + monthly_rate) + monthly_investment_krw
        months += 1

    return round(months / 12, 1)
