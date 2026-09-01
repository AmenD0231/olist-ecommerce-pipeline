# =============================================================================
# KAGGLE_AUTH.PY
# =============================================================================
# Purpose:
# Authenticate with the Kaggle API using username + key, entered securely
# at runtime. This replaces the notebook's KAGGLE_API_TOKEN approach,
# which has a known bug in current kaggle package versions where the
# token gets silently consumed on import.
# =============================================================================

import os
from getpass import getpass


def authenticate_kaggle():
    """
    Prompt for Kaggle username and API key, then set them as environment
    variables. The kaggle package checks KAGGLE_USERNAME and KAGGLE_KEY
    automatically — no kaggle.json file needed.
    """
    username = input("Kaggle username: ").strip()
    key = getpass("Kaggle API key (input hidden): ").strip()

    if not username or not key:
        raise ValueError(
            "Both username and key are required. "
            "Get them from https://www.kaggle.com/settings under the API section."
        )

    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    print("Kaggle credentials set for this session.")


if __name__ == "__main__":
    authenticate_kaggle()