"""
입력 검증 유틸리티
Input validation utilities
"""
import re
import uuid
from typing import Optional, List, Any
from app.core.exceptions import ValidationError


def validate_text_length(
    text: str, min_length: int = 1, max_length: int = 10000, field_name: str = "text"
) -> str:
    """
    텍스트 길이를 검증합니다.

    Args:
        text: 검증할 텍스트
        min_length: 최소 길이
        max_length: 최대 길이
        field_name: 필드 이름 (오류 메시지용)

    Returns:
        검증된 텍스트

    Raises:
        ValidationError: 검증 실패 시
    """
    if not isinstance(text, str):
        raise ValidationError(f"{field_name}는 문자열이어야 합니다")

    # 공백 제거 후 길이 확인
    stripped_text = text.strip()

    if len(stripped_text) < min_length:
        raise ValidationError(f"{field_name}는 최소 {min_length}자 이상이어야 합니다")

    if len(stripped_text) > max_length:
        raise ValidationError(f"{field_name}는 최대 {max_length}자 이하여야 합니다")

    return stripped_text


def validate_uuid(
    value: str, field_name: str = "ID", allow_none: bool = False
) -> Optional[str]:
    """
    UUID 형식을 검증합니다.

    Args:
        value: 검증할 값
        field_name: 필드 이름
        allow_none: None 허용 여부

    Returns:
        검증된 UUID 문자열

    Raises:
        ValidationError: 검증 실패 시
    """
    if value is None:
        if allow_none:
            return None
        else:
            raise ValidationError(f"{field_name}는 필수입니다")

    if not isinstance(value, str):
        raise ValidationError(f"{field_name}는 문자열이어야 합니다")

    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValidationError(f"{field_name}는 올바른 UUID 형식이어야 합니다")


def validate_positive_integer(
    value: int,
    field_name: str = "값",
    min_value: int = 1,
    max_value: Optional[int] = None,
) -> int:
    """
    양의 정수를 검증합니다.

    Args:
        value: 검증할 값
        field_name: 필드 이름
        min_value: 최솟값
        max_value: 최댓값

    Returns:
        검증된 정수

    Raises:
        ValidationError: 검증 실패 시
    """
    if not isinstance(value, int):
        raise ValidationError(f"{field_name}는 정수여야 합니다")

    if value < min_value:
        raise ValidationError(f"{field_name}는 {min_value} 이상이어야 합니다")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name}는 {max_value} 이하여야 합니다")

    return value


def validate_word_list(
    words: List[str],
    min_count: int = 1,
    max_count: int = 200,
    max_word_length: int = 50,
) -> List[str]:
    """
    단어 리스트를 검증합니다.

    Args:
        words: 단어 리스트
        min_count: 최소 단어 수
        max_count: 최대 단어 수
        max_word_length: 단어 최대 길이

    Returns:
        검증된 단어 리스트

    Raises:
        ValidationError: 검증 실패 시
    """
    if not isinstance(words, list):
        raise ValidationError("단어 목록은 리스트여야 합니다")

    if len(words) < min_count:
        raise ValidationError(f"최소 {min_count}개의 단어가 필요합니다")

    if len(words) > max_count:
        raise ValidationError(f"최대 {max_count}개의 단어까지 허용됩니다")

    validated_words = []
    for i, word in enumerate(words):
        if not isinstance(word, str):
            raise ValidationError(f"단어 {i+1}번째 항목은 문자열이어야 합니다")

        word = word.strip()

        if not word:
            raise ValidationError(f"단어 {i+1}번째 항목이 비어있습니다")

        if len(word) > max_word_length:
            raise ValidationError(f"단어 '{word}'가 너무 깁니다 (최대 {max_word_length}자)")

        validated_words.append(word)

    # 중복 제거
    unique_words = list(dict.fromkeys(validated_words))  # 순서 유지하면서 중복 제거

    if len(unique_words) < min_count:
        raise ValidationError(f"중복 제거 후 최소 {min_count}개의 단어가 필요합니다")

    return unique_words


def validate_email(email: str) -> str:
    """
    이메일 주소 형식을 검증합니다.

    Args:
        email: 이메일 주소

    Returns:
        검증된 이메일 주소

    Raises:
        ValidationError: 검증 실패 시
    """
    if not isinstance(email, str):
        raise ValidationError("이메일은 문자열이어야 합니다")

    email = email.strip().lower()

    if not email:
        raise ValidationError("이메일 주소는 필수입니다")

    # 간단한 이메일 정규식 검증
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError("올바른 이메일 주소 형식이 아닙니다")

    return email


def validate_role(role: str) -> str:
    """
    사용자 역할을 검증합니다.

    Args:
        role: 사용자 역할

    Returns:
        검증된 역할

    Raises:
        ValidationError: 검증 실패 시
    """
    valid_roles = ["student", "teacher", "admin"]

    if not isinstance(role, str):
        raise ValidationError("역할은 문자열이어야 합니다")

    role = role.strip().lower()

    if role not in valid_roles:
        raise ValidationError(f"역할은 다음 중 하나여야 합니다: {', '.join(valid_roles)}")

    return role


def validate_analysis_params(
    journey_id: Optional[str] = None,
    journey_week_id: Optional[str] = None,
    mission_instance_id: Optional[str] = None,
    user_id: Optional[str] = None,
    top_n: int = 50,
    min_count: int = 1,
) -> dict:
    """
    분석 파라미터를 검증합니다.

    Args:
        journey_id: Journey ID
        journey_week_id: Journey Week ID
        mission_instance_id: Mission Instance ID
        user_id: User ID
        top_n: 상위 N개
        min_count: 최소 카운트

    Returns:
        검증된 파라미터

    Raises:
        ValidationError: 검증 실패 시
    """
    # 최소 하나의 범위 파라미터 필요
    range_params = [journey_id, journey_week_id, mission_instance_id, user_id]
    if not any(range_params):
        raise ValidationError(
            "최소 하나의 범위 파라미터(journey_id, journey_week_id, mission_instance_id, user_id)가 필요합니다"
        )

    validated_params = {}

    # UUID 검증
    if journey_id:
        validated_params["journey_id"] = validate_uuid(
            journey_id, "Journey ID", allow_none=False
        )

    if journey_week_id:
        validated_params["journey_week_id"] = validate_uuid(
            journey_week_id, "Journey Week ID", allow_none=False
        )

    if mission_instance_id:
        validated_params["mission_instance_id"] = validate_uuid(
            mission_instance_id, "Mission Instance ID", allow_none=False
        )

    if user_id:
        validated_params["user_id"] = validate_uuid(
            user_id, "User ID", allow_none=False
        )

    # 수치 파라미터 검증
    validated_params["top_n"] = validate_positive_integer(
        top_n, "top_n", min_value=1, max_value=200
    )
    validated_params["min_count"] = validate_positive_integer(
        min_count, "min_count", min_value=1, max_value=100
    )

    return validated_params


def validate_text_contains_korean(text: str) -> bool:
    """
    텍스트에 한글이 포함되어 있는지 확인합니다.

    Args:
        text: 검사할 텍스트

    Returns:
        한글 포함 여부
    """
    return bool(re.search(r"[가-힣]", text))


def sanitize_input(value: Any) -> Any:
    """
    입력값을 안전하게 정리합니다.

    Args:
        value: 정리할 값

    Returns:
        정리된 값
    """
    if isinstance(value, str):
        # HTML 태그 제거
        value = re.sub(r"<[^>]*?>", "", value)

        # 스크립트 태그 제거
        value = re.sub(
            r"<script[^>]*?>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL
        )

        # 위험한 문자 제거/치환
        dangerous_chars = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }

        for char, replacement in dangerous_chars.items():
            value = value.replace(char, replacement)

    return value


def validate_cache_key(key: str) -> str:
    """
    캐시 키를 검증합니다.

    Args:
        key: 캐시 키

    Returns:
        검증된 캐시 키

    Raises:
        ValidationError: 검증 실패 시
    """
    if not isinstance(key, str):
        raise ValidationError("캐시 키는 문자열이어야 합니다")

    key = key.strip()

    if not key:
        raise ValidationError("캐시 키는 비어있을 수 없습니다")

    if len(key) > 250:
        raise ValidationError("캐시 키는 250자를 초과할 수 없습니다")

    # 허용되지 않는 문자 확인
    if re.search(r"[^\w\-_:.]", key):
        raise ValidationError("캐시 키에 허용되지 않는 문자가 포함되어 있습니다")

    return key
