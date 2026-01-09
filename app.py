import streamlit as st
import pandas as pd

# ==========================================================
# 1. CONFIGURATION & DATA CONSTANTS
# ==========================================================
st.set_page_config(page_title="Pro MTB Spring Rate Calculator", page_icon="⚙️", layout="centered")

# --- Constants ---
LB_TO_KG = 0.453592
KG_TO_LB = 2.20462
IN_TO_MM = 25.4
MM_TO_IN = 1/25.4
STONE_TO_KG = 6.35029

# --- Data Tables ---
CATEGORY_DATA = {
    "Downcountry": {"travel": 115, "stroke": 45.0, "bias": 60, "base_sag": 28, "progression": 12, "lr_start": 2.75, "desc": "110–120 mm", "bike_mass_def_kg": 12.0},
    "Trail": {"travel": 130, "stroke": 50.0, "bias": 63, "base_sag": 30, "progression": 15, "lr_start": 2.80, "desc": "120–140 mm", "bike_mass_def_kg": 13.5},
    "All-Mountain": {"travel": 145, "stroke": 55.0, "bias": 65, "base_sag": 31, "progression": 18, "lr_start": 2.90, "desc": "140–150 mm", "bike_mass_def_kg": 14.5},
    "Enduro": {"travel": 160, "stroke": 60.0, "bias": 68, "base_sag": 33, "progression": 22, "lr_start": 3.00, "desc": "150–170 mm", "bike_mass_def_kg": 15.5},
    "Long Travel Enduro": {"travel": 175, "stroke": 65.0, "bias": 70, "base_sag": 34, "progression": 25, "lr_start": 3.05, "desc": "170–180 mm", "bike_mass_def_kg": 16.5},
    "Enduro (Race focus)": {"travel": 165, "stroke": 62.5, "bias": 65, "base_sag": 32, "progression": 26, "lr_start": 3.13, "desc": "160–170 mm", "bike_mass_def_kg": 15.8},
    "Downhill (DH)": {"travel": 200, "stroke": 75.0, "bias": 75, "base_sag": 35, "progression": 30, "lr_start": 3.14, "desc": "180–210 mm", "bike_mass_def_kg": 17.5}
}

SKILL_MODIFIERS = {
    "Just starting": {"bias": +4},
    "Beginner": {"bias": +2},
    "Intermediate": {"bias": 0},
    "Advanced": {"bias": -1},
    "Racer": {"bias": -2}
}
SKILL_LEVELS = list(SKILL_MODIFIERS.keys())

COUPLING_COEFFS = {
    "Downcountry": 0.80, "Trail": 0.75, "All-Mountain": 0.70,
    "Enduro": 0.72, "Long Travel Enduro": 0.90,
    "Enduro (Race focus)": 0.78, "Downhill (DH)": 0.95
}

BIKE_WEIGHT_EST = {
    "Downcountry": {"Carbon": [12.2, 11.4, 10.4], "Aluminium": [13.8, 13.1, 12.5]},
    "Trail": {"Carbon": [14.1, 13.4, 12.8], "Aluminium": [15.4, 14.7, 14.0]},
    "All-Mountain": {"Carbon": [15.0, 14.2, 13.5], "Aluminium": [16.2, 15.5, 14.8]},
    "Enduro": {"Carbon": [16.2, 15.5, 14.8], "Aluminium": [17.5, 16.6, 15.8]},
    "Long Travel Enduro": {"Carbon": [16.8, 16.0, 15.2], "Aluminium": [18.0, 17.2, 16.5]},
    "Enduro (Race focus)": {"Carbon": [16.0, 15.2, 14.5], "Aluminium": [17.2, 16.3, 15.5]},
    "Downhill (DH)": {"Carbon": [17.8, 17.0, 16.2], "Aluminium": [19.5, 18.5, 17.5]}
}

SIZE_WEIGHT_MODS = {"XS": -0.5, "S": -0.25, "M": 0.0, "L": 0.3, "XL": 0.6, "XXL": 0.95}

COMMON_STROKES = [37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0, 62.5, 65.0, 70.0, 72.5, 75.0]

# ==========================================================
# 6. UI - CHASSIS (ONLY FIX HERE)
# ==========================================================
st.header("2. Chassis Data")

cat_options = list(CATEGORY_DATA.keys())
cat_labels = [f"{k} ({CATEGORY_DATA[k]['desc']})" for k in cat_options]

selected_idx = st.selectbox(
    "Category",
    range(len(cat_options)),
    format_func=lambda x: cat_labels[x],
    key='category_select'
)
category = cat_options[selected_idx]
defaults = CATEGORY_DATA[category]

col_c1, col_c2 = st.columns(2)

# --- Rear Bias ---
with col_c2:
    cat_def_bias = int(defaults["bias"])
    skill_suggestion = SKILL_MODIFIERS[skill]["bias"]

    if 'rear_bias_slider' not in st.session_state:
        st.session_state.rear_bias_slider = cat_def_bias

    rear_bias_in = st.slider(
        "Base Bias (%)",
        55, 85,
        key="rear_bias_slider",
        label_visibility="collapsed"
    )

    final_bias_calc = rear_bias_in

    st.caption(f"Category Default: **{cat_def_bias}%**")

    if skill_suggestion != 0:
        advice_sign = "+" if skill_suggestion > 0 else ""
        st.info(f"💡 Because you selected **{skill}**, consider applying **{advice_sign}{skill_suggestion}%** bias.")

    # ✅ FIXED LABEL
    st.markdown(f"**Suggested Bias:** :blue-background[{final_bias_calc}%]")

# ==========================================================
# (Everything else remains unchanged)
# ==========================================================
