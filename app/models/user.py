"""
사용자 모델
이메일/비밀번호 기반 인증 + 프리미엄 여부 관리
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계: 사용자 → 수입원 목록
    income_sources: Mapped[list["IncomeSource"]] = relationship(
        "IncomeSource", back_populates="owner", cascade="all, delete-orphan"
    )
    # 관계: 사용자 → 분석 기록
    analyses: Mapped[list["IncomeAnalysis"]] = relationship(
        "IncomeAnalysis", back_populates="owner", cascade="all, delete-orphan"
    )
