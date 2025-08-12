# 📋 Squeeze Backend Development Checklist

## 📊 완료 현황 (2025-08-12)
- ✅ **Core 모듈**: 100% 완료
- ✅ **데이터베이스 모델 및 스키마**: 100% 완료
- ✅ **서비스 레이어**: 100% 완료
- ✅ **API 라우터**: 100% 완료
- ✅ **유틸리티**: 100% 완료
- ✅ **배포 준비**: 90% 완료 (Vercel 배포 성공)
- ⚠️ **테스트**: 개별 테스트 파일 작성됨, 통합 필요
- ⚠️ **문서화**: 기본 문서 작성, 추가 개선 필요

## 🚀 배포 상태
- **Production URL**: Vercel에 성공적으로 배포됨
- **Health Check**: `/api/v1/health` 정상 작동
- **주요 이슈 해결**: 
  - konlpy/jpype1 의존성 문제 → fallback 구현
  - Redis 연결 문제 → serverless 최적화

## 🏗️ 프로젝트 구조 및 기본 설정

### 1. Core 모듈 설정
- [x] `app/core/dependencies.py` - 의존성 주입 (DB, Redis, Auth)
- [x] `app/core/security.py` - JWT 토큰 생성/검증
- [x] `app/core/middleware.py` - CORS, 로깅, 에러 핸들링 미들웨어
- [x] `app/core/exceptions.py` - 커스텀 예외 클래스

### 2. 데이터베이스 모델 및 스키마
- [x] `app/models/__init__.py` - SQLAlchemy 모델 (사용 시)
- [x] `app/models/schemas.py` - Pydantic 스키마 정의
  - [x] `TextAnalysisRequest` - 텍스트 분석 요청
  - [x] `TextAnalysisResponse` - 텍스트 분석 응답
  - [x] `RangeAnalysisRequest` - 범위별 분석 요청
  - [x] `RangeAnalysisResponse` - 범위별 분석 응답
  - [x] `WordGroupingRequest` - 단어 그룹핑 요청
  - [x] `WordGroupingResponse` - 단어 그룹핑 응답

### 3. 서비스 레이어
- [x] `app/services/supabase_unified_auth.py` - Supabase JWT 인증 서비스
  - [x] `verify_supabase_token()` - 토큰 검증
  - [x] `get_current_user()` - 현재 사용자 정보
  - [x] 다양한 토큰 형식 지원 (session, access_token 등)
  
- [x] `app/services/nlp.py` - 한국어 NLP 서비스
  - [x] `initialize_okt()` - Okt 초기화 (fallback 지원)
  - [x] `extract_nouns()` - 명사 추출
  - [x] `remove_stopwords()` - 불용어 제거
  - [x] `calculate_word_frequency()` - 단어 빈도 계산
  - [x] `_fallback_extract_words()` - konlpy 없이 기본 토큰화

- [x] `app/services/cache.py` - 캐싱 서비스
  - [x] `get_cache_key()` - 캐시 키 생성
  - [x] `get_cached_analysis()` - 캐시 조회
  - [x] `set_cached_analysis()` - 캐시 저장
  - [x] `invalidate_cache()` - 캐시 무효화
  - [x] 비동기 캐시 작업 지원

- [x] `app/services/analysis.py` - 텍스트 분석 서비스
  - [x] `analyze_text()` - 단일 텍스트 분석
  - [x] `analyze_multiple_texts()` - 다중 텍스트 분석
  - [x] `get_text_stats()` - 텍스트 통계
  - [x] 캐싱 통합

### 4. API 라우터
- [x] `app/api/v1/__init__.py` - API 버전 관리
- [x] `app/api/v1/analyze.py` - 분석 엔드포인트
  - [x] `POST /analyze/text` - 텍스트 분석 (명사 추출, 빈도)
  - [x] `POST /analyze/multiple` - 다중 텍스트 분석
  - [x] `GET /analyze/cache/{cache_key}` - 캐시 조회

- [x] `app/api/v1/health.py` - 헬스체크 엔드포인트
  - [x] `GET /health` - 서비스 상태 확인
  - [x] Serverless 환경 최적화 (Redis 비필수 처리)

### 5. 유틸리티
- [x] `app/utils/korean_nlp.py` - 한국어 처리 유틸
  - [x] 한국어 불용어 리스트 정의
  - [x] 텍스트 정규화 함수
  - [x] 형태소 분석 헬퍼
  - [x] 기본 패턴 정의

- [x] `app/utils/validators.py` - 입력 검증
  - [x] 텍스트 길이 검증
  - [x] UUID 형식 검증
  - [x] 파라미터 범위 검증
  - [x] 토큰 형식 검증

## 🧪 테스트

### 6. 단위 테스트
- [ ] `tests/test_nlp.py` - NLP 서비스 테스트
  - [ ] 형태소 분석 테스트
  - [ ] 불용어 제거 테스트
  - [ ] 단어 빈도 계산 테스트

- [ ] `tests/test_cache.py` - 캐시 서비스 테스트
  - [ ] 캐시 저장/조회 테스트
  - [ ] TTL 테스트

- [ ] `tests/test_analysis.py` - 분석 서비스 테스트
  - [ ] 텍스트 분석 테스트
  - [ ] 범위별 분석 테스트
  - [ ] 단어 그룹핑 테스트

### 7. 통합 테스트
- [ ] `tests/test_api.py` - API 엔드포인트 테스트
  - [ ] 인증 미들웨어 테스트
  - [ ] 각 엔드포인트 응답 테스트
  - [ ] 에러 핸들링 테스트

## 📝 문서화

### 8. API 문서
- [ ] OpenAPI 스키마 자동 생성 확인
- [ ] API 엔드포인트 설명 추가
- [ ] 요청/응답 예시 추가

### 9. 개발 문서
- [ ] README.md 업데이트
- [ ] 환경 변수 설명 (.env.example)
- [ ] 개발 가이드 작성

## 🚀 배포 준비

### 10. 환경 설정
- [x] `vercel.json` 작성 (Vercel 배포)
- [x] `requirements.txt` - Production 의존성
- [x] `requirements-dev.txt` - 개발 의존성
- [x] 환경 변수 설정 (REDIS_URL, SUPABASE_URL 등)

### 11. 성능 최적화
- [x] 비동기 처리 구현 (async/await)
- [x] 연결 풀링 설정 (Redis, Supabase)
- [x] 로깅 레벨 설정 (structlog)
- [x] Serverless 환경 최적화
  - [x] Redis 연결 관리 개선
  - [x] Event loop 처리
  - [x] Cold start 최적화

### 12. 보안 강화
- [ ] Rate limiting 구현
- [x] 입력 sanitization (Pydantic 검증)
- [x] HTTPS 강제 (Vercel 자동)
- [x] JWT 토큰 검증
- [x] CORS 설정

## 📊 모니터링

### 13. 로깅 및 모니터링
- [ ] Structured logging 설정
- [ ] 에러 추적 (Sentry 등)
- [ ] 성능 메트릭 수집
- [ ] 헬스체크 대시보드

---

## 개발 순서 권장사항

1. **Phase 1 - 기본 구조** (Day 1-2)
   - Core 모듈 설정
   - Pydantic 스키마 정의
   - 기본 라우터 구조

2. **Phase 2 - NLP 서비스** (Day 3-4)
   - Okt 설정 및 테스트
   - 형태소 분석 구현
   - 단어 빈도 계산

3. **Phase 3 - 캐싱 구현** (Day 5)
   - Redis 연결 및 캐싱 로직
   - 캐시 키 전략

4. **Phase 4 - API 구현** (Day 6-7)
   - 엔드포인트 구현
   - 인증 미들웨어
   - 에러 핸들링

5. **Phase 5 - 테스트** (Day 8-9)
   - 단위 테스트
   - 통합 테스트
   - 성능 테스트

6. **Phase 6 - 배포 준비** (Day 10)
   - Docker 설정
   - 문서화
   - 배포 스크립트

---

## FastAPI Best Practices

1. **Dependency Injection**: `Depends()`를 활용한 의존성 주입
2. **Async/Await**: 모든 I/O 작업은 비동기로 구현
3. **Pydantic Models**: 요청/응답 검증 및 문서화
4. **Type Hints**: 모든 함수에 타입 힌트 추가
5. **Error Handling**: HTTPException과 커스텀 예외 활용
6. **Testing**: pytest-asyncio 활용한 비동기 테스트
7. **Security**: OAuth2PasswordBearer for JWT
8. **Documentation**: 모든 엔드포인트에 docstring 추가

---

## 코드 컨벤션

```python
# 파일 구조 예시
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

# 라우터 정의
router = APIRouter(
    prefix="/api/v1/analyze",
    tags=["analysis"]
)

# Pydantic 모델
class WordFrequencyRequest(BaseModel):
    text: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "팀워크는 소통과 협업을 통해 달성된다."
            }
        }

# 엔드포인트
@router.post("/word-frequency", response_model=WordFrequencyResponse)
async def analyze_word_frequency(
    request: WordFrequencyRequest,
    current_user: User = Depends(get_current_user)
) -> WordFrequencyResponse:
    """
    텍스트의 단어 빈도를 분석합니다.
    
    - **text**: 분석할 한국어 텍스트
    - **return**: 단어별 출현 빈도
    """
    # 구현
    pass
```