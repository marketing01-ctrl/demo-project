"""AI 없이 키워드/통계 규칙으로 채팅 메시지를 분석한다."""
import re
from collections import Counter

import pandas as pd

# 카테고리별 키워드. 채팅방 성격에 맞게 자유롭게 추가/수정하면 된다.
SPAM = ["[광고]", "부업", "리딩방", "코인", "수익 보장"]
COMPLAINT = ["신고", "강퇴", "불만", "불편", "산만", "짜증"]
BROKEN_LINK = ["만료", "안 열", "안열", "깨졌", "404", "접속이 안"]
REQUEST = ["공지", "규칙", "해주세요", "해주시면", "좋겠", "부탁"]
QUESTION_END = re.compile(r"(나요|까요|가요|죠|는지|습니까|어디)\s*[?？~ㅠㅜ.!]*$")

STOPWORDS = {
    "저도", "제가", "진짜", "그리고", "혹시", "근데", "너무", "아직", "정말", "그냥", "이번",
    "같아요", "좋아요", "감사합니다", "있나요", "없네요", "하나요", "되나요", "합니다",
    "안녕하세요", "안녕하세", "반갑습니다", "ㅎㅎ", "ㅠㅠ", "ㅋㅋ",
    "같아", "돼요", "어제", "오늘", "언제", "있으면", "좋겠",
}
PARTICLES = ("에서", "으로", "이에요", "예요", "입니다", "해요", "은", "는", "이", "가", "을", "를", "에", "도", "로", "요")

COLUMN_HINTS = {
    "author": ["author", "name", "user", "sender", "작성자", "이름", "보낸", "닉네임"],
    "message": ["message", "content", "text", "body", "메시지", "내용", "대화"],
    "time": ["time", "date", "시간", "날짜", "일시"],
}


def guess_column(columns, kind):
    """컬럼 이름으로 작성자/메시지/시간 컬럼을 추측한다. 못 찾으면 None."""
    for col in columns:
        if any(h in str(col).lower() for h in COLUMN_HINTS[kind]):
            return col
    return None


def has_any(text, keywords):
    return any(k in text for k in keywords)


def is_question(text):
    return "?" in text or "？" in text or bool(QUESTION_END.search(text))


def top_keywords(messages, n=10):
    counts = Counter()
    for text in messages:
        for word in re.findall(r"[가-힣A-Za-z]{2,}", text):
            for p in PARTICLES:
                if word.endswith(p) and len(word) > len(p) + 1:
                    word = word[: -len(p)]
                    break
            if word not in STOPWORDS and len(word) >= 2:
                counts[word] += 1
    return counts.most_common(n)


def analyze(df, author_col, message_col, time_col=None):
    df = df.dropna(subset=[message_col]).copy()
    df[message_col] = df[message_col].astype(str)
    rows = list(zip(df[author_col].astype(str), df[message_col]))

    def pick(keywords):
        return [(a, m) for a, m in rows if has_any(m, keywords)]

    spam = pick(SPAM)
    spam_set = set(spam)
    complaints = [r for r in pick(COMPLAINT) if r not in spam_set]
    broken = pick(BROKEN_LINK)
    requests = [r for r in pick(REQUEST) if r not in spam_set]
    questions = [(a, m) for a, m in rows if is_question(m) and (a, m) not in spam_set]

    period = None
    if time_col:
        times = pd.to_datetime(df[time_col], errors="coerce").dropna()
        if len(times):
            period = (times.min(), times.max())

    actions = []
    if spam:
        spammers = Counter(a for a, _ in spam)
        names = ", ".join(f"{a}({c}건)" for a, c in spammers.most_common())
        actions.append((f"광고/스팸 계정 조치 (경고 또는 강퇴): {names}", spam))
    if complaints:
        actions.append((f"신고·불만 {len(complaints)}건 확인하고 답변하기", complaints))
    if questions:
        actions.append((f"멤버 질문 {len(questions)}개 확인하고 답변·공지하기", questions))
    if broken:
        actions.append((f"만료되거나 안 열리는 링크 {len(broken)}건 교체하기", broken))
    if requests:
        actions.append((f"건의사항 {len(requests)}건 검토하기 (공지, 규칙 등)", requests))

    return {
        "total": len(rows),
        "members": df[author_col].nunique(),
        "period": period,
        "active": Counter(a for a, _ in rows).most_common(5),
        "keywords": top_keywords(m for a, m in rows if (a, m) not in spam_set),
        "actions": actions,
    }
