# Bug Investigation: Negative Volumes in MULTALL Multi-Stage Output

## History

### Phase 1 — Cumulative Offset Fix (committed in `7a6b6e4`)
The `init_channel_data()` function was not applying a cumulative x-offset to stage 2+ channel coordinates. Each stage's channel was computed in its local frame (starting at x=0), causing all stages to overlap spatially. The fix accumulates x-offset per stage so stage N starts where stage N-1 ends.

See the "Cumulative Offset Pipeline Trace" section below.

### Phase 2 — Coordinate Overlap Bug (May 22 session)
After the cumulative offset fix, the monotonicity check revealed that within-stage interfaces (rotor↔stator) are perfect, but **between-stage interfaces** (stator N → rotor N+1) still overlap by ~36 mm.

#### Root Cause
In `Channel_v2.py:448-449`, for internal stages (stage != 1):
```python
x0[0] = -1*round((x0[2]-x0[1])/(1-Rotor[0]), 0)  # ~ -0.667*l_R, typically -40 to -90 mm
```

This backward extrapolation of x0[0] is shifted by `cumulative_x_offset = previous_stage.x0[7]` in `init_channel_data()`, so stage N's far-inlet grid point lands BEFORE stage N-1's stator outlet.

#### Fix Applied (2026-05-22)
**File: `Channel_v2.py:446-457`**
Old code commented out, replaced with:
```python
if stage == 1:
    x0[0] = -inlet_dist * l_R
else:
    x0[0] = 0.0  # was: -1*round((x0[2]-x0[1])/(1-Rotor[0]), 0)
```

**File: `Stage_v3_working_with_bleedair.py:2158-2183`**
Added a DX_in clamp in `inlet_coordinates()` — when x0[0]=x0[1] for internal stages, DX_in ≈ 0 would cause division by zero. The clamp ensures a minimum |DX_in| of max(5% chord, 5 mm).

#### Outlet Area Bug Fix
**File: `Channel_v2.py:537-538`**
```python
# BUGFIX: was old_area * inlet_area (copy-paste error from intake block)
new_area = old_area * outlet_area
```

### Phase 3 — MULTALL Documentation Review (May 22 session)
MULTALL docs added to `Docs/` by user. Key findings:

#### ISHIFT = 2 (hardcoded in `var_Grid.py:307`)
```
ISHIFT    NEXTRAP_LE  NEXTRAP_TE
    2        10        10
```

From MULTALL docs (NOTE 12, second/newer PDF):  
**"ISHIFT = 2 the grids are moved so that they coincide at the mixing plane over the whole span and maintain the input stream surfaces."**

This means MULTALL **automatically shifts all coordinates** of the downstream row to make the mixing plane (J=JM of row N, J=1 of row N+1) coincident. This fixes the coordinate overlap during solver execution, but shifts blade positions from their intended design location.

**ISHIFT=2 is "strongly recommended"** by the MULTALL documentation, so our overlap is partially masked at the solver level. However, large overlap (> chord length) could still cause grid quality issues.

#### NSTG Values
Written as `(i // NROW) + 1` for each row, e.g. for 3 stages, NROW=2: `1 1 2 2 3 3`. This correctly assigns blades to stages.

#### Coordinate Format Rules
From MULTALL docs:
- Coordinates are in **meters** (free format, any scaling via FAC1-FAC4)
- JM (total points), JLE (LE index), JTE (TE index) must be consistent across all span sections
- Points upstream of LE and downstream of TE must be included with zero thickness (d=0)
- Multiple span sections (NSECS_IN) define the blade geometry

### Still Investigated
The root cause of **negative volumes in MULTALL** may include:
1. **~~Inter-stage coordinate overlap~~** — handled by ISHIFT=2, but now also fixed at the source
2. **Inconsistent units** — x_values in mm, r_values in meters, mixed in m_prime arc length calculation
3. **The `r_coords * 1000` hack** in `process_grid_data()` (`var_Grid.py:849-851`) — suggests radii may be in wrong units
4. **Annulus contour spline** — the `r0_N`/`r0_G` control points multiplied by 0.95/1.08 could produce non-monotonic hub/shroud at extreme spans
5. **Blade thickness > pitch** — if Rtheta thickness from the Bezier control points exceeds the blade pitch

## Cumulative Offset Pipeline Trace

```
channel_data[stage]['x_values']  (mm, correctly offset)
    ↓
coordinates(row=3):  stage=(3-1)//2+1=2, reads channel_data[2]['x_values']
    ↓  intpol(m_star_u, m_prime_values, x_values) → x_u values are OFFSET
    ↓
calculation_blade_coordinates(): x_sec = intpol(..., x_u) / 1000 → meters, OFFSET
    ↓
inlet_coordinates(): DX_in = x0[0]/1000 - x_sec[i][0] → local (both offset, diff is same)
    ↓  x_in = x_sec[i][0] + DX_in * (1 - l_in) → meters, OFFSET
    ↓
calc_blade_row_coordinates() → merge → levels → x_new (meters, OFFSET)
    ↓
generate_var_grid_data() stores x_new in all_rows_grid_data
    ↓
process_grid_data() writes x_new to MULTALL .dat file  ✓
```

## Overlap Pattern (BEFORE x0[0] fix)
From debug output:
```
Row 1 (stage1 rotor):  x=[-0.2025, 0.1495]  OK
Row 2 (stage1 stator): x=[0.1495, 0.2720]   *** OVERLAP ***  (false positive — equals prev max)
Row 3 (stage2 rotor):  x=[0.2359, 0.4179]   *** OVERLAP ***  (36 mm overlap with row 2)
Row 4 (stage2 stator): x=[0.4179, 0.5219]   *** OVERLAP ***  (false positive)
Row 5 (stage3 rotor):  x=[0.4930, 0.6106]   *** OVERLAP ***  (19 mm overlap with row 4)
Row 6 (stage3 stator): x=[0.6106, 0.7015]   *** OVERLAP ***  (false positive)
```

Note: within-stage interfaces (rotor→stator) are exact matches. Only rotor rows in internal stages overlap.

## X0 Index Reference

| Index | Purpose | Used By | Local Value (Stage 1) | Local Value (Stage 2+) |
|-------|---------|---------|----------------------|------------------------|
| 0 | Far inlet (upstream duct) | `inlet_coordinates` k=0 (rotors) | `-inlet_dist * l_R` | **0.0** (was `-0.667*l_R`) |
| 1 | Rotor LE / matching plane | Channel spline | 0.0 | 0.0 |
| 2 | Rotor LE geometry | Channel spline | `0.4 * l_R` | `0.4 * l_R` |
| 3 | Rotor TE | Channel spline, `inlet_coordinates` k=3 (stators), `outlet_coordinates` k=3 (rotors) | — | — |
| 4 | Inter-row midpoint | Channel spline | — | — |
| 5 | Stator LE | Channel spline | — | — |
| 6 | Stator TE | Channel spline, `outlet_coordinates` k=6 (stators) | — | — |
| 7 | Stator outlet / offset reference | Channel spline, cumulative offset | — | — |
| 8 | Far outlet (downstream duct) | Channel spline only | `outlet_dist * l_S` | Extrapolated |

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

## Debug-Log Redirection (`src/debug_log.py`)

```python
import os
from datetime import datetime

_file_handle = None
_file_path = None

def open_file(file_path):
    global _file_handle, _file_path
    close_file()
    _file_path = file_path
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    _file_handle = open(file_path, "w", encoding="utf-8")
    _write("[DEBUG LOG OPEN] " + os.path.abspath(file_path))

def close_file():
    global _file_handle
    if _file_handle is not None:
        _write("[DEBUG LOG CLOSED]")
        _file_handle.close()
        _file_handle = None

def _write(msg):
    if _file_handle is not None:
        _file_handle.write(msg + "\n")
        _file_handle.flush()

def debug(msg, context=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    if context:
        _write(f"[{ts}] [{context}] {msg}")
    else:
        _write(f"[{ts}] {msg}")

def section(title):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    _write("")
    _write(f"{'='*60}")
    _write(f"[{ts}] {title}")
    _write(f"{'='*60}")

def file_path():
    return _file_path
```

## Verification Steps
1. Run GUI, load/calculate a multi-stage design (3 stages recommended)
2. Click "Create Default Profiles" (generates per-stage bezier data)
3. Click "Generate Grid"
4. Open `Docs/Output/debug.txt` and check:
   - `init_channel_data` prints showing x0[1], x0[7], next offset per stage
   - `DEBUG row X (stage Y):` showing x_coords first/last — stage 2+ may still show minor overlap (from 5 mm default DX_in)
   - x-range monotonicity check: result may show minor overlap from the default inlet, reduced from 36 mm to ~5 mm per stage
5. Run MULTALL solver on the generated .dat file
6. Check MULTALL output for negative volumes / NaN velocities
7. For single-stage, verify no regression

## MULTALL Documentation Available
The following docs were added by the user to `Docs/`:
- `README.pdf` — System overview
- `General-description.pdf` — Solver algorithm description
- `new-readin-input-data-20.9 .pdf` — Data input format (v20.9)
- `new-readin-input-data (2).pdf` — Data input format (newer, revised)
- `10stg-compr-17.4.dat` — Example 10-stage compressor output

Key finding: MULTALL uses ISHIFT=2 to automatically make grid planes coincident at mixing planes, which partially masks coordinate overlap.
