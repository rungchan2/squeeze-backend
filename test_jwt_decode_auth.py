"""
JWT 디코드 인증 테스트
"""
import asyncio
import base64
import json
from app.services.supabase_unified_auth import get_unified_auth_service


async def test_jwt_decode_auth():
    """JWT 디코드 인증 테스트"""

    # 테스트용 JWT 토큰 (실제 토큰으로 교체 필요)
    # 이 JWT는 app_metadata에 role: admin을 포함하고 있다고 가정
    jwt_token = """eyJhbGciOiJIUzI1NiIsImtpZCI6InNvbWUtand0LWtleSIsInR5cCI6IkpXVCJ9.eyJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvYXV0aCIsInRpbWVzdGFtcCI6MTc1NDQ5NzAwMX1dLCJhcHBfbWV0YWRhdGEiOnsib3JnYW5pemF0aW9uX2lkIjoiMmM4MTgyY2EtYmYyMi00NjA1LWJjZTktMDU4ZTQ5NDNhNmM1IiwicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCIsImdvb2dsZSJdLCJyb2xlIjoiYWRtaW4ifSwiYXVkIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoibGVlaDA5MDc3QGdtYWlsLmNvbSIsImV4cCI6MTc1NDkyNDIwMywiaWF0IjoxNzU0OTIwNjAzLCJpc19hbm9ueW1vdXMiOmZhbHNlLCJpc3MiOiJodHRwczovL2VncHR1dG96ZGZjaGxpb3VlcGhsLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJwaG9uZSI6IiIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwic2Vzc2lvbl9pZCI6IjZhNDBmMDE3LWEyMjctNDZiYi04YTE3LTRlN2NhMWJlZGU5YSIsInN1YiI6ImJjN2QzZDYxLWQwYzUtNDc1NC05ZjY1LTQ0NWViYzk3OTMyYyIsInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0s3YWpMMXNFX0hfNkJaRThEMl9OSGs1LXZKTFpYVW4yc0NkcFMzT2UtU2ZaWVZWZz1zOTYtYyIsImVtYWlsIjoibGVlaDA5MDc3QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJzdF9uYW1lIjoieXkiLCJmdWxsX25hbWUiOiLsnbTtnazssKwiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJsYXN0X25hbWUiOiJ5eSIsIm5hbWUiOiLsnbTtnazssKwiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLN2FqTDFzRV9IXzZCWkU4RDNfTkhrNS12SkxaWFVuMnNDZHBTM09lLVNmWllWVmc9czk2LWMiLCJwcm9maWxlX2ltYWdlIjoiaHR0cHM6Ly9lZ3B0dXRvemRmY2hsaW91ZXBobC5zdXBhYmFzZS5jby9zdG9yYWdlL3YxL29iamVjdC9wdWJsaWMvaW1hZ2VzL3B1YmxpYy9iYzdkM2Q2MS1kMGM1LTQ3NTQtOWY2NS00NDVlYmM5NzkzMmMvMDNfOF8xNzQ0NjE2NTMzMjExLnN2ZyIsInByb3ZpZGVyX2lkIjoiMTAyNTYyMzc0OTQxODMxOTgzMzE0Iiwic3ViIjoiMTAyNTYyMzc0OTQxODMxOTgzMzE0In19.signature"""

    # 세션 데이터 생성 (쿠키에 저장되는 형태)
    session_data = {
        "access_token": jwt_token.strip(),
        "refresh_token": "some-refresh-token",
        "expires_at": 1754924203,
    }

    # JSON → Base64 인코딩
    json_str = json.dumps(session_data)
    encoded = base64.b64encode(json_str.encode()).decode()

    # 실제 쿠키 값 형태로 만들기
    cookie_value = f"base64-{encoded}"

    print(f"Cookie value (first 100 chars): {cookie_value[:100]}...")
    print(f"Cookie length: {len(cookie_value)}")

    # 인증 서비스 테스트
    auth_service = get_unified_auth_service()

    try:
        user_info = await auth_service.authenticate_token(cookie_value)
        print("\n✅ Authentication successful!")
        print(f"User ID: {user_info.get('id')}")
        print(f"Email: {user_info.get('email')}")
        print(f"Role: {user_info.get('role')}")  # admin이어야 함
        print(f"Organization ID: {user_info.get('organization_id')}")

        # 권한 확인 테스트
        is_admin = auth_service.check_permission(user_info.get("role"), "admin")
        is_teacher = auth_service.check_permission(user_info.get("role"), "teacher")
        is_user = auth_service.check_permission(user_info.get("role"), "user")

        print("\n권한 확인:")
        print(f"- Admin 권한: {is_admin}")  # True여야 함
        print(f"- Teacher 권한: {is_teacher}")  # True여야 함
        print(f"- User 권한: {is_user}")  # True여야 함

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_jwt_decode_auth())
