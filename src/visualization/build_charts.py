# =============================================================================
# BUILD_CHARTS.PY
# =============================================================================
# Purpose:
# Generate BI visualizations from the customer segmentation results.
# Cluster labels are derived dynamically from each cluster's own stats
# (not hard-coded numbers) so the charts stay accurate even if a future
# re-run assigns different cluster IDs to the same underlying groups.
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend: we only save PNGs, never
                        # display a window, so this avoids the Tcl/Tk
                        # dependency entirely.
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import FEATURES_DATA_DIR, FIGURES_DIR

SEGMENTS_PATH = FEATURES_DATA_DIR / "customer_segments.parquet"

sns.set_theme(style="whitegrid")


def build_cluster_label(cluster_id: int, cluster_df: pd.DataFrame) -> str:
    """Build a human-readable label from the cluster's own characteristics
    rather than assuming a fixed cluster ID always means the same thing."""
    repeat_pct = (cluster_df["purchase_frequency"] > 1).mean() * 100
    avg_review = cluster_df["avg_review_score"].mean()

    if repeat_pct > 50:
        tag = "Repeat buyers"
    elif avg_review < 2.5:
        tag = "Dissatisfied one-timers"
    elif cluster_df["recency_days"].mean() < 180:
        tag = "Recent one-timers"
    else:
        tag = "Lapsed one-timers"

    return f"Cluster {cluster_id}: {tag}"


def build_charts():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(SEGMENTS_PATH)

    cluster_labels = {
        cid: build_cluster_label(cid, df[df["cluster"] == cid])
        for cid in sorted(df["cluster"].unique())
    }
    df["cluster_label"] = df["cluster"].map(cluster_labels)

    print("=" * 80)
    print("GENERATING BI VISUALIZATIONS")
    print("=" * 80)

    # --- Chart 1: Cluster sizes with repeat-buyer share annotated ---
    fig, ax = plt.subplots(figsize=(9, 5))
    sizes = df["cluster_label"].value_counts().sort_index()
    bars = ax.bar(sizes.index, sizes.values, color=sns.color_palette("viridis", len(sizes)))
    for bar, cid in zip(bars, sorted(df["cluster"].unique())):
        repeat_pct = (df[df["cluster"] == cid]["purchase_frequency"] > 1).mean() * 100
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{repeat_pct:.1f}% repeat", ha="center", fontsize=9)
    ax.set_ylabel("Number of customers")
    ax.set_title("Customer Segment Sizes and Repeat-Buyer Share")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    path1 = FIGURES_DIR / "cluster_sizes.png"
    plt.savefig(path1, dpi=150)
    plt.close()
    print(f"Saved: {path1}")

    # --- Chart 2: Recency vs Spend scatter, colored by cluster ---
    fig, ax = plt.subplots(figsize=(9, 6))
    sample = df.sample(n=min(10000, len(df)), random_state=42)  # subsample for a readable plot
    sns.scatterplot(
        data=sample, x="recency_days", y="total_spent",
        hue="cluster_label", alpha=0.5, s=20, ax=ax,
    )
    ax.set_xlabel("Recency (days since last purchase)")
    ax.set_ylabel("Total spent (R$)")
    ax.set_title("Customer Segments: Recency vs. Spend")
    ax.legend(title=None, fontsize=8, loc="upper right")
    plt.tight_layout()
    path2 = FIGURES_DIR / "recency_vs_spend_scatter.png"
    plt.savefig(path2, dpi=150)
    plt.close()
    print(f"Saved: {path2}")

    # --- Chart 3: Average review score per cluster ---
    fig, ax = plt.subplots(figsize=(9, 5))
    review_means = df.groupby("cluster_label")["avg_review_score"].mean().sort_index()
    bars = ax.bar(review_means.index, review_means.values,
                   color=sns.color_palette("rocket", len(review_means)))
    ax.axhline(3.0, color="gray", linestyle="--", linewidth=1, label="Neutral (3.0)")
    ax.set_ylabel("Average review score (1-5)")
    ax.set_title("Average Customer Satisfaction by Segment")
    ax.legend()
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    path3 = FIGURES_DIR / "avg_review_score_by_cluster.png"
    plt.savefig(path3, dpi=150)
    plt.close()
    print(f"Saved: {path3}")

    print("\n" + "=" * 80)
    print("ALL CHARTS GENERATED")
    print("=" * 80)


if __name__ == "__main__":
    build_charts()