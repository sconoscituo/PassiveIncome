"""
PassiveIncome API 기본 테스트
회원가입, 로그인, 수입원 CRUD, 포트폴리오 요약 검증
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """테스트용 DB 세션 오버라이드"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """각 테스트 전 테이블 생성, 후 삭제"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """비동기 테스트 클라이언트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    """테스트용 인증 헤더 (회원가입 + 로그인)"""
    await client.post("/api/users/register", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    resp = await client.post("/api/users/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health_check(client):
    """헬스체크 엔드포인트 테스트"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register(client):
    """회원가입 테스트"""
    resp = await client.post("/api/users/register", json={
        "email": "new@example.com",
        "password": "password123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["is_premium"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """이메일 중복 회원가입 차단 테스트"""
    payload = {"email": "dup@example.com", "password": "pass123"}
    await client.post("/api/users/register", json=payload)
    resp = await client.post("/api/users/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    """로그인 테스트"""
    await client.post("/api/users/register", json={
        "email": "login@example.com", "password": "pass123"
    })
    resp = await client.post("/api/users/login", data={
        "username": "login@example.com", "password": "pass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_create_income(client, auth_headers):
    """수입원 생성 테스트"""
    resp = await client.post("/api/income/", json={
        "name": "삼성전자 배당",
        "type": "dividend",
        "amount": 100000,
        "frequency": "quarterly",
        "currency": "KRW"
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "삼성전자 배당"
    assert data["monthly_amount_krw"] == pytest.approx(100000 / 3, rel=0.01)


@pytest.mark.asyncio
async def test_list_incomes(client, auth_headers):
    """수입원 목록 조회 테스트"""
    # 수입원 2개 추가
    for i in range(2):
        await client.post("/api/income/", json={
            "name": f"수입원{i}", "type": "savings",
            "amount": 50000, "frequency": "monthly", "currency": "KRW"
        }, headers=auth_headers)

    resp = await client.get("/api/income/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_portfolio_summary(client, auth_headers):
    """포트폴리오 요약 테스트"""
    await client.post("/api/income/", json={
        "name": "월세 수입", "type": "rental",
        "amount": 500000, "frequency": "monthly", "currency": "KRW"
    }, headers=auth_headers)

    resp = await client.get("/api/income/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_monthly_krw"] == 500000
    assert data["source_count"] == 1


@pytest.mark.asyncio
async def test_free_plan_limit(client, auth_headers):
    """무료 플랜 5개 제한 테스트"""
    for i in range(5):
        resp = await client.post("/api/income/", json={
            "name": f"수입원{i}", "type": "other",
            "amount": 10000, "frequency": "monthly", "currency": "KRW"
        }, headers=auth_headers)
        assert resp.status_code == 201

    # 6번째는 차단
    resp = await client.post("/api/income/", json={
        "name": "초과수입원", "type": "other",
        "amount": 10000, "frequency": "monthly", "currency": "KRW"
    }, headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_income(client, auth_headers):
    """수입원 삭제 테스트"""
    create_resp = await client.post("/api/income/", json={
        "name": "삭제할 수입원", "type": "other",
        "amount": 10000, "frequency": "monthly", "currency": "KRW"
    }, headers=auth_headers)
    income_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/income/{income_id}", headers=auth_headers)
    assert del_resp.status_code == 204
