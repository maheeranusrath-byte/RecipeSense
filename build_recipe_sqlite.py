import json
import pickle
import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

PICKLE_FILE = PROJECT_DIR / "data" / "recipe_index.pkl"
SQLITE_FILE = PROJECT_DIR / "data" / "recipe_index.db"


# ============================================================
# MAIN
# ============================================================

def build_sqlite_database():

    print("=" * 70)
    print("          RecipeSense SQLite Index Builder")
    print("=" * 70)

    print("\nLoading existing recipe index...")

    with open(PICKLE_FILE, "rb") as file:
        index_data = pickle.load(file)

    recipes = index_data["recipes"]
    ingredient_index = index_data["ingredient_index"]

    print(f"Recipes loaded: {len(recipes)}")
    print(f"Ingredients indexed: {len(ingredient_index)}")

    # --------------------------------------------------------
    # Remove old database if it exists
    # --------------------------------------------------------

    if SQLITE_FILE.exists():

        print("\nRemoving old SQLite database...")

        SQLITE_FILE.unlink()

    # --------------------------------------------------------
    # Create SQLite database
    # --------------------------------------------------------

    print("\nCreating SQLite database...")

    connection = sqlite3.connect(SQLITE_FILE)

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Performance settings
    # --------------------------------------------------------

    cursor.execute("PRAGMA journal_mode = OFF")
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA temp_store = MEMORY")

    # --------------------------------------------------------
    # Create tables
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE recipes (
            recipe_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            ingredients TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE ingredient_index (
            ingredient TEXT NOT NULL,
            recipe_id INTEGER NOT NULL
        )
    """)

    # --------------------------------------------------------
    # Insert recipes
    # --------------------------------------------------------

    print("\nWriting recipes...")

    recipe_rows = []

    for recipe_id, recipe in recipes.items():

        recipe_rows.append((
            int(recipe_id),
            str(recipe.get("name", "")),
            str(recipe.get("category", "")),
            json.dumps(
                list(recipe.get("ingredients", [])),
                ensure_ascii=False
            )
        ))

        if len(recipe_rows) >= 5000:

            cursor.executemany(
                """
                INSERT INTO recipes
                (recipe_id, name, category, ingredients)
                VALUES (?, ?, ?, ?)
                """,
                recipe_rows
            )

            recipe_rows.clear()

    if recipe_rows:

        cursor.executemany(
            """
            INSERT INTO recipes
            (recipe_id, name, category, ingredients)
            VALUES (?, ?, ?, ?)
            """,
            recipe_rows
        )

    # --------------------------------------------------------
    # Insert ingredient index
    # --------------------------------------------------------

    print("Writing ingredient index...")

    ingredient_rows = []

    for ingredient, recipe_ids in ingredient_index.items():

        for recipe_id in recipe_ids:

            ingredient_rows.append((
                str(ingredient),
                int(recipe_id)
            ))

            if len(ingredient_rows) >= 10000:

                cursor.executemany(
                    """
                    INSERT INTO ingredient_index
                    (ingredient, recipe_id)
                    VALUES (?, ?)
                    """,
                    ingredient_rows
                )

                ingredient_rows.clear()

    if ingredient_rows:

        cursor.executemany(
            """
            INSERT INTO ingredient_index
            (ingredient, recipe_id)
            VALUES (?, ?)
            """,
            ingredient_rows
        )

    # --------------------------------------------------------
    # Create indexes
    # --------------------------------------------------------

    print("\nCreating SQLite indexes...")

    cursor.execute("""
        CREATE INDEX idx_ingredient
        ON ingredient_index(ingredient)
    """)

    cursor.execute("""
        CREATE INDEX idx_recipe_id
        ON ingredient_index(recipe_id)
    """)

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    connection.commit()

    # --------------------------------------------------------
    # Optimize database
    # --------------------------------------------------------

    print("Optimizing database...")

    cursor.execute("VACUUM")

    connection.close()

    # --------------------------------------------------------
    # Final information
    # --------------------------------------------------------

    database_size_mb = (
        SQLITE_FILE.stat().st_size /
        (1024 * 1024)
    )

    print("\n" + "=" * 70)
    print("             SQLite DATABASE CREATED")
    print("=" * 70)

    print(f"\nDatabase:")
    print(SQLITE_FILE)

    print(
        f"\nDatabase size: "
        f"{database_size_mb:.2f} MB"
    )

    print("\nRecipes stored:", len(recipes))

    print(
        "Ingredients indexed:",
        len(ingredient_index)
    )

    print("\n" + "=" * 70)
    print("                    COMPLETE")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    build_sqlite_database()