import streamlit as st

# =========================================================
# CONSTANTS & DEFAULTS
# =========================================================

SKILL_MODIFIERS = {
    "Just starting": {"bias": 0.04},
    "Beginner": {"bias": 0.02},
    "Intermediate": {"bias": 0.00},
    "Advanced": {"bias": -0.01},
    "Racer": {"bias": -0.02},
}

CATEGORY_DEFAULTS = {
    "Downcountry": {"travel": 120, "stroke": 45, "bias": 0.60, "bike_mass": 13.5},
    "Trail": {"travel": 140, "stroke": 50, "bias": 0.63, "bike_mass": 14.5},
    "All-Mountain": {"travel": 150, "stroke": 55, "bias": 0.65, "bike_mass": 15.5},
    "Enduro": {"travel": 165, "stroke": 60, "bias": 0.68, "bike_mass": 16.5},
    "Long Travel Enduro": {"travel": 180, "stroke": 65, "bias": 0.70, "bike_mass": 17.5},
    "Enduro (Race focus)": {"travel": 165, "stroke": 60, "bias": 0.65, "bike_mass": 16.0},
    "Downhill (DH)": {"travel": 200, "stroke": 75, "bias": 0.75, "bike_mass": 18.5},
}

AVAILABLE_STROKES_MM = [45, 50, 55, 60, 62.5, 65, 70, 75]

# =========================================================
# PHYSICS FUNCTIONS
# =========================================================

def compute_mean_leverage_ratio(lr_start, lr_end=None, progression_pct=None):
    if lr_end is not None:
        return (lr_start + lr_end) / 2
    if progression_pct is not None:
        lr_end = lr_start * (1 - progression_pct / 100)
        return (lr_start + lr_end) / 2
    return lr_start


def compute_rear_sprung_weight_lbs(
    rider_mass_kg,
    gear_mass_kg,
    coupling,
    bike_mass_kg,
    rear_bias,
    unsprung_mass_kg,
):
    effective_rider_mass = rider_mass_kg + (gear_mass_kg * coupling)
    total_mass = effective_rider_mass + bike_mass_kg
    rear_sprung_mass = (total_mass * rear_bias) - unsprung_mass_kg
    return rear_sprung_mass * 2.20462


def compute_spring_rate(
    rear_weight_lbs,
    mean_lr,
    stroke_mm,
    sag_percent,
):
    stroke_in = stroke_mm / 25.4
    sag_in = stroke_in * (sag_percent / 100)
    return (rear_weight_lbs * mean_lr) / sag_in


# =========================================================
# STREAMLIT UI
# =========================================================

st.title("MTB Coil Spring Rate Calculator")

# ---------------- Rider ----------------

st.header("Rider")

skill = st.selectbox(
    "Rider Skill",
    ["Just starting", "Beginner", "Intermediate", "Advanced", "Racer"],
)

skill_suggestion = SKILL_MODIFIERS[skill]["bias"]

rider_mass = st.number_input(
    "Rider Body Weight (kg)",
    min_value=40.0,
    max_value=130.0,
    value=75.0,
    step=0.5,
)

gear_mass = st.number_input(
    "Gear Weight (kg)",
    min_value=0.0,
    max_value=10.0,
    value=4.0,
    step=0.5,
)

coupling = st.slider(
    "Gear Coupling Coefficient",
    min_value=0.6,
    max_value=1.0,
    value=0.75,
    step=0.01,
)

# ---------------- Bike ----------------

st.header("Bike")

category = st.selectbox("Bike Category", list(CATEGORY_DEFAULTS.keys()))
defaults = CATEGORY_DEFAULTS[category]

bike_mass = st.number_input(
    "Bike Weight (kg)",
    min_value=10.0,
    max_value=25.0,
    value=float(defaults["bike_mass"]),
    step=0.5,
)

rear_bias = st.slider(
    "Suggested Bias (%)",
    min_value=55,
    max_value=75,
    value=int((defaults["bias"] + skill_suggestion) * 100),
    step=1,
) / 100.0

unsprung_mass = st.number_input(
    "Unsprung Mass (kg)",
    min_value=0.5,
    max_value=5.0,
    value=2.5,
    step=0.1,
)

# ---------------- Suspension ----------------

st.header("Suspension")

travel = st.number_input(
    "Rear Wheel Travel (mm)",
    min_value=100,
    max_value=220,
    value=int(defaults["travel"]),
    step=5,
)

stroke = st.selectbox(
    "Shock Stroke (mm)",
    AVAILABLE_STROKES_MM,
    index=AVAILABLE_STROKES_MM.index(defaults["stroke"]),
)

advanced_kin = st.checkbox("Advanced Kinematics")

if advanced_kin:
    lr_start = st.number_input(
        "Leverage Ratio Start",
        min_value=1.5,
        max_value=4.0,
        value=2.6,
        step=0.05,
    )
    lr_end = st.number_input(
        "Leverage Ratio End",
        min_value=1.5,
        max_value=4.0,
        value=2.3,
        step=0.05,
    )
    mean_lr = compute_mean_leverage_ratio(lr_start, lr_end=lr_end)
else:
    mean_lr = travel / stroke

sag_percent = st.slider(
    "Target Sag (%)",
    min_value=25,
    max_value=37,
    value=33,
    step=1,
)

spring_type = st.selectbox(
    "Spring Type",
    ["Default Category (Linear)", "Sprindex", "Progressive"],
)

# ---------------- Calculation ----------------

rear_weight_lbs = compute_rear_sprung_weight_lbs(
    rider_mass,
    gear_mass,
    coupling,
    bike_mass,
    rear_bias,
    unsprung_mass,
)

raw_rate = compute_spring_rate(
    rear_weight_lbs,
    mean_lr,
    stroke,
    sag_percent,
)

recommended_rate = round(raw_rate / 25) * 25

# ---------------- Results ----------------

st.header("Results")

st.metric("Raw Calculated Spring Rate (lbs/in)", f"{raw_rate:.1f}")
st.metric("Recommended Spring Rate (lbs/in)", f"{recommended_rate}")

st.caption(
    "Note: Rounded to nearest 25 lbs. Verify spring stroke and inner diameter compatibility."
)
