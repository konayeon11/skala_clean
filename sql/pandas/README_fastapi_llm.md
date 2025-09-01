
# FastAPI + LLM(RAG) 연계 (user_embeddings, vector(2))

## 1) FastAPI 실행
```powershell
# 환경변수
$env:PGHOST="localhost"; $env:PGPORT="5432"; $env:PGDATABASE="postgres"; $env:PGUSER="postgres"; $env:PGPASSWORD="secret"

# API 서버 기동
uvicorn fastapi_app_embeddings:app --reload
```

### 엔드포인트
- `GET /health`
- `GET /neighbors?user_id=U0001&k=5`  # 특정 사용자 이웃
- `GET /neighbors?x=0.12&y=-1.03&k=5` # 임의의 2D 벡터와 가까운 사용자

## 2) LLM 프롬프트 생성 (예시)
```python
import requests
from rag_prompt_builder_embeddings import build_prompt

# 1) 이웃 질의
resp = requests.get("http://127.0.0.1:8000/neighbors", params={"user_id":"U0001","k":5})
data = resp.json()

# 2) LLM 프롬프트 생성
prompt = build_prompt("U0001", data["neighbors"])
print(prompt)

# (선택) OpenAI 등 LLM 호출 (예시)
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# completion = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role":"user","content":prompt}],
#     temperature=0.5,
# )
# print(completion.choices[0].message.content)
```
