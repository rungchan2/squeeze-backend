"""
Redis 캐싱 테스트
"""
import asyncio
import time
from app.services.analysis import analyze_text, group_words
from app.services.cache import get_cache_stats, invalidate_analysis_cache
from app.db.redis import check_redis_connection


async def test_redis_caching():
    """Redis 캐싱 기능 테스트"""

    print("=" * 60)
    print("Redis 연결 상태 확인")
    print("=" * 60)

    # Redis 연결 확인
    is_connected = await check_redis_connection()
    if not is_connected:
        print("❌ Redis 연결 실패!")
        return
    else:
        print("✅ Redis 연결 성공!")

    # 캐시 통계
    stats = await get_cache_stats()
    print(f"캐시 통계: {stats}")

    print("\n" + "=" * 60)
    print("텍스트 분석 캐싱 테스트")
    print("=" * 60)

    test_text = "팀워크는 매우 중요합니다. 소통과 협업을 통해 더 나은 결과를 만들 수 있습니다. 신뢰와 책임감이 바탕이 되어야 합니다."

    # 첫 번째 요청 (캐시 없음)
    print("첫 번째 요청 (캐시 miss 예상)...")
    start_time = time.time()
    result1 = await analyze_text(test_text, top_n=10, use_cache=True)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {result1.get('cache_hit', False)}")
    print(f"단어 수: {len(result1.get('word_frequency', []))}")

    # 두 번째 요청 (캐시 히트 예상)
    print("\n두 번째 요청 (캐시 hit 예상)...")
    start_time = time.time()
    result2 = await analyze_text(test_text, top_n=10, use_cache=True)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {result2.get('cache_hit', False)}")
    print(f"단어 수: {len(result2.get('word_frequency', []))}")

    print("\n" + "=" * 60)
    print("단어 그룹핑 캐싱 테스트")
    print("=" * 60)

    test_words = ["소통", "협업", "팀워크", "신뢰", "책임", "리더십", "창의", "혁신", "도전", "성장"]

    # 첫 번째 그룹핑 (캐시 없음)
    print("첫 번째 그룹핑 (캐시 miss 예상)...")
    start_time = time.time()
    grouping1 = await group_words(test_words, num_groups=3, use_cache=True)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {grouping1.get('cache_hit', False)}")
    print(f"그룹 수: {grouping1.get('total_groups', 0)}")
    for i, group in enumerate(grouping1.get("groups", [])):
        print(f"  그룹 {i+1}: {group['label']} - {group['words']}")

    # 두 번째 그룹핑 (캐시 히트 예상)
    print("\n두 번째 그룹핑 (캐시 hit 예상)...")
    start_time = time.time()
    grouping2 = await group_words(test_words, num_groups=3, use_cache=True)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {grouping2.get('cache_hit', False)}")
    print(f"그룹 수: {grouping2.get('total_groups', 0)}")

    print("\n" + "=" * 60)
    print("캐시 무효화 테스트")
    print("=" * 60)

    # 캐시 무효화
    print("모든 분석 캐시 무효화...")
    deleted_count = await invalidate_analysis_cache()
    print(f"무효화된 캐시 키: {deleted_count}개")

    # 무효화 후 다시 요청 (캐시 miss 예상)
    print("\n무효화 후 텍스트 분석 요청...")
    start_time = time.time()
    result3 = await analyze_text(test_text, top_n=10, use_cache=True)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {result3.get('cache_hit', False)}")

    print("\n" + "=" * 60)
    print("캐시 비활성화 테스트")
    print("=" * 60)

    # 캐시 비활성화 테스트
    print("캐시 비활성화 상태에서 분석...")
    start_time = time.time()
    result4 = await analyze_text(test_text, top_n=10, use_cache=False)
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.3f}초")
    print(f"Cache hit: {result4.get('cache_hit', False)}")

    # 최종 캐시 통계
    print("\n" + "=" * 60)
    print("최종 캐시 통계")
    print("=" * 60)
    final_stats = await get_cache_stats()
    print(f"최종 캐시 통계: {final_stats}")


if __name__ == "__main__":
    asyncio.run(test_redis_caching())
