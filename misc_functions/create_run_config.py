import os

# --- Configuration ---
# Define the target directory ONCE. This is where it will look for .dat files
# and where it will save the output .bat file.
target_directory = r'C:\Users\Jonas\sciebo\Geometriegenerator\Studenten\Scholz\Code\Multall\Ergebnisse\Bleedair\aspirated_stators_v2\08xRPM\aspirated_stators_5mflow_08xRPM'

# The name of the batch file to create.
output_filename = 'run_files.bat'
# The title for the batch file window.
batch_title = 'aspirated_stators_08xRPM_5mflow_1st_run'
 
# --- Script Logic ---

def create_batch_file():
    """
    Finds all .dat files in the specified directory and creates a batch script
    to run Multall simulations for each one.
    """
    # Find all files in the directory that end with the specified pattern
    try:
        # We now search in the well-defined 'target_directory'
        filenames = [f for f in os.listdir(target_directory) if f.endswith('hPa.dat')]
    except FileNotFoundError:
        print(f"Error: The directory '{target_directory}' was not found.")
        return

    if not filenames:
        print(f"No '.dat' files were found in '{target_directory}'. No batch file created.")
        return

    # Sort the filenames alphabetically to ensure a consistent order
    filenames.sort()

    # This list will hold all the lines of our final batch file
    batch_content = []

    # Add the initial header lines for the batch file
    batch_content.append('@echo off')
    batch_content.append(f'@title {batch_title}')
    batch_content.append('@rem Automatically generated batch script')
    batch_content.append('') # Add a blank line for readability

    # Loop through each .dat file found
    for filename in filenames:
        # Get the name of the file without the '.dat' extension
        base_name = os.path.splitext(filename)[0]

        # This is the template for the commands for each file.
        command_block = f"""
            multall.exe<        {filename}
            multall2py.exe<run2py.dat
            copy flow_out      flow_out-{base_name}.csv
            cd Output
            copy data_out.csv data_out-{base_name}.csv
            copy flow_avr.tec flow_avr-{base_name}.tec
            copy global.dat    global-{base_name}.csv
            cd ..
            """
        # Add the generated block of commands to our list
        batch_content.append(command_block)

    # --- Write the file ---
    # CORRECTED PART: Create the full, absolute path for the output file
    full_output_path = os.path.join(target_directory, output_filename)

    try:
        # Open the file using its full path
        with open(full_output_path, 'w') as f:
            # Join all the parts together with newlines in between
            f.write('\n'.join(batch_content))
        
        print(f"[OK] Successfully created file at: '{full_output_path}'")
        print(f"Found and processed {len(filenames)} files.")

    except IOError as e:
        print(f"Error: Could not write to the file '{full_output_path}'. Reason: {e}")


# --- Run the main function ---
if __name__ == "__main__":
    create_batch_file()