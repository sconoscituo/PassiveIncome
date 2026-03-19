"""
수입원 모델
패시브 인컴의 각 소스(배당주, 리츠, 예금, 부업, 임대 등)를 표현합니다.
"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class IncomeType(str, enum.Enum):
    """수입원 유형"""
    DIVIDEND = "dividend"       # 배당주
    REITS = "reits"             # 리츠
    SAVINGS = "savings"         # 예금/적금
    SIDE_HUSTLE = "side_hustle" # 부업
    RENTAL = "rental"           # 임대 수입
    OTHER = "other"             # 기타


class Frequency(str, enum.Enum):
    """수익 발생 주기"""
    MONTHLY = "monthly"         # 월별
    QUARTERLY = "quarterly"     # 분기별
    ANNUALLY = "annually"       # 연간


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # 수입원 기본 정보
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[IncomeType] = mapped_column(
        Enum(IncomeType), default=IncomeType.OTHER, nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 수입 금액
    frequency: Mapped[Frequency] = mapped_column(
        Enum(Frequency), default=Frequency.MONTHLY, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), default="KRW")  # 통화 (기본: 원화)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)    # 메모

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 관계: 수입원 → 소유자(User)
    owner: Mapped["User"] = relationship("User", back_populates="income_sources")
