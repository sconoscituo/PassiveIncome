"""
패시브 인컴 포트폴리오 계산기 라우터
"""
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/portfolio", tags=["포트폴리오"])

try:
    from app.config import config
    GEMINI_KEY = config.GEMINI_API_KEY
except Exception:
    GEMINI_KEY = ""


class IncomeStream(BaseModel):
    name: str
    type: str  # 배당, 임대, 디지털상품, 이자, 기타
    monthly_income: float
    initial_investment: Optional[float] = 0
    is_active: bool = True


class PortfolioRequest(BaseModel):
    streams: List[IncomeStream]
    target_monthly_income: float


@router.post("/analyze")
async def analyze_portfolio(request: PortfolioRequest):
    """패시브 인컴 포트폴리오 분석"""
    active = [s for s in request.streams if s.is_active]
    total_monthly = sum(s.monthly_income for s in active)
    total_invested = sum(s.initial_investment or 0 for s in active)
    achievement_rate = min(total_monthly / request.target_monthly_income * 100, 100) if request.target_monthly_income > 0 else 0
    roi = (total_monthly * 12 / total_invested * 100) if total_invested > 0 else 0

    by_type = {}
    for s in active:
        by_type[s.type] = by_type.get(s.type, 0) + s.monthly_income

    return {
        "summary": {
            "total_monthly_income": total_monthly,
            "total_annual_income": total_monthly * 12,
            "total_invested": total_invested,
            "annual_roi_pct": round(roi, 2),
            "achievement_rate": round(achievement_rate, 1),
            "gap_to_target": max(0, request.target_monthly_income - total_monthly),
        },
        "income_by_type": by_type,
        "stream_count": len(active),
        "diversification_score": min(len(by_type) * 20, 100),
    }


@router.post("/ai-recommendations")
async def get_ai_recommendations(
    request: PortfolioRequest,
    current_user: User = Depends(get_current_user),
):
    """AI 패시브 인컴 추천"""
    if not GEMINI_KEY:
        raise HTTPException(500, "AI 서비스 설정이 필요합니다")

    current = sum(s.monthly_income for s in request.streams if s.is_active)
    gap = request.target_monthly_income - current
    types = list({s.type for s in request.streams})

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"현재 패시브 인컴: 월 {current:,.0f}원\n"
        f"목표: 월 {request.target_monthly_income:,.0f}원\n"
        f"부족분: 월 {gap:,.0f}원\n"
        f"현재 소득 유형: {', '.join(types)}\n\n"
        "부족분을 채우기 위한 실용적인 패시브 인컴 전략 3가지를 추천해줘. "
        "각 전략의 초기 투자 규모와 예상 수익도 포함해줘."
    )
    return {
        "current_income": current,
        "target": request.target_monthly_income,
        "recommendations": response.text,
    }
