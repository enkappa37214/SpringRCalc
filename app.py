import streamlit as st
import math

# ==========================================================
# CONFIGURATION
# ==========================================================
st.set_page_config(page_title="General MTB Spring-Rate Calculator", page_icon="⚙️", layout="centered")

COUPLING_DEFAULTS = {
    "Trail / Downcountry": 0.80,
    "Trail / Enduro": 0.75,
    "Enduro / All-Mountain": 0.70,
    "Enduro (Race)": 0.78,
    "DH / Long-Travel Enduro": 0.92,
    "Downhill (DH)": 0.95
}

SAG_DEFAULTS = {
    "Flow / Jumps": 30, "Dynamic": 31, "Alpine": 32,
    "Trail": 33, "Steep / Tech": 34, "Plush": 35
}

# ==========================================================
# PHYSICS BLOCKS
# ==========================================================
def compute_effective_mass(rider, gear, coupling):
    return rider + (gear * coupling)

def compute_rear_load(eff_mass, bike_mass, rear_bias, unsprung_mass):
    sys_mass = eff_mass + bike_mass
    rear_load_kg = (sys_mass * rear_bias) - unsprung_mass
    return rear_load_kg * 2.20462  # Convert to lbs

def compute_kinematics(mode, start, end, progress_pct):
    if mode == "Start & End Rates":
        return (start + end) / 2
    else:  # Start & Progression
        calc_end = start * (1 - (progress_pct / 100))
        return (start + calc_end) / 2

def compute_sag_target(style, skill, shock_type):
    base = SAG_DEFAULTS.get(style, 33)
    # Skill: +1 for beginner (softer), -1 for racer (stiffer)
    skill_map = {"Beginner": 1, "Intermediate": 0, "Advanced": -1, "Racer": -2}
    mod = skill_map.get(skill, 0)
    if shock_type == "Air": mod -= 1
    return max(25, min(37, base + mod))

def compute_spring_rate(load_lbs, lr_mean, stroke_mm, sag_pct):
    stroke_in = stroke_mm / 25.4
    sag_in = stroke_in * (sag_pct / 100)
    raw_rate = (load_lbs * lr_mean) / sag_in
    # Round to nearest 25 lbs
    rounded_rate = 25 * round(raw_rate / 25)
    return rounded_rate, raw_rate

def compute_effective_sag(target_pct, preload_turns, stroke_mm):
    # Fixed pitch: 1.0mm per turn
    preload_mm = preload_turns * 1.0 
    sag_effective = target_pct - (preload_mm / stroke_mm * 100)
    return sag_effective

# ==========================================================
# UI LAYOUT
# ==========================================================
st.title("MTB Spring Rate Calculator")

# 1. Rider
st.subheader("1. Rider Profile")
c1, c2 = st.columns(2)
with c1:
    rider_mass = st.number_input("Rider Weight (kg)", 40.0, 130.0, 75.0, 0.5)
    skill = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced", "Racer"], index=1)
with c2:
    gear_mass = st.number_input("Gear Weight (kg)", 0.0, 15.0, 4.0, 0.5)
    sag_style = st.selectbox("Terrain Style", list(SAG_DEFAULTS.keys()), index=3)

# 2. Bike
st.subheader("2. Chassis Data")
c3, c4 = st.columns(2)
with c3:
    cat = st.selectbox("Category", list(COUPLING_DEFAULTS.keys()), index=2)
    bike_mass = st.number_input("Bike Weight (kg)", 9.0, 25.0, 15.0, 0.1)
with c4:
    bias = st.slider("Rear Bias (%)", 55, 75, 65)
    unsprung = st.number_input("Unsprung Mass (kg)", 2.0, 8.0, 3.5, 0.1)

# 3. Shock
st.subheader("3. Shock & Kinematics")
c5, c6 = st.columns(2)
with c5:
    stroke = st.number_input("Stroke (mm)", 40.0, 90.0, 60.0, 2.5)
    k_mode = st.radio("Kinematics Input", ["Start & End Rates", "Start & Progression %"])
    lr_start = st.number_input("Lev. Ratio Start", 2.0, 4.0, 2.9, 0.05)
    
    lr_end, prog_pct = 2.7, 15.0
    if k_mode == "Start & End Rates":
        lr_end = st.number_input("Lev. Ratio End", 1.5, 3.5, 2.4, 0.05)
    else:
        prog_pct = st.number_input("Progression (%)", 0.0, 60.0, 15.0, 1.0)

with c6:
    spring_type = st.selectbox("Spring Type", ["Linear", "Progressive", "Sprindex"])
    preload = st.number_input("Preload (Turns)", 0.0, 5.0, 1.0, 0.5)

# ==========================================================
# CALCULATION
# ==========================================================
coupling = COUPLING_DEFAULTS[cat]
eff_mass = compute_effective_mass(rider_mass, gear_mass, coupling)
load_lbs = compute_rear_load(eff_mass, bike_mass, bias/100, unsprung)
lr_mean = compute_kinematics(k_mode, lr_start, lr_end, prog_pct)
sag_tgt = compute_sag_target(sag_style, skill, "Coil")

rec_rate, raw_rate = compute_spring_rate(load_lbs, lr_mean, stroke, sag_tgt)
eff_sag = compute_effective_sag(sag_tgt, preload, stroke)

# Correction for progressive springs
if spring_type != "Linear":
    rec_rate = 25 * round((raw_rate * 0.97) / 25)

# ==========================================================
# OUTPUT
# ==========================================================
st.divider()
col_a, col_b, col_c = st.columns(3)
col_a.metric("Recommended Spring", f"{int(rec_rate)} lbs", help=f"Exact: {raw_rate:.1f}")
col_b.metric("Target Sag", f"{sag_tgt:.1f}%")
col_c.metric("Sag w/ Preload", f"{eff_sag:.1f}%", delta=f"{eff_sag-sag_tgt:.1f}%", delta_color="inverse")

if eff_sag < 25: st.warning("Setup is too stiff (Sag < 25%)")
if eff_sag > 35: st.warning("Setup is too soft (Sag > 35%)")
