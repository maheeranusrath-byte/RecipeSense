import pickle
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

INDEX_FILE = PROJECT_DIR / "data" / "recipe_index.pkl"


# ============================================================
# LOAD RECIPE INDEX
# ============================================================

print("Loading RecipeSense index...")

with open(INDEX_FILE, "rb") as file:
    index_data = pickle.load(file)

recipes = index_data["recipes"]
ingredient_index = index_data["ingredient_index"]

print(f"Recipes available: {len(recipes)}")
print(f"Ingredients indexed: {len(ingredient_index)}")


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
# USER INGREDIENTS
# ============================================================

def normalize_user_ingredients(user_input):

    ingredients = user_input.split(",")

    normalized = set()

    for ingredient in ingredients:

        ingredient = normalize_ingredient(
            ingredient
        )

        if ingredient:
            normalized.add(ingredient)

    return normalized


# ============================================================
# MATCH CATEGORY
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
# NORMALIZE RECIPE CATEGORY
# ============================================================

def normalize_category(category):

    if category is None:
        return ""

    category = str(category).lower().strip()

    category = re.sub(
        r"[^a-z0-9\s&-]",
        "",
        category
    )

    category = re.sub(
        r"\s+",
        " ",
        category
    ).strip()

    return category


# ============================================================
# CATEGORY FILTERING
# ============================================================

def recipe_matches_category(recipe, selected_category):

    if not selected_category:
        return True

    recipe_category = normalize_category(
        recipe.get("category", "")
    )

    selected_category = normalize_category(
        selected_category
    )

    if not recipe_category:
        return False

    # Direct match
    if recipe_category == selected_category:
        return True

    # Category groups
    category_groups = {

        "main course": [
            "main course",
            "main dishes",
            "main dish",
            "one dish meal"
        ],

        "starters": [
            "starter",
            "starters",
            "appetizer",
            "appetizers"
        ],

        "desserts": [
            "dessert",
            "desserts"
        ],

        "shakes": [
            "shake",
            "shakes",
            "beverage",
            "beverages",
            "drinks",
            "drink"
        ],

        "salads": [
            "salad",
            "salads"
        ],

        "soups": [
            "soup",
            "soups"
        ],

        "snacks": [
            "snack",
            "snacks"
        ],

        "breakfast": [
            "breakfast",
            "breakfasts"
        ],

        "breads": [
            "bread",
            "breads"
        ]
    }

    if selected_category in category_groups:

        for category in category_groups[selected_category]:

            if category == recipe_category:
                return True

            if category in recipe_category:
                return True

    return False


# ============================================================
# RECIPE SEARCH
# ============================================================

def find_recipes(
    user_ingredients,
    category=None,
    limit=10
):

    candidate_ids = set()

    # --------------------------------------------------------
    # Find candidate recipes using ingredient index
    # --------------------------------------------------------

    for ingredient in user_ingredients:

        recipe_ids = ingredient_index.get(
            ingredient,
            []
        )

        candidate_ids.update(recipe_ids)

    results = []

    seen_names = set()

    # --------------------------------------------------------
    # Evaluate each candidate recipe
    # --------------------------------------------------------

    for recipe_id in candidate_ids:

        recipe = recipes.get(recipe_id)

        if recipe is None:
            continue

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if not recipe_matches_category(
            recipe,
            category
        ):
            continue

        recipe_name = recipe["name"]

        # ----------------------------------------------------
        # Remove duplicate recipe names
        # ----------------------------------------------------

        normalized_name = re.sub(
            r"[^a-z0-9]",
            "",
            recipe_name.lower()
        )

        if normalized_name in seen_names:
            continue

        # ----------------------------------------------------
        # Recipe ingredients
        # ----------------------------------------------------

        recipe_ingredients = set(
            recipe["ingredients"]
        )

        if not recipe_ingredients:
            continue

        # ----------------------------------------------------
        # Matched ingredients
        # ----------------------------------------------------

        matched = user_ingredients.intersection(
            recipe_ingredients
        )

        # We need at least 2 matching ingredients
        if len(matched) < 2:
            continue

        # ----------------------------------------------------
        # Missing ingredients
        # ----------------------------------------------------

        missing = (
            recipe_ingredients -
            user_ingredients
        )

        total = len(recipe_ingredients)

        matched_count = len(matched)

        missing_count = len(missing)

        # ----------------------------------------------------
        # Match percentage
        # ----------------------------------------------------

        percentage = (
            matched_count / total
        ) * 100

        # ----------------------------------------------------
        # Ingredient coverage
        #
        # Measures how much of the user's available
        # ingredients are actually useful for this recipe.
        # ----------------------------------------------------

        user_coverage = (
            matched_count /
            len(user_ingredients)
        ) * 100

        # ----------------------------------------------------
        # Missing ingredient penalty
        #
        # Fewer missing ingredients = better.
        # ----------------------------------------------------

        if total > 0:

            missing_ratio = (
                missing_count / total
            )

        else:

            missing_ratio = 1

        # ----------------------------------------------------
        # Final ranking score
        #
        # Main priority:
        #   1. Recipe match percentage
        #   2. Fewer missing ingredients
        #   3. More matched ingredients
        #
        # This produces a more useful recommendation order.
        # ----------------------------------------------------

        ranking_score = (
            (percentage * 0.60) +
            (user_coverage * 0.25) +
            ((1 - missing_ratio) * 100 * 0.15)
        )

        results.append({

            "name": recipe_name,

            "percentage": percentage,

            "ranking_score": ranking_score,

            "matched": sorted(matched),

            "missing": sorted(missing),

            "total": total,

            "matched_count": matched_count,

            "missing_count": missing_count,

            "category": get_category(
                percentage
            ),

            "recipe_category": recipe.get(
                "category",
                ""
            )
        })

        seen_names.add(
            normalized_name
        )

    # ========================================================
    # SORT RESULTS
    # ========================================================

    results.sort(
        key=lambda x: (
            -x["ranking_score"],
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

        print("\nTry:")

        print("  • Adding more ingredients")

        print("  • Choosing another category")

        return

    for i, recipe in enumerate(
        results,
        start=1
    ):

        print(
            "\n" + "-" * 70
        )

        print(
            f"{i}. {recipe['name']}"
        )

        print(
            f"Match: "
            f"{recipe['percentage']:.1f}%"
        )

        print(
            f"Category: "
            f"{recipe['category']}"
        )

        print(
            f"Ingredients matched: "
            f"{recipe['matched_count']} / "
            f"{recipe['total']}"
        )

        print("\nYou have:")

        for ingredient in recipe["matched"]:

            print(
                f"  ✓ {ingredient}"
            )

        print("\nMissing:")

        if recipe["missing"]:

            for ingredient in recipe["missing"]:

                print(
                    f"  ✗ {ingredient}"
                )

        else:

            print(
                "  None — you have all "
                "recognized ingredients!"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "             Recipe search completed!"
    )

    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\nEnter the ingredients you currently have."
    )

    print(
        "Example: chicken, rice, onion, garlic, yogurt"
    )

    user_input = input(
        "\nYour ingredients: "
    )

    user_ingredients = normalize_user_ingredients(
        user_input
    )

    if not user_ingredients:

        print(
            "\nNo valid ingredients were understood."
        )

        exit()

    print(
        "\nIngredients understood by RecipeSense:"
    )

    for ingredient in sorted(
        user_ingredients
    ):

        print(
            f" - {ingredient}"
        )

    category = input(
        "\nCategory (optional): "
    ).strip()

    if not category:
        category = None

    print(
        "\nSearching recipes..."
    )

    results = find_recipes(
        user_ingredients,
        category=category,
        limit=10
    )

    display_results(results)