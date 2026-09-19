import urllib.request
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)


FILES = {
    "recipe_index.pkl": (
        "https://huggingface.co/datasets/maheeranusrath/recipesense-data/"
        "resolve/main/recipe_index.pkl?download=true"
    ),
    "recipes_cleaned.parquet": (
        "https://huggingface.co/datasets/maheeranusrath/recipesense-data/"
        "resolve/main/recipes_cleaned.parquet?download=true"
    ),
}


def download_file(filename, url):
    destination = DATA_DIR / filename

    if destination.exists():
        print(f"{filename} already exists. Skipping download.")
        return

    print("=" * 60)
    print(f"Downloading: {filename}")
    print("=" * 60)

    urllib.request.urlretrieve(url, destination)

    print(f"Downloaded successfully: {destination}")
    print()


def main():
    print("=" * 60)
    print("       RecipeSense Data Downloader")
    print("=" * 60)

    for filename, url in FILES.items():
        download_file(filename, url)

    print("=" * 60)
    print("All required data files are ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()