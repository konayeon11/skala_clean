# -*- coding: utf-8 -*-
# 임베딩을 2D(PCA)로 축소해 산점도로 시각화, 선택: KMeans로 클러스터 라벨링
import os, numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 1) 파일에서 읽기(빠름)
embs = np.load("embeddings.npy")  #  shape: (N, 384)
df   = pd.read_csv(os.getenv("ISSUES_CSV", "github_issues_large.csv")).fillna("")

# 2) PCA 2D
pca = PCA(n_components=2)
reduced = pca.fit_transform(embs)

# 3) (선택) KMeans로 5개 클러스터
n_clusters = int(os.getenv("N_CLUSTERS", "5"))
km = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
labels = km.fit_predict(reduced)

# 4) 산점도 (한 그래프, 색상 지정하지 않음)
plt.figure(figsize=(6,5))
plt.scatter(reduced[:,0], reduced[:,1], s=10)  # 색상 미지정(요구사항 준수)
plt.title("Issue Embeddings (PCA 2D)")
plt.xlabel("PC1"); plt.ylabel("PC2")
plt.tight_layout()
plt.savefig("issue_embeddings_pca.png", dpi=150)

# 5) 클러스터별 산점도 (레이블 텍스트만)
plt.figure(figsize=(6,5))
plt.scatter(reduced[:,0], reduced[:,1], s=10)
for i, (x, y) in enumerate(reduced[:200]):  # 너무 많으면 복잡하니 200개까지만 표시
    plt.text(x, y, str(labels[i]), fontsize=6)
plt.title(f"Issue Clusters (KMeans={n_clusters})")
plt.xlabel("PC1"); plt.ylabel("PC2")
plt.tight_layout()
plt.savefig("issue_clusters_kmeans.png", dpi=150)

print("Saved: issue_embeddings_pca.png, issue_clusters_kmeans.png")