import pandas as pd

file_path = "data/recipes.parquet"

print("=" * 70)
print("          RecipeSense - Detailed Dataset Inspection")
print("=" * 70)

# Load dataset
df = pd.read_parquet(file_path)

print("\n1. DATASET SIZE")
print("-" * 50)
print("Rows    :", len(df))
print("Columns :", len(df.columns))

# ---------------------------------------------------------
# Duplicate Recipe IDs
# ---------------------------------------------------------

print("\n2. DUPLICATE RECIPE IDs")
print("-" * 50)

duplicate_ids = df["RecipeId"].duplicated().sum()

print("Duplicate Recipe IDs:", duplicate_ids)

# ---------------------------------------------------------
# Important columns
# ---------------------------------------------------------

print("\n3. IMPORTANT COLUMNS")
print("-" * 50)

important_columns = [
    "Name",
    "Description",
    "RecipeCategory",
    "Keywords",
    "RecipeIngredientQuantities",
    "RecipeIngredientParts",
    "RecipeInstructions",
    "RecipeServings"
]

for column in important_columns:
    print("\n", column)
    print("Type:", df[column].dtype)

# ---------------------------------------------------------
# Sample recipe
# ---------------------------------------------------------

print("\n4. SAMPLE RECIPE")
print("-" * 50)

recipe = df.iloc[0]

print("\nRecipe Name:")
print(recipe["Name"])

print("\nCategory:")
print(recipe["RecipeCategory"])

print("\nDescription:")
print(recipe["Description"])

print("\nIngredient Quantities:")
print(recipe["RecipeIngredientQuantities"])

print("\nIngredient Parts:")
print(recipe["RecipeIngredientParts"])

print("\nInstructions:")
print(recipe["RecipeInstructions"])

# ---------------------------------------------------------
# Missing values for important columns
# ---------------------------------------------------------

print("\n5. MISSING VALUES - IMPORTANT COLUMNS")
print("-" * 50)

for column in important_columns:
    print(column, ":", df[column].isna().sum())

# ---------------------------------------------------------
# Unique categories
# ---------------------------------------------------------

print("\n6. RECIPE CATEGORIES")
print("-" * 50)

print("Number of unique categories:",
      df["RecipeCategory"].nunique())

print("\nTop 20 categories:")

print(
    df["RecipeCategory"]
    .value_counts()
    .head(20)
)

print("\n" + "=" * 70)
print("Inspection completed successfully!")
print("=" * 70)