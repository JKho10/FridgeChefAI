import streamlit as st
import time
import re
from agents.coordinator_agent import CoordinatorAgent

st.set_page_config(
    page_title="FridgeChef AI",
    page_icon="🍳",
    layout="wide"
)

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

st.title("🍳 FridgeChef AI")
st.caption("Multi-agent meal intelligence system (Kaggle-style output)")

ingredients = st.text_area(
    "🥕 Ingredients (comma separated)",
    placeholder="Example: chicken, rice, broccoli, carrots"
)
goal = st.selectbox("🎯 Goal", ["Lose Weight", "Maintenance", "Weight Gain"])

st.subheader("🧍 Personal Profile")

weight_unit = st.radio("Weight Unit", ["kg", "lbs"], horizontal=True)
height_unit = st.radio("Height Unit", ["cm", "inches"], horizontal=True)

weight_input = st.text_input("Weight", placeholder="Example: 70")

try:
    weight = float(weight_input)
except:
    weight = 0

height_input = st.text_input("Height", placeholder="Example: 170")

try:
    height = float(height_input)
except:
    height = 0

if weight_unit == "lbs":
    weight *= 0.453592

if height_unit == "inches":
    height *= 2.54

age_input = st.text_input("Age", placeholder="Example: 30")

try:
    age = int(age_input)
except:
    age = 0

sex = st.selectbox("Sex", ["Male", "Female"])
activity_level = st.selectbox(
    "Activity Level",
    ["Sedentary", "Light", "Moderate", "Active", "Very Active"]
)

diet_pref = st.selectbox(
    "Dietary Preference",
    ["None", "High Protein", "Low Carb", "Vegetarian"]
)

if st.button("✨ Generate Meal Plan"):

    if not ingredients.strip():
        st.error("Please enter ingredients.")
        st.stop()

    if weight <= 0:
        st.error("Please enter your weight.")
        st.stop()

    if height <= 0:
        st.error("Please enter your height.")
        st.stop()

    if age <= 0:
        st.error("Please enter your age.")
        st.stop()

    agent = CoordinatorAgent()

    progress = st.progress(0, text="Starting...")

    progress.progress(10, text="Parsing ingredients...")
    time.sleep(0.2)

    progress.progress(25, text="Running safety check...")
    time.sleep(0.2)

    progress.progress(40, text="Generating recipe candidates...")
    result = agent.run(
        ingredients,
        goal,
        weight,
        height,
        age,
        sex,
        activity_level,
        diet_pref
    )

    progress.progress(80, text="Calculating nutrition...")
    time.sleep(0.2)

    progress.progress(95, text="Building grocery list...")
    time.sleep(0.2)

    progress.progress(100, text="Done!")

    recipes = result.get("recipes", [])
    nutrition = result.get("nutrition", {})

    if not recipes:
        st.warning("No recipes found.")
        st.stop()

    st.success("Meal plan generated!")

    st.header("🥗 Recommended Meal Nutrition")

    st.info(
    "ℹ️ Nutrition values shown here are for the top recommended recipe only, "
    "not a complete daily meal plan."
)

    target = safe_number(nutrition.get("target_calories"))

    recipe_list = nutrition.get("recipes", [])
    selected = recipe_list[0] if recipe_list else None

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
    c2.metric("Top Reciple Recommended", f"{calories} kcal")
    c3.metric("Protein", f"{protein} g")
    c4.metric("Carbs", f"{carbs} g")
    c5.metric("Fat", f"{fat} g")

    diff = calories - target

    if diff > 0:
        st.warning(f"{round(diff)} kcal above target")
    else:
        st.success(f"{abs(round(diff))} kcal below target")

    st.header("🍽 Recommended Recipes")

    recipe_nutrition = nutrition.get("recipes", [])

    for r in recipes:

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
                st.write("✔ Matched")
                st.write(", ".join(matched) or "None")

            with col2:
                st.write("✖ Missing")
                st.write(", ".join(missing) or "None")

            with col3:
                st.write("➕ Additional")
                st.write(", ".join(additional) or "None")

        with st.expander("👨‍🍳 Recipe Details"):

            nutrition_match = next(
                (
                    n for n in recipe_nutrition
                    if normalize_name(str(n.get("name", ""))) == normalize_name(str(r.get("name", "")))
                ),
                None
            )

            if nutrition_match:

                servings = nutrition_match.get("servings", 2)

                calories = safe_number(nutrition_match.get("calories"))
                protein = safe_number(nutrition_match.get("protein"))
                carbs = safe_number(nutrition_match.get("carbs"))
                fat = safe_number(nutrition_match.get("fat"))

                total_calories = calories * servings
                total_protein = protein * servings
                total_carbs = carbs * servings
                total_fat = fat * servings

                c1, c2, c3, c4 = st.columns(4)

                c1.metric("Per Serving kcal", f"{calories} kcal")
                c2.metric("Protein", f"{protein} g")
                c3.metric("Carbs", f"{carbs} g")
                c4.metric("Fat", f"{fat} g")

                st.write("---")
                st.write(f"🍲 Serves: {servings}")

                st.write("🍲 Estimated meal totals:")

                st.write(f"{total_calories:.0f} kcal")
                st.write(f"{total_protein:.0f} g protein")
                st.write(f"{total_carbs:.0f} g carbs")
                st.write(f"{total_fat:.0f} g fat")

            st.markdown("### Ingredients")
            for item in r.get("ingredients", []):
                if isinstance(item, dict):
                    st.write(f"- {item.get('measure','')} {item.get('ingredient','')}")
                else:
                    st.write(f"- {item}")

            st.markdown("### Instructions")
            st.write(r.get("instructions", ""))

        st.divider()

    st.header("🛒 Smart Grocery List")

    for item in result.get("shopping_list", []):
        st.write(f"- {item}")

    with st.expander("🔍 Trace"):
        st.json(result.get("trace", []))