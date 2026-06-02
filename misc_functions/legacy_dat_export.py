import os

# --- 1. CONFIGURATION ---
# Please change these values to match your setup.

# Specify the folder where your template file is located.
SOURCE_FOLDER = r'C:\Users\Jonas\sciebo\Geometriegenerator\Studenten\Scholz\Code\Multall\Ergebnisse\Bleedair\aspirated_stators_v2\08xRPM\aspirated_stators_5mflow_08xRPM'

# Specify the folder where you want to save the new files.
OUTPUT_FOLDER = SOURCE_FOLDER

# The name of the master input file to use as a template.
BASE_FILENAME = 'stage_1_11.dat'

# The exact line number you want to change in the file.
TARGET_LINE_NUMBER = 1762

# The string template for the new output filenames.
OUTPUT_FILENAME_TEMPLATE = 'aspirated_stators_08xRPM_5mflow_{}hPa.dat'

# --- Define the overall range and the STANDARD step size ---
START_VALUE = 100000.0
END_VALUE = 150000.0
STEP_VALUE = 5000.0

# --- Define the SPECIAL interval and its step size ---
# This interval starts at START_VALUE and goes up to the value specified here.
# For values *after* this point, the standard STEP_VALUE will be used.
SPECIAL_INTERVAL_END = 120000.0
SPECIAL_STEP_VALUE = 2500.0


# --- 2. SCRIPT LOGIC (No need to edit below this line) ---

def generate_files():
    """
    Reads a base file, modifies a specific line with a range of values
    using different step sizes for different intervals, and saves new files.
    """
    print("--- Starting File Generation ---")

    full_base_path = os.path.join(SOURCE_FOLDER, BASE_FILENAME)

    # --- Read the base template file into memory ---
    try:
        with open(full_base_path, 'r') as f:
            lines = f.readlines()
        print(f"Successfully read base file: '{full_base_path}'")
    except FileNotFoundError:
        print(f"Error: The base file '{full_base_path}' was not found.")
        print("Please check the SOURCE_FOLDER and BASE_FILENAME variables.")
        return

    # --- Validate the file length ---
    if len(lines) < TARGET_LINE_NUMBER:
        print(f"Error: The file '{BASE_FILENAME}' has only {len(lines)} lines, but the script needs to modify line {TARGET_LINE_NUMBER}.")
        return

    # --- Create the output directory if it doesn't exist ---
    if not os.path.exists(OUTPUT_FOLDER):
        try:
            os.makedirs(OUTPUT_FOLDER)
            print(f"Created output directory: '{OUTPUT_FOLDER}'")
        except OSError as e:
            print(f"Error: Could not create output directory '{OUTPUT_FOLDER}'. Reason: {e}")
            return

    # --- Loop through the specified range using a while loop for flexibility ---
    current_value = START_VALUE
    file_counter = 0

    print("\n--- Generating Files ---")
    while current_value <= END_VALUE:
        # Create the new line content and filename
        # The formatting ensures the value has one decimal place, e.g., 100000.0
        new_line = f"  {current_value:.1f}  {current_value:.1f}\n"
        
        # Format the pressure code for the filename (e.g., 1000hPa, 1025hPa)
        # It takes the integer part of the value and divides by 100
        pressure_code = int(current_value / 100)
        new_filename = OUTPUT_FILENAME_TEMPLATE.format(pressure_code)
        
        full_output_path = os.path.join(OUTPUT_FOLDER, new_filename)

        # Create a new list of lines with the modification
        new_lines = list(lines)
        new_lines[TARGET_LINE_NUMBER - 1] = new_line

        # Write the new file to disk
        try:
            with open(full_output_path, 'w') as f:
                f.writelines(new_lines)
            print(f"-> Created: {new_filename} with value {current_value:.1f}")
            file_counter += 1
        except IOError as e:
            print(f"Error: Could not write file '{full_output_path}'. Reason: {e}")

        # --- Logic to determine the next step size ---
        # If the current value is within the special interval, use the special step.
        if current_value < SPECIAL_INTERVAL_END:
            current_value += SPECIAL_STEP_VALUE
        # Otherwise, use the standard step.
        else:
            current_value += STEP_VALUE

    print(f"\n--- File Generation Complete ---")
    print(f"Total files created: {file_counter}")


if __name__ == "__main__":
    generate_files()