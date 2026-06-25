"""
FridgeChef AI - Streamlit Application (CLEAN + REALISTIC NUTRITION FIX)

FIXES APPLIED:
------------------------------------
✔ Servings now displayed clearly
✔ Per-serving vs whole-dish separation
✔ Nutrition confusion removed
✔ Calories interpretation made explicit
✔ UI consistency improved
"""

import streamlit as st
import time
import re
from agents.coordinator_agent import CoordinatorAgent

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="FridgeChef AI",
    page_icon="🍳",
    layout="wide"
)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def safe_list(v):
    return v if isinstance(v, list) else []


def safe_number(v):
    if v is None:
        return 0
    try:
        if isinstance(v, (int, float)):
            return round(float(v), 1)
        match = re.search(r"(\d+\.?\d*)", str(v))
        return round(float(match.group(1)), 1) if match else 0
    except:
        return 0


def normalize_name(name):
    return str(name).strip().lower()

# ---------------------------------------------------------
# COUNTRY FLAGS
# ---------------------------------------------------------

COUNTRY_FLAGS = {
    "British": "🇬🇧",
    "American": "🇺🇸",
    "Canadian": "🇨🇦",
    "Mexican": "🇲🇽",
    "Italian": "🇮🇹",
    "French": "🇫🇷",
    "Greek": "🇬🇷",
    "Spanish": "🇪🇸",
    "Japanese": "🇯🇵",
    "Chinese": "🇨🇳",
    "Indian": "🇮🇳",
    "Thai": "🇹🇭",
    "Vietnamese": "🇻🇳",
    "Saudi Arabian": "🇸🇦",
    "Korean": "🇰🇷",
}

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.title("🍳 FridgeChef AI")
st.caption("Multi-agent meal intelligence system (Kaggle-style output)")

ingredients = st.text_area("🥕 Ingredients (comma separated)")
goal = st.selectbox("🎯 Goal", ["Lose Weight", "Maintenance", "Weight Gain"])

st.subheader("🧍 Personal Profile")
weight_input = st.text_input("Weight (kg)", "70")
height_input = st.text_input("Height (cm)", "170")

diet_pref = st.selectbox(
    "🥗 Dietary Preference",
    ["None", "High Protein", "Low Carb", "Vegetarian"]
)

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if st.button("✨ Generate Meal Plan"):

    if not ingredients.strip():
        st.error("Please enter ingredients.")
        st.stop()

    try:
        weight = float(weight_input)
        height = float(height_input)
    except:
        st.error("Weight and height must be numeric.")
        st.stop()

    agent = CoordinatorAgent()

    progress = st.progress(0)

    progress.progress(10, text="Analyzing ingredients...")
    time.sleep(0.1)

    progress.progress(40, text="Fetching recipes...")
    time.sleep(0.1)

    progress.progress(70, text="Calculating nutrition...")
    time.sleep(0.1)

    result = agent.run(
        ingredients,
        goal,
        weight,
        height,
        diet_pref
    )

    progress.progress(100, text="Done")

    recipes = result.get("recipes", [])
    nutrition = result.get("nutrition", {})

    if not recipes:
        st.warning("No recipes found.")
        st.stop()

    st.success("Meal plan generated!")

    # ---------------------------------------------------------
    # NUTRITION PROFILE
    # ---------------------------------------------------------

    # ---------------------------------------------------------
# NUTRITION PROFILE (FIXED LOGIC)
# ---------------------------------------------------------

    st.header("🥗 Meal Plan Nutrition Summary")

    st.info(
    "Planned calories are based only on the top recommended recipe (1 serving). "
    "They are not the total calories for all suggested recipes or a full-day plan."
    )

    target = safe_number(nutrition.get("target_calories"))

    recipes_list = nutrition.get("recipes", [])
    selected = recipes_list[0] if recipes_list else None

    if selected:
        calories = safe_number(selected.get("calories"))
        protein = safe_number(selected.get("protein"))
        carbs = safe_number(selected.get("carbs"))
        fat = safe_number(selected.get("fat"))

    else:
        calories = safe_number(nutrition.get("estimated_calories"))
        protein = safe_number(nutrition.get("estimated_protein"))
        carbs = safe_number(nutrition.get("estimated_carbs"))
        fat = safe_number(nutrition.get("estimated_fat"))

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Daily Target", f"{target} kcal")
    c2.metric("Planned Calories", f"{calories} kcal")
    c3.metric("Protein", f"{protein} g")
    c4.metric("Carbs", f"{carbs} g")
    c5.metric("Fat", f"{fat} g")

    diff = calories - target

    if diff > 0:
        st.warning(f"{round(diff)} kcal above target")
    else:
        st.success(f"{abs(round(diff))} kcal below target")

    # ---------------------------------------------------------
    # RECIPES
    # ---------------------------------------------------------

    st.header("🍽 Recommended Recipes")

    recipe_nutrition = nutrition.get("recipes", [])

    for r in recipes:

        with st.container():

            left, right = st.columns([1, 2])

            with left:
                if r.get("image"):
                    st.image(r["image"])

            with right:

                if r.get("rank") == 1:
                    st.markdown("⭐ **Top Recommendation**")

                st.subheader(r.get("name", "Unknown Recipe"))

                country = r.get("country", "Unknown")
                flag = COUNTRY_FLAGS.get(country, "🌍")

                st.write(f"{flag} {country}")

                st.metric("Match Score", f"{safe_number(r.get('coverage', 0)):.0f}%")

                matched = safe_list(r.get("matched"))
                missing = safe_list(r.get("missing"))
                additional = safe_list(r.get("additional"))

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("✔ Matched")
                    st.write(", ".join(matched) if matched else "None")

                with col2:
                    st.markdown("✖ Missing")
                    st.write(", ".join(missing) if missing else "None")

                with col3:
                    st.markdown("➕ Additional")
                    st.write(", ".join(additional) if additional else "None")

            # -------------------------------------------------
            # RECIPE DETAILS (FIXED NUTRITION DISPLAY)
            # -------------------------------------------------

            with st.expander("👨‍🍳 Recipe Details"):

                nutrition_match = next(
                    (
                        n for n in recipe_nutrition
                        if normalize_name(n.get("name")) == normalize_name(r.get("name"))
                    ),
                    None
                )

                if nutrition_match:
                    st.markdown("### 🥗 Recipe Nutrition")

                    servings = nutrition_match.get("servings", 2)

                    calories = safe_number(nutrition_match.get("calories"))
                    protein = safe_number(nutrition_match.get("protein"))
                    carbs = safe_number(nutrition_match.get("carbs"))
                    fat = safe_number(nutrition_match.get("fat"))

                    # PER SERVING
                    c1, c2, c3, c4 = st.columns(4)

                    c1.metric("Per Serving kcal", f"{calories} kcal")
                    c2.metric("Protein", f"{protein} g")
                    c3.metric("Carbs", f"{carbs} g")
                    c4.metric("Fat", f"{fat} g")

                    # WHOLE DISH (CLEAR FIX)
                    st.write("---")
                    st.write(f"🍲 Serves: {servings} people")
                    
                st.markdown("### Ingredients")
                for item in r.get("ingredients", []):
                    st.write(f"- {item}")

                st.markdown("### Instructions")
                st.write(r.get("instructions", ""))

            st.divider()

    # ---------------------------------------------------------
    # SHOPPING LIST
    # ---------------------------------------------------------

    st.header("🛒 Smart Grocery List")

    for item in result.get("shopping_list", []):
        st.write(f"- {item}")

    # ---------------------------------------------------------
    # TRACE
    # ---------------------------------------------------------

    with st.expander("🔍 Agent Execution Trace"):
        st.json(result.get("trace", []))