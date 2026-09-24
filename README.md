# 채팅방 분석기 (MVP)

채팅 메시지 CSV를 올리면 요약, 주요 키워드, 방장 액션 아이템을 만들어 줍니다.
AI API 없이 키워드·통계 규칙으로 분석하므로 **무료**이고 API 키가 필요 없습니다.

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

브라우저가 열리면 `sample_chat.csv`를 올리고 "분석하기"를 누르세요.

- `app.py`: 화면
- `analyzer.py`: 분석 규칙. 맨 위의 키워드 목록(`SPAM`, `COMPLAINT` 등)을 고치면 잡아내는 기준이 바뀝니다.
