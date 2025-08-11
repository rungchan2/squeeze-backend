"""
텍스트 분석 서비스
NLP 및 캐싱을 통합한 텍스트 분석 기능
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from app.services.nlp import (
    calculate_word_frequency,
    analyze_multiple_texts,
    get_text_stats,
)
from app.services.cache import (
    get_cached_analysis,
    set_cached_analysis,
    get_cached_range_analysis,
    set_cached_range_analysis,
    get_cached_value,
    set_cached_value,
    get_cache_key,
)
from app.db.supabase import get_supabase_client
from app.core.exceptions import TextAnalysisError, ValidationError

logger = structlog.get_logger()


async def analyze_text(
    text: str,
    top_n: Optional[int] = None,
    min_count: int = 1,
    custom_stopwords: List[str] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    단일 텍스트를 분석합니다.

    Args:
        text: 분석할 텍스트
        top_n: 상위 N개 단어
        min_count: 최소 출현 횟수
        custom_stopwords: 추가 불용어
        use_cache: 캐시 사용 여부

    Returns:
        분석 결과
    """
    try:
        # 입력 검증
        if not text or not text.strip():
            raise ValidationError("텍스트가 비어있습니다")

        text = text.strip()

        # 캐시 조회
        cache_options = {
            "top_n": top_n,
            "min_count": min_count,
            "custom_stopwords": custom_stopwords,
        }

        cached_result = None
        if use_cache:
            cached_result = await get_cached_analysis(text, cache_options)
            if cached_result:
                logger.debug("Cache hit for text analysis")
                return cached_result

        # 단어 빈도 분석
        word_frequency = calculate_word_frequency(
            text=text,
            top_n=top_n,
            min_count=min_count,
            custom_stopwords=custom_stopwords,
        )

        # 텍스트 통계
        stats = get_text_stats(text)

        # 결과 구성
        result = {
            "word_frequency": word_frequency,
            "total_words": stats["total_words"],
            "unique_words": stats["unique_words"],
            "analyzed_at": datetime.utcnow().isoformat(),
            "cache_hit": False,
        }

        # 캐시 저장
        if use_cache:
            await set_cached_analysis(text, result, cache_options)

        return result

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise TextAnalysisError(f"텍스트 분석 중 오류가 발생했습니다: {str(e)}")


async def analyze_posts_range(
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
    top_n: int = 50,
    min_count: int = 1,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    범위별 posts 데이터를 분석합니다.

    Args:
        journey_id: Journey ID
        journey_week_id: Journey Week ID
        mission_instance_id: Mission Instance ID
        user_id: User ID
        top_n: 상위 N개 단어
        min_count: 최소 출현 횟수
        force_refresh: 캐시 무시 여부

    Returns:
        분석 결과
    """
    try:
        # 파라미터 검증
        if not any([journey_id, journey_week_id, mission_instance_id, user_id]):
            raise ValidationError("최소 하나의 범위 파라미터가 필요합니다")

        # 캐시 조회 (force_refresh가 False인 경우)
        cached_result = None
        if not force_refresh:
            cached_result = await get_cached_range_analysis(
                journey_id=journey_id,
                journey_week_id=journey_week_id,
                mission_instance_id=mission_instance_id,
                user_id=user_id,
                top_n=top_n,
                min_count=min_count,
            )

            if cached_result:
                logger.debug("Cache hit for range analysis")
                cached_result["cache_hit"] = True
                return cached_result

        # 데이터베이스에서 posts 조회
        posts_data = await _fetch_posts_from_db(
            journey_id=journey_id,
            journey_week_id=journey_week_id,
            mission_instance_id=mission_instance_id,
            user_id=user_id,
        )

        if not posts_data:
            logger.warning("No posts found for given range parameters")
            return {
                "scope": _determine_analysis_scope(
                    journey_id, journey_week_id, mission_instance_id, user_id
                ),
                "range": _build_range_info(
                    journey_id, journey_week_id, mission_instance_id, user_id
                ),
                "cache_hit": False,
                "word_frequency": [],
                "total_posts": 0,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        # 텍스트 추출
        texts = [post.get("content", "") for post in posts_data if post.get("content")]

        if not texts:
            logger.warning("No text content found in posts")
            return {
                "scope": _determine_analysis_scope(
                    journey_id, journey_week_id, mission_instance_id, user_id
                ),
                "range": _build_range_info(
                    journey_id, journey_week_id, mission_instance_id, user_id
                ),
                "cache_hit": False,
                "word_frequency": [],
                "total_posts": len(posts_data),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        # 여러 텍스트 분석
        word_frequency = analyze_multiple_texts(
            texts=texts, top_n=top_n, min_count=min_count
        )

        # 결과 구성
        result = {
            "scope": _determine_analysis_scope(
                journey_id, journey_week_id, mission_instance_id, user_id
            ),
            "range": _build_range_info(
                journey_id, journey_week_id, mission_instance_id, user_id
            ),
            "cache_hit": False,
            "word_frequency": word_frequency,
            "total_posts": len(posts_data),
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        # 캐시 저장
        await set_cached_range_analysis(
            result=result,
            journey_id=journey_id,
            journey_week_id=journey_week_id,
            mission_instance_id=mission_instance_id,
            user_id=user_id,
            top_n=top_n,
            min_count=min_count,
        )

        return result

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing posts range: {e}")
        raise TextAnalysisError(f"범위별 분석 중 오류가 발생했습니다: {str(e)}")


async def group_words(
    words: List[str],
    num_groups: int = 3,
    method: str = "semantic",
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    단어 리스트를 그룹화합니다.

    Args:
        words: 그룹화할 단어 리스트
        num_groups: 그룹 개수
        method: 그룹화 방법 ("semantic", "frequency")
        use_cache: 캐시 사용 여부

    Returns:
        그룹화 결과
    """
    try:
        # 입력 검증
        if not words:
            raise ValidationError("단어 리스트가 비어있습니다")

        if num_groups < 1 or num_groups > len(words):
            raise ValidationError("그룹 개수가 유효하지 않습니다")

        # 캐시 키 생성
        cache_key = None
        if use_cache:
            # 단어 리스트를 정렬하여 일관된 캐시 키 생성
            sorted_words = sorted(words)
            cache_key = get_cache_key(
                "word_grouping",
                words_hash=hash(tuple(sorted_words)),
                num_groups=num_groups,
                method=method,
            )

            # 캐시 조회
            cached_result = await get_cached_value(cache_key)
            if cached_result:
                logger.debug("Cache hit for word grouping")
                cached_result["cache_hit"] = True
                return cached_result

        # TODO: 실제 단어 그룹화 로직 구현
        # 현재는 간단한 알파벳/길이 기반 그룹화

        groups = []
        words_per_group = max(1, len(words) // num_groups)

        for i in range(num_groups):
            start_idx = i * words_per_group
            end_idx = start_idx + words_per_group if i < num_groups - 1 else len(words)
            group_words = words[start_idx:end_idx]

            # 그룹의 대표 단어를 label로 사용
            # 가장 긴 단어를 대표로 선택 (보통 더 구체적인 의미를 가짐)
            if group_words:
                representative_word = max(group_words, key=len)
                label = f"{representative_word} 관련"
            else:
                label = f"그룹 {i + 1}"

            groups.append({"label": label, "words": group_words})

        result = {
            "groups": groups,
            "total_groups": len(groups),
            "method": method,
            "grouped_at": datetime.utcnow().isoformat(),
            "cache_hit": False,
        }

        # 캐시 저장
        if use_cache and cache_key:
            await set_cached_value(cache_key, result, cache_type="word_grouping")

        return result

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error grouping words: {e}")
        raise TextAnalysisError(f"단어 그룹화 중 오류가 발생했습니다: {str(e)}")


async def _fetch_posts_from_db(
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    데이터베이스에서 posts를 조회합니다.
    """
    try:
        supabase = get_supabase_client()

        # posts 테이블 쿼리 구성
        query = supabase.table("posts").select("id, content, created_at, user_id")

        # 필터 적용
        if user_id:
            query = query.eq("user_id", user_id)

        if mission_instance_id:
            query = query.eq("mission_instance_id", mission_instance_id)

        # TODO: journey_id, journey_week_id 필터링
        # 실제 데이터베이스 스키마에 맞게 조정 필요

        result = query.execute()

        if result.data:
            logger.info(f"Fetched {len(result.data)} posts from database")
            return result.data
        else:
            logger.info("No posts found for given parameters")
            return []

    except Exception as e:
        logger.error(f"Error fetching posts from database: {e}")
        # 개발 중에는 임시 데이터 반환
        return _get_mock_posts_data()


def _get_mock_posts_data() -> List[Dict[str, Any]]:
    """
    개발용 임시 posts 데이터를 반환합니다.
    """
    return [
        {
            "id": "post-1",
            "content": "팀워크는 소통과 협업을 통해 달성된다. 서로 신뢰하고 책임감을 가지는 것이 중요하다.",
            "user_id": "user-1",
            "created_at": "2024-01-01T10:00:00Z",
        },
        {
            "id": "post-2",
            "content": "리더십은 팀원들과 소통하며 방향을 제시하는 능력이다. 협업 정신이 필요하다.",
            "user_id": "user-2",
            "created_at": "2024-01-01T11:00:00Z",
        },
        {
            "id": "post-3",
            "content": "프로젝트 성공을 위해서는 명확한 목표 설정과 팀워크가 필수적이다.",
            "user_id": "user-3",
            "created_at": "2024-01-01T12:00:00Z",
        },
    ]


def _determine_analysis_scope(
    journey_id: Optional[str],
    journey_week_id: Optional[str],
    mission_instance_id: Optional[str],
    user_id: Optional[str],
) -> str:
    """
    분석 범위를 결정합니다.
    """
    if user_id:
        return "USER"
    elif mission_instance_id:
        return "MISSION_INSTANCE"
    elif journey_week_id:
        return "JOURNEY_WEEK"
    elif journey_id:
        return "JOURNEY"
    else:
        return "UNKNOWN"


def _build_range_info(
    journey_id: Optional[str],
    journey_week_id: Optional[str],
    mission_instance_id: Optional[str],
    user_id: Optional[str],
) -> Dict[str, str]:
    """
    범위 정보를 구성합니다.
    """
    range_info = {}

    if journey_id:
        range_info["journey_id"] = journey_id
    if journey_week_id:
        range_info["journey_week_id"] = journey_week_id
    if mission_instance_id:
        range_info["mission_instance_id"] = mission_instance_id
    if user_id:
        range_info["user_id"] = user_id

    return range_info
