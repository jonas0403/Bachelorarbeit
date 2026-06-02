#!/usr/bin/env python3
"""MULTALL Stage Generator — Entry Point

Launches the GUI application by default. Supports headless mode for
batch processing via the --headless flag.

Usage:
    python main.py                            # Launch GUI
    python main.py --headless --json <path>   # Headless grid generation
"""

import os
import sys
import argparse

# Change to project root so relative imports resolve correctly
_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(_ROOT)

# Ensure src/ is on the path
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main():
    parser = argparse.ArgumentParser(
        description="MULTALL Stage Generator — GUI and headless preprocessing tool"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run in headless mode (no GUI). Requires --json."
    )
    parser.add_argument(
        "--json", type=str, default=None,
        help="Path to the JSON project file"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory for generated files (default: outputFiles/)"
    )

    args, _ = parser.parse_known_args()

    if args.headless:
        _run_headless(args.json, args.output)
    else:
        _run_gui()


def _run_headless(json_path, output_path):
    """Launch the headless pipeline in a subprocess."""
    import subprocess

    headless_script = os.path.join(_ROOT, "misc_functions", "run_headless.py")
    cmd = [sys.executable, headless_script]

    if json_path:
        cmd += ["--json", os.path.abspath(json_path)]
    if output_path:
        cmd += ["--output", os.path.abspath(output_path)]

    sys.exit(subprocess.call(cmd))


def _run_gui():
    """Launch the Tkinter GUI."""
    from src.GUI import render_gui
    render_gui()


if __name__ == "__main__":
    main()
