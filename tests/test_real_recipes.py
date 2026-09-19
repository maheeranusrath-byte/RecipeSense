import pandas as pd
from nlp.recipe_parser import extract_ingredient_info, extract_actions


# ---------------------------------------------------------
# LOAD CLEAN DATASET
# ---------------------------------------------------------

FILE_PATH = "data/recipes_cleaned.parquet"

print("=" * 70)
print("        RecipeSense - Real Recipe NLP Testing")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_parquet(FILE_PATH)

print("Recipes loaded:", len(df))


# ---------------------------------------------------------
# TEST 5 REAL RECIPES
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("              TESTING REAL RECIPES")
print("=" * 70)


for index in range(5):

    recipe = df.iloc[index]

    print("\n" + "-" * 70)

    print("RECIPE", index + 1)

    print("-" * 70)

    print("\nName:")
    print(recipe["Name"])

    print("\nIngredients:")
    
    ingredients = recipe["RecipeIngredientParts"]

    for ingredient in ingredients:
        print(" -", ingredient)

    print("\nDetected Cooking Actions:")

    instructions = " ".join(
        recipe["RecipeInstructions"]
    )

    actions = extract_actions(instructions)

    if actions:
        for action in actions:
            print(" -", action)
    else:
        print(" - No actions detected")


print("\n" + "=" * 70)
print("Real recipe testing completed!")
print("=" * 70)