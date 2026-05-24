# Author: Marco Wiens
# Version: 05.12.2024
# Radial-equilibrium
# Programm for calculation of radial equilibrium

import math
import numpy as np
import matplotlib as plt
import debug_log

Pi = math.pi



from Functions_losses import  angle_blade_in, angle_blade_out 
#from GUI import CompressorGui cant be used here because it closes the circle 




#function for meridional velocity
def rad_eq_cm(appr, position, r, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref, Dh_t):
    switch = 1
    if position == 1:
        switch = -1
    
    r_rel = max(r_ref / r, 0.0000001)
    cu_inf = (cu_ref_in + cu_ref_out) / 2
    
    # Free Vortex approach
    cm = cm_ref
    A = cu_inf * r_ref
    B = r_ref * Dh_t / (2 * u_ref)
    
    # Constant Reaction approach
    if appr == 2:
        A = cu_inf / r_ref
        cmq = cm_ref ** 2 + 2 * A ** 2 * (r_ref ** 2 - r ** 2 + switch * 2 * B / A * math.log(r_rel))
        if cmq <= 0:
            cmq = 0
        cm = math.sqrt(cmq)

    # Exponential Method approach
    if appr == 3:
        A = cu_inf
        cmq = cm_ref ** 2 + 2 * A * (A * math.log(r_rel) + switch * 2 * B * (1 / r - 1 / r_rel))
        if cmq <= 0:
            cmq = 0
        cm = math.sqrt(cmq)
    
    return cm

#function for circumferential velocity
def rad_eq_cu(appr, position, r, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref, Dh_t):
    switch = 1
    if position == 1:
        switch = -1

    r_rel = max(r_ref / r, 0.0000001)
    cu_inf = (cu_ref_in + cu_ref_out) / 2

    # Free Vortex approach
    exponent = -1
    A = cu_inf * r_ref
    B = r_ref * Dh_t / (2 * u_ref)
    cu = A * r**exponent + switch * B / r

    # Constant Reaction approach
    if appr == 2:
        exponent = 1
        A = cu_inf / r_ref
        cu = A * r**exponent + switch * B / r

    # Exponential Method approach
    if appr == 3:
        exponent = 0
        A = cu_inf
        cu = A * r**exponent + switch * B / r

    return cu
"""
#calculation of reference valuess
def references(stage, cu1, cu2, cu3, cm1, cm2, cm3, D_m2, u1, u2, u3, CompressorGui):
    # Here could be some errors due to a conversion between meters and milimeters because the original code used both units interchangably
    '''
    # Wraping inputs in lists if they are passed as single floats.
    # This prevents 'TypeError: float object is not subscriptable' when the 
    # code tries to access cu_list[stage-1] for single-stage calculations.
    cu1 = [cu1] if isinstance(cu1, (int, float)) else cu1
    cu2 = [cu2] if isinstance(cu2, (int, float)) else cu2
    cu3 = [cu3] if isinstance(cu3, (int, float)) else cu3
    
    
    meanline = CompressorGui.meanline_data
    '''

    # Ensureing all stage-dependent parameters are lists. 
    # If passed as single floats, wrap them 
    # in lists so the [stage-1] indexing doesn't crash the script.
    params = [cu1, cu2, cu3, cm1, cm2, cm3, u1, u2, u3]
    cu1, cu2, cu3, cm1, cm2, cm3, u1, u2, u3 = [
        [p] if isinstance(p, (int, float)) else p for p in params
    ]

    meanline = CompressorGui.meanline_data

    D_m1 = meanline['D_M1'] # Values are in meters nomenclature is wrong here
    D_m2 = meanline['D_M2'] # Values are in meters nomenclature is wrong here
    D_m3 = meanline['D_M3'] # Values are in meters nomenclature is wrong here
    
    
    cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref = [], [], [], [], []
    for cu_list in [cu1, cu2, cu3]:
        print(f"DEBUG: cu1={type(cu1)}, cu2={type(cu2)}, cu3={type(cu3)}")
        cu_ref_in.append(cu_list[stage-1]) 
        print(f"DEBUG: cu1={type(cu1)}, cu2={type(cu2)}, cu3={type(cu3)}")

    cu_ref_out.append(cu2[stage-1])

    cu_ref_out.append(cu2[stage-1])
    cu_ref_out.append(cu3[stage-1])

    for cm_list in [cm1, cm2, cm3]:
        cm_ref.append(cm_list[stage-1]) 

    for i in range(3):
        r_ref.append(D_m2[i]/(2.0))

    for u_list in [u1, u2, u3]:
        u_ref.append(u_list[stage-1]) 
    
    return D_m1, D_m2, D_m3, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref

"""

def references(stage, cu1, cu2, cu3, cm1, cm2, cm3, D_m2, u1, u2, u3, CompressorGui):
    # --- DEBUG START ---
    # print(f"DEBUG references: Requested stage={stage}, len(cu1)={len(cu1)}")
    # --- DEBUG END ---

    # SAFETY LOGIC: If stage+1 is requested for the exit of the last stage,
    # we must clamp the index to the last available stage data.
    calc_idx = stage - 1
    if calc_idx >= len(cu1):
        # print(f"DEBUG references: Index {calc_idx} out of range. Clamping to {len(cu1)-1}")
        calc_idx = len(cu1) - 1
    elif calc_idx < 0:
        calc_idx = 0

    cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref = [], [], [], [], []
    
    # Use calc_idx instead of stage-1
    cu_ref_in.append(cu1[calc_idx])
    cu_ref_out.append(cu2[calc_idx])
    cm_ref.append(cm2[calc_idx])
    r_ref.append(D_m2[calc_idx] / 2.0)
    u_ref.append(u2[calc_idx])
    
    return None, None, None, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref

# radial equilibrium for the rotor
def radial_equilibrium_R(stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui):

    # --- DATA STANDARDIZATION ---
    # This block ensures that all stage-dependent parameters are subscriptable (lists/arrays).
    # This allows the function to be called with full compressor lists (from main logic) 
    # or single stage values (from internal calls in radial_equilibrium_S).
    params_to_fix = {
        'D_S1': D_S1, 'D_S2': D_S2, 'D_S3': D_S3, 
        'D_H1': D_H1, 'D_H2': D_H2, 'D_H3': D_H3, 
        'D_m1': D_m1, 'D_m2': D_m2, 'D_m3': D_m3, 
        'b1': b1, 'b2': b2, 'b3': b3, 
        'cu1': cu1, 'cu2': cu2, 'cu3': cu3, 
        'u1': u1, 'u2': u2, 'u3': u3, 
        'cm1': cm1, 'cm2': cm2, 'cm3': cm3, 
        'delta_h_t': delta_h_t, 'T_t1': T_t1, 'T_t2': T_t2, 'T_t3': T_t3, 
        'p_t1': p_t1, 'p_t2': p_t2, 'p_t3': p_t3
    }
    
    # If a parameter is a float, wrap it in a list. 
    # If it is already a list, keep it.
    fixed = {k: ([v] if isinstance(v, (int, float, np.float64)) else v) for k, v in params_to_fix.items()}
    
    # Re-assign variables to the fixed versions
    D_S1, D_S2, D_S3 = fixed['D_S1'], fixed['D_S2'], fixed['D_S3']
    D_H1, D_H2, D_H3 = fixed['D_H1'], fixed['D_H2'], fixed['D_H3']
    D_m1, D_m2, D_m3 = fixed['D_m1'], fixed['D_m2'], fixed['D_m3']
    b1, b2, b3 = fixed['b1'], fixed['b2'], fixed['b3']
    cu1, cu2, cu3 = fixed['cu1'], fixed['cu2'], fixed['cu3']
    u1, u2, u3 = fixed['u1'], fixed['u2'], fixed['u3']
    cm1, cm2, cm3 = fixed['cm1'], fixed['cm2'], fixed['cm3']
    delta_h_t = fixed['delta_h_t']
    T_t1, T_t2, T_t3 = fixed['T_t1'], fixed['T_t2'], fixed['T_t3']
    p_t1, p_t2, p_t3 = fixed['p_t1'], fixed['p_t2'], fixed['p_t3']

    # --- CLAMPED INDEXING ---
    # Prevents stage+1 from exceeding list bounds at the compressor outlet
    stg_idx = stage - 1
    if stg_idx >= len(b1):
        stg_idx = len(b1) - 1
    elif stg_idx < 0:
        stg_idx = 0
    # ----------------------------

    meanline = CompressorGui.meanline_data
    kappa = meanline['kappa']
    R = meanline['R']
    cp = meanline['cp']
    
    l_R_t_R = meanline['l_R_t_R']
    d_R_l_R = meanline['d_R_l_R']
    incidence_R = meanline['incidence_R']
    z_R = meanline['z_R']
    
    h_H = [0.0, 0.2, 0.5, 0.8, 1.0]

    # Use 'stage' here because references() likely handles its own indexing logic
    _, _, _, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref = references(stage, cu1, cu2, cu3, cm1, cm2, cm3, D_m2, u1, u2, u3, CompressorGui)
    
    dh = 0.05
    h_rel = np.arange(0.0, 1.0 + dh, dh)
    
    # Rotor inlet
    r_R_in = []
    for i in range(len(h_rel)): 
        # Use stg_idx to prevent subscript errors
        b1_m = b1[stg_idx] / 1000
        
        if constant_r_parameter == 0:
            r_R_in.append(D_H1[stg_idx]/2.0 + h_rel[i]*b1_m)
        elif constant_r_parameter == 1:
            r_R_in.append(D_m1[stg_idx]/2.0 + (h_rel[i]-0.5)*b1_m)
        elif constant_r_parameter == 2:
            r_R_in.append(D_S1[stg_idx]/2.0 + (h_rel[i]-1)*b1_m)
        else:
            radius_err = "Allowed constant radius parameter: 0, 1 and 2."
            print(radius_err)
            debug_log.debug(radius_err, context="radial_equilibrium_R")

    c_m_R_in, c_u_R_in, u_R_in, w_R_in, T_R_in, p_R_in, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in = [], [], [], [], [], [], [], [], [], [], []
    for i in range(len(h_rel)):
        # Using [0] for ref values as references() typically returns the specific stage data already
        c_m_R_in.append(rad_eq_cm(approach, 1, r_R_in[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stg_idx]))
        c_u_R_in.append(rad_eq_cu(approach, 1, r_R_in[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stg_idx]))
        u_R_in.append(r_R_in[i] / r_ref[0] * u_ref[0])
        w_R_in.append(math.sqrt(c_m_R_in[i]**2 + (u_R_in[i] - c_u_R_in[i])**2))
        T_R_in.append(T_t1[stg_idx] - (c_m_R_in[i]**2 + c_u_R_in[i]**2) / (2 * cp))
        p_R_in.append(p_t1[stg_idx] * (T_R_in[i] / T_t1[stg_idx])**(kappa / (kappa - 1)))
        Ma_abs_R_in.append(math.sqrt(c_m_R_in[i]**2 + c_u_R_in[i]**2) / math.sqrt(kappa * R * T_R_in[i]))
        Ma_rel_R_in.append(w_R_in[i] / math.sqrt(kappa * R * T_R_in[i]))
        roh_R_in.append(p_R_in[i] / (T_R_in[i] * R))
        alpha_R_in.append(math.acos(c_u_R_in[i] / math.sqrt(c_u_R_in[i]**2 + c_m_R_in[i]**2)) / Pi * 180)
        beta_R_in.append(math.acos((c_u_R_in[i] - u_R_in[i]) / (math.sqrt((c_u_R_in[i] - u_R_in[i])**2 + c_m_R_in[i]**2))) / Pi * 180)

    MF_Integral_R_in = []
    for i in range(len(h_rel)-1):
        MF_Integral_R_in.append(Pi*(r_R_in[i+1]**2-r_R_in[i]**2)*(c_m_R_in[i+1]*roh_R_in[i+1]+c_m_R_in[i]*roh_R_in[i])/2)

    MF_R_in = sum(MF_Integral_R_in)


    # Rotor outlet/ stator inlet
    r_R_out = []
    for i in range(len(h_rel)): 
        b2_m = b2[stg_idx] / 1000.0
        if constant_r_parameter == 0:
            r_R_out.append(D_H2[stg_idx]/2.0 + h_rel[i]*b2_m)
        elif constant_r_parameter == 1:
            r_R_out.append(D_m2[stg_idx]/2.0 + (h_rel[i]-0.5)*b2_m)
        elif constant_r_parameter == 2:
            r_R_out.append(D_S2[stg_idx]/2.0 + (h_rel[i]-1)*b2_m)
        else:
            radius_err = "Allowed constant radius parameter: 0, 1 and 2."
            print(radius_err)
            debug_log.debug(radius_err, context="radial_equilibrium_R")

    c_m_R_out, c_u_R_out, c_R_out, u_R_out, w_R_out, T_R_out, p_R_out, Ma_abs_R_out, Ma_rel_R_out, roh_R_out, alpha_R_out, beta_R_out = [], [], [], [], [], [], [], [], [], [], [], []
    for i in range(len(h_rel)):
        c_m_R_out.append(rad_eq_cm(approach, 2, r_R_out[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stg_idx]))
        c_u_R_out.append(rad_eq_cu(approach, 2, r_R_out[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stg_idx-1]))
        c_R_out.append(math.sqrt(c_m_R_out[i]**2 + c_u_R_out[i]**2))            
        u_R_out.append(r_R_out[i] / r_ref[0] * u_ref[0])
        w_R_out.append(math.sqrt(c_m_R_out[i]**2 + (u_R_out[i] - c_u_R_out[i])**2))
        T_R_out.append(T_t2[stg_idx-1] - (c_m_R_out[i]**2 + c_u_R_out[i]**2) / (2 * cp)) 
        Ma_abs_R_out.append(math.sqrt(c_m_R_out[i]**2 + c_u_R_out[i]**2) / math.sqrt(kappa * R * T_R_out[i]))
        Ma_rel_R_out.append(u_R_out[i] / math.sqrt(kappa * R * T_R_out[i]))
        p_R_out.append(p_t2[stg_idx-1] * (T_R_out[i] / T_t2[stg_idx-1])**(kappa / (kappa - 1)))
        roh_R_out.append(p_R_out[i] / (T_R_out[i] * R))
        alpha_R_out.append(math.acos(c_u_R_out[i] / math.sqrt(c_u_R_out[i]**2 + c_m_R_out[i]**2)) / Pi * 180)
        beta_R_out.append(math.acos((c_u_R_out[i] - u_R_out[i]) / (math.sqrt((c_u_R_out[i] - u_R_out[i])**2 + c_m_R_out[i]**2))) / Pi * 180)
    

    MF_Integral_R_out = []
    for i in range(len(h_rel)-1):
        MF_Integral_R_out.append(Pi*(r_R_out[i+1]**2-r_R_out[i]**2)*(c_m_R_out[i+1]*roh_R_out[i+1]+c_m_R_out[i]*roh_R_out[i])/2)
        
    MF_S = sum(MF_Integral_R_out)

    beta_blade_R_in, beta_blade_R_out = [], []
    for i in range(len(h_rel)):
        beta_blade_R_in.append(angle_blade_in(beta_R_in[i], beta_R_out[i], w_R_in[i], w_R_out[i], T_R_in[i], T_R_out[i], l_R_t_R[0],  d_R_l_R[0], incidence_R[0], R, kappa))
        beta_blade_R_out.append(angle_blade_out(beta_R_in[i], beta_R_out[i],  w_R_in[i], w_R_out[i], T_R_in[i], T_R_out[i], l_R_t_R[0],  d_R_l_R[0], incidence_R[0], R, kappa))
    
    # Rotor data
    solidity_R = [l_R_t_R[stg_idx-1]]*len(h_rel)
    l_R, axial_length_R, delta_beta_R, w_R_out_w_R_in, D_R = [], [], [], [], []
    for i in range(len(h_rel)):
        l_R.append(solidity_R[i]*2*Pi*(r_R_out[i]+r_R_in[i])/(2*z_R[stg_idx-1])*1000)
        axial_length_R.append(l_R[i]*math.sin((beta_blade_R_out[i]+beta_blade_R_in[i])/(2*180)*Pi))
        delta_beta_R.append(beta_R_out[i]-beta_R_in[i])
        w_R_out_w_R_in.append(w_R_out[i]/w_R_in[i])
        D_R.append(1-w_R_out_w_R_in[i]+abs((c_u_R_out[i]-u_R_out[i])-(c_u_R_in[i]-u_R_in[i]))/(2*solidity_R[i]*w_R_in[i]))
    
    return h_rel, l_R, r_R_out, c_m_R_in, c_m_R_out, c_u_R_in, c_u_R_out, c_R_out, u_R_in, u_R_out, T_R_in, T_R_out, p_R_in, p_R_out, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in, alpha_R_out, beta_R_out, beta_blade_R_in, beta_blade_R_out, D_R


# radial equilibrium for the stator 
def radial_equilibrium_S(stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui):        
    
    # --- DATA STANDARDIZATION ---
    # This block ensures all stage-dependent inputs are treated as subscriptable collections.
    # It allows the function to handle both multi-stage lists and single-stage scalars.
    input_params = {
        'D_S1': D_S1, 'D_S2': D_S2, 'D_S3': D_S3, 
        'D_H1': D_H1, 'D_H2': D_H2, 'D_H3': D_H3, 
        'D_m1': D_m1, 'D_m2': D_m2, 'D_m3': D_m3, 
        'b1': b1, 'b2': b2, 'b3': b3, 
        'cu1': cu1, 'cu2': cu2, 'cu3': cu3, 
        'u1': u1, 'u2': u2, 'u3': u3, 
        'cm1': cm1, 'cm2': cm2, 'cm3': cm3, 
        'delta_h_t': delta_h_t, 
        'T_t1': T_t1, 'T_t2': T_t2, 'T_t3': T_t3, 
        'p_t1': p_t1, 'p_t2': p_t2, 'p_t3': p_t3
    }
    
    # Wrap single floats into lists; keep existing lists/arrays as they are.
    fixed = {k: ([v] if isinstance(v, (int, float, np.float64)) else v) for k, v in input_params.items()}
    
    # Re-assign variables to ensure downstream compatibility
    D_S1, D_S2, D_S3 = fixed['D_S1'], fixed['D_S2'], fixed['D_S3']
    D_H1, D_H2, D_H3 = fixed['D_H1'], fixed['D_H2'], fixed['D_H3']
    D_m1, D_m2, D_m3 = fixed['D_m1'], fixed['D_m2'], fixed['D_m3']
    b1, b2, b3 = fixed['b1'], fixed['b2'], fixed['b3']
    cu1, cu2, cu3 = fixed['cu1'], fixed['cu2'], fixed['cu3']
    u1, u2, u3 = fixed['u1'], fixed['u2'], fixed['u3']
    cm1, cm2, cm3 = fixed['cm1'], fixed['cm2'], fixed['cm3']
    delta_h_t = fixed['delta_h_t']
    T_t1, T_t2, T_t3 = fixed['T_t1'], fixed['T_t2'], fixed['T_t3']
    p_t1, p_t2, p_t3 = fixed['p_t1'], fixed['p_t2'], fixed['p_t3']

    # Determine internal indexing: 
    # If the input list has multiple entries, use stage-1. 
    # If it's a single-entry list (from a scalar), use 0.
    stg_idx = stage - 1 if len(b1) > 1 else 0
    # ----------------------------

    # Inlet values of the stator are the outlet values of the current rotor
    # Using standardized variables ensures the internal radial_equilibrium_R call doesn't crash.
    (h_rel, l_R, r_S_in, c_m_R_in, c_m_S_in, c_u_R_in, c_u_S_in, c_S_in, u_R_in, 
     u_S_in, T_R_in, T_S_in, p_R_in, p_S_in, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, 
     alpha_R_in, beta_R_in, alpha_S_in, beta_S_in, beta_blade_R_in, 
     beta_blade_R_out, D_R) = radial_equilibrium_R(
         stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, 
         D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, 
         delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui
    )
    
    # Outlet values of the stator correspond to the inlet values of the following rotor.
    # Note: If stage+1 exceeds the list length, radial_equilibrium_R standardization 
    # will catch the index and redirect it appropriately.
    (h_rel, l_R, r_R_out, c_m_S_out, c_m_R_out, c_u_S_out, c_u_R_out, c_R_out, 
     u_S_out, u_R_out, T_S_out, T_R_out, p_S_out, p_R_out, Ma_abs_S_out, Ma_rel_S_out, 
     roh_S_out, alpha_S_out, beta_R_in, alpha_R_out, beta_R_out, beta_blade_R_in, 
     beta_blade_R_out, D_R) = radial_equilibrium_R(
         stage+1, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, 
         D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, 
         delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui
    )
    
    meanline = CompressorGui.meanline_data
    kappa = meanline['kappa']
    R = meanline['R']
    
    l_S_t_S = meanline['l_S_t_S']
    d_S_l_S = meanline['d_S_l_S']
    incidence_S = meanline['incidence_S']
    z_S = meanline['z_S']
    
    # Stator Geometry and Velocity Triangles
    r_S_out = []
    for i in range(len(h_rel)):
        # Apply stg_idx to ensure correct list indexing
        b3_m = b3[stg_idx] / 1000.0 
        if constant_r_parameter == 0:
            r_S_out.append(D_H3[stg_idx]/2.0 + h_rel[i]*b3_m)
        elif constant_r_parameter == 1:
            r_S_out.append(D_m3[stg_idx]/2.0 + (h_rel[i]-0.5)*b3_m)
        elif constant_r_parameter == 2:
            r_S_out.append(D_S3[stg_idx]/2.0 + (h_rel[i]-1)*b3_m)
        else:
            radius_err = "Allowed constant radius parameter: 0, 1 and 2."
            print(radius_err)
            debug_log.debug(radius_err, context="radial_equilibrium_S")

    c_S_out = [math.sqrt(c_m_S_out[i]**2 + c_u_S_out[i]**2) for i in range(len(h_rel))]
    
    beta_blade_S_in, beta_blade_S_out = [], []
    for i in range(len(h_rel)):
        # Meanline properties are usually provided as lists per stage
        beta_blade_S_in.append(angle_blade_in(
            alpha_S_in[i], alpha_S_out[i], c_S_in[i], c_S_out[i], T_S_in[i], T_S_out[i], 
            l_S_t_S[stg_idx], d_S_l_S[stg_idx], incidence_S[stg_idx], R, kappa))
        beta_blade_S_out.append(angle_blade_out(
            alpha_S_in[i], alpha_S_out[i], c_S_in[i], c_S_out[i], T_S_in[i], T_S_out[i], 
            l_S_t_S[stg_idx], d_S_l_S[stg_idx], incidence_S[stg_idx], R, kappa))
    
    # Stator Performance Data (Solidity, Diffusion Factor, etc.)
    solidity_S = [l_S_t_S[stg_idx]] * len(h_rel)
    l_S, axial_length_S, delta_beta_S, c_S_out_c_S_in, D_S = [], [], [], [], []
    for i in range(len(h_rel)):
        l_S.append(solidity_S[i]*2*Pi*(r_S_in[i]+r_S_out[i])/(2*z_S[stg_idx])*1000)
        axial_length_S.append(l_S[i]*math.sin((beta_blade_S_out[i]+beta_blade_S_in[i])/(2*180)*Pi))
        delta_beta_S.append(beta_blade_S_out[i]-beta_blade_S_in[i])
        c_S_out_c_S_in.append(c_S_out[i]/c_S_in[i])
        D_S.append(1-c_S_out_c_S_in[i]+abs(c_u_S_out[i]-c_u_S_in[i])/(2*solidity_S[i]*c_S_in[i]))
    
    return h_rel, l_S, c_m_S_in, c_m_S_out, c_u_S_in, c_u_S_out, c_S_out, T_S_in, T_S_out, p_S_in, p_S_out, alpha_S_in, beta_S_in, alpha_S_out, beta_blade_S_in, beta_blade_S_out, D_S

""" 
# radial equilibrium for the rotor
def radial_equilibrium_R(stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui):

    # DEBUG: Find the non-subscriptable variable
    check_vars = {'b1': b1, 'cu1': cu1, 'cm1': cm1, 'D_S1': D_S1}
    for name, val in check_vars.items():
        if not isinstance(val, (list, np.ndarray)):
            print(f"CRITICAL ERROR: Variable '{name}' passed to radial_equilibrium_R is {type(val)}, expected list/array!")

    meanline = CompressorGui.meanline_data
    kappa = meanline['kappa']
    R = meanline['R']
    cp = meanline['cp']
    
    l_R_t_R = meanline['l_R_t_R']
    d_R_l_R = meanline['d_R_l_R']
    incidence_R = meanline['incidence_R']
    incidence_S = meanline['incidence_S']
    z_R = meanline['z_R']
    
    h_H = [0.0, 0.2, 0.5, 0.8, 1.0]

    _, _, _, cu_ref_in, cu_ref_out, cm_ref, r_ref, u_ref = references(stage, cu1, cu2, cu3, cm1, cm2, cm3, D_m2, u1, u2, u3, CompressorGui)
    
    dh = 0.05
    h_rel = np.arange(0.0, 1.0 + dh, dh)
    
    # Rotor inlet
    r_R_in = []
    for i in range(len(h_rel)): 
        b1_m = b1[stage-1] / 1000
        
        if constant_r_parameter == 0:
            r_R_in.append(D_H1[stage-1]/2.0 + h_rel[i]*b1_m)

        elif constant_r_parameter == 1:
            r_R_in.append(D_m1[stage-1]/2.0 + (h_rel[i]-0.5)*b1_m)

        elif constant_r_parameter == 2:
            r_R_in.append(D_S1[stage-1]/2.0 + (h_rel[i]-1)*b1_m)

        else:
            print("Allowed constant radius parameter: 0, 1 and 2.")

    c_m_R_in, c_u_R_in, u_R_in, w_R_in, T_R_in, p_R_in, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in = [], [], [], [], [], [], [], [], [], [], []
    for i in range(len(h_rel)):
        c_m_R_in.append(rad_eq_cm(approach, 1, r_R_in[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stage-1]))
        c_u_R_in.append(rad_eq_cu(approach, 1, r_R_in[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stage-1]))
        u_R_in.append(r_R_in[i] / r_ref[0] * u_ref[0])
        w_R_in.append(math.sqrt(c_m_R_in[i]**2 + (u_R_in[i] - c_u_R_in[i])**2))
        T_R_in.append(T_t1[stage-1] - (c_m_R_in[i]**2 + c_u_R_in[i]**2) / (2 * cp))
        p_R_in.append(p_t1[stage-1] * (T_R_in[i] / T_t1[stage-1])**(kappa / (kappa - 1)))
        Ma_abs_R_in.append(math.sqrt(c_m_R_in[i]**2 + c_u_R_in[i]**2) / math.sqrt(kappa * R * T_R_in[i]))
        Ma_rel_R_in.append(w_R_in[i] / math.sqrt(kappa * R * T_R_in[i]))
        roh_R_in.append(p_R_in[i] / (T_R_in[i] * R))
        alpha_R_in.append(math.acos(c_u_R_in[i] / math.sqrt(c_u_R_in[i]**2 + c_m_R_in[i]**2)) / Pi * 180)
        beta_R_in.append(math.acos((c_u_R_in[i] - u_R_in[i]) / (math.sqrt((c_u_R_in[i] - u_R_in[i])**2 + c_m_R_in[i]**2))) / Pi * 180)

    MF_Integral_R_in = []
    for i in range(len(h_rel)-1):
        MF_Integral_R_in.append(Pi*(r_R_in[i+1]**2-r_R_in[i]**2)*(c_m_R_in[i+1]*roh_R_in[i+1]+c_m_R_in[i]*roh_R_in[i])/2)

    MF_R_in = sum(MF_Integral_R_in)

    # Rotor outlet/ stator inlet
    r_R_out = []
    for i in range(len(h_rel)): 
        b2_m = b2[stage-1] / 1000.0
        if constant_r_parameter == 0:
            r_R_out.append(D_H2[stage-1]/2.0 + h_rel[i]*b2_m)

        elif constant_r_parameter == 1:
            r_R_out.append(D_m2[stage-1]/2.0 + (h_rel[i]-0.5)*b2_m)

        elif constant_r_parameter == 2:
            r_R_out.append(D_S2[stage-1]/2.0 + (h_rel[i]-1)*b2_m)

        else:
            print("Allowed constant radius parameter: 0, 1 and 2.")

    c_m_R_out, c_u_R_out, c_R_out, u_R_out, w_R_out, T_R_out, p_R_out, Ma_abs_R_out, Ma_rel_R_out, roh_R_out, alpha_R_out, beta_R_out = [], [], [], [], [], [], [], [], [], [], [], []
    for i in range(len(h_rel)):
        c_m_R_out.append(rad_eq_cm(approach, 2, r_R_out[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stage-1]))
        c_u_R_out.append(rad_eq_cu(approach, 2, r_R_out[i], cu_ref_in[0], cu_ref_out[0], cm_ref[0], r_ref[0], u_ref[0], delta_h_t[stage-1]))
        c_R_out.append(math.sqrt(c_m_R_out[i]**2 + c_u_R_out[i]**2))            
        u_R_out.append(r_R_out[i] / r_ref[0] * u_ref[0])
        w_R_out.append(math.sqrt(c_m_R_out[i]**2 + (u_R_out[i] - c_u_R_out[i])**2))
        T_R_out.append(T_t2[stage-1] - (c_m_R_out[i]**2 + c_u_R_out[i]**2) / (2 * cp)) 
        Ma_abs_R_out.append(math.sqrt(c_m_R_out[i]**2 + c_u_R_out[i]**2) / math.sqrt(kappa * R * T_R_out[i]))
        Ma_rel_R_out.append(u_R_out[i] / math.sqrt(kappa * R * T_R_out[i]))
        p_R_out.append(p_t2[stage-1] * (T_R_out[i] / T_t2[stage-1])**(kappa / (kappa - 1)))
        roh_R_out.append(p_R_out[i] / (T_R_out[i] * R))
        alpha_R_out.append(math.acos(c_u_R_out[i] / math.sqrt(c_u_R_out[i]**2 + c_m_R_out[i]**2)) / Pi * 180)
        beta_R_out.append(math.acos((c_u_R_out[i] - u_R_out[i]) / (math.sqrt((c_u_R_out[i] - u_R_out[i])**2 + c_m_R_out[i]**2))) / Pi * 180)
    

    MF_Integral_R_out = []
    for i in range(len(h_rel)-1):
        MF_Integral_R_out.append(Pi*(r_R_out[i+1]**2-r_R_out[i]**2)*(c_m_R_out[i+1]*roh_R_out[i+1]+c_m_R_out[i]*roh_R_out[i])/2)
        
    MF_S = sum(MF_Integral_R_out)

    beta_blade_R_in, beta_blade_R_out = [], []
    for i in range(len(h_rel)):
        beta_blade_R_in.append(angle_blade_in(beta_R_in[i], beta_R_out[i], w_R_in[i], w_R_out[i], T_R_in[i], T_R_out[i], l_R_t_R[0],  d_R_l_R[0], incidence_R[0], R, kappa))
        beta_blade_R_out.append(angle_blade_out(beta_R_in[i], beta_R_out[i],  w_R_in[i], w_R_out[i], T_R_in[i], T_R_out[i], l_R_t_R[0],  d_R_l_R[0], incidence_R[0], R, kappa))
    
    # Rotor data
    solidity_R = [l_R_t_R[stage-1]]*len(h_rel)
    l_R, axial_length_R, delta_beta_R, w_R_out_w_R_in, D_R = [], [], [], [], []
    for i in range(len(h_rel)):
        l_R.append(solidity_R[i]*2*Pi*(r_R_out[i]+r_R_in[i])/(2*z_R[stage-1])*1000)
        axial_length_R.append(l_R[i]*math.sin((beta_blade_R_out[i]+beta_blade_R_in[i])/(2*180)*Pi))
        delta_beta_R.append(beta_R_out[i]-beta_R_in[i])
        w_R_out_w_R_in.append(w_R_out[i]/w_R_in[i])
        D_R.append(1-w_R_out_w_R_in[i]+abs((c_u_R_out[i]-u_R_out[i])-(c_u_R_in[i]-u_R_in[i]))/(2*solidity_R[i]*w_R_in[i]))
    
    return h_rel, l_R, r_R_out, c_m_R_in, c_m_R_out, c_u_R_in, c_u_R_out, c_R_out, u_R_in, u_R_out, T_R_in, T_R_out, p_R_in, p_R_out, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in, alpha_R_out, beta_R_out, beta_blade_R_in, beta_blade_R_out, D_R

# radial equilibrium for the stator         
def radial_equilibrium_S(stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui):        
    
    # inlet values of the stator are the outlet values of the rotor befor
    h_rel, l_R, r_S_in, c_m_R_in, c_m_S_in, c_u_R_in, c_u_S_in, c_S_in, u_R_in, u_S_in, T_R_in, T_S_in, p_R_in, p_S_in, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in, alpha_S_in, beta_S_in, beta_blade_R_in, beta_blade_R_out, D_R  = radial_equilibrium_R(stage, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui)
    
    # outlet values of the stator should be inlet values of the following rotor
    h_rel, l_R, r_R_out, c_m_S_out, c_m_R_out, c_u_S_out, c_u_R_out, c_R_out, u_S_out, u_R_out, T_S_out, T_R_out, p_S_out, p_R_out, Ma_abs_S_out, Ma_rel_S_out, roh_S_out, alpha_S_out, beta_R_in, alpha_R_out, beta_R_out, beta_blade_R_in, beta_blade_R_out, D_R = radial_equilibrium_R(stage+1, approach, constant_r_parameter, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, T_t1, T_t2, T_t3, p_t1, p_t2, p_t3, CompressorGui)
    
    meanline = CompressorGui.meanline_data
    kappa = meanline['kappa']
    R = meanline['R']
    
    l_S_t_S = meanline['l_S_t_S']
    d_S_l_S = meanline['d_S_l_S']
    incidence_S = meanline['incidence_S']
    z_S = meanline['z_S']
    
    #Stator
    r_S_out = []
    for i in range(len(h_rel)):
        b3_m = b3[stage-1] / 1000.0 
        if constant_r_parameter == 0:
            r_S_out.append(D_H3[stage-1]/2.0 + h_rel[i]*b3_m)

        elif constant_r_parameter == 1:
            r_S_out.append(D_m3[stage-1]/2.0 + (h_rel[i]-0.5)*b3_m)

        elif constant_r_parameter == 2:
            r_S_out.append(D_S3[stage-1]/2.0 + (h_rel[i]-1)*b3_m)
        else:
            print("Allowed constant radius parameter: 0, 1 and 2.")

    c_S_out = []
    for i in range(len(h_rel)):
        c_S_out.append(math.sqrt(c_m_S_out[i]**2 + c_u_S_out[i]**2))
    
    
    beta_blade_S_in, beta_blade_S_out = [], []
    for i in range(len(h_rel)):
        beta_blade_S_in.append(angle_blade_in(alpha_S_in[i], alpha_S_out[i], c_S_in[i], c_S_out[i], T_S_in[i], T_S_out[i], l_S_t_S[stage-1],  d_S_l_S[stage-1], incidence_S[stage-1], R, kappa))
        beta_blade_S_out.append(angle_blade_out(alpha_S_in[i], alpha_S_out[i], c_S_in[i], c_S_out[i], T_S_in[i], T_S_out[i], l_S_t_S[stage-1],  d_S_l_S[stage-1], incidence_S[stage-1], R, kappa))
    
    #Stator data
    solidity_S = [l_S_t_S[stage-1]]*len(h_rel)
    l_S, axial_length_S, delta_beta_S, c_S_out_c_S_in, D_S = [], [], [], [], []
    for i in range(len(h_rel)):
        l_S.append(solidity_S[i]*2*Pi*(r_S_in[i]+r_S_out[i])/(2*z_S[stage-1])*1000)
        axial_length_S.append(l_S[i]*math.sin((beta_blade_S_out[i]+beta_blade_S_in[i])/(2*180)*Pi))
        delta_beta_S.append(beta_blade_S_out[i]-beta_blade_S_in[i])
        c_S_out_c_S_in.append(c_S_out[i]/c_S_in[i])
        D_S.append(1-c_S_out_c_S_in[i]+abs(c_u_S_out[i]-c_u_S_in[i])/(2*solidity_S[i]*c_S_in[i]))
    
    return h_rel, l_S, c_m_S_in, c_m_S_out, c_u_S_in, c_u_S_out, c_S_out, T_S_in, T_S_out, p_S_in, p_S_out, alpha_S_in, beta_S_in, alpha_S_out, beta_blade_S_in, beta_blade_S_out, D_S	
"""


    

