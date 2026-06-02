# Author: Marco Wiens
# Version: 11.12.2024
# 0-D Thermo Calculation
# Programm for calculation of thermodynamics in axial compressor stages

import math
import tkinter as tk
import os
import sys
import debug_log

from tkinter import ttk
from pathlib import Path

wdpath = os.getcwd()
   
#print(wdpath)

scriptpath = os.path.dirname(sys.argv[0])

current_dir = Path(__file__).parent.parent
static_folder = current_dir/ "static"

#print(scriptpath)
os.chdir(scriptpath)

def read_initial_values(filename):
    global p_t_in, T_t_in, mflow, R, cp, TPR
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('p_t_in = '):
                p_t_in = float(line[9:])
            elif line.startswith('T_t_in = '):
                T_t_in = float(line[9:])
            elif line.startswith('mflow = '):
                mflow = float(line[8:])
            elif line.startswith('R = '):
                R = float(line[4:])
            elif line.startswith('cp = '):
                cp = float(line[5:])
            elif line.startswith('TPR = '):
                TPR = float(line[6:])
                


def create_gui():
    global entries

    read_initial_values(static_folder / 'Thermo_Initial_Values.txt')

    root = tk.Tk()
    root.title("Thermodynamic Initial Values")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    entries = {}

    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Thermodynamic Parameters")

    params = ['p_t_in', 'T_t_in', 'mflow', 'R', 'cp', 'TPR']
    gui_names = ['p_t_in [Pa]', 'T_t_in [K]', 'mflow [kg/s]', 'R [J/kg*K]', 'cp [J/kg*K]', 'TPR [-]']
    path = os.getcwd()
    debug_log.debug(f"cwd={path}", context="thermodynamic_calculation")
    for i, param in enumerate(params):
        ttk.Label(frame, text=f"{gui_names[i]}:").grid(row=i, column=0, padx=5, pady=5, sticky='w')
        entries[param] = []
        entry = ttk.Entry(frame, width=15)
        entry.insert(0, str(globals()[param]))
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[param].append(entry)

    def save_and_initialize():
        try:
            for var_name in entries.keys():
                globals()[var_name] = float(entries[var_name][0].get())
            
            with open(static_folder / 'Thermo_Initial_Values.txt', 'w') as file:
                file.write(f"p_t_in = {p_t_in}\n")
                file.write(f"T_t_in = {T_t_in}\n")
                file.write(f"mflow = {mflow}\n")
                file.write(f"R = {R}\n")
                file.write(f"cp = {cp}\n")
                file.write(f"TPR = {TPR}\n")

            thermo_msg = "Parameters saved and initialized."
            print(thermo_msg)
            debug_log.debug(thermo_msg, context="thermodynamic_calculation")
        except ValueError:
            thermo_err = "Please enter valid numbers for all conditions."
            print(thermo_err)
            debug_log.debug(thermo_err, context="thermodynamic_calculation")

    ttk.Button(root, text="Save and Initialize Parameters", command=save_and_initialize).pack(pady=10)

    root.mainloop()
    
def Thermo(p_t_in, T_t_in, mflow, R, cp, TPR, i_st):
    #global p_t_in, T_t_in, mflow, R, cp, TPR

    
    #read_initial_values(static_folder / 'Thermo_Initial_Values.txt')


    # Optimization: Pre-calculate frequently used values
    kappa = cp / (cp - R)
    roh_t = p_t_in / (T_t_in * R)

    # Rest of your existing Thermo function remains the same
    eta_p = 0.88
    TTR = TPR**(R/(cp*eta_p))
    T_t_a = TTR*T_t_in
    delta_h_t = cp*(T_t_a-T_t_in)
    u_m_approx = 332.0
    psi_h_t_st = 1.0
    
    u_m = math.sqrt(2*delta_h_t/(i_st*psi_h_t_st))

    P = mflow*delta_h_t

    # Compressor propasal inlet 
    Ma_ax_in = 0.6
    v_in = 0.37027027
    u_m_in = u_m

    T_in = T_t_in/(1 + (kappa-1)/2*Ma_ax_in**2)
    roh_in = roh_t/(1 + (kappa-1)/2*Ma_ax_in**2)**(1/(kappa-1))
    p_in = p_t_in*(T_in/T_t_in)**(kappa/(kappa-1)) 

    c_ax_in = Ma_ax_in*math.sqrt(kappa*R*T_in)

    A_in = mflow/(roh_in*c_ax_in)
    D_S_in = 2*math.sqrt(A_in/(math.pi*(1-v_in**2)))
    D_H_in = D_S_in*v_in
    D_m_in = (D_S_in+D_H_in)/2

    u_S_in = u_m_in*D_S_in/D_m_in
    u_H_in = u_m_in*D_H_in/D_m_in

    n_in = u_m_in/(math.pi*D_m_in)*60

    # Compressor propasal outlet
    p_t_out = p_t_in * TPR
    T_t_out = T_t_in *TTR
    roh_t_out = p_t_out/(T_t_out*R)

    c_ax_out = c_ax_in
    T_out = T_t_out-c_ax_out**2/(2*cp)
    Ma_ax_out = c_ax_out/math.sqrt(kappa*R*T_out)

    roh_out = roh_t_out/(1 + (kappa-1)/2*Ma_ax_out**2)**(1/(kappa-1))
    p_out =  p_t_out*(T_out/T_t_out)**(kappa/(kappa-1))

    A_out = mflow/(roh_out*c_ax_out)
    D_m_out = D_m_in
    D_S_out = D_m_out+0.5*A_out/(2*math.pi*D_m_out)
    D_H_out = D_m_out-0.5*A_out/(2*math.pi*D_m_out)
    v_out = D_H_out/D_S_out 

    u_m_out = math.pi*D_m_out*n_in/60
    u_S_out = u_S_in*D_S_out/D_m_out
    u_H_out = u_m_out*D_H_out/D_m_out

    delta_h_t = [delta_h_t/i_st]*i_st

    n = [n_in]*i_st
    D_m = [D_m_in]*i_st

    u_m, psi_h = [], []
    for i in range(i_st):
        u_m.append(D_m[i]*n[i]*math.pi/60)
        psi_h.append(2*delta_h_t[i]/(u_m[i]**2))

    T_t_out = [] 
    for i in range(i_st):
        if i == 0:
            T_t_out.append(T_t_in + delta_h_t[i] / cp)
        else:
            T_t_out.append(T_t_out[i - 1] + delta_h_t[i] / cp)

    TTR = []
    for i in range(i_st):
        if i == 0:
            TTR.append(T_t_out[i]/T_t_in)
        else:   
            TTR.append(T_t_out[i]/T_t_out[i-1])

    eta_p = [eta_p]*i_st

    TPR_stage = []
    for i in range(i_st):
        TPR_stage.append(TTR[i]**(eta_p[i]*cp/R))

    p_t_out = []
    for i in range(i_st):
        if i == 0:
            p_t_out.append(p_t_in*TPR_stage[i])
        else:
            p_t_out.append(p_t_out[i-1]*TPR_stage[i])

    eta_s = []
    for i in range(i_st):
        eta_s.append((TPR_stage[i]**((kappa-1)/kappa)-1)/(TTR[i]-1))

    c_ax = [c_ax_in]*i_st

    h_R = [(D_S_in-D_H_in)/2*1000]
    T_out, p_out, roh_out, phi, A_out, D_S_out, D_H_out, u_S_out, u_H_out = [], [], [], [], [], [], [], [], []
    for i in range(i_st):
        T_out.append(T_t_out[i] - c_ax[i]**2/(2*cp))
        p_out.append(p_t_out[i]*(T_out[i] / T_t_out[i])**(kappa/(kappa-1)))
        roh_out.append(p_out[i] / (T_out[i]*R))    
        phi.append(c_ax[i] / u_m[i])
        A_out.append(mflow/(roh_out[i]*c_ax[i]))
        D_S_out.append(D_m[i]+A_out[i] / (math.pi*D_m[i]))
        D_H_out.append(D_m[i]-A_out[i] / (math.pi*D_m[i]))
        u_S_out.append(u_m[i]*D_S_out[i]/D_m[i])
        u_H_out.append(u_m[i]*D_H_out[i]/D_m[i])
        h_R.append((D_S_out[i]-D_H_out[i])/2*1000)

    h_S = [((D_S_in-D_H_in)+(D_S_out[0]-D_H_out[0]))/4*1000]
    for i in range(i_st-1):
        h_S.append(((D_S_out[i]-D_H_out[i])+(D_S_out[i+1]-D_H_out[i+1]))/4*1000)
    
    
    '''
    Save results in a dict for gui
    '''
    result = {
        'mflow': mflow,
        'p_t_in': p_t_in,
        'T_t_in': T_t_in,
        'kappa': kappa,
        'R': R,
        'cp': cp,
        'h_R': h_R,
        'h_S': h_S,
        'i_st': i_st,
        'TPR': TPR
    }
    
    
    return result

#if __name__ == "__main__":
    #results = Thermo(GUI_On = 1)