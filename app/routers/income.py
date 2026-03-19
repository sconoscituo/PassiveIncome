"""
수입원 라우터
CRUD + 포트폴리오 요약 + AI 최적화 조언
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.income import IncomeSource
from app.models.user import User
from app.schemas.income import (
    IncomeCreate,
    IncomeUpdate,
    IncomeResponse,
    PortfolioSummary,
    OptimizationAdvice,
)
from app.services.calculator import (
    calculate_portfolio,
    estimate_tax,
    calculate_fire_years,
    to_monthly_krw,
)
from app.services.optimizer import get_optimization_advice
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/income", tags=["수입원 관리"])
settings = get_settings()


def _to_response(source: IncomeSource) -> IncomeResponse:
    """ORM 객체 → 응답 스키마 변환 (월 환산 금액 포함)"""
    data = IncomeResponse.model_validate(source)
    data.monthly_amount_krw = to_monthly_krw(source)
    return data


@router.post("/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
async def create_income(
    income_data: IncomeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수입원 추가 (무료: 최대 5개 제한)"""
    # 무료 플랜 한도 체크
    if not current_user.is_premium:
        result = await db.execute(
            select(IncomeSource).where(IncomeSource.user_id == current_user.id)
        )
        existing = result.scalars().all()
        if len(existing) >= settings.free_plan_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"무료 플랜은 최대 {settings.free_plan_limit}개의 수입원만 등록할 수 있습니다. 프리미엄으로 업그레이드하세요.",
            )

    source = IncomeSource(user_id=current_user.id, **income_data.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return _to_response(source)


@router.get("/", response_model=list[IncomeResponse])
async def list_incomes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 수입원 목록 조회"""
    result = await db.execute(
        select(IncomeSource).where(IncomeSource.user_id == current_user.id)
    )
    sources = result.scalars().all()
    return [_to_response(s) for s in sources]


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """포트폴리오 전체 요약 (월/연 수입, 유형별 분류, FIRE 진척도)"""
    result = await db.execute(
        select(IncomeSource).where(IncomeSource.user_id == current_user.id)
    )
    sources = result.scalars().all()
    calc = calculate_portfolio(sources)

    # FIRE 달성 진척도 (%)
    fire_progress = min(
        calc["total_monthly_krw"] / 3_000_000 * 100, 100.0
    )

    summary = PortfolioSummary(
        total_monthly_krw=calc["total_monthly_krw"],
        total_annually_krw=calc["total_annually_krw"],
        source_count=len(sources),
        top_source=calc["top_source"],
        by_type=calc["by_type"],
        fire_progress_pct=round(fire_progress, 1),
    )

    # 프리미엄 전용: 세금 추정 + FIRE 연수
    if current_user.is_premium:
        summary.tax_estimate_krw = estimate_tax(sources)
        summary.fire_years = calculate_fire_years(calc["total_monthly_krw"])

    return summary


@router.get("/optimize", response_model=OptimizationAdvice)
async def get_optimization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 포트폴리오 최적화 조언 (프리미엄 전용)"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI 최적화 기능은 프리미엄 플랜 전용입니다.",
        )

    result = await db.execute(
        select(IncomeSource).where(IncomeSource.user_id == current_user.id)
    )
    sources = result.scalars().all()

    if not sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="분석할 수입원이 없습니다. 먼저 수입원을 추가하세요.",
        )

    calc = calculate_portfolio(sources)
    ai_result = await get_optimization_advice(sources, calc)
    tax = estimate_tax(sources)
    fire_years = calculate_fire_years(calc["total_monthly_krw"]) or 99.0

    return OptimizationAdvice(
        advice=ai_result["advice"],
        tax_estimate_krw=tax,
        fire_years=fire_years,
        top_recommendations=ai_result["top_recommendations"],
    )


@router.get("/{income_id}", response_model=IncomeResponse)
async def get_income(
    income_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 수입원 조회"""
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == income_id,
            IncomeSource.user_id == current_user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="수입원을 찾을 수 없습니다.")
    return _to_response(source)


@router.patch("/{income_id}", response_model=IncomeResponse)
async def update_income(
    income_id: int,
    income_data: IncomeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수입원 수정"""
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == income_id,
            IncomeSource.user_id == current_user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="수입원을 찾을 수 없습니다.")

    for field, value in income_data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    db.add(source)
    await db.flush()
    await db.refresh(source)
    return _to_response(source)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """수입원 삭제"""
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == income_id,
            IncomeSource.user_id == current_user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="수입원을 찾을 수 없습니다.")

    await db.delete(source)
