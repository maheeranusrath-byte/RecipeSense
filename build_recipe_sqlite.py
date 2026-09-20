# ============================================================
# RecipeSense
# Build SQLite Recipe Database
#
# SQLite contains:
# - Recipe search index
# - Ingredient index
# - Compressed complete recipe details
#
# This version uses the REAL RecipeId from
# recipes_cleaned.parquet.
# ============================================================

import json
import re
import sqlite3
import zlib

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_DIR = PROJECT_DIR / "data"

PARQUET_FILE = (
    DATA_DIR / "recipes_cleaned.parquet"
)

SQLITE_FILE = (
    DATA_DIR / "recipe_index.db"
)


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

    ingredient = ingredient.replace(
        "&",
        " and "
    )

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

    ingredient = " ".join(words)

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


def normalize_with_alias(
    ingredient
):

    ingredient = normalize_ingredient(
        ingredient
    )

    if not ingredient:
        return ""

    return INGREDIENT_ALIASES.get(
        ingredient,
        ingredient
    )


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def json_safe(value):

    if isinstance(
        value,
        dict
    ):

        return {
            str(key): json_safe(val)
            for key, val in value.items()
        }

    if isinstance(
        value,
        (list, tuple)
    ):

        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        np.ndarray
    ):

        return [
            json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(
        value,
        np.integer
    ):

        return int(value)

    if isinstance(
        value,
        np.floating
    ):

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


def clean_value(
    value
):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except Exception:
        pass

    return json_safe(value)


# ============================================================
# CONVERT LIST-LIKE DATA
# ============================================================

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

    # Some datasets may contain
    # string representations of lists.

    if isinstance(
        value,
        str
    ):

        text = value.strip()

        if not text:
            return []

        try:

            parsed = json.loads(text)

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
# CREATE DATABASE
# ============================================================

def create_database():

    DATA_DIR.mkdir(
        exist_ok=True
    )

    if not PARQUET_FILE.exists():

        raise FileNotFoundError(
            f"Parquet file not found:\n"
            f"{PARQUET_FILE}"
        )

    if SQLITE_FILE.exists():

        print()
        print(
            "Removing old SQLite database..."
        )

        SQLITE_FILE.unlink()

    print()
    print("=" * 70)
    print(
        "       RecipeSense SQLite Database Builder"
    )
    print("=" * 70)

    print()
    print(
        "Source:"
    )
    print(
        PARQUET_FILE
    )

    print()
    print(
        "Destination:"
    )
    print(
        SQLITE_FILE
    )

    print()
    print(
        "Reading recipe dataset..."
    )

    columns = [

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

    df = pd.read_parquet(
        PARQUET_FILE,
        columns=columns
    )

    print(
        "Rows loaded:",
        len(df)
    )

    print()
    print(
        "Converting RecipeId..."
    )

    df["RecipeId"] = pd.to_numeric(
        df["RecipeId"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["RecipeId"]
    )

    df["RecipeId"] = (
        df["RecipeId"]
        .astype("int64")
    )

    # Remove duplicate RecipeIds.
    df = df.drop_duplicates(
        subset=["RecipeId"],
        keep="first"
    )

    print(
        "Valid unique recipes:",
        len(df)
    )

    # ========================================================
    # SQLITE
    # ========================================================

    print()
    print(
        "Creating SQLite database..."
    )

    connection = sqlite3.connect(
        SQLITE_FILE
    )

    cursor = connection.cursor()

    # Performance settings during build.

    cursor.execute(
        "PRAGMA journal_mode=OFF"
    )

    cursor.execute(
        "PRAGMA synchronous=OFF"
    )

    cursor.execute(
        "PRAGMA temp_store=MEMORY"
    )

    cursor.execute(
        "PRAGMA cache_size=-100000"
    )

    # ========================================================
    # TABLES
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE recipes (

            recipe_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL,

            category TEXT,

            ingredients TEXT NOT NULL,

            details BLOB
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE ingredient_index (

            ingredient TEXT NOT NULL,

            recipe_id INTEGER NOT NULL
        )
        """
    )

    connection.commit()

    # ========================================================
    # INSERT RECIPES
    # ========================================================

    print()
    print(
        "Building recipe records..."
    )

    recipe_rows = []

    ingredient_rows = []

    total = len(df)

    for index, row in df.iterrows():

        recipe_id = int(
            row["RecipeId"]
        )

        name = clean_value(
            row["Name"]
        )

        category = clean_value(
            row["RecipeCategory"]
        )

        ingredients = to_list(
            row[
                "RecipeIngredientParts"
            ]
        )

        quantities = to_list(
            row[
                "RecipeIngredientQuantities"
            ]
        )

        instructions = to_list(
            row[
                "RecipeInstructions"
            ]
        )

        # ----------------------------------------------------
        # Normalize ingredients for search index
        # ----------------------------------------------------

        normalized_ingredients = []

        seen_ingredients = set()

        for ingredient in ingredients:

            normalized = (
                normalize_with_alias(
                    ingredient
                )
            )

            if (
                normalized
                and normalized
                not in seen_ingredients
            ):

                normalized_ingredients.append(
                    normalized
                )

                seen_ingredients.add(
                    normalized
                )

                ingredient_rows.append(
                    (
                        normalized,
                        recipe_id
                    )
                )

        # ----------------------------------------------------
        # Complete recipe data
        # ----------------------------------------------------

        details = {

            "RecipeId": recipe_id,

            "Name": name,

            "Description": clean_value(
                row["Description"]
            ),

            "RecipeCategory": category,

            "Keywords": clean_value(
                row["Keywords"]
            ),

            "CookTime": clean_value(
                row["CookTime"]
            ),

            "PrepTime": clean_value(
                row["PrepTime"]
            ),

            "TotalTime": clean_value(
                row["TotalTime"]
            ),

            "RecipeIngredientQuantities":
                quantities,

            "RecipeIngredientParts":
                ingredients,

            "RecipeInstructions":
                instructions,

            "RecipeServings": clean_value(
                row["RecipeServings"]
            ),

            "Calories": clean_value(
                row["Calories"]
            )
        }

        details_json = json.dumps(
            json_safe(details),
            ensure_ascii=False,
            separators=(
                ",",
                ":"
            )
        )

        # Compress recipe details.
        compressed_details = (
            zlib.compress(
                details_json.encode(
                    "utf-8"
                ),
                level=6
            )
        )

        recipe_rows.append(
            (
                recipe_id,
                str(name),
                str(category),
                json.dumps(
                    normalized_ingredients,
                    ensure_ascii=False
                ),
                compressed_details
            )
        )

        # ----------------------------------------------------
        # Batch insertion
        # ----------------------------------------------------

        if len(recipe_rows) >= 2000:

            cursor.executemany(
                """
                INSERT INTO recipes
                (
                    recipe_id,
                    name,
                    category,
                    ingredients,
                    details
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                recipe_rows
            )

            connection.commit()

            recipe_rows.clear()

        if (
            index % 25000 == 0
            or index == total - 1
        ):

            percent = (
                (index + 1)
                / total
                * 100
            )

            print(
                f"\rProgress: "
                f"{index + 1:,}/{total:,} "
                f"({percent:.1f}%)",
                end=""
            )

    # Remaining recipes.

    if recipe_rows:

        cursor.executemany(
            """
            INSERT INTO recipes
            (
                recipe_id,
                name,
                category,
                ingredients,
                details
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            recipe_rows
        )

        connection.commit()

    print()

    # ========================================================
    # INSERT INGREDIENT INDEX
    # ========================================================

    print()
    print(
        "Building ingredient index..."
    )

    cursor.executemany(
        """
        INSERT INTO ingredient_index
        (
            ingredient,
            recipe_id
        )
        VALUES (?, ?)
        """,
        ingredient_rows
    )

    connection.commit()

    print(
        "Ingredient index rows:",
        len(ingredient_rows)
    )

    # ========================================================
    # INDEXES
    # ========================================================

    print()
    print(
        "Creating database indexes..."
    )

    cursor.execute(
        """
        CREATE INDEX idx_ingredient
        ON ingredient_index(ingredient)
        """
    )

    cursor.execute(
        """
        CREATE INDEX idx_recipe_id
        ON ingredient_index(recipe_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX idx_recipe_name
        ON recipes(name)
        """
    )

    cursor.execute(
        """
        CREATE INDEX idx_recipe_category
        ON recipes(category)
        """
    )

    connection.commit()

    # ========================================================
    # VERIFY SAMBAR
    # ========================================================

    print()
    print("=" * 70)
    print(
        "Sambar verification:"
    )
    print("-" * 70)

    cursor.execute(
        """
        SELECT recipe_id, name
        FROM recipes
        WHERE LOWER(name) LIKE '%sambar%'
        LIMIT 10
        """
    )

    sambar_rows = cursor.fetchall()

    for recipe_id, name in sambar_rows:

        print(
            f"{recipe_id} -> {name}"
        )

    print("-" * 70)

    # Exact Sambar.

    cursor.execute(
        """
        SELECT recipe_id, name
        FROM recipes
        WHERE LOWER(name) = 'sambar'
        LIMIT 1
        """
    )

    exact_sambar = cursor.fetchone()

    if exact_sambar:

        print(
            "Exact Sambar:",
            exact_sambar[0],
            "->",
            exact_sambar[1]
        )

    else:

        print(
            "WARNING: Exact Sambar not found."
        )

    # ========================================================
    # DATABASE STATS
    # ========================================================

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

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM ingredient_index
        """
    )

    index_count = cursor.fetchone()[0]

    # ========================================================
    # OPTIMIZE
    # ========================================================

    print()
    print(
        "Optimizing database..."
    )

    cursor.execute(
        "VACUUM"
    )

    connection.close()

    # ========================================================
    # FINAL
    # ========================================================

    database_size_mb = (
        SQLITE_FILE.stat().st_size
        / (1024 * 1024)
    )

    print()
    print("=" * 70)

    print(
        "Recipes:",
        f"{recipe_count:,}"
    )

    print(
        "Unique ingredients:",
        f"{ingredient_count:,}"
    )

    print(
        "Ingredient index rows:",
        f"{index_count:,}"
    )

    print(
        "Database:"
    )

    print(
        SQLITE_FILE
    )

    print()
    print(
        "Database size:",
        f"{database_size_mb:.2f} MB"
    )

    print()
    print("=" * 70)
    print(
        "       BUILD COMPLETE"
    )
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_database()