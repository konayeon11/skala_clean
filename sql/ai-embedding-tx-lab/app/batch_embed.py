# -*- coding: utf-8 -*-
import os, sys, csv, traceback, math
import psycopg2
from dotenv import load_dotenv, find_dotenv
from sentence_transformers import SentenceTransformer

def safe_load_dotenv():
    try:
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            for enc in ("utf-8", "utf8-sig", "cp949", "euc-kr"):
                try:
                    load_dotenv(dotenv_path=dotenv_path, encoding=enc, override=False); break
                except Exception: continue
    except Exception: pass
safe_load_dotenv()

DB = {
  "host": os.getenv("DB_HOST","127.0.0.1"),
  "dbname": os.getenv("DB_NAME","appdb"),
  "user": os.getenv("DB_USER","postgres"),
  "password": os.getenv("DB_PASSWORD",""),
  "port": int(os.getenv("DB_PORT") or 5432),
}

def to_pgvector_literal(vec): return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"
def valid(v): return len(v)==384 and all(not (math.isinf(float(x)) or math.isnan(float(x))) for x in v)

csv_path = os.path.join("data", "sample_designs_500.csv")  # description 컬럼 가정

model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")

conn = None
ok = fail = 0
try:
    conn = psycopg2.connect(options="-c client_encoding=UTF8 -c lc_messages=C", **DB)
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    cur.execute("BEGIN;")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            desc = (row.get("description") or "").strip()
            if not desc:
                print(f"[{i}] 빈 description → skip"); continue

            sp = f"sp_{i}"
            cur.execute(f"SAVEPOINT {sp};")
            try:
                emb = model.encode([desc])[0]
                if not valid(emb): raise ValueError("invalid embedding")
                cur.execute("""
                  INSERT INTO app.designs (description, embedding)
                  VALUES (%s, %s);
                """, (desc, to_pgvector_literal(emb)))
                ok += 1
            except Exception as e:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp};")
                fail += 1
                print(f"[{i}] 실패 → ROLLBACK TO {sp} | {e}")

    conn.commit()
    print(f"COMMIT ✅  ok={ok}, fail={fail}")

except Exception as e:
    if conn:
        conn.rollback(); print("ROLLBACK 🔁 (배치 전체 취소)")
    print("오류:", repr(e)); traceback.print_exc()
finally:
    if conn: conn.close()