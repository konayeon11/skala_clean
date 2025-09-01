# -*- coding: utf-8 -*-
"""
make_embeddings.py
- 입력 CSV에서 PCA(2D) 임베딩을 만들고 user_id, embedding 두 컬럼으로 저장
Usage:
  python make_embeddings.py --input "user_behavior.csv" --output user_embeddings.csv
"""
import argparse, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def to_vec_str(x, y, ndigits=6):
    return f"[{x:.{ndigits}f}, {y:.{ndigits}f}]"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="user_embeddings.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    cols = ["user_id","age","income","gender","spending_score","visit_count"]
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"누락된 컬럼: {c}")
    # numeric
    num_cols = ["age","income","spending_score","visit_count"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(df[c].median())

    # scale + pca(2)
    X = df[num_cols].astype(float).values
    X = (X - X.mean(axis=0)) / X.std(axis=0, ddof=0)
    pca = PCA(n_components=2, random_state=args.seed)
    X2 = pca.fit_transform(X)

    out = pd.DataFrame({
        "user_id": df["user_id"],
        "embedding": [to_vec_str(a, b) for a, b in X2]
    })
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print("Saved:", args.output, "rows:", len(out))

if __name__ == "__main__":
    main()
