import pandas as pd
import numpy as np
import re
import pickle
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"

INDEX_FILE = PROJECT_DIR / "data" / "recipe_index.pkl"


# ============================================================
# INGREDIENT NORMALIZATION
# ============================================================

def normalize_ingredient(ingredient):

    if ingredient is None:
        return ""

    ingredient = str(ingredient).lower().strip()

    # Remove punctuation
    ingredient = re.sub(
        r"[^a-z0-9\s]",
        " ",
        ingredient
    )

    # Remove extra spaces
    ingredient = re.sub(
        r"\s+",
        " ",
        ingredient
    ).strip()

    # Remove quantity/unit words
    words_to_remove = {
        "cup",
        "cups",
        "tablespoon",
        "tablespoons",
        "tbsp",
        "teaspoon",
        "teaspoons",
        "tsp",
        "gram",
        "grams",
        "kg",
        "kilogram",
        "kilograms",
        "ml",
        "milliliter",
        "milliliters",
        "liter",
        "liters",
        "l",
        "ounce",
        "ounces",
        "oz",
        "pound",
        "pounds",
        "lb",
        "lbs",
        "pinch",
        "dash"
    }

    words = ingredient.split()

    words = [
        word
        for word in words
        if word not in words_to_remove
    ]

    ingredient = " ".join(words)

    # Remove preparation/descriptive words
    preparation_words = [
        "chopped",
        "diced",
        "sliced",
        "minced",
        "grated",
        "shredded",
        "crushed",
        "ground",
        "fresh",
        "frozen",
        "cooked",
        "raw",
        "melted",
        "softened",
        "large",
        "small",
        "medium"
    ]

    for word in preparation_words:

        ingredient = re.sub(
            r"\b" + word + r"\b",
            "",
            ingredient
        )

    ingredient = re.sub(
        r"\s+",
        " ",
        ingredient
    ).strip()

    # Basic plural normalization
    if ingredient.endswith("ies"):
        ingredient = ingredient[:-3] + "y"

    elif ingredient.endswith("s") and not ingredient.endswith("ss"):
        ingredient = ingredient[:-1]

    return ingredient


# ============================================================
# EXTRACT RECIPE INGREDIENTS
# ============================================================

def get_recipe_ingredients(ingredients):

    if ingredients is None:
        return set()

    # Food.com stores ingredient lists as NumPy arrays
    if isinstance(ingredients, np.ndarray):
        ingredients = ingredients.tolist()

    elif not isinstance(ingredients, (list, tuple)):
        return set()

    normalized = set()

    for ingredient in ingredients:

        ingredient = normalize_ingredient(
            ingredient
        )

        if ingredient:
            normalized.add(ingredient)

    return normalized


# ============================================================
# NORMALIZE CATEGORY
# ============================================================

def normalize_category(category):

    if category is None:
        return ""

    if pd.isna(category):
        return ""

    category = str(category).strip()

    return category


# ============================================================
# BUILD INDEX
# ============================================================

def build_index():

    print("=" * 70)
    print("              RecipeSense Recipe Index Builder")
    print("=" * 70)

    print("\nLoading cleaned recipe dataset...")

    df = pd.read_parquet(DATA_FILE)

    print(
        f"Recipes loaded: {len(df)}"
    )

    print("\nBuilding ingredient index...")
    print("This may take a few minutes.")

    # --------------------------------------------------------
    # Recipe information
    # --------------------------------------------------------

    recipes = {}

    # --------------------------------------------------------
    # Ingredient → Recipe IDs
    # --------------------------------------------------------

    ingredient_index = {}

    processed = 0

    for recipe_id, row in df.iterrows():

        recipe_name = str(
            row["Name"]
        ).strip()

        if not recipe_name:
            continue

        # ----------------------------------------------------
        # Get recipe category
        # ----------------------------------------------------

        category = normalize_category(
            row.get("RecipeCategory", "")
        )

        # ----------------------------------------------------
        # Get recipe ingredients
        # ----------------------------------------------------

        ingredients = get_recipe_ingredients(
            row["RecipeIngredientParts"]
        )

        # Ignore recipes with fewer than 3
        # recognized ingredients
        if len(ingredients) < 3:
            continue

        # ----------------------------------------------------
        # Store recipe information
        # ----------------------------------------------------

        recipe_data = {
            "name": recipe_name,
            "ingredients": ingredients,
            "category": category
        }

        recipes[recipe_id] = recipe_data

        # ----------------------------------------------------
        # Add recipe to ingredient index
        # ----------------------------------------------------

        for ingredient in ingredients:

            if ingredient not in ingredient_index:
                ingredient_index[ingredient] = []

            ingredient_index[ingredient].append(
                recipe_id
            )

        processed += 1

        # Progress display
        if processed % 10000 == 0:

            print(
                f"Processed recipes: {processed}"
            )

    # ========================================================
    # SAVE INDEX
    # ========================================================

    index_data = {
        "recipes": recipes,
        "ingredient_index": ingredient_index
    }

    print("\nSaving recipe index...")

    with open(
        INDEX_FILE,
        "wb"
    ) as file:

        pickle.dump(
            index_data,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("                 INDEX BUILD COMPLETE")
    print("=" * 70)

    print(
        f"\nRecipes indexed   : {len(recipes)}"
    )

    print(
        f"Unique ingredients: {len(ingredient_index)}"
    )

    print(
        f"Index saved to    : {INDEX_FILE}"
    )

    print("\nRecipe categories are now included!")

    print("\nRecipeSense is ready for fast searching!")

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_index()