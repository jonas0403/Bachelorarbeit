# Author: Luca De Francesco
# Script for Bachelor thesis
    

import matplotlib.pyplot as plt
import numpy as np
import os
import stage_calculation as Stage
import json
import debug_log

#from old.stage_calculation import NROW

        

# Writes values in blocks of 8 per line to the file
def write_values_in_block(section, liste, file_handle, JM):
    if section >= len(liste):
        data = [0.0] * JM  # Initializes a list of zeros with length JM
    else:
        data = list(liste[section])
    
    for i in range(len(data)):
        if not np.isfinite(data[i]):
            error_msg = f"Invalid value at position {i} in sequence {section}: {data[i]}. Setting to 1e-6."
            print(error_msg)
            debug_log.debug(error_msg, context="write_values_in_block")
            data[i] = 1e-6
    
    if len(data) < JM:
        data += [0.0] * (JM - len(data))  # Pads the list with zeros if shorter than JM
    
    elif len(data) > JM:
        data = data[:JM]
    
    for k in range(0, JM, 8):
        chunk = data[k:k+8]  # Takes 8 elements at once
        line = " " +"".join(f"{element:12.6f}" for element in chunk) + "\n"
        file_handle.write(line)  # Writes the line to the file
      
def grid_adaption(grid_count, max=20, beta=2 ): # Generates grid spacings based on count
    x_norm = np.linspace(0.0, 1.0, grid_count) # Creates a list from 0 to 1 with grid_count points
    x_stretched = 0.5 * (1.0 + np.tanh(beta *(2.0 * x_norm - 1.0))) / np.tanh(beta) # Maximum grid spacing is 20
    #return x_stretched[::-1] * (grid_count-1) + 1.0 # Reverses the array and scales to grid_count
    
    spacings = np.diff(x_stretched) # Calculates the distances between points
    min_val = np.min(spacings)
    max_val = np.max(spacings)
    
    if (max_val - min_val) < 1e-9:
        return np.ones_like(spacings)  # If all spacings are equal, returns ones to avoid MULTALL errors
    
    scaled_spacings = 1 + (max - 1.0) * (spacings - min_val) / (max_val - min_val) # Scales spacings to range 1 to max
    scaled_spacings = np.nan_to_num(scaled_spacings, nan=0.0,posinf=0.0, neginf=0.0)
    
    return scaled_spacings

def create_bleed_air_card(file_path, patches_data, current_stage):
    
    stage_key = f"Stage {current_stage}"
    
    # Filter patches for this stage only
    stage_patches = [patches for patches in patches_data if patches[0] == stage_key]
    
    debug_log.debug(f"file_path={file_path}, stage_key={stage_key}, matches={len(stage_patches)}", context="create_bleed_air_card")
    with open(file_path, "a") as file:
        # One NBLEED per call (one blade row)
        file.write("NBLEED\n")
        file.write(f"{len(stage_patches)}\n")
        for patches in stage_patches:
            file.write('\t'.join(str(p) for p in patches[1:]) + '\n')
    
    '''
    # Filter patches for current stage 
    stage_key = f"Stage {current_stage}"
    
    # index 0 is stage string, rest are coords and mflow
    rotor_stage_patches = [patches for patches in rotor_data if patches[0] == stage_key]
    stator_stage_patches = [patches for patches in stator_data if patches[0] == stage_key]
    
    # Nbleed needs to be written for each row in each stage 
    print(f"file_path = {file_path}")
    with open(file_path, "a") as file:
        # Rotor NBLEED always written
        file.write("NBLEED\n")
        file.write(f"{len(rotor_stage_patches)}\n")
        for patches in rotor_stage_patches:
            file.write('\t'.join(str(p) for p in patches[1:])+ '\n')
            
        # Stator NBLEED needs to be writte if NROW != 1
        if NROW != 1:
            file.write("NBLEED\n")
            file.write(f"{len(stator_stage_patches)}\n")
            for patches in stator_stage_patches:
                file.write('\t'.join(str(p) for p in patches[1:])+ '\n')
    '''
    
    # Old bleed air card writing. Not usuable for multistage purposes
    '''
    print(f"file={file}")
    with open(file, "a") as file:
        if len(rotor_data) != 0 or len(stator_data) != 0:
            file.write("NBLEED\n")
            file.write(f"{len(rotor_data)}\n")
            for patches in rotor_data:
                file.write('\t'.join(patches)+ '\n')
            # Write Stator Bleedair Patches in NROW != 1
            if NROW != 1:
                file.write("NBLEED\n")
                file.write(f"{len(stator_data)}\n")
                for patches in stator_data:
                    file.write('\t'.join(patches)+ '\n')
    '''
## MULTALL .dat file writing
# Needs to be looped or called multiple times for each section IN EACH stage
def multall_grid_data_head_row(file_path, NSEC, row, JLE, JM, JTE, KM, tip_clearance, levels, CompressorGui, RPM, row_num, current_stage_num):
    section = 0
    
    current_stage = current_stage_num - 1
    debug_log.debug(f"current_stage (idx) = {current_stage}", context="multall_grid_data_head_row")
    debug_log.debug(f"current_stage_num = {current_stage_num}", context="multall_grid_data_head_row")
    
    global_row_num = row_num - 1
    debug_log.debug(f"global_row_num (idx) = {global_row_num}", context="multall_grid_data_head_row")
    debug_log.debug(f"global_row = {row_num}", context="multall_grid_data_head_row")
    
    
    ktipstart = 0
    ktipend = 0
    actual_tip_clearance = 0.0
    debug_log.debug(f"current_stage value = {current_stage}, type = {type(current_stage)}", context="multall_grid_data_head_row")
    if tip_clearance[current_stage] > 0:
        if row_num %2 != 0:
            ktipstart = KM - 4
            ktipend = KM
            actual_tip_clearance = tip_clearance[current_stage]
        else:
            ktipstart = 0
            ktipend = 0
    
    if tip_clearance[current_stage] == 0:
        ktipstart = 0
        ktipend = 0

    if section == 0:
        if row_num % 2 != 0:  # Odd rows = rotor
            x = round(Stage.p_1[current_stage], 1)
            y = round(Stage.p_2[current_stage], 1)
            z = RPM[0] #  rpm can stay 0 bceause rpm is const over stages
            blades = Stage.z_R[current_stage]
        else: # even rows = stator
            x = round(Stage.p_2[current_stage], 1)
            y = round(Stage.p_3[current_stage], 1)
            z = 0.0
            blades = Stage.z_S[current_stage]
    '''
    # section = 0 is hardcoded so this can be ignored
    # Dont delete incase of changing away from hardcoded section definition
    else:
        if row == 1:
            i = levels[section-1]
            for j in range(len(Stage.h_rel)):
                if round(Stage.h_rel[j],2) == i:
                    x = round(Stage.p_R_in[j], 1)
                    y = round(Stage.p_R_out[j], 1)

            z = Stage.RPM[0]
            blades = Stage.z_R[0]
        elif row == 2:
            i = levels[section-1]
            for j in range(len(Stage.h_rel)):
                if round(Stage.h_rel[j],2) == i:
                    x = round(Stage.p_S_in[j], 1)
                    y = round(Stage.p_S_out[j], 1)
            
            blades = Stage.z_S[0]
            z = 0.0
    '''
    with open(file_path, "a") as file:
        file.write(" ***************************************************************\n")
        file.write(" ************STARTING THE INPUT FOR EACH BLADE ROW**************\n")
        file.write(f"  BLADE ROW NUMBER =        {global_row_num + 1}                                           \n")
        file.write("    NUMBER OF BLADES IN ROW \n")
        file.write(f"        {blades}\n")                                       
        file.write("        JM        JLE       JTE \n")
        file.write(f"        {JM}        {JLE}        {JTE}\n")
        file.write("      KTIPSTART  KTIPEND \n")
        file.write(f"         {ktipstart}         {ktipend}\n")
        if ktipstart > 0:
            
            file.write("  FRACTIP1,     FRACTIP2 \n")
            file.write(f"  {actual_tip_clearance:.8f}       {actual_tip_clearance:.8f}\n")
        
            file.write("  FTHICK(K) \n")
            ftchick_values = [1.0] * KM
            if tip_clearance[current_stage] > 0:
                ftchick_values[ktipstart-2] = 0.9
                ftchick_values[ktipstart-1] = 0.5
            for k in range(ktipstart, KM):
                ftchick_values[k] = 0.0
            
        
            for i in range(0, KM, 8): # Counts in steps of 8
                line_number = ftchick_values[i:i+8] # Gets intermediate values from the grid distribution
                file.write(" ".join(f"{value:.6f}" for value in line_number) + "\n") # Writes the constructed line
        
        file.write("       BOUNDARY LAYER TRANSITION POINTS \n")
        file.write("         0         0         0         0\n")
        file.write("  SET NEWGRID= 1 TO GENERATE A NEW GRID WITH DIFFERENT \"J\" POINTS AND SPACINGS.\n")
        file.write("         0\n")
        file.write("   RPMROW,    RPMHUB \n")
        file.write(f"    {z}    {z}\n")
        file.write("       JROTHS    JROTHE    JROTTS    JROTTE \n")
        file.write("         1         1         1         1\n")
        file.write("   PUPROW    PLEROW   PTEROW    PDROW \n")
        file.write(f"   {x}   {x}   {y}  {y}\n")
        file.write("      NSECS_ROW   INSURF  \n")
        file.write(f"         {NSEC}         0\n")
        file.write("  IF_CUSP   IFANGLES \n")
        file.write("         0         0\n")
    
def write_head_file(KM_grid_density, IM_grid_density, file_path, section, NROW, NSEC, Q3D_value, enable_bleed_air, CompressorGui):
    if enable_bleed_air == True:
        bleed_air = 1
    else: 
        bleed_air = 0 
    with open(file_path, "w+") as file:
        file.write(" DATA SET FOR \"multall\" . GENERATED BY \"stagen\" .                       \n")
        file.write("    CP   and   GAMMA \n")
        file.write(f" {Stage.cp}    {Stage.kappa}\n")
        file.write("       ITIMST \n")
        file.write("         3\n")
        file.write("     CFL,    DAMP,    MACHLIM,    F_PDOWN \n")
        file.write("  0.320000 9.000000  2.000000  0.000000\n")
        file.write("  IF_RESTART \n")
        file.write("         0\n")
        file.write("  NSTEPS_MAX, CONLIM\n")
        if CompressorGui.stages_to_calc > 1:
            file.write("      120000  0.006000\n") # Documentation calls for more steps in multistage applications
        elif section == 0:
            file.write("      9000  0.006000\n")
        else: 
            file.write("      60000  0.005000\n")
        file.write("   SFX,      SFT,      FAC_4TH,     NCHANGE \n")
        file.write("  0.005000  0.005000  0.800000      1000\n")
        file.write("       NUMBER OF BLADE ROWS \n")# Number of blades in row?
        file.write(f"         {CompressorGui.stages_to_calc * NROW}\n")
        file.write("        IM        KM \n")
        
        if section == 0:
            file.write(f"        {IM_grid_density}        {KM_grid_density}\n")
        else:
            file.write(f"        {IM_grid_density}        2\n")
            
        value_IM = grid_adaption(IM_grid_density)
        file.write("  FP(I),I=1,IMM1 \n")
        for i in range(0, len(value_IM), 8): # Counts in steps of 8
            chunk = value_IM[i:i+8] # Gets intermediate values from the grid distribution
            line_value = " " # Inserts a leading space
            for value in chunk:
                line_value += f"{value:.6f} " # Adds 8 numbers with 6 decimal places
            line_value += "\n" # Adds a newline
            file.write(line_value) # Writes the constructed line
        
        if section == 0 and not Q3D_value:        
            value_KM = grid_adaption(KM_grid_density)
            file.write("  FR(K),K=1,KMM1 \n")
            for i in range(0, len(value_KM), 8): # Counts in steps of 8
                chunk = value_KM[i:i+8] # Gets intermediate values from the grid distribution
                line_value = " " # Inserts a leading space
                for value in chunk:
                    line_value += f"{value:.6f} " # Adds 8 numbers with 6 decimal places
                line_value += "\n" # Adds a newline
                file.write(line_value) # Writes the constructed line        
        else: # Sets FR to 1 when Q3D is active or only one row exists
             file.write("  FR(K),K=1,KMM1 \n")
             file.write("  1.000000\n")

        file.write("        IR        JR        KR        IRBB      JRBB      KRBB \n")
        file.write("         3         3         3         9         9         9\n")
        file.write("   FBLK1,     FBLK2,     FBLK3  \n")
        file.write("  0.400000  0.200000  0.100000\n")
        file.write("       IFMIX \n")
        file.write("         1\n")
        file.write("   RFMIX,    FEXTRAP,   FSMTHB,    FANGLE \n")
        file.write("  0.020000  0.800000  1.000000  0.800000\n")
        file.write("      IFCOOL    IFBLEED    IF_ROUGH \n")
        file.write(f"         0         {bleed_air}         0\n")
        file.write("       NSECS_IN \n")
        file.write(f"         {NSEC}\n")
        file.write("       IN_PRESS  IN_VTAN   IN_VR    IN_FLOW  IF_REPEAT  RFIN \n")
        file.write("         0         0         1         0         0   0.50000\n")
        file.write("  IPOUT  SFEXIT  NSFEXIT \n")
        file.write("    1  0.000000    0\n")
        file.write("  PLATE_LOSS  THROTTLE_EXIT \n")
        file.write("  0.000000  0.000000\n")
        file.write("        ILOS      NLOS      IBOUND \n")
        file.write("        10         5         0\n")
        file.write("   REYNO,     RF_VIS,   FTRANS, TURBVIS_LIM, PRANDTL, YPLUSWALL\n")
        if CompressorGui.stages_to_calc >1:
            file.write("  800000.0     0.500     0.000  3000.000       1.0     0.000\n") #  The doc explicitly states: "higher values, up to 3000, may be necessary in multistage machines." 
        else:
            file.write("  800000.0     0.500     0.000  1000.000       1.0     0.000\n")
        file.write("   YPLAM      YPTURB \n")
        file.write("  5.000000 25.000000\n")
        file.write("      ISHIFT    NEXTRAP_LE  NEXTRAP_TE \n")
        file.write("         2        10        10\n")
        file.write("  (NSTG(N),N=1,NROWS) \n")
        
        nstg_values = " ".join([str((i // NROW) + 1) for i in range(CompressorGui.stages_to_calc * NROW)])
        
        file.write(nstg_values + "\n")
        file.write("  5  TIME STEPS FOR PRINTOUT \n")
        file.write("      9000      9000      9000      9000      9000\n")
        file.write("  MARKER FOR VARIABLES TO BE SENT TO THE OUTPUT FILE.\n")
        file.write(" 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
        file.write("  STREAM SURFACES ON WHICH RESULTS ARE TO BE SENT TO   THE OUTPUT FILE \n")
        file.write(" ".join(f"0  " for _ in range(KM_grid_density)) + "\n")
        

# Writes the coordinates of all sections to a file for MULTALL
# MULTALL section geometry writer for a blade row.
# MULTALL format expects per section (confirmed by 10stg-compr-17.4.dat reference):
#   1. x-coordinates
#   2. FAC1=1.0 XSHIFT=0.0
#   3. Upper surface R*theta
#   4. FAC2=1.0 TSHIFT=0.0
#   5. Blade tangential thickness d (= upper - lower), ZERO upstream/downstream of blade
#   6. FAC3=1.0
#   7. r-coordinates
#   8. FAC4=1.0 RSHIFT=0.0
#
# NOTE: Card 63 must be BLADE TANGENTIAL THICKNESS d, NOT the lower surface R*theta.
# MULTALL computes lower_surface = upper_surface - d internally, then derives
# passage width = pitch - d. Writing the lower surface directly makes MULTALL
# interpret (rtheta - d) as a huge "thickness" exceeding pitch, causing NaN.
def write_coordinates(x, rtheta, d, r, file, row, a, b, JM, global_row_num, current_stage):
    with open(file, "a") as file:
        for i in range(a, b):       
            file.write(" ***************************************************************\n")
            file.write(f"  ROW NUMBER           {row}  SECTION NUMBER            {i+1}\n           0           0           0  IF_DESIGN etc \n   1.00000   0.00000    0\n")
            write_values_in_block(i, x, file, JM)
            file.write("  1.000000  0.000000\n")
            write_values_in_block(i, rtheta, file, JM)
            file.write("  1.000000\n")
            write_values_in_block(i, d, file, JM)
            file.write("  1.000000  0.000000\n")
            write_values_in_block(i, r, file, JM)
            
# writes information for Q3D calculation
def Q3D_information(file):
    with open(file, "a") as file:
        file.write("  DATA FOR STREAM SURFACE THICKNESS\n")
        file.write("   1.00000000      Q3DFORCE\n")
        file.write("           5  A UNIFORM  SS THICKNESS IS INITIALLY SET\n")
        file.write("   0.00000000      0.250000000      0.500000000      0.750000000      1.00000000\n")
        file.write("   1.00000000      1.00000000      1.00000000      1.00000000      1.00000000\n")     

"""
# writes end of the file 
def write_end_file(row, file, section, KM, levels, CompressorGui, radial_data_R, radial_data_S):
    # total_rows is NROW (e.g., 6 for 3 stages)
    # Get the last stage number
    last_stage = CompressorGui.stages_to_calc

    # Here needs to be new logic because row only works for one stage 
    # Some logic for the rows and NROW is missing
    if row == 1: # Maybe use modulus here to get if the row is odd (rotor) or even (stator)
        x = round(Stage.p_R_out[0], 1)
        y = round(Stage.p_R_out[len(Stage.h_rel)-1], 1)
        t = round(Stage.T_t1[0], 4)
        p = round(Stage.p_t1[0], 1)
        um = round(Stage.cm1[0], 4)
    
    elif row == 2:
        x = round(Stage.p_S_out[0], 1)
        y = round(Stage.p_R_out[len(Stage.h_rel)-1], 1)
        t = round(Stage.T_t1[0], 4)
        p = round(Stage.p_t1[0], 1)
        um = round(Stage.cm1[0], 4)
        
    with open(file, "a", encoding='ascii') as file:
        if section == 0:
            file.write("  STARTING INLET BOUNDARY CONDITION DATA .\n")
            file.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
            file.write(f"        {KM}\n") # Number of inlet points depends on grid density KM
            file.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
            
            value_KM = grid_adaption(KM)
            for i in range(0, len(value_KM), 8): # Counts in steps of 8
                file.write(" ".join(f"{v:.6f}" for v in value_KM[i:i+8]) + "\n") # Writes the constructed line
            
            # Dynamic adjustment of inlet boundary conditions by KM
            file.write("   INLET STAGNATION PRESSURES \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"{p:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   INLET STAGNATION TEMPERATURES \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"{t:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   INLET ABSOLUTE TANGENTIAL VELOCITY \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"0.000" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   INLET MERIDIONAL VELOCITY \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"{um:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   INLET MERIDIONAL YAW ANGLE \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"0.000" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   INLET PITCH ANGLE \n")
            for i in range(0, KM, 8):
                file.write(" ".join(f"0.000" for _ in range(KM)[i:i+8]) + "\n")
            file.write("   PDOWN_HUB   PDOWN_TIP \n")
            file.write(f"  {x}  {y}\n")
            file.write(" MIXING LENGTH LIMITS ON ALL BLADE ROWS\n")
            
            for _ in range(row * CompressorGui.stages_to_calc): # in here row needs to equal NROW (total number of blade rows), not just the current row number. 
                file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS \n")
            file.write("   2.00000 1000\n")
        else:         
            if row == 1:
                i = levels[section-1]
                for j in range(len(Stage.h_rel)):
                    if round(Stage.h_rel[j],2) == i:
                        x = round(Stage.p_S_out[j], 1)
                        y = round(Stage.p_R_out[j], 1)

            elif row == 2:
                i = levels[section-1]
                for j in range(len(Stage.h_rel)):
                    if round(Stage.h_rel[j],2) == i:
                        x = round(Stage.p_S_out[j], 1)
                        y = round(Stage.p_S_out[j], 1)

            file.write("STARTING INLET BOUNDARY CONDITION DATA .\n")
            file.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
            file.write("         2\n")
            file.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
            file.write("  1.000000\n")
            file.write("   INLET STAGNATION PRESSURES \n")
            file.write(f"  {p} {p}\n")
            file.write("   INLET STAGNATION TEMPERATURES \n")
            file.write(f"  {t} {t}\n")
            file.write("   INLET ABSOLUTE TANGENTIAL VELOCITY \n")
            file.write("    0.0000 0.0000\n")
            file.write("   INLET MERIDIONAL VELOCITY\n")
            file.write(f"  {um} {um}\n")
            file.write("   INLET MERIDIONAL YAW ANGLE\n")
            file.write("    0.0000 0.0000\n")
            file.write("   INLET PITCH ANGLE\n")
            file.write("    0.0000 0.0000\n")
            file.write("   PDOWN_HUB   PDOWN_TIP\n")
            file.write(f"  {x}  {y}\n")
            file.write(" MIXING LENGTH LIMITS ON ALL BLADE ROWS\n")
            '''
            ### Copied from docs ###
            For each of NROWS blade rows input
                XLLIM_IN The mixing length limit at the upstream boundary to the
                blade row. Typical value = 0.02 .
                XLLIM_LE The mixing length limit at the leading edge of the blade
                row. Typical value = 0.03 .
                XLLIM_TE The mixing length limit at the trailing edge of the blade
                row. Typical value = 0.04 .
                XLLIM_DN The mixing length limit at the exit boundary of the blade
                row. Typical value = 0.05 .
                FSTURB The free stream turbulent viscosity as a multiple of the
                laminar viscosity. Usually = 0.0 but increase in regions of
                high turbulence.
                TURBVIS_DAMP On passing through a mixing plane the turbulent
                viscosity downstream of the plane is this multiple of the
                pitchwise averaged turbulent viscosity upstream of the
                mixing plane. Typical value = 0.5, but this is very much a
                guess.
                There are NROWS lines of data needed here. Increase the mixing length limits and FSTURB
                if the flow is known to be highly turbulent or in regions where separations occur.
                The defaults are XLLIM_IN = 0.02, XLLIM_LE = 0.03, XLLIM_TE = 0.04, XLLIM_DN =
                0.05, FSTURB = 1.0, TURBVIS_DAMP = 0.5 
            '''
            for _ in range(row): # This needs to loop for every row so twice per stage
                file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS\n")
            file.write("   2.00000 1000\n")

    """        

def write_end_file(total_rows, file, section, KM, levels, CompressorGui, radial_data_R, radial_data_S):
    """
    Writes the inlet boundary conditions, exit pressure (PDOWN), and mixing length 
    limits for the MULTALL grid file. Refactored to pull from Stage module.
    """
    # Identify the last stage to set the exit backpressure (PDOWN)
    last_stg_idx = CompressorGui.stages_to_calc
    
    debug_log.debug(f"Starting write_end_file for {total_rows} rows. Last stage index: {last_stg_idx}", context="write_end_file")

    try:
        # 1. Get Inlet Boundary Conditions (from global Stage module)
        # These was causing the AttributeError when called on CompressorGui
        t_inlet = round(Stage.T_t1[0], 4)
        p_inlet = round(Stage.p_t1[0], 1)
        um_inlet = round(Stage.cm1[0], 4)
        
        debug_log.debug(f"Inlet data loaded -> P:{p_inlet}, T:{t_inlet}", context="write_end_file")

        # 2. Get Exit Boundary Conditions (PDOWN) from the last stage
        if last_stg_idx in radial_data_S:
            last_stg_data = radial_data_S[last_stg_idx]
            p_out_array = last_stg_data['p_S_out']
            debug_log.debug(f"Pulling PDOWN from Stator {last_stg_idx}", context="write_end_file")
        elif last_stg_idx in radial_data_R:
            last_stg_data = radial_data_R[last_stg_idx]
            p_out_array = last_stg_data['p_R_out']
            debug_log.debug(f"Pulling PDOWN from Rotor {last_stg_idx}", context="write_end_file")
        else:
            raise KeyError(f"Stage {last_stg_idx} not found in radial data")

        p_exit_hub = round(p_out_array[0], 1)
        p_exit_tip = round(p_out_array[-1], 1)

    except (KeyError, IndexError, AttributeError) as e:
        debug_log.debug(f"Error accessing stage data: {e}. Using safety fallbacks.", context="write_end_file")
        # Engineering fallbacks to prevent crash
        p_exit_hub, p_exit_tip = 101325.0, 101325.0
        t_inlet, p_inlet, um_inlet = 288.15, 101325.0, 150.0

    with open(file, "a", encoding='ascii') as f:
        if section == 0:
            f.write("  STARTING INLET BOUNDARY CONDITION DATA .\n")
            f.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
            f.write(f"        {KM}\n") 
            f.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
            
            value_KM = grid_adaption(KM)
            for i in range(0, len(value_KM), 8):
                f.write(" ".join(f"{v:.6f}" for v in value_KM[i:i+8]) + "\n")
            
            f.write("   INLET STAGNATION PRESSURES \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"{p_inlet:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   INLET STAGNATION TEMPERATURES \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"{t_inlet:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   INLET ABSOLUTE TANGENTIAL VELOCITY \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"0.000000" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   INLET MERIDIONAL VELOCITY \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"{um_inlet:.6f}" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   INLET MERIDIONAL YAW ANGLE \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"0.000000" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   INLET PITCH ANGLE \n")
            for i in range(0, KM, 8):
                f.write(" ".join(f"0.000000" for _ in range(KM)[i:i+8]) + "\n")
            
            f.write("   PDOWN_HUB   PDOWN_TIP \n")
            f.write(f"  {p_exit_hub}  {p_exit_tip}\n")
            
            f.write(" MIXING LENGTH LIMITS ON ALL BLADE ROWS\n")
            # Loop for NROW (total blade rows)
            for _ in range(total_rows):
                f.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            
            f.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS \n")
            f.write("   2.00000 1000\n")
            
        else:
            # Fallback for alternative grid sections
            f.write("STARTING INLET BOUNDARY CONDITION DATA .\n")
            f.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
            f.write("         2\n")
            f.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
            f.write("  1.000000\n")
            f.write("   INLET STAGNATION PRESSURES \n")
            f.write(f"  {p_inlet} {p_inlet}\n")
            f.write("   INLET STAGNATION TEMPERATURES \n")
            f.write(f"  {t_inlet} {t_inlet}\n")
            f.write("   INLET ABSOLUTE TANGENTIAL VELOCITY \n")
            f.write("    0.0000 0.0000\n")
            f.write("   INLET MERIDIONAL VELOCITY\n")
            f.write(f"  {um_inlet} {um_inlet}\n")
            f.write("   INLET MERIDIONAL YAW ANGLE\n")
            f.write("    0.0000 0.0000\n")
            f.write("   INLET PITCH ANGLE\n")
            f.write("    0.0000 0.0000\n")
            f.write("   PDOWN_HUB   PDOWN_TIP\n")
            f.write(f"  {p_exit_hub}  {p_exit_tip}\n")
            
            f.write(" MIXING LENGTH LIMITS ON ALL BLADE ROWS\n")
            for _ in range(total_rows):
                f.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            
            f.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS\n")
            f.write("   2.00000 1000\n")

# Plotting:

def plot_all(grid_data_list, grid_density):
    plt.figure(figsize=(15, 10))
    colors = ['blue', 'red']
    row_labels = ['Rotor', 'Stator']

    for i, data in enumerate(grid_data_list):
        row_num = data['row_num']
        x_coords = data['x_new'][0] 
        d_coords = data['d_new'][0]
        rtheta_coords = data['Rtheta_new'][0]
        
        rtheta_upper = rtheta_coords
        rtheta_lower = [upper - d for upper, d in zip(rtheta_upper, d_coords)]
        
        color = colors[i % len(colors)]
        label = f"{row_labels[i % len(row_labels)]} (Row {row_num})"
        
        plt.plot(x_coords, rtheta_upper, color=color, marker='.', markersize=3, label=label)
        plt.plot(x_coords, rtheta_lower, color=color, marker='.', markersize=3)
    
    plt.xlabel("x-coordinate [mm]")
    plt.ylabel("R-theta coordinate [mm]")
    plt.title(f"Dynamic grid (Density: {grid_density})")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    plt.show()

def generate_var_grid_data(nrow, IM_grid_density, KM_grid_density, JM_grid_density, inlet_percentage, outlet_percentage, reference_chord_length, levels, CompressorGui):
    
    # List to store results for each blade row
    all_rows_grid_data = []
    all_rows_data_plot = []

    # Variable to calc which rows will be calculated
    nrow_wert = nrow * CompressorGui.stages_to_calc
    
    for row_num in range(1, nrow_wert + 1):
        status_msg = f"Processing blade row {row_num} (Density: {JM_grid_density})"
        print(f"\n{status_msg}")
        debug_log.debug(status_msg, context="generate_var_grid_data")

        # Checks blade size at 50% span and compares with reference value
        actual_chord, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = Stage.calculation_of_section(0.5, row_num)
        
        chord_msg = f"Chord length for row {row_num}: {actual_chord:.2f} mm"
        print(chord_msg)
        debug_log.debug(chord_msg, context="generate_var_grid_data")

        JM_dynamic = int(round((actual_chord / reference_chord_length) * JM_grid_density))
        
        # Dynamic calculation of grid points at inlet and outlet
        n_max_in = int(round(JM_dynamic * inlet_percentage))
        j_prime_max = JM_dynamic
        n_max_out = int(round(JM_dynamic * outlet_percentage))
        
        JLE = n_max_in
        JTE = n_max_in + j_prime_max - 1
        JM = n_max_in + n_max_out + j_prime_max - 2
        
        if row_num % 2 != 0:
            JM_dynamic_rotor = JM_dynamic
        else:
            JM_dynamic_stator = JM_dynamic
        dynamic_msg = f"Dynamic grid points (blade only): {JM_dynamic}"
        print(dynamic_msg)
        debug_log.debug(dynamic_msg, context="generate_var_grid_data")
        points_msg = f"Total points (JM): {JM}, Inlet index (JLE): {JLE}, Outlet index (JTE): {JTE}"
        print(points_msg)
        debug_log.debug(points_msg, context="generate_var_grid_data")
        i_o_msg = f"Inlet points: {n_max_in}, Outlet points: {n_max_out}"
        print(i_o_msg)
        debug_log.debug(i_o_msg, context="generate_var_grid_data")
        
        x_new, d_new, R_new, Rtheta_new = Stage.calc_blade_row_coordinates(
            row=row_num, 
            j_prime_max=JM_dynamic, 
            num_planes=5, 
            n_max_in=n_max_in, 
            l_inlet=1, 
            n_max_out=n_max_out, 
            l_outlet=1, 
            Z_H=0.05, 
            Z_S=0.95, 
            levels=levels)
        
        
        debug_log.debug(f"row_num={row_num}: x_new[0][0]={x_new[0][0]:.4f}, x_new[0][-1]={x_new[0][-1]:.4f}, R_new[0][0]={R_new[0][0]:.6f}", context="generate_var_grid_data")
        # x_new_plot, d_new_plot, R_new_plot, Rtheta_new_plot = Stage.calc_blade_row_coordinates(
        #     row=row_num, 
        #     j_prime_max=j_prime_max_plot, 
        #     num_planes=5, 
        #     n_max_in=n_max_in, 
        #     l_inlet=1, 
        #     n_max_out=n_max_out, 
        #     l_outlet=1, 
        #     Z_H=0.05, 
        #     Z_S=0.95, 
        #     levels=[h_H_plot]
        # )
        
        # Store the calculated data for this row
        all_rows_grid_data.append({
            'row_num': row_num,
            'x_new': x_new,
            'd_new': d_new,
            'R_new': R_new,
            'Rtheta_new': Rtheta_new,
            'JM': JM,
            'JLE': JLE,
            'JTE': JTE,
            'IM': IM_grid_density,
            'KM': KM_grid_density,
            'JM_dynamic': JM_dynamic
        })
        
        # all_rows_data_plot.append({
        #     'row_num': row_num,
        #     'x_new': x_new_plot,
        #     'd_new': d_new_plot,
        #     'R_new': R_new_plot,
        #     'Rtheta_new': Rtheta_new_plot
        # })
    
    return all_rows_grid_data


def process_grid_data(json_path, CompressorGui):
    '''
    Multistage LOGIC :
    # 1. Write once
        write_head_file(...)

    # 2. Loop over rows
        for row in all_rows_grid_data:
            multall_grid_data_head_row(...)   # row header
            write_coordinates(...)             # geometry sections
            if enable_bleed_air:
                create_bleed_air_card(...)     # bleed cards per row # Here will be issues at the moment bleed is only working for first stage

    # 3. Write once at the end
        if Q3D_value:
            Q3D_information(...)

        write_end_file(NROW, ...)   # inlet BCs + mixing length limits
    '''
    
    
    
    """
    Receives data from the main GUI, unpacks it and
    starts the grid generation (MULTALL .dat creation).
    """
    unpack_msg = "\n--- Starting to unpack GUI data in grid_generator ---"
    print(unpack_msg)
    debug_log.debug(unpack_msg, context="process_grid_data")
    
    try:
        all_json_data = {}
        
        try:
            with open(json_path, 'r') as file:
                all_json_data = json.load(file)
        
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        grid_data_gui = all_json_data['Grid_data'] 
        meanline_data_gui = all_json_data['Meanline_input_data']
        #thermo_data_gui = all_json_data['Thermo_data']
        Metadata = all_json_data['Metadata']
        bleed_air_data = all_json_data['Bleed_air_data']


        
                   
    except ValueError:
        error_msg = "Please enter valid numbers for all conditions."
        print(error_msg)
        debug_log.debug(error_msg, context="process_grid_data")
        
        '''
        Unpacking Grid Data
        '''

    IM_grid_density = int(grid_data_gui['im_selection'])
    KM_grid_density = int(grid_data_gui['km_selection'])
    JM_grid_density = int(grid_data_gui['JM_grid_density'])
    nrow_wert = int(grid_data_gui['nrow'])
    tip_clearance_mm_rotor = float(grid_data_gui['tip_clearance_rotor'])
    Q3D_value = grid_data_gui['Q3D_mode']
    ref_chord_length = float(grid_data_gui['ref_chord_length'])
    inlet_percentage = float(grid_data_gui['inlet_percentage'])
    outlet_percentage = float(grid_data_gui['outlet_percentage'])
    SA_Mode = grid_data_gui['SA_mode']

    RPM = meanline_data_gui['n']
    
    output_path = Metadata['output_folder']
    levels = Metadata['levels']

    # NOTE: debug_log.open_file() is called ONCE in GUI.py:2845 before process_grid_data,
    # so channel init messages from run_main_logic() are preserved in the log.
    debug_log.debug(f"tip_clearance_mm_rotor = {tip_clearance_mm_rotor}, b2 = {CompressorGui.meanline_data['b2']}", context="process_grid_data")
    tip_clearance_multall = [tip_clearance_mm_rotor / x for x in CompressorGui.meanline_data['b2']]


    

    enable_bleed_air = bleed_air_data['enable_bleed_air']
    
    all_rows_grid_data = generate_var_grid_data(nrow_wert, IM_grid_density, KM_grid_density, JM_grid_density, inlet_percentage, outlet_percentage, ref_chord_length, levels, CompressorGui)    
    
    # --- X-RANGE MONOTONICITY CHECK ---
    debug_log.section("X-Range Monotonicity Check")
    prev_max_x = -float('inf')
    all_ok = True
    for data in all_rows_grid_data:
        min_x = min(data['x_new'][0])
        max_x = max(data['x_new'][0])
        status = "OK" if min_x >= prev_max_x - 1e-10 else "*** OVERLAP ***"
        debug_log.debug(f"Row {data['row_num']}: x=[{min_x:.4f}, {max_x:.4f}]  {status}", context="monotonicity")
        if status != "OK":
            all_ok = False
        prev_max_x = max_x
    debug_log.debug(f"Result: {'PASSED' if all_ok else 'FAILED'}", context="monotonicity")
    
    # Old hardcoded first value
    #JM_dynamic_rotor = all_rows_grid_data[0]['JM_dynamic']
    JM_dynamic_rotor = [row['JM_dynamic'] for row in all_rows_grid_data[::2]]
    
    if nrow_wert > 1:
        JM_dynamic_stator = [row['JM_dynamic'] for row in all_rows_grid_data[1::2]]
    else:
        JM_dynamic_stator = 0

    if Q3D_value:
        output_name = f"multall_grid_Q3D_IM_{IM_grid_density}__R_{JM_dynamic_rotor}_S_{JM_dynamic_stator}_rows_{nrow_wert}.dat"
    else:
        output_name = f"multall_grid_IM_{IM_grid_density}_KM_{KM_grid_density}_R_{JM_dynamic_rotor}_S_{JM_dynamic_stator}_rows_{nrow_wert}.dat"
        
    full_output_path = os.path.join(output_path, output_name)
    
    NSEC = len(levels)

    head_msg = "Writing MULTALL grid data head row..."
    print(head_msg)
    debug_log.debug(head_msg, context="process_grid_data")
    write_head_file(KM_grid_density, IM_grid_density, full_output_path, 0, nrow_wert, NSEC, Q3D_value, enable_bleed_air, CompressorGui)

    
    # Calls grid/row data writing for each blade row across all stages
    for i, data in enumerate(all_rows_grid_data):
        row_num = data['row_num']
        x_coords = data['x_new'] 
        d_coords = data['d_new']
        r_coords = data['R_new']
        rtheta_coords = data['Rtheta_new']
        
        # SAFETY: If r_coords somehow arrive in mm instead of meters (max_r < 0.05),
        # convert to meters. The root cause (channel.py returning r in meters
        # while x in mm) was fixed, so this should not trigger.
        max_r = max(max(sec) for sec in r_coords)
        if max_r < 0.05:
            r_coords = [[val * 1000.0 for val in sec] for sec in r_coords]
        
        JLE = data['JLE']
        JTE = data['JTE']
        JM_row = data['JM']
        NSEC_new = len(data['x_new'])

        # Global row number (1-based across all stages)
        global_row_num = i + 1
        
        # Stage number derived from row index
        current_stage = (i // 2) + 1
        
        debug_log.debug(f"i={i}, row_num={row_num}, current_stage={current_stage}", context="process_grid_data")
        debug_log.debug(f"Row {global_row_num} (stage {current_stage}):", context="process_grid_data")
        debug_log.debug(f"  x_coords first section first point: {x_coords[0][0]:.4f}", context="process_grid_data")
        debug_log.debug(f"  x_coords first section last point:  {x_coords[0][-1]:.4f}", context="process_grid_data")
        debug_log.debug(f"  r_coords first section first point: {r_coords[0][0]:.4f}", context="process_grid_data")
        debug_log.debug(f"  r_coords first section last point:  {r_coords[0][-1]:.4f}", context="process_grid_data")
        debug_log.debug(f"  r_coords LAST section first point: {r_coords[-1][0]:.4f}", context="process_grid_data")
        debug_log.debug(f"  r_coords LAST section last point:  {r_coords[-1][-1]:.4f}", context="process_grid_data")
        debug_log.debug(f"  rtheta_coords first section first point: {rtheta_coords[0][0]:.6f}", context="process_grid_data")
        debug_log.debug(f"  rtheta_coords first section last point:  {rtheta_coords[0][-1]:.6f}", context="process_grid_data")
        debug_log.debug(f"  d_coords first section first point: {d_coords[0][0]:.6f}", context="process_grid_data")
        debug_log.debug(f"  d_coords first section last point:  {d_coords[0][-1]:.6f}", context="process_grid_data")
        
        # BUGFIX VERIFICATION: log passage width before (wrong) and after (correct)
        sec0_rtheta = rtheta_coords[0]
        sec0_d = d_coords[0]
        sec0_r = r_coords[0]
        # Number of blades for this row from meanline data
        if row_num % 2 != 0:
            z_blades = CompressorGui.meanline_data['z_R'][current_stage - 1]
        else:
            z_blades = CompressorGui.meanline_data['z_S'][current_stage - 1]
        # Blade mid index (JM/2) as representative sample
        mid_k = JM_row // 2
        r_mid = sec0_r[mid_k]
        pitch = 2 * 3.14159265 * r_mid / z_blades if z_blades > 0 else 0
        thick = sec0_d[mid_k]
        old_passage = abs(sec0_d[mid_k] - sec0_rtheta[mid_k])  # what MULTALL previously saw
        new_passage = abs((sec0_rtheta[mid_k] - sec0_d[mid_k]) - sec0_rtheta[mid_k])  # what MULTALL now sees = thick
        debug_log.debug(f"  BUGFIX: row {row_num} first section mid: r={r_mid:.4f}, z={z_blades}, pitch={pitch:.6f}, thick={thick:.6f}", context="passage_width")
        debug_log.debug(f"  BUGFIX: OLD block3=d -> MULTALL saw passage width = {old_passage:.6f} (WRONG, should be ~pitch)", context="passage_width")
        debug_log.debug(f"  BUGFIX: NEW block3=rtheta-d -> MULTALL sees thickness = {new_passage:.6f}, pitch-thickness = {pitch - thick:.6f}", context="passage_width")
        
        multall_grid_data_head_row(full_output_path, NSEC_new, row_num, JLE, JM_row, JTE, KM_grid_density, tip_clearance_multall, levels, CompressorGui, RPM, global_row_num, current_stage)
        write_coordinates(x_coords, rtheta_coords, d_coords, r_coords, full_output_path, row_num, 0, NSEC_new, JM_row, global_row_num, current_stage)
        '''
        # possible worng location of bleed air 
        if enable_bleed_air:
            rotor_data = [
                bleed_air_data[f"rotor_patch_{j+1}"] 
                for j in range(bleed_air_data.get('rotor_patches', 0))
                if f"rotor_patch_{j+1}" in bleed_air_data
            ]
            stator_data = [
                bleed_air_data[f"stator_patch_{j+1}"] 
                for j in range(bleed_air_data.get('stator_patches', 0))
                if f"stator_patch_{j+1}" in bleed_air_data
            ]
            
            # call once per row, passing rotor or stator data depending on row type
            if row_num == 1:  # rotor row
                create_bleed_air_card(full_output_path, rotor_data, current_stage)
            else:  # stator row
                create_bleed_air_card(full_output_path, stator_data, current_stage)
        '''
        row_done_msg = f"Grid data for row {row_num} written successfully."
        print(row_done_msg)
        debug_log.debug(row_done_msg, context="process_grid_data")
    '''
    # Maybe placement of bleedair was wrong 
    if enable_bleed_air:
        rotor_data = [
            bleed_air_data[f"rotor_patch_{j+1}"] 
            for j in range(bleed_air_data.get('rotor_patches', 0))
            if f"rotor_patch_{j+1}" in bleed_air_data
        ]
        stator_data = [
            bleed_air_data[f"stator_patch_{j+1}"] 
            for j in range(bleed_air_data.get('stator_patches', 0))
            if f"stator_patch_{j+1}" in bleed_air_data
        ]
        
        # CHANGE: one NBLEED card per blade row, in order rotor then stator per stage
        for i, data in enumerate(all_rows_grid_data):
            row_num = data['row_num']
            current_stage = (i // 2) + 1
            
            if i % 2 == 0:  # rotor
                create_bleed_air_card(full_output_path, rotor_data, current_stage)
            else:  # stator
                create_bleed_air_card(full_output_path, stator_data, current_stage)

    
    # --- INTER-ROW CONTINUITY CHECK ---
    debug_log.section("Inter-Row Continuity Check (matching planes)")
    for j in range(len(all_rows_grid_data) - 1):
        row_a = all_rows_grid_data[j]
        row_b = all_rows_grid_data[j + 1]
        x_prev_max = max(row_a['x_new'][0])
        x_next_min = min(row_b['x_new'][0])
        R_prev_last = row_a['R_new'][0][-1] if row_a['R_new'][0] else -1
        R_next_first = row_b['R_new'][0][0] if row_b['R_new'][0] else -1
        gap = x_next_min - x_prev_max
        R_jump = R_next_first - R_prev_last
        debug_log.debug(f"Row {row_a['row_num']}→{row_b['row_num']}: x_gap={gap:.4f}m  R_jump={R_jump:.4f}m", context="continuity")
        if abs(R_jump) > 0.001:
            debug_log.debug(f"  *** R discontinuity at matching plane: {R_prev_last:.4f} → {R_next_first:.4f} (jump={R_jump:.4f}m)", context="continuity")
    
    '''
    
    if Q3D_value:
        Q3D_information(full_output_path)
        q3d_msg = "Q3D information written successfully."
        print(q3d_msg)
        debug_log.debug(q3d_msg, context="process_grid_data")
    
    endfile_msg = "Starting writing end of file..."
    print(endfile_msg)
    debug_log.debug(endfile_msg, context="process_grid_data")
    
    total_blade_rows = nrow_wert * CompressorGui.stages_to_calc
    
    write_end_file(total_blade_rows, full_output_path, 0, KM_grid_density, levels, CompressorGui, Stage.radial_data_R, Stage.radial_data_S)
    
    done_msg = f"Grid data for all rows written to {full_output_path} successfully."
    print(done_msg)
    debug_log.debug(done_msg, context="process_grid_data")
    all_done_msg = "All tasks completed successfully."
    print(all_done_msg)
    debug_log.debug(all_done_msg, context="process_grid_data")

    
    if enable_bleed_air:
        rotor_data = [
            bleed_air_data[f"rotor_patch_{j+1}"] 
            for j in range(bleed_air_data.get('rotor_patches', 0))
            if f"rotor_patch_{j+1}" in bleed_air_data
        ]
        stator_data = [
            bleed_air_data[f"stator_patch_{j+1}"] 
            for j in range(bleed_air_data.get('stator_patches', 0))
            if f"stator_patch_{j+1}" in bleed_air_data
        ]
        
        # one NBLEED card per blade row, in order rotor then stator per stage
        for i, data in enumerate(all_rows_grid_data):
            row_num = data['row_num']
            current_stage = (i // 2) + 1
            
            if i % 2 == 0:  # rotor
                create_bleed_air_card(full_output_path, rotor_data, current_stage)
            else:  # stator
                create_bleed_air_card(full_output_path, stator_data, current_stage)

    