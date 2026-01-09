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
    "Downcountry": {
        "travel": 115, "stroke": 45.0, "bias": 60, 
        "progression": 12, "lr_start": 3.19, "lr_end": 2.81,
        "desc": "110–120mm | Efficient climbing",
        "bike_mass_def_kg": 12.0
    },
    "Trail": {
        "travel": 130, "stroke": 50.0, "bias": 63, 
        "progression": 15, "lr_start": 2.92, "lr_end": 2.48,
        "desc": "120–140mm | Versatile all-rounder",
        "bike_mass_def_kg": 13.5
    },
    "All-Mountain": {
        "travel": 145, "stroke": 55.0, "bias": 65, 
        "progression": 18, "lr_start": 3.00, "lr_end": 2.46,
        "desc": "140–150mm | Tech backcountry",
        "bike_mass_def_kg": 14.5
    },
    "Enduro": {
        "travel": 160, "stroke": 60.0, "bias": 68, 
        "progression": 22, "lr_start": 3.00, "lr_end": 2.34,
        "desc": "150–170mm | Aggressive descending",
        "bike_mass_def_kg": 15.5
    },
    "Long Travel Enduro": {
        "travel": 175, "stroke": 65.0, "bias": 70, 
        "progression": 25, "lr_start": 3.00, "lr_end": 2.25,
        "desc": "170–180mm | Near-DH capability",
        "bike_mass_def_kg": 16.5
    },
    "Enduro (Race focus)": {
        "travel": 165, "stroke": 62.5, "bias": 65, 
        "progression": 26, "lr_start": 3.13, "lr_end": 2.32,
        "desc": "160–170mm | Speed/tracking focus",
        "bike_mass_def_kg": 15.8
    },
    "Downhill (DH)": {
        "travel": 200, "stroke": 75.0, "bias": 75, 
        "progression": 30, "lr_start": 3.14, "lr_end": 2.20,
        "desc": "180–210mm | Gravity focus",
        "bike_mass_def_kg": 17.5
    }
}

# Define options list globally so it is accessible to callbacks
CAT_OPTIONS = list(CATEGORY_DATA.keys())

SKILL_MODIFIERS = {
    "Just starting": {"bias": +4, "sag_mod": 1.5},
    "Beginner":      {"bias": +2, "sag_mod": 1.0},
    "Intermediate":  {"bias": 0,  "sag_mod": 0.0},
    "Advanced":      {"bias": -1, "sag_mod": -0.5},
    "Racer":         {"bias": -2, "sag_mod": -1.0}
}

COUPLING_COEFFS = {
    "Downcountry": 0.80, "Trail": 0.75, "All-Mountain": 0.70,
    "Enduro": 0.72, "Long Travel Enduro": 0.90, 
    "Enduro (Race focus)": 0.78, "Downhill (DH)": 0.95
}

BIKE_WEIGHT_EST = {
    "Downcountry": {"Carbon": [12.2, 11.4, 10.4], "Aluminium": [13.8, 13.1, 12.5]},
    "Trail":       {"Carbon": [14.1, 13.4, 12.8], "Aluminium": [15.4, 14.7, 14.0]},
    "All-Mountain":{"Carbon": [15.0, 14.2, 13.5], "Aluminium": [16.2, 15.5, 14.8]},
    "Enduro":      {"Carbon": [16.2, 15.5, 14.8], "Aluminium": [17.5, 16.6, 15.8]},
    "Long Travel Enduro": {"Carbon": [16.8, 16.0, 15.2], "Aluminium": [18.0, 17.2, 16.5]},
    "Enduro (Race focus)": {"Carbon": [16.0, 15.2, 14.5], "Aluminium": [17.2, 16.3, 15.5]},
    "Downhill (DH)": {"Carbon": [17.8, 17.0, 16.2], "Aluminium": [19.5, 18.5, 17.5]}
}

SIZE_WEIGHT_MODS = {"XS": -0.5, "S": -0.25, "M": 0.0, "L": 0.3, "XL": 0.6, "XXL": 0.95}

SPRINDEX_DATA = {
    "XC/Trail (55mm)": {"max_stroke": 55, "ranges": ["380-430", "430-500", "490-560", "550-610", "610-690", "650-760"]},
    "Enduro (65mm)":   {"max_stroke": 65, "ranges": ["340-380", "390-430", "450-500", "500-550", "540-610", "610-700"]},
    "DH (75mm)":       {"max_stroke": 75, "ranges": ["290-320", "340-370", "400-440", "450-490", "510-570", "570-630"]}
}

# ==========================================================
# 2. HELPER FUNCTIONS
# ==========================================================
def estimate_unsprung(wheel_tier, frame_mat):
    base = 1.0 # Drivetrain/Brakes
    wheels = {"Light": 1.7, "Standard": 2.3, "Heavy": 3.0}[wheel_tier]
    swingarm = 0.4 if frame_mat == "Carbon" else 0.7
    return base + wheels + swingarm

def recommend_spring_type(progression_pct):
    if progression_pct < 15:
        return "Progressive Coil", f"Frame is linear ({progression_pct:.1f}% progression). Progressive spring recommended to prevent bottom-out."
    else:
        return "Standard Steel (Linear)", f"Frame is progressive ({progression_pct:.1f}%). Linear spring will work well."

# ==========================================================
# 3. SESSION STATE & CALLBACKS
# ==========================================================
if 'last_category' not in st.session_state:
    st.session_state.last_category = None
if 'rear_bias_slider' not in st.session_state:
    st.session_state.rear_bias_slider = 65 

# Callback: Update Bias when Category changes
def update_bias_from_category():
    # .category_select now returns the String Key (e.g., "Downcountry")
    cat = st.session_state.category_select
    if cat != st.session_state.last_category:
        defaults = CATEGORY_DATA[cat]
        st.session_state.rear_bias_slider = int(defaults["bias"])
        st.session_state.last_category = cat

# Callback: Reset Button
def reset_chassis():
    for key in ['bike_weight_man', 'rear_bias_slider']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.last_category = None 

# ==========================================================
# 4. CONFIG SIDEBAR
# ==========================================================
st.sidebar.header("⚙️ Configuration")
unit_mass = st.sidebar.radio("Rider/Bike Units", ["North America (lbs)", "Global (kg)", "UK Hybrid (st & kg)"])
unit_len = st.sidebar.radio("Suspension Units", ["Millimetres (mm)", "Inches (\")"])

# ==========================================================
# 5. UI - RIDER
# ==========================================================
st.title("Pro MTB Spring Rate Calculator")

st.header("1. Rider Profile")
col_r1, col_r2 = st.columns(2)

with col_r1:
    skill = st.selectbox("Rider Skill", list(SKILL_MODIFIERS.keys()), index=2)
    
with col_r2:
    if unit_mass == "UK Hybrid (st & kg)":
        stone = st.number_input("Rider Weight (st)", 5.0, 20.0, 11.0, 0.5)
        lbs_rem = st.number_input("Rider Weight (+lbs)", 0.0, 13.9, 0.0, 1.0)
        rider_kg = (stone * STONE_TO_KG) + (lbs_rem * LB_TO_KG)
        st.caption(f"Total: {rider_kg:.1f} kg")
    elif unit_mass == "North America (lbs)":
        rider_in = st.number_input("Rider Weight (lbs)", 90.0, 280.0, 160.0, 1.0)
        rider_kg = rider_in * LB_TO_KG
    else:
        rider_in = st.number_input("Rider Weight (kg)", 40.0, 130.0, 75.0, 0.5)
        rider_kg = rider_in

    # Gear Weight
    gear_label = "Gear Weight (lbs)" if unit_mass == "North America (lbs)" else "Gear Weight (kg)"
    gear_def = 5.0 if unit_mass == "North America (lbs)" else 2.5
    gear_in = st.number_input(gear_label, 0.0, 25.0, gear_def, 0.5)
    gear_kg = gear_in * LB_TO_KG if "lbs" in unit_mass else gear_in

# ==========================================================
# 6. UI - CHASSIS
# ==========================================================
st.header("2. Chassis Data")

# FIX: Passed CAT_OPTIONS directly and formatted the string for display.
category = st.selectbox(
    "Category", 
    options=CAT_OPTIONS, 
    format_func=lambda x: f"{x} ({CATEGORY_DATA[x]['desc']})",
    key='category_select',
    on_change=update_bias_from_category
)
defaults = CATEGORY_DATA[category]

st.button("Reset Chassis to Category Defaults", on_click=reset_chassis)

col_c1, col_c2 = st.columns(2)

# --- Bike Weight ---
with col_c1:
    weight_mode = st.radio("Bike Weight Mode", ["Manual Input", "Estimate"], horizontal=True)
    if weight_mode == "Estimate":
        mat = st.selectbox("Frame Material", ["Carbon", "Aluminium"])
        level = st.selectbox("Build Level", ["Entry-Level", "Mid-Level", "High-End"])
        size = st.selectbox("Size", list(SIZE_WEIGHT_MODS.keys()), index=2)
        
        # Estimation Logic
        level_idx = {"Entry-Level": 0, "Mid-Level": 1, "High-End": 2}[level]
        base_w = BIKE_WEIGHT_EST[category][mat][level_idx]
        est_w = base_w + SIZE_WEIGHT_MODS[size]
        
        st.info(f"Estimated: {est_w:.2f} kg ({est_w * KG_TO_LB:.1f} lbs)")
        bike_kg = est_w
    else:
        is_lbs = unit_mass == "North America (lbs)"
        lbl = "Bike Weight (lbs)" if is_lbs else "Bike Weight (kg)"
        def_w_kg = defaults.get("bike_mass_def_kg", 14.5)
        def_w_val = def_w_kg * KG_TO_LB if is_lbs else def_w_kg
        
        w_in = st.number_input(lbl, 5.0, 60.0, float(def_w_val), 0.1, key="bike_weight_man")
        bike_kg = w_in * LB_TO_KG if is_lbs else w_in

# --- Rear Bias ---
with col_c2:
    skill_bias_mod = SKILL_MODIFIERS[skill]["bias"]
    
    # Initialize slider state if missing (safety check)
    if 'rear_bias_slider' not in st.session_state:
        st.session_state.rear_bias_slider = int(defaults["bias"])
        
    if skill in ["Just starting", "Beginner"]:
        st.caption("🔒 Bias range constrained for safety.")
    
    # The Slider
    rear_bias_in = st.slider(
        "Rear Weight Bias (%)", 
        55, 75, 
        key="rear_bias_slider" 
    )
    
    final_bias_calc = rear_bias_in + skill_bias_mod
    st.caption(f"Skill Modifier ({skill}): {skill_bias_mod:+.0f}%")
    st.caption(f"**Effective Bias:** {final_bias_calc}%")

# --- Unsprung Mass ---
with col_c1:
    unsprung_mode = st.toggle("Estimate Unsprung Mass", value=True)
    if unsprung_mode:
        u_tier = st.selectbox("Wheelset Tier", ["Light", "Standard", "Heavy"], index=1)
        u_mat = st.selectbox("Rear Triangle", ["Carbon", "Aluminium"], index=1)
        unsprung_kg = estimate_unsprung(u_tier, u_mat)
        st.caption(f"Est: {unsprung_kg:.1f} kg")
    else:
        is_lbs = unit_mass == "North America (lbs)"
        lbl_u = "Unsprung (lbs)" if is_lbs else "Unsprung (kg)"
        u_def = 9.0 if is_lbs else 4.0
        u_in = st.number_input(lbl_u, 0.0, 20.0, u_def, 0.1)
        unsprung_kg = u_in * LB_TO_KG if is_lbs else u_in

# ==========================================================
# 7. SHOCK & KINEMATICS
# ==========================================================
st.header("3. Shock & Kinematics")
col_k1, col_k2 = st.columns(2)

# Handling Defaults logic
def_travel = defaults["travel"] if unit_len == "Millimetres (mm)" else defaults["travel"] * MM_TO_IN
def_stroke = defaults["stroke"] if unit_len == "Millimetres (mm)" else defaults["stroke"] * MM_TO_IN

with col_k1:
    t_lbl = "Rear Travel (mm)" if unit_len == "Millimetres (mm)" else "Rear Travel (in)"
    travel_in = st.number_input(t_lbl, 0.0, 300.0, float(def_travel), 1.0)
    
    s_lbl = "Shock Stroke (mm)" if unit_len == "Millimetres (mm)" else "Shock Stroke (in)"
    stroke_in = st.number_input(s_lbl, 0.0, 100.0, float(def_stroke), 0.5)

travel_mm = travel_in * IN_TO_MM if unit_len != "Millimetres (mm)" else travel_in
stroke_mm = stroke_in * IN_TO_MM if unit_len != "Millimetres (mm)" else stroke_in

with col_k2:
    adv_kinematics = st.checkbox("Advanced Kinematics")
    if adv_kinematics:
        st.caption(f"Defaults for {category}")
        lr_start = st.number_input("LR Start", 1.0, 4.0, defaults["lr_start"], 0.05)
        lr_end = st.number_input("LR End", 1.0, 4.0, defaults["lr_end"], 0.05)
        
        # Calculate progression for logic use
        prog_calc = ((lr_start - lr_end) / lr_start) * 100
        st.caption(f"Calculated Progression: {prog_calc:.1f}%")
        mean_lr = (lr_start + lr_end) / 2
    else:
        prog_calc = float(defaults["progression"]) 
        mean_lr = travel_mm / stroke_mm
        st.metric("Mean Leverage Ratio", f"{mean_lr:.2f}")

# Spring Type Selection with Auto-Recommend
spring_type_options = ["Auto-Recommend", "Standard Steel (Linear)", "Lightweight Steel/Ti", "Sprindex", "Progressive Coil"]
spring_type_sel = st.selectbox("Spring Type", spring_type_options, index=0)

active_spring_type = spring_type_sel
if spring_type_sel == "Auto-Recommend":
    rec_type, rec_reason = recommend_spring_type(prog_calc)
    active_spring_type = rec_type
    st.success(f"💡 Recommended: **{rec_type}**")
    st.caption(rec_reason)

# ==========================================================
# 8. SAG TARGET & CALCULATIONS
# ==========================================================
st.header("4. Setup Preferences")

# 1. Calculate Smart Default based on inputs
cat_sag_map = {"Downcountry": 28, "Trail": 30, "All-Mountain": 31, "Enduro": 33, 
               "Long Travel Enduro": 34, "Enduro (Race focus)": 32, "Downhill (DH)": 35}
base_sag = cat_sag_map[category]
skill_mod = SKILL_MODIFIERS[skill]["sag_mod"]
smart_default_sag = base_sag + skill_mod

# 2. User Input (Initialized with Smart Default)
target_sag = st.slider(
    "Target Sag (%)", 
    min_value=20.0, 
    max_value=40.0, 
    value=float(smart_default_sag), 
    step=0.5,
    help="Default calculated from Bike Category + Rider Skill. Adjust preference here."
)

# ---------------- PHYSICS ENGINE ----------------
# Mass
coupling = COUPLING_COEFFS[category]
eff_rider_kg = rider_kg + (gear_kg * coupling)
system_kg = eff_rider_kg + bike_kg
rear_load_kg = (system_kg * (final_bias_calc / 100)) - unsprung_kg
rear_load_lbs = rear_load_kg * KG_TO_LB

# Spring Rate Formula
sag_mm = stroke_mm * (target_sag / 100)
raw_rate = (rear_load_lbs * mean_lr) / (sag_mm * MM_TO_IN)

# Progression Correction
if active_spring_type == "Progressive Coil":
    raw_rate = raw_rate * 0.97

# ==========================================================
# 9. OUTPUTS
# ==========================================================
st.divider()
st.header("Results")

res_c1, res_c2 = st.columns(2)
res_c1.metric("Ideal Spring Rate", f"{int(raw_rate)} lbs/in", help="Exact calculated rate for target sag")
res_c2.metric("Target Sag", f"{target_sag:.1f}%", f"{sag_mm:.1f} mm")

# --- Spring Options Matrix ---
st.subheader("Available Spring Options")
st.caption("Select the spring that best fits your preference range.")

# Generate neighbor rates (Recommended +/- 25lbs)
options = []
base_step = 25
center_rate = int(round(raw_rate / base_step) * base_step)
rates_to_check = [center_rate - base_step, center_rate, center_rate + base_step]

for rate in rates_to_check:
    if rate <= 0: continue
    
    # Inverse Physics: Calculate Sag resulting from this specific Spring Rate
    resulting_sag_mm = (rear_load_lbs * mean_lr) / (rate * MM_TO_IN) 
    resulting_sag_pct = (resulting_sag_mm / stroke_mm) * 100
    
    tag = ""
    if rate == center_rate: tag = "✅ Recommended"
    elif resulting_sag_pct > 35: tag = "⚠️ Too Soft"
    elif resulting_sag_pct < 25: tag = "⚠️ Too Stiff"
    else: tag = "Alternative"

    options.append({
        "Spring Rate": f"{rate} lbs",
        "Resulting Sag": f"{resulting_sag_pct:.1f}%",
        "Travel Usage": f"{resulting_sag_mm:.1f} mm",
        "Fit": tag
    })

df_options = pd.DataFrame(options)
st.dataframe(
    df_options.style.apply(lambda x: ['background-color: #d4edda' if 'Recommended' in v else '' for v in x], subset=['Fit']), 
    hide_index=True, 
    use_container_width=True
)

# --- Preload Table ---
st.subheader("Fine Tuning (Preload)")
st.caption(f"Effect of preload on the **{center_rate} lbs** spring:")

preload_data = []
for turns in [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    preload_mm = turns * 1.0 
    preload_in = preload_mm * MM_TO_IN
    # Calculate effective load support with preload
    sag_in_eff = (rear_load_lbs * mean_lr / center_rate) - preload_in
    sag_pct_eff = (sag_in_eff / (stroke_mm * MM_TO_IN)) * 100
    
    status = "✅"
    if turns >= 3.0: status = "⚠️ Excessive"
    elif sag_pct_eff < 25: status = "⚠️ Too Stiff"
    
    preload_data.append({
        "Turns": turns,
        "Sag (%)": f"{sag_pct_eff:.1f}%",
        "Sag (mm)": f"{(sag_pct_eff/100)*stroke_mm:.1f} mm",
        "Status": status
    })

st.dataframe(pd.DataFrame(preload_data), hide_index=True)

# --- Sprindex Logic ---
if active_spring_type == "Sprindex":
    st.subheader("Sprindex Recommendation")
    family = None
    if stroke_mm <= 55: family = "XC/Trail (55mm)"
    elif stroke_mm <= 65: family = "Enduro (65mm)"
    elif stroke_mm <= 75: family = "DH (75mm)"
    
    if family:
        st.markdown(f"**Compatible Family:** {family}")
        valid_ranges = []
        for r_str in SPRINDEX_DATA[family]["ranges"]:
            low, high = map(int, r_str.split("-"))
            if low <= raw_rate <= high:
                valid_ranges.append(r_str)
        if valid_ranges:
            st.success(f"Recommended Sprindex Range: **{valid_ranges[0]} lbs/in**")
        else:
            st.error("Calculated rate is outside standard Sprindex ranges.")
    else:
        st.error(f"Shock stroke ({stroke_mm}mm) exceeds Sprindex maximums.")

st.info("""
**Disclaimers:**
* **Rate Tolerance:** Standard coils vary +/- 5%.
* **Stroke Compatibility:** Ensure spring stroke > shock stroke to avoid coil bind.
* **Diameter:** Check spring ID compatibility with your specific shock body.
""")
