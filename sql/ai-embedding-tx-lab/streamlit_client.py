import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Design 등록 (no title)", layout="centered")
st.title("🧩 Design 등록 ")

with st.form("reg_form"):
    description = st.text_area("Description (필수)", height=180, placeholder="설계안 내용을 입력하세요…")
    submitted = st.form_submit_button("등록")

if submitted:
    if not description.strip():
        st.error("Description은 필수입니다.")
    else:
        try:
            with st.spinner("임베딩 계산 및 등록 중…"):
                resp = requests.post(
                    f"{API_URL}/register_design",
                    json={"description": description},
                    timeout=120
                )
            if resp.ok:
                data = resp.json()
                st.success("등록 성공!")
                st.json(data)
                st.info("확인 쿼리:\nSELECT id, left(description,80), created_at FROM app.designs WHERE id = %s;" % data["id"])
            else:
                st.error(f"실패: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"요청 오류: {e}")

st.caption(f"API_URL = {API_URL} • FastAPI: uvicorn app:app --reload")