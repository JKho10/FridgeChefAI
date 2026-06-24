import streamlit as st
from agents.coordinator_agent import CoordinatorAgent
import time

country_flags = {
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
    "India": "🇮🇳",
    "Thai": "🇹🇭",
    "Vietnamese": "🇻🇳",
    "Malaysian": "🇲🇾",
    "Turkish": "🇹🇷",
    "Jamaican": "🇯🇲"
}

st.set_page_config(
    page_title="FridgeChef AI",
    layout="wide"
)

st.title("🍳 FridgeChef AI")
st.caption(
    "Multi-agent AI system for personalized meal planning using ingredient intelligence, nutrition modeling, and MCP-based tools"
)

# User input 
ingredients = st.text_area(
    "🥕 Enter ingredients (comma separated)",
    placeholder="chicken, rice, eggs"
)

goal = st.selectbox(
    "🎯 Select your goal",
    ["Lose Weight", "Maintenance", "Weight Gain"]
)

st.subheader("🧍 Personal Profile")

weight_input = st.text_input("Weight (kg)", placeholder="e.g. 70")
height_input = st.text_input("Height (cm)", placeholder="e.g. 170")

diet_pref = st.selectbox(
    "🥗 Dietary Preference",
    ["None", "High Protein", "Low Carb", "Vegetarian"]
)

if st.button("✨ Generate Meal Plan"):

    # Basic input validation
    if not ingredients.strip():
        st.error("Please enter ingredients.")
        st.stop()

    try:
        weight = float(weight_input)
        height = float(height_input)
    except:
        st.error("Please enter valid numeric values for weight and height.")
        st.stop()

    if weight <= 0 or height <= 0:
        st.error("Weight and height must be greater than 0.")
        st.stop()

    # Progress indicator for multi-step workflow
    progress = st.progress(0, text="Validating input safety...")

    time.sleep(0.2)
    progress.progress(30, text="Analyzing ingredients and strategy...")

    time.sleep(0.2)
    progress.progress(60, text="Retrieving and ranking recipes via MCP tools...")

    # Run Agent Pipeline
    agent = CoordinatorAgent()
    result = agent.run(ingredients, goal, weight, height, diet_pref)

    progress.progress(90, text="Computing nutrition and shopping list...")

    time.sleep(0.2)
    progress.progress(100, text="Finalizing results...")

    recipes = result.get("recipes", [])

    if not recipes:
        st.warning("No recipes found. Try different ingredients.")
        st.stop()

    st.success("Meal plan generated!")

    # Nutrition summary
    st.subheader("🥗 Nutrition Profile")

    nutrition = result.get("nutrition", {})

    estimated = nutrition.get("estimated_calories", 0)
    target = nutrition.get("target_calories", 0)

    st.write({
        "Target Calories": target,
        "Estimated Calories": estimated,
        "Protein (g)": nutrition.get("estimated_protein", 0),
        "Diet Preference": nutrition.get("dietary_preference", diet_pref)
    })

    diff = estimated - target

    if target > 0:
        if diff > 0:
            st.warning(f"⚠️ {diff} calories above target")
        else:
            st.success(f"✔ {abs(diff)} calories under target")

    # Execution trace
    with st.expander("🔍 Agent Execution Trace"):
        st.json(result.get("trace", []))

    # Explanation
    st.subheader("💡 AI Reasoning")
    reason = result.get("reason", "")

    if reason:
        st.write(reason)
    else:
        st.info("No explanation was generated for this run.")

    # Results
    st.markdown("## 🍽 Recommended Meal Plan")

    for r in recipes:

        with st.container():

            col1, col2 = st.columns([1, 2])

            # IMAGE
            with col1:
                st.image(r.get("image"), use_container_width=True)

            # DETAILS
            with col2:

                if r.get("rank") == 1:
                    st.markdown("⭐ **Top AI Recommendation**")

                st.subheader(r.get("name", "Unknown Recipe"))

                country = r.get("country", "Unknown")
                flag = country_flags.get(country, "🌍")

                st.markdown(f"{flag} **{country}**")

                coverage = r.get("coverage", 0)

                st.metric("Ingredient Match", f"{coverage}%")

                matched = r.get("matched", [])
                missing = r.get("missing", [])

                st.caption(f"Uses {len(matched)} ingredient(s) from your fridge")

                if coverage == 100:
                    st.success("🟢 Perfect Match")
                elif coverage >= 70:
                    st.info("🟡 Strong Match")
                elif coverage >= 40:
                    st.warning("🟠 Medium Match")
                else:
                    st.error("🔴 Low Match")

                st.write(r.get("why", "").split("\n")[0])

                # Matched / Missing
                #colA, colB = st.columns(2)
                additional = r.get("additional", [])

                colA, colB, colC = st.columns(3)

                with colA:
                    st.markdown("✔ Matched")
                    st.write(", ".join(matched) if matched else "None")

                with colB:
                    st.markdown("✖ Missing (user input not in recipe)")
                    st.write(", ".join(missing) if missing else "None")

                with colC:
                    st.markdown("➕ Additional Needed (recipe requires)")
                    st.write(", ".join(additional) if additional else "None")

            # Full Recipe Details
            with st.expander("👨‍🍳 View Full Recipe"):
                st.markdown("### Ingredients")
                for item in r.get("ingredients", []):
                    st.markdown(f"- {item}")

                st.markdown("### Instructions")
                st.write(r.get("instructions", ""))

            st.divider()

    # Shopping list
    st.subheader("🛒 Smart Grocery List")
    st.write(result.get("shopping_list", []))