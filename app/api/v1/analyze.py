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
        # 범위별 분석 서비스 호출
        result = await analyze_posts_range(
            journey_id=journey_id,
            journey_week_id=journey_week_id,
            mission_instance_id=mission_instance_id,
            user_id=user_id,
            top_n=top_n,
            min_count=min_count,
            force_refresh=force_refresh,
        )

        from datetime import datetime

        return RangeAnalysisResponse(
            scope=AnalysisScope(result["scope"]),
            range=result["range"],
            cache_hit=result["cache_hit"],
            word_frequency=result["word_frequency"],
            total_posts=result["total_posts"],
            analyzed_at=datetime.fromisoformat(
                result["analyzed_at"].replace("Z", "+00:00")
            ),
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
