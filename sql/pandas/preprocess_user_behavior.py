# -*- coding: utf-8 -*-
"""
CLI 전처리 스크립트 (VS Code 실행용)
Usage:
  python preprocess_user_behavior.py --input "17. CSV → Pandas → PostgreSQL 적재 실습_user_behavior.csv" --output user_behavior_enriched.csv --k 5
Options:
  --input      입력 CSV 경로
  --output     저장할 CSV 경로
  --k          KMeans k (기본 5)
  --qmin       클리핑 하한 분위수(기본 0.01)
  --qmax       클리핑 상한 분위수(기본 0.99)
  --seed       랜덤시드(기본 42)
  --no-plot    PCA/클러스터 플롯 생략
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

def to_vec_str(arr, ndigits=6):
    return "[" + ", ".join(f"{float(x):.{ndigits}f}" for x in arr) + "]"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="user_behavior_enriched.csv")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--qmin", type=float, default=0.01)
    ap.add_argument("--qmax", type=float, default=0.99)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    print("[1/7] Load CSV:", args.input)
    df = pd.read_csv(args.input, encoding="utf-8-sig")

    expected_cols = ["user_id","age","income","gender","spending_score","visit_count"]
    for c in expected_cols:
        if c not in df.columns:
            raise ValueError(f"누락된 컬럼: {c}")
    df = df[expected_cols]

    print("[2/7] DType 정리 및 결측 처리")
    num_cols = ["age","income","spending_score","visit_count"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(df[c].median())
    df["gender"] = df["gender"].astype(str).str.upper().str[0]
    df.loc[~df["gender"].isin(["M","F"]), "gender"] = "U"

    print("[3/7] 이상치 클리핑:", args.qmin, args.qmax)
    Qlo = df[num_cols].quantile(args.qmin)
    Qhi = df[num_cols].quantile(args.qmax)
    df[num_cols] = df[num_cols].clip(lower=Qlo, upper=Qhi, axis=1)

    print("[4/7] 표준화(Scaling)")
    scaler = StandardScaler()
    X = df[num_cols].astype(float).values
    X_scaled = scaler.fit_transform(X)
    for i, c in enumerate(num_cols):
        df[c + "_s"] = X_scaled[:, i]

    print("[5/7] PCA (2D)")
    pca = PCA(n_components=2, random_state=args.seed)
    X_pca = pca.fit_transform(X_scaled)
    df["pca1"] = X_pca[:,0]
    df["pca2"] = X_pca[:,1]
    explained = pca.explained_variance_ratio_.sum()
    print(f"  - 누적 설명분산비: {explained:.2%}")

    if not args.no_plot:
        plt.figure()
        plt.scatter(df["pca1"], df["pca2"])
        plt.xlabel("PCA1"); plt.ylabel("PCA2"); plt.title("PCA Scatter")
        plt.show()

    print(f"[6/7] KMeans (k={args.k})")
    kmeans = KMeans(n_clusters=args.k, n_init=10, random_state=args.seed)
    df["cluster"] = kmeans.fit_predict(X_scaled).astype(int)

    if not args.no_plot:
        plt.figure()
        for cl in sorted(df["cluster"].unique()):
            part = df[df["cluster"] == cl]
            plt.scatter(part["pca1"], part["pca2"], label=f"cluster {cl}")
        plt.xlabel("PCA1"); plt.ylabel("PCA2"); plt.title("Clusters on PCA plane")
        plt.legend()
        plt.show()

    print("[7/7] 벡터 문자열(user_vec/pca_vec) 생성 & 저장")
    df["user_vec"] = [to_vec_str(row) for row in X_scaled]
    df["pca_vec"]  = [to_vec_str(row) for row in X_pca]

    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print("저장 완료:", args.output, "행:", len(df))

if __name__ == "__main__":
    main()
