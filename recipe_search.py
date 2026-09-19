import json
import re
import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

SQLITE_FILE = PROJECT_DIR / "data" / "recipe_index.db"


# ============================================================
# SQLITE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        SQLITE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INFORMATION
# ============================================================

def get_database_stats():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM recipes"
    )

    recipe_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT ingredient) FROM ingredient_index"
    )

    ingredient_count = cursor.fetchone()[0]

    connection.close()

    return recipe_count, ingredient_count


recipe_count, ingredient_count = get_database_stats()

print("RecipeSense SQLite index ready.")
print(
    f"Recipes available: {recipe_count}"
)
print(
    f"Ingredients indexed: {ingredient_count}"
)


# ============================================================
# INGREDIENT NORMALIZATION
# ============================================================

def normalize_ingredient(ingredient):

    if ingredient is None:
        return ""

    ingredient = str(
        ingredient
    ).lower().strip()

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

    # --------------------------------------------------------
    # Quantity and unit words
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Preparation words
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Basic plural normalization
    # --------------------------------------------------------

    if ingredient.endswith("ies"):

        ingredient = (
            ingredient[:-3] +
            "y"
        )

    elif (
        ingredient.endswith("s")
        and not ingredient.endswith("ss")
    ):

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

            normalized.add(
                ingredient
            )

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

    category = str(
        category
    ).lower().strip()

    category = category.replace(
        "_",
        " "
    )

    category = category.replace(
        "/",
        " "
    )

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
# CATEGORY GROUPS
# ============================================================

CATEGORY_GROUPS = {

    "main course": [
        "main course",
        "main courses",
        "main dish",
        "main dishes",
        "one dish meal",
        "one dish meals",
        "entree",
        "entrees"
    ],

    "starters": [
        "starter",
        "starters",
        "appetizer",
        "appetizers",
        "appetizer snack"
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
        "drink",
        "drinks"
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


# ============================================================
# CATEGORY FILTERING
# ============================================================

def recipe_matches_category(
    recipe_category,
    selected_category
):

    if not selected_category:

        return True

    recipe_category = normalize_category(
        recipe_category
    )

    selected_category = normalize_category(
        selected_category
    )

    if not recipe_category:

        return False

    # Direct match
    if recipe_category == selected_category:

        return True

    # Group match
    if selected_category in CATEGORY_GROUPS:

        for category in CATEGORY_GROUPS[
            selected_category
        ]:

            category = normalize_category(
                category
            )

            if recipe_category == category:

                return True

            if category in recipe_category:

                return True

    # Flexible matching
    if (
        selected_category in recipe_category
        or recipe_category in selected_category
    ):

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

    # --------------------------------------------------------
    # Normalize selected category
    # --------------------------------------------------------

    if category:

        category = normalize_category(
            category
        )

    # --------------------------------------------------------
    # Open database
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Find candidate recipe IDs
    #
    # IMPORTANT:
    # We collect IDs but DO NOT put all of them into
    # one giant SQL IN (...) query.
    # --------------------------------------------------------

    candidate_ids = set()

    for ingredient in user_ingredients:

        cursor.execute(
            """
            SELECT recipe_id
            FROM ingredient_index
            WHERE ingredient = ?
            """,
            (ingredient,)
        )

        rows = cursor.fetchall()

        for row in rows:

            candidate_ids.add(
                int(row["recipe_id"])
            )

    # --------------------------------------------------------
    # No candidates
    # --------------------------------------------------------

    if not candidate_ids:

        connection.close()

        return []

    # --------------------------------------------------------
    # Evaluate recipes in batches
    #
    # SQLite has a limit on the number of SQL variables.
    # Therefore we process recipe IDs in small batches.
    # --------------------------------------------------------

    candidate_ids = list(
        candidate_ids
    )

    BATCH_SIZE = 500

    results = []

    seen_names = set()

    # --------------------------------------------------------
    # Process batches
    # --------------------------------------------------------

    for start in range(
        0,
        len(candidate_ids),
        BATCH_SIZE
    ):

        batch_ids = candidate_ids[
            start:start + BATCH_SIZE
        ]

        placeholders = ",".join(
            ["?"] * len(batch_ids)
        )

        cursor.execute(
            f"""
            SELECT
                recipe_id,
                name,
                category,
                ingredients
            FROM recipes
            WHERE recipe_id IN ({placeholders})
            """,
            tuple(batch_ids)
        )

        recipes = cursor.fetchall()

        # ----------------------------------------------------
        # Evaluate recipes
        # ----------------------------------------------------

        for recipe in recipes:

            recipe_category = recipe[
                "category"
            ]

            # ------------------------------------------------
            # CATEGORY FILTER
            # ------------------------------------------------

            if not recipe_matches_category(
                recipe_category,
                category
            ):

                continue

            recipe_name = recipe[
                "name"
            ]

            # ------------------------------------------------
            # Remove duplicate recipe names
            # ------------------------------------------------

            normalized_name = re.sub(
                r"[^a-z0-9]",
                "",
                recipe_name.lower()
            )

            if normalized_name in seen_names:

                continue

            # ------------------------------------------------
            # Recipe ingredients
            # ------------------------------------------------

            try:

                recipe_ingredients = set(
                    json.loads(
                        recipe[
                            "ingredients"
                        ]
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                recipe_ingredients = set()

            if not recipe_ingredients:

                continue

            # ------------------------------------------------
            # Matched ingredients
            # ------------------------------------------------

            matched = (
                user_ingredients.intersection(
                    recipe_ingredients
                )
            )

            # ------------------------------------------------
            # Minimum matching requirement
            # ------------------------------------------------

            if len(matched) < 2:

                continue

            # ------------------------------------------------
            # Missing ingredients
            # ------------------------------------------------

            missing = (
                recipe_ingredients -
                user_ingredients
            )

            total = len(
                recipe_ingredients
            )

            matched_count = len(
                matched
            )

            missing_count = len(
                missing
            )

            # ------------------------------------------------
            # Match percentage
            # ------------------------------------------------

            percentage = (
                matched_count /
                total
            ) * 100

            # ------------------------------------------------
            # User coverage
            # ------------------------------------------------

            if len(user_ingredients) > 0:

                user_coverage = (
                    matched_count /
                    len(user_ingredients)
                ) * 100

            else:

                user_coverage = 0

            # ------------------------------------------------
            # Missing ratio
            # ------------------------------------------------

            if total > 0:

                missing_ratio = (
                    missing_count /
                    total
                )

            else:

                missing_ratio = 1

            # ------------------------------------------------
            # Ranking score
            # ------------------------------------------------

            ranking_score = (

                (percentage * 0.60)

                +

                (user_coverage * 0.25)

                +

                (
                    (1 - missing_ratio)
                    * 100
                    * 0.15
                )
            )

            results.append({

                "name": recipe_name,

                "percentage": percentage,

                "ranking_score": ranking_score,

                "matched": sorted(
                    matched
                ),

                "missing": sorted(
                    missing
                ),

                "total": total,

                "matched_count": matched_count,

                "missing_count": missing_count,

                "category": get_category(
                    percentage
                ),

                "recipe_category": (
                    recipe_category
                )

            })

            seen_names.add(
                normalized_name
            )

    # --------------------------------------------------------
    # Close database
    # --------------------------------------------------------

    connection.close()

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

    print(
        "\n" + "=" * 70
    )

    print(
        "                 RECIPES YOU CAN MAKE"
    )

    print(
        "=" * 70
    )

    if not results:

        print(
            "\nNo suitable recipes found."
        )

        print(
            "\nTry:"
        )

        print(
            "  • Adding more ingredients"
        )

        print(
            "  • Choosing another category"
        )

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
            f"Recipe Category: "
            f"{recipe['recipe_category']}"
        )

        print(
            f"Match Level: "
            f"{recipe['category']}"
        )

        print(
            f"Ingredients matched: "
            f"{recipe['matched_count']} / "
            f"{recipe['total']}"
        )

        print(
            "\nYou have:"
        )

        for ingredient in recipe[
            "matched"
        ]:

            print(
                f"  ✓ {ingredient}"
            )

        print(
            "\nMissing:"
        )

        if recipe["missing"]:

            for ingredient in recipe[
                "missing"
            ]:

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

    user_ingredients = (
        normalize_user_ingredients(
            user_input
        )
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

    display_results(
        results
    )