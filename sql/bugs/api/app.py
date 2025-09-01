# -*- coding: utf-8 -*-
from fastapi import FastAPI, Query, Header
from pydantic import BaseModel
import os, psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# (RAG용) OpenAI 선택적 사용
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5433/issue_sim")
MODEL = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 있으면 RAG 사용

app = FastAPI(title="Issue Similarity + RAG API")
model = SentenceTransformer(MODEL)

def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"

class Item(BaseModel):
    id: int
    title: str
    score: float

@app.get("/ping")
def ping():
    return {"ok": True}

# ===== 검색(Search) =====
@app.get("/search", response_model=list[Item])
def search(
    q: str = Query(..., description="검색 문장"),
    k: int = 5,
    x_user_id: int | None = Header(default=None, alias="X-User-Id")
):
    user_id = x_user_id or 1  # 헤더 없으면 1번 사용자로
    qvec = model.encode([q], normalize_embeddings=True)[0]
    qlit = vec_literal(qvec)

    sql = """
    SELECT id, title, 1 - (embedding <=> %s::vector) AS score
    FROM issues
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """

    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        # RLS용 세션 변수 설정
        cur.execute("SET LOCAL app.user_id = %s;", (user_id,))
        cur.execute(sql, (qlit, qlit, k))
        rows = cur.fetchall()

    return [Item(id=r[0], title=r[1], score=float(r[2])) for r in rows]

# ===== RAG(검색+요약/답변) =====
class RagAnswer(BaseModel):
    answer: str
    items: list[Item]

@app.get("/rag", response_model=RagAnswer)
def rag(
    q: str = Query(..., description="사용자 질문/버그 설명"),
    k: int = 5,
    x_user_id: int | None = Header(default=None, alias="X-User-Id")
):
    user_id = x_user_id or 1
    qvec = model.encode([q], normalize_embeddings=True)[0]
    qlit = vec_literal(qvec)

    fetch_sql = """
    SELECT id, title, description, 1 - (embedding <=> %s::vector) AS score
    FROM issues
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SET LOCAL app.user_id = %s;", (user_id,))
        cur.execute(fetch_sql, (qlit, qlit, k))
        rows = cur.fetchall()

    items = [Item(id=r[0], title=r[1], score=float(r[3])) for r in rows]
    contexts = [
        {"id": r[0], "title": r[1], "description": r[2], "score": float(r[3])}
        for r in rows
    ]

    # LLM 호출(선택): OPENAI_API_KEY가 있을 때만
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""You are an issue triage assistant.
User query:
{q}

Top-{k} similar issues (id | title | score | description):
{os.linesep.join(f"{c['id']} | {c['title']} | {c['score']:.2f} | {c['description'][:500]}" for c in contexts)}

Write a concise Korean answer:
- 먼저 가장 유사한 이슈 번호와 이유를 한 줄 요약
- 다음에 잠재 원인과 재현 조건을 bullet로
- 마지막에 빠른 해결 체크리스트 3개
"""
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2,
        )
        answer = chat.choices[0].message.content.strip()
    else:
        answer = (
            "LLM 키가 없어서 RAG 요약은 생략합니다. "
            "아래 Top-K 유사 이슈 목록을 참고하세요."
        )

    return RagAnswer(answer=answer, items=items)
