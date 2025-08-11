"""
실제 JWT 토큰을 사용한 인증 테스트
"""
import asyncio
import base64
import json
from jose import jwt
from app.services.supabase_unified_auth import get_unified_auth_service


async def test_real_jwt_auth():
    """실제 JWT 토큰으로 인증 테스트"""

    # 실제 JWT 토큰을 여기에 입력하세요
    # 프론트엔드에서 받은 access_token을 그대로 넣으면 됩니다
    print("실제 JWT access_token을 입력하세요 (Enter 키로 입력 완료):")
    jwt_token = input().strip()

    if not jwt_token:
        print("토큰이 입력되지 않았습니다.")
        return

    # 1. JWT 디코드 테스트 (signature 검증 없이)
    try:
        decoded_jwt = jwt.decode(jwt_token, key="", options={"verify_signature": False})
        print("\n✅ JWT 디코드 성공!")
        print(json.dumps(decoded_jwt, indent=2, ensure_ascii=False))

        # app_metadata 확인
        app_metadata = decoded_jwt.get("app_metadata", {})
        print("\n📋 app_metadata:")
        print(f"  - role: {app_metadata.get('role')}")
        print(f"  - organization_id: {app_metadata.get('organization_id')}")

    except Exception as e:
        print(f"❌ JWT 디코드 실패: {e}")
        return

    # 2. 세션 데이터 생성 (쿠키에 저장되는 형태)
    session_data = {
        "access_token": jwt_token,
        "refresh_token": "dummy-refresh-token",
        "expires_at": decoded_jwt.get("exp", 0),
    }

    # JSON → Base64 인코딩
    json_str = json.dumps(session_data)
    encoded = base64.b64encode(json_str.encode()).decode()

    # 실제 쿠키 값 형태로 만들기
    cookie_value = f"base64-{encoded}"

    print(f"\n🍪 Cookie value (first 100 chars): {cookie_value[:100]}...")
    print(f"Cookie length: {len(cookie_value)}")

    # 3. 인증 서비스 테스트
    auth_service = get_unified_auth_service()

    try:
        user_info = await auth_service.authenticate_token(cookie_value)
        print("\n✅ Authentication successful!")
        print(f"User ID: {user_info.get('id')}")
        print(f"Email: {user_info.get('email')}")
        print(f"Role: {user_info.get('role')}")
        print(f"Organization ID: {user_info.get('organization_id')}")

        # 권한 확인 테스트
        role = user_info.get("role", "user")
        is_admin = auth_service.check_permission(role, "admin")
        is_teacher = auth_service.check_permission(role, "teacher")
        is_user = auth_service.check_permission(role, "user")

        print(f"\n권한 확인 (현재 role: {role}):")
        print(f"- Admin 권한: {is_admin}")
        print(f"- Teacher 권한: {is_teacher}")
        print(f"- User 권한: {is_user}")

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_jwt_auth())
