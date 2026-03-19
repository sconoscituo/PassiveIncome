"""
앱 설정 관리 모듈
환경 변수를 읽어 전체 앱에서 사용할 설정 객체를 제공합니다.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 앱 기본 설정
    app_name: str = "PassiveIncome API"
    debug: bool = False

    # 데이터베이스
    database_url: str = "sqlite+aiosqlite:///./passiveincome.db"

    # JWT 인증
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24시간

    # Gemini AI
    gemini_api_key: str = ""

    # 무료 플랜 제한
    free_plan_limit: int = 5  # 무료 사용자 수입원 최대 개수

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 (캐시 적용)"""
    return Settings()
