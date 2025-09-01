"""
==========================================
파일명   : app.py
목적     : FastAPI 기반 /register_design API로 설계안(description)을 임베딩하여
          PostgreSQL(pgvector)에 트랜잭션으로 안전 저장하고 메타정보(id, created_at)를 반환
작성자   : 고나연
작성일   : 2025-08-27
버전     : Python 3.11+ / FastAPI / Uvicorn / PostgreSQL 16 + pgvector / Docker Desktop(Linux)
설명     :
    - .env에서 DB 접속정보와 모델명을 읽어 SimpleConnectionPool로 연결 관리
    - 서버 시작 시 스키마 보장:
        * CREATE SCHEMA app / TABLE app.designs(VECTOR(384))
        * 누락 컬럼(title, created_at) 자동 보강(ALTER TABLE ... IF NOT EXISTS)
        * ivfflat(vector_cosine_ops) 인덱스 및 ANALYZE
    - SentenceTransformer(paraphrase-MiniLM-L6-v2, 384d)로 임베딩 생성
    - 트랜잭션(with conn:)으로 INSERT, 예외 시 자동 ROLLBACK

주요 기능:
    1) GET  /health
       - 서버/DB/모델 상태 확인
    2) POST /register_design
       - Request(JSON): { "title": Optional[str], "description": str }
       - Process      : 임베딩 계산(384d) → VECTOR 리터럴로 INSERT
       - Response(JSON): { "id": int, "created_at": ISO8601, "dim": 384, "message": "ok" }

실행 순서:
    1) (사전) Docker로 Postgres(pgvector) 기동, .env(DB_PORT 등) 확인
    2) uvicorn app:app --reload
    3) 브라우저에서 http://127.0.0.1:8000/docs 로 스펙 확인/테스트

결과 확인(원라이너 예시):
    docker exec -it pgvector16 psql -U postgres -d appdb -c 
    "SELECT id, title, left(description,80) AS desc_80, created_at
       FROM app.designs
      WHERE id = <응답 id>;"

참고     :
    - pgvector: https://github.com/pgvector/pgvector
    - Sentence-Transformers: paraphrase-MiniLM-L6-v2
    - 트랜잭션 제어: with conn: (자동 COMMIT/ROLLBACK)
==========================================
"""

import os
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from sentence_transformers import SentenceTransformer

# ---------- env ----------
_ = load_dotenv(find_dotenv(), override=False)
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/paraphrase-MiniLM-L6-v2")
EMB_DIM = 384  # paraphrase-MiniLM-L6-v2 = 384

def to_pgvector_literal(vec):
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

# ---------- app ----------
app = FastAPI(title="Design Register API (no title)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

POOL: Optional[SimpleConnectionPool] = None
MODEL: Optional[SentenceTransformer] = None

# DDL: title 컬럼 없이 스키마 보장
DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.designs (
  id           BIGSERIAL PRIMARY KEY,
  description  TEXT NOT NULL,
  embedding    VECTOR({EMB_DIM}) NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS designs_embedding_ivfflat
  ON app.designs USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

ANALYZE app.designs;
"""

# (선택) 과거에 title을 만들었다면 지우고 싶을 때만 주석 해제
# DDL += "ALTER TABLE app.designs DROP COLUMN IF EXISTS title;"

@app.on_event("startup")
def on_startup():
    global POOL, MODEL
    POOL = SimpleConnectionPool(
        minconn=1, maxconn=5,
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        options="-c client_encoding=UTF8 -c lc_messages=C"
    )
    MODEL = SentenceTransformer(MODEL_NAME)

    conn = POOL.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(DDL)
    finally:
        POOL.putconn(conn)

@app.on_event("shutdown")
def on_shutdown():
    if POOL:
        POOL.closeall()

class DesignIn(BaseModel):
    description: str = Field(min_length=1)

class DesignOut(BaseModel):
    id: int
    created_at: datetime
    dim: int = EMB_DIM
    message: str = "ok"

@app.get("/health")
def health():
    return {"status": "ok", "db": DB_NAME, "model": MODEL_NAME}

@app.post("/register_design", response_model=DesignOut)
def register_design(payload: DesignIn):
    desc = payload.description.strip()
    if not desc:
        raise HTTPException(status_code=400, detail="description is empty")

    vec = MODEL.encode([desc])[0]
    if len(vec) != EMB_DIM:
        raise HTTPException(status_code=500, detail=f"embedding dim mismatch: {len(vec)} != {EMB_DIM}")
    vec_lit = to_pgvector_literal(vec)

    conn = POOL.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app.designs (description, embedding)
                    VALUES (%s, %s::vector)
                    RETURNING id, created_at;
                    """,
                    (desc, vec_lit)
                )
                new_id, created_at = cur.fetchone()
        return DesignOut(id=new_id, created_at=created_at)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    finally:
        POOL.putconn(conn)
