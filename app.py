import io

import pandas as pd
import streamlit as st

from analyzer import analyze, guess_column


def decode_csv(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp949")  # 한국어 Windows 엑셀에서 저장한 CSV


st.set_page_config(page_title="채팅방 분석기")
st.title("채팅방 분석기")
st.caption("채팅 메시지 CSV를 올리면 요약과 방장 액션 아이템을 만들어 드립니다. (무료, AI 없이 규칙 기반)")

uploaded = st.file_uploader("채팅 CSV 파일", type="csv")
if uploaded is None:
    st.stop()

try:
    df = pd.read_csv(io.StringIO(decode_csv(uploaded.getvalue())))
except Exception as e:
    st.error(f"CSV를 읽지 못했습니다: {e}")
    st.stop()

st.write(f"메시지 {len(df)}개")
st.dataframe(df.head(20))

# 컬럼 이름으로 자동 추측하고, 틀리면 직접 고를 수 있게 한다.
cols = list(df.columns)
NONE = "(없음)"
c1, c2, c3 = st.columns(3)
author_col = c1.selectbox("작성자 컬럼", cols, index=cols.index(guess_column(cols, "author") or cols[0]))
message_col = c2.selectbox("메시지 컬럼", cols, index=cols.index(guess_column(cols, "message") or cols[-1]))
time_guess = guess_column(cols, "time")
time_col = c3.selectbox("시간 컬럼", [NONE] + cols, index=cols.index(time_guess) + 1 if time_guess else 0)

if not st.button("분석하기", type="primary"):
    st.stop()

r = analyze(df, author_col, message_col, None if time_col == NONE else time_col)

st.header("요약")
period = f"{r['period'][0]:%Y-%m-%d} ~ {r['period'][1]:%Y-%m-%d} 동안 " if r["period"] else ""
st.write(f"{period}멤버 {r['members']}명이 메시지 {r['total']}개를 보냈습니다.")
st.subheader("가장 활발한 멤버")
st.bar_chart(pd.DataFrame(r["active"], columns=["멤버", "메시지 수"]).set_index("멤버"))

st.header("주요 키워드")
st.write(", ".join(f"**{w}** ({c})" for w, c in r["keywords"]) or "키워드가 없습니다.")

st.header("방장 액션 아이템")
if not r["actions"]:
    st.success("특별히 조치할 일이 없어 보여요.")
for title, evidence in r["actions"]:
    st.checkbox(title, key=title)
    with st.expander(f"근거 메시지 {len(evidence)}개"):
        for author, msg in evidence:
            st.markdown(f"- **{author}**: {msg}")
