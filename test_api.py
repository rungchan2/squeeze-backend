"""
Basic API testing script
간단한 API 테스트를 위한 스크립트
"""
import asyncio
import sys
from datetime import datetime
from app.services.nlp import calculate_word_frequency, get_text_stats
from app.services.auth import create_token_for_user, authenticate_user
from app.models.schemas import UserInDB


async def test_nlp_service():
    """NLP 서비스 테스트"""
    print("=== NLP Service Test ===")

    test_text = "팀워크는 소통과 협업을 통해 달성된다. 리더십과 책임감이 중요하며, 서로 신뢰하는 관계를 구축해야 한다."

    try:
        # 단어 빈도 분석
        word_frequency = calculate_word_frequency(test_text, top_n=10)
        print("Word Frequency Analysis:")
        for word, count in word_frequency:
            print(f"  - {word}: {count}")

        # 텍스트 통계
        stats = get_text_stats(test_text)
        print("\nText Statistics:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")

        print("✓ NLP Service test passed")

    except Exception as e:
        print(f"✗ NLP Service test failed: {e}")
        return False

    return True


async def test_auth_service():
    """인증 서비스 테스트"""
    print("\n=== Auth Service Test ===")

    try:
        from app.models.schemas import UserRole

        # 임시 사용자 생성
        test_user = UserInDB(
            id="test-user-123",
            email="test@example.com",
            role=UserRole.TEACHER,
            created_at=datetime.now(),
            hashed_password="fake-hash",
            is_active=True,
        )

        # 토큰 생성
        token = create_token_for_user(test_user)
        print(f"Generated token: {token[:50]}...")

        # 사용자 인증 테스트
        auth_user = await authenticate_user("teacher@example.com", "teacher123")
        if auth_user:
            print(f"Authentication successful: {auth_user.email} ({auth_user.role})")
        else:
            print("Authentication failed (expected for non-existing user)")

        print("✓ Auth Service test passed")

    except Exception as e:
        print(f"✗ Auth Service test failed: {e}")
        return False

    return True


async def test_analysis_service():
    """분석 서비스 테스트"""
    print("\n=== Analysis Service Test ===")

    try:
        from app.services.analysis import analyze_text, group_words

        test_text = "협업은 팀의 성공을 위해 중요합니다. 소통을 통해 팀워크를 발전시킬 수 있습니다."

        # 텍스트 분석
        analysis_result = await analyze_text(test_text, use_cache=False)
        print("Text Analysis Result:")
        print(f"  - Total words: {analysis_result['total_words']}")
        print(f"  - Unique words: {analysis_result['unique_words']}")
        print(f"  - Top words: {analysis_result['word_frequency'][:3]}")

        # 단어 그룹핑 테스트
        test_words = ["협업", "팀워크", "소통", "리더십", "책임", "신뢰"]
        grouping_result = await group_words(test_words, num_groups=2)
        print("\nWord Grouping Result:")
        print(f"  - Total groups: {grouping_result['total_groups']}")
        for i, group in enumerate(grouping_result["groups"]):
            print(f"  - Group {i+1}: {group['words']}")

        print("✓ Analysis Service test passed")

    except Exception as e:
        print(f"✗ Analysis Service test failed: {e}")
        return False

    return True


async def test_cache_service():
    """캐시 서비스 테스트"""
    print("\n=== Cache Service Test ===")

    try:
        from app.services.cache import get_cache_key, get_cached_value, set_cached_value

        # 캐시 키 생성 테스트
        cache_key = get_cache_key("test", user_id="123", text="sample")
        print(f"Generated cache key: {cache_key}")

        # 캐시 저장/조회 테스트 (Redis가 실행 중이지 않으면 실패할 수 있음)
        test_data = {"message": "test data", "timestamp": datetime.now().isoformat()}

        # 이 부분은 Redis가 연결되지 않으면 실패할 수 있음
        saved = await set_cached_value("test-key", test_data)
        if saved:
            cached_data = await get_cached_value("test-key")
            print(f"Cache test successful: {cached_data}")
        else:
            print("Cache not available (Redis not connected)")

        print("✓ Cache Service test passed")

    except Exception as e:
        print(f"✗ Cache Service test failed: {e}")
        return False

    return True


async def run_all_tests():
    """모든 테스트 실행"""
    print("Starting API Tests...")
    print(f"Test time: {datetime.now().isoformat()}")

    tests = [
        test_nlp_service(),
        test_auth_service(),
        test_analysis_service(),
        test_cache_service(),
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    passed = sum(1 for result in results if result is True)
    total = len(results)

    print("\n=== Test Summary ===")
    print(f"Passed: {passed}/{total}")

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
