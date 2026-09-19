import pandas as pd
import numpy as np
import re


INPUT_FILE = "data/recipes.parquet"
OUTPUT_FILE = "data/recipes_cleaned.parquet"


print("=" * 70)
print("              RecipeSense - Data Cleaning")
print("=" * 70)


# ---------------------------------------------------------
# 1. LOAD DATASET
# ---------------------------------------------------------

print("\n1. Loading dataset...")

df = pd.read_parquet(INPUT_FILE)

print("Original rows:", len(df))


# ---------------------------------------------------------
# 2. SELECT USEFUL COLUMNS
# ---------------------------------------------------------

columns_to_keep = [
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

df = df[columns_to_keep]

print("\nColumns selected:", len(df.columns))


# ---------------------------------------------------------
# 3. REMOVE DUPLICATE RECIPE IDs
# ---------------------------------------------------------

before = len(df)

df = df.drop_duplicates(
    subset="RecipeId",
    keep="first"
)

duplicates_removed = before - len(df)

print("\n2. Duplicate recipes removed:", duplicates_removed)


# ---------------------------------------------------------
# 4. REMOVE RECIPES WITHOUT ESSENTIAL INFORMATION
# ---------------------------------------------------------

before = len(df)

df = df.dropna(
    subset=[
        "Name",
        "RecipeIngredientParts",
        "RecipeInstructions"
    ]
)

missing_removed = before - len(df)

print("3. Recipes removed due to missing essential data:",
      missing_removed)


# ---------------------------------------------------------
# 5. CLEAN RECIPE NAMES
# ---------------------------------------------------------

df["Name"] = (
    df["Name"]
    .astype(str)
    .str.strip()
)


# ---------------------------------------------------------
# 6. CLEAN DESCRIPTION
# ---------------------------------------------------------

df["Description"] = (
    df["Description"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ---------------------------------------------------------
# 7. CLEAN CATEGORY
# ---------------------------------------------------------

df["RecipeCategory"] = (
    df["RecipeCategory"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)


# ---------------------------------------------------------
# 8. CLEAN TIME COLUMNS
# ---------------------------------------------------------

for column in ["CookTime", "PrepTime", "TotalTime"]:

    df[column] = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# ---------------------------------------------------------
# 9. CLEAN KEYWORDS
# ---------------------------------------------------------

df["Keywords"] = df["Keywords"].apply(
    lambda x: [] if x is None else x
)


# ---------------------------------------------------------
# 10. CLEAN INGREDIENT PARTS
# ---------------------------------------------------------

def clean_ingredients(value):

    if value is None:
        return []

    if isinstance(value, np.ndarray):
        value = value.tolist()

    if not isinstance(value, (list, tuple)):
        return []

    cleaned = []

    for item in value:

        if item is None:
            continue

        item = str(item).strip().lower()

        if item:
            cleaned.append(item)

    return cleaned


df["RecipeIngredientParts"] = (
    df["RecipeIngredientParts"]
    .apply(clean_ingredients)
)


# ---------------------------------------------------------
# 11. CLEAN INGREDIENT QUANTITIES
# ---------------------------------------------------------

def clean_quantities(value):

    if value is None:
        return []

    if isinstance(value, np.ndarray):
        value = value.tolist()

    if not isinstance(value, (list, tuple)):
        return []

    cleaned = []

    for item in value:

        if item is None:
            continue

        item = str(item).strip()

        if item:
            cleaned.append(item)

    return cleaned


df["RecipeIngredientQuantities"] = (
    df["RecipeIngredientQuantities"]
    .apply(clean_quantities)
)


# ---------------------------------------------------------
# 12. CLEAN INSTRUCTIONS
# ---------------------------------------------------------

def clean_instructions(value):

    if value is None:
        return []

    if isinstance(value, np.ndarray):
        value = value.tolist()

    if not isinstance(value, (list, tuple)):
        return []

    cleaned = []

    for instruction in value:

        if instruction is None:
            continue

        instruction = str(instruction).strip()

        if instruction:
            cleaned.append(instruction)

    return cleaned


df["RecipeInstructions"] = (
    df["RecipeInstructions"]
    .apply(clean_instructions)
)


# ---------------------------------------------------------
# 13. REMOVE RECIPES WITH EMPTY INGREDIENTS
# ---------------------------------------------------------

before = len(df)

df = df[
    df["RecipeIngredientParts"].apply(len) > 0
]

ingredients_removed = before - len(df)

print("\n4. Recipes removed with no ingredients:",
      ingredients_removed)


# ---------------------------------------------------------
# 14. REMOVE RECIPES WITH EMPTY INSTRUCTIONS
# ---------------------------------------------------------

before = len(df)

df = df[
    df["RecipeInstructions"].apply(len) > 0
]

instructions_removed = before - len(df)

print("5. Recipes removed with no instructions:",
      instructions_removed)


# ---------------------------------------------------------
# 15. SAVE CLEAN DATASET
# ---------------------------------------------------------

df.to_parquet(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 16. FINAL SUMMARY
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("                  CLEANING SUMMARY")
print("=" * 70)

print("\nOriginal rows       :", 522517)
print("Final rows          :", len(df))
print("Rows removed        :", 522517 - len(df))
print("Final columns       :", len(df.columns))

print("\nClean dataset saved to:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("              Cleaning completed!")
print("=" * 70)