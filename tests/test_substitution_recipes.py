import pandas as pd
import numpy as np
from pathlib import Path

from nlp.recipe_parser import normalize_ingredient_name
from nlp.substitution_engine import get_substitutes


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"

SUBSTITUTION_FILE = PROJECT_DIR / "data" / "substitutions.csv"


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("        RecipeSense - Substitution Recipe Finder")
print("=" * 70)


# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading dataset...")

df = pd.read_parquet(DATA_FILE)

print("Recipes loaded:", len(df))


# ============================================================
# LOAD SUBSTITUTION DATA
# ============================================================

substitution_df = pd.read_csv(
    SUBSTITUTION_FILE
)

substitution_ingredients = (
    substitution_df["ingredient"]
    .astype(str)
    .str.lower()
    .str.strip()
    .unique()
    .tolist()
)

print(
    "Substitution ingredients:",
    len(substitution_ingredients)
)


# ============================================================
# FIND MATCHING SUBSTITUTIONS
# ============================================================

def find_matching_substitution(ingredient):

    normalized = normalize_ingredient_name(
        str(ingredient)
    ).lower().strip()

    matches = []

    for substitution_ingredient in substitution_ingredients:

        if normalized == substitution_ingredient:

            matches.append(substitution_ingredient)

        elif substitution_ingredient in normalized:

            matches.append(substitution_ingredient)

        elif normalized in substitution_ingredient:

            matches.append(substitution_ingredient)

    return list(set(matches))


# ============================================================
# SEARCH RECIPES
# ============================================================

print("\nSearching recipes...")

found_recipes = []

for index, recipe in df.iterrows():

    ingredients = recipe["RecipeIngredientParts"]

    # Food.com stores these as NumPy arrays
    if isinstance(ingredients, np.ndarray):

        ingredients = ingredients.tolist()

    elif isinstance(ingredients, tuple):

        ingredients = list(ingredients)

    elif not isinstance(ingredients, list):

        continue

    matched = []

    for ingredient in ingredients:

        matches = find_matching_substitution(
            ingredient
        )

        for match in matches:

            if match not in matched:

                matched.append(match)

    if matched:

        found_recipes.append({
            "index": index,
            "name": recipe["Name"],
            "ingredients": ingredients,
            "matched": matched
        })

    # Stop after finding 5 recipes
    if len(found_recipes) >= 5:

        break


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("       RECIPES WITH AVAILABLE SUBSTITUTIONS")
print("=" * 70)


if not found_recipes:

    print("\nNo matching recipes found.")

else:

    for number, recipe in enumerate(
        found_recipes,
        start=1
    ):

        print("\n" + "-" * 70)

        print(
            f"RECIPE {number}:",
            recipe["name"]
        )

        print("\nIngredients:")

        for ingredient in recipe["ingredients"]:

            print(" -", ingredient)

        print(
            "\nIngredients with substitutions:"
        )

        for ingredient in recipe["matched"]:

            print(
                f"\n  {ingredient}"
            )

            substitutes = get_substitutes(
                ingredient
            )

            for substitute in substitutes:

                print(
                    f"    → {substitute['substitute']}"
                )

                print(
                    f"      Ratio : "
                    f"{substitute['ratio']}"
                )

                print(
                    f"      Reason: "
                    f"{substitute['reason']}"
                )


# ============================================================
# COMPLETION
# ============================================================

print("\n" + "=" * 70)
print("       Recipe search completed!")
print("=" * 70)