# =============================================================================
# BUILD_SEGMENTATION.PY
# =============================================================================
# Purpose:
# Cluster customers into segments using KMeans on RFM features, then
# profile each cluster honestly — including reporting if clusters end up
# dominated by one-time buyers, which is an expected consequence of
# Olist's ~3% repeat-purchase rate, not a modeling failure.
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from config import FEATURES_DATA_DIR, REPORTS_DIR

FEATURES_PATH = FEATURES_DATA_DIR / "customer_features.parquet"
N_CLUSTERS = 4  # Consistent with the original project's cluster count

CLUSTERING_FEATURES = [
    "recency_days",
    "purchase_frequency",
    "total_spent",
    "avg_review_score",
]


def build_segmentation():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("CUSTOMER SEGMENTATION (KMEANS)")
    print("=" * 80)

    df = pd.read_parquet(FEATURES_PATH)

    # avg_review_score can be null for customers whose order has no review
    # yet; drop rather than impute, since imputing a review score would
    # fabricate sentiment data that was never actually given.
    before = len(df)
    df = df.dropna(subset=CLUSTERING_FEATURES)
    print(f"Customers with complete features: {len(df):,} "
          f"(dropped {before - len(df):,} missing review scores)")

    X = df[CLUSTERING_FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    sil_score = silhouette_score(X_scaled, df["cluster"])
    print(f"\nSilhouette score: {sil_score:.3f}")
    print("(Scores near 0 are expected here — with ~97% one-time buyers, "
          "clusters will overlap heavily rather than separate cleanly. "
          "This reflects the real distribution, not a modeling error.)")

    print("\n" + "=" * 80)
    print("CLUSTER PROFILES (mean values per cluster)")
    print("=" * 80)
    profile = df.groupby("cluster")[CLUSTERING_FEATURES].mean().round(2)
    profile["customer_count"] = df.groupby("cluster").size()
    profile["pct_of_total"] = (profile["customer_count"] / len(df) * 100).round(2)
    print(profile.to_string())

    # Report repeat-buyer share per cluster explicitly — this is the
    # number that determines whether a cluster is meaningfully distinct
    # or just another one-time-buyer bucket.
    print("\nRepeat-buyer share per cluster:")
    for cluster_id in sorted(df["cluster"].unique()):
        cluster_df = df[df["cluster"] == cluster_id]
        repeat_pct = (cluster_df["purchase_frequency"] > 1).mean() * 100
        print(f"  Cluster {cluster_id}: {repeat_pct:.2f}% repeat buyers "
              f"(n={len(cluster_df):,})")

    output_path = FEATURES_DATA_DIR / "customer_segments.parquet"
    df.to_parquet(output_path, index=False)
    profile_path = REPORTS_DIR / "cluster_profiles.csv"
    profile.to_csv(profile_path)

    print(f"\nSegmented customers saved to: {output_path}")
    print(f"Cluster profiles saved to: {profile_path}")


if __name__ == "__main__":
    build_segmentation()