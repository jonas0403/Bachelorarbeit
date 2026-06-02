"""Temporary debug script to analyze x-monotonicity failures."""
import sys
sys.path.insert(0, ".")
from tools.dat_validator import parse_dat

filepath = r"D:\Uni\Bachelorarbeit\test2\Bachelorarbeit\outputFiles\multall_grid_IM_37_KM_37_R_[96, 96]_S_[97, 97]_rows_2.dat"
data = parse_dat(filepath)

print("=== X-MONOTONICITY PER SECTION ===")
for sec in data["sections"]:
    x = sec["x"]
    non_mono = [j for j in range(1, len(x)) if x[j] < x[j-1] - 1e-12]
    if non_mono:
        first = non_mono[0]
        last = non_mono[-1]
        print(f"Row {sec['row']} Sec {sec['sec']}: {len(non_mono)} failures, "
              f"J={first}..{last}, "
              f"x[{first-1}]={x[first-1]:.6f} -> x[{first}]={x[first]:.6f}")

print("\n=== X-RANGE PER ROW (min/max across all sections) ===")
rows = {}
for sec in data["sections"]:
    r = sec["row"]
    if r not in rows:
        rows[r] = {"min": float("inf"), "max": -float("inf")}
    rows[r]["min"] = min(rows[r]["min"], min(sec["x"]))
    rows[r]["max"] = max(rows[r]["max"], max(sec["x"]))

for r in sorted(rows):
    print(f"Row {r}: x=[{rows[r]['min']:.4f}, {rows[r]['max']:.4f}]")

print("\n=== ROW 4 SEC 1 X_VALS AROUND TE ===")
for sec in data["sections"]:
    if sec["row"] == 4 and sec["sec"] == 1:
        x = sec["x"]
        JTE = data["row_meta"][4]["JTE"]  # 1-based
        for j in range(JTE - 2, min(JTE + 10, len(x))):
            marker = " <-- TE" if j == JTE - 1 else ""
            print(f"  J={j} (1-based): x={x[j]:.6f}{marker}")
        break

# Also check 1-stage file Row 2 for comparison
print("\n=== 1-STAGE FILE: Row 2 x-near-TE (for comparison) ===")
data1 = parse_dat(r"D:\Uni\Bachelorarbeit\test2\Bachelorarbeit\outputFiles\multall_grid_IM_37_KM_37_R_[96]_S_[97]_rows_2.dat")
for sec in data1["sections"]:
    if sec["row"] == 2 and sec["sec"] == 1:
        x = sec["x"]
        JTE = data1["row_meta"][2]["JTE"]
        for j in range(JTE - 2, min(JTE + 10, len(x))):
            marker = " <-- TE" if j == JTE - 1 else ""
            print(f"  J={j} (1-based): x={x[j]:.6f}{marker}")
        break

# Also check Row 3 (Stage 2 rotor)
print("\n=== ROW 3 (Stage 2 Rotor) X-MONOTONICITY ===")
for sec in data["sections"]:
    if sec["row"] == 3:
        x = sec["x"]
        non_mono = [j for j in range(1, len(x)) if x[j] < x[j-1] - 1e-12]
        if non_mono:
            print(f"  Sec {sec['sec']}: {len(non_mono)} non-mono at J={non_mono[0]}..{non_mono[-1]}")
        else:
            print(f"  Sec {sec['sec']}: OK")
