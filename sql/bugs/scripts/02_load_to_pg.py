# -*- coding: utf-8 -*-
import os, numpy as np, pandas as pd, psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5433/issue_sim")

def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v.tolist()) + "]"

def main():
    df   = pd.read_parquet("issues_payload.parquet")
    embs = np.load("embeddings.npy")
    assert len(df) == len(embs), "rows != embeddings"

    rows = []
    for r, e in zip(df.to_dict("records"), embs):
        rows.append((
            r.get("title",""),
            r.get("description",""),
            vec_literal(e)
        ))

    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO issues (title, description, embedding)
            VALUES %s
        """, rows, template="(%s,%s,%s::vector)")
        conn.commit()
    print("Loaded rows:", len(rows))

if __name__ == "__main__":
    main()