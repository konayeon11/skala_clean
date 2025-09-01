# -*- coding: utf-8 -*-
"""
load_embeddings_to_pg.py
- user_embeddings.csv (user_id, embedding) 을 PostgreSQL user_embeddings 테이블에 upsert
Usage:
  # 환경변수 설정 후:
  #   Windows PowerShell 예시:
  #   $env:PGHOST="localhost"; $env:PGPORT="5432"; $env:PGDATABASE="postgres"; $env:PGUSER="postgres"; $env:PGPASSWORD="secret"
  # 실행:
  #   python load_embeddings_to_pg.py --csv user_embeddings.csv
"""
import os, argparse, csv, psycopg2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--table", default="user_embeddings")
    ap.add_argument("--dim", type=int, default=2)
    args = ap.parse_args()

    dsn = "host=%s port=%s dbname=%s user=%s password=%s" % (
        os.getenv("PGHOST","localhost"),
        os.getenv("PGPORT","5432"),
        os.getenv("PGDATABASE","postgres"),
        os.getenv("PGUSER","postgres"),
        os.getenv("PGPASSWORD","postgres"),
    )
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # ensure extension & table
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {args.table} (
    user_id VARCHAR(10) PRIMARY KEY,
    embedding vector({args.dim})
);
""")
    conn.commit()

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    sql = f"""INSERT INTO {args.table} (user_id, embedding)
VALUES (%(user_id)s, %(embedding)s::vector)
ON CONFLICT (user_id) DO UPDATE SET embedding = EXCLUDED.embedding;
"""
    for r in rows:
        # r["embedding"] 는 "[x, y]" 문자열이어야 함
        cur.execute(sql, r)

    conn.commit()
    cur.close(); conn.close()
    print("Upserted rows:", len(rows))

if __name__ == "__main__":
    main()
