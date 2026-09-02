import os
from getpass import getpass

def authenticate_kaggle():
    """
    Use KAGGLE_USERNAME/KAGGLE_KEY if already set in the environment
    (needed for unattended runs, e.g. via Airflow). Otherwise prompt
    interactively — this path is only hit during manual runs.
    """
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        print("Using existing Kaggle credentials from environment variables.")
        return

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