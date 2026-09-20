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

    # --------------------------------------------------------
    # Replace common symbols
    # --------------------------------------------------------

    ingredient = ingredient.replace(
        "&",
        " and "
    )

    # --------------------------------------------------------
    # Remove punctuation
    # --------------------------------------------------------

    ingredient = re.sub(
        r"[^a-z0-9\s]",
        " ",
        ingredient
    )

    # --------------------------------------------------------
    # Remove extra spaces
    # --------------------------------------------------------

    ingredient = re.sub(
        r"\s+",
        " ",
        ingredient
    ).strip()

    # --------------------------------------------------------
    # Quantity / unit words
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
    # Preparation / descriptor words
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
            r"\b" + re.escape(word) + r"\b",
            "",
            ingredient
        )

    # --------------------------------------------------------
    # Remove common ingredient-form words
    # --------------------------------------------------------

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
        r"\bstrips?\b",
        "",
        ingredient
    )

    ingredient = re.sub(
        r"\bslices?\b",
        "",
        ingredient
    )

    ingredient = re.sub(
        r"\bchunks?\b",
        "",
        ingredient
    )

    ingredient = re.sub(
        r"\bpackages?\b",
        "",
        ingredient
    )

    # --------------------------------------------------------
    # Remove "of"
    # --------------------------------------------------------

    ingredient = re.sub(
        r"\bof\b",
        "",
        ingredient
    )

    # --------------------------------------------------------
    # Remove extra spaces again
    # --------------------------------------------------------

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
        and not ingredient.endswith("ss")
    ):

        ingredient = ingredient[:-1]

    return ingredient.strip()


# ============================================================
# INGREDIENT ALIASES
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


# ============================================================
# NORMALIZE WITH ALIASES
# ============================================================

def normalize_with_alias(ingredient):

    ingredient = normalize_ingredient(
        ingredient
    )

    if not ingredient:
        return ""

    if ingredient in INGREDIENT_ALIASES:

        return INGREDIENT_ALIASES[
            ingredient
        ]

    return ingredient


# ============================================================
# USER INGREDIENTS
# ============================================================

def normalize_user_ingredients(user_input):

    if user_input is None:

        return set()

    # --------------------------------------------------------
    # Support both string and list input
    # --------------------------------------------------------

    if isinstance(
        user_input,
        str
    ):

        ingredients = user_input.split(",")

    elif isinstance(
        user_input,
        (list, tuple, set)
    ):

        ingredients = user_input

    else:

        return set()

    normalized = set()

    for ingredient in ingredients:

        ingredient = normalize_with_alias(
            ingredient
        )

        if ingredient:

            normalized.add(
                ingredient
            )

    return normalized


# ============================================================
# NORMALIZE DATABASE INGREDIENT
# ============================================================

def normalize_database_ingredient(
    ingredient
):

    return normalize_with_alias(
        ingredient
    )


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

    # --------------------------------------------------------
    # MAIN COURSE
    # --------------------------------------------------------

    "main course": [

        "main course",
        "main courses",
        "main dish",
        "main dishes",
        "one dish meal",
        "one dish meals",
        "entree",
        "entrees",
        "meat",
        "chicken",
        "pork",
        "lamb/sheep",
        "poultry",
        "beef",
        "stew",
        "stews",
        "curries",
        "rice",
        "pasta",
        "spaghetti"

    ],

    # --------------------------------------------------------
    # STARTERS
    #
    # Food.com combines many starter/snack recipes under
    # "Lunch/Snacks". We use that category as the database
    # source and then rank starter-like recipe names higher.
    # --------------------------------------------------------

    "starters": [

        "lunch/snacks",
        "appetizer",
        "appetizers",
        "starter",
        "starters",
        "hors d'oeuvre",
        "hors d oeuvres"

    ],

    # --------------------------------------------------------
    # DESSERTS
    # --------------------------------------------------------

    "desserts": [

        "dessert",
        "desserts",
        "frozen desserts",
        "cheesecake",
        "pie",
        "tarts",
        "candy",
        "bar cookie",
        "drop cookies",
        "gelatin"

    ],

    # --------------------------------------------------------
    # SHAKES
    # --------------------------------------------------------

    "shakes": [

        "shake",
        "shakes",
        "smoothie",
        "smoothies",
        "beverage",
        "beverages",
        "drink",
        "drinks",
        "punch beverage"

    ],

    # --------------------------------------------------------
    # SALADS
    # --------------------------------------------------------

    "salads": [

        "salad",
        "salads",
        "salad dressings"

    ],

    # --------------------------------------------------------
    # SOUPS
    # --------------------------------------------------------

    "soups": [

        "soup",
        "soups",
        "clear soup",
        "chowders"

    ],

    # --------------------------------------------------------
    # SNACKS
    #
    # Food.com uses "Lunch/Snacks".
    # --------------------------------------------------------

    "snacks": [

        "lunch/snacks",
        "snack",
        "snacks"

    ],

    # --------------------------------------------------------
    # BREAKFAST
    # --------------------------------------------------------

    "breakfast": [

        "breakfast",
        "breakfasts",
        "brunch"

    ],

    # --------------------------------------------------------
    # BREADS
    # --------------------------------------------------------

    "breads": [

        "bread",
        "breads",
        "quick breads",
        "yeast breads",
        "scones"

    ]
}


# ============================================================
# STARTER / SNACK NAME SIGNALS
# ============================================================

STARTER_KEYWORDS = [

    "appetizer",
    "appetisers",
    "appetizer",
    "starter",
    "starters",
    "hors d'oeuvre",
    "hors d oeuvres",
    "dip",
    "dips",
    "bruschetta",
    "pakora",
    "pakoras",
    "samosa",
    "samosas",
    "spring roll",
    "spring rolls",
    "egg roll",
    "egg rolls",
    "stuffed mushroom",
    "stuffed mushrooms",
    "finger food",
    "finger foods",
    "bites",
    "bite",
    "canape",
    "canapes",
    "croquette",
    "croquettes",
    "fritter",
    "fritters",
    "tapas"
]


SNACK_KEYWORDS = [

    "snack",
    "snacks",
    "chips",
    "popcorn",
    "cracker",
    "crackers",
    "cookie",
    "cookies",
    "trail mix",
    "granola bar",
    "granola bars",
    "energy bar",
    "energy bars",
    "munchies",
    "party mix",
    "party snack",
    "party snacks",
    "nuts",
    "roasted",
    "roast",
    "nachos",
    "pretzel",
    "pretzels"
]


# ============================================================
# CATEGORY SIGNAL SCORE
# ============================================================

def get_category_signal_score(
    recipe_name,
    recipe_category,
    selected_category
):

    if not selected_category:

        return 0

    selected_category = normalize_category(
        selected_category
    )

    recipe_name = str(
        recipe_name
        if recipe_name
        else ""
    ).lower()

    recipe_category = str(
        recipe_category
        if recipe_category
        else ""
    ).lower()

    searchable_text = (
        recipe_name
        + " "
        + recipe_category
    )

    score = 0

    # --------------------------------------------------------
    # STARTERS
    # --------------------------------------------------------

    if selected_category == "starters":

        for keyword in STARTER_KEYWORDS:

            if keyword in searchable_text:

                score += 15

        # A Lunch/Snacks recipe without an obvious
        # starter keyword is still allowed.
        if "lunch/snacks" in recipe_category:

            score += 2

    # --------------------------------------------------------
    # SNACKS
    # --------------------------------------------------------

    elif selected_category == "snacks":

        for keyword in SNACK_KEYWORDS:

            if keyword in searchable_text:

                score += 15

        if "lunch/snacks" in recipe_category:

            score += 2

    # --------------------------------------------------------
    # OTHER CATEGORIES
    # --------------------------------------------------------

    elif selected_category in CATEGORY_GROUPS:

        for keyword in CATEGORY_GROUPS[
            selected_category
        ]:

            normalized_keyword = normalize_category(
                keyword
            )

            if (
                recipe_category
                == normalized_keyword
            ):

                score += 10

            elif (
                normalized_keyword
                in recipe_category
            ):

                score += 5

    return score


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

    # --------------------------------------------------------
    # Direct match
    # --------------------------------------------------------

    if recipe_category == selected_category:

        return True

    # --------------------------------------------------------
    # Group match
    # --------------------------------------------------------

    if selected_category in CATEGORY_GROUPS:

        for category in CATEGORY_GROUPS[
            selected_category
        ]:

            normalized_category = normalize_category(
                category
            )

            if recipe_category == normalized_category:

                return True

            if normalized_category in recipe_category:

                return True

    # --------------------------------------------------------
    # Flexible matching
    #
    # IMPORTANT:
    # Do not use this blindly for Starters/Snacks because
    # "starter" and "snack" do not occur in "lunch snacks"
    # in a reliable way after normalization.
    # --------------------------------------------------------

    if selected_category not in {
        "starters",
        "snacks"
    }:

        if (
            selected_category in recipe_category
            or recipe_category in selected_category
        ):

            return True

    return False


# ============================================================
# PARSE RECIPE INGREDIENTS
# ============================================================

def parse_recipe_ingredients(
    ingredients_json
):

    if not ingredients_json:

        return set()

    # --------------------------------------------------------
    # SQLite stores ingredients as JSON text.
    # --------------------------------------------------------

    try:

        raw_ingredients = json.loads(
            ingredients_json
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return set()

    if not isinstance(
        raw_ingredients,
        (list, tuple, set)
    ):

        return set()

    normalized = set()

    for ingredient in raw_ingredients:

        normalized_ingredient = (
            normalize_database_ingredient(
                ingredient
            )
        )

        if normalized_ingredient:

            normalized.add(
                normalized_ingredient
            )

    return normalized


# ============================================================
# RECIPE SEARCH
# ============================================================

def find_recipes(
    user_ingredients,
    category=None,
    limit=10
):

    # --------------------------------------------------------
    # Normalize user ingredients
    # --------------------------------------------------------

    normalized_user_ingredients = set()

    for ingredient in user_ingredients:

        normalized = normalize_with_alias(
            ingredient
        )

        if normalized:

            normalized_user_ingredients.add(
                normalized
            )

    user_ingredients = (
        normalized_user_ingredients
    )

    if not user_ingredients:

        return []

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
    # Process recipes in batches
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
            # Category filter
            # ------------------------------------------------

            if not recipe_matches_category(
                recipe_category,
                category
            ):

                continue

            recipe_name = recipe[
                "name"
            ]

            if not recipe_name:

                continue

            # ------------------------------------------------
            # Duplicate recipe names
            # ------------------------------------------------

            normalized_name = re.sub(
                r"[^a-z0-9]",
                "",
                str(recipe_name).lower()
            )

            if normalized_name in seen_names:

                continue

            # ------------------------------------------------
            # Recipe ingredients
            # ------------------------------------------------

            recipe_ingredients = (
                parse_recipe_ingredients(
                    recipe["ingredients"]
                )
            )

            if not recipe_ingredients:

                continue

            # ------------------------------------------------
            # Matched ingredients
            # ------------------------------------------------

            matched = (
                user_ingredients
                .intersection(
                    recipe_ingredients
                )
            )

            # ------------------------------------------------
            # Require at least 2 ingredients
            # ------------------------------------------------

            if len(matched) < 2:

                continue

            # ------------------------------------------------
            # Missing ingredients
            # ------------------------------------------------

            missing = (
                recipe_ingredients
                - user_ingredients
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

            if total == 0:

                continue

            # ------------------------------------------------
            # Match percentage
            # ------------------------------------------------

            percentage = (
                matched_count
                / total
            ) * 100

            # ------------------------------------------------
            # User coverage
            # ------------------------------------------------

            if len(user_ingredients) > 0:

                user_coverage = (
                    matched_count
                    / len(user_ingredients)
                ) * 100

            else:

                user_coverage = 0

            # ------------------------------------------------
            # Missing ratio
            # ------------------------------------------------

            missing_ratio = (
                missing_count
                / total
            )

            # ------------------------------------------------
            # Base ranking score
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

            # ------------------------------------------------
            # Category relevance bonus
            #
            # This is especially important for distinguishing
            # Starters from Snacks.
            # ------------------------------------------------

            category_signal = (
                get_category_signal_score(
                    recipe_name,
                    recipe_category,
                    category
                )
            )

            ranking_score += category_signal

            # ------------------------------------------------
            # JSON-safe lists
            # ------------------------------------------------

            matched_list = sorted(
                list(matched)
            )

            missing_list = sorted(
                list(missing)
            )

            # ------------------------------------------------
            # Create result
            # ------------------------------------------------

            results.append({

                "name": str(
                    recipe_name
                ),

                "percentage": float(
                    percentage
                ),

                "ranking_score": float(
                    ranking_score
                ),

                "matched": matched_list,

                "missing": missing_list,

                "total": int(
                    total
                ),

                "matched_count": int(
                    matched_count
                ),

                "missing_count": int(
                    missing_count
                ),

                "category": str(
                    get_category(
                        percentage
                    )
                ),

                "recipe_category": str(
                    recipe_category
                    if recipe_category
                    else ""
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

    # ========================================================
    # FINAL JSON-SAFE CLEANUP
    # ========================================================

    safe_results = []

    for result in results[:limit]:

        safe_results.append({

            "name": result["name"],

            "percentage": float(
                result["percentage"]
            ),

            "ranking_score": float(
                result["ranking_score"]
            ),

            "matched": list(
                result["matched"]
            ),

            "missing": list(
                result["missing"]
            ),

            "total": int(
                result["total"]
            ),

            "matched_count": int(
                result["matched_count"]
            ),

            "missing_count": int(
                result["missing_count"]
            ),

            "category": result[
                "category"
            ],

            "recipe_category": result[
                "recipe_category"
            ]

        })

    return safe_results


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