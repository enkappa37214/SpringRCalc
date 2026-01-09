# SpringRCalc
complex calculator for MTB spring rate
Features
1. General-Purpose Physics Model

Uses effective rider mass, including gear and a coupling coefficient to account for mass that partially bypasses suspension motion (backpacks, water, tools).

Computes rear sprung mass from total rider + bike system, rear bias, and unsprung mass.

Fully supports leverage ratio kinematics: start, end, or progression percentage.

Applies target sag (%) based on riding style, skill level, and shock type.

2. Rider Inputs

Rider Body Mass (kg)

Gear Mass (kg), with automatic coupling coefficient based on bike category

Skill Modifier (-1% to +1%) to slightly adjust sag for advanced or novice riders

3. Bike Inputs

Bike Mass (kg), can be estimated or measured

Rear Weight Bias (%), default by bike category

Rear Unsprung Mass (kg)

4. Suspension Inputs

Shock Stroke (mm)

Leverage Ratio Start / End or Progression %

Riding Style / Application

Spring Type: Linear, Progressive, or Sprindex

End-Coil Effect Fraction (optional)

Preload Turns, which adjust effective sag without changing spring rate

5. Outputs

Rear Sprung Mass (lbs)

Mean Leverage Ratio

Target Sag (%)

Raw Spring Rate (lbs/in)

Final Spring Rate (lbs/in), adjusted for spring type and end-coil effects

Effective Sag (%) after preload

6. Built-In Physics Logic

Calculates effective rider system mass: rider_mass + gear_mass * coupling

Determines rear sprung mass for accurate spring sizing

Uses shock stroke and leverage ratio to compute raw spring rate

Applies spring type correction for progressive or Sprindex springs

Calculates effective sag after preload adjustment

Keeps all units in lbs/in for spring rate, mm/in for stroke, and kg for mass inputs

7. UI & Experience

Interactive Streamlit app with number inputs, sliders, and dropdowns

Displays all outputs as metrics for clarity

Fully general, no brand-specific features
