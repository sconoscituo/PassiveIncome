"""
Gemini AI 포트폴리오 최적화 서비스 (프리미엄 전용)
사용자의 수입 포트폴리오를 분석해 맞춤 전략을 제안합니다.
"""
import json
import re
import google.generativeai as genai
from app.config import get_settings
from app.models.income import IncomeSource

settings = get_settings()


def _build_prompt(sources: list[IncomeSource], summary: dict) -> str:
    """Gemini에 전달할 프롬프트 구성"""
    source_list = "\n".join(
        f"- {s.name} ({s.type.value}): {s.amount:,.0f} {s.currency} / {s.frequency.value}"
        for s in sources
    )

    return f"""당신은 대한민국 최고의 패시브 인컴 재테크 전문가입니다.
아래 사용자의 패시브 인컴 포트폴리오를 분석하고 최적화 전략을 제시해주세요.

## 현재 포트폴리오
{source_list}

## 요약
- 월 총 수입 (원화): {summary['total_monthly_krw']:,.0f}원
- 연 총 수입 (원화): {summary['total_annually_krw']:,.0f}원
- 주요 수입원: {summary.get('top_source', '없음')}

## 요청사항
다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
  "advice": "전체 포트폴리오 분석 및 개선 방향 (300자 이내, 한국어)",
  "top_recommendations": [
    "구체적 추천 1 (한국어)",
    "구체적 추천 2 (한국어)",
    "구체적 추천 3 (한국어)"
  ]
}}
"""


async def get_optimization_advice(
    sources: list[IncomeSource],
    summary: dict,
) -> dict:
    """
    Gemini AI를 호출해 포트폴리오 최적화 조언 반환
    API 키가 없거나 오류 시 기본 조언 반환
    """
    if not settings.gemini_api_key:
        return _default_advice(summary)

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = _build_prompt(sources, summary)
        response = model.generate_content(prompt)
        text = response.text.strip()

        # JSON 파싱 시도
        # 마크다운 코드 블록 제거
        text = re.sub(r"```json\s*|\s*```", "", text).strip()
        result = json.loads(text)

        return {
            "advice": result.get("advice", "분석 결과를 가져올 수 없습니다."),
            "top_recommendations": result.get("top_recommendations", []),
        }

    except json.JSONDecodeError:
        # JSON 파싱 실패 시 텍스트 그대로 반환
        return {
            "advice": response.text[:500] if response else "분석 실패",
            "top_recommendations": [],
        }
    except Exception as e:
        # API 오류 시 기본 조언 반환
        return _default_advice(summary)


def _default_advice(summary: dict) -> dict:
    """API 미설정 또는 오류 시 규칙 기반 기본 조언"""
    monthly = summary.get("total_monthly_krw", 0)
    by_type = summary.get("by_type", {})

    tips = []

    # 포트폴리오 다양성 체크
    if len(by_type) < 3:
        tips.append("수입원을 3가지 이상 유형으로 다양화하여 리스크를 분산하세요.")

    # 배당 비중 체크
    dividend_ratio = by_type.get("dividend", 0) / max(monthly, 1)
    if dividend_ratio < 0.2:
        tips.append("배당주 비중을 늘려 안정적인 현금흐름을 확보하세요.")

    # 리츠 추천
    if "reits" not in by_type:
        tips.append("리츠(REITs)를 추가하면 부동산 수익을 소액으로 얻을 수 있습니다.")

    if not tips:
        tips.append("포트폴리오가 잘 구성되어 있습니다. 정기적으로 리밸런싱하세요.")

    advice = f"현재 월 {monthly:,.0f}원의 패시브 인컴을 창출하고 있습니다. " \
             f"지속적인 투자와 다각화로 수익을 극대화하세요."

    return {"advice": advice, "top_recommendations": tips}
