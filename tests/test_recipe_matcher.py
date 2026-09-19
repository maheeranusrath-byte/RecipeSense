import pandas as pd
import numpy as np
import re
from pathlib import Path


# ============================================================
# PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("             RecipeSense - What Can I Make?")
print("=" * 70)

print("\nLoading recipe dataset...")

df = pd.read_parquet(DATA_FILE)

print(f"Recipes loaded: {len(df)}")


# ============================================================
# INGREDIENT NORMALIZATION
# ============================================================

def normalize_ingredient(ingredient):
    """
    Convert an ingredient into a simpler searchable form.
    """

    if ingredient is None:
        return ""

    ingredient = str(ingredient).lower().strip()

    # Remove punctuation
    ingredient = re.sub(r"[^a-z0-9\s]", " ", ingredient)

    # Remove extra spaces
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    # Remove common quantity/unit words
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
        "g",
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
        word for word in words
        if word not in words_to_remove
    ]

    ingredient = " ".join(words)

    # Remove common preparation words
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

    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    # Basic plural normalization
    if ingredient.endswith("ies"):
        ingredient = ingredient[:-3] + "y"

    elif ingredient.endswith("s") and not ingredient.endswith("ss"):
        ingredient = ingredient[:-1]

    return ingredient


# ============================================================
# USER INGREDIENTS
# ============================================================

def normalize_user_ingredients(user_input):

    ingredients = user_input.split(",")

    normalized = set()

    for ingredient in ingredients:

        ingredient = normalize_ingredient(ingredient)

        if ingredient:
            normalized.add(ingredient)

    return normalized


# ============================================================
# DATASET INGREDIENT EXTRACTION
# ============================================================

def get_recipe_ingredients(row):

    ingredients = row["RecipeIngredientParts"]

    if ingredients is None:
        return []

    # Food.com parquet stores these as NumPy arrays
    if isinstance(ingredients, np.ndarray):
        ingredients = ingredients.tolist()

    elif not isinstance(ingredients, (list, tuple)):
        return []

    normalized_ingredients = set()

    for ingredient in ingredients:

        normalized = normalize_ingredient(ingredient)

        if normalized:
            normalized_ingredients.add(normalized)

    return list(normalized_ingredients)


# ============================================================
# MATCHING
# ============================================================

def calculate_match(user_ingredients, recipe_ingredients):

    recipe_set = set(recipe_ingredients)

    matched = user_ingredients.intersection(recipe_set)

    missing = recipe_set - user_ingredients

    total = len(recipe_set)

    if total == 0:
        return 0, [], []

    percentage = (len(matched) / total) * 100

    return percentage, sorted(matched), sorted(missing)


# ============================================================
# CATEGORY
# ============================================================

def get_category(percentage):

    if percentage >= 75:
        return "Excellent match"

    elif percentage >= 50:
        return "Good match"

    elif percentage >= 25:
        return "Partial match"

    else:
        return "Low match"


# ============================================================
# SEARCH RECIPES
# ============================================================

def find_recipes(user_ingredients, limit=10):

    results = []

    seen_names = set()

    print("\nSearching recipes...")

    for _, row in df.iterrows():

        recipe_name = str(row["Name"]).strip()

        if not recipe_name:
            continue

        # Stronger duplicate-name normalization
        normalized_name = re.sub(
            r"[^a-z0-9]",
            "",
            recipe_name.lower()
        )

        if normalized_name in seen_names:
            continue

        recipe_ingredients = get_recipe_ingredients(row)

        # Ignore recipes with too few recognized ingredients
        if len(recipe_ingredients) < 3:
            continue

        percentage, matched, missing = calculate_match(
            user_ingredients,
            recipe_ingredients
        )

        # We need at least 2 ingredients from the user's list
        if len(matched) < 2:
            continue

        results.append({
            "name": recipe_name,
            "percentage": percentage,
            "matched": matched,
            "missing": missing,
            "total": len(recipe_ingredients),
            "matched_count": len(matched),
            "missing_count": len(missing),
            "category": get_category(percentage)
        })

        seen_names.add(normalized_name)

    # ========================================================
    # IMPORTANT RANKING
    # ========================================================
    #
    # 1. More ingredients matched
    # 2. Fewer missing ingredients
    # 3. Higher percentage
    #
    # This prevents tiny 2-ingredient recipes from dominating.
    # ========================================================

    results.sort(
        key=lambda x: (
            -x["matched_count"],
            x["missing_count"],
            -x["percentage"]
        )
    )

    return results[:limit]


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(results):

    print("\n" + "=" * 70)
    print("                 RECIPES YOU CAN MAKE")
    print("=" * 70)

    if not results:

        print("\nNo suitable recipes found.")

        print(
            "\nTry entering more ingredients, "
            "for example:"
        )

        print("chicken, rice, onion, garlic, tomato")

        return

    for i, recipe in enumerate(results, start=1):

        print("\n" + "-" * 70)

        print(f"{i}. {recipe['name']}")

        print(
            f"Match: {recipe['percentage']:.1f}%"
        )

        print(
            f"Category: {recipe['category']}"
        )

        print(
            f"Ingredients matched: "
            f"{recipe['matched_count']} / {recipe['total']}"
        )

        print("\nYou have:")

        for ingredient in recipe["matched"]:
            print(f"  ✓ {ingredient}")

        print("\nMissing:")

        if recipe["missing"]:

            for ingredient in recipe["missing"]:
                print(f"  ✗ {ingredient}")

        else:

            print(
                "  None — you have all recognized ingredients!"
            )

    print("\n" + "=" * 70)
    print("             Recipe search completed!")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    user_input = input(
        "\nEnter the ingredients you currently have.\n"
        "Example: chicken, rice, onion, garlic, yogurt\n\n"
        "Your ingredients: "
    )

    user_ingredients = normalize_user_ingredients(
        user_input
    )

    print("\nIngredients understood by RecipeSense:")

    for ingredient in sorted(user_ingredients):
        print(f" - {ingredient}")

    results = find_recipes(
        user_ingredients,
        limit=10
    )

    display_results(results)