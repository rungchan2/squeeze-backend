"""
통합 인증 시스템 테스트
실제 토큰 형식을 사용한 테스트
"""

import asyncio
import sys
from app.services.supabase_unified_auth import authenticate_token
from app.services.supabase_token_extractor import get_token_extractor


def get_sample_session_token():
    """실제와 유사한 세션 토큰 샘플"""
    # 이것은 문서에서 확인한 첫 번째 토큰 형식입니다
    return "base64-eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSklVekkxTmlJc0ltdHBaQ0k2SWpWNUwzWTBTVEZYTkZNMFVVMXRNVFlpTENKMGVYQWlPaUpLVjFRaWZRLmV5SmhZV3dpT2lKaFlXd3hJaXdpWVc1eUlqcGJleUp0WlhSb2IyUWlPaUp2WVhWMGFDSXNJblJwYldWemRHRnRjQ0k2TVRjMU5EUTROamszT1gxZExDSmhjSEJmYldWMFlXUmhkR0VpT25zaWIzSm5ZVzVwZW1GMGFXOXVYMmxrSWpvaU1tTTRNVGd5WTJFdFltWXlNaTAwTmpBMUxXSmpaVGt0TURVNFpUUTVORE5oTm1NMUlpd2ljSEp2Wm1sc1pWOXBaQ0k2SW1Kak4yUXpaRFl4TFdRd1l6VXRORGMxTkMwNVpqWTFMVFEwTldWaVl6azNPVE15WXlJc0luSnZiR1VpT2lKaFpHMXBiaUo5TENKaGRXUWlPaUpoZFhSb1pXNTBhV05oZEdWa0lpd2laVzFoYVd3aU9pSnNaV1ZvTURrd056ZEFaMjFoYVd3dVkyOXRJaXdpWlhod0lqb3hOelUwTkRrd05UYzVMQ0pwWVhRaU9qRTNOVFEwT0RZNU56a3NJbWx6WDJGdWIyNTViVzkxY3lJNlptRnNjMlVzSW1semN5STZJbWgwZEhCek9pOHZaV2R3ZEhWMGIzcGtabU5vYkdsdmRXVndhR3d1YzNWd1lXSmhjMlV1WTI4dllYVjBhQzkyTVNJc0luQm9iMjVsSWpvaUlpd2ljbTlzWlNJNkltRjFkR2hsYm5ScFkyRjBaV1FpTENKelpYTnphVzl1WDJsa0lqb2lNV1poTWpReFkyRXRZVGRtTmkwME1qSTFMV0ZtWmpndE9EazVPV1F4WldZMVptUTBJaXdpYzNWaUlqb2lZbU0zWkROa05qRXRaREJqTlMwME56VTBMVGxtTmpVdE5EUTFaV0pqT1RjNU16SmpJaXdpZFhObGNsOXRaWFJoWkdGMFlTSTZleUpsYldGcGJDSTZJbXhsWldnd09UQTNOMEJuYldGcGJDNWpiMjBpTENKbWFYSnpkRjl1WVcxbElqb2llWGtpTENKc1lYTjBYMjVoYldVaU9pSjVlU0lzSW5CeWIyWnBiR1ZmYVcxaFoyVWlPaUpvZEhSd2N6b3ZMMlZuY0hSMWRHOTZaR1pqYUd4cGIzVmxjR2hzTG5OMWNHRmlZWE5sTG1OdkwzTjBiM0poWjJVdmRqRXZiMkpxWldOMEwzQjFZbXhwWXk5cGJXRm5aWE12Y0hWaWJHbGpMMkpqTjJRelpEWXhMV1F3WXpVdE5EYzFOQzA1WmpZMUxUUTBOV1ZpWXprM09UTXlZeTh3TTE4NFh6RTNORFEyTVRZMU16TXlNVEV1YzNabkluMTkuU1BEakFnT1RLMHNtWmFuNzR6OUxnYUpUOFJoZFRmQ29VOURreVFFX2ZOYyIsInRva2VuX3R5cGUiOiJiZWFyZXIiLCJleHBpcmVzX2luIjozNjAwLCJleHBpcmVzX2F0IjoxNzU0NDkwNTc5LCJyZWZyZXNoX3Rva2VuIjoiNXBqcG1peXllY3JtIiwidXNlciI6eyJpZCI6ImJjN2QzZDYxLWQwYzUtNDc1NC05ZjY1LTQ0NWViYzk3OTMyYyIsImF1ZCI6ImF1dGhlbnRpY2F0ZWQiLCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImVtYWlsIjoibGVlaDA5MDc3QGdtYWlsLmNvbSIsImVtYWlsX2NvbmZpcm1lZF9hdCI6IjIwMjUtMDQtMTJUMTU6MDM6MTQuNjEwNTAzWiIsInBob25lIjoiIiwiY29uZmlybWVkX2F0IjoiMjAyNS0wNC0xMlQxNTowMzoxNC42MTA1MDNaIiwibGFzdF9zaWduX2luX2F0IjoiMjAyNS0wOC0wNlQxMzoyOTozOC45OTkwMTYxNDNaIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiLCJnb29nbGUiXX0sInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0s3YWpMMXNFX0hfNkJaRThEM19OSGs1LXZKTFpYVW4yc0NkcFMzT2UtU2ZaWVZWZz1zOTYtYyIsImVtYWlsIjoibGVlaDA5MDc3QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWUiOiLsnbTtnazssKwiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJuYW1lIjoi7J207Z2s7LCsIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSzdhakwxc0VfSF82QlpFOEQzX05IazUtdkpMWlhVbjJzQ2RwUzNPZS1TZlpZVlZnPXM5Ni1jIiwicHJvdmlkZXJfaWQiOiIxMDI1NjIzNzQ5NDE4MzE5ODMzMTQiLCJzdWIiOiIxMDI1NjIzNzQ5NDE4MzE5ODMzMTQifX0="


async def test_token_extraction():
    """토큰 추출 테스트"""
    print("=== Token Extraction Test ===")

    sample_token = get_sample_session_token()
    extractor = get_token_extractor()

    try:
        # 1. 사용자 정보 직접 추출
        user_info = extractor.extract_user_from_session_token(sample_token)
        print("✓ Direct user extraction successful:")
        print(f"  - User ID: {user_info.get('id')}")
        print(f"  - Email: {user_info.get('email')}")
        print(f"  - Role: {user_info.get('role')}")
        print(f"  - Profile Image: {user_info.get('profile_image') is not None}")

        # 2. JWT 토큰 추출
        jwt_token = extractor.extract_jwt_from_session_token(sample_token)
        print("\n✓ JWT extraction successful:")
        print(f"  - JWT length: {len(jwt_token)}")
        print(f"  - JWT preview: {jwt_token[:50]}...")

        return True

    except Exception as e:
        print(f"✗ Token extraction failed: {e}")
        return False


async def test_unified_auth():
    """통합 인증 테스트"""
    print("\n=== Unified Authentication Test ===")

    sample_token = get_sample_session_token()

    try:
        user_info = await authenticate_token(sample_token)
        print("✓ Unified authentication successful:")
        print(f"  - User ID: {user_info.get('id')}")
        print(f"  - Email: {user_info.get('email')}")
        print(f"  - Role: {user_info.get('role')}")
        print(f"  - First Name: {user_info.get('first_name')}")
        print(f"  - Profile Image: {user_info.get('profile_image') is not None}")

        return True

    except Exception as e:
        print(f"✗ Unified authentication failed: {e}")
        return False


async def test_different_formats():
    """다양한 토큰 형식 테스트"""
    print("\n=== Different Token Format Test ===")

    sample_token = get_sample_session_token()

    formats = [
        (sample_token, "Full base64- session token"),
        (sample_token[7:], "Without base64- prefix"),
        (f"Bearer {sample_token[7:]}", "With Bearer prefix"),
    ]

    success_count = 0

    for token, description in formats:
        try:
            user_info = await authenticate_token(token)
            print(f"✓ {description}: Success ({user_info.get('email')})")
            success_count += 1
        except Exception as e:
            print(f"✗ {description}: Failed ({str(e)[:50]})")

    print(f"\nFormat compatibility: {success_count}/{len(formats)}")
    return success_count > 0


async def run_all_tests():
    """모든 테스트 실행"""
    print("Starting Unified Auth Tests...")
    print("=" * 50)

    tests = [test_token_extraction(), test_unified_auth(), test_different_formats()]

    results = await asyncio.gather(*tests, return_exceptions=True)

    passed = sum(1 for result in results if result is True)
    total = len(results)

    print(f"\n{'='*50}")
    print(f"Test Summary: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
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
