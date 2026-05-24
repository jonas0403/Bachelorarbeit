# Bug Investigation: Negative Rtheta in Blade Coordinate Generation

## Discovery

After fixing the inter-stage coordinate overlap (x0[0] fix), a 3-stage test case was run on 2026-05-22. The debug log (`Docs/Output/debug.txt`) reveals that **all 6 blade rows produce `[INVALID] TRACE final`** with 54-61 negative Rtheta points out of 127-129 total grid points.

## Key Finding: The INVALID Flags Are FALSE POSITIVES

After thorough investigation, the negative Rtheta values are **physically correct** for blades that turn the flow past the zero-Rtheta reference line. The `v < 0` check in the INVALID validation is too strict.

## Session 3 (2026-05-22): Spanwise Angle Discontinuity in Rotor Profiles

### Root Cause

The `create_default_profiles()` function generates 4×5 Bezier control points (4 CPs × 5 span positions) for each blade row. For rotors, the blade outlet angles (`beta_blade_R_out` from radial equilibrium) can cross 90° at some span positions (e.g., 20% span for rotor 1, hub for rotors 2-3). The per-section reflection logic:

```python
if b1 > 90.0 and b2 < 90.0:
    b2 = 180.0 - b2
```

reflected some span sections to > 90° but left others unchanged, creating a **discontinuity in the spanwise TE angle distribution**.

### Evidence from Run 2 (Before This Fix)

**Row 1 (Stage 1 Rotor)** — beta_BP (interpolated):
| h/H | LE (CP1) | CP2 | CP3 | TE (CP4) | Problem |
|-----|----------|-----|-----|----------|---------|
| 0.0 | 147.54 | 134.64 | 132.64 | 129.69 | baseline |
| 0.2 | **151.21** | **108.67** | **102.07** | **92.33** | **SHARP DIP** — TE 37° lower than hub |
| 0.5 | 155.62 | 137.67 | 134.88 | 130.77 | smooth |
| 0.8 | 158.70 | 150.09 | 148.76 | 146.78 | smooth |
| 1.0 | 161.23 | 155.78 | 154.93 | 153.68 | smooth |

At 20% span, `beta_blade_R_out` ≈ 87° (< 90°), which was reflected to 93°. Other spans had `beta_blade_R_out` > 90° and were unchanged. Result: TE = [129.69, 92.33, 130.77, 146.78, 153.68] — a 37° discontinuity at 20% span causing the blade surface to be non-smooth.

**Rows 3 and 5** show the same pattern but at hub instead of 20%.

### Fix Applied

1. **`create_default_profiles()`**: Changed to a two-pass approach:
   - **Pass 1**: Collect all 5 raw b1/b2 pairs from radial equilibrium
   - **Global decision**: If ALL 5 LE values > 90°, reflect ALL TE < 90° to > 90° (span-consistent)
   - **Pass 2**: Apply reflection consistently + compute CPs
   - **Spanwise smoothing**: 3-point moving average on CP2, CP3, CP4 to eliminate any residual discontinuity

2. **`blade_metal_BP()`**: Changed from per-section `if beta_M_e[i] > 90.0` to global check `all(v > 90.0 for v in beta_M_e)` for reflection decision.

### New Debug Logs Added

| Context | Location | What it logs |
|---------|----------|-------------|
| `create_default` | `create_default_profiles()` | Full radial equilibrium arrays per stage |
| `create_default` | `create_default_profiles()` | Per-section pre/post reflection values + reflection decision |
| `create_default` | `create_default_profiles()` | Final 20-element angle array + spanwise smoothing |
| `blade_metal_raw` | `blade_metal_BP()` | Raw JSON values before clamping |
| `TRACE calc_blade_coords` | `calculation_blade_coordinates()` | d_sec max/mid (not just LE/TE) |

## Detailed Analysis

### Run Comparison: Before vs After Angle Clamping Fix

**Before clamping (Run 1):**
| Row | Type | LE Rtheta | TE Rtheta | Direction | Correct? |
|-----|------|-----------|-----------|-----------|----------|
| 1 | Rotor 1 | 0.0054 | 0.0083 | INCREASING | ❌ wrong |
| 2 | Stator 1 | -0.0193 | 0.0099 | INCREASING | ✅ correct |
| 3 | Rotor 2 | 0.0107 | -0.0034 | DECREASING | ✅ correct |
| 4 | Stator 2 | -0.0154 | 0.0079 | INCREASING | ✅ correct |

**After clamping (Run 2):**
| Row | Type | LE Rtheta | TE Rtheta | Direction | Correct? |
|-----|------|-----------|-----------|-----------|----------|
| 1 | Rotor 1 | 0.0128 | -0.0143 | DECREASING | ✅ **FIXED** |
| 2 | Stator 1 | -0.0193 | 0.0099 | INCREASING | ✅ correct |
| 3 | Rotor 2 | 0.0109 | -0.0057 | DECREASING | ✅ correct |
| 4 | Stator 2 | -0.0154 | 0.0079 | INCREASING | ✅ correct |
| 5 | Rotor 3 | 0.0131 | -0.0080 | DECREASING | ✅ correct |
| 6 | Stator 3 | -0.0144 | 0.0074 | INCREASING | ✅ correct |

**The clamping fix flipped Rotor 1's Rtheta direction from wrong (increasing) to correct (decreasing).**

### Why Negative Rtheta Is Valid

For a **rotor** (e.g., Row 1 hub section):
- Rtheta starts at 0.0128 (LE, positive) — flow enters with positive tangential velocity
- Rtheta ends at -0.0143 (TE, negative) — blade turns the flow past the zero reference
- Turning: ΔRtheta/R = (0.0128 - (-0.0143)) / 0.095 = 0.285 rad = **16.3°**
- This is physically reasonable for a compressor rotor

For a **stator** (e.g., Row 2 hub section):
- Rtheta starts at -0.0193 (LE, negative) — flow enters with negative Rtheta from upstream rotor
- Rtheta ends at 0.0099 (TE, positive) — blade turns flow back past the zero reference
- This is physically correct flow straightening

### Grid Validity Check

For a valid MULTALL grid, three conditions must hold:
1. **x monotonic** — ✅ PASSES (confirmed by existing check)
2. **d = Rtheta_upper - Rtheta_lower > 0** — ✅ ALWAYS TRUE (thickness is positive by construction)
3. **Rtheta monotonic along blade** — ✅ PASSES (no back-and-forth in the data)

The grid cells should have positive volumes.

### What Was Likely Causing MULTALL Negative Volumes

1. **Passage width bug (NOW FIXED)**: Old code wrote `d` (thickness) to MULTALL block 3 instead of `Rtheta`. MULTALL saw `d` as the upper surface Rtheta and computed passage width from the wrong data. The BUGFIX (`var_Grid.py:337-357`) now correctly writes `Rtheta` to block 3 and `Rtheta - d` to block 5.

2. **Coordinate overlap (NOW FIXED)**: Internal stages had x0[0] extending ~40-90 mm backward, overlapping with the previous stage's stator outlet.

3. **Rotor direction error (NOW FIXED)**: Rotor 1 Rtheta was increasing LE→TE (wrong). The clamping fix corrected this by reflecting TE angles > 90°.

### The INVALID Check Bug

At `Stage_v3_working_with_bleedair.py:2490`:
```python
n_neg = sum(1 for v in arr if v < 0)
```

This flags ANY negative value in x, d, R, or Rtheta. For Rtheta, negative values are physically valid when the blade turns past the zero reference line.

**Fix**: Change the check to only flag NaN and Inf (remove the `v < 0` check), or add a monotonicity check instead.

### Passage Width BUGFIX Verification (from Run 2)

```
Row 1: pitch=0.029845, thick=0.003330, passage=0.026515  ✅ thick < pitch
Row 2: pitch=0.011479, thick=0.003457, passage=0.008021  ✅ thick < pitch
Row 3: pitch=0.041166, thick=0.003096, passage=0.038070  ✅ thick < pitch
Row 4: pitch=0.018088, thick=0.003251, passage=0.014837  ✅ thick < pitch
Row 5: pitch=0.029117, thick=0.003363, passage=0.025754  ✅ thick < pitch
Row 6: pitch=0.017054, thick=0.003183, passage=0.013872  ✅ thick < pitch
```

All rows have thickness < pitch, so the blade fits in the passage. The old (wrong) value would have been close to zero, making MULTALL see extremely narrow or negative passages.

## Session 4 (2026-05-22): ROOT CAUSE of MULTALL Negative Volumes — Non-Monotonic Spanwise Section Ordering

### Discovery

After all prior fixes (angle clamping, passage width, coordinate overlap, spanwise smoothing), MULTALL still reported **45756 negative volumes** — nearly all grid cells. This pointed to a systematic grid inversion, not a localized geometry defect.

### Root Cause

The `additional_section()` function at `Stage_v3_working_with_bleedair.py:2467-2507` inserts two interpolated span sections:
- **Z_H** (h=0.05) between hub (h=0.0, idx 0) and section 1 (h=0.20, idx 1)
- **Z_S** (h=0.95) between section 3 (h=0.80, idx 3) and shroud (h=1.0, idx 4)

**The bug**: After the Z_H insert (section list = 6 elements), Z_S was inserted at **index 4**, but should have been at **index 5**:

```
Before Z_S insert (after Z_H already inserted at index 1):
  [0] h=0.0     hub
  [1] h=0.05    Z_H
  [2] h=0.20    section 1
  [3] h=0.50    section 2
  [4] h=0.80    section 3
  [5] h=1.0     shroud ← was index 4 originally, shifted to 5

WRONG insert at index 4:
  [4] h=0.95    Z_S ← placed BEFORE h=0.80!
  [5] h=0.80    section 3 ← shifted AFTER Z_S
  [6] h=1.0     shroud

Result: h=0.95 → h=0.80 → h=1.0  (NON-MONOTONIC)

CORRECT insert at index 5:
  [4] h=0.80    section 3
  [5] h=0.95    Z_S ← correctly between 0.80 and 1.0
  [6] h=1.0     shroud
```

### Why This Causes Negative Volumes

MULTALL generates an H-grid where the K-index runs hub→shroud. Sections must be ordered by increasing radius. With Z_S (h=0.95) before section 3 (h=0.80):

| Section | h | R (hub, row 1 inlet) | R (shroud, row 1 inlet) |
|---------|---|---------------------|------------------------|
| [0] hub | 0.00 | 0.095 | 0.095 |
| [1] Z_H | 0.05 | ~0.108 | ~0.108 |
| [2] sec1 | 0.20 | 0.162 | 0.162 |
| [3] sec2 | 0.50 | 0.264 | 0.264 |
| **[4] Z_S** | **0.95** | **~0.415** | **~0.415** |
| **[5] sec3** | **0.80** | **0.365** | **0.365** |
| [6] shroud | 1.00 | 0.432 | 0.432 |

Between sections 4 and 5, radius **decreases** from ~0.415 to ~0.365 m. MULTALL's 3D grid interpolation creates inverted cells between these sections, affecting all (JM × LM) cells between the corresponding KM layers. This cascades through all 6 blade rows.

### Fix Applied

**File**: `src/Stage_v3_working_with_bleedair.py:2499-2505`

Changed all Z_S insert indices from 4 to 5:
```python
# Before (BUG): Z_S at index 4 → gives wrong order
x.insert(4, X_0_95)
Rtheta.insert(4, Rtheta_0_95)
d.insert(4, d_0_95)
R.insert(4, R_0_95)

# After (FIX): Z_S at index 5 → correct monotonic order
x.insert(5, X_0_95)
Rtheta.insert(5, Rtheta_0_95)
d.insert(5, d_0_95)
R.insert(5, R_0_95)
```

Also added a **monotonicity check** debug message that logs section radii at inlet and whether they are monotonic:
```
Section ordering: radii at inlet = ['0.0950', '0.1084', '0.1624', '0.2635', '0.3646', '0.4152', '0.4320']  monotonic=True
```

## Summary

| Issue | Status | Impact |
|-------|--------|--------|
| Rotor 1 wrong Rtheta direction | ✅ **FIXED** by angle clamping | Would cause negative volumes |
| Passage width block3=d | ✅ **FIXED** (now writes Rtheta) | Would cause negative passages |
| Coordinate overlap x0[0] | ✅ **FIXED** | Would cause grid overlap |
| INVALID check flags negative Rtheta | ✅ **FIXED** — now only flags NaN/Inf for Rtheta | Was false positive |
| Spanwise TE angle discontinuity | ✅ **FIXED** — global reflection + spanwise smoothing | Caused non-smooth blade surfaces |
| **Non-monotonic section ordering** | ✅ **FIXED** — Z_S insert 4→5 | **LIKELY ROOT CAUSE of 45756 negative volumes** |
| MULTALL negative volumes | ⏳ Need to re-test with current .dat | Should be resolved by section ordering fix

## Files Modified (Session 4)

- `src/Stage_v3_working_with_bleedair.py:2497-2512` — **FIXED**: Z_S insert index 4→5 for x, Rtheta, d, R in `additional_section()`. Added monotonicity check debug log.

## Debug Log Summary

| Context | Location | What it logs |
|---------|----------|-------------|
| `create_default` | `create_default_profiles()` | Full radial eq arrays, per-section pre/post reflection, final angles, spanwise smoothing |
| `blade_metal_raw` | `blade_metal_BP()` | Raw JSON angle values before clamping |
| `blade_metal_angles` | `blade_metal_BP()` | 4×5 angle control points after clamping, per row |
| `camber_angles` | `calculation_of_section()` / `_0_5()` | Interpolated beta_BP [LE, CP2, CP3, TE] per span section |
| `Rtheta_integration` | `calculation_of_section()` | R_theta_s_prime[0] (LE), R_theta_s_prime[124] (TE), beta_S[0], beta_S[124] |
| `Rt_negative_info` | `calc_blade_row_coordinates()` | Count of negative Rtheta points per level (informational only) |
| `INVALID` | `calc_blade_row_coordinates()` | NaN/Inf in any coordinate array; negative values in x/d/R (not Rt) |
| `TRACE calc_blade_coords` | `calculation_blade_coordinates()` | x_sec, d_sec max/mid, Rtheta_sec per section |
| `TRACE merged` | `calc_blade_row_coordinates()` | Merged blade+inlet+outlet coordinates for all 5 span planes |
| `TRACE final` | `calc_blade_row_coordinates()` | Final coordinates after interpolation to requested levels |
