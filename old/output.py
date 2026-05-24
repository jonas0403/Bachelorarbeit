import numpy as np

def write_all_settings(data):
    
    '''
    Getting all necessary data from the data dictionary to write the .dat file for Multall and the bleed air card. 
    The data is organized in different sections for better readability and maintenance. 
    '''
    
    # Grid Data 
    KM_grid_density = data['KM_grid_density']
    IM_grid_density = data['IM_grid_density']
    grid_data_list = data['grid_data_list']
    Q3D_value = data['Q3D_value']
    
    # General data for the file
    nrow_wert = data['nrow_wert']
    full_output_path = data['full_output_path']
    NSEC = data['NSEC']
    section = data['section']
    stage_levels = data['stage_levels']

    # Compressor specific data
    kappa = data['kappa']
    cp = data['cp']
    tip_clearance_multall = data['tip_clearance_multall']
    RPM = data['RPM']
    z_R = data['z_R']
    z_S = data['z_S']
    p_1 = data['p_1']
    p_2 = data['p_2']
    p_3 = data['p_3']
    h_rel = data['h_rel']
    p_R_in = data['p_R_in']
    p_R_out = data['p_R_out']
    p_S_in = data['p_S_in']
    p_S_out = data['p_S_out']
    T_t1 = data['T_t1']
    p_t1 = data['p_t1']
    cm1 = data['cm1']
    
    
    # Data for the head of the file

    
    # Data for the bleed air card
    rotor_data = data['rotor_data']
    stator_data = data['stator_data']


    print("Starting to write head of the file...")    
    write_head_file(KM_grid_density, IM_grid_density, full_output_path, section, nrow_wert, NSEC, Q3D_value, cp, kappa)
    
    for i, data in enumerate(grid_data_list):
            row_num = data['row_num']
            x_coords = data['x_new'] 
            d_coords = data['d_new']
            r_coords = data['R_new']
            rtheta_coords = data['Rtheta_new']
            JLE = data['JLE']
            JTE = data['JTE']
            JM = data['JM']
            NSEC_new = len(data['x_new'])
        
            print("Writing Multall grid data head row...")
            multall_grid_data_head_row(full_output_path, NSEC, nrow_wert, JLE, JM, JTE, KM_grid_density, tip_clearance_multall, stage_levels, RPM, z_R, z_S, p_1, p_2, p_3, h_rel, p_R_in, p_R_out, p_S_in, p_S_out)
            print("Multall grid data head row written successfully.")

            print(f"Writing coordinates for row {row_num}...")
            write_coordinates(x_coords, rtheta_coords, d_coords, r_coords, full_output_path, row_num, 0, NSEC_new, JM)
            print(f"Grid data for row {row_num} written successfully.")
        
    if Q3D_value:
        Q3D_information(full_output_path)
        print("Q3D information written successfully.")
    
    print("Starting writing end of file...")
    write_end_file(nrow_wert, full_output_path, section, KM_grid_density, stage_levels, p_R_out, p_S_out, T_t1, p_t1, cm1, h_rel)
    print(f"Grid data for all rows written to {full_output_path} successfully.")
    
    print("Starting to create bleed air card...")
    create_bleed_air_card(nrow_wert, full_output_path, rotor_data, stator_data)
    print("All tasks completed successfully.")
    
    def create_bleed_air_card(NROW, file, rotor_data, stator_data):
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
        

    def write_values_in_block(section, liste, file_handle, JM):
        
        
        
        if section >= len(liste):
            data = [0.0] * JM  # Initialisiert eine Liste mit Nullen der Länge JM
        else:
            data = list(liste[section])
        
        for i in range(len(data)):
            if not np.isfinite(data[i]):
                print(f"Ungültiger Wert an der Stelle {i} in der Reihenfolge {section}: {data[i]}. Dieser Wert wird auf 0.0 gesetzt.")
                data[i] = 1e-6
        
        if len(data) < JM:
            data += [0.0] * (JM - len(data))  # Füllt die Liste auf, falls sie kürzer ist als JM
        
        elif len(data) > JM:
            data = data[:JM]
        
        for k in range(0, JM, 8):
            abschnitt = data[k:k+8]  
            line = " " +"".join(f"{element:12.6f}" for element in abschnitt) + "\n"
            file_handle.write(line)  
        
    def grid_adaption(grid_count, max=20, beta=2 ): 
        x_norm = np.linspace(0.0, 1.0, grid_count) 
        x_stretched = 0.5 * (1.0 + np.tanh(beta *(2.0 * x_norm - 1.0))) / np.tanh(beta) 
        #return x_stretched[::-1] * (grid_count-1) + 1.0
        
        spacings = np.diff(x_stretched) 
        min_val = np.min(spacings)
        max_val = np.max(spacings)
        
        if (max_val - min_val) < 1e-9:
            return np.ones_like(spacings) 
        
        scaled_spacings = 1 + (max - 1.0) * (spacings - min_val) / (max_val - min_val) 
        scaled_spacings = np.nan_to_num(scaled_spacings, nan=0.0,posinf=0.0, neginf=0.0)
        
        return scaled_spacings

    ## Multall .dat File writer for the head of the file with all necessary information for the grid and the blade row
    def multall_grid_data_head_row(file_path, NSEC, row, JLE, JM, JTE, KM, tip_clearance, levels, RPM, z_R, z_S, p_1, p_2, p_3, h_rel, p_R_in, p_R_out, p_S_in, p_S_out, T_t1, p_t1, cm1):
        section = 0
        NSEC
        
        ktipstart = 0
        ktipend = 0
        actual_tip_clearance = 0
        
        if tip_clearance > 0:
            if row == 1:
                ktipstart = KM - 2
                ktipend = KM
                actual_tip_clearance = tip_clearance
            else:
                ktipstart = 0
                ktipend = 0
                actual_tip_clearance = 0.0
        
        if tip_clearance == 0:
            actual_tip_clearance = 0
            ktipstart = 0
            ktipend = 0

        if section == 0:
            if row == 1:
                x = round(p_1[0], 1)
                y = round(p_2[0], 1)
                z = RPM[0]
                blades = z_R[0]
            elif row == 2:
                x = round(p_2[0], 1)
                y = round(p_3[0], 1)
                z = 0.0
                blades = z_S[0]
        else:
            if row == 1:
                i = levels[section-1]
                for j in range(len(h_rel)):
                    if round(h_rel[j],2) == i:
                        x = round(p_R_in[j], 1)
                        y = round(p_R_out[j], 1)

                z = RPM[0]
                blades = z_R[0]
            elif row == 2:
                i = levels[section-1]
                for j in range(len(h_rel)):
                    if round(h_rel[j],2) == i:
                        x = round(p_S_in[j], 1)
                        y = round(p_S_out[j], 1)
                
                blades = z_S[0]
                z = 0.0

        with open(file_path, "a") as file:
            file.write(" ***************************************************************\n")
            file.write(" ************STARTING THE INPUT FOR EACH BLADE ROW**************\n")
            file.write(f"  BLADE ROW NUMBER =        {row}                                           \n")
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
                if tip_clearance > 0:
                    ftchick_values[ktipstart-2] = 0.9
                    ftchick_values[ktipstart-1] = 0.5
                for k in range(ktipstart, KM):
                    ftchick_values[k] = 0.0
                
            
                for i in range(0, KM, 8): # Zählweise in 8ter Schritten
                    line_number = ftchick_values[i:i+8] # Holt die Zwischenschritte aus der Gridverteilung
                    file.write(" ".join(f"{value:.6f}" for value in line_number) + "\n") # Schreibt die gebaute Zeile
            
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
        
    def write_head_file(KM_grid_density, IM_grid_density, file_path, section, NROW, NSEC, Q3D_value, cp, kappa):
            
        with open(file_path, "w+") as file:
            file.write(" DATA SET FOR \"multall\" . GENERATED BY \"stagen\" .                       \n")
            file.write("    CP   and   GAMMA \n")
            file.write(f" {cp}    {kappa}\n")
            file.write("       ITIMST \n")
            file.write("         3\n")
            file.write("     CFL,    DAMP,    MACHLIM,    F_PDOWN \n")
            file.write("  0.300000 10.000000  2.000000  0.000000\n")
            file.write("  IF_RESTART \n")
            file.write("         0\n")
            file.write("  NSTEPS_MAX, CONLIM\n")
            if section == 0:
                file.write("      9000  0.006000\n")
            else: 
                file.write("      60000  0.005000\n")
            file.write("   SFX,      SFT,      FAC_4TH,     NCHANGE \n")
            file.write("  0.005000  0.005000  0.800000      1000\n")
            file.write("       NUMBER OF BLADE ROWS \n")
            file.write(f"         {NROW}\n")
            file.write("        IM        KM \n")
            
            if section == 0:
                file.write(f"        {IM_grid_density}        {KM_grid_density}\n")
            else:
                file.write(f"        {IM_grid_density}        2\n")
            
            value_IM = grid_adaption(IM_grid_density)
            file.write("  FP(I),I=1,IMM1 \n")
            for i in range (0,len(value_IM), 8): # Zählweise in 8ter Schritten
                line_number = value_IM[i:i+8] # Holt die Zwischenschritte aus der Gridverteilung
                line_value = " " # fügt eine Leerzeile ein
                for value in line_number:
                    line_value += f"{value:.6f} " # Fügt 8 Zahlen mit 6 Nachkommastellen ein
                line_value += "\n" # Fügt einen Zeilenumbruch ein
                file.write(line_value) # Schreibt die gebaute Zeile
            
            if section == 0 and not Q3D_value:        
                value_KM = grid_adaption(KM_grid_density)
                file.write("  FR(K),K=1,KMM1 \n")
                for i in range (0,len(value_KM), 8): # Zählweise in 8ter Schritten
                    line_number = value_KM[i:i+8] # Holt die Zwischenschritte aus der Gridverteilung
                    line_value = " " # fügt eine Leerzeile ein
                    for value in line_number:
                        line_value += f"{value:.6f} " # Fügt 8 Zahlen mit 6 Nachkommastellen ein
                    line_value += "\n" # Fügt einen Zeilenumbruch ein
                    file.write(line_value) # Schreibt die gebaute Zeile        
            else: # Setzt FR auf 1 wenn Q3D aktiv ist oder es nur eine Reihe gibt
                file.write("  FR(K),K=1,KMM1 \n")
                file.write("  1.000000\n")

            file.write("        IR        JR        KR        IRBB      JRBB      KRBB \n")
            file.write("         3         3         3         9         9         9\n")
            file.write("   FBLK1,     FBLK2,     FBLK3  \n")
            file.write("  0.400000  0.200000  0.100000\n")
            file.write("       IFMIX \n")
            file.write("         1\n")
            file.write("   RFMIX,    FEXTRAP,   FSMTHB,    FANGLE \n")
            file.write("  0.025000  0.800000  1.000000  0.800000\n")
            file.write("      IFCOOL    IFBLEED    IF_ROUGH \n")
            file.write("         0         0         0\n")
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
            file.write("  800000.0     0.500     0.000  1000.000       1.0     0.000\n")
            file.write("   YPLAM      YPTURB \n")
            file.write("  5.000000 25.000000\n")
            file.write("      ISHIFT    NEXTRAP_LE  NEXTRAP_TE \n")
            file.write("         2        10        10\n")
            file.write("  (NSTG(N),N=1,NROWS) \n")
            nstg_values = " ".join(["   1"] * NROW) # Needs to change to this:
            '''
            nstg_values = " ".join([f"{i:>10} {i:>10}" for i in range(1, NROW + 1)])
            
            '''
            file.write(nstg_values + "\n")
            file.write("  5  TIME STEPS FOR PRINTOUT \n")
            file.write("      9000      9000      9000      9000      9000\n")
            file.write("  MARKER FOR VARIABLES TO BE SENT TO THE OUTPUT FILE.\n")
            file.write(" 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            file.write("  STREAM SURFACES ON WHICH RESULTS ARE TO BE SENT TO   THE OUTPUT FILE \n")
            file.write(" ".join(f"0  " for _ in range(KM_grid_density)) + "\n")
            

    #writes the coordinates of all sections in a file for MULTALL
    # schreibt die Koordinaten aller Abschnitte in eine Datei für MULTALL
    def write_coordinates(x, rtheta, d, r, file, row, a, b, JM):
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


    # writes end of the file 
    def write_end_file(row, file, section, KM, levels, p_R_out, p_S_out, T_t1, p_t1, cm1, h_rel):
        
        if row == 1:
            x = round(p_R_out[0], 1)
            y = round(p_R_out[len(h_rel)-1], 1)
            t = round(T_t1[0], 4)
            p = round(p_t1[0], 1)
            um = round(cm1[0], 4)
        
        elif row == 2:
            x = round(p_S_out[0], 1)
            y = round(p_S_out[len(h_rel)-1], 1)
            t = round(T_t1[0], 4)
            p = round(p_t1[0], 1)
            um = round(cm1[0], 4)
            
        with open(file, "a", encoding='ascii') as file:
            if section == 0:
                file.write("  STARTING INLET BOUNDARY CONDITION DATA .\n")
                file.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
                file.write(f"        {KM}\n") # Number of Inlet Point wird Abhängig von der Gitterdichte KM 
                file.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
                
                value_KM = grid_adaption(KM)
                for i in range (0,len(value_KM), 8): # Zählweise in 8ter Schritten
                    file.write(" ".join(f"{v:.6f}" for v in value_KM[i:i+8])+"\n") # Schreibt die gebaute Zeile
                
                # Dynamische Anpassung der Inlet Bedingungen durch KM
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
                for _ in range(row):
                    file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
                file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS \n")
                file.write("   2.00000 1000\n")
            else:         
                if row == 1:
                    i = levels[section-1]
                    for j in range(len(h_rel)):
                        if round(h_rel[j],2) == i:
                            x = round(p_R_out[j], 1)
                            y = round(p_R_out[j], 1)

                elif row == 2:
                    i = levels[section-1]
                    for j in range(len(h_rel)):
                        if round(h_rel[j],2) == i:
                            x = round(p_S_out[j], 1)
                            y = round(p_S_out[j], 1)

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
                for _ in range(row):
                    file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
                file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS\n")
                file.write("   2.00000 1000\n")