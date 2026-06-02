import os
import glob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    """
    Translates a MATLAB script to Python for reading and processing
    complex .dat/.csv files with multiple data blocks and headers.
    """

    # ## Step 0: Find files
    # Define the folder and search pattern to find the input files.
    folder_path = r'C:\Users\Jonas\sciebo\Geometriegenerator\Studenten\Scholz\Code\Multall\Ergebnisse\Kanalkontur_konst_TPR_mflow_n\Drehzahl_09\mean_psi08_09xRPM\Output'
    search_pattern = 'global-fixed_mean06_09xRPM_*hPa.csv'
    
    # Define the output filename
    output_filename = 'data_global.csv'

    # Create the full path for the output file to save it in the same folder
    # as the input files. 
    output_filepath = os.path.join(folder_path, output_filename)

    
    # Use glob to find all matching files
    full_search_path = os.path.join(folder_path, search_pattern)
    file_list = glob.glob(full_search_path)
    
    # Filter out files containing '_NaN.csv'
    filenames = [f for f in file_list if '_NaN.csv' not in os.path.basename(f)]
    
    # Initialize a list to store data for the final plot from the last file
    all_circ_data_final = np.array([])
    CP_final, KAPPA_final = 0, 0
    
    # ## Main Loop: Iterate through each file found
    for i, current_full_path in enumerate(filenames):
        try:
            # ## Step 1: Open the file for reading
            current_filename = os.path.basename(current_full_path)
            print(f"Opening file: {current_filename}")

            with open(current_full_path, 'r') as f:
                
                # ## Step 2: Read initial parameters
                # Read single-value parameters from the top of the file.
                NSTEP = int(f.readline().split(',')[0])
                CP = float(f.readline().split(',')[0])
                CP_final = CP # Store for final plot
                KAPPA = float(f.readline().split(',')[0])
                KAPPA_final = KAPPA # Store for final plot
                
                IM = int(f.readline().split(',')[0])
                JM = int(f.readline().split(',')[0])
                KM = int(f.readline().split(',')[0])
                NROW = int(f.readline().split(',')[0])
                
                print('\n--- Initial Parameters ---')
                print(f'NSTEP = {NSTEP}')
                print(f'CP = {CP:.4f}')
                print(f'KAPPA = {KAPPA:.4f}')
                print(f'IM = {IM}')
                print(f'JM = {JM}')
                print(f'KM = {KM}')
                print(f'NROW = {NROW}')
                
                # ## Step 3: Read 'NR, JS...' table
                f.readline()  # Skip header line
                blade_data_rows = [next(f) for _ in range(2)]
                blade_table = np.loadtxt(blade_data_rows, delimiter=',')
                
                print('\n--- Blade Table Data ---')
                print(blade_table)

                # Helper function to find and read data tables using pandas
                def find_and_read_table(file_handle, start_text, num_rows):
                    """Skips lines until start_text is found, then reads the table."""
                    for line in file_handle:
                        if start_text in line:
                            break
                    
                    file_handle.readline() # Skip blank line after header
                    header_line = file_handle.readline().strip()
                    headers = [h.strip() for h in header_line.split(',')]
                    
                    df = pd.read_csv(file_handle, header=None, names=headers, nrows=num_rows)
                    return df

                # ## Step 4: Read 'massflow averaged values' table
                massflow_df = find_and_read_table(f, 'massflow averaged values', 3)
                print('\n--- Massflow Averaged Data ---')
                print(massflow_df)

                # ## Step 5: Read 'area averaged values' table
                area_df = find_and_read_table(f, 'area averaged values', 3)
                print('\n--- Area Averaged Data ---')
                print(area_df)

                # ## Step 5.5: Write data to a single output file
                file_mode = 'w' if i == 0 else 'a'
                # MODIFIED: Use the full output filepath
                with open(output_filepath, file_mode, newline='') as f_out:
                    if i > 0:
                        f_out.write('\n\n========================================\n\n')
                    f_out.write(f'Data from: {current_filename}\n\n')
                    
                    # Write massflow data
                    f_out.write('massflow averaged values\n')
                    massflow_df.to_csv(f_out, index=False)
                    f_out.write('\n')
                    
                    # Write area data
                    f_out.write('area averaged values\n')
                    area_df.to_csv(f_out, index=False)

                # MODIFIED: Use the full output filepath in the confirmation message
                print(f'Data from {current_filename} successfully written to {output_filepath}.')
                
                # ## Step 6: Read 'circumferentially averaged values' tables
                all_circ_data_rows = []
                line = f.readline()
                
                # Loop through the rest of the file to find all relevant data blocks
                while line:
                    if 'circumferentially averaged values' in line:
                        # Found a block, now skip headers
                        next(f)  # Skip empty line
                        next(f)  # Skip 'ROW i inlet/outlet' line
                        next(f)  # Skip empty line
                        next(f)  # Skip the header line (e.g., 'K, ETA...')
                        
                        # Read data lines until an empty line is found
                        while True:
                            data_line = f.readline()
                            if not data_line or not data_line.strip():
                                break # End of table block
                            
                            # Sanitize line by splitting on any whitespace or comma
                            values_str = re.split(r'[\s,]+', data_line.strip())
                            
                            # Filter out empty strings that may result from splitting
                            values_str = [v for v in values_str if v]
                            
                            if len(values_str) == 14:
                                all_circ_data_rows.append([float(v) for v in values_str])
                    
                    if 'MASS FLOW ALONG THE FLOW PATH' in line:
                        break # Stop reading if we hit the next major section
                        
                    line = f.readline()

                all_circ_data = np.array(all_circ_data_rows)
                all_circ_data_final = all_circ_data # Save data from the last file for plotting
                
                if all_circ_data.size > 0:
                    print(f'\n--- Combined Circumferentially Averaged Data ({len(all_circ_data)} rows) ---')
                    print(all_circ_data)

        except FileNotFoundError:
            print(f"Error: Could not open file {current_full_path}. Please check the path.")
        except Exception as e:
            print(f"An error occurred while processing {current_filename}: {e}")

    # ## Step 7 is commented out in MATLAB, so it is skipped here.
'''  
    # ## Step 8: Create h-s-Diagram (from commented-out MATLAB code)
    # This section uses the data from the LAST processed file.
    if all_circ_data_final.size > 0:
        print("\n--- Generating h-s Diagram ---")
        
        T_ref = 293.15
        P_ref = 101325.0
        R = 287.0
        
        # --- Plot 1: Using specific points ---
        # Find indices where the 'ETA' value (column 2) is closest to 0.37
        # assuming 3 blocks of 36 rows each
        target_value = 0.37
        # Ensure we don't slice beyond the array's bounds
        block1_end = min(36, len(all_circ_data_final))
        block2_end = min(72, len(all_circ_data_final))
        block3_end = min(108, len(all_circ_data_final))

        list1 = all_circ_data_final[0:block1_end, 1]
        list2 = all_circ_data_final[block1_end:block2_end, 1]
        list3 = all_circ_data_final[block2_end:block3_end, 1]
        
        if list1.size > 0 and list2.size > 0 and list3.size > 0:
            index1 = np.abs(list1 - target_value).argmin()
            index2 = np.abs(list2 - target_value).argmin() + block1_end
            index3 = np.abs(list3 - target_value).argmin() + block2_end
            
            # Extract pressure (p) and temperature (t) at specific locations
            p1 = np.array([
                all_circ_data_final[block1_end - 1, 12], # Last row of block 1
                all_circ_data_final[block1_end, 12],     # First row of block 2
                all_circ_data_final[block2_end, 12]      # First row of block 3
            ])
            
            t1 = np.array([
                all_circ_data_final[index1, 13], # Column 14 at found index
                all_circ_data_final[index2, 13],
                all_circ_data_final[index3, 13]
            ])

            # Calculate specific enthalpy (h) and entropy (s)
            h = CP_final * t1
            # Added a small epsilon to prevent log(0) or negative values if pressure is non-positive
            s = CP_final * np.log(t1 / T_ref) - R * np.log(p1 / P_ref + 1e-9)

            plt.figure(figsize=(10, 7))
            plt.plot(s, h, 'b-o', label='Calculated Points', linewidth=1.5, markersize=5)
            
            plt.xlabel('Specific Entropy $s$ [J/(kg·K)]')
            plt.ylabel('Specific Enthalpy $h$ [J/kg]')
            plt.title('h-s Diagram')
            plt.grid(True)
            plt.legend()
            plt.show()

            print("h-s diagram has been generated and displayed. 📈")
        else:
            print("Not enough data in 'all_circ_data_final' to generate the plot.")
'''

print('\nAll files have been successfully processed.')

if __name__ == '__main__':
    main()