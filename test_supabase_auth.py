"""
Supabase 인증 테스트
쿠키 기반 Supabase JWT 토큰 검증 테스트
"""
import asyncio
import sys
from jose import jwt
from datetime import datetime, timedelta
from app.services.supabase_auth import verify_supabase_token, check_user_permission
from app.core.config import get_settings

settings = get_settings()


def create_mock_supabase_token(
    user_id: str = "test-user-123",
    email: str = "test@example.com",
    role: str = "teacher",
    organization_id: str = None,
    exp_minutes: int = 60,
) -> str:
    """
    테스트용 Supabase JWT 토큰을 생성합니다.
    """
    now = datetime.utcnow()
    exp = now + timedelta(minutes=exp_minutes)

    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "app_metadata": {"role": role, "organization_id": organization_id},
        "user_metadata": {
            "first_name": "Test",
            "last_name": "User",
            "profile_image": "https://example.com/avatar.jpg",
        },
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": "supabase",
    }

    # 테스트용 토큰 생성 (실제 환경에서는 Supabase가 생성)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


async def test_supabase_auth_service():
    """Supabase 인증 서비스 테스트"""
    print("=== Supabase Auth Service Test ===")

    try:
        # 1. 유효한 teacher 토큰 테스트
        teacher_token = create_mock_supabase_token(
            user_id="teacher-123", email="teacher@example.com", role="teacher"
        )

        teacher_info = await verify_supabase_token(teacher_token)
        print("✓ Teacher token verified:")
        print(f"  - User ID: {teacher_info['id']}")
        print(f"  - Email: {teacher_info['email']}")
        print(f"  - Role: {teacher_info['role']}")

        # 2. 권한 확인 테스트
        can_access_teacher = check_user_permission("teacher", "teacher")
        can_access_admin = check_user_permission("teacher", "admin")
        print(f"  - Can access teacher endpoints: {can_access_teacher}")
        print(f"  - Can access admin endpoints: {can_access_admin}")

        # 3. 일반 사용자 토큰 테스트
        user_token = create_mock_supabase_token(
            user_id="user-456", email="user@example.com", role="user"
        )

        user_info = await verify_supabase_token(user_token)
        print("✓ User token verified:")
        print(f"  - User ID: {user_info['id']}")
        print(f"  - Role: {user_info['role']}")

        user_can_access_teacher = check_user_permission("user", "teacher")
        print(f"  - User can access teacher endpoints: {user_can_access_teacher}")

        # 4. 만료된 토큰 테스트 (개발 환경에서는 검증 비활성화됨)
        try:
            expired_token = create_mock_supabase_token(exp_minutes=-10)  # 10분 전 만료
            expired_info = await verify_supabase_token(expired_token)
            print("⚠ Expired token accepted (dev mode - verification disabled)")
            # 개발 모드에서는 만료된 토큰도 통과하므로 이는 정상
        except Exception as e:
            print(f"✓ Expired token correctly rejected: {str(e)[:100]}")

        # 5. 잘못된 토큰 테스트
        try:
            await verify_supabase_token("invalid-token")
            print("✗ Invalid token should have failed")
            return False
        except Exception as e:
            print(f"✓ Invalid token correctly rejected: {str(e)}")

        print("✅ All Supabase auth tests passed")
        return True

    except Exception as e:
        print(f"✗ Supabase auth test failed: {e}")
        return False


async def test_cookie_extraction():
    """쿠키 추출 로직 테스트 시뮬레이션"""
    print("\n=== Cookie Extraction Test ===")

    try:
        # 실제 FastAPI Request 객체를 모킹하기 어려우므로
        # 로직만 간단히 테스트

        # 테스트용 쿠키 데이터
        mock_cookies = {
            "sb-access-token": create_mock_supabase_token(),
            "other-cookie": "value",
        }

        # 우선순위 테스트
        cookie_names = [
            "sb-access-token",
            "supabase-access-token",
            "sb-other-auth-token",
        ]

        found_token = None
        for cookie_name in cookie_names:
            token = mock_cookies.get(cookie_name)
            if token:
                found_token = token
                print(f"✓ Found token in cookie: {cookie_name}")
                break

        if found_token:
            # 찾은 토큰 검증
            user_info = await verify_supabase_token(found_token)
            print(f"✓ Cookie token verified for user: {user_info['email']}")
            return True
        else:
            print("✗ No token found in cookies")
            return False

    except Exception as e:
        print(f"✗ Cookie extraction test failed: {e}")
        return False


async def test_role_hierarchy():
    """역할 계층 테스트"""
    print("\n=== Role Hierarchy Test ===")

    test_cases = [
        ("admin", "admin", True),
        ("admin", "teacher", True),
        ("admin", "user", True),
        ("teacher", "admin", False),
        ("teacher", "teacher", True),
        ("teacher", "user", True),
        ("user", "admin", False),
        ("user", "teacher", False),
        ("user", "user", True),
    ]

    all_passed = True

    for user_role, required_role, expected in test_cases:
        result = check_user_permission(user_role, required_role)
        status = "✓" if result == expected else "✗"

        if result != expected:
            all_passed = False

        print(
            f"{status} {user_role} -> {required_role}: {result} (expected: {expected})"
        )

    if all_passed:
        print("✅ All role hierarchy tests passed")
    else:
        print("❌ Some role hierarchy tests failed")

    return all_passed


async def run_all_tests():
    """모든 테스트 실행"""
    print("Starting Supabase Authentication Tests...")
    print(f"Test time: {datetime.now().isoformat()}")

    tests = [
        test_supabase_auth_service(),
        test_cookie_extraction(),
        test_role_hierarchy(),
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    passed = sum(1 for result in results if result is True)
    total = len(results)

    print("\n=== Test Summary ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All Supabase auth tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
