import pandas as pd
from pathlib import Path

from nlp.recipe_parser import normalize_ingredient_name


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"
SUBSTITUTION_FILE = PROJECT_DIR / "data" / "substitutions.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("        RecipeSense - Ingredient Matching Diagnostic")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_parquet(DATA_FILE)

print("Recipes loaded:", len(df))


# ============================================================
# LOAD SUBSTITUTION INGREDIENTS
# ============================================================

sub_df = pd.read_csv(SUBSTITUTION_FILE)

substitution_ingredients = (
    sub_df["ingredient"]
    .astype(str)
    .str.lower()
    .str.strip()
    .unique()
    .tolist()
)

print("\nSubstitution ingredients:")
print("-" * 70)

for ingredient in substitution_ingredients:
    print("-", ingredient)


# ============================================================
# COLLECT RAW INGREDIENTS
# ============================================================

print("\n\nChecking real Food.com ingredients...")
print("-" * 70)

raw_ingredients = []

for ingredients in df["RecipeIngredientParts"]:

    if isinstance(ingredients, (list, tuple)):

        for ingredient in ingredients:

            raw_ingredients.append(str(ingredient))

            if len(raw_ingredients) >= 100:
                break

    if len(raw_ingredients) >= 100:
        break


# ============================================================
# DISPLAY NORMALIZED INGREDIENTS
# ============================================================

print("\nFirst 100 real ingredients:")
print("-" * 70)

for ingredient in raw_ingredients:

    normalized = normalize_ingredient_name(
        ingredient
    )

    print(
        f"RAW        : {ingredient}"
    )

    print(
        f"NORMALIZED  : {normalized}"
    )

    print()


# ============================================================
# TEST SUBSTITUTION MATCHING
# ============================================================

print("=" * 70)
print("        POSSIBLE MATCHES")
print("=" * 70)

match_count = 0

for ingredient in raw_ingredients:

    normalized = normalize_ingredient_name(
        ingredient
    ).lower().strip()

    for sub in substitution_ingredients:

        if (
            sub == normalized
            or sub in normalized
            or normalized in sub
        ):

            print(
                f"{ingredient}  --->  {sub}"
            )

            match_count += 1


# ============================================================
# RESULT
# ============================================================

print("\n" + "=" * 70)

print(
    "Possible matches found:",
    match_count
)

print("=" * 70)