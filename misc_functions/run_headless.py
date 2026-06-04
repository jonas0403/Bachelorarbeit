"""
Headless runner for MULTALL Stage Generator.
Runs the full pipeline (meanline -> channel -> radial equilibrium -> grid output)
without any GUI interaction. Useful for debugging and automated testing.

Usage:
    python run_headless.py [--json static/Populated_data.json] [--output outputFiles/]
"""

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from types import SimpleNamespace

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

if sys.argv[0]:
    sys.argv[0] = os.path.abspath(sys.argv[0])
else:
    sys.argv[0] = os.path.abspath(__file__)

import tkinter as tk

import debug_log
from thermodynamic_calculation import Thermo
from meanline import meanline
from stage_calculation import run_main_logic, init_channel_data, create_default_profiles
import grid_generator as VG


def load_json_or_die(path):
    if not os.path.exists(path):
        print(f"ERROR: JSON file not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)


def build_compressor_gui_data(json_data, output_path):
    cg = SimpleNamespace()
    all_data = json_data
    thermo_input = all_data.get("Thermodynamic_input_data", {})
    meanline_input = all_data.get("Meanline_input_data", {})
    diameter_data = all_data.get("Diameter_data", {})
    grid_data = all_data.get("Grid_data", {})
    metadata = all_data.get("Metadata", {})
    bleed_air_data = all_data.get("Bleed_air_data", {})

    stages_total = len(meanline_input.get("n", [3]))
    # stages_total = min(stages_total, 2)  # TEMP: force 2 stages for diagnostic
    cg.stage = stages_total
    cg.stages_to_calc = stages_total

    root = tk.Tk()
    root.withdraw()

    cg.inlet_area_var = tk.DoubleVar(value=all_data.get("Intake_Outtake_area", {}).get("inlet_area", 1.0))
    cg.inlet_dist_var = tk.DoubleVar(value=all_data.get("Intake_Outtake_area", {}).get("inlet_dist", 1.5))
    cg.outlet_area_var = tk.DoubleVar(value=all_data.get("Intake_Outtake_area", {}).get("outlet_area", 1.0))
    cg.outlet_dist_var = tk.DoubleVar(value=all_data.get("Intake_Outtake_area", {}).get("outlet_dist", 2.0))

    cg.prepop_grid_data = grid_data
    cg.prepop_metadata = metadata
    cg.prepop_bleed_air_data = bleed_air_data

    debug_log.section("Thermodynamic calculation")
    thermodata = Thermo(
        thermo_input.get("p_t_in", 101325),
        thermo_input.get("T_t_in", 293.15),
        thermo_input.get("mflow", 60.0),
        thermo_input.get("R", 287.0),
        thermo_input.get("cp", 1004.5),
        thermo_input.get("TPR", 2.4),
        stages_total
    )
    cg.Thermodata = thermodata
    debug_log.debug(f"Thermodata keys: {list(thermodata.keys())}", context="headless")

    debug_log.section("Meanline calculation")
    debug_log.dump_var("thermodata keys", list(thermodata.keys()), context="headless")
    debug_log.dump_var("meanline_input keys", list(meanline_input.keys()), context="headless")
    debug_log.dump_var("diameter_data", diameter_data, context="headless")

    meanline_result = meanline(thermodata, meanline_input, diameter_data, plot_channel_contour=False)
    cg.meanline_data = meanline_result
    debug_log.debug("meanline calculation complete", context="headless")
    debug_log.dump_var("meanline_result keys", list(meanline_result.keys()), context="headless")

    cg.bleed_air_data = bleed_air_data

    if "Bezier_point_data" in all_data:
        cg.prepop_bezier_point_rotor = all_data["Bezier_point_data"]
        cg.prepop_bezier_point_stator = all_data["Bezier_point_data"]

    level_str = metadata.get("levels", "0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.0")
    if isinstance(level_str, str):
        cg.prepop_metadata["levels"] = [float(x.strip()) for x in level_str.split(",")]
    else:
        cg.prepop_metadata["levels"] = [float(x) for x in level_str]

    if not cg.prepop_metadata.get("output_folder"):
        cg.prepop_metadata["output_folder"] = output_path

    return cg


def main():
    parser = argparse.ArgumentParser(description="Headless MULTALL grid generator")
    parser.add_argument("--json", default="static/Populated_data.json")
    parser.add_argument("--output", default="outputFiles")
    args = parser.parse_args()

    json_path = os.path.abspath(args.json)
    output_path = os.path.abspath(args.output)
    os.makedirs(output_path, exist_ok=True)

    debug_log_path = os.path.join(output_path, "debug_headless.txt")
    debug_log.open_file(debug_log_path)

    debug_log.section("Headless Run Started")
    debug_log.debug(f"JSON path: {json_path}", context="headless")
    debug_log.debug(f"Output path: {output_path}", context="headless")

    t_start = time.time()

    debug_log.section("Step 1: Loading JSON data")
    json_data = load_json_or_die(json_path)

    debug_log.section("Step 2: Building compressor GUI data proxy")
    cg = build_compressor_gui_data(json_data, output_path)

    debug_log.section("Step 3: Running main calculation logic")
    t1 = time.time()
    try:
        run_main_logic({"main_choice": "default"}, cg, json_path)
    except Exception as e:
        debug_log.debug(f"CRASH in run_main_logic: {e}", context="headless")
        debug_log.debug(traceback.format_exc(), context="headless")
        print(f"\nERROR: run_main_logic crashed: {e}")
        debug_log.close_file()
        sys.exit(1)
    t2 = time.time()
    debug_log.debug(f"run_main_logic completed in {t2 - t1:.2f}s", context="headless")

    debug_log.section("Step 4: Saving updated data to JSON")
    json_data["Metadata"] = cg.prepop_metadata
    json_data["Grid_data"] = cg.prepop_grid_data
    json_data["Bleed_air_data"] = cg.prepop_bleed_air_data
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=4)

    debug_log.section("Step 5: Generating default blade profiles from radial equilibrium data")
    t_profile = time.time()
    try:
        create_default_profiles(cg, json_path)
    except Exception as e:
        debug_log.debug(f"CRASH in create_default_profiles: {e}", context="headless")
        debug_log.debug(traceback.format_exc(), context="headless")
        print(f"\nERROR: create_default_profiles crashed: {e}")
        debug_log.close_file()
        sys.exit(1)
    t_profile_end = time.time()
    debug_log.debug(f"create_default_profiles completed in {t_profile_end - t_profile:.2f}s", context="headless")

    debug_log.section("Step 6: Generating grid and writing MULTALL .dat file")
    t3 = time.time()
    try:
        VG.process_grid_data(json_path, cg)
    except Exception as e:
        debug_log.debug(f"CRASH in process_grid_data: {e}", context="headless")
        debug_log.debug(traceback.format_exc(), context="headless")
        print(f"\nERROR: process_grid_data crashed: {e}")
        debug_log.close_file()
        sys.exit(1)
    t4 = time.time()
    debug_log.debug(f"Grid generation took {t4 - t3:.2f}s", context="headless")

    elapsed = time.time() - t_start
    debug_log.section("Headless Run Complete")
    debug_log.debug(f"Total time: {elapsed:.2f}s", context="headless")
    debug_log.close_file()

    dat_files = sorted(
        [f for f in os.listdir(output_path) if f.endswith(".dat")],
        key=lambda f: os.path.getmtime(os.path.join(output_path, f)),
        reverse=True
    )

    print(f"\n{'='*60}")
    print(f"Headless run completed successfully.")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Debug log:  {debug_log_path}")
    if dat_files:
        print(f"  Output .dat: {os.path.join(output_path, dat_files[0])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
