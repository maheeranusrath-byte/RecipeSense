from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from pathlib import Path

from nlp.recipe_parser import extract_ingredient_info, extract_actions
from nlp.substitution_engine import get_substitutes
from recipe_search import find_recipes, normalize_user_ingredients


app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(value):
    """
    Convert Python sets, NumPy values and arrays into
    JSON-serializable Python objects.
    """

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }


    if isinstance(value, set):

        return sorted(
            make_json_safe(item)
            for item in value
        )


    if isinstance(value, (list, tuple)):

        return [
            make_json_safe(item)
            for item in value
        ]


    if isinstance(value, np.ndarray):

        return [
            make_json_safe(item)
            for item in value.tolist()
        ]


    if isinstance(value, np.integer):

        return int(value)


    if isinstance(value, np.floating):

        return float(value)


    if isinstance(value, np.bool_):

        return bool(value)


    if pd.isna(value):

        return ""


    return value


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# FEATURE PAGES
# ============================================================

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


# ============================================================
# ANALYZE RECIPE API
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    try:

        data = request.get_json()


        if not data:

            return jsonify({
                "success": False,
                "error": "No data received."
            }), 400


        recipe_text = data.get(
            "recipe_text",
            ""
        ).strip()


        if not recipe_text:

            return jsonify({
                "success": False,
                "error": "Please enter a recipe."
            }), 400


        ingredients = extract_ingredient_info(
            recipe_text
        )

        actions = extract_actions(
            recipe_text
        )


        ingredient_results = []


        for item in ingredients:

            ingredient_results.append({

                "ingredient":
                    item["ingredient"],

                "normalized_ingredient":
                    item["normalized_ingredient"],

                "quantity":
                    item["quantity"],

                "unit":
                    item["unit"],

                "original":
                    item["ingredient"]

            })


        substitutions = []

        seen = set()


        for item in ingredients:

            normalized = item[
                "normalized_ingredient"
            ]


            if not normalized:
                continue


            if normalized in seen:
                continue


            seen.add(
                normalized
            )


            matches = get_substitutes(
                normalized
            )


            if matches:

                substitutions.append({

                    "ingredient":
                        normalized,

                    "quantity":
                        item["quantity"],

                    "unit":
                        item["unit"],

                    "substitutes":
                        matches

                })


        result = {

            "ingredients":
                ingredient_results,

            "actions":
                actions,

            "substitutions":
                substitutions

        }


        return jsonify({

            "success":
                True,

            "result":
                make_json_safe(result)

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# SINGLE INGREDIENT SUBSTITUTION API
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

                "success":
                    False,

                "error":
                    "No data received."

            }), 400


        ingredient_text = data.get(
            "ingredient",
            ""
        ).strip()


        if not ingredient_text:

            return jsonify({

                "success":
                    False,

                "error":
                    "Please enter an ingredient."

            }), 400


        extracted = extract_ingredient_info(
            ingredient_text
        )


        if not extracted:

            return jsonify({

                "success":
                    False,

                "error":
                    "Could not understand the ingredient."

            }), 400


        item = extracted[0]


        normalized = item[
            "normalized_ingredient"
        ]


        substitutes = get_substitutes(
            normalized
        )


        result = {

            "original":
                ingredient_text,

            "ingredient":
                normalized,

            "quantity":
                item["quantity"],

            "unit":
                item["unit"],

            "substitutes":
                substitutes

        }


        return jsonify({

            "success":
                True,

            "result":
                make_json_safe(result)

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# FIND RECIPES API
# ============================================================

@app.route(
    "/find-recipes",
    methods=["POST"]
)
def find_recipes_api():

    try:

        data = request.get_json()


        if not data:

            return jsonify({

                "success":
                    False,

                "error":
                    "No data received."

            }), 400


        ingredient_text = data.get(
            "ingredients",
            ""
        ).strip()


        if not ingredient_text:

            return jsonify({

                "success":
                    False,

                "error":
                    "Please enter at least one ingredient."

            }), 400


        user_ingredients = (
            normalize_user_ingredients(
                ingredient_text
            )
        )


        if not user_ingredients:

            return jsonify({

                "success":
                    False,

                "error":
                    "No valid ingredients found."

            }), 400


        results = find_recipes(
            user_ingredients,
            limit=10
        )


        # IMPORTANT:
        # Recipe matcher may return sets.
        # Convert everything into JSON-safe values.

        results = make_json_safe(
            results
        )


        safe_ingredients = make_json_safe(
            user_ingredients
        )


        return jsonify({

            "success":
                True,

            "ingredients":
                sorted(safe_ingredients),

            "results":
                results

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500


# ============================================================
# RECIPE DETAILS API
# ============================================================

@app.route(
    "/recipe-details"
)
def recipe_details():

    try:

        recipe_name = request.args.get(
            "name",
            ""
        ).strip()


        if not recipe_name:

            return jsonify({

                "success":
                    False,

                "error":
                    "Recipe name is required."

            }), 400


        columns = [

            "RecipeId",
            "Name",
            "Description",
            "RecipeCategory",
            "CookTime",
            "PrepTime",
            "TotalTime",
            "RecipeIngredientQuantities",
            "RecipeIngredientParts",
            "RecipeInstructions",
            "RecipeServings",
            "Calories"

        ]


        # ----------------------------------------------------
        # First attempt: PyArrow filtering
        # ----------------------------------------------------

        try:

            df = pd.read_parquet(

                DATA_FILE,

                columns=columns,

                filters=[
                    [
                        (
                            "Name",
                            "==",
                            recipe_name
                        )
                    ]
                ]

            )

        except Exception:

            df = pd.DataFrame()


        # ----------------------------------------------------
        # Fallback: case-insensitive search
        # ----------------------------------------------------

        if df.empty:

            names_df = pd.read_parquet(

                DATA_FILE,

                columns=["Name"]

            )


            matches = names_df[

                names_df["Name"]
                .astype(str)
                .str.lower()
                ==
                recipe_name.lower()

            ]


            if matches.empty:

                return jsonify({

                    "success":
                        False,

                    "error":
                        "Recipe not found."

                }), 404


            actual_name = matches.iloc[0][
                "Name"
            ]


            df = pd.read_parquet(

                DATA_FILE,

                columns=columns,

                filters=[
                    [
                        (
                            "Name",
                            "==",
                            actual_name
                        )
                    ]
                ]

            )


        if df.empty:

            return jsonify({

                "success":
                    False,

                "error":
                    "Recipe not found."

            }), 404


        row = df.iloc[0]


        # ----------------------------------------------------
        # Safe array conversion
        # ----------------------------------------------------

        def to_list(value):

            if value is None:
                return []


            if isinstance(
                value,
                np.ndarray
            ):

                return value.tolist()


            if isinstance(
                value,
                (list, tuple)
            ):

                return list(value)


            try:

                if pd.isna(value):
                    return []

            except Exception:
                pass


            return [value]


        quantities = to_list(
            row.get(
                "RecipeIngredientQuantities"
            )
        )


        parts = to_list(
            row.get(
                "RecipeIngredientParts"
            )
        )


        instructions = to_list(
            row.get(
                "RecipeInstructions"
            )
        )


        # ----------------------------------------------------
        # Ingredients
        # ----------------------------------------------------

        ingredient_list = []


        max_length = max(
            len(quantities),
            len(parts)
        )


        for i in range(
            max_length
        ):

            quantity = (

                str(
                    quantities[i]
                ).strip()

                if i < len(quantities)

                else ""

            )


            ingredient = (

                str(
                    parts[i]
                ).strip()

                if i < len(parts)

                else ""

            )


            if ingredient.lower() == "nan":

                ingredient = ""


            if quantity.lower() == "nan":

                quantity = ""


            if ingredient:

                if quantity:

                    ingredient_list.append(

                        f"{quantity} {ingredient}"

                    )

                else:

                    ingredient_list.append(
                        ingredient
                    )


        # ----------------------------------------------------
        # Instructions
        # ----------------------------------------------------

        instruction_list = []


        for instruction in instructions:

            text = str(
                instruction
            ).strip()


            if (

                text

                and

                text.lower()
                != "nan"

            ):

                instruction_list.append(
                    text
                )


        # ----------------------------------------------------
        # Safe values
        # ----------------------------------------------------

        def safe_value(value):

            if value is None:
                return ""


            try:

                if pd.isna(value):
                    return ""

            except Exception:
                pass


            return str(value)


        result = {

            "name":
                safe_value(
                    row.get("Name")
                ),

            "description":
                safe_value(
                    row.get("Description")
                ),

            "category":
                safe_value(
                    row.get("RecipeCategory")
                ),

            "prep_time":
                safe_value(
                    row.get("PrepTime")
                ),

            "cook_time":
                safe_value(
                    row.get("CookTime")
                ),

            "total_time":
                safe_value(
                    row.get("TotalTime")
                ),

            "servings":
                safe_value(
                    row.get("RecipeServings")
                ),

            "calories":
                safe_value(
                    row.get("Calories")
                ),

            "ingredients":
                ingredient_list,

            "instructions":
                instruction_list

        }


        return jsonify({

            "success":
                True,

            "result":
                make_json_safe(result)

        })


    except Exception as e:

        return jsonify({

            "success":
                False,

            "error":
                str(e)

        }), 500
@app.route("/make-recipe-page")
def make_recipe_page():
    return render_template("make_recipe.html")
@app.route("/make-recipe", methods=["POST"])
def make_recipe():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data received."
            }), 400

        dish = data.get("dish", "").strip()

        if not dish:
            return jsonify({
                "success": False,
                "error": "Please enter a dish name."
            }), 400

        columns = [
            "Name",
            "Description",
            "RecipeCategory",
            "PrepTime",
            "CookTime",
            "TotalTime",
            "RecipeIngredientQuantities",
            "RecipeIngredientParts",
            "RecipeInstructions",
            "RecipeServings",
            "Calories"
        ]

        df = pd.read_parquet(
            DATA_FILE,
            columns=columns
        )

        # ----------------------------------------------------
        # Search recipe name
        # ----------------------------------------------------

        dish_lower = dish.lower()

        exact_matches = df[
            df["Name"]
            .astype(str)
            .str.lower()
            == dish_lower
        ]

        if not exact_matches.empty:

            row = exact_matches.iloc[0]

        else:

            partial_matches = df[
                df["Name"]
                .astype(str)
                .str.lower()
                .str.contains(
                    dish_lower,
                    regex=False,
                    na=False
                )
            ]

            if partial_matches.empty:

                return jsonify({
                    "success": False,
                    "error":
                        f"No recipe found for '{dish}'."
                }), 404

            row = partial_matches.iloc[0]

        # ----------------------------------------------------
        # Convert arrays safely
        # ----------------------------------------------------

        def to_list(value):

            if value is None:
                return []

            if isinstance(
                value,
                np.ndarray
            ):
                return value.tolist()

            if isinstance(
                value,
                (list, tuple)
            ):
                return list(value)

            try:

                if pd.isna(value):
                    return []

            except Exception:
                pass

            return [value]

        quantities = to_list(
            row["RecipeIngredientQuantities"]
        )

        parts = to_list(
            row["RecipeIngredientParts"]
        )

        instructions = to_list(
            row["RecipeInstructions"]
        )

        # ----------------------------------------------------
        # Build ingredients
        # ----------------------------------------------------

        ingredients = []

        max_length = max(
            len(quantities),
            len(parts)
        )

        for i in range(max_length):

            quantity = ""

            ingredient_name = ""

            if i < len(quantities):

                quantity = str(
                    quantities[i]
                ).strip()

            if i < len(parts):

                ingredient_name = str(
                    parts[i]
                ).strip()

            if (
                quantity.lower()
                == "nan"
            ):
                quantity = ""

            if (
                ingredient_name.lower()
                == "nan"
            ):
                ingredient_name = ""

            if not ingredient_name:
                continue

            # ------------------------------------------------
            # Parse ingredient to obtain normalized name
            # ------------------------------------------------

            parsed = extract_ingredient_info(
                f"{quantity} {ingredient_name}".strip()
            )

            normalized = ingredient_name.lower().strip()

            if parsed:

                normalized = parsed[0][
                    "normalized_ingredient"
                ]

            substitutions = get_substitutes(
                normalized
            )

            if quantity:

                display = (
                    f"{quantity} "
                    f"{ingredient_name}"
                )

            else:

                display = ingredient_name

            ingredients.append({

                "display":
                    display,

                "ingredient":
                    normalized,

                "quantity":
                    quantity,

                "substitutions":
                    substitutions

            })

        # ----------------------------------------------------
        # Instructions
        # ----------------------------------------------------

        clean_instructions = []

        for instruction in instructions:

            text = str(
                instruction
            ).strip()

            if (
                text
                and text.lower() != "nan"
            ):

                clean_instructions.append(
                    text
                )

        # ----------------------------------------------------
        # Safe values
        # ----------------------------------------------------

        def safe_value(value):

            if value is None:
                return ""

            try:

                if pd.isna(value):
                    return ""

            except Exception:
                pass

            return str(value)

        recipe = {

            "name":
                safe_value(
                    row["Name"]
                ),

            "description":
                safe_value(
                    row["Description"]
                ),

            "category":
                safe_value(
                    row["RecipeCategory"]
                ),

            "prep_time":
                safe_value(
                    row["PrepTime"]
                ),

            "cook_time":
                safe_value(
                    row["CookTime"]
                ),

            "total_time":
                safe_value(
                    row["TotalTime"]
                ),

            "servings":
                safe_value(
                    row["RecipeServings"]
                ),

            "calories":
                safe_value(
                    row["Calories"]
                ),

            "ingredients":
                ingredients,

            "instructions":
                clean_instructions

        }

        return jsonify({

            "success": True,

            "recipe":
                make_json_safe(recipe)

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

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
        "       AI Recipe Understanding System"
    )

    print("=" * 60)

    print(
        "\nStarting Flask server..."
    )

    print(
        "Open: http://127.0.0.1:5000"
    )

    app.run(
        debug=True
    )