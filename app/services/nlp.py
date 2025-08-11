"""
한국어 NLP 서비스
Korean text processing using konlpy (Okt)
"""
from typing import List, Tuple, Dict
from collections import Counter
import re
from konlpy.tag import Okt
import structlog

logger = structlog.get_logger()

# Okt 인스턴스 (싱글톤)
_okt_instance = None

# 한국어 불용어 리스트
KOREAN_STOPWORDS = {
    # 조사
    "의",
    "가",
    "이",
    "은",
    "들",
    "는",
    "좀",
    "잘",
    "걍",
    "과",
    "도",
    "를",
    "으로",
    "자",
    "에",
    "와",
    "한",
    "하다",
    # 대명사
    "이",
    "그",
    "저",
    "것",
    "수",
    "등",
    "등등",
    # 일반적인 동사/형용사
    "있다",
    "있",
    "없다",
    "없",
    "되다",
    "되",
    "하다",
    "하",
    "같다",
    "같",
    # 부사
    "또",
    "그리고",
    "그러나",
    "하지만",
    "즉",
    "그래서",
    "그러므로",
    "따라서",
    # 기타
    "년",
    "월",
    "일",
    "시",
    "분",
    "초",
    "때",
    "곳",
    "개",
    "명",
    "번",
    "차",
    "가지",
    # 영어 불용어
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
}


def initialize_okt() -> Okt:
    """
    Okt 인스턴스를 초기화하고 반환합니다.
    싱글톤 패턴으로 구현되어 있어 한 번만 초기화됩니다.
    """
    global _okt_instance
    if _okt_instance is None:
        logger.info("Initializing Okt instance")
        _okt_instance = Okt()
    return _okt_instance


def normalize_text(text: str) -> str:
    """
    텍스트 정규화
    - 특수문자 제거
    - 공백 정리
    - 소문자 변환 (영어)
    """
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)

    # URL 제거
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )

    # 이메일 제거
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "", text)

    # 특수문자를 공백으로 변환 (한글, 영문, 숫자, 공백만 유지)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)

    # 연속된 공백을 하나로
    text = re.sub(r"\s+", " ", text)

    # 양쪽 공백 제거
    text = text.strip()

    return text


def extract_nouns(text: str, normalize: bool = True) -> List[str]:
    """
    텍스트에서 명사를 추출합니다.

    Args:
        text: 분석할 텍스트
        normalize: 텍스트 정규화 여부

    Returns:
        명사 리스트
    """
    okt = initialize_okt()

    if normalize:
        text = normalize_text(text)

    # 빈 텍스트 처리
    if not text:
        return []

    try:
        # 명사 추출
        nouns = okt.nouns(text)

        # 한 글자 명사 제거 (선택적)
        nouns = [noun for noun in nouns if len(noun) > 1]

        return nouns
    except Exception as e:
        logger.error(f"Error extracting nouns: {e}")
        return []


def remove_stopwords(words: List[str], custom_stopwords: List[str] = None) -> List[str]:
    """
    불용어를 제거합니다.

    Args:
        words: 단어 리스트
        custom_stopwords: 추가 불용어 리스트

    Returns:
        불용어가 제거된 단어 리스트
    """
    stopwords = KOREAN_STOPWORDS.copy()

    # 사용자 정의 불용어 추가
    if custom_stopwords:
        stopwords.update(custom_stopwords)

    # 불용어 제거
    filtered_words = [word for word in words if word.lower() not in stopwords]

    return filtered_words


def calculate_word_frequency(
    text: str, top_n: int = None, min_count: int = 1, custom_stopwords: List[str] = None
) -> List[Tuple[str, int]]:
    """
    텍스트의 단어 빈도를 계산합니다.

    Args:
        text: 분석할 텍스트
        top_n: 상위 N개 단어만 반환 (None이면 모두 반환)
        min_count: 최소 출현 횟수
        custom_stopwords: 추가 불용어 리스트

    Returns:
        [(단어, 빈도), ...] 형태의 리스트
    """
    # 1. 명사 추출
    nouns = extract_nouns(text)

    # 2. 불용어 제거
    filtered_words = remove_stopwords(nouns, custom_stopwords)

    # 3. 빈도 계산
    word_counter = Counter(filtered_words)

    # 4. 최소 빈도 필터링
    if min_count > 1:
        word_counter = Counter(
            {word: count for word, count in word_counter.items() if count >= min_count}
        )

    # 5. 상위 N개 추출
    if top_n:
        most_common = word_counter.most_common(top_n)
    else:
        most_common = word_counter.most_common()

    return most_common


def analyze_multiple_texts(
    texts: List[str],
    top_n: int = None,
    min_count: int = 1,
    custom_stopwords: List[str] = None,
) -> List[Tuple[str, int]]:
    """
    여러 텍스트의 단어 빈도를 통합하여 계산합니다.

    Args:
        texts: 텍스트 리스트
        top_n: 상위 N개 단어만 반환
        min_count: 최소 출현 횟수
        custom_stopwords: 추가 불용어 리스트

    Returns:
        [(단어, 빈도), ...] 형태의 리스트
    """
    all_words = []

    # 모든 텍스트에서 명사 추출
    for text in texts:
        nouns = extract_nouns(text)
        all_words.extend(nouns)

    # 불용어 제거
    filtered_words = remove_stopwords(all_words, custom_stopwords)

    # 빈도 계산
    word_counter = Counter(filtered_words)

    # 최소 빈도 필터링
    if min_count > 1:
        word_counter = Counter(
            {word: count for word, count in word_counter.items() if count >= min_count}
        )

    # 상위 N개 추출
    if top_n:
        most_common = word_counter.most_common(top_n)
    else:
        most_common = word_counter.most_common()

    return most_common


def get_text_stats(text: str) -> Dict[str, int]:
    """
    텍스트의 기본 통계를 계산합니다.

    Args:
        text: 분석할 텍스트

    Returns:
        총 단어 수, 고유 단어 수 등의 통계
    """
    nouns = extract_nouns(text)
    filtered_words = remove_stopwords(nouns)

    return {
        "total_words": len(filtered_words),
        "unique_words": len(set(filtered_words)),
        "total_nouns": len(nouns),
        "unique_nouns": len(set(nouns)),
    }
