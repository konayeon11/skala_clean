# -*- coding: utf-8 -*-
import os, psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5433/issue_sim")
MODEL = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"

def search(query, k=5):
    model = SentenceTransformer(MODEL)
    q = model.encode([query], normalize_embeddings=True)[0]
    qlit = vec_literal(q)
    sql = """
    SELECT id, title,
           1 - (embedding <=> %s::vector) AS score
    FROM issues
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(sql, (qlit, qlit, k))
        return cur.fetchall()

if __name__ == "__main__":
    for row in search("memory leak after upgrade", 5):
        print(row)