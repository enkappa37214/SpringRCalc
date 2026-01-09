import streamlit as st
import math
import pandas as pd

# ==========================================================
# STREAMLIT CONFIG
# ==========================================================
st.set_page_config(
    page_title="MTB Coil Spring Rate Calculator",
    page_icon="⚙️",
    layout="centered"
)

# ==========================================================
# CONSTANTS & DEFAULT TABLES
# ==========================================================
LB_PER_KG = 2.20462
MM_PER_IN = 25.4

CATEGORY_DEFAULTS = {
    "Downcountry": {"travel": 115, "stroke": 45, "rear_bias": 0.60, "bike_mass": 12.5},
    "Trail": {"travel": 130, "stroke": 50, "rear_bias": 0.63, "bike_mass": 13.8},
    "All-Mountain": {"travel": 145, "stroke": 55, "rear_bias": 0.65, "bike_mass": 14.8},
    "Enduro": {"travel": 160, "stroke": 62.5, "rear_bias": 0.68, "bike_mass": 15.8},
    "Long Travel Enduro": {"travel": 175, "stroke": 65, "rear_bias": 0.70, "bike_mass": 16.5},
    "Enduro (Race focus)": {"travel": 165, "stroke": 62.5, "rear_bias": 0.65, "bike_mass": 15.5},
    "Downhill (DH)": {"travel": 200, "stroke": 75, "rear_bias": 0.75, "bike_mass": 18.5},
}

SKILL_BIAS_MOD = {
    "Just starting": 0.04,
    "Beginner": 0.02,
    "Intermediate": 0.0,
    "Advanced": -0.01,
    "Racer": -0.02
}

SKILL_SAG_MOD = {
    "Just starting": 1.5,
    "Beginner": 1.0,
    "Intermediate": 0.0,
    "Advanced": -0.5,
    "Racer": -1.0
}

GEAR_COUPLING = {
    "Downcountry": 0.80,
    "Trail": 0.78,
    "All-Mountain": 0.70,
    "Enduro": 0.72,
    "Long Travel Enduro": 0.90,
    "Enduro (Race focus)": 0.78,
    "Downhill (DH)": 0.95
}

SAG_BASE = {
    "Downcountry": 28,
    "Trail": 30,
    "All-Mountain": 31,
    "Enduro": 33,
    "Long Travel Enduro": 34,
    "Enduro (Race focus)": 32,
    "Downhill (DH)": 35
}

SPRINDEX_RANGES = [
    ("XC / Trail", 55, 380, 760),
    ("Enduro", 65, 340, 700),
    ("DH", 75, 290, 630)
]

# ==========================================================
# PHYSICS BLOCKS
# ==========================================================
def compute_effective_mass(rider, gear, coupling, bike, rear_bias, unsprung):
    system_mass = rider + (gear * coupling) + bike
    rear_sprung = (system_mass * rear_bias) - unsprung
    return rear_sprung * LB_PER_KG

def mean_leverage_ratio(lr_start, lr_end=None, progression=None):
    if progression is not None:
        lr_end = lr_start * (1 - progression)
    return (lr_start + lr_end) / 2

def spring_rate_lbs(rear_load_lbs, lr_mean, stroke_mm, sag_pct):
    sag_in = (stroke_mm / MM_PER_IN) * (sag_pct / 100)
    return (rear_load_lbs * lr_mean) / sag_in

def round_spring(rate):
    return int(round(rate / 25) * 25)

# ==========================================================
# UI — INPUTS
# ==========================================================
st.title("MTB Coil Spring Rate Calculator")

# --- Units ---
st.header("1. Units")
mass_unit = st.radio("Mass Units", ["Global (kg)", "North America (lbs)", "UK Hybrid"])
length_unit = st.radio("Suspension Units", ["Metric (mm)", "Imperial (in)"])

# --- Rider ---
st.header("2. Rider Profile")
skill = st.selectbox("Rider Skill", list(SKILL_BIAS_MOD.keys()))

if mass_unit == "UK Hybrid":
    st.write("Rider Weight")
    st_col1, st_col2 = st.columns(2)
    stone = st_col1.number_input("Stone", 5, 25, 11)
    pounds = st_col2.number_input("Pounds", 0, 13, 6)
    rider_mass = ((stone * 14) + pounds) / LB_PER_KG
else:
    rider_input = st.number_input(
        "Rider Weight with gear removed",
        45.0, 120.0, 72.0
    )
    rider_mass = rider_input / LB_PER_KG if mass_unit == "North America (lbs)" else rider_input

# --- Category ---
st.header("3. Bike Category")
category = st.selectbox("Bike Application", list(CATEGORY_DEFAULTS.keys()))
defaults = CATEGORY_DEFAULTS[category]

# --- Bike Mass ---
estimate_bike = st.toggle("Estimate Bike Weight", True)
if estimate_bike:
    bike_mass = defaults["bike_mass"]
else:
    bike_input = st.number_input("Bike Weight", 10.0, 25.0, defaults["bike_mass"])
    bike_mass = bike_input / LB_PER_KG if mass_unit == "North America (lbs)" else bike_input

# --- Gear ---
gear_mass = st.number_input("Gear Weight", 0.0, 10.0, 4.0)
if mass_unit == "North America (lbs)":
    gear_mass /= LB_PER_KG

coupling = GEAR_COUPLING[category]

# --- Rear Bias ---
base_bias = defaults["rear_bias"]
rear_bias = base_bias + SKILL_BIAS_MOD[skill]
rear_bias = st.slider("Rear Weight Bias (%)", 55, 75, int(rear_bias * 100)) / 100

# --- Unsprung ---
estimate_unsprung = st.toggle("Estimate Unsprung Mass", True)
if estimate_unsprung:
    unsprung = 4.5
else:
    unsprung = st.number_input("Unsprung Mass (kg)", 2.0, 8.0, 4.5)

# --- Suspension ---
st.header("4. Suspension & Kinematics")
if length_unit == "Metric (mm)":
    travel = st.number_input("Rear Wheel Travel (mm)", 100, 220, defaults["travel"])
    stroke = st.number_input("Shock Stroke (mm)", 40.0, 80.0, defaults["stroke"])
else:
    travel = st.number_input("Rear Wheel Travel (in)", 4.0, 9.0, defaults["travel"] / MM_PER_IN) * MM_PER_IN
    stroke = st.number_input("Shock Stroke (in)", 1.5, 3.5, defaults["stroke"] / MM_PER_IN) * MM_PER_IN

advanced = st.checkbox("Advanced Kinematics")

if advanced:
    lr_start = st.number_input("Leverage Ratio Start", 2.0, 4.0, 2.8)
    mode = st.radio("Define progression via:", ["LR End", "Progression %"])
    if mode == "LR End":
        lr_end = st.number_input("Leverage Ratio End", 1.5, lr_start, 2.3)
        progression = None
    else:
        progression = st.number_input("Progression (%)", 5.0, 35.0, 20.0) / 100
        lr_end = None
else:
    lr_start = travel / stroke
    lr_end = None
    progression = 0.20

lr_mean = mean_leverage_ratio(lr_start, lr_end, progression)

# --- Sag ---
base_sag = SAG_BASE[category]
target_sag = base_sag + SKILL_SAG_MOD[skill]

# ==========================================================
# CALCULATION
# ==========================================================
rear_load = compute_effective_mass(
    rider_mass, gear_mass, coupling,
    bike_mass, rear_bias, unsprung
)

raw_rate = spring_rate_lbs(rear_load, lr_mean, stroke, target_sag)
final_rate = round_spring(raw_rate)

# ==========================================================
# OUTPUTS
# ==========================================================
st.header("Results")

st.metric("Recommended Spring Rate", f"{final_rate} lbs/in")
st.metric("Target Sag", f"{target_sag:.1f}%")

# --- Preload Table ---
rows = []
for turns in [0, 0.5, 1, 1.5, 2, 2.5, 3]:
    sag_adj = target_sag - (turns * 1.0)
    rows.append({"Preload (turns)": turns, "Sag %": round(sag_adj, 1)})

df = pd.DataFrame(rows)
st.subheader("Preload vs Sag")
st.dataframe(df, use_container_width=True)

# --- Sprindex ---
st.subheader("Sprindex Guidance")
for name, max_stroke, lo, hi in SPRINDEX_RANGES:
    if stroke <= max_stroke:
        if lo <= final_rate <= hi:
            st.success(f"{name}: Compatible (Target in lower-mid range recommended)")
        break

# --- Disclaimers ---
st.markdown("""
**Notes & Disclaimers**
- Coil rates vary ±5% by manufacturer.
- Spring stroke must exceed shock stroke to avoid coil bind.
- Verify spring inner diameter compatibility with your shock.
""")
