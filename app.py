# ============================================================
# RecipeSense
# AI Recipe Understanding & Ingredient Substitution System
# ============================================================

from flask import Flask, render_template, request, jsonify

import pandas as pd
import numpy as np
import sqlite3
import time
import pyarrow as pa
import pyarrow.dataset as ds

from pathlib import Path
from difflib import SequenceMatcher
from functools import lru_cache

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
# PARQUET DATASET CACHE
# ============================================================
#
# IMPORTANT:
#
# We DO NOT load the entire Parquet file.
#
# PyArrow Dataset is opened once and reused.
# Individual recipes are retrieved using RecipeId filtering.
#
# ============================================================

_RECIPE_DATASET = None


def get_recipe_dataset():

    global _RECIPE_DATASET

    if _RECIPE_DATASET is None:

        print()
        print("=" * 60)
        print("INITIALIZING RECIPE PARQUET DATASET")
        print("=" * 60)

        dataset_start = time.perf_counter()

        if not DATA_FILE.exists():

            raise FileNotFoundError(
                f"Recipe dataset not found: {DATA_FILE}"
            )

        _RECIPE_DATASET = ds.dataset(
            str(DATA_FILE),
            format="parquet"
        )

        dataset_time = (
            time.perf_counter()
            - dataset_start
        )

        print(
            f"Dataset initialized in {dataset_time:.3f} seconds"
        )

        print(
            "Parquet schema loaded successfully."
        )

        print("=" * 60)

    return _RECIPE_DATASET


# ============================================================
# SQLITE CONNECTION
# ============================================================

def get_sqlite_connection():

    connection = sqlite3.connect(
        SQLITE_FILE,
        timeout=10
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

            substitutes = get_cached_substitutes(
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
# CACHED SUBSTITUTION LOOKUP
# ============================================================
#
# The substitution engine can be called many times while
# building a recipe.
#
# Cache repeated ingredient requests.
#
# ============================================================

@lru_cache(maxsize=2048)
def get_cached_substitutes(
    ingredient
):

    try:

        return get_substitutes(
            ingredient
        )

    except Exception as error:

        print(
            "Substitution lookup error:",
            error
        )

        return []


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

        result = get_cached_substitutes(
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
# FIND RECIPES
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
        # PREPARE RESULTS
        # ====================================================

        enriched_results = []

        for result in results:

            enriched_results.append(
                dict(result)
            )

        total_time = (
            time.perf_counter()
            -
            start_time
        )

        # ====================================================
        # PERFORMANCE INFORMATION
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
            f"Search time:   {search_time:.3f} seconds"
        )

        print(
            f"Total backend: {total_time:.3f} seconds"
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
# CONVERT RECIPE ID FOR ARROW
# ============================================================

def normalize_recipe_id(
    recipe_id,
    arrow_type
):

    try:

        numeric_id = int(
            float(recipe_id)
        )

    except (TypeError, ValueError):

        return None

    # --------------------------------------------------------
    # Integer RecipeId
    # --------------------------------------------------------

    if pa.types.is_integer(
        arrow_type
    ):

        return numeric_id

    # --------------------------------------------------------
    # Floating RecipeId
    # --------------------------------------------------------

    if pa.types.is_floating(
        arrow_type
    ):

        return float(
            numeric_id
        )

    # --------------------------------------------------------
    # String RecipeId
    # --------------------------------------------------------

    return str(
        numeric_id
    )


# ============================================================
# LOAD RECIPE FROM PARQUET BY EXACT RECIPE ID
# ============================================================
#
# THIS IS THE IMPORTANT FIX.
#
# We NEVER do:
#
#     pd.read_parquet(DATA_FILE)
#
# for a recipe request.
#
# Instead:
#
#     1. Open cached PyArrow Dataset.
#     2. Detect RecipeId datatype.
#     3. Apply exact RecipeId filter.
#     4. Read only required columns.
#     5. Convert only the matching row to pandas.
#
# There is NO full-Parquet fallback.
#
# ============================================================

def load_recipe_from_parquet_by_id(
    recipe_id
):

    start_time = time.perf_counter()

    try:

        dataset = get_recipe_dataset()

        columns = get_recipe_columns()

        # ----------------------------------------------------
        # Check RecipeId datatype
        # ----------------------------------------------------

        recipe_id_field = dataset.schema.field(
            "RecipeId"
        )

        arrow_recipe_id = normalize_recipe_id(
            recipe_id,
            recipe_id_field.type
        )

        if arrow_recipe_id is None:

            print(
                "Invalid RecipeId:",
                recipe_id
            )

            return None

        # ----------------------------------------------------
        # Exact filter
        # ----------------------------------------------------

        filter_expression = (
            ds.field("RecipeId")
            ==
            arrow_recipe_id
        )

        # ----------------------------------------------------
        # Read only matching row
        # ----------------------------------------------------

        table = dataset.to_table(

            columns=columns,

            filter=filter_expression,

            use_threads=True

        )

        # ----------------------------------------------------
        # No matching recipe
        # ----------------------------------------------------

        if table.num_rows == 0:

            elapsed = (
                time.perf_counter()
                -
                start_time
            )

            print(
                f"RecipeId {recipe_id} not found "
                f"in Parquet ({elapsed:.3f}s)"
            )

            return None

        # ----------------------------------------------------
        # Convert only matching row
        # ----------------------------------------------------

        recipe_df = table.to_pandas()

        if recipe_df.empty:

            return None

        recipe_row = recipe_df.iloc[0]

        # ----------------------------------------------------
        # Extra safety verification
        # ----------------------------------------------------

        actual_id = recipe_row[
            "RecipeId"
        ]

        try:

            actual_id = int(
                float(actual_id)
            )

            expected_id = int(
                float(recipe_id)
            )

        except (TypeError, ValueError):

            print(
                "RecipeId conversion failed."
            )

            return None

        if actual_id != expected_id:

            print()
            print("RECIPE ID VERIFICATION FAILED")
            print(
                "Expected:",
                expected_id
            )
            print(
                "Actual:",
                actual_id
            )

            return None

        elapsed = (
            time.perf_counter()
            -
            start_time
        )

        print(
            f"Exact Parquet lookup: "
            f"{elapsed:.3f} seconds"
        )

        return recipe_row

    except Exception as error:

        print()
        print("=" * 60)
        print("PARQUET LOOKUP ERROR")
        print("=" * 60)
        print(error)
        print("=" * 60)

        return None


# ============================================================
# LOAD RECIPE FROM PARQUET BY NAME
# ============================================================
#
# Name is ONLY used to locate the RecipeId through SQLite.
#
# The actual recipe is ALWAYS loaded by RecipeId.
#
# ============================================================

def load_recipe_from_parquet(
    recipe_name
):

    matched_recipe = find_best_recipe(
        recipe_name
    )

    if matched_recipe is None:

        return None

    return load_recipe_from_parquet_by_id(
        matched_recipe["recipe_id"]
    )


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

    # --------------------------------------------------------
    # Convert quantities
    # --------------------------------------------------------

    try:

        quantities = list(
            quantities
        )

    except Exception:

        quantities = []

    # --------------------------------------------------------
    # Convert ingredients
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # Parse ingredient
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Cached substitutions
        # ----------------------------------------------------

        substitutions = get_cached_substitutes(
            normalized
        )

        # ----------------------------------------------------
        # Display quantity
        # ----------------------------------------------------

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

    # ========================================================
    # Instructions
    # ========================================================

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

    # ========================================================
    # Clean basic values
    # ========================================================

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

    # ========================================================
    # Recipe object
    # ========================================================

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

            matched_recipe = find_best_recipe(
                recipe_name
            )

            if matched_recipe is None:

                return jsonify({

                    "success": False,

                    "message": "Recipe not found."

                })

            recipe_row = (
                load_recipe_from_parquet_by_id(
                    matched_recipe["recipe_id"]
                )
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

            matched_recipe = find_best_recipe(
                recipe_name
            )

            if matched_recipe is None:

                return jsonify({

                    "success": False,

                    "message": "Recipe not found."

                })

            recipe_id = matched_recipe[
                "recipe_id"
            ]

        # ====================================================
        # RECIPE ID REQUIRED
        # ====================================================

        if recipe_id is None:

            return jsonify({

                "success": False,

                "message": (
                    "Recipe ID or recipe name "
                    "is required."
                )

            })

        # ====================================================
        # LOAD EXACT RECIPE
        # ====================================================

        recipe_row = load_recipe_from_parquet_by_id(
            recipe_id
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

def normalize_dish_name(
    text
):

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

        "sambhar": "sambar",

        "sambars": "sambar",

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

def get_dish_tokens(
    text
):

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

    try:

        cursor = connection.cursor()

        # ====================================================
        # EXACT NAME MATCH
        # ====================================================

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

            return exact

        # ====================================================
        # TOKEN SEARCH
        # ====================================================

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

            elif token == "sambar":

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
                    "%sambar%"
                )

                parameters.append(
                    "%sambhar%"
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

    finally:

        connection.close()

    # ========================================================
    # VALIDATE + SCORE
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

        # ----------------------------------------------------
        # Every requested token must exist
        # ----------------------------------------------------

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

            elif token == "kebab":

                if (
                    "kebab" not in recipe_tokens
                    and
                    "kabob" not in recipe_tokens
                ):

                    all_words_present = False

                    break

            elif token == "sambar":

                if (
                    "sambar" not in recipe_tokens
                    and
                    "sambhar" not in recipe_tokens
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

        # ----------------------------------------------------
        # Exact name
        # ----------------------------------------------------

        if recipe_name == normalized_query:

            score += 1000

        # ----------------------------------------------------
        # Query appears inside recipe name
        # ----------------------------------------------------

        if normalized_query in recipe_name:

            score += 300

        # ----------------------------------------------------
        # Matching tokens
        # ----------------------------------------------------

        score += (
            len(query_tokens)
            * 200
        )

        # ----------------------------------------------------
        # Similarity
        # ----------------------------------------------------

        similarity = SequenceMatcher(

            None,

            normalized_query,

            recipe_name

        ).ratio()

        score += (
            similarity
            * 100
        )

        # ----------------------------------------------------
        # Penalize extra words
        # ----------------------------------------------------

        extra_words = max(

            0,

            len(recipe_name.split())
            -
            len(query_tokens)

        )

        score -= (
            extra_words
            * 5
        )

        if score > best_score:

            best_score = score

            best = candidate

    # ========================================================
    # NO MATCH
    # ========================================================

    if best is None:

        return None

    # ========================================================
    # WEAK MATCH PROTECTION
    # ========================================================

    if best_score < 300:

        return None

    return best


# ============================================================
# WHAT DO YOU WANT TO MAKE?
# ============================================================

@app.route(
    "/make-recipe",
    methods=["POST"]
)
def make_recipe():

    start_time = time.perf_counter()

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
        # FIND RECIPE IN SQLITE
        # ====================================================

        sqlite_start = time.perf_counter()

        matched_recipe = find_best_recipe(
            dish_name
        )

        sqlite_time = (
            time.perf_counter()
            -
            sqlite_start
        )

        if matched_recipe is None:

            print(
                "No suitable recipe found."
            )

            print(
                f"SQLite search: "
                f"{sqlite_time:.3f} seconds"
            )

            print("=" * 60)

            return jsonify({

                "success": False,

                "message": (

                    f"No matching recipe found "
                    f"for '{dish_name}'."

                )

            })

        recipe_id = matched_recipe[
            "recipe_id"
        ]

        matched_name = matched_recipe[
            "name"
        ]

        print()
        print("SQLite match:")
        print(matched_name)

        print(
            "Recipe ID:",
            recipe_id
        )

        # ====================================================
        # LOAD EXACT RECIPE BY ID
        # ====================================================

        parquet_start = time.perf_counter()

        recipe_row = load_recipe_from_parquet_by_id(
            recipe_id
        )

        parquet_time = (
            time.perf_counter()
            -
            parquet_start
        )

        if recipe_row is None:

            print(
                "Exact RecipeId was not found in Parquet."
            )

            print(
                f"SQLite search: "
                f"{sqlite_time:.3f} seconds"
            )

            print(
                f"Parquet load: "
                f"{parquet_time:.3f} seconds"
            )

            print("=" * 60)

            return jsonify({

                "success": False,

                "message": (

                    "The recipe was found in the "
                    "search index, but its complete "
                    "recipe data could not be loaded."

                )

            })

        print()
        print("Parquet match:")
        print(
            recipe_row["Name"]
        )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        parquet_recipe_id = recipe_row[
            "RecipeId"
        ]

        try:

            parquet_recipe_id = int(
                float(
                    parquet_recipe_id
                )
            )

            expected_recipe_id = int(
                float(
                    recipe_id
                )
            )

        except (
            TypeError,
            ValueError
        ):

            print(
                "Recipe ID conversion failed."
            )

            return jsonify({

                "success": False,

                "message": (
                    "Recipe verification failed."
                )

            }), 500

        if parquet_recipe_id != expected_recipe_id:

            print(
                "RECIPE ID MISMATCH!"
            )

            print(
                "SQLite ID:",
                expected_recipe_id
            )

            print(
                "Parquet ID:",
                parquet_recipe_id
            )

            print("=" * 60)

            return jsonify({

                "success": False,

                "message": (

                    "Recipe verification failed. "
                    "The recipe data did not match "
                    "the search result."

                )

            }), 500

        # ====================================================
        # BUILD RECIPE
        # ====================================================

        build_start = time.perf_counter()

        recipe = build_recipe_detail(
            recipe_row
        )

        build_time = (
            time.perf_counter()
            -
            build_start
        )

        total_time = (
            time.perf_counter()
            -
            start_time
        )

        # ====================================================
        # PERFORMANCE
        # ====================================================

        print()
        print("-" * 60)

        print(
            f"SQLite search:   "
            f"{sqlite_time:.3f} seconds"
        )

        print(
            f"Parquet lookup:  "
            f"{parquet_time:.3f} seconds"
        )

        print(
            f"Recipe building: "
            f"{build_time:.3f} seconds"
        )

        print(
            f"TOTAL:           "
            f"{total_time:.3f} seconds"
        )

        print("-" * 60)

        print(
            "Recipe successfully loaded."
        )

        print("=" * 60)

        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify(
            make_json_safe({

                "success": True,

                "recipe": recipe

            })
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