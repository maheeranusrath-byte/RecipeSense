# ============================================================
# RecipeSense
# AI Recipe Understanding & Ingredient Substitution System
# ============================================================

from flask import Flask, render_template, request, jsonify

import json
import pickle
import sqlite3
import time
import zlib
import math

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

SQLITE_FILE = DATA_DIR / "recipe_index.db"


# ============================================================
# SQLITE CONNECTION
# ============================================================

def get_sqlite_connection():

    if not SQLITE_FILE.exists():

        raise FileNotFoundError(
            f"Recipe database not found: {SQLITE_FILE}"
        )

    connection = sqlite3.connect(
        SQLITE_FILE,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(value):

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(val)
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

    if isinstance(value, bytes):

        try:
            return value.decode("utf-8")
        except Exception:
            return str(value)

    if value is None:

        return None

    if isinstance(value, bool):

        return value

    if isinstance(value, int):

        return value

    if isinstance(value, float):

        if math.isnan(value) or math.isinf(value):
            return None

        return value

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
# CACHED SUBSTITUTION LOOKUP
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
# ANALYZE RECIPE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
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

                "substitutions":
                    substitution_results

            })
        )

    except Exception as error:

        print()
        print("ANALYZE ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to analyze recipe.",

            "error":
                str(error)

        }), 500


# ============================================================
# INGREDIENT SUBSTITUTION
# ============================================================

@app.route(
    "/substitute",
    methods=["POST"]
)
def substitute():

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No ingredient data received."

            })

        ingredient = data.get(
            "ingredient",
            ""
        ).strip()

        if not ingredient:

            return jsonify({

                "success": False,

                "message":
                    "Please enter an ingredient."

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

        print()
        print("SUBSTITUTION ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to find substitutions.",

            "error":
                str(error)

        }), 500


# ============================================================
# WHAT CAN I MAKE?
# ============================================================

@app.route(
    "/find-recipes",
    methods=["POST"]
)
def find_recipe_results():

    start_time = time.perf_counter()

    try:

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No recipe search data received."

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

                "message":
                    "Please enter ingredients."

            })

        user_ingredients = (
            normalize_user_ingredients(
                ingredients_text
            )
        )

        if not user_ingredients:

            return jsonify({

                "success": False,

                "message":
                    "No valid ingredients found."

            })

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

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
            f"Search time:   "
            f"{search_time:.3f} seconds"
        )

        print(
            f"Total backend: "
            f"{total_time:.3f} seconds"
        )

        print("=" * 60)

        response_data = {

            "success": True,

            "ingredients":
                user_ingredients,

            "category":
                category,

            "results":
                enriched_results

        }

        return jsonify(
            make_json_safe(
                response_data
            )
        )

    except Exception as error:

        print()
        print("FIND RECIPES ERROR:")
        print(error)

        return jsonify({

            "success": False,

            "message":
                "Unable to find recipes.",

            "error":
                str(error)

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

    normalized_query = (
        normalize_dish_name(
            dish_name
        )
    )

    query_tokens = (
        get_dish_tokens(
            normalized_query
        )
    )

    if not query_tokens:

        return None

    connection = get_sqlite_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Token search
        # ----------------------------------------------------

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

    # --------------------------------------------------------
    # Score candidates
    # --------------------------------------------------------

    best = None

    best_score = -1

    for candidate in candidates:

        recipe_name = (
            normalize_dish_name(
                candidate["name"]
            )
        )

        recipe_tokens = set(
            recipe_name.split()
        )

        all_words_present = True

        for token in query_tokens:

            if token == "biryani":

                if (
                    "biryani"
                    not in recipe_tokens
                    and
                    "biriyani"
                    not in recipe_tokens
                ):

                    all_words_present = False
                    break

            elif token == "kebab":

                if (
                    "kebab"
                    not in recipe_tokens
                    and
                    "kabob"
                    not in recipe_tokens
                ):

                    all_words_present = False
                    break

            elif token == "sambar":

                if (
                    "sambar"
                    not in recipe_tokens
                    and
                    "sambhar"
                    not in recipe_tokens
                ):

                    all_words_present = False
                    break

            elif token not in recipe_tokens:

                all_words_present = False
                break

        if not all_words_present:

            continue

        score = 0

        if recipe_name == normalized_query:

            score += 1000

        if normalized_query in recipe_name:

            score += 300

        score += (
            len(query_tokens)
            * 200
        )

        similarity = SequenceMatcher(

            None,

            normalized_query,

            recipe_name

        ).ratio()

        score += (
            similarity
            * 100
        )

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

    if best is None:

        return None

    if best_score < 300:

        return None

    return best


# ============================================================
# DECODE SQLITE RECIPE DETAILS
# ============================================================

def decode_recipe_details(
    details
):

    if details is None:

        return None

    try:

        if isinstance(
            details,
            memoryview
        ):

            details = (
                details.tobytes()
            )

        if isinstance(
            details,
            bytes
        ):

            try:

                details = zlib.decompress(
                    details
                )

            except Exception:

                pass

            try:

                return json.loads(
                    details.decode(
                        "utf-8"
                    )
                )

            except Exception:

                try:

                    return pickle.loads(
                        details
                    )

                except Exception:

                    return None

        if isinstance(
            details,
            str
        ):

            try:

                return json.loads(
                    details
                )

            except Exception:

                return None

        if isinstance(
            details,
            dict
        ):

            return details

    except Exception as error:

        print(
            "Recipe detail decode error:",
            error
        )

    return None


# ============================================================
# CONVERT VALUE TO LIST
# ============================================================

def to_list(
    value
):

    if value is None:

        return []

    if isinstance(
        value,
        list
    ):

        return value

    if isinstance(
        value,
        tuple
    ):

        return list(value)

    if isinstance(
        value,
        str
    ):

        text = value.strip()

        if not text:

            return []

        try:

            parsed = json.loads(
                text
            )

            if isinstance(
                parsed,
                list
            ):

                return parsed

        except Exception:

            pass

        return [text]

    return [value]


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(
    value,
    default=""
):

    if value is None:

        return default

    if isinstance(
        value,
        str
    ):

        if value.strip().lower() in {
            "",
            "nan",
            "none",
            "null"
        }:

            return default

    return value


# ============================================================
# BUILD RECIPE DETAIL
# ============================================================

def build_recipe_detail(
    recipe_data
):

    if not recipe_data:

        return None

    # --------------------------------------------------------
    # Already-built recipe object
    # --------------------------------------------------------

    if (
        "name" in recipe_data
        and
        "ingredients" in recipe_data
        and
        "instructions" in recipe_data
    ):

        recipe = dict(
            recipe_data
        )

        ingredients = []

        for item in to_list(
            recipe.get(
                "ingredients",
                []
            )
        ):

            if isinstance(
                item,
                dict
            ):

                item = dict(item)

                normalized = item.get(
                    "normalized_ingredient",
                    item.get(
                        "ingredient",
                        ""
                    )
                )

                if "substitutions" not in item:

                    item["substitutions"] = (
                        get_cached_substitutes(
                            normalized
                        )
                    )

                ingredients.append(
                    item
                )

            else:

                ingredient_text = str(
                    item
                ).strip()

                if not ingredient_text:

                    continue

                parsed = (
                    extract_ingredient_info(
                        ingredient_text
                    )
                )

                normalized = (
                    parsed[0].get(
                        "normalized_ingredient",
                        ingredient_text
                    )
                    if parsed
                    else ingredient_text
                )

                ingredients.append({

                    "ingredient":
                        ingredient_text,

                    "display":
                        ingredient_text,

                    "normalized_ingredient":
                        normalized,

                    "quantity":
                        parsed[0].get(
                            "quantity",
                            ""
                        )
                        if parsed else "",

                    "unit":
                        parsed[0].get(
                            "unit",
                            ""
                        )
                        if parsed else "",

                    "substitutions":
                        get_cached_substitutes(
                            normalized
                        )

                })

        recipe["ingredients"] = ingredients

        recipe["instructions"] = [

            str(item).strip()

            for item in to_list(
                recipe.get(
                    "instructions",
                    []
                )
            )

            if str(item).strip()

        ]

        return recipe

    # --------------------------------------------------------
    # Original Food.com-style data
    # --------------------------------------------------------

    quantities = to_list(
        recipe_data.get(
            "RecipeIngredientQuantities",
            []
        )
    )

    ingredients = to_list(
        recipe_data.get(
            "RecipeIngredientParts",
            []
        )
    )

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

            if quantity.lower() in {
                "nan",
                "none",
                "null"
            }:

                quantity = ""

        combined = (
            f"{quantity} "
            f"{ingredient}"
        ).strip()

        parsed = (
            extract_ingredient_info(
                combined
            )
        )

        normalized = ingredient

        parsed_quantity = quantity

        parsed_unit = ""

        if parsed:

            parsed_item = parsed[0]

            normalized = (
                parsed_item.get(
                    "normalized_ingredient",
                    ingredient
                )
            )

            parsed_quantity = (
                parsed_item.get(
                    "quantity",
                    quantity
                )
            )

            parsed_unit = (
                parsed_item.get(
                    "unit",
                    ""
                )
            )

        substitutions = (
            get_cached_substitutes(
                normalized
            )
        )

        if (
            parsed_quantity
            and
            parsed_unit
        ):

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

            "ingredient":
                ingredient,

            "display":
                display,

            "normalized_ingredient":
                normalized,

            "quantity":
                parsed_quantity,

            "unit":
                parsed_unit,

            "substitutions":
                substitutions

        })

    instructions = [

        str(item).strip()

        for item in to_list(
            recipe_data.get(
                "RecipeInstructions",
                []
            )
        )

        if str(item).strip()

    ]

    return {

        "id": clean_value(
            recipe_data.get(
                "RecipeId",
                recipe_data.get(
                    "id",
                    ""
                )
            )
        ),

        "name": clean_value(
            recipe_data.get(
                "Name",
                recipe_data.get(
                    "name",
                    ""
                )
            )
        ),

        "category": clean_value(
            recipe_data.get(
                "RecipeCategory",
                recipe_data.get(
                    "category",
                    ""
                )
            )
        ),

        "description": clean_value(
            recipe_data.get(
                "Description",
                recipe_data.get(
                    "description",
                    ""
                )
            )
        ),

        "keywords": clean_value(
            recipe_data.get(
                "Keywords",
                recipe_data.get(
                    "keywords",
                    ""
                )
            )
        ),

        "prep_time": clean_value(
            recipe_data.get(
                "PrepTime",
                recipe_data.get(
                    "prep_time",
                    ""
                )
            )
        ),

        "cook_time": clean_value(
            recipe_data.get(
                "CookTime",
                recipe_data.get(
                    "cook_time",
                    ""
                )
            )
        ),

        "total_time": clean_value(
            recipe_data.get(
                "TotalTime",
                recipe_data.get(
                    "total_time",
                    ""
                )
            )
        ),

        "servings": clean_value(
            recipe_data.get(
                "RecipeServings",
                recipe_data.get(
                    "servings",
                    ""
                )
            )
        ),

        "calories": clean_value(
            recipe_data.get(
                "Calories",
                recipe_data.get(
                    "calories",
                    ""
                )
            )
        ),

        "ingredients":
            ingredient_list,

        "instructions":
            instructions

    }


# ============================================================
# LOAD RECIPE FROM SQLITE BY ID
# ============================================================

def load_recipe_from_sqlite_by_id(
    recipe_id
):

    start_time = time.perf_counter()

    try:

        connection = (
            get_sqlite_connection()
        )

        cursor = (
            connection.cursor()
        )

        cursor.execute(
            "PRAGMA table_info(recipes)"
        )

        columns = {

            row["name"]

            for row in cursor.fetchall()

        }

        # ----------------------------------------------------
        # New database with compressed details
        # ----------------------------------------------------

        if "details" in columns:

            cursor.execute(

                """
                SELECT
                    recipe_id,
                    name,
                    category,
                    ingredients,
                    details
                FROM recipes
                WHERE recipe_id = ?
                LIMIT 1
                """,

                (
                    int(float(recipe_id)),
                )

            )

        else:

            cursor.execute(

                """
                SELECT
                    recipe_id,
                    name,
                    category,
                    ingredients
                FROM recipes
                WHERE recipe_id = ?
                LIMIT 1
                """,

                (
                    int(float(recipe_id)),
                )

            )

        row = cursor.fetchone()

        connection.close()

        if row is None:

            return None

        # ----------------------------------------------------
        # Decode complete details
        # ----------------------------------------------------

        if "details" in columns:

            details = (
                decode_recipe_details(
                    row["details"]
                )
            )

            if details:

                recipe = (
                    build_recipe_detail(
                        details
                    )
                )

                if recipe:

                    elapsed = (
                        time.perf_counter()
                        -
                        start_time
                    )

                    print(
                        f"SQLite recipe lookup: "
                        f"{elapsed:.3f} seconds"
                    )

                    return recipe

        # ----------------------------------------------------
        # Fallback for older SQLite database
        # ----------------------------------------------------

        fallback = {

            "RecipeId":
                row["recipe_id"],

            "Name":
                row["name"],

            "RecipeCategory":
                row["category"],

            "RecipeIngredientParts":
                json.loads(
                    row["ingredients"]
                )
                if row["ingredients"]
                else [],

            "RecipeInstructions":
                []

        }

        return build_recipe_detail(
            fallback
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("SQLITE RECIPE LOOKUP ERROR")
        print("=" * 60)
        print(error)
        print("=" * 60)

        return None


# ============================================================
# LOAD RECIPE BY NAME
# ============================================================

def load_recipe_from_sqlite(
    recipe_name
):

    matched_recipe = (
        find_best_recipe(
            recipe_name
        )
    )

    if matched_recipe is None:

        return None

    return load_recipe_from_sqlite_by_id(
        matched_recipe["recipe_id"]
    )


# ============================================================
# RECIPE DETAILS
# ============================================================

@app.route(
    "/recipe-details",
    methods=["GET", "POST"]
)
def recipe_details():

    try:

        # ----------------------------------------------------
        # GET
        # ----------------------------------------------------

        if request.method == "GET":

            recipe_name = request.args.get(
                "name",
                ""
            ).strip()

            if not recipe_name:

                return jsonify({

                    "success": False,

                    "message":
                        "Recipe name is required."

                })

            recipe = (
                load_recipe_from_sqlite(
                    recipe_name
                )
            )

            if recipe is None:

                return jsonify({

                    "success": False,

                    "message":
                        "Recipe not found."

                })

            return jsonify(
                make_json_safe({

                    "success": True,

                    "recipe": recipe,

                    "result": recipe

                })
            )

        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No recipe data received."

            })

        recipe_id = data.get(
            "recipe_id"
        )

        recipe_name = data.get(
            "name",
            ""
        ).strip()

        if recipe_id is not None:

            recipe = (
                load_recipe_from_sqlite_by_id(
                    recipe_id
                )
            )

        elif recipe_name:

            recipe = (
                load_recipe_from_sqlite(
                    recipe_name
                )
            )

        else:

            return jsonify({

                "success": False,

                "message":
                    "Recipe ID or recipe name is required."

            })

        if recipe is None:

            return jsonify({

                "success": False,

                "message":
                    "Recipe not found."

            })

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
        print("RECIPE DETAILS ERROR")
        print(error)
        print("=" * 60)

        return jsonify({

            "success": False,

            "message":
                "Unable to load recipe details.",

            "error":
                str(error)

        }), 500


# ============================================================
# MAKE RECIPE
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

                "message":
                    "No request data received."

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

                "message":
                    "Please enter a dish name."

            })

        print()
        print("=" * 60)
        print("MAKE RECIPE")
        print("Dish:", dish_name)

        # ----------------------------------------------------
        # Find recipe
        # ----------------------------------------------------

        search_start = (
            time.perf_counter()
        )

        matched_recipe = (
            find_best_recipe(
                dish_name
            )
        )

        search_time = (
            time.perf_counter()
            -
            search_start
        )

        if matched_recipe is None:

            return jsonify({

                "success": False,

                "message":
                    f"No matching recipe found "
                    f"for '{dish_name}'."

            })

        recipe_id = (
            matched_recipe[
                "recipe_id"
            ]
        )

        print(
            "SQLite match:",
            matched_recipe["name"]
        )

        print(
            "Recipe ID:",
            recipe_id
        )

        # ----------------------------------------------------
        # Load complete recipe
        # ----------------------------------------------------

        load_start = (
            time.perf_counter()
        )

        recipe = (
            load_recipe_from_sqlite_by_id(
                recipe_id
            )
        )

        load_time = (
            time.perf_counter()
            -
            load_start
        )

        if recipe is None:

            return jsonify({

                "success": False,

                "message":
                    "Recipe was found, "
                    "but complete recipe data "
                    "could not be loaded."

            })

        total_time = (
            time.perf_counter()
            -
            start_time
        )

        print()
        print("-" * 60)

        print(
            f"SQLite search:  "
            f"{search_time:.3f} seconds"
        )

        print(
            f"Recipe loading: "
            f"{load_time:.3f} seconds"
        )

        print(
            f"TOTAL:           "
            f"{total_time:.3f} seconds"
        )

        print(
            "Recipe successfully loaded."
        )

        print("-" * 60)
        print("=" * 60)

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
        print("MAKE RECIPE ERROR")
        print(error)
        print("=" * 60)

        return jsonify({

            "success": False,

            "message":
                "An error occurred while "
                "finding the recipe.",

            "error":
                str(error)

        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    try:

        connection = (
            get_sqlite_connection()
        )

        cursor = (
            connection.cursor()
        )

        cursor.execute(
            "SELECT COUNT(*) FROM recipes"
        )

        recipe_count = (
            cursor.fetchone()[0]
        )

        connection.close()

        return jsonify({

            "status": "ok",

            "database":
                "connected",

            "recipes":
                recipe_count

        })

    except Exception as error:

        return jsonify({

            "status":
                "error",

            "message":
                str(error)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("              RecipeSense")
    print(" AI Recipe Understanding & Ingredient Substitution System")
    print("=" * 60)

    print()

    print(
        "Database:"
    )

    print(
        SQLITE_FILE
    )

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