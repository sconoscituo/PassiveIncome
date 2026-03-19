"""
PassiveIncome FastAPI 앱 진입점
라우터 등록, DB 초기화, 미들웨어 설정
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import income, users, portfolio
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 라이프사이클 핸들러"""
    # 시작: DB 테이블 생성
    await init_db()
    yield
    # 종료: 정리 작업 (필요 시 추가)


app = FastAPI(
    title="PassiveIncome API",
    description="패시브 인컴 포트폴리오 추적 + AI 최적화 도우미",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (개발 환경에서는 전체 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router)
app.include_router(income.router)
app.include_router(portfolio.router, prefix="/api/v1")


@app.get("/", tags=["헬스체크"])
async def root():
    """서버 상태 확인"""
    return {"status": "ok", "service": "PassiveIncome API", "version": "1.0.0"}


@app.get("/health", tags=["헬스체크"])
async def health():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
