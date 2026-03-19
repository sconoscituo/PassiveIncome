# PassiveIncome 💰

패시브 인컴 포트폴리오 추적 + AI 최적화 도우미

## 개요

배당주, 리츠, 예금, 부업 수입 등 모든 패시브 인컴 소스를 한 곳에서 관리하고,
Gemini AI가 수익 극대화 전략을 제안합니다.

## 주요 기능

- 수입원 CRUD (배당주/리츠/예금/부업/임대)
- 월/연간 수익 자동 환산
- FIRE 달성 예측 계산
- Gemini AI 포트폴리오 최적화 조언
- 세금 추정 (무료: 5개 소스, 유료: 무제한)

## 수익 구조

| 플랜 | 수입원 | AI 최적화 | 세금 계산 |
|------|--------|-----------|----------|
| 무료 | 5개    | X         | X        |
| 프리미엄 | 무제한 | O      | O        |

## 빠른 시작

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
```

## Docker 실행

```bash
docker-compose up -d
```

## API 문서

서버 실행 후 http://localhost:8000/docs 접속

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy, aiosqlite
- **AI**: Google Gemini API
- **인증**: JWT (python-jose)
