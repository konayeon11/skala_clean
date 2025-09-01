
# fastapi_app_embeddings.py
# Run: uvicorn fastapi_app_embeddings:app --reload
import os
from typing import Any, Dict, List, Optional
import psycopg2, psycopg2.extras
from fastapi import FastAPI, HTTPException, Query

def get_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST","localhost"),
        port=os.getenv("PGPORT","5432"),
        dbname=os.getenv("PGDATABASE","postgres"),
        user=os.getenv("PGUSER","postgres"),
        password=os.getenv("PGPASSWORD","postgres"),
    )

app = FastAPI(title="User Embeddings API (pgvector)")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/neighbors")
def neighbors(
    user_id: Optional[str] = None,
    x: Optional[float] = Query(None, description="query vector x (if user_id not provided)"),
    y: Optional[float] = Query(None, description="query vector y (if user_id not provided)"),
    k: int = 5,
) -> Dict[str, Any]:
    """
    Two modes:
      1) user_id provided -> find neighbors of that user's embedding
      2) x,y provided -> find neighbors of the ad-hoc query vector [x, y]
    """
    if not user_id and (x is None or y is None):
        raise HTTPException(status_code=400, detail="Provide user_id OR both x and y")

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if user_id:
        cur.execute("SELECT embedding FROM user_embeddings WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail=f"user_id {user_id} not found")
        qvec = row["embedding"]
        vec_literal = "%s::vector"
        params = (qvec, user_id, qvec, k)
        sql = """
            SELECT user_id, embedding <=> {q} AS cosine_distance
            FROM user_embeddings
            WHERE user_id <> %s
            ORDER BY embedding <=> {q}
            LIMIT %s
        """.format(q=vec_literal)
    else:
        # ad-hoc vector literal like '[x, y]'::vector
        vec_literal = f"'[{x}, {y}]'::vector"
        params = (k,)
        sql = f"""
            SELECT user_id, embedding <=> {vec_literal} AS cosine_distance
            FROM user_embeddings
            ORDER BY embedding <=> {vec_literal}
            LIMIT %s
        """

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {
        "mode": "user_id" if user_id else "ad_hoc",
        "query": user_id if user_id else [x, y],
        "k": k,
        "neighbors": rows
    }
