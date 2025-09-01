# app.py (psycopg3 권장 버전)
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
import os, psycopg
from pgvector.psycopg import register_vector, Vector

DIM = 384
DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@localhost:5432/postgres")

Vector384 = conlist(float, min_length=DIM, max_length=DIM)

class VectorQuery(BaseModel):
    vector: Vector384
    limit: int = 10
    metric: Literal["cosine", "l2"] = "cosine"

app = FastAPI(title="similarity search")

@app.post("/similar_docs")
def find_similar_docs(q: VectorQuery):
    op = "<=>" if q.metric == "cosine" else "<->"
    sql = f"""
      SELECT id, title, (embedding_vector {op} %s) AS score
      FROM design_doc
      ORDER BY score
      LIMIT %s
    """
    try:
        with psycopg.connect(DSN) as conn:
            register_vector(conn)  # vector 어댑터 등록
            with conn.cursor() as cur:
                # (선택) 인덱스 사용 유도 & 탐색 폭
                cur.execute("""
                    SET enable_seqscan=off;
                    SET enable_bitmapscan=off;
                    SET enable_indexscan=on;
                    SET ivfflat.probes=10;
                    SET jit=off;
                """)
                cur.execute(sql, (Vector(q.vector), q.limit))
                rows = cur.fetchall()
        return {"results": [{"id": r[0], "title": r[1], "score": float(r[2])} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))