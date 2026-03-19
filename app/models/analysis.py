"""
수입 분석 결과 모델
AI가 생성한 포트폴리오 분석 및 최적화 조언을 저장합니다.
"""
from datetime import datetime
from sqlalchemy import Float, Integer, ForeignKey, DateTime, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class IncomeAnalysis(Base):
    __tablename__ = "income_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # 수치 분석 결과
    total_monthly: Mapped[float] = mapped_column(Float, default=0.0)   # 월 총 수입 (원화 환산)
    total_annually: Mapped[float] = mapped_column(Float, default=0.0)  # 연 총 수입
    top_source: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 최대 수입원 이름

    # AI 생성 콘텐츠
    ai_advice: Mapped[str | None] = mapped_column(Text, nullable=True)  # Gemini 최적화 조언
    tax_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 세금 추정액

    # FIRE(경제적 자유) 달성 예측
    fire_years: Mapped[float | None] = mapped_column(Float, nullable=True)  # FIRE까지 남은 연수

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계: 분석 → 소유자(User)
    owner: Mapped["User"] = relationship("User", back_populates="analyses")
