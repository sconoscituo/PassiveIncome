import os
import json
from typing import List, Dict, Any
import google.generativeai as genai
from app.models.income_source import IncomeSource, IncomeType


genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))


class PortfolioAnalyzer:
    """Gemini AI 기반 수동 소득 포트폴리오 분석기."""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _build_portfolio_summary(self, sources: List[IncomeSource]) -> Dict[str, Any]:
        total_monthly = sum(s.monthly_amount for s in sources if s.is_active)
        by_type: Dict[str, float] = {}
        for s in sources:
            if s.is_active:
                by_type[s.type] = by_type.get(s.type, 0) + s.monthly_amount
        return {
            "total_monthly_income": round(total_monthly, 2),
            "total_annual_income": round(total_monthly * 12, 2),
            "income_by_type": {k: round(v, 2) for k, v in by_type.items()},
            "source_count": len([s for s in sources if s.is_active]),
            "diversification_score": len(by_type),
        }

    async def analyze_portfolio(
        self,
        sources: List[IncomeSource],
        goal_monthly: float = 0.0,
    ) -> Dict[str, Any]:
        """포트폴리오 분석 및 AI 최적화 조언 생성."""
        summary = self._build_portfolio_summary(sources)
        achievement_rate = (
            (summary["total_monthly_income"] / goal_monthly * 100) if goal_monthly > 0 else 0
        )

        prompt = f"""
당신은 수동 소득 포트폴리오 전문 재무 분석가입니다.
다음 포트폴리오 데이터를 분석하고 최적화 조언을 제공해주세요.

## 현재 포트폴리오
- 월 총 수익: {summary['total_monthly_income']:,.0f}원
- 연 총 수익: {summary['total_annual_income']:,.0f}원
- 수익원 개수: {summary['source_count']}개
- 수익 유형별 분포: {json.dumps(summary['income_by_type'], ensure_ascii=False)}
- 월 수익 목표: {goal_monthly:,.0f}원
- 목표 달성률: {achievement_rate:.1f}%

## 수익원 상세
{chr(10).join([f"- {s.name} ({s.type}): 월 {s.monthly_amount:,.0f}원" for s in sources if s.is_active])}

다음 JSON 형식으로 응답해주세요:
{{
  "overall_assessment": "전반적 평가 (2-3문장)",
  "strengths": ["강점1", "강점2", "강점3"],
  "weaknesses": ["약점1", "약점2"],
  "recommendations": [
    {{"title": "추천1 제목", "description": "상세 설명", "priority": "high/medium/low"}},
    {{"title": "추천2 제목", "description": "상세 설명", "priority": "high/medium/low"}},
    {{"title": "추천3 제목", "description": "상세 설명", "priority": "high/medium/low"}}
  ],
  "next_milestone": "다음 목표 제안",
  "risk_level": "low/medium/high",
  "diversification_advice": "다각화 조언"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            advice = json.loads(text)
        except Exception as e:
            advice = {
                "overall_assessment": "AI 분석을 일시적으로 사용할 수 없습니다.",
                "strengths": ["수동 소득 시작"],
                "weaknesses": ["분석 불가"],
                "recommendations": [],
                "next_milestone": "첫 번째 수익원 추가",
                "risk_level": "medium",
                "diversification_advice": "다양한 수익원을 추가하세요.",
                "error": str(e),
            }

        return {
            "summary": summary,
            "achievement_rate": round(achievement_rate, 1),
            "advice": advice,
        }

    async def generate_growth_plan(
        self,
        sources: List[IncomeSource],
        target_monthly: float,
        months: int = 12,
    ) -> Dict[str, Any]:
        """수익 성장 계획 생성."""
        summary = self._build_portfolio_summary(sources)
        gap = max(0, target_monthly - summary["total_monthly_income"])

        prompt = f"""
수동 소득 성장 전문가로서 {months}개월 성장 계획을 수립해주세요.

현재 월 수익: {summary['total_monthly_income']:,.0f}원
목표 월 수익: {target_monthly:,.0f}원
부족액: {gap:,.0f}원
기간: {months}개월

JSON 형식으로 응답:
{{
  "monthly_milestones": [
    {{"month": 1, "target": 금액, "action": "실행 계획"}},
    {{"month": 3, "target": 금액, "action": "실행 계획"}},
    {{"month": 6, "target": 금액, "action": "실행 계획"}},
    {{"month": 12, "target": 금액, "action": "실행 계획"}}
  ],
  "new_income_sources": ["추천 신규 수익원1", "추천 신규 수익원2", "추천 신규 수익원3"],
  "investment_required": "필요 초기 투자금 추정",
  "feasibility": "실현 가능성 평가"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            plan = json.loads(text)
        except Exception as e:
            plan = {
                "monthly_milestones": [],
                "new_income_sources": [],
                "investment_required": "분석 불가",
                "feasibility": "분석 불가",
                "error": str(e),
            }

        return {
            "current_monthly": summary["total_monthly_income"],
            "target_monthly": target_monthly,
            "gap": gap,
            "months": months,
            "plan": plan,
        }
