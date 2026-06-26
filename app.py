import streamlit as st
import re
from agents.coordinator_agent import CoordinatorAgent

#streamlit frontend for fridgechef ai

#This module defines the complete user interface for the meal planning system.
#It handles user input collection, data validation, agent execution, and
#visualization of generated recipes, nutrition information, and grocery lists.

#The app acts as the orchestration layer between the user and the backend
#multi-agent pipeline (coordinator, recipe, nutrition, shopping, safety).

st.set_page_config(
    page_title="FridgeChef AI",
    page_icon="🍳",
    layout="wide"
)

def safe_list(v):
    """
    Safely returns a list or empty list if input is invalid.
    This prevents runtime errors when backend fields are missing or malformed.
    """
    return v if isinstance(v, list) else []

def safe_number(v):
    """
    Extracts and normalizes numeric values from mixed input types.
    Supports:
    - int/float values
    - numeric strings
    - strings containing embedded numbers

    returns 0 if parsing fails.
    """
    try:
        if v is None:
            return 0
        if isinstance(v, (int, float)):
            return round(float(v), 1)
        match = re.search(r"(\d+\.?\d*)", str(v))
        return round(float(match.group(1)), 1) if match else 0
    except:
        return 0

def normalize_name(name):
    """
    Normalizes recipe or ingredient names for comparison.
    This ensures consistent matching between nutrition and recipe outputs.
    """
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
    "Jamaican": "🇯🇲"
}

with st.sidebar:
    st.title("FridgeChef AI")
    st.caption("Multi-agent system overview")

    st.write("🧠 Pipeline:")
    st.write("- Safety filtering")
    st.write("- Recipe ranking (coverage scoring)")
    st.write("- Nutrition estimation (TDEE model)")
    st.write("- Grocery synthesis")
    st.write("- MCP tool abstraction layer")

    st.divider()

    st.write("⚙️ Design:")
    st.write("- Rule-based agents")
    st.write("- Deterministic scoring")
    st.write("- No LLM dependency")

st.title("🍳 FridgeChef AI")
st.caption("Multi-agent MCP-based meal planning system with recipe ranking, nutrition estimation, and grocery synthesis")

ingredients = st.text_area("🥕 Ingredients", placeholder="e.g. chicken, rice, eggs, spinach")
goal = st.selectbox("🎯 Goal", ["Lose Weight", "Maintenance", "Weight Gain"])

st.subheader("🧍 Personal Profile")

weight_unit = st.radio("Weight Unit", ["kg", "lbs"], horizontal=True)
height_unit = st.radio("Height Unit", ["cm", "inches"], horizontal=True)

weight_input = st.text_input("Weight", placeholder="e.g. 70 (kg or lbs depending on selection)")
height_input = st.text_input("Height", placeholder="e.g. 175 (cm or inches)")
age_input = st.text_input("Age", placeholder="e.g. 25")

weight = float(weight_input) if weight_input else 0
height = float(height_input) if height_input else 0
age = int(age_input) if age_input else 0

if weight_unit == "lbs":
    weight *= 0.453592

if height_unit == "inches":
    height *= 2.54

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

    if weight <= 0 or height <= 0 or age <= 0:
        st.error("Please complete weight, height, and age.")
        st.stop()

    agent = CoordinatorAgent()

    progress = st.progress(0, text="Starting...")

    with st.spinner("Running multi-agent pipeline..."):
        progress.progress(30, text="Generating recipes...")

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

        progress.progress(100, text="Done!")

    recipes = result.get("recipes", [])
    nutrition = result.get("nutrition", {})

    if not recipes:
        st.warning("No recipes found.")
        st.stop()

    st.success("Meal plan generated!")

    st.header("🥗 Recommended Meal Nutrition")
    st.info("Values shown are for the top recipe only.")

    recipe_nutrition = nutrition.get("recipes", [])
    selected = recipe_nutrition[0] if recipe_nutrition else None

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

    target = safe_number(nutrition.get("target_calories"))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Daily Target", f"{target} kcal")
    c2.metric("Top Recipe", f"{calories} kcal")
    c3.metric("Protein", f"{protein} g")
    c4.metric("Carbs", f"{carbs} g")
    c5.metric("Fat", f"{fat} g")

    diff = calories - target
    if diff > 0:
        st.warning(f"{round(diff)} kcal above target")
    else:
        st.success(f"{abs(round(diff))} kcal below target")

    st.header("🍽 Recommended Recipes")

    for idx, r in enumerate(recipes):

        left, right = st.columns([1, 2])

        with left:
            if r.get("image"):
                st.image(r["image"])

        with right:
            if r.get("rank") == 1:
                st.markdown("⭐ Top Recommendation")

            st.subheader(r.get("name", "Unknown"))
            st.write(f"{COUNTRY_FLAGS.get(r.get('country',''), '🌍')} {r.get('country','Unknown')}")
            st.metric("Match Score", f"{safe_number(r.get('coverage',0)):.0f}%")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("✔ Matched")
                st.write(", ".join(safe_list(r.get("matched"))) or "None")

            with col2:
                st.write("✖ Missing")
                st.write(", ".join(safe_list(r.get("missing"))) or "None")

            with col3:
                st.write("➕ Additional")
                st.write(", ".join(safe_list(r.get("additional"))) or "None")

        with st.expander("👨‍🍳 Recipe Details"):

            match = next(
                (n for n in recipe_nutrition
                 if normalize_name(n.get("name","")) == normalize_name(r.get("name",""))),
                None
            )

            if match:
                servings = max(1, int(match.get("servings", 2)))

                cal = safe_number(match.get("calories"))
                pro = safe_number(match.get("protein"))
                carb = safe_number(match.get("carbs"))
                fatv = safe_number(match.get("fat"))

                total_cal = cal * servings
                total_pro = pro * servings
                total_carb = carb * servings
                total_fat = fatv * servings

                c1, c2, c3, c4 = st.columns(4)

                c1.metric("Per Serving kcal", f"{cal} kcal")
                c2.metric("Protein", f"{pro} g")
                c3.metric("Carbs", f"{carb} g")
                c4.metric("Fat", f"{fatv} g")

                st.write(f"🍲 Serves: {servings}")
                st.write(f"{total_cal:.0f} kcal total")
                st.write(f"{total_pro:.0f} g protein")
                st.write(f"{total_carb:.0f} g carbs")
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