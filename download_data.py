import urllib.request
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

DATA_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# HUGGING FACE DATA
# ============================================================

SQLITE_URL = (
    "https://huggingface.co/datasets/"
    "maheeranusrath/recipesense-data/"
    "resolve/main/recipe_index.db?download=true"
)

SQLITE_FILE = DATA_DIR / "recipe_index.db"


# ============================================================
# DOWNLOAD DATABASE
# ============================================================

def download_database():

    if SQLITE_FILE.exists():

        print("=" * 60)
        print("Recipe database already exists.")
        print(SQLITE_FILE)
        print("=" * 60)

        return


    print("=" * 60)
    print("       RecipeSense Database Downloader")
    print("=" * 60)

    print()
    print("Downloading SQLite recipe database...")
    print()
    print("Source:")
    print(SQLITE_URL)
    print()

    try:

        urllib.request.urlretrieve(
            SQLITE_URL,
            SQLITE_FILE
        )

        print()
        print("Database downloaded successfully.")
        print()
        print("Location:")
        print(SQLITE_FILE)

        size_mb = (
            SQLITE_FILE.stat().st_size
            / (1024 * 1024)
        )

        print()
        print(
            f"Database size: {size_mb:.2f} MB"
        )

        print()
        print("=" * 60)
        print("       Download Complete")
        print("=" * 60)


    except Exception as error:

        print()
        print("=" * 60)
        print("DATABASE DOWNLOAD FAILED")
        print("=" * 60)

        print()
        print("Error:")
        print(error)

        print()

        if SQLITE_FILE.exists():

            SQLITE_FILE.unlink()

        raise


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    download_database()