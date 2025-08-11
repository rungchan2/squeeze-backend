# 📋 Squeeze Backend Development Checklist

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
- [ ] `app/services/auth.py` - JWT 인증 서비스
  - [ ] `verify_token()` - 토큰 검증
  - [ ] `get_current_user()` - 현재 사용자 정보
  - [ ] `check_role()` - teacher/admin 권한 확인
  
- [ ] `app/services/nlp.py` - 한국어 NLP 서비스
  - [ ] `initialize_okt()` - Okt 초기화
  - [ ] `extract_nouns()` - 명사 추출
  - [ ] `remove_stopwords()` - 불용어 제거
  - [ ] `calculate_word_frequency()` - 단어 빈도 계산

- [ ] `app/services/cache.py` - 캐싱 서비스
  - [ ] `get_cache_key()` - 캐시 키 생성
  - [ ] `get_cached_analysis()` - 캐시 조회
  - [ ] `set_cached_analysis()` - 캐시 저장
  - [ ] `invalidate_cache()` - 캐시 무효화

- [ ] `app/services/analysis.py` - 텍스트 분석 서비스
  - [ ] `analyze_text()` - 단일 텍스트 분석
  - [ ] `analyze_posts_range()` - 범위별 posts 분석
  - [ ] `group_words()` - 단어 그룹핑 (TF-IDF)

### 4. API 라우터
- [ ] `app/api/v1/__init__.py` - API 버전 관리
- [ ] `app/api/v1/analyze.py` - 분석 엔드포인트
  - [ ] `POST /word-frequency` - 텍스트 단어 빈도 분석
  - [ ] `GET /range-word-frequency` - 범위별 단어 빈도 분석
  - [ ] `POST /group-words` - 단어 그룹핑

- [ ] `app/api/v1/health.py` - 헬스체크 엔드포인트
  - [ ] `GET /health` - 서비스 상태 확인

### 5. 유틸리티
- [ ] `app/utils/korean_nlp.py` - 한국어 처리 유틸
  - [ ] 한국어 불용어 리스트 정의
  - [ ] 텍스트 정규화 함수
  - [ ] 형태소 분석 헬퍼

- [ ] `app/utils/validators.py` - 입력 검증
  - [ ] 텍스트 길이 검증
  - [ ] UUID 형식 검증
  - [ ] 파라미터 범위 검증

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
- [ ] `Dockerfile` 작성
- [ ] `docker-compose.yml` 작성
- [ ] 환경별 설정 파일 (dev, staging, prod)

### 11. 성능 최적화
- [ ] 비동기 처리 구현 (async/await)
- [ ] 연결 풀링 설정 (Redis, Supabase)
- [ ] 로깅 레벨 설정

### 12. 보안 강화
- [ ] Rate limiting 구현
- [ ] 입력 sanitization
- [ ] HTTPS 강제
- [ ] 보안 헤더 설정

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