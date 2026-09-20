# ============================================================
# RecipeSense
# AI Recipe Understanding & Ingredient Substitution System
# ============================================================

from flask import Flask, render_template, request, jsonify

import pandas as pd
import numpy as np
import sqlite3
import time

from pathlib import Path
from difflib import SequenceMatcher

from nlp.recipe_parser import extract_ingredient_info
from nlp.substitution_engine import get_substitutes

from recipe_search import (
    find_recipes,
    normalize_user_ingredients
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

DATA_FILE = DATA_DIR / "recipes_cleaned.parquet"
SQLITE_FILE = DATA_DIR / "recipe_index.db"


# ============================================================
# SQLITE CONNECTION
# ============================================================

def get_sqlite_connection():

    connection = sqlite3.connect(
        SQLITE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(value):

    if isinstance(value, dict):

        return {
            key: make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, set):

        return [
            make_json_safe(item)
            for item in sorted(
                value,
                key=lambda x: str(x)
            )
        ]

    if isinstance(value, np.ndarray):

        return [
            make_json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, np.integer):

        return int(value)

    if isinstance(value, np.floating):

        if np.isnan(value):

            return None

        return float(value)

    if value is None:

        return None

    try:

        if pd.isna(value):

            return None

    except Exception:

        pass

    return value


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/analyze-page")
def analyze_page():

    return render_template(
        "analyze.html"
    )


@app.route("/find-recipes-page")
def find_recipes_page():

    return render_template(
        "find_recipes.html"
    )


@app.route("/substitute-page")
def substitute_page():

    return render_template(
        "substitute.html"
    )


@app.route("/make-recipe-page")
def make_recipe_page():

    return render_template(
        "make_recipe.html"
    )


# ============================================================
# ANALYZE RECIPE
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze_recipe():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No recipe data received."
            })

        recipe_text = data.get(
            "recipe",
            ""
        ).strip()

        if not recipe_text:

            return jsonify({
                "success": False,
                "message": "Please enter a recipe."
            })

        ingredients = []

        for line in recipe_text.split("\n"):

            line = line.strip()

            if not line:
                continue

            parsed = extract_ingredient_info(
                line
            )

            if parsed:

                ingredients.extend(
                    parsed
                )

        # ----------------------------------------------------
        # Cooking actions
        # ----------------------------------------------------

        action_words = [

            "add",
            "bake",
            "beat",
            "boil",
            "chop",
            "combine",
            "cook",
            "cut",
            "fry",
            "grill",
            "heat",
            "knead",
            "marinate",
            "melt",
            "mix",
            "peel",
            "pour",
            "process",
            "roast",
            "saute",
            "sauté",
            "season",
            "serve",
            "simmer",
            "slice",
            "spread",
            "sprinkle",
            "stir",
            "strain",
            "toss",
            "transfer",
            "whisk",
            "freeze",
            "blend",
            "fold",
            "drain",
            "grate",
            "roll"

        ]

        lower_text = recipe_text.lower()

        cooking_actions = []

        for action in action_words:

            if action in lower_text:

                cooking_actions.append(
                    action
                )

        cooking_actions = sorted(
            list(
                set(cooking_actions)
            )
        )

        # ----------------------------------------------------
        # Substitutions
        # ----------------------------------------------------

        substitution_results = []

        for ingredient in ingredients:

            normalized = ingredient.get(
                "normalized_ingredient",
                ingredient.get(
                    "ingredient",
                    ""
                )
            )

            substitutes = get_substitutes(
                normalized
            )

            substitution_results.append({

                "ingredient": normalized,

                "substitutes": substitutes

            })

        return jsonify(
            make_json_safe({

                "success": True,

                "ingredients": ingredients,

                "actions": cooking_actions,

                "substitutions": substitution_results

            })
        )

    except Exception as error:

        print("\nANALYZE ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message": "Unable to analyze recipe.",

            "error": str(error)

        }), 500


# ============================================================
# INGREDIENT SUBSTITUTION
# ============================================================

@app.route("/substitute", methods=["POST"])
def substitute():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No ingredient data received."
            })

        ingredient = data.get(
            "ingredient",
            ""
        ).strip()

        if not ingredient:

            return jsonify({
                "success": False,
                "message": "Please enter an ingredient."
            })

        result = get_substitutes(
            ingredient
        )

        return jsonify(
            make_json_safe({

                "success": True,

                "ingredient": ingredient,

                "substitutes": result

            })
        )

    except Exception as error:

        print("\nSUBSTITUTION ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message": "Unable to find substitutions.",

            "error": str(error)

        }), 500


# ============================================================
# WHAT CAN I MAKE?
# ============================================================

@app.route("/find-recipes", methods=["POST"])
def find_recipe_results():

    start_time = time.perf_counter()

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message": "No recipe search data received."

            })

        ingredients_text = data.get(
            "ingredients",
            ""
        ).strip()

        category = data.get(
            "category",
            ""
        ).strip()

        if not ingredients_text:

            return jsonify({

                "success": False,

                "message": "Please enter ingredients."

            })

        # ====================================================
        # NORMALIZE INGREDIENTS
        # ====================================================

        user_ingredients = normalize_user_ingredients(
            ingredients_text
        )

        if not user_ingredients:

            return jsonify({

                "success": False,

                "message": "No valid ingredients found."

            })

        # ====================================================
        # SEARCH RECIPES
        # ====================================================

        search_start = time.perf_counter()

        results = find_recipes(

            user_ingredients,

            category=category,

            limit=10

        )

        search_time = (
            time.perf_counter()
            -
            search_start
        )

        # ====================================================
        # OPTIMIZED RECIPE ID LOOKUP
        #
        # OLD:
        #
        # for every recipe:
        #     SELECT recipe_id ...
        #
        # NEW:
        #
        # ONE SQLite query for all recipe names.
        # ====================================================

        enrichment_start = time.perf_counter()

        enriched_results = []

        if results:

            recipe_names = [

                str(
                    result.get(
                        "name",
                        ""
                    )
                )

                for result in results

                if result.get(
                    "name",
                    ""
                )
            ]

            recipe_id_map = {}

            if recipe_names:

                connection = get_sqlite_connection()

                cursor = connection.cursor()

                placeholders = ",".join(
                    ["?"] * len(recipe_names)
                )

                query = f"""
                    SELECT
                        recipe_id,
                        name
                    FROM recipes
                    WHERE name IN ({placeholders})
                """

                cursor.execute(
                    query,
                    recipe_names
                )

                rows = cursor.fetchall()

                for row in rows:

                    recipe_id_map[
                        row["name"]
                    ] = row["recipe_id"]

                connection.close()

            # ------------------------------------------------
            # Add IDs without additional database queries
            # ------------------------------------------------

            for result in results:

                result_copy = dict(
                    result
                )

                recipe_name = result_copy.get(
                    "name",
                    ""
                )

                result_copy["recipe_id"] = (
                    recipe_id_map.get(
                        recipe_name
                    )
                )

                enriched_results.append(
                    result_copy
                )

        enrichment_time = (
            time.perf_counter()
            -
            enrichment_start
        )

        total_time = (
            time.perf_counter()
            -
            start_time
        )

        # ====================================================
        # PERFORMANCE DEBUG INFORMATION
        # ====================================================

        print()
        print("=" * 60)
        print("RECIPE SEARCH PERFORMANCE")
        print("=" * 60)

        print(
            "Ingredients:",
            ingredients_text
        )

        print(
            "Category:",
            category
        )

        print(
            "Results:",
            len(enriched_results)
        )

        print(
            f"Search time:      {search_time:.3f} seconds"
        )

        print(
            f"ID lookup time:   {enrichment_time:.3f} seconds"
        )

        print(
            f"Total backend:    {total_time:.3f} seconds"
        )

        print("=" * 60)

        # ====================================================
        # RESPONSE
        # ====================================================

        response_data = {

            "success": True,

            "ingredients": user_ingredients,

            "category": category,

            "results": enriched_results

        }

        return jsonify(
            make_json_safe(
                response_data
            )
        )

    except Exception as error:

        print("\nFIND RECIPES ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message": "Unable to find recipes.",

            "error": str(error)

        }), 500


# ============================================================
# RECIPE DETAIL HELPERS
# ============================================================

def get_recipe_columns():

    return [

        "RecipeId",
        "Name",
        "Description",
        "RecipeCategory",
        "Keywords",
        "CookTime",
        "PrepTime",
        "TotalTime",
        "RecipeIngredientQuantities",
        "RecipeIngredientParts",
        "RecipeInstructions",
        "RecipeServings",
        "Calories"

    ]


# ============================================================
# LOAD RECIPE FROM PARQUET BY NAME
# ============================================================

def load_recipe_from_parquet(
    recipe_name
):

    columns = get_recipe_columns()

    recipe_df = pd.read_parquet(

        DATA_FILE,

        columns=columns

    )

    target_name = normalize_dish_name(
        recipe_name
    )

    normalized_names = (

        recipe_df["Name"]

        .astype(str)

        .str.lower()

        .str.strip()

    )

    # --------------------------------------------------------
    # Exact normalized match
    # --------------------------------------------------------

    exact_mask = (

        normalized_names

        .apply(
            normalize_dish_name
        )

        == target_name

    )

    matches = recipe_df[
        exact_mask
    ]

    # --------------------------------------------------------
    # Token matching fallback
    # --------------------------------------------------------

    if matches.empty:

        query_tokens = get_dish_tokens(
            recipe_name
        )

        if not query_tokens:

            return None

        normalized_series = (

            normalized_names

            .apply(
                normalize_dish_name
            )

        )

        mask = pd.Series(
            True,
            index=recipe_df.index
        )

        for token in query_tokens:

            if token == "biryani":

                token_mask = (

                    normalized_series.str.contains(

                        "biryani|biriyani",

                        regex=True,

                        na=False

                    )

                )

            else:

                token_mask = (

                    normalized_series.str.contains(

                        rf"\b{token}\b",

                        regex=True,

                        na=False

                    )

                )

            mask = mask & token_mask

        matches = recipe_df[
            mask
        ]

    if matches.empty:

        return None

    return matches.iloc[0]


# ============================================================
# BUILD RECIPE DETAIL OBJECT
# ============================================================

def build_recipe_detail(
    recipe_row
):

    quantities = recipe_row[
        "RecipeIngredientQuantities"
    ]

    ingredients = recipe_row[
        "RecipeIngredientParts"
    ]

    try:

        quantities = list(
            quantities
        )

    except Exception:

        quantities = []

    try:

        ingredients = list(
            ingredients
        )

    except Exception:

        ingredients = []

    ingredient_list = []

    for index, ingredient in enumerate(
        ingredients
    ):

        ingredient = str(
            ingredient
        ).strip()

        if not ingredient:

            continue

        quantity = ""

        if index < len(
            quantities
        ):

            quantity = str(
                quantities[index]
            ).strip()

            if quantity.lower() == "nan":

                quantity = ""

        parsed = extract_ingredient_info(

            f"{quantity} {ingredient}".strip()

        )

        normalized = ingredient
        parsed_quantity = quantity
        parsed_unit = ""

        if parsed:

            parsed_item = parsed[0]

            normalized = parsed_item.get(
                "normalized_ingredient",
                ingredient
            )

            parsed_quantity = parsed_item.get(
                "quantity",
                quantity
            )

            parsed_unit = parsed_item.get(
                "unit",
                ""
            )

        substitutions = get_substitutes(
            normalized
        )

        if parsed_quantity and parsed_unit:

            display = (

                f"{parsed_quantity} "
                f"{parsed_unit} "
                f"{ingredient}"

            )

        elif parsed_quantity:

            display = (

                f"{parsed_quantity} "
                f"{ingredient}"

            )

        else:

            display = ingredient

        ingredient_list.append({

            "ingredient": ingredient,

            "display": display,

            "normalized_ingredient": normalized,

            "quantity": parsed_quantity,

            "unit": parsed_unit,

            "substitutions": substitutions

        })

    # --------------------------------------------------------
    # Instructions
    # --------------------------------------------------------

    instructions = recipe_row[
        "RecipeInstructions"
    ]

    if instructions is None:

        instructions = []

    try:

        instructions = list(
            instructions
        )

    except Exception:

        instructions = [
            str(instructions)
        ]

    cleaned_instructions = []

    for instruction in instructions:

        instruction = str(
            instruction
        ).strip()

        if instruction:

            cleaned_instructions.append(
                instruction
            )

    # --------------------------------------------------------
    # Clean basic values
    # --------------------------------------------------------

    def clean_value(
        value,
        default=""
    ):

        if value is None:

            return default

        try:

            if pd.isna(value):

                return default

        except Exception:

            pass

        return value

    # --------------------------------------------------------
    # Recipe object
    # --------------------------------------------------------

    recipe = {

        "id": clean_value(
            recipe_row["RecipeId"]
        ),

        "name": clean_value(
            recipe_row["Name"]
        ),

        "category": clean_value(
            recipe_row["RecipeCategory"]
        ),

        "description": clean_value(
            recipe_row["Description"]
        ),

        "keywords": clean_value(
            recipe_row["Keywords"]
        ),

        "prep_time": clean_value(
            recipe_row["PrepTime"]
        ),

        "cook_time": clean_value(
            recipe_row["CookTime"]
        ),

        "total_time": clean_value(
            recipe_row["TotalTime"]
        ),

        "servings": clean_value(
            recipe_row["RecipeServings"]
        ),

        "calories": clean_value(
            recipe_row["Calories"]
        ),

        "ingredients": ingredient_list,

        "instructions": cleaned_instructions

    }

    return recipe


# ============================================================
# RECIPE DETAILS
# ============================================================

@app.route(
    "/recipe-details",
    methods=["GET", "POST"]
)
def recipe_details():

    try:

        # ====================================================
        # GET
        # ====================================================

        if request.method == "GET":

            recipe_name = request.args.get(
                "name",
                ""
            ).strip()

            if not recipe_name:

                return jsonify({

                    "success": False,

                    "message": "Recipe name is required."

                })

            print()
            print("=" * 60)
            print("RECIPE DETAILS REQUEST")
            print("Recipe name:", recipe_name)

            recipe_row = load_recipe_from_parquet(
                recipe_name
            )

            if recipe_row is None:

                return jsonify({

                    "success": False,

                    "message": "Recipe not found."

                })

            recipe = build_recipe_detail(
                recipe_row
            )

            response = {

                "success": True,

                "recipe": recipe,

                "result": recipe

            }

            print(
                "Recipe loaded:",
                recipe["name"]
            )

            print("=" * 60)

            return jsonify(
                make_json_safe(
                    response
                )
            )

        # ====================================================
        # POST
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message": "No recipe data received."

            })

        recipe_id = data.get(
            "recipe_id"
        )

        recipe_name = data.get(
            "name",
            ""
        ).strip()

        # ====================================================
        # POST BY NAME
        # ====================================================

        if recipe_id is None and recipe_name:

            recipe_row = load_recipe_from_parquet(
                recipe_name
            )

            if recipe_row is None:

                return jsonify({

                    "success": False,

                    "message": "Recipe not found."

                })

            recipe = build_recipe_detail(
                recipe_row
            )

            return jsonify(
                make_json_safe({

                    "success": True,

                    "recipe": recipe,

                    "result": recipe

                })
            )

        # ====================================================
        # POST BY ID
        # ====================================================

        if recipe_id is None:

            return jsonify({

                "success": False,

                "message": "Recipe ID or recipe name is required."

            })

        columns = get_recipe_columns()

        recipe_df = pd.read_parquet(

            DATA_FILE,

            columns=columns

        )

        recipe_ids = pd.to_numeric(

            recipe_df["RecipeId"],

            errors="coerce"

        )

        recipe_df = recipe_df[
            recipe_ids == float(recipe_id)
        ]

        if recipe_df.empty:

            return jsonify({

                "success": False,

                "message": "Recipe not found."

            })

        row = recipe_df.iloc[0]

        recipe = build_recipe_detail(
            row
        )

        return jsonify(
            make_json_safe({

                "success": True,

                "recipe": recipe,

                "result": recipe

            })
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("RECIPE DETAILS ERROR:")
        print(error)
        print("=" * 60)

        return jsonify({

            "success": False,

            "message": "Unable to load recipe details.",

            "error": str(error)

        }), 500


# ============================================================
# DISH NAME NORMALIZATION
# ============================================================

def normalize_dish_name(text):

    text = str(
        text
    ).lower().strip()

    replacements = {

        "biriyani": "biryani",

        "biryanis": "biryani",

        "briyani": "biryani",

        "briani": "biryani",

        "panneer": "paneer",

        "kabob": "kebab",

        "kababs": "kebab",

        "kebob": "kebab",

        "kebobs": "kebab",

        "chilly": "chili",

        "chillies": "chili"

    }

    words = text.split()

    normalized_words = []

    for word in words:

        word = word.strip(
            ".,!?;:'\"()[]{}"
        )

        if word in replacements:

            word = replacements[word]

        normalized_words.append(
            word
        )

    return " ".join(
        normalized_words
    )


# ============================================================
# DISH SEARCH TOKENS
# ============================================================

def get_dish_tokens(text):

    normalized = normalize_dish_name(
        text
    )

    stop_words = {

        "recipe",
        "dish",
        "food",
        "the",
        "a",
        "an",
        "of",
        "and",
        "with",
        "style",
        "easy",
        "simple",
        "best",
        "homemade",
        "home"

    }

    return [

        word

        for word in normalized.split()

        if word not in stop_words

        and len(word) > 1

    ]


# ============================================================
# FIND BEST RECIPE
# ============================================================

def find_best_recipe(
    dish_name
):

    normalized_query = normalize_dish_name(
        dish_name
    )

    query_tokens = get_dish_tokens(
        normalized_query
    )

    if not query_tokens:

        return None

    connection = get_sqlite_connection()
    cursor = connection.cursor()

    # ========================================================
    # EXACT NAME
    # ========================================================

    cursor.execute(

        """
        SELECT
            recipe_id,
            name,
            category
        FROM recipes
        WHERE LOWER(name) = LOWER(?)
        LIMIT 1
        """,

        (
            normalized_query,
        )

    )

    exact = cursor.fetchone()

    if exact:

        connection.close()

        return exact

    # ========================================================
    # SEARCH TOKENS
    # ========================================================

    conditions = []
    parameters = []

    for token in query_tokens:

        if token == "biryani":

            conditions.append(

                """
                (
                    LOWER(name) LIKE ?
                    OR
                    LOWER(name) LIKE ?
                )
                """

            )

            parameters.append(
                "%biryani%"
            )

            parameters.append(
                "%biriyani%"
            )

        elif token == "kebab":

            conditions.append(

                """
                (
                    LOWER(name) LIKE ?
                    OR
                    LOWER(name) LIKE ?
                )
                """

            )

            parameters.append(
                "%kebab%"
            )

            parameters.append(
                "%kabob%"
            )

        else:

            conditions.append(
                "LOWER(name) LIKE ?"
            )

            parameters.append(
                f"%{token}%"
            )

    query = f"""

        SELECT
            recipe_id,
            name,
            category

        FROM recipes

        WHERE
            {" AND ".join(conditions)}

        ORDER BY
            LENGTH(name) ASC

        LIMIT 100

    """

    cursor.execute(
        query,
        parameters
    )

    candidates = cursor.fetchall()

    connection.close()

    # ========================================================
    # VALIDATE CANDIDATES
    # ========================================================

    best = None
    best_score = -1

    for candidate in candidates:

        recipe_name = normalize_dish_name(
            candidate["name"]
        )

        recipe_tokens = set(
            recipe_name.split()
        )

        all_words_present = True

        for token in query_tokens:

            if token == "biryani":

                if (
                    "biryani" not in recipe_tokens
                    and
                    "biriyani" not in recipe_tokens
                ):

                    all_words_present = False
                    break

            elif token not in recipe_tokens:

                all_words_present = False
                break

        if not all_words_present:

            continue

        # ====================================================
        # SCORING
        # ====================================================

        score = 0

        if recipe_name == normalized_query:

            score += 1000

        if normalized_query in recipe_name:

            score += 300

        score += len(
            query_tokens
        ) * 200

        similarity = SequenceMatcher(

            None,

            normalized_query,

            recipe_name

        ).ratio()

        score += similarity * 100

        extra_words = max(

            0,

            len(recipe_name.split())
            -
            len(query_tokens)

        )

        score -= extra_words * 5

        if score > best_score:

            best_score = score

            best = candidate

    return best


# ============================================================
# WHAT DO YOU WANT TO MAKE?
# ============================================================

@app.route(
    "/make-recipe",
    methods=["POST"]
)
def make_recipe():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message": "No request data received."

            })

        dish_name = data.get(
            "dish",
            ""
        ).strip()

        if not dish_name:

            dish_name = data.get(
                "recipe",
                ""
            ).strip()

        if not dish_name:

            return jsonify({

                "success": False,

                "message": "Please enter a dish name."

            })

        print()
        print("=" * 60)

        print("DISH SEARCH:")
        print(dish_name)

        # ====================================================
        # FIND USING SQLITE
        # ====================================================

        matched_recipe = find_best_recipe(
            dish_name
        )

        if matched_recipe is None:

            print(
                "No matching recipe found."
            )

            return jsonify({

                "success": False,

                "message": (

                    f"No matching recipe found "
                    f"for '{dish_name}'."

                )

            })

        matched_name = matched_recipe[
            "name"
        ]

        print("SQLite match:")
        print(matched_name)

        # ====================================================
        # LOAD COMPLETE RECIPE
        # ====================================================

        recipe_row = load_recipe_from_parquet(
            matched_name
        )

        if recipe_row is None:

            print(
                "Parquet recipe could not be found."
            )

            return jsonify({

                "success": False,

                "message": (

                    "The recipe was found in the "
                    "search index, but the complete "
                    "recipe could not be loaded."

                )

            })

        print("Parquet match:")
        print(recipe_row["Name"])

        # ====================================================
        # BUILD COMPLETE RECIPE
        # ====================================================

        recipe = build_recipe_detail(
            recipe_row
        )

        result = {

            "success": True,

            "recipe": recipe

        }

        print(
            "Recipe successfully loaded."
        )

        print("=" * 60)

        return jsonify(
            make_json_safe(
                result
            )
        )

    except Exception as error:

        print()
        print("=" * 60)

        print(
            "MAKE RECIPE ERROR:"
        )

        print(error)

        print("=" * 60)

        return jsonify({

            "success": False,

            "message": (

                "An error occurred while "
                "finding the recipe."

            ),

            "error": str(error)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "              RecipeSense"
    )

    print(
        " AI Recipe Understanding & Ingredient Substitution System"
    )

    print("=" * 60)

    print()

    print(
        "Server running at:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    app.run(
        debug=True
    )