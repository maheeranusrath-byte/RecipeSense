# ============================================================
# RecipeSense
# Fast SQLite Recipe Search
# ============================================================

import json
import re
import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

SQLITE_FILE = (
    PROJECT_DIR
    / "data"
    / "recipe_index.db"
)


# ============================================================
# SQLITE
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
        """
        SELECT COUNT(DISTINCT ingredient)
        FROM ingredient_index
        """
    )

    ingredient_count = (
        cursor.fetchone()[0]
    )

    connection.close()

    return (
        recipe_count,
        ingredient_count
    )


try:

    recipe_count, ingredient_count = (
        get_database_stats()
    )

    print(
        "RecipeSense SQLite index ready."
    )

    print(
        f"Recipes available: "
        f"{recipe_count}"
    )

    print(
        f"Ingredients indexed: "
        f"{ingredient_count}"
    )

except Exception as error:

    print(
        "SQLite database initialization failed:"
    )

    print(error)


# ============================================================
# INGREDIENT NORMALIZATION
# ============================================================

INGREDIENT_ALIASES = {

    "chicken breast": "chicken",
    "chicken thigh": "chicken",
    "chicken thighs": "chicken",
    "chicken breasts": "chicken",

    "garlic clove": "garlic",
    "garlic cloves": "garlic",

    "onion": "onion",
    "onions": "onion",

    "tomato": "tomato",
    "tomatoes": "tomato",

    "potato": "potato",
    "potatoes": "potato",

    "carrot": "carrot",
    "carrots": "carrot",

    "egg": "egg",
    "eggs": "egg",

    "capsicum": "bell pepper",
    "bell peppers": "bell pepper",

    "green chilli": "green chili",
    "green chillies": "green chili",
    "green chilies": "green chili",

    "yogurt": "yogurt",
    "yoghurt": "yogurt",
    "curd": "yogurt",

    "rice": "rice",

    "flour": "flour",
    "all purpose flour": "flour",
    "maida": "flour",

    "sugar": "sugar",

    "salt": "salt",

    "butter": "butter",

    "oil": "oil",
    "vegetable oil": "oil",
    "olive oil": "oil"
}


def normalize_ingredient(
    ingredient
):

    if ingredient is None:

        return ""

    ingredient = str(
        ingredient
    ).lower().strip()

    ingredient = re.sub(
        r"[^a-z0-9\s]",
        " ",
        ingredient
    )

    ingredient = re.sub(
        r"\s+",
        " ",
        ingredient
    ).strip()

    # --------------------------------------------------------
    # Remove quantity/unit words
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

        word

        for word in words

        if word not in words_to_remove
    ]

    ingredient = " ".join(
        words
    )

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
        "medium",

        "boneless",
        "skinless",
        "seedless",

        "ripe",
        "whole",
        "halved",
        "quartered",
        "peeled"
    ]

    for word in preparation_words:

        ingredient = re.sub(

            r"\b"
            + re.escape(word)
            + r"\b",

            "",

            ingredient
        )

    ingredient = re.sub(

        r"\bcloves?\b",
        "",
        ingredient
    )

    ingredient = re.sub(

        r"\bpieces?\b",
        "",
        ingredient
    )

    ingredient = re.sub(

        r"\bof\b",
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
            ingredient[:-3]
            + "y"
        )

    elif (

        ingredient.endswith("s")

        and

        not ingredient.endswith("ss")
    ):

        ingredient = (
            ingredient[:-1]
        )

    # --------------------------------------------------------
    # Aliases
    # --------------------------------------------------------

    ingredient = INGREDIENT_ALIASES.get(

        ingredient,

        ingredient
    )

    return ingredient.strip()


# ============================================================
# USER INGREDIENTS
# ============================================================

def normalize_user_ingredients(
    user_input
):

    if user_input is None:

        return set()

    if isinstance(
        user_input,
        str
    ):

        ingredients = (
            user_input.split(",")
        )

    elif isinstance(
        user_input,
        (
            list,
            tuple,
            set
        )
    ):

        ingredients = user_input

    else:

        return set()

    normalized = set()

    for ingredient in ingredients:

        ingredient = (
            normalize_ingredient(
                ingredient
            )
        )

        if ingredient:

            normalized.add(
                ingredient
            )

    return normalized


# ============================================================
# CATEGORY NORMALIZATION
# ============================================================

def normalize_category(
    category
):

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
# CATEGORY MATCHING
# ============================================================

def recipe_matches_category(

    recipe_category,

    selected_category

):

    if not selected_category:

        return True

    recipe_category = (
        normalize_category(
            recipe_category
        )
    )

    selected_category = (
        normalize_category(
            selected_category
        )
    )

    if not recipe_category:

        return False

    if (
        recipe_category
        == selected_category
    ):

        return True

    if (
        selected_category
        in CATEGORY_GROUPS
    ):

        for category in CATEGORY_GROUPS[
            selected_category
        ]:

            category = (
                normalize_category(
                    category
                )
            )

            if (
                recipe_category
                == category
            ):

                return True

            if (
                category
                in recipe_category
            ):

                return True

    if (

        selected_category
        in recipe_category

        or

        recipe_category
        in selected_category

    ):

        return True

    return False


# ============================================================
# MATCH CATEGORY LABEL
# ============================================================

def get_category(
    percentage
):

    if percentage >= 75:

        return "Excellent match"

    if percentage >= 50:

        return "Good match"

    if percentage >= 25:

        return "Partial match"

    return "Low match"


# ============================================================
# FAST RECIPE SEARCH
# ============================================================

def find_recipes(

    user_ingredients,

    category=None,

    limit=10

):

    # --------------------------------------------------------
    # Normalize input
    # --------------------------------------------------------

    if isinstance(
        user_ingredients,
        str
    ):

        user_ingredients = (
            normalize_user_ingredients(
                user_ingredients
            )
        )

    else:

        user_ingredients = {

            normalize_ingredient(
                ingredient
            )

            for ingredient
            in user_ingredients

            if normalize_ingredient(
                ingredient
            )
        }

    if not user_ingredients:

        return []

    category = (
        normalize_category(
            category
        )
        if category
        else ""
    )

    connection = get_connection()

    cursor = connection.cursor()

    # ========================================================
    # IMPORTANT PERFORMANCE OPTIMIZATION
    # ========================================================
    #
    # OLD:
    #
    # ingredient -> ALL recipe IDs
    # -> Python set
    # -> huge batches
    # -> decode thousands/millions of JSON records
    #
    # NEW:
    #
    # SQLite directly finds recipes matching multiple
    # ingredients and returns only the strongest candidates.
    #
    # ========================================================

    ingredient_list = sorted(
        user_ingredients
    )

    placeholders = ",".join(
        ["?"] * len(
            ingredient_list
        )
    )

    # --------------------------------------------------------
    # Candidate selection
    # --------------------------------------------------------

    candidate_limit = 3000

    query = f"""

        SELECT

            r.recipe_id,

            r.name,

            r.category,

            r.ingredients,

            COUNT(
                DISTINCT ii.ingredient
            ) AS matched_count

        FROM ingredient_index ii

        INNER JOIN recipes r

            ON r.recipe_id =
               ii.recipe_id

        WHERE ii.ingredient
              IN ({placeholders})

        GROUP BY

            r.recipe_id,

            r.name,

            r.category,

            r.ingredients

        HAVING

            COUNT(
                DISTINCT ii.ingredient
            ) >= 2

        ORDER BY

            matched_count DESC

        LIMIT ?

    """

    parameters = (
        ingredient_list
        + [candidate_limit]
    )

    cursor.execute(
        query,
        parameters
    )

    candidates = (
        cursor.fetchall()
    )

    # ========================================================
    # EVALUATE ONLY CANDIDATES
    # ========================================================

    results = []

    seen_names = set()

    for recipe in candidates:

        recipe_category = (
            recipe["category"]
        )

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if not recipe_matches_category(

            recipe_category,

            category

        ):

            continue

        recipe_name = (
            recipe["name"]
        )

        # ----------------------------------------------------
        # Duplicate names
        # ----------------------------------------------------

        normalized_name = re.sub(

            r"[^a-z0-9]",

            "",

            recipe_name.lower()
        )

        if (
            normalized_name
            in seen_names
        ):

            continue

        # ----------------------------------------------------
        # Decode ingredient list
        # ----------------------------------------------------

        try:

            recipe_ingredients = set(

                json.loads(
                    recipe[
                        "ingredients"
                    ]
                )
            )

        except Exception:

            recipe_ingredients = set()

        if not recipe_ingredients:

            continue

        # ----------------------------------------------------
        # Matching
        # ----------------------------------------------------

        matched = (

            user_ingredients

            &

            recipe_ingredients
        )

        matched_count = len(
            matched
        )

        if matched_count < 2:

            continue

        total = len(
            recipe_ingredients
        )

        missing = (

            recipe_ingredients

            -

            user_ingredients
        )

        missing_count = len(
            missing
        )

        # ----------------------------------------------------
        # Percentage
        # ----------------------------------------------------

        percentage = (

            matched_count

            /

            total

        ) * 100

        # ----------------------------------------------------
        # User coverage
        # ----------------------------------------------------

        user_coverage = (

            matched_count

            /

            max(
                len(
                    user_ingredients
                ),
                1
            )

        ) * 100

        # ----------------------------------------------------
        # Missing ratio
        # ----------------------------------------------------

        missing_ratio = (

            missing_count

            /

            max(
                total,
                1
            )
        )

        # ----------------------------------------------------
        # Ranking
        # ----------------------------------------------------

        ranking_score = (

            percentage
            * 0.60

            +

            user_coverage
            * 0.25

            +

            (
                (1 - missing_ratio)
                * 100
                * 0.15
            )
        )

        results.append({

            "name":
                recipe_name,

            "percentage":
                percentage,

            "ranking_score":
                ranking_score,

            "matched":
                sorted(
                    matched
                ),

            "missing":
                sorted(
                    missing
                ),

            "total":
                total,

            "matched_count":
                matched_count,

            "missing_count":
                missing_count,

            "category":
                get_category(
                    percentage
                ),

            "recipe_category":
                recipe_category
        })

        seen_names.add(
            normalized_name
        )

    connection.close()

    # ========================================================
    # FINAL SORT
    # ========================================================

    results.sort(

        key=lambda item: (

            -item[
                "ranking_score"
            ],

            -item[
                "matched_count"
            ],

            item[
                "missing_count"
            ],

            -item[
                "percentage"
            ]
        )
    )

    return results[:limit]


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    results
):

    print(
        "\n"
        + "=" * 70
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

        return

    for index, recipe in enumerate(

        results,

        start=1

    ):

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"{index}. "
            f"{recipe['name']}"
        )

        print(
            f"Match: "
            f"{recipe['percentage']:.1f}%"
        )

        print(
            f"Category: "
            f"{recipe['recipe_category']}"
        )

        print(
            f"Match Level: "
            f"{recipe['category']}"
        )

        print(
            f"Matched: "
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
                "  None"
            )

    print(
        "\n"
        + "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\nEnter your ingredients."
    )

    user_input = input(
        "Ingredients: "
    )

    ingredients = (
        normalize_user_ingredients(
            user_input
        )
    )

    if not ingredients:

        print(
            "No valid ingredients found."
        )

        raise SystemExit

    category = input(
        "Category (optional): "
    ).strip()

    if not category:

        category = None

    print(
        "\nSearching..."
    )

    results = find_recipes(

        ingredients,

        category=category,

        limit=10
    )

    display_results(
        results
    )