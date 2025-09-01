
# llm_recommender.py
# Utilities to fetch neighbors from Postgres, build a prompt, and call an LLM.

import os
from typing import List, Dict, Any
import psycopg2, psycopg2.extras

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # handled at runtime

from rag_prompt_builder_embeddings import build_prompt

def get_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST","localhost"),
        port=os.getenv("PGPORT","5432"),
        dbname=os.getenv("PGDATABASE","postgres"),
        user=os.getenv("PGUSER","postgres"),
        password=os.getenv("PGPASSWORD","postgres"),
    )

def fetch_neighbors(user_id: str, k: int = 5) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT embedding FROM user_embeddings WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise ValueError(f"user_id {user_id} not found")

    qvec = row["embedding"]
    sql = """
        SELECT user_id, embedding <=> %s::vector AS cosine_distance
        FROM user_embeddings
        WHERE user_id <> %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    cur.execute(sql, (qvec, user_id, qvec, k))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def call_llm(prompt: str, model: str = None, temperature: float = 0.5) -> str:
    """
    Returns generated text from OpenAI. Requires OPENAI_API_KEY env var.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        # Fallback mock (no external call)
        return "[MOCK OUTPUT]\\n- 첫 제안\\n- 둘째 제안\\n- 셋째 제안"

    client = OpenAI(api_key=api_key)
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

def recommend_for_user(user_id: str, k: int = 5, model: str = None, temperature: float = 0.5) -> Dict[str, Any]:
    neighbors = fetch_neighbors(user_id, k=k)
    prompt = build_prompt(user_id, neighbors)
    output = call_llm(prompt, model=model, temperature=temperature)
    return {"user_id": user_id, "k": k, "prompt": prompt, "llm_output": output, "neighbors": neighbors}
