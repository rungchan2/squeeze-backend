# Supabase Custom Auth Hook 인증 가이드

이 백엔드는 프론트엔드의 Supabase Custom Auth Hook 시스템과 연동하여 인증을 처리합니다.

## 🔧 인증 방식

### 1. 토큰 전송 방법 (우선순위 순)

#### 방법 1: Authorization 헤더 (권장)
```http
Authorization: base64-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
또는
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
또는
```http
Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 방법 2: 쿠키
```http
Cookie: sb-access-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. 지원하는 쿠키 이름
- `sb-access-token`
- `supabase-access-token`
- `sb-{project-ref}-auth-token`

## 🚀 사용법

### 1. 프론트엔드에서 API 호출 시

```typescript
// Next.js/React 예시
const response = await fetch('/api/v1/analyze/word-frequency', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}` // Supabase session에서 가져온 토큰
  },
  credentials: 'include', // 쿠키 포함
  body: JSON.stringify({
    text: "분석할 텍스트"
  })
});
```

### 2. 쿠키를 통한 인증 (자동)

프론트엔드에서 Supabase 인증 후, 브라우저가 자동으로 쿠키를 설정하면 별도의 헤더 없이도 인증됩니다.

```typescript
// 쿠키가 설정된 경우 Authorization 헤더 없이도 가능
const response = await fetch('/api/v1/analyze/word-frequency', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // 쿠키 포함 필수
  body: JSON.stringify({
    text: "분석할 텍스트"
  })
});
```

## 🔐 권한 레벨

### 역할 계층구조
- `user` (레벨 1): 기본 사용자
- `teacher` (레벨 2): 교사 권한
- `admin` (레벨 3): 관리자 권한

### API 엔드포인트 권한
- **분석 API**: `teacher` 이상 권한 필요
  - `POST /api/v1/analyze/word-frequency`
  - `GET /api/v1/analyze/range-word-frequency`  
  - `POST /api/v1/analyze/group-words`

- **헬스체크**: 인증 불필요
  - `GET /api/v1/health/`

## 🧪 테스트

### 개발용 토큰 생성 (테스트용)

```bash
python test_supabase_auth.py
```

### 실제 Supabase 토큰 확인

프론트엔드에서 Supabase 세션을 확인:

```typescript
// 현재 세션 정보 확인
const { data: { session } } = await supabase.auth.getSession();
console.log('Access Token:', session?.access_token);

// Custom Auth Hook 사용 시 브라우저 개발자 도구에서:
// Application → Cookies → base64-로 시작하는 토큰 값 확인
```

### Custom Auth Hook 토큰 특징

Custom Auth Hook을 사용하면:
- 토큰에 `base64-` prefix가 붙음
- JWT 디코더로 직접 디코딩이 어려울 수 있음 (Supabase 내부 형식)
- 토큰 내에 `app_metadata`와 `user_metadata`가 포함됨:
  ```json
  {
    "app_metadata": {
      "role": "teacher",
      "organization_id": "...",
      "profile_id": "..."
    },
    "user_metadata": {
      "first_name": "...",
      "last_name": "...",
      "email": "...",
      "profile_image": "..."
    }
  }
  ```

## ⚠️ 주의사항

### 1. 개발 환경 설정
- 현재 JWT 서명 검증이 비활성화되어 있습니다 (개발용)
- 프로덕션에서는 `app/services/supabase_auth.py`에서 검증 옵션을 활성화하세요:

```python
options={
    "verify_signature": True,   # 프로덕션에서는 True
    "verify_exp": True,        # 프로덕션에서는 True
    "verify_aud": False        # 필요에 따라 설정
}
```

### 2. JWT Secret 설정
`.env.local`에 Supabase JWT Secret을 추가하세요:

```env
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
```

### 3. CORS 설정
프론트엔드 도메인이 CORS에 허용되어 있는지 확인하세요.

## 🔍 디버깅

### 인증 실패 시 확인사항

1. **토큰 존재 확인**
   ```javascript
   console.log('Cookies:', document.cookie);
   console.log('Session:', session?.access_token);
   ```

2. **토큰 유효성 확인**
   ```javascript
   // JWT 디코딩
   try {
     const decoded = jwtDecode(token);
     console.log('Token valid until:', new Date(decoded.exp * 1000));
     console.log('User role:', decoded.app_metadata?.role);
   } catch (error) {
     console.error('Invalid token:', error);
   }
   ```

3. **백엔드 로그 확인**
   ```bash
   # 백엔드 서버 실행 시 로그 확인
   uvicorn main:app --reload --log-level debug
   ```

### 일반적인 오류들

- `401 Unauthorized`: 토큰이 없거나 유효하지 않음
- `403 Forbidden`: 권한 부족 (role 확인)
- `Invalid token`: JWT 형식이 잘못되었거나 만료됨

## 📝 API 응답 예시

### 성공 응답
```json
{
  "word_frequency": [
    ["팀워크", 5],
    ["협업", 3],
    ["소통", 2]
  ],
  "total_words": 10,
  "unique_words": 8
}
```

### 오류 응답
```json
{
  "detail": "Teacher 이상의 권한이 필요합니다"
}
```

## 🔄 프론트엔드 연동 예시

useSupabaseAuth 훅을 사용한 API 호출:

```typescript
const { session } = useSupabaseAuth();

const analyzeText = async (text: string) => {
  if (!session?.access_token) {
    throw new Error('로그인이 필요합니다');
  }

  const response = await fetch('/api/v1/analyze/word-frequency', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    },
    body: JSON.stringify({ text })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '분석 중 오류가 발생했습니다');
  }

  return await response.json();
};
```