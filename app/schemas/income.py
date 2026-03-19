"""
수입원 관련 Pydantic 스키마
요청/응답 데이터 검증 및 직렬화
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.models.income import IncomeType, Frequency


class IncomeCreate(BaseModel):
    """수입원 생성 요청 스키마"""
    name: str = Field(..., min_length=1, max_length=200, description="수입원 이름")
    type: IncomeType = Field(..., description="수입 유형 (dividend/reits/savings/side_hustle/rental/other)")
    amount: float = Field(..., gt=0, description="수입 금액")
    frequency: Frequency = Field(default=Frequency.MONTHLY, description="수익 발생 주기")
    currency: str = Field(default="KRW", max_length=10, description="통화 코드")
    notes: Optional[str] = Field(None, max_length=1000, description="메모")


class IncomeUpdate(BaseModel):
    """수입원 수정 요청 스키마 (모든 필드 선택적)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[IncomeType] = None
    amount: Optional[float] = Field(None, gt=0)
    frequency: Optional[Frequency] = None
    currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=1000)


class IncomeResponse(BaseModel):
    """수입원 응답 스키마"""
    id: int
    user_id: int
    name: str
    type: IncomeType
    amount: float
    frequency: Frequency
    currency: str
    notes: Optional[str]
    monthly_amount_krw: float = Field(0.0, description="월 환산 금액 (원화)")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    """포트폴리오 전체 요약"""
    total_monthly_krw: float = Field(description="월 총 수입 (원화)")
    total_annually_krw: float = Field(description="연 총 수입 (원화)")
    source_count: int = Field(description="수입원 개수")
    top_source: Optional[str] = Field(None, description="최대 수입원 이름")
    by_type: dict = Field(default_factory=dict, description="유형별 월 수입 합계")
    fire_progress_pct: float = Field(0.0, description="FIRE 달성 진척도 (%)")
    tax_estimate_krw: Optional[float] = Field(None, description="예상 세금 (원화, 프리미엄 전용)")
    fire_years: Optional[float] = Field(None, description="FIRE까지 남은 연수 (프리미엄 전용)")


class OptimizationAdvice(BaseModel):
    """AI 포트폴리오 최적화 조언 (프리미엄 전용)"""
    advice: str = Field(description="Gemini AI 최적화 조언")
    tax_estimate_krw: float = Field(description="예상 세금 (원화)")
    fire_years: float = Field(description="FIRE까지 남은 연수")
    top_recommendations: list[str] = Field(default_factory=list, description="핵심 추천 목록")
