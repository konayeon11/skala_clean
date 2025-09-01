
# fastapi_app_llm.py
# Run: python -m uvicorn fastapi_app_llm:app --reload --host 127.0.0.1 --port 8030

import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from llm_recommender import recommend_for_user

app = FastAPI(title="User Embeddings + LLM Recommender")

@app.get("/health")
def health():
    # Also surface whether OPENAI_API_KEY is set (for debugging)
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    return {"ok": True, "openai_key": "set" if has_key else "missing"}

@app.get("/recommend_llm")
def recommend_llm(
    user_id: str,
    k: int = Query(5, ge=1, le=20),
    model: str = Query(None, description="OpenAI model name, e.g., gpt-4o-mini"),
    temperature: float = Query(0.5, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    try:
        result = recommend_for_user(user_id=user_id, k=k, model=model, temperature=temperature)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
