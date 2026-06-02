# MULTALL Stage Generator

A Python-based graphical preprocessor replacing the Fortran-coded **MEANGEN** and **STAGEN** modules of the [MULTALL](https://sites.google.com/view/multall-turbomachinery-design) turbomachinery CFD solver suite.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [JSON Project Files](#json-project-files)
- [Contributing](#contributing)
- [Background & References](#background--references)
- [License](#license)
- [Contact](#contact)

---

## About

**MULTALL Stage Generator** is an open-source Python/Tkinter GUI application developed as part of Bachelor's theses at **FH Aachen University of Applied Sciences**, Faculty of Aerospace Engineering, in the course *Turbomachinery Design and Analysis* supervised by **Prof. Grates**.

The project was originally initiated in 2025 by **Jonas Scholz** and **Luca De Francesco**, building upon foundational work by **Marco Wiens**, whose earlier Bachelor's thesis laid the groundwork for the Python-based replacement of MULTALL's preprocessing pipeline.

MULTALL is a well-established CFD solver for turbomachinery developed by John Denton at Cambridge University. Its preprocessing chain traditionally relies on two Fortran programs:

- **MEANGEN** — Meanline design and thermodynamic cycle analysis
- **STAGEN** — Streamline curvature and radial equilibrium calculations

This tool replaces both with a modern, interactive GUI, making the preprocessing workflow more accessible, maintainable, and extensible for students and researchers.

---

## Features

- **Full GUI** — Tkinter-based input for all meanline, radial equilibrium, and grid parameters
- **JSON project files** — Save, load, and share complete design configurations
- **Meanline design** — Thermodynamic cycle calculation with multi-stage support
- **Radial equilibrium** — Streamline curvature solver with configurable span sections
- **Multi-stage** — Supports single-stage and multi-stage compressors with bleed air modelling
- **Blade profiling** — Bezier-curve blade angle profiles with automatic generation from radial equilibrium
- **Grid generation** — Variable grid with configurable sections, levels, and refinement
- **MULTALL export** — Direct `.dat` output file generation compatible with the MULTALL solver
- **Headless pipeline** — Run the full workflow from the command line without the GUI
- **Compressor maps** — Generate multiple `.dat` files with varying pressure ratios and batch run scripts
- **Debug logging** — Comprehensive debug output with timestamps, sections, and context tags

---

## Quickstart

### Requirements

- Python 3.9 or higher
- Third-party packages:

```bash
pip install numpy matplotlib scipy
```

The following packages are part of the Python standard library: `tkinter`, `os`, `sys`, `shutil`, `json`, `math`, `csv`, `subprocess`, `pathlib`, `atexit`.

> **Note:** `tkinter` is included with most standard Python installations. If missing, install via your OS package manager (e.g. `sudo apt install python3-tk` on Ubuntu).

### Clone & Run

```bash
git clone https://github.com/jonas0403/MULTALL-Stage-Generator.git
cd MULTALL-Stage-Generator
python main.py
```

### Headless Pipeline (No GUI)

For automated or debugging runs without the GUI:

```bash
python main.py --headless --json static/Populated_data.json --output outputFiles
```

This runs the full workflow — meanline, radial equilibrium, blade profiling, and grid generation — and writes the MULTALL `.dat` file and a debug log to the output directory. The JSON file is updated in place with the generated metadata and grid data.

> **Tip:** Back up your JSON before a headless run:
> ```powershell
> Copy-Item static/Populated_data.json static/Populated_data.json.bak
> ```

---

## Usage

### GUI Mode

1. Launch the application: `python main.py`
2. On startup, values are loaded from the project JSON file into the GUI input fields
3. Configure your turbomachinery design across the input tabs (thermodynamics, meanline, geometry, bleed air, grid settings)
4. Save your configuration at any time via the GUI
5. Run the meanline and radial equilibrium calculations
6. Review results in the visualization panels
7. Generate blade profiles from the radial equilibrium data
8. Export the MULTALL-compatible `.dat` output file

### Compressor Map Generation

The "Other-Settings" tab provides tools for running parametric MULTALL studies:

1. Generate a single grid `.dat` file via the grid generation workflow
2. Enable "Create multiple DAT files for compressor map"
3. Configure the pressure range (start, end, step) and filename template
4. Click "Generate Outputfile" to create multiple `.dat` files with varying back pressure
5. Optionally generate a batch script (`run_all.bat`) to execute all cases through MULTALL
6. Check "Run MULTALL after generation" to launch the solver automatically

### Configuration Files

| File | Purpose |
|------|---------|
| `static/Populated_data.json` | Main project file — all design parameters |
| `static/Setting.txt` | Default output folder path |
| `static/Meanline_Initial_Values.txt` | Default meanline parameters |
| `static/Thermo_Initial_Values.txt` | Default thermodynamic parameters |
| `static/Diameter_Values.txt` | Default diameter/hub/shroud values |

---

## Project Structure

```
MULTALL-Stage-Generator/
├── main.py                                  # Entry point (GUI or headless)
├── src/
│   ├── GUI.py                               # Main Tkinter GUI application (3050+ lines)
│   ├── stage_calculation.py                 # Core stage calculation & coordinate pipeline
│   ├── grid_generator.py                    # MULTALL grid generation & .dat file export
│   ├── channel.py                           # Flow channel geometry (annulus contour)
│   ├── Radial_equilibrium.py                # Radial equilibrium solver
│   ├── meanline.py                          # Meanline calculation module
│   ├── thermodynamic_calculation.py         # Thermodynamic cycle calculations
│   ├── Bezier_curve.py                      # Bezier curve interpolation
│   ├── cubic_spline.py                      # Cubic spline interpolation
│   ├── Interpolation.py                     # Interpolation utilities
│   ├── loss_models.py                       # Loss model functions
│   ├── debug_log.py                         # Structured debug logging module
│   ├── plot_channel.py                      # Channel geometry visualization
│   ├── run_multall.py                       # MULTALL solver interface
│   └── __init__.py
├── misc_functions/
│   ├── run_headless.py                      # Headless pipeline runner
│   ├── generate_dat_files_multiple.py       # Compressor map DAT file generation
│   ├── generate_run_batch.py                # Batch script creation for MULTALL runs
│   ├── run_multall_solver.py                # MULTALL solver launcher
│   ├── compressor_map_plotting.py           # Compressor map plotting
│   ├── plotting_program.py                  # General plotting utilities
│   ├── data_importer.py                     # Data import utilities
│   ├── legacy_dat_export.py                 # Legacy DAT file creation
│   └── create_run_config.py                 # Run configuration file creation
├── static/
│   ├── Populated_data.json                  # Main project data file
│   ├── Populated_data.template.json         # Template with placeholder values
│   ├── Setting.txt                          # Default output folder configuration
│   ├── Meanline_Initial_Values.txt          # Default meanline values
│   ├── Thermo_Initial_Values.txt            # Default thermodynamic values
│   ├── Diameter_Values.txt                  # Default diameter values
│   ├── bezier_control_points_R.txt          # Rotor bezier control points
│   ├── bezier_control_points_S.txt          # Stator bezier control points
│   └── image/                               # Screenshots and visualizations
├── tools/
│   ├── dat_validator.py                     # MULTALL .dat file validation
│   └── _debug_analysis.py                   # Debug analysis utilities
├── Docs/
│   ├── AGENTS.md                            # Development session log
│   ├── BugInvestigation.md                  # Bug analysis documentation
│   ├── Negative_Volume_Debug_Log.md         # Negative volume root cause analysis
│   ├── Root_Cause_Investigation_Plan.md     # Investigation methodology
│   ├── 10stg-compr-17.4.dat                # Reference 10-stage compressor output
│   └── README.pdf                           # MULTALL system overview (original docs)
├── Run_Multall/                             # MULTALL solver binaries & runtime
│   ├── multall.exe                          # MULTALL CFD solver
│   ├── multall2dat.exe                      # MULTALL output converter
│   └── multall2py.exe                       # MULTALL Python interface
└── outputFiles/                             # Generated grid output files (gitignored)
```

---

## JSON Project Files

All calculation inputs are stored in a single `.json` file. This file serves as both the persistent settings store and the input format for the calculation backend. You can either configure everything through the GUI or write values directly into the JSON before starting.

The JSON is structured into the following top-level sections:

| Section | Description |
|---------|-------------|
| `Thermodynamic_input_data` | RPM, mass flow, pressure ratio, efficiencies, gas properties |
| `Meanline_input_data` | Per-stage diameters, chord lengths, blade counts, solidity, angles |
| `Diameter_data` | Hub, mean, and shroud diameter distributions |
| `Bezier_point_data` | Blade angle control points for Bezier profiling |
| `Metadata` | Grid settings, output paths, levels configuration |
| `Grid_data` | Grid dimensions (IM, JM, KM), section definitions |
| `Bleed_air_data` | Bleed air mass flow and position per stage |
| `Intake_Outtake_area` | Inlet and outlet duct areas |

A template file with placeholder values is available at `static/Populated_data.template.json`.

---

## Contributing

Forks and pull requests are welcome.

1. **Fork** this repository
2. Create a new branch for your feature or fix: `git checkout -b feature/your-feature-name`
3. Commit your changes with clear messages
4. Open a **Pull Request** describing what you changed and why

Please ensure your code is reasonably documented and does not break existing functionality before submitting.

---

## Background & References

- **MULTALL** — J.D. Denton, Cambridge University — Turbomachinery CFD solver
- **MEANGEN / STAGEN** — Original Fortran preprocessing programs by J.D. Denton
- **Turbomachinery Design and Analysis** — Course at FH Aachen, Faculty of Aerospace Engineering, Prof. Grates
- **Marco Wiens** — Original Python preprocessing codebase (Bachelor's Thesis, FH Aachen)
- **Jonas Scholz & Luca De Francesco** — GUI development, restructuring, and multi-stage extensions (Bachelor's Theses, FH Aachen, 2025)

---

## License

This project is intended for academic use. Please contact the authors or FH Aachen for licensing clarifications before using this in a commercial context.

---

## Contact

For questions related to the project, feel free to open a [GitHub Issue](https://github.com/jonas0403/MULTALL-Stage-Generator/issues) or reach out via the FH Aachen Faculty of Aerospace Engineering.
