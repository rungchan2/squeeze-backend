"""
한국어 처리 유틸리티
Korean NLP utilities and helper functions
"""
import re
from typing import List, Set

# 한국어 불용어 확장 리스트
EXTENDED_KOREAN_STOPWORDS: Set[str] = {
    # 조사 (Postpositions)
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
    "에서",
    "부터",
    "까지",
    "로",
    "으로서",
    "에게",
    "한테",
    "께",
    "로부터",
    "에게서",
    "한테서",
    "께서",
    # 대명사 (Pronouns)
    "이",
    "그",
    "저",
    "것",
    "수",
    "등",
    "등등",
    "이것",
    "그것",
    "저것",
    "여기",
    "거기",
    "저기",
    "나",
    "너",
    "우리",
    "당신",
    "그들",
    "자신",
    "본인",
    # 관형사 (Determiners)
    "모든",
    "각",
    "어떤",
    "이런",
    "그런",
    "저런",
    "다른",
    "같은",
    "새로운",
    "전체",
    # 부사 (Adverbs)
    "또",
    "그리고",
    "그러나",
    "하지만",
    "즉",
    "그래서",
    "그러므로",
    "따라서",
    "그런데",
    "그러면",
    "아직",
    "이미",
    "벌써",
    "아직도",
    "여전히",
    "계속",
    "항상",
    "가끔",
    "때때로",
    "자주",
    "매우",
    "정말",
    "진짜",
    "너무",
    "아주",
    "상당히",
    "꽤",
    "조금",
    "약간",
    "좀",
    # 동사 활용 (Verb forms)
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
    "아니다",
    "않다",
    "이다",
    "거다",
    "것이다",
    "나다",
    "오다",
    "가다",
    "보다",
    "주다",
    "받다",
    "주어지다",
    # 형용사 활용 (Adjective forms)
    "좋다",
    "좋",
    "나쁘다",
    "나쁜",
    "크다",
    "큰",
    "작다",
    "작은",
    "높다",
    "낮다",
    "많다",
    "적다",
    # 접속사 (Conjunctions)
    "그리고",
    "하지만",
    "그러나",
    "또는",
    "혹은",
    "이나",
    "아니면",
    "만약",
    "만일",
    # 감탄사 (Interjections)
    "아",
    "어",
    "오",
    "우",
    "으",
    "흠",
    "음",
    "네",
    "예",
    "아니",
    "맞다",
    # 시간 관련 (Time)
    "년",
    "월",
    "일",
    "시",
    "분",
    "초",
    "때",
    "동안",
    "시간",
    "날",
    "오늘",
    "어제",
    "내일",
    "이번",
    "다음",
    "지난",
    "앞으로",
    "나중에",
    # 장소 관련 (Place)
    "곳",
    "데",
    "곳곳",
    "여기저기",
    "이곳",
    "그곳",
    "저곳",
    "어디",
    "어디든지",
    # 단위 (Units)
    "개",
    "명",
    "번",
    "차",
    "가지",
    "종류",
    "타입",
    "방법",
    "방식",
    # 기타 (Others)
    "뭐",
    "무엇",
    "누구",
    "언제",
    "어디",
    "왜",
    "어떻게",
    "얼마",
    "얼마나",
    "이런",
    "그런",
    "저런",
    "어떤",
    "무슨",
    "어느",
    "정도",
    "만큼",
    "처럼",
    "같이",
    "위해",
    "위한",
    "대해",
    "대한",
    "관해",
    "관한",
    "통해",
    "통한",
    "의해",
    "의한",
    "따라",
    "따른",
    "대로",
    "만큼",
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
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "can",
    "shall",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    # 자주 나타나는 의미없는 단어들
    "것",
    "거",
    "분",
    "점",
    "면",
    "때문",
    "경우",
    "상황",
    "문제",
    "결과",
    "이유",
    "목적",
    "방향",
    "상태",
    "형태",
    "모습",
    "모양",
    "느낌",
    "생각",
    "의견",
    "견해",
    # 웹/채팅 관련
    "ㅋ",
    "ㅋㅋ",
    "ㅋㅋㅋ",
    "ㅎ",
    "ㅎㅎ",
    "ㅎㅎㅎ",
    "ㅠ",
    "ㅠㅠ",
    "ㅜ",
    "ㅜㅜ",
    "ㅡ",
    "ㅡㅡ",
    ";;",
    "...",
    "!!",
    "??",
    "~~",
    # 단일 문자 (일반적으로 의미없는 경우가 많음)
    "ㄱ",
    "ㄴ",
    "ㄷ",
    "ㄹ",
    "ㅁ",
    "ㅂ",
    "ㅅ",
    "ㅇ",
    "ㅈ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
}


def normalize_korean_text(text: str) -> str:
    """
    한국어 텍스트를 정규화합니다.

    Args:
        text: 정규화할 텍스트

    Returns:
        정규화된 텍스트
    """
    if not text:
        return ""

    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)

    # URL 제거
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )

    # 이메일 주소 제거
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "", text)

    # 전화번호 제거 (한국 형식)
    text = re.sub(r"\d{2,3}-\d{3,4}-\d{4}", "", text)

    # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)

    # 반복되는 문자 정리 (ㅋㅋㅋㅋ -> ㅋㅋ)
    text = re.sub(r"([ㅋㅎㅠㅜ])\1{2,}", r"\1\1", text)

    # 연속된 공백을 하나로
    text = re.sub(r"\s+", " ", text)

    # 양쪽 공백 제거
    text = text.strip()

    return text


def is_meaningful_word(word: str, min_length: int = 2) -> bool:
    """
    의미있는 단어인지 판단합니다.

    Args:
        word: 검사할 단어
        min_length: 최소 길이

    Returns:
        의미있는 단어 여부
    """
    if not word or len(word) < min_length:
        return False

    # 불용어 체크
    if word.lower() in EXTENDED_KOREAN_STOPWORDS:
        return False

    # 숫자만 있는 경우
    if word.isdigit():
        return False

    # 특정 패턴 제외
    # 반복 문자 (aaaa, 1111)
    if len(set(word)) == 1 and len(word) > 2:
        return False

    # 영문자만 있고 길이가 1인 경우
    if word.isalpha() and len(word) == 1:
        return False

    return True


def extract_korean_nouns_simple(text: str) -> List[str]:
    """
    간단한 한국어 명사 추출 (konlpy 없이)
    정확도는 떨어지지만 빠른 처리를 위한 방법
    """
    if not text:
        return []

    # 텍스트 정규화
    normalized = normalize_korean_text(text)

    # 공백으로 분리
    words = normalized.split()

    # 필터링
    filtered_words = []
    for word in words:
        if is_meaningful_word(word):
            # 한글이 포함된 단어만 추출
            if re.search(r"[가-힣]", word):
                filtered_words.append(word)

    return filtered_words


def clean_word_list(words: List[str]) -> List[str]:
    """
    단어 리스트를 정리합니다.

    Args:
        words: 단어 리스트

    Returns:
        정리된 단어 리스트
    """
    cleaned_words = []

    for word in words:
        # 공백 제거 및 소문자 변환
        cleaned_word = word.strip().lower()

        # 유효한 단어만 추가
        if is_meaningful_word(cleaned_word):
            cleaned_words.append(cleaned_word)

    # 중복 제거하면서 순서 유지
    seen = set()
    result = []
    for word in cleaned_words:
        if word not in seen:
            seen.add(word)
            result.append(word)

    return result


def get_word_variations(word: str) -> List[str]:
    """
    단어의 변형을 생성합니다.
    (예: 활용형, 높임말 등)

    Args:
        word: 기본 단어

    Returns:
        변형 단어들
    """
    variations = [word]

    # 기본적인 한국어 어미 변형
    if len(word) >= 2:
        # 하다 동사의 경우
        if word.endswith("하다"):
            base = word[:-2]
            variations.extend(
                [
                    base + "하기",
                    base + "하는",
                    base + "했다",
                    base + "하여",
                    base + "해서",
                    base + "하면",
                ]
            )

        # ㄴ/은 과거형
        if word.endswith(("다", "었다", "았다")):
            # 기본형만 추가
            if word.endswith("었다"):
                variations.append(word[:-2] + "다")
            elif word.endswith("았다"):
                variations.append(word[:-2] + "다")

    return list(set(variations))


def calculate_text_readability(text: str) -> dict:
    """
    텍스트의 가독성을 계산합니다.

    Args:
        text: 분석할 텍스트

    Returns:
        가독성 지표
    """
    if not text:
        return {"readability_score": 0, "difficulty": "unknown"}

    # 문장 수 계산
    sentences = re.split(r"[.!?]+", text)
    sentence_count = len([s for s in sentences if s.strip()])

    # 단어 수 계산
    words = text.split()
    word_count = len(words)

    # 평균 문장 길이
    avg_sentence_length = word_count / max(sentence_count, 1)

    # 한글 비율
    korean_chars = len(re.findall(r"[가-힣]", text))
    total_chars = len(re.sub(r"\s", "", text))
    korean_ratio = korean_chars / max(total_chars, 1)

    # 간단한 가독성 점수 계산 (0-100)
    readability_score = max(0, min(100, 100 - (avg_sentence_length * 2)))

    # 난이도 분류
    if readability_score >= 80:
        difficulty = "easy"
    elif readability_score >= 60:
        difficulty = "medium"
    else:
        difficulty = "hard"

    return {
        "readability_score": round(readability_score, 2),
        "difficulty": difficulty,
        "sentence_count": sentence_count,
        "word_count": word_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "korean_ratio": round(korean_ratio, 2),
    }
