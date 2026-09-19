import re


# ============================================================
# FRACTION NORMALIZATION
# ============================================================

FRACTIONS = {
    "½": "1/2",
    "¼": "1/4",
    "¾": "3/4",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8"
}


# ============================================================
# COOKING ACTIONS
# ============================================================

COOKING_ACTIONS = [
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


# ============================================================
# INGREDIENT DESCRIPTORS
# ============================================================

DESCRIPTORS = [
    "fresh",
    "large",
    "small",
    "medium",
    "extra",
    "firm",
    "boneless",
    "skinless",
    "low fat",
    "low-fat",
    "fat free",
    "fat-free",
    "reduced fat",
    "reduced-fat",
    "unsalted",
    "salted",
    "melted",
    "softened",
    "chopped",
    "diced",
    "sliced",
    "minced",
    "grated",
    "ground",
    "crushed",
    "shredded",
    "frozen",
    "cooked",
    "raw",
    "hot",
    "cold",
    "dry",
    "dried",
    "whole",
    "plain"
]


# ============================================================
# UNITS
# ============================================================

UNITS = [
    "cups?",
    "tablespoons?",
    "tbsp",
    "teaspoons?",
    "tsp",
    "grams?",
    "g",
    "kilograms?",
    "kg",
    "milliliters?",
    "ml",
    "liters?",
    "l",
    "ounces?",
    "oz",
    "pounds?",
    "lbs?",
    "pinch",
    "dash"
]


# ============================================================
# NORMALIZE FRACTIONS
# ============================================================

def normalize_fractions(text):

    for symbol, value in FRACTIONS.items():
        text = text.replace(symbol, value)

    text = text.replace("⁄", "/")

    return text


# ============================================================
# NORMALIZE INGREDIENT NAME
# ============================================================

def normalize_ingredient_name(ingredient):

    ingredient = ingredient.lower().strip()

    # Remove "of" from the beginning
    # Example:
    # "of melted butter" -> "melted butter"
    ingredient = re.sub(r"^\s*of\s+", "", ingredient)

    # Remove text after comma
    # Example:
    # "lemons, rind of" -> "lemons"
    ingredient = ingredient.split(",")[0].strip()

    # Remove brackets and their contents
    ingredient = re.sub(r"\([^)]*\)", "", ingredient)

    # Remove descriptors
    for descriptor in DESCRIPTORS:

        pattern = r"\b" + re.escape(descriptor) + r"\b"

        ingredient = re.sub(pattern, "", ingredient)

    # Remove extra spaces
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    # Common ingredient normalization
    replacements = {
        "cloves": "",
        "clove": "",
        "leaves": "",
        "leaf": "",
        "berries": "berry",
        "tomatoes": "tomato",
        "onions": "onion",
        "lemons": "lemon",
        "eggs": "egg"
    }

    words = ingredient.split()

    cleaned_words = []

    for word in words:

        if word in replacements:

            replacement = replacements[word]

            if replacement:
                cleaned_words.append(replacement)

        else:
            cleaned_words.append(word)

    ingredient = " ".join(cleaned_words)

    # Final cleanup
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    return ingredient


# ============================================================
# EXTRACT INGREDIENT INFORMATION
# ============================================================

def extract_ingredient_info(text):

    text = normalize_fractions(text.lower())

    results = []

    pattern = (
        r"(\d+(?:\s+\d+/\d+|/\d+|(?:\.\d+)?))"
        r"\s*"
        r"("
        + "|".join(UNITS) +
        r")?"
        r"\s+"
        r"(.+)"
    )

    matches = re.findall(pattern, text)

    for match in matches:

        quantity = match[0].strip()
        unit = match[1].strip()
        ingredient = match[2].strip()

        normalized = normalize_ingredient_name(ingredient)

        results.append({
            "ingredient": ingredient,
            "normalized_ingredient": normalized,
            "quantity": quantity,
            "unit": unit
        })

    return results


# ============================================================
# EXTRACT COOKING ACTIONS
# ============================================================

def extract_actions(text):

    text = text.lower()

    found_actions = []

    for action in COOKING_ACTIONS:

        pattern = r"\b" + re.escape(action) + r"\b"

        if re.search(pattern, text):

            found_actions.append(action)

    return found_actions


# ============================================================
# TEST PROGRAM
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("        RecipeSense NLP Parser")
    print("=" * 60)

    sample_ingredients = [
        "2 cups flour",
        "1/2 teaspoon salt",
        "3 large eggs",
        "2 tablespoons melted butter",
        "1 cup of fresh milk",
        "2 cloves of garlic"
    ]

    print("\nINGREDIENT INFORMATION")
    print("-" * 60)

    for ingredient in sample_ingredients:

        result = extract_ingredient_info(ingredient)

        for item in result:
            print(item)

    sample_text = """
    Add the flour and salt.
    Beat the eggs and mix with melted butter.
    Bake until golden brown.
    """

    print("\nCOOKING ACTIONS")
    print("-" * 60)

    actions = extract_actions(sample_text)

    for action in actions:
        print("-", action)

    print("\n" + "=" * 60)