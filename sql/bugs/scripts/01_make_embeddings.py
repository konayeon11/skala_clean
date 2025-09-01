# -*- coding: utf-8 -*-
import os, pandas as pd, numpy as np
from sentence_transformers import SentenceTransformer

CSV_PATH = "github_issues_large.csv"   # 필요 시 sample로 변경
MODEL = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

def build_text(row):
    title = str(row.get("title", "")).strip()
    desc  = str(row.get("description", "")).strip()
    base  = f"{title}. {desc}".strip(". ")
    if "tags" in row and str(row["tags"]).strip():
        return f"{base} Tags: {row['tags']}"
    return base

def main():
    df = pd.read_csv(CSV_PATH).fillna("")
    texts = [build_text(r) for r in df.to_dict("records")]
    model = SentenceTransformer(MODEL)
    embs = model.encode(texts, batch_size=64, convert_to_numpy=True,
                        normalize_embeddings=True, show_progress_bar=True)
    np.save("embeddings.npy", embs)
    df.to_parquet("issues_payload.parquet", index=False)
    print("Saved: embeddings.npy, issues_payload.parquet")

if __name__ == "__main__":
    main()