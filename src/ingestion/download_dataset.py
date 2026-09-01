# =============================================================================
# DOWNLOAD_DATASET.PY
# =============================================================================
# Purpose:
# Download the Olist dataset from Kaggle into data/raw, then list what
# was downloaded as a sanity check. Ported from notebook Steps 18-19.
# =============================================================================

import sys
from pathlib import Path

# Allow importing config.py and kaggle_auth.py from their actual locations
sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))

from config import RAW_DATA_DIR, KAGGLE_DATASET
from kaggle_auth import authenticate_kaggle


def download_olist_dataset():
    authenticate_kaggle()

    # Import kaggle AFTER setting credentials — the kaggle package reads
    # environment variables at import time, not on first use.
    import kaggle

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Downloading {KAGGLE_DATASET} to {RAW_DATA_DIR}")
    print("=" * 70)

    kaggle.api.dataset_download_files(
        KAGGLE_DATASET,
        path=str(RAW_DATA_DIR),
        unzip=True,
    )

    print("=" * 70)
    print("DOWNLOAD COMPLETE — files in data/raw:")
    print("=" * 70)
    for f in sorted(RAW_DATA_DIR.iterdir()):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:<40} {size_mb:>8.2f} MB")


if __name__ == "__main__":
    download_olist_dataset()