# 📘 API Design Canvas & Spec

## 1. Canvas

### 1.1 목적
- **Text Analysis**: 주관식 답변에 대한 단어 빈도 분석 및 유사도 기반 단어 그룹 제공
- **Simple API**: 간단한 텍스트 입력으로 형태소 분석 및 단어 빈도 계산
- **Caching**: 분석 결과 캐싱을 통한 빠른 응답

### 1.2 핵심 지표
- 캐시 적중 응답 p50 < 200ms, 미적중 p95 < 2.5s
- 동일 파라미터 요청은 Redis/Supabase 캐시에 의해 재계산 없이 응답

### 1.3 주요 사용자
- **교사**: 텍스트 분석 리포트 조회, 단어 빈도 분석
- **관리자**: 전체 시스템 분석, 사용자 관리

### 1.4 데이터 소스
- **Core Tables**: posts (content/answers_data), journeys, journey_weeks, journey_mission_instances
- **User Data**: profiles, user_journeys
- **Analysis Cache**: Redis + Supabase persistent cache

### 1.5 보안
- JWT 기반 인증, RLS로 organization/journey 단위 접근 제한
- 역할 기반 권한: user(학생) < teacher(교사) < admin(관리자)

### 1.6 성능 전략
- **Simple Processing**: 텍스트 기반 처리로 빠른 응답
- **Caching**: Redis + Supabase 이중 캐시로 분석 결과 저장
- **Korean NLP**: Okt 라이브러리로 한국어 형태소 분석

### 1.7 실패 처리
- 텍스트 파라미터 검증 실패: 400 Bad Request
- 분석 API 오류: 캐시된 이전 결과 반환 + 에러 로깅
- 데이터 없음: 200 OK with 빈 배열

---

## 2. Endpoints (간단 명세)

### 2.1 형태소 분석 및 단어 빈도 (SIMPLIFIED)
**endpoint :** `/api/v1/analyze/word-frequency`

**기능 :** 텍스트 입력으로 한국어 형태소 분석 후 단어 빈도 계산. 불용어 제거 포함.

**method :** POST

**body, params :**
```json
{
  "text": "팀워크는 소통과 협업을 통해 달성된다. 좋은 협업이 프로젝트 성공의 열쇠다."
}
```

**response :**
```json
{
  "word_frequency": [
    ["팀워크", 1],
    ["소통", 1], 
    ["협업", 2],
    ["프로젝트", 1],
    ["성공", 1]
  ],
  "total_words": 6,
  "unique_words": 5,
  "processed_at": "2025-01-26T10:00:00Z"
}
```

---

### 2.2 범위별 단어 빈도 분석 (CACHED)
**endpoint :** `/api/v1/analyze/range-word-frequency`

**기능 :** journey/week/mission/student 범위별 posts 데이터에서 단어 빈도 분석. 캐시 우선.

**method :** GET

**body, params :** query → journey_id, journey_week_id, mission_instance_id, user_id, top_n, min_count, force_refresh

**response :**
```json
{
  "scope": "journey_week",
  "range": {"journey_id":"uuid","journey_week_id":"uuid"},
  "cache_hit": true,
  "word_frequency": [
    ["협업", 123],
    ["소통", 89],
    ["팀워크", 67],
    ["프로젝트", 45]
  ],
  "total_posts": 45,
  "analyzed_at": "2025-01-26T10:00:00Z"
}
```

---

### 2.3 단어 그룹핑
**endpoint :** `/api/v1/analyze/group-words`

**기능 :** 단어 리스트를 유사도 기반으로 그룹화

**method :** POST

**body, params :**
```json
{
  "words": ["소통","협업","대화","책임","신뢰","팀워크"],
  "n_clusters": 3
}
```

**response :**
```json
{
  "groups": [
    {
      "label": "소통 관련",
      "words": ["소통","대화"]
    },
    {
      "label": "협업 관련", 
      "words": ["협업","팀워크"]
    },
    {
      "label": "신뢰 관련",
      "words": ["책임","신뢰"]
    }
  ],
  "total_groups": 3
}
```

---

### 2.4 헬스체크
**endpoint :** `/api/v1/health`

**기능 :** 서비스 상태 및 데이터베이스 연결 확인

**method :** GET

**body, params :** 없음

**response :**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "redis": "healthy",
    "supabase": "healthy"
  },
  "uptime_seconds": 3600
}
```


---

## 3. 구현 가이드라인

### 3.1 API 응답 표준
- **단순성**: 최소한의 필드로 명확한 응답 구조
- **일관성**: 모든 단어 빈도는 `[단어, 빈도수]` 배열 형태
- **에러 처리**: 400/500 상태 코드와 명확한 에러 메시지
- **버전 관리**: `/api/v1/` 접두사

### 3.2 성능 최적화  
- **캐시 전략**: Redis 캐시 우선, TTL 7일
- **한국어 NLP**: Okt 라이브러리로 형태소 분석
- **불용어 제거**: 조사, 어미 등 의미없는 단어 제거

### 3.3 보안
- **인증**: JWT 토큰 기반
- **권한**: teacher/admin만 분석 API 접근
- **데이터 격리**: organization 단위 데이터 분리

---

## 4. 비고

이 간소화된 API는 핵심 텍스트 분석 기능에 집중합니다:
- 텍스트 입력 → 형태소 분석 → 단어 빈도 반환
- DB 데이터 범위 분석 → 캐시된 단어 빈도 반환  
- 단어 리스트 → 유사도 기반 그룹핑
- 시스템 상태 확인

모든 응답은 Pydantic 스키마로 검증되며, 단어 빈도는 `[단어, 횟수]` 형태의 배열로 일관성있게 반환됩니다.
"
