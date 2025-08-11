# 🎓 project-basic.md
창업동아리 성찰문 Theme 분석 & 시각화 백엔드 (FastAPI)

본 문서는 제품 목적(PRD)과 기술 스택 및 운영 원칙을 한 파일로 요약합니다. 세부 API는 `api-spec.md`, 스키마 이전은 `schema-migration-strategy.md`를 참고하세요. 또한 migration 이전 supabase full schema 를 확인하려면 `full-supabase-schema.md`를 확인하세요.

---

## 1. 배경과 문제 정의

- 학생들은 회차마다 200–2000자 분량의 과제를 제출하며, 여러 질문(주관식/객관식)이 포함된다.
- 기존에는 posts.content 한 필드에 혼합 텍스트로 저장되어 질문 단위 분석이 어렵고 전처리 비용이 크다.
- 교사/관리자는 클래스·주차·과제·학생 등 어떤 단위든 빠르게 단어 빈출과 유사도 기반 단어 그룹을 보고 싶다.
- 반복 조회가 많아 재계산 비용 최소화와 응답 속도 보장이 필요하다.

---

## 2. 제품 목표 (Goals)

1. 질문 단위로 구조화된 텍스트를 기반으로 정확한 분석 제공.
2. journey / week / mission / student 등 범위 파라미터만 바꿔도 동일 패턴으로 응답.
3. Supabase에 분석 결과를 Persistent Cache로 저장하여 오버헤드 최소화.
4. 대시보드 시각화에 바로 쓰이는 간결한 JSON 스키마 제공.
5. RLS와 역할 기반 제어로 안전한 데이터 접근 보장.

---

## 3. 범위 (Scope)

### 반드시 제공 (MVP)
- CSV/XLSX 업로드 및 미리보기.
- 형태소 분석(Okt), 불용어 제거.
- 범위 기반 단어 빈도 `/word-freq` (캐시).
- 단어 그룹 추천 `/group-words` (독립 라우트).
- Theme/빈도 요약 `/analyze/theme-summary`.
- 리포트 요약 `/report/summary` (Excel/JSON).
- posts → post_answers 이관 `/ingest/post-answers`.

### 차기
- 대표 문장 추출 정교화, 클러스터 자동 라벨링.
- KoBERT/임베딩 기반 고도화.
- PDF/Word 리포트 자동화.
- RLS 정책 정교화, 사용량 모니터링/알림.

---

## 4. 핵심 사용자 & 시나리오

### 사용자
- 교사, 교육 관리자, 연구자.

### 시나리오
- 클래스 N반 주차 M의 상위 단어 Top-N 확인.
- 학생 A의 전체 회차 변화 추세 라인 차트.
- 선택된 범위 상위 단어를 유사도 그룹으로 묶어 추천.
- 같은 요청을 재조회할 때 1초 내 응답.

---

## 5. 성공 지표 (KPIs)

- 캐시 적중 p50 < 200ms.
- 캐시 미적중 p95 < 2.5s.
- 캐시 적중률 ≥ 70%.
- 분석 성공률(주관식 파싱 성공) ≥ 98%.
- 동일 파라미터 재요청 결과 해시 일치율 100%.

---

## 6. 상위 아키텍처

Next.js 대시보드 → FastAPI → Supabase

- Next.js: 범위 선택 → `/word-freq`, `/group-words`, `/analyze/theme-summary` 호출.
- FastAPI: 캐시 조회 → 미스 시 DB 원문 수집 → NLP → 결과 저장 → 응답.
- Supabase: 원본 데이터(posts, journeys 등) + 구조화 저장(post_answers) + 캐시(word_analysis_results, word_clusters).

---

## 7. 데이터 모델 요약

- posts: 메타 중심. `content_legacy`로 보존.
- post_answers: 질문/답변 구조화 저장. `answer_type='subjective'`가 NLP 대상.
- word_analysis_results: 범위별 단어 빈도 캐시(JSONB).
- word_clusters: 유사도 클러스터 결과 캐시(JSONB).

인덱스 축: scope, journey_id, week, mission, user_id.

---

## 8. API 요약 (상세는 api-spec.md)

- `/upload-text` POST: 파일 업로드/미리보기.
- `/analyze/morph` POST: 형태소 분석.
- `/word-freq` GET: 범위 기반 단어 빈도(캐시).
- `/word-freq` POST: 직접 토큰 입력 분석.
- `/group-words` POST: 단어 그룹 생성.
- `/group-words/{cluster_id}` GET: 그룹 결과 조회.
- `/analyze/theme-summary` GET: Theme/빈도 요약.
- `/persona` GET: 대표 문장 추출.
- `/report/summary` GET: 리포트.
- `/analysis/{analysis_id}` GET: 분석 단건.
- `/analysis` GET: 분석 목록.
- `/analysis/recompute` POST: 강제 재계산.
- `/ingest/post-answers` POST: content_legacy 파싱 이관.
- `/health` GET: 상태 확인.

---

## 9. 성능/운영 원칙

- 캐시 우선 응답. `force_refresh`로 재계산 허용.
- 상위 N 단어 제한(기본 100)으로 전송량 제어.
- 실패 시 구조적 에러 반환 및 로깅. 재시도 경로 확보.
- 분석 파이프라인 버전 관리: 알고리즘/사전 변경 시 결과 호환성 고려.

---

## 10. 보안

- JWT 인증 필수. teacher 이상 권한으로 분석 API 허용.
- Supabase RLS로 journey 기반 접근 제한.
- 로그에 원문 텍스트 저장 금지. 식별자 중심 기록.

---

## 11. 마일스톤(예시, Asia/Seoul)

- 2025-07-26 ~ 2025-07-28: 설계 확정.
- 2025-07-29: 스키마 적용.
- 2025-07-29 ~ 2025-08-01: 파서 개발/Dry-run.
- 2025-08-02: 본 이관.
- 2025-08-03 ~ 2025-08-07: 검증/튜닝.
- 2025-08-08: 운영 전환.

---

## 12. 리스크 & 대응

- 파싱 오류: 템플릿 기반, 예외 로깅, 재처리 큐.
- 대용량 처리: 배치, 캐시, 상위 N 제한.
- 권한 오남용: RLS, 역할 체크, 감사 로그.
- 알고리즘 변경: 버전 태깅, 재계산 범위 제한.

---

## 13. 결론

- post_answers 중심 구조 + 캐시 테이블의 조합은 정확도·속도·운영성을 모두 충족한다.
- 범위 기반 API 패턴으로 어떤 단위든 동일한 사용성을 제공한다.
- 단계적 마이그레이션과 철저한 검증으로 안정적인 운영 전환이 가능하다.

## 14. 환경 변수
.env.local 에 저장됨

- REDIS_URL : redis 연결용
- SUPABASE_URL : supabase url
- SUPABASE_ANON_KEY : supabase anon key
- PROJECT_ID : supabase project id