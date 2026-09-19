import urllib.request
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# HUGGING FACE DATA FILES
# ============================================================

FILES = {

    "recipe_index.db": (
        "https://huggingface.co/datasets/"
        "maheeranusrath/recipesense-data/"
        "resolve/main/recipe_index.db?download=true"
    ),

    "recipes_cleaned.parquet": (
        "https://huggingface.co/datasets/"
        "maheeranusrath/recipesense-data/"
        "resolve/main/recipes_cleaned.parquet?download=true"
    )
}


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_file(filename, url):

    destination = DATA_DIR / filename

    # --------------------------------------------------------
    # Skip existing files
    # --------------------------------------------------------

    if destination.exists():

        print(
            f"{filename} already exists. "
            "Skipping download."
        )

        return

    print("=" * 60)

    print(
        f"Downloading: {filename}"
    )

    print("=" * 60)

    try:

        urllib.request.urlretrieve(
            url,
            destination
        )

        print(
            f"Downloaded successfully:"
        )

        print(destination)

        print()

    except Exception as error:

        print(
            f"\nFailed to download {filename}"
        )

        print(
            f"Error: {error}"
        )

        # Remove incomplete file
        if destination.exists():

            destination.unlink()

        raise


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "       RecipeSense Data Downloader"
    )

    print("=" * 60)

    print()

    for filename, url in FILES.items():

        download_file(
            filename,
            url
        )

    print("=" * 60)

    print(
        "All required data files are ready."
    )

    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()