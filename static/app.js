// ============================================================
// RecipeSense - Frontend JavaScript
// ============================================================


// ============================================================
// HELPER FUNCTIONS
// ============================================================

function showElement(element) {

    if (element) {
        element.classList.remove("hidden");
    }
}


function hideElement(element) {

    if (element) {
        element.classList.add("hidden");
    }
}


function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text == null
            ? ""
            : String(text);

    return div.innerHTML;
}


function showError(
    element,
    message
) {

    if (!element) {
        return;
    }

    element.innerHTML = `
        <div class="error-message">
            ${escapeHTML(message)}
        </div>
    `;

    showElement(element);
}


// ============================================================
// RECIPE ANALYZER
// ============================================================

const analyzeBtn =
    document.getElementById(
        "analyzeBtn"
    );

const recipeText =
    document.getElementById(
        "recipeText"
    );

const analyzeLoading =
    document.getElementById(
        "analyzeLoading"
    );

const analyzeResult =
    document.getElementById(
        "analyzeResult"
    );


if (analyzeBtn) {

    analyzeBtn.addEventListener(
        "click",
        async function () {

            const text =
                recipeText.value.trim();

            if (!text) {

                showError(
                    analyzeResult,
                    "Please enter a recipe first."
                );

                return;
            }

            showElement(
                analyzeLoading
            );

            hideElement(
                analyzeResult
            );

            analyzeBtn.disabled = true;

            try {

                const response =
                    await fetch(
                        "/analyze",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    recipe_text:
                                        text
                                })
                        }
                    );

                const data =
                    await response.json();

                if (!data.success) {

                    throw new Error(
                        data.message ||
                        "Unable to analyze recipe."
                    );
                }

                displayRecipeAnalysis(
                    data.result
                );

            }
            catch (error) {

                showError(
                    analyzeResult,
                    error.message
                );

            }
            finally {

                hideElement(
                    analyzeLoading
                );

                analyzeBtn.disabled = false;
            }
        }
    );
}


// ============================================================
// DISPLAY RECIPE ANALYSIS
// ============================================================

function displayRecipeAnalysis(
    result
) {

    let html = `
        <h3>🧠 Recipe Analysis</h3>
    `;


    // --------------------------------------------------------
    // Ingredients
    // --------------------------------------------------------

    if (
        result.ingredients &&
        result.ingredients.length > 0
    ) {

        html += `
            <div class="result-section">

                <h4>🥕 Ingredients</h4>

                <div class="analysis-grid">
        `;

        result.ingredients.forEach(
            function (item) {

                const quantity =
                    item.quantity || "";

                const unit =
                    item.unit || "";

                const ingredient =
                    item.ingredient ||
                    item.normalized_ingredient ||
                    "Unknown ingredient";

                html += `
                    <div class="ingredient-item">

                        <div class="ingredient-name">

                            ${escapeHTML(
                                ingredient
                            )}

                        </div>

                        <div class="ingredient-detail">

                            ${escapeHTML(
                                quantity
                            )}

                            ${escapeHTML(
                                unit
                            )}

                        </div>

                    </div>
                `;
            }
        );

        html += `
                </div>

            </div>
        `;
    }


    // --------------------------------------------------------
    // Cooking Actions
    // --------------------------------------------------------

    if (
        result.actions &&
        result.actions.length > 0
    ) {

        html += `
            <div class="result-section">

                <h4>👨‍🍳 Cooking Actions</h4>

                <div class="action-list">
        `;

        result.actions.forEach(
            function (action) {

                html += `
                    <span class="action-tag">

                        ${escapeHTML(
                            action
                        )}

                    </span>
                `;
            }
        );

        html += `
                </div>

            </div>
        `;
    }


    // --------------------------------------------------------
    // Substitutions
    // --------------------------------------------------------

    if (
        result.substitutions &&
        result.substitutions.length > 0
    ) {

        html += `
            <div class="result-section">

                <h4>🔄 Possible Substitutions</h4>
        `;

        result.substitutions.forEach(
            function (item) {

                html += `
                    <div class="substitution-card">

                        <h4>

                            ${escapeHTML(
                                item.ingredient
                            )}

                            →

                            ${escapeHTML(
                                item.substitute
                            )}

                        </h4>

                        <p>

                            <strong>
                                Ratio:
                            </strong>

                            ${escapeHTML(
                                item.ratio
                            )}

                        </p>

                        <p>

                            <strong>
                                Reason:
                            </strong>

                            ${escapeHTML(
                                item.reason
                            )}

                        </p>

                    </div>
                `;
            }
        );

        html += `
            </div>
        `;
    }


    if (
        result.ingredients.length === 0 &&
        result.actions.length === 0
    ) {

        html += `
            <div class="error-message">

                RecipeSense could not identify
                enough information from this recipe.

            </div>
        `;
    }


    analyzeResult.innerHTML =
        html;

    showElement(
        analyzeResult
    );
}


// ============================================================
// WHAT CAN I MAKE?
// ============================================================

const findRecipesBtn =
    document.getElementById(
        "findRecipesBtn"
    );

const availableIngredients =
    document.getElementById(
        "availableIngredients"
    );

const recipeLoading =
    document.getElementById(
        "recipeLoading"
    );

const recipeResult =
    document.getElementById(
        "recipeResult"
    );


if (findRecipesBtn) {

    findRecipesBtn.addEventListener(
        "click",
        async function () {

            const ingredients =
                availableIngredients.value.trim();

            if (!ingredients) {

                showError(
                    recipeResult,
                    "Please enter the ingredients you have."
                );

                return;
            }

            showElement(
                recipeLoading
            );

            hideElement(
                recipeResult
            );

            findRecipesBtn.disabled = true;

            try {

                const response =
                    await fetch(
                        "/find-recipes",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    ingredients:
                                        ingredients
                                })
                        }
                    );

                const data =
                    await response.json();

                if (!data.success) {

                    throw new Error(
                        data.message ||
                        "Unable to find recipes."
                    );
                }

                displayRecipeMatches(
                    data.ingredients,
                    data.results
                );

            }
            catch (error) {

                showError(
                    recipeResult,
                    error.message
                );

            }
            finally {

                hideElement(
                    recipeLoading
                );

                findRecipesBtn.disabled = false;
            }
        }
    );
}


// ============================================================
// DISPLAY RECIPE MATCHES
// ============================================================

function displayRecipeMatches(
    ingredients,
    results
) {

    let html = `

        <div class="result-heading">

            <h3>
                🔎 Recipes You Can Make
            </h3>

            <p>
                Ranked by ingredient compatibility
            </p>

        </div>

        <div class="success-message">

            <strong>
                Ingredients understood:
            </strong>

            ${ingredients
                .map(
                    ingredient =>
                        escapeHTML(
                            ingredient
                        )
                )
                .join(", ")
            }

        </div>
    `;


    if (
        !results ||
        results.length === 0
    ) {

        html += `

            <div class="error-message">

                No suitable recipes found.

                Try adding more ingredients.

            </div>

        `;

        recipeResult.innerHTML =
            html;

        showElement(
            recipeResult
        );

        return;
    }


    // --------------------------------------------------------
    // Recipe cards
    // --------------------------------------------------------

    results.forEach(
        function (recipe, index) {

            const percentage =
                Number(
                    recipe.percentage || 0
                );

            const safePercentage =
                Math.max(
                    0,
                    Math.min(
                        100,
                        percentage
                    )
                );


            html += `

                <div class="recipe-result-card">

                    <div class="recipe-card-header">

                        <div>

                            <span class="recipe-number">
                                ${index + 1}
                            </span>

                            <h3 class="recipe-title">

                                ${escapeHTML(
                                    recipe.name
                                )}

                            </h3>

                        </div>

                        <span class="match-badge">

                            ${safePercentage.toFixed(1)}%

                        </span>

                    </div>


                    <div class="match-bar">

                        <div
                            class="match-bar-fill"
                            style="width: ${safePercentage}%"
                        ></div>

                    </div>


                    <div class="match-label">

                        ${escapeHTML(
                            recipe.category
                        )}

                        &nbsp; • &nbsp;

                        ${recipe.matched_count}
                        /
                        ${recipe.total}
                        ingredients

                    </div>


                    <div class="recipe-columns">

                        <div class="matched-list">

                            <h4>
                                ✓ You Have
                            </h4>
            `;


            // ------------------------------------------------
            // Matched ingredients
            // ------------------------------------------------

            if (
                recipe.matched &&
                recipe.matched.length > 0
            ) {

                recipe.matched.forEach(
                    function (ingredient) {

                        html += `

                            <span class="matched-item">

                                ✓

                                ${escapeHTML(
                                    ingredient
                                )}

                            </span>

                        `;
                    }
                );

            }
            else {

                html += `

                    <span class="muted">
                        No matching ingredients
                    </span>

                `;
            }


            html += `

                        </div>

                        <div class="missing-list">

                            <h4>
                                ✗ Missing
                            </h4>

            `;


            // ------------------------------------------------
            // Missing ingredients
            // ------------------------------------------------

            if (
                recipe.missing &&
                recipe.missing.length > 0
            ) {

                recipe.missing.forEach(
                    function (ingredient) {

                        html += `

                            <span class="missing-item">

                                ${escapeHTML(
                                    ingredient
                                )}

                            </span>

                        `;
                    }
                );

            }
            else {

                html += `

                    <span class="all-have">

                        None — you have
                        all recognized ingredients!

                    </span>

                `;
            }


            html += `

                        </div>

                    </div>


                    <button
                        class="view-recipe-btn"
                        type="button"
                        onclick="openRecipeDetails(
                            '${escapeHTML(
                                String(recipe.name)
                            ).replace(
                                /'/g,
                                "\\'"
                            )}'
                        )"
                    >

                        📖 View Recipe

                    </button>


                </div>

            `;
        }
    );


    recipeResult.innerHTML =
        html;

    showElement(
        recipeResult
    );
}


// ============================================================
// RECIPE DETAILS
// ============================================================

async function openRecipeDetails(
    recipeName
) {

    createRecipeModal();

    const modal =
        document.getElementById(
            "recipeModal"
        );

    const content =
        document.getElementById(
            "recipeModalContent"
        );

    showElement(
        modal
    );

    content.innerHTML = `

        <div class="recipe-detail-loading">

            <div class="loading-spinner"></div>

            <p>
                Loading recipe...
            </p>

        </div>

    `;


    try {

        const response =
            await fetch(
                "/recipe-details?name=" +
                encodeURIComponent(
                    recipeName
                )
            );

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                data.message ||
                "Recipe details not found."
            );
        }

        displayRecipeDetails(
            data.recipe
        );

    }
    catch (error) {

        content.innerHTML = `

            <div class="error-message">

                ${escapeHTML(
                    error.message
                )}

            </div>

        `;
    }
}


// ============================================================
// CREATE RECIPE MODAL
// ============================================================

function createRecipeModal() {

    if (
        document.getElementById(
            "recipeModal"
        )
    ) {

        return;
    }


    const modal =
        document.createElement(
            "div"
        );

    modal.id =
        "recipeModal";

    modal.className =
        "recipe-modal hidden";


    modal.innerHTML = `

        <div class="recipe-modal-overlay"></div>

        <div class="recipe-modal-box">

            <button
                type="button"
                class="recipe-modal-close"
                id="closeRecipeModal"
                aria-label="Close recipe details"
            >

                ×

            </button>

            <div
                id="recipeModalContent"
            >

            </div>

        </div>

    `;


    document.body.appendChild(
        modal
    );


    // ========================================================
    // CLOSE BUTTON FIX
    // ========================================================

    const closeButton =
        modal.querySelector(
            "#closeRecipeModal"
        );

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function (event) {

                event.preventDefault();
                event.stopPropagation();

                closeRecipeModal();

            }
        );
    }


    // ========================================================
    // CLOSE WHEN CLICKING OUTSIDE MODAL
    // ========================================================

    const overlay =
        modal.querySelector(
            ".recipe-modal-overlay"
        );

    if (overlay) {

        overlay.addEventListener(
            "click",
            function () {

                closeRecipeModal();

            }
        );
    }


    // ========================================================
    // ESCAPE KEY
    // ========================================================

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                closeRecipeModal();

            }
        }
    );
}


// ============================================================
// CLOSE MODAL
// ============================================================

function closeRecipeModal() {

    const modal =
        document.getElementById(
            "recipeModal"
        );

    if (modal) {

        modal.classList.add(
            "hidden"
        );

    }
}


// ============================================================
// DISPLAY RECIPE DETAILS
// ============================================================

function displayRecipeDetails(
    recipe
) {

    const content =
        document.getElementById(
            "recipeModalContent"
        );


    let html = `

        <div class="recipe-detail">

            <div class="recipe-detail-header">

                <span class="detail-category">

                    ${escapeHTML(
                        recipe.category ||
                        "Recipe"
                    )}

                </span>

                <h2>

                    ${escapeHTML(
                        recipe.name
                    )}

                </h2>

            </div>

    `;


    // --------------------------------------------------------
    // Description
    // --------------------------------------------------------

    if (recipe.description) {

        html += `

            <div class="recipe-description">

                ${escapeHTML(
                    recipe.description
                )}

            </div>

        `;
    }


    // --------------------------------------------------------
    // Time information
    // --------------------------------------------------------

    html += `

        <div class="recipe-meta">

            <div>

                <span>⏱</span>

                <strong>
                    Prep
                </strong>

                <small>
                    ${escapeHTML(
                        recipe.prep_time ||
                        "Not specified"
                    )}
                </small>

            </div>


            <div>

                <span>🍳</span>

                <strong>
                    Cook
                </strong>

                <small>
                    ${escapeHTML(
                        recipe.cook_time ||
                        "Not specified"
                    )}
                </small>

            </div>


            <div>

                <span>⏰</span>

                <strong>
                    Total
                </strong>

                <small>
                    ${escapeHTML(
                        recipe.total_time ||
                        "Not specified"
                    )}
                </small>

            </div>


            <div>

                <span>🍽</span>

                <strong>
                    Servings
                </strong>

                <small>
                    ${escapeHTML(
                        recipe.servings ||
                        "Not specified"
                    )}
                </small>

            </div>

        </div>

    `;


    // --------------------------------------------------------
    // Ingredients
    // --------------------------------------------------------

    html += `

        <div class="recipe-detail-section">

            <h3>
                🥕 Ingredients
            </h3>

            <ul class="recipe-ingredients">

    `;


    if (
        recipe.ingredients &&
        recipe.ingredients.length > 0
    ) {

        recipe.ingredients.forEach(
            function (ingredient) {

                html += `

                    <li>

                        <span>•</span>

                        ${escapeHTML(
                            ingredient
                        )}

                    </li>

                `;
            }
        );

    }
    else {

        html += `

            <li>
                Ingredient information unavailable.
            </li>

        `;
    }


    html += `

            </ul>

        </div>

    `;


    // --------------------------------------------------------
    // Instructions
    // --------------------------------------------------------

    html += `

        <div class="recipe-detail-section">

            <h3>
                👨‍🍳 Cooking Instructions
            </h3>

            <ol class="recipe-instructions">

    `;


    if (
        recipe.instructions &&
        recipe.instructions.length > 0
    ) {

        recipe.instructions.forEach(
            function (
                instruction,
                index
            ) {

                html += `

                    <li>

                        <span class="step-number">

                            ${index + 1}

                        </span>

                        <span>

                            ${escapeHTML(
                                instruction
                            )}

                        </span>

                    </li>

                `;
            }
        );

    }
    else {

        html += `

            <li>

                Cooking instructions
                are not available.

            </li>

        `;
    }


    html += `

            </ol>

        </div>

        <div class="recipe-source-note">

            Recipe information sourced from
            the Food.com dataset used by RecipeSense.

        </div>

        </div>

    `;


    content.innerHTML =
        html;
}


// ============================================================
// ENTER KEY SUPPORT
// ============================================================

if (availableIngredients) {

    availableIngredients.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                findRecipesBtn.click();
            }
        }
    );
}


const substitutionIngredient =
    document.getElementById(
        "substitutionIngredient"
    );


const substituteBtn =
    document.getElementById(
        "substituteBtn"
    );


const substitutionLoading =
    document.getElementById(
        "substitutionLoading"
    );


const substitutionResult =
    document.getElementById(
        "substitutionResult"
    );


// ============================================================
// INGREDIENT SUBSTITUTION
// ============================================================

if (substituteBtn) {

    substituteBtn.addEventListener(
        "click",
        async function () {

            const ingredient =
                substitutionIngredient.value.trim();

            if (!ingredient) {

                showError(
                    substitutionResult,
                    "Please enter an ingredient."
                );

                return;
            }

            showElement(
                substitutionLoading
            );

            hideElement(
                substitutionResult
            );

            substituteBtn.disabled =
                true;

            try {

                const response =
                    await fetch(
                        "/substitute",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    ingredient:
                                        ingredient
                                })
                        }
                    );

                const data =
                    await response.json();

                if (!data.success) {

                    throw new Error(
                        data.message ||
                        "Unable to find substitutes."
                    );
                }

                displaySubstitutions(
                    data.result
                );

            }
            catch (error) {

                showError(
                    substitutionResult,
                    error.message
                );

            }
            finally {

                hideElement(
                    substitutionLoading
                );

                substituteBtn.disabled =
                    false;
            }
        }
    );
}


// ============================================================
// DISPLAY SUBSTITUTIONS
// ============================================================

function displaySubstitutions(
    result
) {

    let html = `

        <h3>
            🔄 Substitution Suggestions
        </h3>

        <div class="success-message">

            Ingredient understood:

            <strong>
                ${escapeHTML(
                    result.ingredient
                )}
            </strong>

            <br>

            Quantity:

            ${escapeHTML(
                result.quantity || ""
            )}

            ${escapeHTML(
                result.unit || ""
            )}

        </div>

    `;


    if (
        !result.substitutes ||
        result.substitutes.length === 0
    ) {

        html += `

            <div class="error-message">

                No substitution found
                for this ingredient.

            </div>

        `;

        substitutionResult.innerHTML =
            html;

        showElement(
            substitutionResult
        );

        return;
    }


    result.substitutes.forEach(
        function (item) {

            html += `

                <div class="substitution-card">

                    <h4>

                        ${escapeHTML(
                            result.ingredient
                        )}

                        →

                        ${escapeHTML(
                            item.substitute
                        )}

                    </h4>

                    <p>

                        <strong>
                            Replacement Ratio:
                        </strong>

                        ${escapeHTML(
                            item.ratio
                        )}

                    </p>

                    <p>

                        <strong>
                            Why:
                        </strong>

                        ${escapeHTML(
                            item.reason
                        )}

                    </p>

                </div>

            `;
        }
    );


    substitutionResult.innerHTML =
        html;

    showElement(
        substitutionResult
    );
}


if (substitutionIngredient) {

    substitutionIngredient.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                substituteBtn.click();
            }
        }
    );
}