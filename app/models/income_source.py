from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class IncomeType(str, enum.Enum):
    DIVIDEND = "dividend"
    RENTAL = "rental"
    DIGITAL_PRODUCT = "digital_product"
    AD_REVENUE = "ad_revenue"
    ROYALTY = "royalty"
    INTEREST = "interest"
    OTHER = "other"


class IncomeFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default=IncomeType.OTHER)
    amount = Column(Float, nullable=False, default=0.0)
    frequency = Column(String(50), nullable=False, default=IncomeFrequency.MONTHLY)
    description = Column(String(1000), nullable=True)
    platform = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    target_amount = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = relationship("IncomeLog", back_populates="source", cascade="all, delete-orphan")

    @property
    def monthly_amount(self) -> float:
        """Normalize amount to monthly equivalent."""
        freq_multipliers = {
            IncomeFrequency.DAILY: 30,
            IncomeFrequency.WEEKLY: 4.33,
            IncomeFrequency.MONTHLY: 1,
            IncomeFrequency.QUARTERLY: 1 / 3,
            IncomeFrequency.ANNUALLY: 1 / 12,
        }
        return self.amount * freq_multipliers.get(self.frequency, 1)
