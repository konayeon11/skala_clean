"""
==========================================
파일명   : [skala]AI_임베딩_트랜잭션_실습.py
목적     : Docker+PostgreSQL(pgvector)과 Python(psycopg2)을 이용해
          설계안 텍스트 임베딩 → 트랜잭션(BEGIN/COMMIT/ROLLBACK)으로 안전 적재 →
          코사인 거리 기반 Top-K 검색까지 재현/검증
작성자   : 고나연
작성일   : 2025-08-27
버전     : Python 3.11+ / PostgreSQL 16 + pgvector / Docker Desktop (Linux containers)
설명     :
    본 프로그램은 사용자가 입력하거나 CSV에서 읽은 설계안(description)을
    SentenceTransformer(paraphrase-MiniLM-L6-v2, 384d)로 임베딩하여
    PostgreSQL(pgvector 확장)의 VECTOR(384) 컬럼에 저장하고,
    트랜잭션 제어(BEGIN/COMMIT/ROLLBACK, SAVEPOINT)를 통해
    장애/오류 상황에서도 데이터 정합성을 보장하는 파이프라인을 구현한다.
    또한 pgvector의 코사인 거리 연산자(<=>)와 ivfflat 인덱스를 이용해
    유사도 Top-K 검색을 수행한다.

주요 기능:
    1) 환경 기동: docker compose로 Postgres+pgvector 컨테이너 기동 (호스트포트 5433→컨테이너 5432)
    2) 스키마 준비: app.designs(id, description, embedding VECTOR(384), created_at)
       + ivfflat (vector_cosine_ops) 인덱스 생성 및 ANALYZE
    3) 임베딩 계산: SentenceTransformer로 384차원 임베딩 생성 및 유효성 검사(NaN/Inf/차원)
    4) 트랜잭션 입력:
       - 단건: BEGIN → INSERT → COMMIT, 실패 시 ROLLBACK
       - 배치: BEGIN → SAVEPOINT per row → 실패 행만 ROLLBACK TO SAVEPOINT → 최종 COMMIT
    5) 검증/검색: psql에서 총건수 확인, 코사인 거리 기반 Top-K 유사도 검색

실습 환경/사전 요구:
    - Docker Desktop (Linux containers 모드, OSType: linux)
    - 포트: 호스트 5433 사용 시 .env의 DB_PORT=5433
    - Python 패키지: psycopg2-binary, python-dotenv, sentence-transformers
    - 데이터: data/sample_designs_500.csv (description 컬럼)

핵심 SQL(참고):
    -- 트랜잭션 예시
    BEGIN;
      INSERT INTO app.designs(description, embedding)
      VALUES ('정상 트랜잭션 예시',
              '[' || array_to_string(ARRAY(SELECT 0.0 FROM generate_series(1,384)), ',') || ']');
    COMMIT;

    BEGIN;
      INSERT INTO app.designs(description, embedding) VALUES ('차원 오류 예시','[0.1,0.2]');
    ROLLBACK;

    -- Top-K 유사도 (코사인 거리: 작을수록 유사)
    WITH base AS (SELECT embedding FROM app.designs ORDER BY id LIMIT 1)
    SELECT d.id, left(d.description,80) AS desc_80,
           (d.embedding <=> (SELECT embedding FROM base)) AS cosine_distance
    FROM app.designs d
    ORDER BY d.embedding <=> (SELECT embedding FROM base)
    LIMIT 5;

실행 순서(요약):
    1) docker compose up -d            # Postgres(pgvector) 기동
    2) psql 접속 후 \dx / \dn / \d 확인
    3) python app/batch_embed.py       # CSV → 임베딩 → 트랜잭션 적재(COMMIT/SAVEPOINT)
    4) SELECT count(*) FROM app.designs;
    5) 위 Top-K 쿼리로 유사도 검색

참고     :
    - pgvector: https://github.com/pgvector/pgvector
    - Sentence-Transformers: paraphrase-MiniLM-L6-v2
    - 트랜잭션 제어: BEGIN/COMMIT/ROLLBACK, SAVEPOINT
    - 코사인 거리 연산자: <=> (vector_cosine_ops)
==========================================
"""

# -*- coding: utf-8 -*-
import os, sys, traceback
import psycopg2
from dotenv import load_dotenv, find_dotenv
from sentence_transformers import SentenceTransformer

def safe_load_dotenv():
    try:
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            for enc in ("utf-8", "utf8-sig", "cp949", "euc-kr"):
                try:
                    load_dotenv(dotenv_path=dotenv_path, encoding=enc, override=False)
                    break
                except Exception:
                    continue
    except Exception:
        pass
safe_load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT") or 5432)

for k,v in {"DB_HOST":DB_HOST,"DB_NAME":DB_NAME,"DB_USER":DB_USER,"DB_PASSWORD":DB_PASSWORD}.items():
    if not v:
        print(f"[오류] 환경변수 {k}가 비어있습니다."); sys.exit(1)

def to_pgvector_literal(vec):
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

def is_valid(vec):
    import math
    return (len(vec) == 384) and all((not (math.isinf(float(x)) or math.isnan(float(x)))) for x in vec)

print("모델 로드: sentence-transformers/paraphrase-MiniLM-L6-v2 (384d)")
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")

if len(sys.argv) >= 2:
    description = " ".join(sys.argv[1:])
else:
    description = input("설계안 텍스트(description)를 입력하세요: ").strip()

if not description:
    print("[중단] description이 비었습니다."); sys.exit(1)

emb = model.encode([description])[0]
if not is_valid(emb):
    print("[중단] 임베딩 값이 유효하지 않습니다."); sys.exit(1)
emb_str = to_pgvector_literal(emb)

conn = None
try:
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT,
        options="-c client_encoding=UTF8 -c lc_messages=C"
    )
    conn.set_client_encoding("UTF8")
    cur = conn.cursor()

    print("BEGIN")
    cur.execute("BEGIN;")

    cur.execute("""
        INSERT INTO app.designs (description, embedding)
        VALUES (%s, %s)
        RETURNING id, created_at;
    """, (description, emb_str))

    new_id, created_at = cur.fetchone()
    conn.commit()
    print(f"COMMIT ✅  (id={new_id}, created_at={created_at})")

except Exception as e:
    if conn:
        conn.rollback()
        print("ROLLBACK 🔁 (오류로 인해 취소)")
    print("오류:", repr(e)); traceback.print_exc()
finally:
    if conn:
        conn.close()