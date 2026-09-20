import json
import re
import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_DIR = PROJECT_DIR / "data"

PARQUET_FILE = (
    DATA_DIR
    / "recipes_cleaned.parquet"
)

SQLITE_FILE = (
    DATA_DIR
    / "recipe_index.db"
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
            r"\b"
            + re.escape(word)
            + r"\b",
            "",
            ingredient
        )

    # --------------------------------------------------------
    # Ingredient-form words
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
    # Remove extra spaces
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

    return INGREDIENT_ALIASES.get(
        ingredient,
        ingredient
    )


# ============================================================
# CONVERT INGREDIENT LIST TO JSON
# ============================================================

def serialize_ingredients(value):

    if value is None:
        return "[]"

    # --------------------------------------------------------
    # Handle pandas / NumPy arrays
    # --------------------------------------------------------

    try:

        if hasattr(
            value,
            "tolist"
        ):

            value = value.tolist()

    except Exception:
        pass

    # --------------------------------------------------------
    # Convert to list
    # --------------------------------------------------------

    if not isinstance(
        value,
        (list, tuple)
    ):

        return "[]"

    ingredients = []

    for ingredient in value:

        if ingredient is None:
            continue

        try:

            if pd.isna(
                ingredient
            ):

                continue

        except Exception:
            pass

        ingredient = str(
            ingredient
        ).strip()

        if ingredient:
            ingredients.append(
                ingredient
            )

    return json.dumps(
        ingredients,
        ensure_ascii=False
    )


# ============================================================
# BUILD DATABASE
# ============================================================

def build_database():

    print("=" * 70)
    print("       RecipeSense SQLite Index Builder")
    print("=" * 70)
    print()

    print(
        "Source:",
        PARQUET_FILE
    )

    print(
        "Output:",
        SQLITE_FILE
    )

    print()

    # --------------------------------------------------------
    # Check Parquet file
    # --------------------------------------------------------

    if not PARQUET_FILE.exists():

        raise FileNotFoundError(
            f"Parquet file not found:\n"
            f"{PARQUET_FILE}"
        )

    # --------------------------------------------------------
    # Delete old database
    # --------------------------------------------------------

    if SQLITE_FILE.exists():

        print(
            "Removing old SQLite database..."
        )

        SQLITE_FILE.unlink()

        print(
            "Old database removed."
        )

        print()

    # --------------------------------------------------------
    # Load required columns
    # --------------------------------------------------------

    print(
        "Loading recipes_cleaned.parquet..."
    )

    dataframe = pd.read_parquet(
        PARQUET_FILE,
        columns=[
            "RecipeId",
            "Name",
            "RecipeCategory",
            "RecipeIngredientParts"
        ]
    )

    print(
        f"Rows loaded: {len(dataframe):,}"
    )

    print()

    # ========================================================
    # IMPORTANT
    # ========================================================
    #
    # RecipeId MUST come from the actual RecipeId column.
    #
    # We DO NOT use:
    #
    #     dataframe.index
    #
    # and we DO NOT generate new IDs.
    #
    # This is the fix for the Sambar -> Peach Cobbler bug.
    # ========================================================

    print(
        "Preparing RecipeId values..."
    )

    dataframe["RecipeId"] = pd.to_numeric(
        dataframe["RecipeId"],
        errors="coerce"
    )

    # Remove rows without valid RecipeId

    dataframe = dataframe[
        dataframe["RecipeId"].notna()
    ].copy()

    # Convert float IDs such as 81933.0
    # into integer IDs such as 81933

    dataframe["RecipeId"] = (
        dataframe["RecipeId"]
        .astype("int64")
    )

    print(
        f"Valid recipes: {len(dataframe):,}"
    )

    print()

    # --------------------------------------------------------
    # Check duplicate RecipeIds
    # --------------------------------------------------------

    duplicate_count = (
        dataframe["RecipeId"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate RecipeIds: "
        f"{duplicate_count:,}"
    )

    if duplicate_count > 0:

        print(
            "Removing duplicate RecipeIds..."
        )

        dataframe = (
            dataframe
            .drop_duplicates(
                subset=["RecipeId"],
                keep="first"
            )
            .copy()
        )

    print(
        f"Final recipes: "
        f"{len(dataframe):,}"
    )

    print()

    # ========================================================
    # CREATE SQLITE DATABASE
    # ========================================================

    print(
        "Creating SQLite database..."
    )

    connection = sqlite3.connect(
        SQLITE_FILE
    )

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Performance settings
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA journal_mode = WAL"
    )

    cursor.execute(
        "PRAGMA synchronous = NORMAL"
    )

    cursor.execute(
        "PRAGMA temp_store = MEMORY"
    )

    cursor.execute(
        "PRAGMA cache_size = -200000"
    )

    # --------------------------------------------------------
    # Recipes table
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE recipes (

            recipe_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL,

            category TEXT,

            ingredients TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # Ingredient index table
    # --------------------------------------------------------

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
    # INSERT DATA
    # ========================================================

    recipe_rows = []

    ingredient_rows = []

    total_rows = len(
        dataframe
    )

    print(
        "Building recipe index..."
    )

    print()

    for position, (_, row) in enumerate(
        dataframe.iterrows(),
        start=1
    ):

        # ----------------------------------------------------
        # REAL RecipeId
        # ----------------------------------------------------

        recipe_id = int(
            row["RecipeId"]
        )

        # ----------------------------------------------------
        # Name
        # ----------------------------------------------------

        name = row["Name"]

        if name is None:

            name = ""

        else:

            name = str(
                name
            ).strip()

        if not name:
            continue

        # ----------------------------------------------------
        # Category
        # ----------------------------------------------------

        category = row[
            "RecipeCategory"
        ]

        if category is None:

            category = ""

        else:

            category = str(
                category
            ).strip()

        # ----------------------------------------------------
        # Original ingredient list
        # ----------------------------------------------------

        raw_ingredients = row[
            "RecipeIngredientParts"
        ]

        # Convert NumPy array/list
        # into normal Python list

        if raw_ingredients is None:

            raw_ingredients = []

        else:

            try:

                if hasattr(
                    raw_ingredients,
                    "tolist"
                ):

                    raw_ingredients = (
                        raw_ingredients.tolist()
                    )

            except Exception:
                pass

        if not isinstance(
            raw_ingredients,
            (list, tuple)
        ):

            raw_ingredients = []

        # ----------------------------------------------------
        # Store original ingredient list
        # ----------------------------------------------------

        ingredients_json = (
            serialize_ingredients(
                raw_ingredients
            )
        )

        recipe_rows.append(
            (
                recipe_id,
                name,
                category,
                ingredients_json
            )
        )

        # ----------------------------------------------------
        # Build normalized ingredient index
        # ----------------------------------------------------

        unique_ingredients = set()

        for ingredient in raw_ingredients:

            normalized = (
                normalize_with_alias(
                    ingredient
                )
            )

            if normalized:

                unique_ingredients.add(
                    normalized
                )

        for ingredient in unique_ingredients:

            ingredient_rows.append(
                (
                    ingredient,
                    recipe_id
                )
            )

        # ----------------------------------------------------
        # Batch insert
        # ----------------------------------------------------

        if (
            len(recipe_rows)
            >= 5000
        ):

            cursor.executemany(
                """
                INSERT OR IGNORE INTO recipes
                (
                    recipe_id,
                    name,
                    category,
                    ingredients
                )
                VALUES (?, ?, ?, ?)
                """,
                recipe_rows
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

            recipe_rows.clear()
            ingredient_rows.clear()

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            position % 25000 == 0
            or position == total_rows
        ):

            percentage = (
                position
                / total_rows
            ) * 100

            print(
                f"Processed "
                f"{position:,} / "
                f"{total_rows:,} "
                f"({percentage:.1f}%)"
            )

    # ========================================================
    # INSERT REMAINING ROWS
    # ========================================================

    if recipe_rows:

        cursor.executemany(
            """
            INSERT OR IGNORE INTO recipes
            (
                recipe_id,
                name,
                category,
                ingredients
            )
            VALUES (?, ?, ?, ?)
            """,
            recipe_rows
        )

    if ingredient_rows:

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

    # ========================================================
    # CREATE INDEXES
    # ========================================================

    print()
    print(
        "Creating SQLite indexes..."
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

    connection.commit()

    # ========================================================
    # VERIFY DATABASE
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
        SELECT recipe_id, name
        FROM recipes
        WHERE LOWER(name) LIKE '%sambar%'
        LIMIT 10
        """
    )

    sambar_rows = cursor.fetchall()

    # ========================================================
    # OPTIMIZE DATABASE
    # ========================================================

    print(
        "Optimizing database..."
    )

    cursor.execute(
        "VACUUM"
    )

    connection.commit()

    connection.close()

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print("       SQLite DATABASE CREATED")
    print("=" * 70)

    print()

    print(
        f"Recipes indexed: "
        f"{recipe_count:,}"
    )

    print(
        f"Ingredients indexed: "
        f"{ingredient_count:,}"
    )

    print()

    print(
        "Sambar verification:"
    )

    print("-" * 70)

    for recipe_id, name in sambar_rows:

        print(
            f"{recipe_id} -> {name}"
        )

    print("-" * 70)

    print()

    print(
        "Database:"
    )

    print(
        SQLITE_FILE
    )

    print()
    database_size_mb = (
    SQLITE_FILE.stat().st_size
    / (1024 * 1024)
    )

    print(
    "Database size:",
    f"{database_size_mb:.2f} MB"
)

    print()

    print("=" * 70)
    print("       BUILD COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_database()