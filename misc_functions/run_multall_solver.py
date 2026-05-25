"""
Headless MULTALL solver runner.
Usage:
    python misc_functions/run_multall_solver.py <dat_file> [--continue Y|N]
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Run MULTALL solver on a .dat file")
    parser.add_argument("dat_file", help="Path to the .dat file")
    parser.add_argument("--continue", dest="continue_answer", default="Y", choices=["Y", "N"])
    parser.add_argument("--multall-dir", default=None)
    args = parser.parse_args()

    dat_file = os.path.abspath(args.dat_file)
    if not os.path.exists(dat_file):
        print(f"ERROR: .dat file not found: {dat_file}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    multall_dir = args.multall_dir if args.multall_dir else os.path.join(script_dir, "Run_Multall")
    multall_dir = os.path.abspath(multall_dir)
    multall_exe = os.path.join(multall_dir, "multall.exe")

    if not os.path.exists(multall_exe):
        print(f"ERROR: multall.exe not found in {multall_dir}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dat_basename = os.path.splitext(os.path.basename(dat_file))[0]
    log_file = os.path.join(multall_dir, f"multall_run_{dat_basename}_{timestamp}.log")

    print(f"MULTALL Runner")
    print(f"  Multall dir: {multall_dir}")
    print(f"  Data file:   {dat_file}")
    print(f"  Log file:    {log_file}")

    with open(os.path.join(multall_dir, "fort.1"), "w") as f:
        f.write(args.continue_answer + "\n")
    print(f"  Wrote '{args.continue_answer}' to fort.1")

    cmd = f'multall.exe < "{dat_file}"'
    print(f"  Running: {cmd}")

    t_start = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=multall_dir,
            capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired:
        msg = "MULTALL timed out after 600 seconds."
        print(f"\n{msg}")
        with open(log_file, "w") as f:
            f.write(msg + "\n")
        sys.exit(1)
    except Exception as e:
        msg = f"MULTALL failed: {e}"
        print(f"\n{msg}")
        with open(log_file, "w") as f:
            f.write(msg + "\n")
        sys.exit(1)

    elapsed = time.time() - t_start
    stdout = result.stdout or ""
    stderr = result.stderr or ""

    with open(log_file, "w") as f:
        f.write(f"MULTALL Run: {dat_file}\n")
        f.write(f"Started: {datetime.fromtimestamp(t_start).strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Elapsed: {elapsed:.2f}s\n")
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"{'='*60}\nSTDOUT:\n{'='*60}\n")
        f.write(stdout)
        f.write(f"\n{'='*60}\nSTDERR:\n{'='*60}\n")
        f.write(stderr)

    print(f"Return code: {result.returncode}")
    print(f"Elapsed: {elapsed:.2f}s")

    if stdout:
        print(f"\n{'='*60}\nSTDOUT (last 80 lines):\n{'='*60}")
        lines = stdout.splitlines()
        for line in lines[-80:]:
            print(line)

    if stderr:
        print(f"\n{'='*60}\nSTDERR:\n{'='*60}\n{stderr}")

    print(f"\nFull output saved to: {log_file}")


if __name__ == "__main__":
    main()
