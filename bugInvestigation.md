# Bug Investigation: Negative Volumes in MULTALL Multi-Stage Output

## Root Cause
The `init_channel_data()` function (Stage_v3_working_with_bleedair.py) was not applying a cumulative x-offset to stage 2+ channel coordinates. Each stage's channel was computed in its local frame (starting at x≈0), causing all stages to overlap spatially when written to the MULTALL grid file. Overlapping blade rows produce inverted/negative-volume elements in the MULTALL solver.

### Anatomy of the bug
```
channel() returns local coordinates for each stage:
  Stage 1: x ≈ [-200, +150] mm
  Stage 2: x ≈ [-70,  +115] mm   ← starts at ~0, same as stage 1!
  Stage 3: x ≈ [-40,   +75] mm   ← starts at ~0, same as stage 1!

MULTALL interprets all rows sequentially in one global frame:
  Row 1 (stage1 rotor): x=[-0.2025, 0.1495] m
  Row 2 (stage1 stator): x=[...]
  Row 3 (stage2 rotor): x=[-0.0670, 0.1150] m  ← OVERLAPS row 1&2!
  Row 4 (stage2 stator): x=[...]                 ← OVERLAPS row 1&2!

Result: elements are spatially folded → negative volumes → NaN velocities
```

### Fix (committed in `7a6b6e4` by FrickenWing)
`init_channel_data()` now accumulates offsets so each stage sits end-to-end in the global frame:

```
init_channel_data(compressor_gui_data):
    cumulative_x_offset = 0.0

    FOR each stage s = 1 to stages_to_calc:
        compressor_gui_data.stage = s
        x_values_s, r_values_s, m_prime_values_s, x0_s = channel(compressor_gui_data)
        x0_s = list(x0_s)

        IF cumulative_x_offset != 0.0:
            x0_s = [x + cumulative_x_offset  FOR x in x0_s]
            FOR each span index k:
                x_values_s[k] = [v + cumulative_x_offset  FOR v in x_values_s[k]]
                m_prime_values_s[k] = [v + cumulative_x_offset  FOR v in m_prime_values_s[k]]

        channel_data[s] = {
            'x_values':       x_values_s,
            'r_values':       r_values_s,
            'm_prime_values': m_prime_values_s,
            'x0':             x0_s,
        }

        cumulative_x_offset = x0_s[7]

        print "Stage {s}: stored. x0[1]={x0_s[1]} x0[7]={x0_s[7]} → next offset={cumulative_x_offset}"
```

### How offset propagates through the pipeline
```
channel_data[stage]['x_values']  (mm, correctly offset)
    ↓
coordinates(row=3):  stage=(3-1)//2+1=2, reads channel_data[2]['x_values']
    ↓  intpol(m_star_u, m_prime_values, x_values) → x_u values are OFFSET
    ↓
calculation_blade_coordinates(): x_sec = intpol(..., x_u) / 1000 → meters, OFFSET
    ↓
inlet_coordinates(): DX_in = x0[0]/1000 - x_sec[i][0] → local (both offset, difference is same)
    ↓  x_in = x_sec[i][0] + DX_in * (1 - l_in) → meters, OFFSET
    ↓
calc_blade_row_coordinates() → merge → levels → x_new (meters, OFFSET)
    ↓
generate_var_grid_data() stores x_new in all_rows_grid_data
    ↓
process_grid_data() writes x_new to MULTALL .dat file  ✓
```

Expected result for 3-stage:
```
Row 1 (stage1): x ≈ [-0.2025, 0.1495]  m
Row 2 (stage1): x ≈ [...]
Row 3 (stage2): x ≈ [0.150, 0.469]     m  ← starts where stage1 ends
Row 4 (stage2): x ≈ [...]
Row 5 (stage3): x ≈ [0.469, 0.708]     m  ← starts where stage2 ends
Row 6 (stage3): x ≈ [...]
```

## Coordinate Pipeline Verified
All key functions correctly derive `stage = (row-1)//2 + 1` and read from `channel_data[stage]`:

| Function | File:Line | Stage Resolution |
|---|---|---|
| `coordinates()` | Stage_v3...py:2011 | `(row-1)//2 + 1` |
| `calculation_of_section()` | Stage_v3...py:1652 | `(row-1)//2 + 1` |
| `mLE_TE_cntr()` | Stage_v3...py:1630 | `(row-1)//2 + 1` |
| `inlet_coordinates()` | Stage_v3...py:2115 | `(row-1)//2 + 1` |
| `outlet_coordinates()` | Stage_v3...py:2199 | `(row-1)//2 + 1` |
| `blade_metal_BP()` | Stage_v3...py:1236+ | `(row-1)//2 + 1` |

## Additional Issues Found & Fixed

### 1. Off-by-one in `multall_grid_data_head_row()` — WAS ALREADY CORRECT
Line 116: `current_stage = current_stage_num - 1` converts 1-based → 0-based index.
All `Stage.*[current_stage]` accesses are correct.

### 2. `mLE_TE_cntr()` debug print uses undefined variable `stage` — FIXED
**Location**: `Stage_v3_working_with_bleedair.py:1632`
**Bug**: `print(f"...stage={stage}...")` — `stage` is the module-level global, always = 1
**Fix**: Changed to `stage={stage_to_calc}` which is correctly derived as `(row - 1) // 2 + 1`

```python
# BEFORE (bug):
def mLE_TE_cntr(row):
    stage_to_calc = (row - 1) // 2 + 1
    x0 = channel_data[stage_to_calc]['x0']
    print(f"...stage={stage}: ...")  # BUG: 'stage' is global (=1)

# AFTER (fix):
def mLE_TE_cntr(row):
    stage_to_calc = (row - 1) // 2 + 1
    x0 = channel_data[stage_to_calc]['x0']
    debug_log.debug(f"...stage={stage_to_calc}: ...")  # OK
```

### 3. `Channel_v2.py` r0_G[0] formula mismatch — FIXED
**Location**: `Channel_v2.py:490`
**Bug**: `*(x0[0])` — should be `*(x0[0]-x0[1])` for correct linear interpolation.
**Context**: x0[1] is always 0 currently (no-op today), but needed for `current_x_offset` support.
**Fix**:
```python
# BEFORE:
r0_G[0] = round((r0_G[2]-r0_G[1])/(x0[2]-x0[1])*x0[0]+r0_G[1], 1)
# AFTER:
r0_G[0] = round((r0_G[2]-r0_G[1])/(x0[2]-x0[1])*(x0[0]-x0[1])+r0_G[1], 1)
```

### 4. `actual_tip_clearance` type fragility — FIXED
**Location**: `var_Grid.py:127-142`
**Bug**: Mixed types (int, list, float) — would crash with `TypeError` at subscript.
**Fix**:
```python
# BEFORE:
actual_tip_clearance = tip_clearance  # stores entire list!
...
file.write(f"{actual_tip_clearance[current_stage]:.8f} ...")  # CRASH

# AFTER:
actual_tip_clearance = tip_clearance[current_stage]  # scalar only
...
file.write(f"{actual_tip_clearance:.8f} ...")  # OK
```

### 5. NSTG formula updated in `write_head_file()`
**Location**: `var_Grid.py:307`
**Fix**: `* 2` → `* NROW` for rotor-only mode (NROW=1).

### 6. All debug output redirected from stdout to file
Created `src/debug_log.py` — lightweight file-based logger. All ~25 `print()` calls replaced with `debug_log.debug()`. File opened at `outputFiles/debug.txt`.

### 7. X-range monotonicity check re-added
After `generate_var_grid_data()`, each row's x-range is checked against the previous row's max. Writes pass/fail to debug log.

---

## Proposed Commit Message

```
fix: apply cumulative x-offset to stage 2+ channel coordinates; clean up debug output

- Fix overlapping stage geometry by accumulating x-offset in
  init_channel_data() — stage N now starts where stage N-1 ends,
  preventing inverted/negative-volume elements in MULTALL

- Redirect all debug/VERIFY prints to outputFiles/debug.txt via new
  src/debug_log.py module — preserves clean terminal output while
  keeping full trace for analysis

- Fix mLE_TE_cntr debug print referencing undefined global `stage`
  instead of correctly derived local `stage_to_calc`

- Fix r0_G[0] interpolation formula in Channel_v2.py — use
  (x0[0]-x0[1]) instead of x0[0] for correctness when x0[1] != 0

- Fix actual_tip_clearance type inconsistency in var_Grid.py —
  always scalar float now, removes fragile list subscript at write site

- Fix NSTG formula in write_head_file() — use NROW instead of
  hardcoded 2 for rotor-only configurations

- Restore x-range monotonicity check in process_grid_data() to
  visually confirm non-overlapping rows in the debug log
```

## Steps to Reapply on New PC

### Step 1: Create `src/debug_log.py`
New file — see full code in the "Debug-Log Redirection" section below.

### Step 2: Edit `src/Stage_v3_working_with_bleedair.py`
Add `import debug_log` at top. Replace 10 print calls with `debug_log.debug()` (listed below). Fix `stage` → `stage_to_calc` in `mLE_TE_cntr()`.

### Step 3: Edit `src/var_Grid.py`
Add `import debug_log` at top. Replace 11 print calls with `debug_log.debug()`. Fix `actual_tip_clearance` storage and write site. Open debug file in `process_grid_data()`. Add monotonicity check after `generate_var_grid_data()`.

### Step 4: Edit `src/Channel_v2.py`
Line 490: `*x0[0]` → `*(x0[0]-x0[1])`.

### Step 5: Edit `src/GUI.py`
Add `import debug_log`. Open debug file before `run_main_logic()`.

### All print → debug_log.debug replacements (21 total):
```
Stage_v3_working_with_bleedair.py (10):
  init_channel_data()                     Stage offset print
  run_main_logic()                        DEBUG LOOP START
  run_main_logic()                        DEBUG TYPE CHECK
  run_main_logic()                        --- Processing Stage {s} ---
  run_main_logic()                        DEBUG Stage {s}: b1[s-1]=...
  run_main_logic()                        VERIFY radial_data_R keys
  run_main_logic()                        DEBUG: radial_equilibrium_S Results
  calculation_of_section_0_5()            VERIFY overall_values
  mLE_TE_cntr()                           VERIFY mLE_TE_cntr (also fixed stage variable)
  calculation_of_section()                VERIFY overall_values

var_Grid.py (11):
  multall_grid_data_head_row()            Debug current_stage (x5)
  write_end_file()                        DEBUG: Starting/Inlet/PDOWN/Error (x6)
  generate_var_grid_data()                DEBUG row_num={row_num}
  process_grid_data()                     DEBUG TIPCLEARENCE (x1)
  process_grid_data()                     DEBUG row {global_row_num} (x6)
```

## Debug-Log Redirection (new file: `src/debug_log.py`)

```python
import os

_file_handle = None
_file_path = None

def open_file(file_path):
    global _file_handle, _file_path
    close_file()
    _file_path = file_path
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    _file_handle = open(file_path, "w", encoding="utf-8")

def debug(msg):
    if _file_handle is not None:
        _file_handle.write(str(msg) + "\n")
        _file_handle.flush()

def close_file():
    global _file_handle
    if _file_handle is not None:
        _file_handle.close()
        _file_handle = None

def file_path():
    return _file_path
```

## Verification Steps
1. Run GUI, load/calculate a multi-stage design (3 stages recommended)
2. Click "Create Default Profiles" (generates per-stage bezier data)
3. Click "Generate Grid"
4. Open `outputFiles/debug.txt` and check:
   - `init_channel_data` prints showing x0[1], x0[7], next offset per stage
   - `DEBUG row X (stage Y):` showing x_coords first/last — stage 2+ must start after stage 1
   - x-range monotonicity check: each row's min_x > previous row's max_x, Result: PASSED
5. Run MULTALL solver on the generated .dat file
6. Check MULTALL output for negative volumes / NaN velocities
7. For single-stage, verify no regression

## Remaining Concerns
- `channel()` has `start_x = getattr(..., 'current_x_offset', 0.0)` — dead code (always 0). If externally set, would double-offset with `init_channel_data()`. Unify or remove.
- `blade_metal_BP()` reads per-stage JSON keys — run `create_default_profiles()` after upgrading.
