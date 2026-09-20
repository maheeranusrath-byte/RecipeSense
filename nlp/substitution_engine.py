import pandas as pd
from pathlib import Path

from nlp.recipe_parser import extract_ingredient_info


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

SUBSTITUTION_FILE = (
    PROJECT_DIR
    / "data"
    / "substitutions.csv"
)


# ============================================================
# COMMON INGREDIENT ALIASES
# ============================================================

INGREDIENT_ALIASES = {

    "extra virgin olive oil": "olive oil",
    "virgin olive oil": "olive oil",
    "evoo": "olive oil",
    "ev olive oil": "olive oil",

    "all-purpose flour": "all purpose flour",
    "all purpose flour": "all purpose flour",

    "whole wheat flour": "whole wheat flour",

    "granulated sugar": "sugar",
    "white sugar": "sugar",

    "cow milk": "milk",
    "whole milk": "milk",

    "plain yogurt": "yogurt",
    "natural yogurt": "yogurt",

    "fresh garlic": "garlic",
    "garlic cloves": "garlic",

    "fresh onion": "onion",
    "onions": "onion",

    "lemon": "lemon juice",

    "chicken breast": "chicken",
    "chicken breasts": "chicken",

    "beef mince": "beef",
    "ground beef": "beef",

    "breadcrumbs": "breadcrumbs",

    "corn starch": "cornstarch",

    "parmesan": "parmesan cheese"
}


# ============================================================
# ADDITIONAL CURATED SUBSTITUTIONS
# ============================================================

ADDITIONAL_SUBSTITUTIONS = {

    "olive oil": [

        {
            "substitute": "vegetable oil",
            "ratio": "1:1",
            "reason": "Useful neutral cooking oil alternative"
        },

        {
            "substitute": "canola oil",
            "ratio": "1:1",
            "reason": "Useful neutral cooking oil alternative"
        },

        {
            "substitute": "sunflower oil",
            "ratio": "1:1",
            "reason": "Useful neutral cooking oil alternative"
        }

    ],

    "vegetable oil": [

        {
            "substitute": "canola oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        },

        {
            "substitute": "sunflower oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        },

        {
            "substitute": "olive oil",
            "ratio": "1:1",
            "reason": "Works well for many cooking applications"
        }

    ],

    "canola oil": [

        {
            "substitute": "vegetable oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        },

        {
            "substitute": "sunflower oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        }

    ],

    "sunflower oil": [

        {
            "substitute": "vegetable oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        },

        {
            "substitute": "canola oil",
            "ratio": "1:1",
            "reason": "Similar neutral cooking oil"
        }

    ],

    "butter": [

        {
            "substitute": "coconut oil",
            "ratio": "1:1",
            "reason": "Good alternative for baking and cooking"
        },

        {
            "substitute": "olive oil",
            "ratio": "3:4",
            "reason": "Useful for many savory cooking applications"
        },

        {
            "substitute": "vegetable shortening",
            "ratio": "1:1",
            "reason": "Useful alternative for baking"
        }

    ],

    "milk": [

        {
            "substitute": "soy milk",
            "ratio": "1:1",
            "reason": "Similar liquid consistency and useful dairy-free alternative"
        },

        {
            "substitute": "almond milk",
            "ratio": "1:1",
            "reason": "Useful dairy-free alternative"
        },

        {
            "substitute": "oat milk",
            "ratio": "1:1",
            "reason": "Useful dairy-free alternative"
        }

    ],

    "heavy cream": [

        {
            "substitute": "coconut cream",
            "ratio": "1:1",
            "reason": "Similar creamy consistency"
        },

        {
            "substitute": "evaporated milk",
            "ratio": "1:1",
            "reason": "Useful alternative in many creamy recipes"
        }

    ],

    "sour cream": [

        {
            "substitute": "greek yogurt",
            "ratio": "1:1",
            "reason": "Similar creamy texture"
        }

    ],

    "yogurt": [

        {
            "substitute": "greek yogurt",
            "ratio": "1:1",
            "reason": "Similar texture with a thicker consistency"
        },

        {
            "substitute": "buttermilk",
            "ratio": "1:1",
            "reason": "Useful alternative in some baking recipes"
        }

    ],

    "egg": [

        {
            "substitute": "flaxseed meal",
            "ratio": "1:1",
            "reason": "Can replace egg in some baking recipes"
        },

        {
            "substitute": "applesauce",
            "ratio": "1:4",
            "reason": "Can replace egg in some baked goods"
        }

    ],

    "sugar": [

        {
            "substitute": "honey",
            "ratio": "3:4",
            "reason": "Provides sweetness but adds liquid"
        },

        {
            "substitute": "maple syrup",
            "ratio": "3:4",
            "reason": "Provides sweetness but adds liquid"
        }

    ],

    "lemon juice": [

        {
            "substitute": "lime juice",
            "ratio": "1:1",
            "reason": "Similar acidity and citrus flavor"
        },

        {
            "substitute": "vinegar",
            "ratio": "1:1",
            "reason": "Provides acidity but changes the flavor"
        }

    ],

    "breadcrumbs": [

        {
            "substitute": "crushed crackers",
            "ratio": "1:1",
            "reason": "Similar coating and binding function"
        },

        {
            "substitute": "oats",
            "ratio": "1:1",
            "reason": "Can provide coating and binding"
        }

    ],

    "all purpose flour": [

        {
            "substitute": "oat flour",
            "ratio": "1:1",
            "reason": "Alternative flour for some recipes"
        },

        {
            "substitute": "whole wheat flour",
            "ratio": "1:1",
            "reason": "Alternative flour with a stronger flavor"
        }

    ],

    "cornstarch": [

        {
            "substitute": "arrowroot powder",
            "ratio": "1:1",
            "reason": "Similar thickening function"
        }

    ],

    "garlic": [

        {
            "substitute": "garlic powder",
            "ratio": "3:1",
            "reason": "Concentrated garlic flavor"
        }

    ],

    "onion": [

        {
            "substitute": "onion powder",
            "ratio": "3:1",
            "reason": "Concentrated onion flavor"
        }

    ],

    "parmesan cheese": [

        {
            "substitute": "nutritional yeast",
            "ratio": "1:1",
            "reason": "Provides savory cheesy flavor"
        }

    ],

    "soy sauce": [

        {
            "substitute": "tamari",
            "ratio": "1:1",
            "reason": "Similar savory umami flavor"
        },

        {
            "substitute": "coconut aminos",
            "ratio": "1:1",
            "reason": "Alternative savory sauce"
        }

    ],

    "rice": [

        {
            "substitute": "quinoa",
            "ratio": "1:1",
            "reason": "Alternative grain with a different texture"
        }

    ],

    "chicken": [

        {
            "substitute": "tofu",
            "ratio": "1:1",
            "reason": "Plant-based protein alternative"
        }

    ],

    "beef": [

        {
            "substitute": "mushrooms",
            "ratio": "1:1",
            "reason": "Savory plant-based alternative"
        }

    ]
}


# ============================================================
# LOAD CSV SUBSTITUTIONS
# ============================================================

def load_substitutions():

    return pd.read_csv(
        SUBSTITUTION_FILE
    )


# ============================================================
# NORMALIZE INGREDIENT
#
# This function now supports BOTH:
#
#     sugar
#
# and:
#
#     2 teaspoon sugar
#     1 cup milk
#     2 tablespoons butter
#
# ============================================================

def normalize_ingredient(ingredient):

    ingredient = str(
        ingredient
    ).lower().strip()

    ingredient = " ".join(
        ingredient.split()
    )

    # --------------------------------------------------------
    # Try parsing a complete ingredient expression first.
    # --------------------------------------------------------

    parsed = extract_ingredient_info(
        ingredient
    )

    if parsed:

        parsed_ingredient = parsed[0].get(
            "normalized_ingredient",
            ""
        )

        if parsed_ingredient:

            ingredient = str(
                parsed_ingredient
            ).lower().strip()

            ingredient = " ".join(
                ingredient.split()
            )

    # --------------------------------------------------------
    # Apply aliases
    # --------------------------------------------------------

    ingredient = INGREDIENT_ALIASES.get(
        ingredient,
        ingredient
    )

    return ingredient


# ============================================================
# FIND SUBSTITUTIONS FROM CSV
# ============================================================

def find_substitutes(ingredient):

    df = load_substitutions()

    ingredient = normalize_ingredient(
        ingredient
    )

    matches = df[
        df["ingredient"]
        .astype(str)
        .str.lower()
        .str.strip()
        .apply(normalize_ingredient)
        == ingredient
    ]

    return matches


# ============================================================
# GET SUBSTITUTIONS
# ============================================================

def get_substitutes(ingredient):

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # This now accepts:
    #
    # sugar
    # 2 teaspoon sugar
    # 1 cup milk
    # 2 tablespoons butter
    #
    # and automatically extracts the actual ingredient.
    # --------------------------------------------------------

    ingredient = normalize_ingredient(
        ingredient
    )

    results = []


    # ========================================================
    # 1. CSV SUBSTITUTIONS
    # ========================================================

    matches = find_substitutes(
        ingredient
    )

    for _, row in matches.iterrows():

        results.append({

            "ingredient":
                ingredient,

            "substitute":
                row["substitute"],

            "ratio":
                row["ratio"],

            "reason":
                row["reason"]

        })


    # ========================================================
    # 2. CURATED SUBSTITUTIONS
    # ========================================================

    additional = ADDITIONAL_SUBSTITUTIONS.get(
        ingredient,
        []
    )

    for item in additional:

        results.append({

            "ingredient":
                ingredient,

            "substitute":
                item["substitute"],

            "ratio":
                item["ratio"],

            "reason":
                item["reason"]

        })


    # ========================================================
    # 3. REMOVE DUPLICATES
    # ========================================================

    unique_results = []

    seen = set()

    for item in results:

        key = (

            item["ingredient"],

            item["substitute"]

        )

        if key not in seen:

            seen.add(
                key
            )

            unique_results.append(
                item
            )

    return unique_results


# ============================================================
# ANALYZE INGREDIENT
# ============================================================

def analyze_ingredient(
    ingredient_text
):

    extracted = extract_ingredient_info(
        ingredient_text
    )

    if not extracted:

        return None

    ingredient_data = extracted[0]

    normalized = normalize_ingredient(
        ingredient_data[
            "normalized_ingredient"
        ]
    )

    substitutes = get_substitutes(
        normalized
    )

    return {

        "original":
            ingredient_text,

        "ingredient":
            normalized,

        "quantity":
            ingredient_data[
                "quantity"
            ],

        "unit":
            ingredient_data[
                "unit"
            ],

        "substitutes":
            substitutes

    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(result):

    if result is None:

        print(
            "\nCould not understand the ingredient."
        )

        return


    print(
        "\n" + "-" * 60
    )

    print(
        "Original   :",
        result["original"]
    )

    print(
        "Ingredient :",
        result["ingredient"]
    )

    print(
        "Quantity   :",
        result["quantity"]
    )

    print(
        "Unit       :",
        result["unit"]
    )


    print(
        "\nPossible Substitutes"
    )

    print(
        "-" * 60
    )


    if result["substitutes"]:

        for item in result[
            "substitutes"
        ]:

            print(

                f"\n{result['quantity']} "
                f"{result['unit']} "
                f"{result['ingredient']} "
                f"→ "
                f"{item['substitute']}"

            )

            print(
                "Ratio  :",
                item["ratio"]
            )

            print(
                "Reason :",
                item["reason"]
            )

    else:

        print(
            "No substitution found."
        )


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "      RecipeSense Ingredient Analyzer"
    )

    print(
        "=" * 60
    )


    ingredient = input(
        "\nEnter an ingredient with quantity: "
    )


    result = analyze_ingredient(
        ingredient
    )


    display_result(
        result
    )


    print(
        "\n" + "=" * 60
    )