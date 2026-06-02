"""
.dat file validator for MULTALL grid output.

Parses a MULTALL .dat file and runs geometric validation checks:
  - x-monotonicity within each section
  - Inter-row x-continuity
  - Rtheta monotonicity along chord
  - Spanwise section ordering (hub-to-tip)
  - Thickness > 0 everywhere
  - Thickness < pitch (passage width > 0)
  - Hub/shroud radial continuity at interfaces
  - JM consistency across sections
  - R coordinate monotonicity hub->shroud

Usage:
    python -m tools.dat_validator <path_to_dat_file> [--verbose]
"""

import re
import math
import sys
import os
from collections import defaultdict


# ── PARSING ──────────────────────────────────────────────────────────────

ROW_HEADER_RE = re.compile(r"BLADE ROW NUMBER\s*=\s*(\d+)")
SECTION_RE = re.compile(r"ROW NUMBER\s+(\d+)\s+SECTION NUMBER\s+(\d+)")
SCALE_LINE_RE = re.compile(r"^\s*1\.0+\s")
NBLADES_RE = re.compile(r"NUMBER OF BLADES IN ROW\s*\n\s+(\d+)", re.MULTILINE)
JM_RE = re.compile(r"\s+JM\s+JLE\s+JTE\s*\n\s+(\d+)\s+(\d+)\s+(\d+)", re.MULTILINE)


def parse_dat(filepath):
    """Parse .dat file into structured list of rows and sections."""
    with open(filepath, "r") as f:
        text = f.read()
    lines = text.split("\n")

    # ---- extract global header info ----
    nrows_match = re.search(r"NUMBER OF BLADE ROWS\s*\n\s+(\d+)", text)
    nrows = int(nrows_match.group(1)) if nrows_match else None

    # ---- extract per-row metadata ----
    row_meta = {}
    for i in range(1, nrows + 1) if nrows else range(1, 100):
        nb = re.search(
            rf"BLADE ROW NUMBER\s*=\s*{i}\s*\n\s+NUMBER OF BLADES IN ROW\s*\n\s+(\d+)",
            text,
        )
        jm = re.search(
            rf"BLADE ROW NUMBER\s*=\s*{i}\s*\n.*?\n\s+JM\s+JLE\s+JTE\s*\n\s+(\d+)\s+(\d+)\s+(\d+)",
            text,
            re.DOTALL,
        )
        if nb and jm:
            row_meta[i] = {
                "n_blades": int(nb.group(1)),
                "JM": int(jm.group(1)),
                "JLE": int(jm.group(2)),
                "JTE": int(jm.group(3)),
            }

    # ---- parse section blocks by scanning line-by-line ----
    sections = []  # list of dicts: row, sec, x, rtheta, d, r

    def is_section_header(line):
        return SECTION_RE.search(line)

    def is_row_header(line):
        return ROW_HEADER_RE.search(line)

    def is_scale_or_empty(line):
        stripped = line.strip()
        # empty, "1.00000   0.00000", "1.000000", etc.
        return not stripped or re.match(r"^1\.0+\s", stripped) or stripped == "0"

    def parse_values_block(start_idx, lines, JM_expected=None):
        """Read values from lines[start_idx:] until a scale/header line, return (values, next_idx)."""
        values = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if is_section_header(line) or is_row_header(line):
                break
            if is_scale_or_empty(line):
                # If we already have values, the scale line ends the block
                if values:
                    break
                # skip leading scale lines
                i += 1
                continue
            # Actually try to parse numbers
            tokens = line.strip().split()
            nums = []
            for t in tokens:
                try:
                    nums.append(float(t))
                except ValueError:
                    pass
            if nums:
                values.extend(nums)
            i += 1
        # Trim or pad to JM_expected
        if JM_expected and len(values) != JM_expected:
            pass  # will be reported by validator
        return values, i

    i = 0
    current_row = None
    while i < len(lines):
        line = lines[i]
        m = is_row_header(line)
        if m:
            current_row = int(m.group(1))
            i += 1
            continue
        m = is_section_header(line)
        if m and current_row is not None:
            row_num = int(m.group(1))
            sec_num = int(m.group(2))
            meta = row_meta.get(row_num, {})
            JM = meta.get("JM", None)

            # Skip past section header, IF_DESIGN line, and "1.00000   0.00000    0" to reach first x-value line
            i += 3

            # Block 1: x-coordinates
            x_vals, i = parse_values_block(i, lines, JM)
            # After x: skip scale "1.000000  0.000000"
            if i < len(lines) and is_scale_or_empty(lines[i]):
                i += 1

            # Block 2: Rtheta upper surface
            rtheta_vals, i = parse_values_block(i, lines, JM)
            # After rtheta: skip scale "1.000000"
            if i < len(lines) and is_scale_or_empty(lines[i]):
                i += 1

            # Block 3: thickness d
            d_vals, i = parse_values_block(i, lines, JM)
            # After d: skip scale "1.000000  0.000000"
            if i < len(lines) and is_scale_or_empty(lines[i]):
                i += 1

            # Block 4: radius r
            r_vals, i = parse_values_block(i, lines, JM)

            sections.append(
                {
                    "row": row_num,
                    "sec": sec_num,
                    "x": x_vals,
                    "rtheta": rtheta_vals,
                    "d": d_vals,
                    "r": r_vals,
                }
            )
            continue
        i += 1

    return {
        "nrows": nrows,
        "row_meta": row_meta,
        "sections": sections,
        "filepath": filepath,
    }


# ── CHECKS ──────────────────────────────────────────────────────────────


def check_x_monotonicity(data):
    """Check x-coordinates are strictly increasing within each section."""
    issues = []
    for sec in data["sections"]:
        x = sec["x"]
        for j in range(1, len(x)):
            if x[j] < x[j - 1] - 1e-12:
                issues.append(
                    f"  Row {sec['row']} Sec {sec['sec']}: x[{j}]={x[j]:.6f} < x[{j-1}]={x[j-1]:.6f} (non-monotonic)"
                )
    return issues


def check_inter_row_x_continuity(data):
    """Check that rows don't overlap in x: row N max_x < row N+1 min_x."""
    issues = []
    row_bounds = {}
    for sec in data["sections"]:
        r = sec["row"]
        if r not in row_bounds:
            row_bounds[r] = {"min": float("inf"), "max": -float("inf")}
        row_bounds[r]["min"] = min(row_bounds[r]["min"], min(sec["x"]))
        row_bounds[r]["max"] = max(row_bounds[r]["max"], max(sec["x"]))

    sorted_rows = sorted(row_bounds.keys())
    for i in range(len(sorted_rows) - 1):
        r1 = sorted_rows[i]
        r2 = sorted_rows[i + 1]
        overlap = row_bounds[r1]["max"] - row_bounds[r2]["min"]
        gap = row_bounds[r2]["min"] - row_bounds[r1]["max"]
        if overlap > 1e-6:
            issues.append(
                f"  Row {r1} max_x={row_bounds[r1]['max']:.4f} > Row {r2} min_x={row_bounds[r2]['min']:.4f} (overlap={overlap:.4f}m)"
            )
        else:
            pass  # gap is fine (ISHIFT handles it)
    return issues


def check_rtheta_monotonicity(data):
    """Check Rtheta is monotonic along the chord WITHIN the blade passage (JLE to JTE).

    Upstream of LE and downstream of TE, Rtheta can freely vary (inlet/outlet duct).
    Only folding within the blade passage indicates camber-line problems.
    """
    issues = []
    for sec in data["sections"]:
        row = sec["row"]
        meta = data["row_meta"].get(row, {})
        JLE = meta.get("JLE", 1) - 1  # 0-based
        JTE = meta.get("JTE", 1) - 1
        rt = sec["rtheta"]
        if not rt or JLE >= len(rt) or JTE >= len(rt):
            continue
        blade_rt = rt[JLE:JTE+1]
        if len(blade_rt) < 3:
            continue
        decreasing = all(blade_rt[j] <= blade_rt[j - 1] + 1e-12 for j in range(1, len(blade_rt)))
        increasing = all(blade_rt[j] >= blade_rt[j - 1] - 1e-12 for j in range(1, len(blade_rt)))
        if not decreasing and not increasing:
            for j_rel in range(2, len(blade_rt)):
                d1 = blade_rt[j_rel - 1] - blade_rt[j_rel - 2]
                d2 = blade_rt[j_rel] - blade_rt[j_rel - 1]
                if d1 * d2 < -1e-12:  # sign change
                    j_abs = JLE + j_rel
                    issues.append(
                        f"  Row {row} Sec {sec['sec']}: Rtheta reverses at J={j_abs} "
                        f"(within blade, d1={d1:.6f}, d2={d2:.6f})"
                    )
                    break
    return issues


def check_thickness_positive(data):
    """Check blade thickness d > 0 everywhere (except upstream/downstream of blade)."""
    issues = []
    for sec in data["sections"]:
        d = sec["d"]
        neg_indices = [j for j, v in enumerate(d) if v < -1e-12]
        if neg_indices:
            sample = neg_indices[:5]
            issues.append(
                f"  Row {sec['row']} Sec {sec['sec']}: d < 0 at J indices {sample} (values: {[f'{d[j]:.6f}' for j in sample]})"
            )
    return issues


def check_thickness_vs_pitch(data):
    """Check d < pitch everywhere within the blade passage (JLE to JTE).

    Skips points where r=0 (tip clearance fictitious points, outside physical domain).
    """
    issues = []
    for sec in data["sections"]:
        row = sec["row"]
        meta = data["row_meta"].get(row, {})
        n_blades = meta.get("n_blades")
        JLE = meta.get("JLE", 1) - 1  # 0-based
        JTE = meta.get("JTE", 1) - 1
        if not n_blades or n_blades == 0:
            continue
        r = sec["r"]
        d = sec["d"]
        for j in range(max(0, JLE), min(len(r), JTE + 1)):
            if r[j] < 1e-10:
                continue  # skip fictitious tip-clearance points (r=0)
            pitch = 2 * math.pi * r[j] / n_blades
            if d[j] > pitch + 1e-12:
                issues.append(
                    f"  Row {row} Sec {sec['sec']} J={j}: d={d[j]:.6f} > pitch={pitch:.6f} (passage width negative)"
                )
    return issues


def check_section_span_ordering(data):
    """Check that sections within each row are ordered hub->tip by radius."""
    issues = []
    rows = defaultdict(list)
    for sec in data["sections"]:
        rows[sec["row"]].append(sec)

    for row, sections in sorted(rows.items()):
        valid = [s for s in sections if s["r"]]
        if len(valid) < 2:
            continue
        # Use average radius of first x-station as section height proxy
        r_avg = [sum(s["r"]) / len(s["r"]) for s in valid]
        for i in range(1, len(r_avg)):
            if r_avg[i] < r_avg[i - 1] - 1e-10:
                issues.append(
                    f"  Row {row}: Sec {sections[i]['sec']} (r_avg={r_avg[i]:.4f}) < Sec {sections[i-1]['sec']} (r_avg={r_avg[i-1]:.4f}) — non-monotonic span"
                )
    return issues


def check_radial_continuity(data):
    """Check hub/shroud continuity at inter-row interfaces (row N last sec vs row N+1 first sec)."""
    issues = []
    rows = defaultdict(list)
    for sec in data["sections"]:
        rows[sec["row"]].append(sec)

    sorted_rows = sorted(rows.keys())
    for i in range(len(sorted_rows) - 1):
        r1 = sorted_rows[i]
        r2 = sorted_rows[i + 1]
        r1_sections = [s for s in rows[r1] if s["r"]]
        r2_sections = [s for s in rows[r2] if s["r"]]
        if not r1_sections or not r2_sections:
            continue
        last_sec_r1 = r1_sections[-1]
        first_sec_r2 = r2_sections[0]
        # Compare hub (first section, first J) and shroud (last section, first J)
        r1_hub = last_sec_r1["r"][0]
        r1_shroud = last_sec_r1["r"][-1]
        r2_hub = first_sec_r2["r"][0]
        r2_shroud = first_sec_r2["r"][-1]

        dh = abs(r1_hub - r2_hub)
        ds = abs(r1_shroud - r2_shroud)
        tol = 0.001  # 1mm tolerance
        if dh > tol:
            issues.append(
                f"  Row {r1}->{r2}: hub radius jumps {r1_hub:.4f} -> {r2_hub:.4f} (delta={dh*1000:.1f} mm)"
            )
        if ds > tol:
            issues.append(
                f"  Row {r1}->{r2}: shroud radius jumps {r1_shroud:.4f} -> {r2_shroud:.4f} (delta={ds*1000:.1f} mm)"
            )
    return issues


def check_jm_consistency(data):
    """Check all sections within a row have same JM."""
    issues = []
    rows = defaultdict(list)
    for sec in data["sections"]:
        rows[sec["row"]].append(sec)

    for row, sections in sorted(rows.items()):
        lengths = set(len(s["x"]) for s in sections)
        if len(lengths) > 1:
            issues.append(
                f"  Row {row}: inconsistent JM values: {lengths}"
            )
    return issues


def check_r_monotonicity_spanwise(data):
    """Check radii are increasing hub->shroud at each axial station."""
    issues = []
    rows = defaultdict(list)
    for sec in data["sections"]:
        rows[sec["row"]].append(sec)

    for row, sections in sorted(rows.items()):
        valid = [s for s in sections if s["r"]]
        if len(valid) < 2:
            continue
        JM = len(valid[0]["r"])
        for j in range(JM):
            r_col = [valid[s]["r"][j] for s in range(len(valid))]
            for s in range(1, n_sec):
                if r_col[s] < r_col[s - 1] - 1e-10:
                    issues.append(
                        f"  Row {row} J={j}: Sec {sections[s]['sec']} r={r_col[s]:.4f} < Sec {sections[s-1]['sec']} r={r_col[s-1]:.4f}"
                    )
                    break
    return issues


# ── RUNNER ──────────────────────────────────────────────────────────────


def validate_dat(filepath, verbose=False):
    """Run all validation checks on a .dat file and print results."""
    print(f"\n{'='*70}")
    print(f"  Validating: {os.path.basename(filepath)}")
    print(f"{'='*70}")

    data = parse_dat(filepath)

    print(f"\n  File structure:")
    print(f"    Blade rows:     {data['nrows']}")
    n_sections = len(data["sections"])
    n_rows_actual = len(set(s["row"] for s in data["sections"]))
    print(f"    Sections total: {n_sections} across {n_rows_actual} rows")
    if data["row_meta"]:
        for r, m in sorted(data["row_meta"].items()):
            print(f"    Row {r}: {m['n_blades']} blades, JM={m['JM']}, JLE={m['JLE']}, JTE={m['JTE']}")

    checks = [
        ("X-Monotonicity (per section)", check_x_monotonicity),
        ("Inter-row X-Continuity", check_inter_row_x_continuity),
        ("Rtheta Monotonicity (camber-line)", check_rtheta_monotonicity),
        ("Thickness > 0", check_thickness_positive),
        ("Thickness < Pitch (passage width)", check_thickness_vs_pitch),
        ("Spanwise Section Ordering", check_section_span_ordering),
        ("Radial Continuity at Interfaces", check_radial_continuity),
        ("JM Consistency across Sections", check_jm_consistency),
        ("R Monotonicity Hub->Shroud", check_r_monotonicity_spanwise),
    ]

    all_passed = True
    for name, func in checks:
        issues = func(data)
        status = "PASS" if not issues else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"\n  [{status}] {name}")
        for issue in issues[:10]:
            print(issue)
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more issues")

    print(f"\n{'='*70}")
    if all_passed:
        print(f"  RESULT: ALL CHECKS PASSED")
    else:
        print(f"  RESULT: SOME CHECKS FAILED")
    print(f"{'='*70}\n")

    return all_passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tools.dat_validator <path_to_dat_file> [--verbose]")
        sys.exit(1)

    filepath = sys.argv[1]
    verbose = "--verbose" in sys.argv

    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    passed = validate_dat(filepath, verbose)
    sys.exit(0 if passed else 1)
