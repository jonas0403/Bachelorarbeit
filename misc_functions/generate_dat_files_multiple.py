import os
import sys


def find_target_line_index(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'PDOWN_HUB' in line and 'PDOWN_TIP' in line:
            return i + 1
    raise ValueError(
        f"Could not find 'PDOWN_HUB   PDOWN_TIP' in {file_path}"
    )


def generate_multiple_dat_files(source_file, output_folder, start, end, step, filename_template):
    if not os.path.isfile(source_file):
        raise FileNotFoundError(f"Source file not found: {source_file}")

    os.makedirs(output_folder, exist_ok=True)

    with open(source_file, 'r') as f:
        lines = f.readlines()

    target_idx = find_target_line_index(source_file)

    if target_idx >= len(lines):
        raise ValueError(
            f"Target line index {target_idx} exceeds file length {len(lines)}"
        )

    current = start
    file_counter = 0
    while current <= end:
        new_lines = list(lines)
        new_lines[target_idx] = f"  {current:.1f}  {current:.1f}\n"

        value_int = int(round(current))
        filename = filename_template.replace('{}', str(value_int))
        output_path = os.path.join(output_folder, filename)

        with open(output_path, 'w') as f:
            f.writelines(new_lines)

        file_counter += 1
        current += step

    return file_counter
