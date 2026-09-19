import pandas as pd
from pathlib import Path

from nlp.recipe_parser import extract_ingredient_info
from nlp.substitution_engine import get_substitutes


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_DIR / "data" / "recipes_cleaned.parquet"


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    print("\nLoading recipe dataset...")

    df = pd.read_parquet(DATA_FILE)

    print("Recipes loaded:", len(df))

    return df


# ============================================================
# NORMALIZE LIST VALUES
# ============================================================

def normalize_list(value):

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if hasattr(value, "tolist"):

        result = value.tolist()

        if isinstance(result, list):
            return result

    return [str(value)]


# ============================================================
# COMBINE QUANTITY + INGREDIENT
# ============================================================

def combine_ingredients(quantities, ingredients):

    quantities = normalize_list(quantities)
    ingredients = normalize_list(ingredients)

    combined = []

    max_length = max(
        len(quantities),
        len(ingredients)
    )

    for i in range(max_length):

        quantity = ""

        ingredient = ""

        if i < len(quantities):

            quantity = str(
                quantities[i]
            ).strip()

        if i < len(ingredients):

            ingredient = str(
                ingredients[i]
            ).strip()

        # Skip empty ingredients
        if not ingredient:
            continue

        # If quantity exists
        if quantity and quantity.lower() != "nan":

            combined_text = (
                quantity + " " + ingredient
            )

        else:

            combined_text = ingredient

        combined.append(combined_text)

    return combined


# ============================================================
# ANALYZE ONE INGREDIENT
# ============================================================

def analyze_ingredient(ingredient_text):

    # First try the normal NLP parser
    extracted = extract_ingredient_info(
        ingredient_text
    )

    # --------------------------------------------------------
    # If quantity is detected
    # --------------------------------------------------------

    if extracted:

        ingredient_data = extracted[0]

        normalized = ingredient_data[
            "normalized_ingredient"
        ]

        substitutes = get_substitutes(
            normalized
        )

        return {
            "original": ingredient_text,
            "ingredient": normalized,
            "quantity": ingredient_data["quantity"],
            "unit": ingredient_data["unit"],
            "substitutes": substitutes
        }

    # --------------------------------------------------------
    # If no quantity exists
    # --------------------------------------------------------

    normalized = ingredient_text.lower().strip()

    substitutes = get_substitutes(
        normalized
    )

    return {
        "original": ingredient_text,
        "ingredient": normalized,
        "quantity": "",
        "unit": "",
        "substitutes": substitutes
    }


# ============================================================
# ANALYZE COMPLETE RECIPE
# ============================================================

def analyze_recipe(
    quantities,
    ingredients
):

    combined_ingredients = combine_ingredients(
        quantities,
        ingredients
    )

    results = []

    for ingredient in combined_ingredients:

        result = analyze_ingredient(
            ingredient
        )

        if result:

            results.append(result)

    return combined_ingredients, results


# ============================================================
# DISPLAY ANALYSIS
# ============================================================

def display_analysis(results):

    print("\n" + "=" * 70)
    print("                 RECIPE INGREDIENT ANALYSIS")
    print("=" * 70)

    for item in results:

        print("\n" + "-" * 70)

        print(
            "Original Ingredient :",
            item["original"]
        )

        print(
            "Normalized Ingredient:",
            item["ingredient"]
        )

        if item["quantity"]:

            print(
                "Quantity            :",
                item["quantity"],
                item["unit"]
            )

        print("\nPossible Substitutes:")

        if item["substitutes"]:

            for substitute in item["substitutes"]:

                print(
                    f"  → {substitute['substitute']}"
                )

                print(
                    f"    Ratio : {substitute['ratio']}"
                )

                print(
                    f"    Reason: {substitute['reason']}"
                )

        else:

            print(
                "  No substitution available"
            )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("             RecipeSense Whole Recipe Analyzer")
    print("=" * 70)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    df = load_dataset()

    # --------------------------------------------------------
    # Select recipe
    # --------------------------------------------------------

    recipe_index = 0

    recipe = df.iloc[recipe_index]

    print("\n" + "=" * 70)
    print("                     SELECTED RECIPE")
    print("=" * 70)

    print("\nRecipe Name:")
    print(recipe["Name"])

    # --------------------------------------------------------
    # Get quantities and ingredients
    # --------------------------------------------------------

    quantities = recipe[
        "RecipeIngredientQuantities"
    ]

    ingredients = recipe[
        "RecipeIngredientParts"
    ]

    # --------------------------------------------------------
    # Combine them
    # --------------------------------------------------------

    combined, results = analyze_recipe(
        quantities,
        ingredients
    )

    # --------------------------------------------------------
    # Display combined ingredients
    # --------------------------------------------------------

    print("\nCombined Ingredients:")
    print("-" * 70)

    for ingredient in combined:

        print(" -", ingredient)

    # --------------------------------------------------------
    # Display NLP analysis
    # --------------------------------------------------------

    display_analysis(results)

    print("\n" + "=" * 70)
    print("             Recipe analysis completed!")
    print("=" * 70)