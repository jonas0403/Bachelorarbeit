# Author: Marco Wiens
# Version:09.04.2024
# funcions_losses
# Programm for all loss functions, diffusion and Reynolds-number

import math
Pi = math.pi

# clearance loss
def xi_a_cl(angle_in, angle_out, solidity, clearance, channelheight):
    cc = 0.6
    ang_in = angle_in / 180.0 * math.pi
    ang_out = angle_out / 180.0 * math.pi
    s2t = solidity
    t2s = 1 / s2t
    h = channelheight / 1000.0
    d_cl = clearance / 1000.0
    
    xi_a_cl = cc * d_cl / (math.sqrt(2) * h) * math.sqrt(t2s) \
            * math.sqrt(abs(math.cos(ang_out - 2 * ang_in) + math.cos(ang_in) - math.cos(ang_out) - math.cos(2 * ang_out - ang_in))) \
            * (math.sin(ang_in) + math.sin(ang_out) + t2s * math.sin(abs(ang_out - ang_in))) \
            * math.sin(abs(ang_out - ang_in)) / ((math.sin(ang_in)) ** 3 * math.sin(ang_out))
    
    return xi_a_cl

# secondary flow loss
def xi_a_sec(angle_in, angle_out, solidity, pitch, channelheight):
    
    ang_in = angle_in / 180.0 * math.pi
    ang_out = angle_out / 180.0 * math.pi
    ang_m = math.atan(2 / (math.cos(ang_in) / math.sin(ang_in) + math.cos(ang_out) / math.sin(ang_out)))
    if ang_m < 0:
        ang_m += math.pi
    
    s2t = solidity
    t = pitch / 1000.0
    s = s2t * t
    h = channelheight / 1000.0
    
    xi_a_sec = 0.75 * 0.1336 * s / (8 * h) * math.sin(ang_out) / math.sqrt(math.sin(ang_in)) \
             * (2 * (math.cos(ang_in) / math.sin(ang_in) - math.cos(ang_out) / math.sin(ang_out)) * math.sin(ang_m)) ** 2 \
             * math.sin(ang_out) ** 2 / math.sin(ang_m) ** 3
    
    return xi_a_sec

# incidence angle loss
def xi_ac_inc(angle_in, angle_out, incidence):
    ang_in = angle_in / 180.0 * Pi
    ang_out = angle_out / 180.0 * Pi
    inc = incidence / 180.0 * Pi
    
    xi_ac_inc = (math.sin(inc))**2 * (math.sin(ang_out) / math.sin(ang_in))**2
    
    return xi_ac_inc

# Mach-number related loss
def xi_ac_ma(vel_in, T_in):

    kappa = 1.4
    r = 287.0
    
    # Calculate Mach number at inlet
    Ma_in = vel_in / math.sqrt(kappa * r * T_in)
    omega = 0.0
    
    if Ma_in >= 1.0:
        omega = 0.32 * Ma_in ** 2 - 0.62 * Ma_in + 0.3
    
    # Calculate the factor
    fak = 2 / kappa * (((1 + (kappa - 1) / 2 * Ma_in ** 2) ** (kappa / (kappa - 1)) - 1) / Ma_in ** 2)
    
    # Calculate trailing edge losses
    xi_ac_ma = omega * fak
    
    return xi_ac_ma

# profil loss
def xi_ac_pro(angle_in, angle_out, solidity):

    cd = 0.002
    ang_in = angle_in / 180 * math.pi
    ang_out = angle_out / 180 * math.pi
    s2t = solidity
    t2s = 1 / s2t
    
    xi_ac_pro = cd * ((1 / math.sin(ang_in) + 1 / math.sin(ang_out)) / (1 / math.sin(ang_in)) ** 2) * \
                (s2t * ((1 / math.sin(ang_in)) ** 2 + (1 / math.sin(ang_out)) ** 2 \
                + 2 * t2s * (1 / math.tan(ang_out) - 1 / math.tan(ang_in)) ** 2))
    
    return xi_ac_pro

# trailing edge losses in an AXIAL COMPRESSOR
def xi_ac_te(angle_in, angle_out, solidity, pitch, thickness_TE, Re_x):    
    cpb = 0.2
    ang_in = angle_in / 180 * math.pi
    ang_out = angle_out / 180 * math.pi
    s2t = solidity
    t = pitch / 1000
    s = s2t * t
    d_te = thickness_TE / 1000
    d_1 = s * 0.046 * Re_x ** -0.2
    d_2 = s * 0.036 * Re_x ** -0.2
     
    xi_ac_te = (math.sin(ang_in) / math.sin(ang_out)) ** 2 * \
               (cpb * (t * math.sin(ang_out) * d_te) / (t * math.sin(ang_out) - d_te - d_1) ** 2 + \
                (2 * t * math.sin(ang_out) * d_2) / (t * math.sin(ang_out) - d_te - d_1) ** 2 + \
                (d_1 + d_te) ** 2 / (t * math.sin(ang_out) - d_te - d_1) ** 2)
    
    return xi_ac_te

# Reynolds-number
def Re(rho, cref, x, t):
    # Sutherland law of viscosity for air
    mue0 = 0.174 * 10 ** -4
    T0 = 283.15
    s = 110.4
     
    mue = mue0 * (t / T0) ** 1.5 * (T0 + s) / (t + s)
     
    Re = rho * cref * x / 1000 / mue
    return Re

# metal angle inlet
def angle_blade_in(angle_in, angle_out, vel_in, vel_out, T_in, T_out, solidity, thickness2chord, incidence, R, kappa):

    # Convert angle to radians
    ang_in = angle_in / 180.0 * math.pi
    ang_out = angle_out / 180.0 * math.pi
    ang_m = (ang_out + ang_in) / 2.0
    inc = incidence / 180.0 * math.pi
    rot = 0.0
    
    # If the mean angle is greater than Pi/2, then reverse
    if ang_m > math.pi / 2.0:
        ang_m = math.pi - ang_m
        ang_in = math.pi - ang_in
        ang_out = math.pi - ang_out
        rot = math.pi
    
    ang_ins = ang_in + inc
    s2t = solidity
    t2s = 1.0 / s2t
    d2s = thickness2chord
    
    # Prandl-Glauert transformation
    Ma = (vel_out + vel_in) / 2.0 / math.sqrt(kappa * R * (T_out + T_in) / 2.0)
    #print(f"vel_out = {vel_out}")
    #print(f"vel_in = {vel_in}")
    #print(f"T_out = {T_out}")
    #print(f"T_in = {T_in}")
    Ma_in = vel_in / math.sqrt(kappa * R * T_in)
    Ma_lim = min(abs(Ma), 0.8)
    #print(f"Ma_in({Ma_in})= vel_in({vel_in}) / math.sqrt(kappa({kappa}) * R({R}) * T_in({T_in})")
    #print(f"Ma: {Ma}")
    #print(f"Ma_lim: {Ma_lim}")
    PGSF = math.sqrt(1 - Ma_lim ** 2)                                               # Prandl-Glauert scaling factor
    
    ang_mi = math.atan(PGSF * math.tan(ang_m))
    ang_ini = ang_mi - math.atan(math.tan(ang_m - ang_in) / PGSF)
    ang_insi = ang_mi - math.atan(math.tan(ang_m - ang_ins) / PGSF)
    ang_outi = ang_mi + math.atan(math.tan(ang_out - ang_m) / PGSF)
    
    t2si = t2s * math.sqrt((math.cos(ang_m)) ** 2 + PGSF ** 2 * (math.sin(ang_m)) ** 2)
    t2si_lim = min(t2si, 1.75)
    d2si = d2s / PGSF
    
    if t2s >= 0.6:
        ai = 0.0037 * math.sin(ang_mi) + 0.9864
        bi = 3.5497 * (math.sin(ang_mi)) ** (-0.3792)
        ci = -1.1038 * (math.sin(ang_mi)) ** 2 + 1.801 * math.sin(ang_mi) + 0.9864
        di = 0.5449 * math.sin(ang_mi) + 0.1611
        
        A = di + (ai - di) / (1 + (t2si / ci) ** bi)
    else:
        A = (1 - 0.98264403) / 0.6 * t2si + 1
    
    inci = ang_insi - ang_ini
    ang_outsi = ang_outi + (1 - A) * inci
    
    mue0 = 0.4867675 + (-0.0019722 - 0.4867675) / (1 + (t2si / 2.017826) ** 4.965654) + (-0.4260008 * t2si + 1)
    
    a1 = -0.66699 * t2si_lim ** 5 + 2.72709 * t2si_lim ** 4 - 3.57363 * t2si_lim ** 3 + 1.75986 * t2si_lim ** 2 - 0.5769 * t2si_lim
    b1 = 1.07109 * t2si_lim ** 5 - 4.35528 * t2si_lim ** 4 + 5.61798 * t2si_lim ** 3 - 2.71971 * t2si_lim ** 2 + 1.16433 * t2si_lim
    c1 = -0.42012 * t2si_lim ** 5 + 1.69992 * t2si_lim ** 4 - 2.15442 * t2si_lim ** 3 + 1.03032 * t2si_lim ** 2 - 0.60624 * t2si_lim + 0.0019722
    
    dmue = a1 * (math.sin(ang_mi)) ** 2 + b1 * math.sin(ang_mi) + c1
    mue = max(mue0 + dmue, 0.1)
    
    de_al_1 = (1 - mue) / (2 * mue) * (ang_outsi - ang_insi)
    
    de_al_2 = 5 * (-5.243 * (math.sin(abs(ang_mi - math.pi / 4))) ** 2 - 1.4408 * math.sin(abs(ang_mi - math.pi / 4)) + 4) * d2si / t2si ** 2
    de_al_2 = de_al_2 / 180.0 * math.pi
    
    ang_bld_ini = ang_insi - de_al_1 + de_al_2
    ang_bld_outi = ang_outsi + de_al_1 + de_al_2
    
    # Back transformation
    ang_bld_in = ang_m - math.atan(PGSF * math.tan(ang_mi - ang_bld_ini))
    ang_bld_in = ang_bld_in / math.pi * 180.0
    
    if rot > 0:
        ang_bld_in = 180.0 - ang_bld_in
    
    if Ma_in > 0.8:
        Ma_lim = min(Ma_in, 1.0)
        ang_bld_in = angle_in + (ang_bld_in - angle_in) / 0.2 * (1 - Ma_lim)
    
    return ang_bld_in

# metal angele outlet
def angle_blade_out(angle_in, angle_out, vel_in, vel_out, T_in, T_out, solidity, thickness2chord, incidence, R, kappa):
    
    ang_in = angle_in / 180.0 * math.pi
    ang_out = angle_out / 180.0 * math.pi
    ang_m = (ang_out + ang_in) / 2.0
    inc = incidence / 180.0 * math.pi
    rot = 0.0
    
    if ang_m > math.pi / 2.0:
        ang_m = math.pi - ang_m
        ang_in = math.pi - ang_in
        ang_out = math.pi - ang_out
        rot = math.pi
        
    ang_ins = ang_in + inc
    
    s2t = solidity
    t2s = 1 / s2t
    d2s = thickness2chord
    
    Ma = (vel_out + vel_in) / 2.0 / math.sqrt(kappa * R * (T_out + T_in) / 2.0)
    Ma_out = vel_out / math.sqrt(kappa * R * T_out)
    Ma_lim = min(Ma, 0.8)
    PGSF = math.sqrt(1 - Ma_lim ** 2) # Prandl-Glauert scaling factor
    
    ang_mi = math.atan(PGSF * math.tan(ang_m))
    ang_ini = ang_mi - math.atan(math.tan(ang_m - ang_in) / PGSF)
    ang_insi = ang_mi - math.atan(math.tan(ang_m - ang_ins) / PGSF)
    ang_outi = ang_mi + math.atan(math.tan(ang_out - ang_m) / PGSF)
    
    t2si = t2s * math.sqrt((math.cos(ang_m)) ** 2 + PGSF ** 2 * (math.sin(ang_m)) ** 2)
    t2si_lim = min(t2si, 1.75)
    d2si = d2s / PGSF
    
    if t2s >= 0.6:
        ai = 0.0037 * math.sin(ang_mi) + 0.9864
        bi = 3.5497 * (math.sin(ang_mi)) ** (-0.3792)
        ci = -1.1038 * (math.sin(ang_mi)) ** 2 + 1.801 * math.sin(ang_mi) + 0.9864
        di = 0.5449 * math.sin(ang_mi) + 0.1611
        
        A = di + (ai - di) / (1 + (t2si / ci) ** bi)
    else:
        A = (1 - 0.98264403) / 0.6 * t2si + 1
    
    inci = ang_insi - ang_ini
    ang_outsi = ang_outi + (1 - A) * inci
    
    mue0 = 0.4867675 + (-0.0019722 - 0.4867675) / (1 + (t2si / 2.017826) ** (4.965654)) + (-0.4260008 * t2si + 1)
    
    a1 = -0.66699 * t2si_lim ** 5 + 2.72709 * t2si_lim ** 4 - 3.57363 * t2si_lim ** 3 + 1.75986 * t2si_lim ** 2 - 0.5769 * t2si_lim
    b1 = 1.07109 * t2si_lim ** 5 - 4.35528 * t2si_lim ** 4 + 5.61798 * t2si_lim ** 3 - 2.71971 * t2si_lim ** 2 + 1.16433 * t2si_lim
    c1 = -0.42012 * t2si_lim ** 5 + 1.69992 * t2si_lim ** 4 - 2.15442 * t2si_lim ** 3 + 1.03032 * t2si_lim ** 2 - 0.60624 * t2si_lim + 0.0019722
    
    dmue = a1 * (math.sin(ang_mi)) ** 2 + b1 * math.sin(ang_mi) + c1
          
    mue = max(mue0 + dmue, 0.1)
    
    de_al_1 = (1 - mue) / (2 * mue) * (ang_outsi - ang_insi)
    
    de_al_2 = 5 * (-5.243 * (math.sin(abs(ang_mi - math.pi / 4))) ** 2 - 1.4408 * math.sin(abs(ang_mi - math.pi / 4)) + 4) * d2si / t2si ** 2
    de_al_2 = de_al_2 / 180.0 * math.pi
    
    ang_bld_outi = ang_outsi + de_al_1 + de_al_2
    
    ang_bld_out = ang_m + math.atan(PGSF * math.tan(ang_bld_outi - ang_mi))
    ang_bld_out = ang_bld_out / math.pi * 180
    
    if rot > 0:
        ang_bld_out = 180 - ang_bld_out
    
    if Ma_out > 0.8:
        Ma_lim = min(Ma_out, 1)
        ang_bld_out = angle_out + (ang_bld_out - angle_out) / 0.2 * (1 - Ma_lim)
    
    return ang_bld_out

# diffusion  
def diffusion(angle_in, angle_out, vel_in, vel_out, solidity):

    # Convert angles to radians
    ang_in = angle_in / 180.0 * Pi
    ang_out = angle_out / 180.0 * Pi
    
    # Calculate parameters
    s2t = solidity
    vel_m = (vel_out + vel_in) / 2.0
    dc_u = abs((vel_out * math.cos(ang_out)) - (vel_in * math.cos(ang_in)))
    
    # Calculate diffusion factor
    diffusion = 1 - vel_out / vel_in + vel_m / (4.0 * s2t * vel_in) * 2 * dc_u / vel_m
    
    return diffusion
