"""
Pydantic 스키마 정의
API 요청/응답에 사용되는 모든 데이터 모델을 정의합니다.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class UserRole(str, Enum):
    """사용자 역할"""

    USER = "user"
    TEACHER = "teacher"
    ADMIN = "admin"


class AnalysisScope(str, Enum):
    """분석 범위"""

    JOURNEY = "journey"
    JOURNEY_WEEK = "journey_week"
    MISSION_INSTANCE = "mission_instance"
    USER = "user"
    UNKNOWN = "unknown"


# Base Models
class BaseResponse(BaseModel):
    """기본 응답 모델"""

    processed_at: datetime = Field(default_factory=datetime.utcnow)


# Text Analysis Models
class TextAnalysisRequest(BaseModel):
    """텍스트 분석 요청 모델"""

    text: str = Field(..., min_length=1, max_length=10000, description="분석할 텍스트")

    class Config:
        json_schema_extra = {
            "example": {"text": "팀워크는 소통과 협업을 통해 달성된다. 좋은 협업이 프로젝트 성공의 열쇠다."}
        }

    @validator("text")
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("텍스트는 비어있을 수 없습니다")
        return v.strip()


class TextAnalysisResponse(BaseResponse):
    """텍스트 분석 응답 모델"""

    word_frequency: List[Tuple[str, int]] = Field(..., description="단어와 빈도수 배열")
    total_words: int = Field(..., ge=0, description="전체 단어 수")
    unique_words: int = Field(..., ge=0, description="고유 단어 수")

    class Config:
        json_schema_extra = {
            "example": {
                "word_frequency": [
                    ["팀워크", 1],
                    ["소통", 1],
                    ["협업", 2],
                    ["프로젝트", 1],
                    ["성공", 1],
                ],
                "total_words": 6,
                "unique_words": 5,
                "processed_at": "2025-01-26T10:00:00Z",
            }
        }


# Range Analysis Models
class RangeAnalysisRequest(BaseModel):
    """범위별 분석 요청 모델 (Query Parameters)"""

    journey_id: Optional[str] = Field(None, description="Journey ID")
    journey_week_id: Optional[str] = Field(None, description="Journey Week ID")
    mission_instance_id: Optional[str] = Field(None, description="Mission Instance ID")
    user_id: Optional[str] = Field(None, description="User ID")
    top_n: Optional[int] = Field(50, ge=1, le=200, description="상위 N개 단어")
    min_count: Optional[int] = Field(1, ge=1, description="최소 출현 횟수")
    force_refresh: Optional[bool] = Field(False, description="캐시 무시 여부")

    @validator("journey_id", "journey_week_id", "mission_instance_id", "user_id")
    def validate_uuid(cls, v):
        if v and len(v) != 36:  # Simple UUID length check
            raise ValueError("Invalid UUID format")
        return v


class RangeAnalysisResponse(BaseResponse):
    """범위별 분석 응답 모델"""

    scope: AnalysisScope = Field(..., description="분석 범위")
    range: Dict[str, str] = Field(..., description="분석 범위 상세")
    cache_hit: bool = Field(..., description="캐시 적중 여부")
    word_frequency: List[Tuple[str, int]] = Field(..., description="단어와 빈도수 배열")
    total_posts: int = Field(..., ge=0, description="분석된 게시물 수")
    analyzed_at: datetime = Field(..., description="분석 시점")
    source_texts: Optional[List[str]] = Field(None, description="분석에 사용된 원본 텍스트 배열")

    class Config:
        json_schema_extra = {
            "example": {
                "scope": "journey_week",
                "range": {"journey_id": "uuid", "journey_week_id": "uuid"},
                "cache_hit": True,
                "word_frequency": [["협업", 123], ["소통", 89], ["팀워크", 67], ["프로젝트", 45]],
                "total_posts": 45,
                "analyzed_at": "2025-01-26T10:00:00Z",
                "processed_at": "2025-01-26T10:00:00Z",
            }
        }


# Word Grouping Models
class WordGroupingRequest(BaseModel):
    """단어 그룹핑 요청 모델"""

    words: List[str] = Field(
        ..., min_length=2, max_length=1000, description="그룹화할 단어 리스트"
    )
    n_clusters: int = Field(3, ge=2, le=20, description="생성할 그룹 수")

    class Config:
        json_schema_extra = {
            "example": {"words": ["소통", "협업", "대화", "책임", "신뢰", "팀워크"], "n_clusters": 3}
        }

    @validator("words")
    def validate_words(cls, v):
        # 중복 제거 및 빈 문자열 필터링
        unique_words = list(set(word.strip() for word in v if word.strip()))
        if len(unique_words) < 2:
            raise ValueError("최소 2개 이상의 고유한 단어가 필요합니다")
        return unique_words


class WordGroup(BaseModel):
    """단어 그룹 모델"""

    label: str = Field(..., description="그룹 레이블")
    words: List[str] = Field(..., description="그룹에 속한 단어들")


class WordGroupingResponse(BaseResponse):
    """단어 그룹핑 응답 모델"""

    groups: List[WordGroup] = Field(..., description="단어 그룹 리스트")
    total_groups: int = Field(..., ge=0, description="전체 그룹 수")

    class Config:
        json_schema_extra = {
            "example": {
                "groups": [
                    {"label": "소통 관련", "words": ["소통", "대화"]},
                    {"label": "협업 관련", "words": ["협업", "팀워크"]},
                    {"label": "신뢰 관련", "words": ["책임", "신뢰"]},
                ],
                "total_groups": 3,
                "processed_at": "2025-01-26T10:00:00Z",
            }
        }


# Health Check Models
class ServiceStatus(BaseModel):
    """서비스 상태 모델"""

    redis: str = Field(..., description="Redis 상태")
    supabase: str = Field(..., description="Supabase 상태")


class HealthCheckResponse(BaseModel):
    """헬스체크 응답 모델"""

    status: str = Field(..., description="전체 서비스 상태")
    version: str = Field(..., description="API 버전")
    services: ServiceStatus = Field(..., description="개별 서비스 상태")
    uptime_seconds: int = Field(..., ge=0, description="서비스 가동 시간(초)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "services": {"redis": "healthy", "supabase": "healthy"},
                "uptime_seconds": 3600,
            }
        }


# User Models (for authentication)
class UserBase(BaseModel):
    """사용자 기본 모델"""

    email: str = Field(..., description="이메일 주소")
    role: UserRole = Field(UserRole.USER, description="사용자 역할")
    organization_id: Optional[str] = Field(None, description="조직 ID")


class UserInDB(UserBase):
    """DB에 저장된 사용자 모델"""

    id: str = Field(..., description="사용자 ID")
    first_name: Optional[str] = Field(None, description="이름")
    last_name: Optional[str] = Field(None, description="성")
    hashed_password: str = Field(..., description="해시된 비밀번호")
    is_active: bool = Field(True, description="활성화 상태")
    created_at: datetime = Field(..., description="생성 시간")


class TokenData(BaseModel):
    """JWT 토큰 데이터"""

    sub: str = Field(..., description="Subject (user_id)")
    role: UserRole = Field(..., description="사용자 역할")
    organization_id: Optional[str] = Field(None, description="조직 ID")
    exp: Optional[datetime] = Field(None, description="만료 시간")


# Error Response Models
class ErrorResponse(BaseModel):
    """에러 응답 모델"""

    detail: str = Field(..., description="에러 상세 메시지")

    class Config:
        json_schema_extra = {"example": {"detail": "텍스트는 비어있을 수 없습니다"}}
