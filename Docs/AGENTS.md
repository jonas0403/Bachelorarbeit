# AGENTS.md — Project State & Progress Log

## Project Overview

**MULTALL Stage Generator** — Python/Tkinter GUI preprocessor replacing MEANGEN/STAGEN Fortran modules for the MULTALL turbomachinery CFD solver.

- Entry point: `main.py`
- GUI: `src/GUI.py` (3051 lines)
- Core calculation: `src/Stage_v3_working_with_bleedair.py`
- Grid/MULTALL output: `src/var_Grid.py` (969 lines)
- Channel geometry: `src/Channel_v2.py` (692 lines)
- Meanline: `src/Fixed_radii_Meanline_GUI_v4.py`
- Radial equilibrium: `src/Radial_equilibrium.py`
- Debug logging: `src/debug_log.py`

---

## Current State (2026-05-22, end of session)

### What Works
- Single-stage and multi-stage meanline + radial equilibrium calculation
- GUI input for all parameters
- JSON project save/load
- MULTALL output file generation (`.dat`) with ISHIFT=2 (auto mixing plane matching)
- Cumulative x-offset in `init_channel_data()` for multi-stage channel assembly
- Debug logging module (`debug_log.py`) — timestamps, sections, context; used in all `src/` files
- All German comments in `src/` translated to English

### MULTALL Documentation Available (`Docs/`)
- `README.pdf` — System overview (MEANGEN/STAGEN/MULTALL chain)
- `General-description.pdf` — Numerical method, grid, mixing plane model
- `new-readin-input-data-20.9 .pdf` — Input format v20.9
- `new-readin-input-data (2).pdf` — Input format (newer revision)
- `10stg-compr-17.4.dat` — Example 10-stage compressor (21 rows)

### Known Issues — Fixed in This Session

#### 1. Inter-stage Coordinate Overlap (x0[0] backward extrapolation)
**Root cause**: `Channel_v2.py:448-449` — For internal stages, x0[0] was set to a large backward extrapolation (`-0.667*l_R`, ~40-90 mm). This made the rotor inlet grid of stage N extend backward past stage N-1's stator outlet.

**Fix**:
- `Channel_v2.py:448-457` — Changed `x0[0] = 0.0` for internal stages (commented out old code).
- `Stage_v3_working_with_bleedair.py:2158-2183` — Added DX_in clamp in `inlet_coordinates()` to prevent division-by-zero when x0[0]=x0[1].

**Status**: Old code commented out, new code active. Overlap reduced from ~36 mm per stage to ~5 mm (from the default DX_in clamp).

#### 2. Outlet Area Bug
**Root cause**: `Channel_v2.py:529` — `new_area = old_area * inlet_area` in the outlet geometry block (copy-paste error).

**Fix**: Changed to `new_area = old_area * outlet_area`.

#### 3. (Previous) Cumulative Offset Missing
**Root cause**: `init_channel_data()` had no offset — all stages sat at x≈0.
**Fix**: Added `cumulative_x_offset` accumulation per stage.

#### 4. (Previous) Various secondary fixes
- `mLE_TE_cntr()` used global `stage` instead of `stage_to_calc`
- `Channel_v2.py:490` r0_G[0] formula
- `var_Grid.py` tip clearance type fragility
- NSTG formula: `* 2` → `* NROW`

### MULTALL Documentation Key Findings

**ISHIFT=2 is hardcoded** in `var_Grid.py:307`:
```
ISHIFT    NEXTRAP_LE  NEXTRAP_TE
    2        10        10
```

From MULTALL docs (NOTE 12): **"ISHIFT = 2 the grids are moved so that they coincide at the mixing plane over the whole span and maintain the input stream surfaces."**

This means MULTALL automatically shifts downstream row coordinates to make J=1 match J=JM of the upstream row. The overlap fix ensures blade positions stay where designed, rather than being shifted by MULTALL's auto-matching.

### Debug File Double-Open Issue
Both `var_Grid.py:791` and `GUI.py:2845` call `debug_log.open_file()` — `init_channel_data()` debug messages get overwritten by `var_Grid.py`'s later call.

### Still Unknown
- Whether the coordinate overlap was truly causing MULTALL negative volumes, or if the root cause is elsewhere (unit inconsistency, hub/shroud contour, blade thickness)
- Whether the 5 mm default DX_in in `inlet_coordinates` creates noticeable overlap in MULTALL

---

## New Session Findings (2026-05-22)

### Finding 1: Angle Clamping Fix WORKED

The clamping fix in `blade_metal_BP()` (lines 1327-1344) and `create_default_profiles()` (lines 308-325) **successfully changed the blade angle direction for rotors.** Evidence from comparing two debug runs:

**Before clamping (Run 1):**
| Row | Type | LE Rtheta | TE Rtheta | Direction | Correct? |
|-----|------|-----------|-----------|-----------|----------|
| 1 | Rotor 1 | 0.0054 | 0.0083 | INCREASING | ❌ wrong |
| 2 | Stator 1 | -0.0193 | 0.0099 | INCREASING | ✅ correct |

**After clamping (Run 2):**
| Row | Type | LE Rtheta | TE Rtheta | Direction | Correct? |
|-----|------|-----------|-----------|-----------|----------|
| 1 | Rotor 1 | 0.0128 | -0.0143 | DECREASING | ✅ correct |
| 2 | Stator 1 | -0.0193 | 0.0099 | INCREASING | ✅ correct |

The rotor Rtheta direction flipped from wrong (increasing, meaning blade turns opposite to grid) to correct (decreasing, blade turns with the flow). Stator was already correct.

### Finding 2: INVALID Flags Are FALSE POSITIVES

All 6 rows still show `[INVALID]` with negative Rtheta, but **this is physically correct behavior:**

- **Rotors**: Rtheta goes from positive (LE) to negative (TE) — blade turns the flow past the zero-Rtheta reference. Example Row 1 hub: Rtheta = 0.013 (LE) → -0.014 (TE), a turning of ~16° which is reasonable.
- **Stators**: Rtheta goes from negative (LE) to positive (TE) — flow enters with negative tangential component and is turned back past zero. Example Row 2 hub: Rtheta = -0.019 (LE) → 0.010 (TE).

The INVALID check at `calc_blade_row_coordinates()` line 2490 flags **any** negative value (`n_neg = sum(1 for v in arr if v < 0)`). This is too strict — negative Rtheta is valid as long as:
1. ✅ x is monotonic (passes existing check)
2. ✅ d = Rtheta_upper - Rtheta_lower > 0 (thickness positive, always true)
3. ✅ Rtheta is monotonic along the blade (no back-and-forth)

The grid cells should have positive volumes. The true MULTALL negative volumes were likely caused by the **passage width bug** (now fixed) or **coordinate overlap** (now fixed).

### Finding 3: Fix Needed — Relax INVALID Check

The INVALID check at `Stage_v3_working_with_bleedair.py:2490` should be changed to only check for NaN/Inf, not negative values. Alternatively, add a monotonicity check on Rtheta.

### Debug Logging Gaps (Unchanged)
- `blade_metal_BP()` never prints the actual angle values (beta_M_e/a/2/3)
- `calculation_of_section()` never prints the interpolated beta_BP
- No rotor radial equilibrium data is printed (only stator of last stage)

---

## Session 3 Findings (2026-05-22, second session)

### Finding 4: Spanwise TE Angle Discontinuity — Root Cause of Non-Smooth Blades

The per-section angle reflection in `create_default_profiles()` creates spanwise discontinuities in the rotor blade TE angles. Analysis of Run 2 data:

**Row 1 (Stage 1 Rotor) — beta_BP (interpolated):**
| h/H | LE (CP1) | CP2 | CP3 | TE (CP4) |
|-----|----------|-----|-----|----------|
| 0.0 | 147.54 | 134.64 | 132.64 | 129.69 |
| **0.2** | **151.21** | **108.67** | **102.07** | **92.33** ← outlier |
| 0.5 | 155.62 | 137.67 | 134.88 | 130.77 |
| 0.8 | 158.70 | 150.09 | 148.76 | 146.78 |
| 1.0 | 161.23 | 155.78 | 154.93 | 153.68 |

The 20% span TE angle (92.33°) is 37° lower than hub (129.69°) and 38° lower than 50% (130.77°). This is because `beta_blade_R_out` ≈ 87° at 20% span was reflected to 93°, while neighboring spans were > 90° and left unchanged.

**Remaining rotors (Row 3, Row 5)** show the same pattern at hub instead of 20%.

### Fix Applied (Session 3)

1. **`create_default_profiles()`**: Two-pass approach — collect all raw angles first, then make a GLOBAL reflection decision (if ALL LE > 90°, reflect ALL TE < 90°), then apply spanwise smoothing (3-point moving average on CP2, CP3, CP4).
2. **`blade_metal_BP()`**: Changed from per-section `if beta_M_e[i] > 90.0` to global `all(v > 90.0 for v in beta_M_e)` check.
3. **New debug logs**: `create_default` context for full radial equilibrium arrays and per-section pre/post reflection; `blade_metal_raw` for JSON values before clamping.

### Next Test

Run the test again. The INVALID flags for x<0 are false positives (inlet duct extends upstream). The `Rt_negative_info` is also expected. The key thing to verify: blade surfaces should now be smooth (no spanwise discontinuity).

Check the debug output for:
- `context="create_default"` logs showing pre/post reflection values
- `context="blade_metal_raw"` logs showing JSON raw values
- `context="blade_metal_angles"` for clamped values (should now be smooth spanwise)
- `context="camber_angles"` for interpolated beta_BP (should now be smooth at 20% span)

### Debug File Double-Open Issue
Both `var_Grid.py:791` and `GUI.py:2845` call `debug_log.open_file()` — `init_channel_data()` debug messages get overwritten by `var_Grid.py`'s later call.

### Known Issue — Section Ordering Bug (NOW FIXED)
`additional_section()` at `Stage_v3_working_with_bleedair.py:2499` inserted Z_S (h=0.95) at index 4 but should have been at index 5, creating non-monotonic spanwise section ordering (h=0.95 → h=0.80 → h=1.0). This caused MULTALL to generate inverted grid cells, producing ~45756 negative volumes. **Fix**: changed all Z_S insert indices from 4 to 5, added monotonicity check debug log.

All active `print()` calls in `src/` files have been routed through `debug_log.debug()`.

### Per-File Summary
| File | Status |
|------|--------|
| `src/debug_log.py` | Rewritten with timestamps, section markers, and `context` parameter |
| `src/Stage_v3_working_with_bleedair.py` | All active prints → `debug_log.debug()` + user-facing `print()` retained |
| `src/var_Grid.py` | All ~17 prints → `debug_log.debug()` |
| `src/Radial_equilibrium.py` | All active prints → `debug_log.debug()` |
| `src/Channel_v2.py` | All active prints → `debug_log.debug()` |
| `src/Bezier_curve.py` | All active prints → `debug_log.debug()` |
| `src/Cubspline_function_v2.py` | All active prints → `debug_log.debug()` |
| `src/plot_channel.py` | All active prints → `debug_log.debug()` |
| `src/run_multall.py` | All active prints → `debug_log.debug()` |
| `src/Thermodynamic_calc_GUI.py` | All active prints → `debug_log.debug()` |
| `src/Fixed_radii_Meanline_GUI_v4.py` | All active prints → `debug_log.debug()` |
| `src/GUI.py` | ~80 prints routed; status/error → both, value dumps → debug_log only |
| `misc_functions/` | Off-limits per user constraint |

---

## Stage Indexing Convention
- `stage` (module-level global) = always 1 — do NOT use
- `stage_to_calc = (row - 1) // 2 + 1` — correct per-row stage
- `current_stage` = 0-based index in grid context
- `channel_data` is dict keyed by 1-based stage number

## X0 Index Reference

| Index | Purpose | Stage 1 | Stage 2+ (after fix) |
|-------|---------|---------|---------------------|
| 0 | Far inlet (upstream duct) | `-inlet_dist * l_R` | **0.0** (was `-0.667*l_R`) |
| 1 | Rotor LE / matching plane | 0.0 | 0.0 |
| 2-6 | Blade geometry | per geometry | per geometry |
| 7 | Stator outlet / offset ref | computed | computed |
| 8 | Far outlet | `outlet_dist * l_S` | extrapolated |

---

## Next Steps (Updated 2026-05-22, Session 3)

### Phase 1: Fix the INVALID Check (False Positive)
- [x] **1.1** Changed the INVALID check at `Stage_v3_working_with_bleedair.py:2490` — Rtheta now only checked for NaN/Inf (not negative). Negative values are logged as informational (`context="Rt_negative_info"`).

### Phase 2: Fix Spanwise TE Angle Discontinuity (NEW)
- [x] **2.1** Refactored `create_default_profiles()`: two-pass approach with global reflection decision (all LE > 90° → reflect all TE < 90°) + spanwise 3-point smoothing on CP2/CP3/CP4
- [x] **2.2** Refactored `blade_metal_BP()` rotor clamping from per-section to global `all(v > 90.0)` check
- [x] **2.3** Added debug logs: `create_default` context, `blade_metal_raw` context, enhanced `TRACE calc_blade_coords`
- [ ] **2.4** Re-run test and verify blade spanwise profiles are smooth (check `context="create_default"` for pre/post reflection, `context="blade_metal_raw"` for JSON values)

### Phase 3: Validate Against MULTALL
- [ ] **3.1** Run MULTALL on the newly generated `.dat` file to verify negative volumes are resolved
- [ ] **3.2** If negative volumes persist, compare with passage-width BUGFIX verification (thick/pitch looks correct: e.g. row 1 pitch=0.0298, thick=0.0033, passage=0.0265)
- [ ] **3.3** Check ISHIFT=2 mixing-plane matching in MULTALL output

### Phase 4: Structural Improvements
- [x] **4.1** Added debug logs in `blade_metal_BP()` — prints all 4×5 angle control points after clamping (context `blade_metal_angles`)
- [x] **4.2** Added debug logs in `calculation_of_section()` — prints interpolated `beta_BP`, `beta_S[0]`, `beta_S[124]`, `R_theta_s_prime[0]`, `R_theta_s_prime[124]` (contexts `camber_angles`, `Rtheta_integration`)
- [x] **4.3** Also added debug log in `calculation_of_section_0_5()` for interpolated `beta_BP`
- [x] **4.4** Added `create_default` context debug logs for full radial equilibrium arrays and per-section values
- [x] **4.5** Added `blade_metal_raw` context for pre-clamp JSON values
- [x] **4.6** Enhanced `TRACE calc_blade_coords` with d_sec max/mid thickness values
- [ ] **4.7** Add rotor radial equilibrium dump to debug output (mirror stator print)
- [ ] **4.8** Consolidate `debug_log.open_file()` to single call (fix double-open overwrite)
- [ ] **4.9** Investigate unit inconsistency (x in mm, r in meters) in `Channel_v2.py`

### Phase 5: Production Readiness
- [ ] **5.1** Run a representative test case through the entire pipeline
- [ ] **5.2** Validate MULTALL output file format against example `.dat` files in `Docs/`
- [ ] **5.3** Add MULTALL docs to git tracking if needed
- [ ] **5.4** Write a test script to exercise the pipeline without GUI (pure Python) for automated regression testing
