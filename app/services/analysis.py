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
from app.db.supabase import get_supabase_client, get_supabase_admin_client
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
        # 분석 타입 로깅
        analysis_type = "개별 학생 분석" if user_id else "전체 학생 분석"
        logger.info(f"Starting {analysis_type}: journey_id={journey_id}, journey_week_id={journey_week_id}, mission_instance_id={mission_instance_id}, user_id={user_id}, top_n={top_n}, min_count={min_count}")
        
        # 파라미터 검증
        if not any([journey_id, journey_week_id, mission_instance_id, user_id]):
            raise ValidationError("최소 하나의 범위 파라미터가 필요합니다")
        
        # user_id가 제공된 경우 유효성 검증
        if user_id:
            is_valid_user = await _validate_user_access(
                user_id=user_id,
                journey_id=journey_id,
                journey_week_id=journey_week_id,
                mission_instance_id=mission_instance_id
            )
            if not is_valid_user:
                raise ValidationError(f"사용자 {user_id}는 해당 범위에 접근할 수 없습니다")

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
                # 이전 캐시에 source_texts가 없는 경우 빈 배열로 설정
                if "source_texts" not in cached_result:
                    cached_result["source_texts"] = []
                return cached_result

        # 데이터베이스에서 posts 조회
        posts_data = await _fetch_posts_from_db(
            journey_id=journey_id,
            journey_week_id=journey_week_id,
            mission_instance_id=mission_instance_id,
            user_id=user_id,
        )

        if not posts_data:
            logger.warning(f"No posts found for {analysis_type} with parameters: journey_id={journey_id}, journey_week_id={journey_week_id}, mission_instance_id={mission_instance_id}, user_id={user_id}")
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
                "source_texts": [],
            }

        # 텍스트 추출 - answers_data와 content 모두에서 추출
        texts = []
        for post in posts_data:
            # content 필드에서 텍스트 추출 (legacy missions)
            if post.get("content"):
                texts.append(post["content"])
            
            # answers_data에서 텍스트 추출 (modern missions)
            answers_data = post.get("answers_data")
            if answers_data and isinstance(answers_data, dict):
                answers = answers_data.get("answers", [])
                for answer in answers:
                    # 최신 구조: answer_text_plain 우선 사용 (HTML 태그 제거된 순수 텍스트)
                    answer_text_plain = answer.get("answer_text_plain", "")
                    if answer_text_plain and answer_text_plain.strip():
                        texts.append(answer_text_plain)
                    else:
                        # fallback: legacy HTML 데이터 사용
                        answer_text = answer.get("answer_text", "")
                        if answer_text and answer_text.strip():
                            texts.append(answer_text)

        if not texts:
            logger.warning(f"No text content found in {len(posts_data)} posts for {analysis_type}")
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
                "source_texts": [],
            }
        else:
            logger.info(f"Extracted {len(texts)} texts from {len(posts_data)} posts for {analysis_type}")

        # 여러 텍스트 분석
        word_frequency = analyze_multiple_texts(
            texts=texts, top_n=top_n, min_count=min_count
        )
        
        logger.info(f"Analysis completed for {analysis_type}: found {len(word_frequency)} words, {len(posts_data)} posts")

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
            "source_texts": texts,
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
        # RLS를 우회하여 모든 데이터에 접근하기 위해 admin client 사용
        supabase = get_supabase_admin_client()

        # posts 테이블 쿼리 구성 - 올바른 Supabase client 문법 사용
        if journey_id or journey_week_id:
            if journey_week_id:
                # journey_week_id로 mission_instance_ids 조회
                logger.info(f"Querying mission instances for journey_week_id: {journey_week_id}")
                mission_query = supabase.table("journey_mission_instances").select("id").eq("journey_week_id", journey_week_id)
                mission_result = mission_query.execute()
                
                logger.info(f"Mission query result: {mission_result.data}")
                
                if mission_result.data:
                    mission_ids = [item["id"] for item in mission_result.data]
                    logger.info(f"Found mission_ids: {mission_ids}")
                    
                    # 각 mission_id에 대해 posts 조회 (in 연산자 문제 회피)
                    all_posts = []
                    for mission_id in mission_ids:
                        posts_query = supabase.table("posts").select("id, content, answers_data, created_at, user_id").eq("mission_instance_id", mission_id)
                        
                        # user_id 필터 적용
                        if user_id:
                            posts_query = posts_query.eq("user_id", user_id)
                            logger.debug(f"Applying user_id filter: {user_id} for mission_id: {mission_id}")
                        
                        posts_result = posts_query.execute()
                        
                        if posts_result.data:
                            logger.info(f"Found {len(posts_result.data)} posts for mission_id: {mission_id}")
                            all_posts.extend(posts_result.data)
                    
                    logger.info(f"Total posts found: {len(all_posts)}")
                    return all_posts
                else:
                    logger.warning("No mission instances found for journey_week_id")
                    return []
                    
            elif journey_id:
                # journey_id로 journey_week_ids 먼저 조회
                logger.info(f"Querying journey weeks for journey_id: {journey_id}")
                week_query = supabase.table("journey_weeks").select("id").eq("journey_id", journey_id)
                week_result = week_query.execute()
                
                if week_result.data:
                    week_ids = [item["id"] for item in week_result.data]
                    logger.info(f"Found week_ids: {week_ids}")
                    
                    # 각 week_id에 대해 mission_instances 조회
                    all_posts = []
                    for week_id in week_ids:
                        mission_query = supabase.table("journey_mission_instances").select("id").eq("journey_week_id", week_id)
                        mission_result = mission_query.execute()
                        
                        if mission_result.data:
                            for mission_data in mission_result.data:
                                mission_id = mission_data["id"]
                                posts_query = supabase.table("posts").select("id, content, answers_data, created_at, user_id").eq("mission_instance_id", mission_id)
                                
                                # user_id 필터 적용
                                if user_id:
                                    posts_query = posts_query.eq("user_id", user_id)
                                    logger.debug(f"Applying user_id filter: {user_id} for mission_id: {mission_id}")
                                
                                posts_result = posts_query.execute()
                                
                                if posts_result.data:
                                    all_posts.extend(posts_result.data)
                    
                    logger.info(f"Total posts found for journey: {len(all_posts)}")
                    return all_posts
                else:
                    logger.warning("No journey weeks found for journey_id")
                    return []
        
        # 일반적인 posts 쿼리 (journey 필터링 없음)
        query = supabase.table("posts").select("id, content, answers_data, created_at, user_id")

        # 기타 필터 적용
        if user_id:
            query = query.eq("user_id", user_id)

        if mission_instance_id:
            query = query.eq("mission_instance_id", mission_instance_id)

        result = query.execute()

        if result.data:
            logger.info(f"Fetched {len(result.data)} posts from database")
            return result.data
        else:
            logger.info("No posts found for given parameters")
            return []

    except Exception as e:
        logger.error(f"Error fetching posts from database: {e}", exc_info=True)
        # 예외를 다시 발생시켜서 실제 문제를 확인
        raise e


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
    개별 사용자 분석과 전체 분석을 구분합니다.
    """
    if user_id:
        # 개별 사용자 분석
        if mission_instance_id:
            return "individual_user_mission"
        elif journey_week_id:
            return "individual_user_week"
        elif journey_id:
            return "individual_user_journey"
        else:
            return "individual_user"
    else:
        # 전체 분석
        if mission_instance_id:
            return "mission_instance"
        elif journey_week_id:
            return "journey_week"
        elif journey_id:
            return "journey"
        else:
            return "unknown"


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


async def _validate_user_access(
    user_id: str,
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
) -> bool:
    """
    사용자가 해당 범위에 접근할 수 있는지 검증합니다.
    
    Args:
        user_id: 검증할 사용자 ID
        journey_id: Journey ID
        journey_week_id: Journey Week ID
        mission_instance_id: Mission Instance ID
    
    Returns:
        접근 가능 여부
    """
    try:
        supabase = get_supabase_admin_client()
        
        # mission_instance_id가 제공된 경우
        if mission_instance_id:
            # 해당 mission_instance에 사용자가 posts를 작성했는지 확인
            posts_query = supabase.table("posts").select("id").eq("mission_instance_id", mission_instance_id).eq("user_id", user_id).limit(1)
            posts_result = posts_query.execute()
            return len(posts_result.data) > 0
        
        # journey_week_id가 제공된 경우
        elif journey_week_id:
            # journey_week_id로 mission_instances 조회
            mission_query = supabase.table("journey_mission_instances").select("id").eq("journey_week_id", journey_week_id)
            mission_result = mission_query.execute()
            
            if mission_result.data:
                mission_ids = [item["id"] for item in mission_result.data]
                
                # 해당 mission_instances에 사용자가 posts를 작성했는지 확인
                for mission_id in mission_ids:
                    posts_query = supabase.table("posts").select("id").eq("mission_instance_id", mission_id).eq("user_id", user_id).limit(1)
                    posts_result = posts_query.execute()
                    if posts_result.data:
                        return True
            return False
        
        # journey_id가 제공된 경우
        elif journey_id:
            # journey_id로 weeks 조회 후 mission_instances 조회
            week_query = supabase.table("journey_weeks").select("id").eq("journey_id", journey_id)
            week_result = week_query.execute()
            
            if week_result.data:
                for week_data in week_result.data:
                    week_id = week_data["id"]
                    mission_query = supabase.table("journey_mission_instances").select("id").eq("journey_week_id", week_id)
                    mission_result = mission_query.execute()
                    
                    if mission_result.data:
                        for mission_data in mission_result.data:
                            mission_id = mission_data["id"]
                            posts_query = supabase.table("posts").select("id").eq("mission_instance_id", mission_id).eq("user_id", user_id).limit(1)
                            posts_result = posts_query.execute()
                            if posts_result.data:
                                return True
            return False
        
        # 범위가 지정되지 않은 경우, 해당 사용자가 존재하는지만 확인
        else:
            # profiles 테이블에서 사용자 존재 여부 확인
            profile_query = supabase.table("profiles").select("id").eq("id", user_id).limit(1)
            profile_result = profile_query.execute()
            return len(profile_result.data) > 0
            
    except Exception as e:
        logger.error(f"Error validating user access: {e}")
        # 검증 오류 시 접근 허용 (관대한 정책)
        return True
