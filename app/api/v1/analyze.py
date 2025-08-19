"""
텍스트 분석 관련 엔드포인트
단어 빈도 분석, 단어 그룹핑 등의 API를 제공합니다.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    RangeAnalysisResponse,
    WordGroupingRequest,
    WordGroupingResponse,
    AnalysisScope,
    WordGroup,
)
from app.core.dependencies import require_teacher_role
from app.core.exceptions import TextAnalysisError, ValidationError
from app.services.analysis import analyze_text, analyze_posts_range, group_words
from app.services.cache import invalidate_journey_week_cache
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/word-frequency",
    response_model=TextAnalysisResponse,
    summary="텍스트 단어 빈도 분석",
    description="입력된 텍스트의 형태소를 분석하고 단어 빈도를 계산합니다.",
)
async def analyze_word_frequency(
    request: TextAnalysisRequest,
    current_user: dict = Depends(require_teacher_role),  # Teacher 이상 권한 필요
) -> TextAnalysisResponse:
    """
    텍스트의 단어 빈도를 분석합니다.

    - 한국어 형태소 분석을 통해 명사 추출
    - 불용어 제거
    - 단어별 출현 빈도 계산

    Args:
        request: 분석할 텍스트

    Returns:
        단어 빈도 분석 결과
    """
    try:
        # 텍스트 분석 서비스 호출
        result = await analyze_text(
            text=request.text,
            top_n=getattr(request, "top_n", None),
            min_count=getattr(request, "min_count", 1),
            custom_stopwords=getattr(request, "custom_stopwords", None),
            use_cache=True,
        )

        return TextAnalysisResponse(
            word_frequency=result["word_frequency"],
            total_words=result["total_words"],
            unique_words=result["unique_words"],
        )

    except (TextAnalysisError, ValidationError) as e:
        logger.error(f"Text analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in word frequency analysis: {e}")
        raise HTTPException(status_code=500, detail="분석 중 오류가 발생했습니다")


@router.get(
    "/range-word-frequency",
    response_model=RangeAnalysisResponse,
    summary="범위별 단어 빈도 분석",
    description="지정된 범위의 posts 데이터에서 단어 빈도를 분석합니다.",
)
async def analyze_range_word_frequency(
    journey_id: Optional[str] = Query(None, description="Journey ID"),
    journey_week_id: Optional[str] = Query(None, description="Journey Week ID"),
    mission_instance_id: Optional[str] = Query(None, description="Mission Instance ID"),
    user_id: Optional[str] = Query(None, description="User ID"),
    top_n: int = Query(50, ge=1, le=200, description="상위 N개 단어"),
    min_count: int = Query(1, ge=1, description="최소 출현 횟수"),
    force_refresh: bool = Query(False, description="캐시 무시 여부"),
    current_user: dict = Depends(require_teacher_role),  # Teacher 이상 권한 필요
) -> RangeAnalysisResponse:
    """
    지정된 범위의 posts 데이터에서 단어 빈도를 분석합니다.

    - 캐시 우선 조회
    - 범위: journey, week, mission, user 단위
    - 상위 N개 단어만 반환

    Args:
        Various query parameters for filtering

    Returns:
        범위별 단어 빈도 분석 결과
    """
    try:
        # 범위별 분석 서비스 호출 - 현재 사용자의 role 전달
        result = await analyze_posts_range(
            journey_id=journey_id,
            journey_week_id=journey_week_id,
            mission_instance_id=mission_instance_id,
            user_id=user_id,
            top_n=top_n,
            min_count=min_count,
            force_refresh=force_refresh,
            current_user_role=current_user.get("role", "user"),
        )

        from datetime import datetime

        # scope 값을 소문자로 변환하여 enum과 매칭
        scope_value = result["scope"].lower() if isinstance(result["scope"], str) else result["scope"]
        
        return RangeAnalysisResponse(
            scope=AnalysisScope(scope_value),
            range=result["range"],
            cache_hit=result["cache_hit"],
            word_frequency=result["word_frequency"],
            total_posts=result["total_posts"],
            analyzed_at=datetime.fromisoformat(
                result["analyzed_at"].replace("Z", "+00:00")
            ),
            source_texts=result.get("source_texts", []),
        )

    except (TextAnalysisError, ValidationError) as e:
        logger.error(f"Range analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in range analysis: {e}")
        raise HTTPException(status_code=500, detail="범위별 분석 중 오류가 발생했습니다")


@router.post(
    "/group-words",
    response_model=WordGroupingResponse,
    summary="단어 그룹핑",
    description="단어 리스트를 유사도 기반으로 그룹화합니다.",
)
async def group_words_endpoint(
    request: WordGroupingRequest,
    current_user: dict = Depends(require_teacher_role),  # Teacher 이상 권한 필요
) -> WordGroupingResponse:
    """
    단어 리스트를 유사도 기반으로 그룹화합니다.

    - TF-IDF 기반 유사도 계산
    - K-means 클러스터링

    Args:
        request: 그룹화할 단어 리스트와 그룹 수

    Returns:
        단어 그룹핑 결과
    """
    try:
        # 단어 그룹핑 서비스 호출
        result = await group_words(
            words=request.words,
            num_groups=request.n_clusters,
            method=getattr(request, "method", "semantic"),
        )

        # WordGroup 객체로 변환
        groups = [
            WordGroup(label=group["label"], words=group["words"])
            for group in result["groups"]
        ]

        return WordGroupingResponse(groups=groups, total_groups=result["total_groups"])

    except (TextAnalysisError, ValidationError) as e:
        logger.error(f"Word grouping error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in word grouping: {e}")
        raise HTTPException(status_code=500, detail="단어 그룹핑 중 오류가 발생했습니다")


@router.delete(
    "/cache/journey-week/{journey_week_id}",
    summary="Journey Week 캐시 무효화",
    description="특정 journey week의 분석 캐시를 무효화합니다.",
)
async def invalidate_journey_week_cache_endpoint(
    journey_week_id: str,
    current_user: dict = Depends(require_teacher_role),  # Teacher 이상 권한 필요
):
    """
    특정 journey week의 분석 캐시를 무효화합니다.
    
    새로운 필드가 추가되거나 분석 로직이 변경된 경우 사용합니다.
    """
    try:
        deleted_count = await invalidate_journey_week_cache(journey_week_id)
        
        return {
            "message": f"Journey week {journey_week_id}의 캐시 무효화 완료",
            "deleted_keys": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error invalidating journey week cache: {e}")
        raise HTTPException(status_code=500, detail="캐시 무효화 중 오류가 발생했습니다")


@router.get(
    "/debug/journey-week/{journey_week_id}",
    summary="Journey Week 데이터베이스 쿼리 디버깅",
    description="각 단계별 쿼리 결과를 확인합니다.",
)
async def debug_journey_week_query(
    journey_week_id: str,
    current_user: dict = Depends(require_teacher_role),
):
    """
    Journey Week 데이터 조회 디버깅 엔드포인트
    """
    from app.db.supabase import get_supabase_client, get_supabase_admin_client
    
    try:
        supabase = get_supabase_client()
        debug_info = {}
        
        # 현재 사용자 정보 확인
        debug_info["current_user"] = {
            "user_id": current_user.get("sub"),
            "role": current_user.get("role"), 
            "email": current_user.get("email")
        }
        
        # Supabase client에 현재 사용자의 JWT 토큰 설정
        # 이렇게 해야 RLS 정책이 올바르게 적용됩니다
        from fastapi import Request
        request = current_user.get("_request")  # 임시 방법
        
        # 1단계: journey_week_id로 mission_instance_ids 조회
        logger.info(f"[DEBUG] Step 1: Querying mission instances for journey_week_id: {journey_week_id}")
        
        # Admin client로 테스트 (RLS 우회)
        admin_supabase = get_supabase_admin_client()
        try:
            admin_mission_query = admin_supabase.table("journey_mission_instances").select("id, journey_week_id").eq("journey_week_id", journey_week_id)
            admin_mission_result = admin_mission_query.execute()
            debug_info["admin_client_test"] = {
                "success": True,
                "count": len(admin_mission_result.data) if admin_mission_result.data else 0,
                "data": admin_mission_result.data
            }
        except Exception as admin_error:
            debug_info["admin_client_test"] = {
                "success": False,
                "error": str(admin_error)
            }
        
        # 일반 테이블 쿼리 (RLS 적용)
        mission_query = supabase.table("journey_mission_instances").select("id, journey_week_id").eq("journey_week_id", journey_week_id)
        mission_result = mission_query.execute()
        
        debug_info["step1_mission_instances"] = {
            "query": f"SELECT id, journey_week_id FROM journey_mission_instances WHERE journey_week_id = '{journey_week_id}'",
            "count": len(mission_result.data) if mission_result.data else 0,
            "data": mission_result.data[:3] if mission_result.data else []  # 처음 3개만
        }
        
        if not mission_result.data:
            debug_info["error"] = "No mission instances found"
            return debug_info
            
        # 2단계: 각 mission_instance_id로 posts 조회
        mission_ids = [item["id"] for item in mission_result.data]
        debug_info["mission_ids"] = mission_ids
        
        all_posts = []
        posts_by_mission = {}
        
        for mission_id in mission_ids:
            logger.info(f"[DEBUG] Step 2: Querying posts for mission_id: {mission_id}")
            posts_query = supabase.table("posts").select("id, content, answers_data, created_at, user_id").eq("mission_instance_id", mission_id)
            posts_result = posts_query.execute()
            
            posts_count = len(posts_result.data) if posts_result.data else 0
            posts_by_mission[mission_id] = {
                "count": posts_count,
                "posts": posts_result.data[:2] if posts_result.data else []  # 처음 2개만
            }
            
            if posts_result.data:
                all_posts.extend(posts_result.data)
                
        debug_info["step2_posts_by_mission"] = posts_by_mission
        debug_info["total_posts_found"] = len(all_posts)
        
        # 3단계: 텍스트 추출 테스트
        texts = []
        text_sources = []
        
        for i, post in enumerate(all_posts[:3]):  # 처음 3개 posts만 분석
            post_texts = []
            
            # content 필드에서 텍스트 추출
            if post.get("content"):
                post_texts.append({
                    "source": "content",
                    "length": len(post["content"]),
                    "preview": post["content"][:100] + "..." if len(post["content"]) > 100 else post["content"]
                })
                texts.append(post["content"])
            
            # answers_data에서 텍스트 추출
            answers_data = post.get("answers_data")
            if answers_data and isinstance(answers_data, dict):
                answers = answers_data.get("answers", [])
                for j, answer in enumerate(answers):
                    answer_text = answer.get("answer_text", "")
                    if answer_text and answer_text.strip():
                        post_texts.append({
                            "source": f"answers_data.answers[{j}].answer_text",
                            "length": len(answer_text),
                            "preview": answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                        })
                        texts.append(answer_text)
            
            text_sources.append({
                "post_id": post["id"],
                "extracted_texts": post_texts
            })
            
        debug_info["step3_text_extraction"] = {
            "total_texts_extracted": len(texts),
            "text_sources": text_sources
        }
        
        # 4단계: NLP 분석 테스트 (간단한 단어 개수만)
        if texts:
            from app.services.nlp import analyze_multiple_texts
            try:
                word_frequency = analyze_multiple_texts(texts=texts, top_n=10, min_count=1)
                debug_info["step4_nlp_analysis"] = {
                    "success": True,
                    "word_count": len(word_frequency),
                    "top_words": word_frequency[:5]
                }
            except Exception as nlp_error:
                debug_info["step4_nlp_analysis"] = {
                    "success": False,
                    "error": str(nlp_error)
                }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }
