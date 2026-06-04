# Author: Marco Wiens
# Modified by: Jonas Scholz
# Version: 01.10.2025
# Stage
# Programm for calculation of blade geometry and creating the data for MULTALL

import math 
import numpy as np
import matplotlib.pyplot as plt
import csv
import os 
import sys
import shutil 
from matplotlib.widgets import Slider
import tkinter as tk
from tkinter import filedialog
import json
import debug_log


import tkinter.messagebox as messagebox
import tkinter as tk
from tkinter import ttk, filedialog, Label, Toplevel

from cubic_spline import cubspline
from meanline import meanline 
from Radial_equilibrium import radial_equilibrium_R, radial_equilibrium_S
from Bezier_curve import bezier
from Interpolation import intpol, intp_new
from channel import channel

wdpath = os.getcwd()
   
#print(wdpath)

scriptpath = os.path.dirname(sys.argv[0])

#print(scriptpath)
os.chdir(scriptpath)

''' Here needs to be a fix radial equilibirium needs to be called for all stages
# parameter for radial equilibrium
stage = 1
approach = 1
constant_r_parameter = 1
'''
stage = 1
approach = 1
constant_r_parameter = 1

ACTIVE_JSON_PATH = None 
h_H = [0.0, 0.2, 0.5, 0.8, 1.0]
LE_shift = 0.025
Pi = math.pi


#Radial distribution of Temperature:
def plot_temp_alpha_beta(T_Plot, beta_R_Plot, alpha_S_Plot):
    #Temp plot
    if T_Plot == 1:
        plt.plot(T_S_out, h_rel, label = "T_out'")
        plt.plot(T_R_in, h_rel, label = 'T_in"')
        plt.plot(T_R_out, h_rel, label = "T_out'' = T_in'")
        plt.legend()
        plt.show()
        
    #Beta plot
    if beta_R_Plot == 1:
        plt.plot(beta_blade_R_in, h_rel, label = "beta_blade_R_in'")
        plt.plot(beta_blade_R_out, h_rel, label = "beta_blade_R_out'")
        plt.plot(beta_R_in, h_rel, label = "beta_R_in'")
        plt.plot(beta_R_out, h_rel, label = "beta_R_out''")
        plt.legend()
        plt.show()

    # Alpha plot
    if alpha_S_Plot == 1:
        plt.plot(alpha_S_in, h_rel, label = "alpha_S_in'")
        plt.plot(alpha_S_out, h_rel, label = "alpha_S_out'")
        plt.plot(beta_blade_S_in, h_rel, label = "beta_blade_S_in''")
        plt.plot(beta_blade_S_out, h_rel, label = "beta_blade_S_out''")
        plt.legend()
        plt.show()



#function for writing Bézier-points
'''
def create_default_profiles(self, json_path):  
    gen_msg = "Generating default profiles..."
    print(gen_msg)
    debug_log.debug(gen_msg, context="Stage")
    if not hasattr(self, 'meanline_data') or self.meanline_data is None:
        messagebox.showwarning(
            "Fehlende Daten", 
            "Bitte berechne und speichere zuerst die '1D-Settings' (Meanline), bevor du die Standard-Profile erstellst!"
        )
        return

    
    # Debugging screen 
    
       
    try:
        try:
            #print(f"[DEBUG] Calling run_main_logic...")
            #print(f"[DEBUG] self.meanline_data type: {type(self.meanline_data)}")
            #print(f"[DEBUG] self.meanline_data value: {self.meanline_data}")
            #print(f"[DEBUG] hasattr meanline_data: {hasattr(self, 'meanline_data')}")
            run_main_logic({'main_choice': 'default'}, self, json_path)
        except Exception as e:
            import traceback
            #print(f"[DEBUG] Error executing run_main_logic: {e}")
            #print(f"[DEBUG] Full traceback:")
            traceback.print_exc()  # ← This shows you EXACTLY which line crashed
            messagebox.showerror("Error", "Please calculate the Meanline (1D Settings) first and make sure it's saved!")
            return 
            
    try:
        try:
            run_main_logic({'main_choice': 'default'}, self, json_path)
        except Exception as e:
            err_msg = f"Error executing run_main_logic: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="create_default_profiles")
            messagebox.showerror("Error", "Please calculate the Meanline (1D Settings) first and make sure it's saved!")
            return

        global h_rel, l_R, l_S, beta_blade_R_in, beta_blade_R_out, alpha_S_in, alpha_S_out
        
        num_stages = len(radial_data_R)
        h_H_ref = [0.0, 0.2, 0.5, 0.8, 1.0]

        chord_length_R = np.interp(h_H, h_rel, l_R)
        chord_length_S = np.interp(h_H, h_rel, l_S)

        sort_idx = np.argsort(h_rel)
        h_rel_sorted = np.array(h_rel)[sort_idx]
        l_R_sorted = np.array(l_R)[sort_idx]
        l_S_sorted = np.array(l_S)[sort_idx]
        
        def generate_dict(row):
            
    
            beta_S_BP_1, beta_S_BP_2, beta_S_BP_3, beta_S_BP_4 = [],[],[],[]
            alpha_S_BP_1, alpha_S_BP_2, alpha_S_BP_3, alpha_S_BP_4 = [],[],[],[]
            
            c_03 = 0.277558
            c_07 = 0.165432
            h_H = [0, 0.2, 0.5, 0.8, 1.0]
            
            for i in range(len(h_H)):
                for j in range(len(h_rel)):
                    if row % 2 != 0:
                        if h_rel[j] == h_H[i]:
                                beta_1 = beta_blade_R_in[j]
                                beta_2 = beta_blade_R_out[j]
                                
                                # delta_beta_1 = beta_2 - bez
            
                                # c_03 = delta_beta_1/delta_beta_0
                                # c_07 = delta_beta_2/delta_beta_0
                                
                                delta_beta_0 = beta_2 - beta_1
                                
                                beta_neu_03 = beta_2 - delta_beta_0 * c_03
                                beta_neu_07 = beta_2 - delta_beta_0 * c_07
                                
                                beta_S_BP_1.append(round(beta_blade_R_in[j], 2))
                                beta_S_BP_4.append(round(beta_blade_R_out[j], 2))
                                beta_S_BP_2.append(round(beta_neu_03, 2))
                                beta_S_BP_3.append(round(beta_neu_07, 2))

                                #print(angle_in[j], beta_neu_03, beta_neu_07,angle_out[j],delta_beta_0,c_03,c_07)
                                
                                # beta_S_BP_1.append(round(angle_in[j], 2))
                                # beta_S_BP_4.append(round(angle_out[j], 2))
                                # beta_S_BP_2.append(round((beta_S_BP_4[i]-beta_S_BP_1[i])/3+beta_S_BP_1[i], 2))
                                # beta_S_BP_3.append(round(2*(beta_S_BP_4[i]-beta_S_BP_1[i])/3+beta_S_BP_1[i], 2))
                    elif row % 2 == 0:
                        if h_rel[j] == h_H[i]:
                            
                                alpha_1 = alpha_S_in[j]
                                alpha_2 = alpha_S_out[j]
                                
                                delta_alpha_0 = alpha_2 - alpha_1
                                
                                alpha_neu_03 = alpha_2 - delta_alpha_0 * c_03
                                alpha_neu_07 = alpha_2 - delta_alpha_0 * c_07
                                
                                alpha_S_BP_1.append(round(alpha_S_in[j], 2))
                                alpha_S_BP_4.append(round(alpha_S_out[j], 2))
                                alpha_S_BP_2.append(round(alpha_neu_03, 2))
                                alpha_S_BP_3.append(round(alpha_neu_07, 2))

            if row % 2 != 0 :
                rel_thickness = np.array([[0.023,0.020,0.015,0.011,0.007],
                                            [0.082,0.071,0.055,0.038,0.027],
                                            [0.017,0.015,0.011,0.008,0.005],
                                            [0.010,0.009,0.007,0.005,0.003]])
                abs_thickness = rel_thickness * chord_length_R[2]
                angles = beta_S_BP_1 + beta_S_BP_2 + beta_S_BP_3 + beta_S_BP_4
                angle_key = "beta_S"
            else:
                rel_thickness = np.array([[0.015,0.015,0.015,0.015,0.015],
                                            [0.058,0.058,0.058,0.058,0.058],
                                            [0.011,0.011,0.011,0.011,0.011],
                                            [0.006,0.006,0.006,0.006,0.006]])
                abs_thickness = rel_thickness * chord_length_S[2]
                angles = alpha_S_BP_1 + alpha_S_BP_2 + alpha_S_BP_3 + alpha_S_BP_4
                angle_key = "alpha_S"

            thickness_combined = [round(float(val), 3) for row_vals in abs_thickness for val in row_vals]

            return {
                "h/H": list(h_H),
                angle_key: angles,
                "d/l": thickness_combined,
                "m*": [0.0]*5 + [0.3]*5 + [0.7]*5 + [1.0]*5
            }
            
            
        rotor_dict = generate_dict(1)
        stator_dict = generate_dict(2)

        with open(json_path, 'r') as f:
            data = json.load(f)

        if "Bezier_point_data" not in data:
            data["Bezier_point_data"] = {}
            
        data["Bezier_point_data"]["rotor"] = rotor_dict
        data["Bezier_point_data"]["stator"] = stator_dict

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

        if hasattr(self, "prepop_bezier_point_rotor"):
            self.prepop_bezier_point_rotor = rotor_dict
            self.prepop_bezier_point_stator = stator_dict

        print("Default profiles successfully generated and saved to JSON!")
        messagebox.showinfo("Success", "Default profiles successfully created and saved to JSON!")

    except NameError as e:
        print(f"Variable Error: {e}")
        messagebox.showerror("Error", "Please calculate the Meanline (1D Settings) first! (Debug: #2)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
'''

def _gui_messagebox(show_func, title, message):
    try:
        if tk._default_root is not None:
            show_func(title, message)
    except Exception:
        pass

def create_default_profiles(self, json_path): 
    gen_msg = "Generating default profiles..."
    print(gen_msg)
    debug_log.debug(gen_msg, context="Stage")
 
    try:
        try:
            run_main_logic({'main_choice': 'default'}, self, json_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            _gui_messagebox(messagebox.showerror,
                "Error",
                "Please calculate the Meanline (1D Settings) first and make sure it's saved!"
            )
            return
 
        # h_H is the standard spanwise sample positions
        h_H = [0.0, 0.2, 0.5, 0.8, 1.0]
        c_03 = 0.277558
        c_07 = 0.165432
 
        # We will build a dict of all stage bezier data to write once
        all_bezier_data = {}
 
        for stage_num in range(1, self.stages_to_calc + 1):
            # ---- pull per-stage radial-equilibrium results ----
            rad_R = radial_data_R[stage_num]   # dict stored by run_main_logic
            rad_S = radial_data_S[stage_num]
 
            h_rel_s          = rad_R['h_rel']
            l_R_s            = rad_R['l_R']
            l_S_s            = rad_S['l_S']
            beta_blade_R_in  = rad_R['beta_blade_R_in']
            beta_blade_R_out = rad_R['beta_blade_R_out']
            alpha_S_in       = rad_S['alpha_S_in']
            alpha_S_out      = rad_S['alpha_S_out']

            debug_log.debug(f"  create_default [stage={stage_num}] h_rel_s={[round(v,2) for v in h_rel_s]}", context="create_default")
            debug_log.debug(f"  create_default [stage={stage_num}] beta_blade_R_in={[round(v,2) for v in beta_blade_R_in]}", context="create_default")
            debug_log.debug(f"  create_default [stage={stage_num}] beta_blade_R_out={[round(v,2) for v in beta_blade_R_out]}", context="create_default")
            debug_log.debug(f"  create_default [stage={stage_num}] alpha_S_in={[round(v,2) for v in alpha_S_in]}", context="create_default")
            debug_log.debug(f"  create_default [stage={stage_num}] alpha_S_out={[round(v,2) for v in alpha_S_out]}", context="create_default")
 
            # Chord lengths interpolated to the five standard h_H positions
            chord_length_R = np.interp(h_H, h_rel_s, l_R_s)
            chord_length_S = np.interp(h_H, h_rel_s, l_S_s)
 
            def generate_dict_for_stage(is_rotor):
                """Build the bezier-point dict for one row of this stage."""
                beta_S_BP_1, beta_S_BP_2, beta_S_BP_3, beta_S_BP_4 = [], [], [], []
                alpha_S_BP_1, alpha_S_BP_2, alpha_S_BP_3, alpha_S_BP_4 = [], [], [], []

                if is_rotor:
                    # --- PASS 1: collect raw LE/TE angles for all 5 span positions ---
                    raw_b1_list = []
                    raw_b2_list = []
                    for i, h_val in enumerate(h_H):
                        for j in range(len(h_rel_s)):
                            if abs(h_rel_s[j] - h_val) < 1e-6:
                                raw_b1_list.append(beta_blade_R_in[j])
                                raw_b2_list.append(beta_blade_R_out[j])
                                break

                    # --- Global reflection decision ---
                    # If ALL 5 LE values are > 90°, the rotor uses the >90° convention.
                    # Reflect ALL TE values < 90° to > 90° so the Bezier curve stays
                    # on one side of 90° and 1/tan(beta) doesn't change sign.
                    le_all_above_90 = all(b1 > 90.0 for b1 in raw_b1_list)

                    # --- PASS 2: apply reflection and build control points ---
                    for i, h_val in enumerate(h_H):
                        for j in range(len(h_rel_s)):
                            if abs(h_rel_s[j] - h_val) < 1e-6:
                                b1 = raw_b1_list[i]
                                b2 = raw_b2_list[i]
                                reflected = False
                                if le_all_above_90 and b2 < 90.0:
                                    b2 = 180.0 - b2
                                    reflected = True
                                delta = b2 - b1
                                beta_S_BP_1.append(round(b1, 2))
                                beta_S_BP_4.append(round(b2, 2))
                                beta_S_BP_2.append(round(b2 - delta * c_03, 2))
                                beta_S_BP_3.append(round(b2 - delta * c_07, 2))
                                debug_log.debug(f"  create_default [stage={stage_num}, ROTOR, h={h_val:.1f}]: b1(pre)={raw_b1_list[i]:.2f}, b2(pre)={raw_b2_list[i]:.2f} → b1={b1:.2f}, b2={b2:.2f} reflected={reflected} delta={delta:.2f} le_all_above_90={le_all_above_90}", context="create_default")
                                break

                else:
                    for i, h_val in enumerate(h_H):
                        for j in range(len(h_rel_s)):
                            if abs(h_rel_s[j] - h_val) < 1e-6:
                                a1_orig = alpha_S_in[j]
                                a2_orig = alpha_S_out[j]
                                a1 = a1_orig
                                a2 = a2_orig
                                reflected = False
                                if a2 > 90.0:
                                    a2 = 180.0 - a2
                                    reflected = True
                                debug_log.debug(f"  create_default [stage={stage_num}, STATOR, h={h_val:.1f}]: a1(pre)={a1_orig:.2f}, a2(pre)={a2_orig:.2f} → a1={a1:.2f}, a2={a2:.2f} reflected={reflected} delta={a2-a1:.2f}", context="create_default")
                                delta = a2 - a1
                                alpha_S_BP_1.append(round(a1, 2))
                                alpha_S_BP_4.append(round(a2, 2))
                                alpha_S_BP_2.append(round(a2 - delta * c_03, 2))
                                alpha_S_BP_3.append(round(a2 - delta * c_07, 2))
                                break
 
                if is_rotor:
                    ref_chord = chord_length_R[2]   # 50% span chord
                    rel_thickness = np.array([
                        [0.023, 0.020, 0.015, 0.011, 0.007],
                        [0.082, 0.071, 0.055, 0.038, 0.027],
                        [0.017, 0.015, 0.011, 0.008, 0.005],
                        [0.010, 0.009, 0.007, 0.005, 0.003],
                    ])
                    abs_thickness = rel_thickness * ref_chord
                    # ---- Spanwise smoothing of rotor angles ----
                    # The per-section reflection can create spanwise discontinuities
                    # when beta_blade_R_out crosses 90° at some spans but not others.
                    # Apply light 3-point moving average to TE-side CPs to smooth them.
                    for cp_list in [beta_S_BP_2, beta_S_BP_3, beta_S_BP_4]:
                        orig = list(cp_list)
                        smoothed = list(cp_list)
                        for i in range(1, 4):
                            smoothed[i] = round((orig[i-1] + orig[i] + orig[i+1]) / 3.0, 2)
                        debug_log.debug(f"  create_default [stage={stage_num}, ROTOR] spanwise smoothing: {orig} → {smoothed}", context="create_default")
                        cp_list[:] = smoothed
                    angles = beta_S_BP_1 + beta_S_BP_2 + beta_S_BP_3 + beta_S_BP_4
                    angle_key = "beta_S"
                    debug_log.debug(f"  create_default [stage={stage_num}, ROTOR]: final angles={[round(v,2) for v in angles]}", context="create_default")
                else:
                    ref_chord = chord_length_S[2]
                    rel_thickness = np.array([
                        [0.015, 0.015, 0.015, 0.015, 0.015],
                        [0.058, 0.058, 0.058, 0.058, 0.058],
                        [0.011, 0.011, 0.011, 0.011, 0.011],
                        [0.006, 0.006, 0.006, 0.006, 0.006],
                    ])
                    abs_thickness = rel_thickness * ref_chord
                    angles = alpha_S_BP_1 + alpha_S_BP_2 + alpha_S_BP_3 + alpha_S_BP_4
                    angle_key = "alpha_S"
                    debug_log.debug(f"  create_default [stage={stage_num}, STATOR]: angles={[round(v,2) for v in angles]}", context="create_default")

                thickness_combined = [
                    round(float(v), 3)
                    for row_vals in abs_thickness
                    for v in row_vals
                ]

                return {
                    "h/H":   list(h_H),
                    angle_key: angles,
                    "d/l":   thickness_combined,
                    "m*":    [0.0]*5 + [0.3]*5 + [0.7]*5 + [1.0]*5,
                }

            rotor_dict  = generate_dict_for_stage(is_rotor=True)
            stator_dict = generate_dict_for_stage(is_rotor=False)

            # Keys: rotor_stage_1, stator_stage_1, rotor_stage_2, …
            all_bezier_data[f"rotor_stage_{stage_num}"]  = rotor_dict
            all_bezier_data[f"stator_stage_{stage_num}"] = stator_dict

            bp_msg = f"Stage {stage_num}: rotor/stator bezier points generated."
            print(bp_msg)
            debug_log.debug(bp_msg, context="create_default_profiles")

        # ---- write everything to JSON in one pass ----
        with open(json_path, 'r') as f:
            data = json.load(f)

        data["Bezier_point_data"] = all_bezier_data

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

        # Update in-memory cache on the GUI object
        if hasattr(self, "prepop_bezier_point_rotor"):
            self.prepop_bezier_point_rotor = all_bezier_data.get("rotor_stage_1", {})
            self.prepop_bezier_point_stator = all_bezier_data.get("stator_stage_1", {})

        profile_msg = f"Default profiles for {self.stages_to_calc} stage(s) saved to JSON."
        print(profile_msg)
        debug_log.debug(profile_msg, context="create_default_profiles")
        _gui_messagebox(messagebox.showinfo,
            "Success",
            f"Default profiles for {self.stages_to_calc} stage(s) successfully created and saved to JSON!"
        )

    except NameError as e:
        var_err = f"Variable Error: {e}"
        print(var_err)
        debug_log.debug(var_err, context="create_default_profiles")
        _gui_messagebox(messagebox.showerror, "Error", "Please calculate the Meanline (1D Settings) first! (Debug: #2)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        _gui_messagebox(messagebox.showerror, "Error", f"An unexpected error occurred: {e}")

def save_profile(source_filename):
        if not os.path.exists(source_filename):
            return
        
        root_dialog = tk.Tk()
        root_dialog.withdraw()
        
        filepath = filedialog.asksaveasfilename(
            parent=root_dialog,
            title=f"Save Profile '{source_filename} as",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"),("All files", "*.*"))
        )
        
        root_dialog.destroy()
        
        if not filepath:
            return
        
        try:
            shutil.copy(source_filename, filepath)
            save_msg = f"Profile successfully saved to {filepath}"
            print(save_msg)
            debug_log.debug(save_msg, context="save_profile")
        except Exception as e:
            err_msg = f"Error saving profile: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="save_profile")                                                        

channel_data = {}
# Move the declarations to module level
radial_data_R = {}   
radial_data_S = {}

def init_channel_data(compressor_gui_data):
    """
    Compute channel geometry for every stage and store it in the global
    channel_data dict.  Each stage after the first is shifted by a
    cumulative axial offset so that all coordinates live in one global
    reference frame instead of each stage starting at x = 0.
    """
    global channel_data
    channel_data = {}
    cumulative_x_offset = 0.0          # global axial position of stage-1 inlet

    for s in range(1, compressor_gui_data.stages_to_calc + 1):
        compressor_gui_data.stage = s
        x_values_s, r_values_s, m_prime_values_s, x0_s, r0_N_s, r0_G_s = channel(compressor_gui_data)

        # channel() returns x0 as numpy array; convert to list
        x0_s = list(x0_s)

        # ── shift every x-coordinate into the global frame ──────────────
        if cumulative_x_offset != 0.0:
            # x0: the 9 spline control points
            x0_s = [x + cumulative_x_offset for x in x0_s]
            # x_values and m_prime_values: one list per span height (h_H)
            for k in range(len(x_values_s)):
                x_values_s[k]      = [v + cumulative_x_offset for v in x_values_s[k]]
                m_prime_values_s[k] = [v + cumulative_x_offset for v in m_prime_values_s[k]]
            # r_values are radii – they are NOT shifted

        channel_data[s] = {
            'x_values':       x_values_s,
            'r_values':       r_values_s,
            'm_prime_values': m_prime_values_s,
            'x0':             x0_s,
            'r0_N_mm':        r0_N_s,
            'r0_G_mm':        r0_G_s,
        }

        # Stage s+1's local x0[1]=0 (rotor inlet) must land at the current
        # stage's stator outlet x0[7] in the global frame.
        cumulative_x_offset = x0_s[7]

        debug_log.debug(f"Stage {s}: channel stored. "
                         f"x0[0]={x0_s[0]:.1f} x0[7]={x0_s[7]:.1f} mm  "
                         f"→ next offset = {cumulative_x_offset:.1f} mm",
                         context="init_channel_data")
        # Verify x0 monotonicity (BUGFIX v2: all x0 values in local frame → monotonic)
        x0_all = [round(v, 1) for v in x0_s]
        x0_ok = all(x0_all[i] <= x0_all[i+1] for i in range(len(x0_all)-1))
        debug_log.debug(f"Stage {s}: x0_values = {x0_all}  monotonic={x0_ok}",
                         context="init_channel_data")

    # ── Global annulus spline (Option B) ──────────────────────────────────────
    # Build a single continuous hub/shroud annulus across all stages by
    # concatenating per-stage control points (x0[1..7], excluding duct points
    # x0[0] and x0[8]) and constructing global splines.  Each stage's r_values
    # are then re-sampled from the global spline, eliminating the radial
    # discontinuity at inter-stage interfaces that caused ~18000 negative volumes.
    # See Docs/Negative_Volume_Debug_Log.md for details.
    # m_prime_values are kept from the per-stage computation (the arc-length
    # correction from the radial adjustment is O(dr²) and negligible).

    # Log interface radii before correction
    for s in range(1, compressor_gui_data.stages_to_calc):
        hub_s   = channel_data[s]['r0_N_mm']
        hub_n   = channel_data[s + 1]['r0_N_mm']
        shrd_s  = channel_data[s]['r0_G_mm']
        shrd_n  = channel_data[s + 1]['r0_G_mm']
        x0_s    = channel_data[s]['x0']
        x0_n    = channel_data[s + 1]['x0']
        debug_log.debug(
            f"INTERFACE Stage {s}→{s+1} BEFORE: "
            f"hub={hub_s[7]:.1f}→{hub_n[1]:.1f} mm "
            f"(Δ={hub_n[1]-hub_s[7]:+.1f}), "
            f"shroud={shrd_s[7]:.1f}→{shrd_n[1]:.1f} mm "
            f"(Δ={shrd_n[1]-shrd_s[7]:+.1f}), "
            f"x={x0_s[7]:.1f}/{x0_n[1]:.1f} mm",
            context="global_annulus")

    # ── 1. Build global control-point arrays ──────────────────────────────
    num_stages = compressor_gui_data.stages_to_calc
    x_hub_all, r_hub_all = [], []
    x_shroud_all, r_shroud_all = [], []

    h_H = [0.0, 0.2, 0.5, 0.8, 1.0]

    for s in range(1, num_stages + 1):
        x0_g = channel_data[s]['x0']        # 9 control points, global x [mm]
        rN   = channel_data[s]['r0_N_mm']   # hub control points [mm]
        rG   = channel_data[s]['r0_G_mm']   # shroud control points [mm]

        # Stage 1: include x0[0..7] (include inlet duct point x0[0]
        #           so cubspline doesn't extrapolate for x < 0).
        # Stage 2+: include x0[2..7]  (skip x0[1] which duplicates prev x0[7]).
        # Last stage: also include x0[8] (outlet duct point) to avoid
        #             extrapolation for x > x0[7].
        if s == 1:
            start = 0
        elif s == 2:
            start = 2
        else:
            start = 2  # same for all intermediate stages

        if s == num_stages:
            end = 8
        else:
            end = 7

        for i in range(start, end + 1):
            x_hub_all.append(x0_g[i])
            r_hub_all.append(rN[i])
            x_shroud_all.append(x0_g[i])
            r_shroud_all.append(rG[i])

    debug_log.debug(
        f"Global annulus: {len(x_hub_all)} hub control points, "
        f"x range [{x_hub_all[0]:.1f}, {x_hub_all[-1]:.1f}] mm",
        context="global_annulus")

    # ── 2. Re-sample each stage from the global spline ────────────────────
    for s in range(1, num_stages + 1):
        x_stage = channel_data[s]['x_values'][0]  # hub x-coords, ~130 pts [mm]
        old_rN = channel_data[s]['r_values'][0]   # old hub radii [mm]
        old_rG = channel_data[s]['r_values'][4]   # old shroud radii [mm]

        # Re-sample hub and shroud via cubspline (Method 3)
        r_N_new = [cubspline(3, x, x_hub_all, r_hub_all) for x in x_stage]
        r_G_new = [cubspline(3, x, x_shroud_all, r_shroud_all) for x in x_stage]

        # Re-compute r_values for all 5 span heights
        r_values_new = []
        for k, element in enumerate(h_H):
            r_span = [r_N_new[i] + element * (r_G_new[i] - r_N_new[i])
                      for i in range(len(x_stage))]
            r_values_new.append(r_span)

        channel_data[s]['r_values'] = r_values_new

    # Log interface radii after correction (compare at same x-position)
    for s in range(1, num_stages):
        x_interface = channel_data[s]['x0'][7]  # same as next stage's x0[1]
        x_stage_s   = channel_data[s]['x_values'][0]
        x_stage_n   = channel_data[s + 1]['x_values'][0]
        hub_s       = channel_data[s]['r_values'][0]
        hub_n       = channel_data[s + 1]['r_values'][0]
        shrd_s      = channel_data[s]['r_values'][4]
        shrd_n      = channel_data[s + 1]['r_values'][4]
        # Find closest index to interface in each stage's x array
        i_s = min(range(len(x_stage_s)), key=lambda i: abs(x_stage_s[i] - x_interface))
        i_n = min(range(len(x_stage_n)), key=lambda i: abs(x_stage_n[i] - x_interface))
        debug_log.debug(
            f"INTERFACE Stage {s}→{s+1} AFTER: "
            f"hub={hub_s[i_s]:.4f}→{hub_n[i_n]:.4f} mm "
            f"(Δ={hub_n[i_n]-hub_s[i_s]:+.4f}), "
            f"shroud={shrd_s[i_s]:.4f}→{shrd_n[i_n]:.4f} mm "
            f"(Δ={shrd_n[i_n]-shrd_s[i_s]:+.4f}), "
            f"x={x_stage_s[i_s]:.1f}/{x_stage_n[i_n]:.1f} mm",
            context="global_annulus")

# def init_channel_data(compressor_gui_data):
#     '''
#     Defining variables from the channel function for further use
    
#     '''
#     global channel_data
#     channel_data = {}
#     cumulative_x_offset = 0.0
    
#     for s in range(1, compressor_gui_data.stages_to_calc + 1):
#         compressor_gui_data.stage = s
#         x_values_s, r_values_s, m_prime_values_s, x0_s = channel(compressor_gui_data)

#         x0_s = list(x0_s)

#         if cumulative_x_offset != 0.0:
#             # ── shift every x-coordinate into the global frame ──────────────
#             # x0: the 9 spline control points
#             x0_s = [x + cumulative_x_offset for x in x0_s]

#             # x_values and m_prime_values: one list per span height (h_H)
#             for k in range(len(x_values_s)):
#                 x_values_s[k]      = [v + cumulative_x_offset for v in x_values_s[k]]
#                 m_prime_values_s[k] = [v + cumulative_x_offset for v in m_prime_values_s[k]]
#             # r_values are radii – they are NOT shifted

#         channel_data[s] = {
#             'x_values':       x_values_s,
#             'r_values':       r_values_s,
#             'm_prime_values': m_prime_values_s,
#             'x0':             x0_s,
#         }
        
#         cumulative_x_offset = x0_s[7]

#         print(f"Stage {s}: channel stored. "
#               f"x0[1]={x0_s[1]:.1f} mm  x0[7]={x0_s[7]:.1f} mm  "
#               f"→ next offset = {cumulative_x_offset:.1f} mm")
    
#     #x_values, r_values, m_prime_values, x0 = channel(compressor_gui_data)

def run_main_logic(new_adjustment_data, compressor_gui_data, json_path):# approach = 1 constant_r_parameter = 1 need to be defined here
    # Calls the channel function to initialise the channel coordinates for all stages that are beeing calculated
    init_channel_data(compressor_gui_data)
    global ACTIVE_JSON_PATH
    ACTIVE_JSON_PATH = json_path
    #should not be needed anymore
    global mflow, RPM, kappa, R, cp, i_st, T_t1, T_t2, T_t3, T_1, T_2, T_3, p_1, p_2, p_3, p_t1, p_t2, p_t3
    global D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3
    global cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, l_R, l_S
    global l_R_t_R, l_S_t_S, d_R_l_R, d_S_l_S, incidence_R, incidence_S, z_R, z_S
    global beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3, TPR_M, eta_sC_tt_M, eta_pC_tt_M, fixed_radius_type
    global h_rel, l_S_rad, c_m_S_in, c_m_S_out, c_u_S_in, c_u_S_out, c_S_out, T_S_in, T_S_out, p_S_in, p_S_out, alpha_S_in, beta_S_in, alpha_S_out, beta_blade_S_in, beta_blade_S_out, D_S
    global l_R_rad, r_R_out, c_m_R_in, c_m_R_out, c_u_R_in, c_u_R_out, c_R_out, u_R_in, u_R_out, T_R_in, T_R_out, p_R_in, p_R_out, Ma_abs_R_in, Ma_rel_R_in, roh_R_in, alpha_R_in, beta_R_in, alpha_R_out, beta_R_out, beta_blade_R_in, beta_blade_R_out, D_R
    global x_values, r_values, m_prime_values, x0
    
    # Needed for correct calling of radial equilibrium values
    global radial_data_R, radial_data_S

    
    #results_meanline = meanline()
    '''
    # Old
    (mflow, RPM, kappa, R, cp, i_st, T_t1, T_t2, T_t3, T_1, T_2, T_3, p_1, p_2, p_3, p_t1, p_t2, p_t3, 
    D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, 
    cm1, cm2, cm3, delta_h_t, l_R, l_S, l_R_t_R, l_S_t_S, d_R_l_R, d_S_l_S, incidence_R, incidence_S, 
    z_R, z_S, beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3, TPR_M, eta_sC_tt_M, eta_pC_tt_M, 
    fixed_radius_type) = compressor_gui_data.meanline_data()
    '''
    
    '''
    writing the Meanline-data out of the compact Dict into the already in use variable names
    
    '''
    global beta_blade_S_in, beta_blade_S_out, beta_blade_R_in, beta_blade_R_out, h_rel, l_S, l_R, alpha_S_in, alpha_S_out
    
    meanline = compressor_gui_data.meanline_data
    
    # Process- & Fluidparameter
    mflow = meanline['mflow']
    n = meanline['n']
    kappa = meanline['kappa']
    R = meanline['R']
    cp = meanline['cp']
    i_st = meanline['i_st']

    # Temperatures (Static & Total)
    T_t1 = meanline['T_t1']
    T_t2 = meanline['T_t2']
    T_t3 = meanline['T_t3']
    T_1 = meanline['T_1']
    T_2 = meanline['T_2']
    T_3 = meanline['T_3']

    # Pressures (Static & Total)
    p_1 = meanline['p_1']
    p_2 = meanline['p_2']
    p_3 = meanline['p_3']
    p_t1 = meanline['p_t1']
    p_t2 = meanline['p_t2']
    p_t3 = meanline['p_t3']

    # Gemoetrydiameters in Meters(Shroud, Hub, Mean)
    D_S1 = meanline['D_S1']
    D_S2 = meanline['D_S2']
    D_S3 = meanline['D_S3']
    D_H1 = meanline['D_H1']
    D_H2 = meanline['D_H2']
    D_H3 = meanline['D_H3']
    D_m1 = meanline['D_M1'] # Values are in meters nomenclature is wrong here
    D_m2 = meanline['D_M2'] # Values are in meters nomenclature is wrong here
    D_m3 = meanline['D_M3'] # Values are in meters nomenclature is wrong here

    # Velocity triangles & widths
    b1 = meanline['b1']
    b2 = meanline['b2']
    b3 = meanline['b3']
    cu1 = meanline['cu1']
    cu2 = meanline['cu2']
    cu3 = meanline['cu3']
    u1 = meanline['u1']
    u2 = meanline['u2']
    u3 = meanline['u3']
    cm1 = meanline['cm1']
    cm2 = meanline['cm2']
    cm3 = meanline['cm3']

    # Energetics- & Bladeparameters
    delta_h_t = meanline['delta_h_t']
    l_R = meanline['l_R']
    l_S = meanline['l_S']
    l_R_t_R = meanline['l_R_t_R']
    l_S_t_S = meanline['l_S_t_S']
    d_R_l_R = meanline['d_R_l_R']
    d_S_l_S = meanline['d_S_l_S']
    incidence_R = meanline['incidence_R']
    incidence_S = meanline['incidence_S']
    z_R = meanline['z_R']
    z_S = meanline['z_S']

    # Angles & Efficienties
    beta_blade_1 = meanline['beta_blade_1']
    beta_blade_2 = meanline['beta_blade_2']
    alpha_blade_2 = meanline['alpha_blade_2']
    alpha_blade_3 = meanline['alpha_blade_3']
    TPR_M = meanline['TPR_M']
    eta_sC_tt_M = meanline['eta_sC_tt_M']
    eta_pC_tt_M = meanline['eta_pC_tt_M']

    # Configurations
    fixed_radius_type = meanline['fixed_radius_type']
    plot_channel_contour = meanline['plot_channel_contour']
    
    
    
    ##### Hugh error dimension of all variables to short because they are defined as one stage and for one stage only 
    
    to_check = [
        'D_S1', 'D_S2', 'D_S3', 'D_H1', 'D_H2', 'D_H3', 'D_m1', 'D_m2', 'D_m3',
        'b1', 'b2', 'b3', 'cu1', 'cu2', 'cu3', 'u1', 'u2', 'u3', 'cm1', 'cm2', 'cm3',
        'delta_h_t', 'T_t1', 'T_t2', 'T_t3', 'p_t1', 'p_t2', 'p_t3'
    ]
    """
    for var_name in to_check:
        # Get the value from the local variables
        val = locals()[var_name]
        # If it's a single number, turn it into a list
        if isinstance(val, (int, float)):
            locals()[var_name] = [val]
    """
    '''
    Defining the values calculated by the radial equilibrium function
    
    '''
    ### New logic for radial equilibrium because it needs to calculated all stages ###
    
    # --- STANDARDIZATION BLOCK ---
    # Explicitly check and wrap variables in lists if they are single floats.
    # This ensures the [s-1] indexing in the loop below never fails.
    
    # 1. Geometry
    D_S1 = [D_S1] if isinstance(D_S1, (int, float)) else D_S1
    D_S2 = [D_S2] if isinstance(D_S2, (int, float)) else D_S2
    D_S3 = [D_S3] if isinstance(D_S3, (int, float)) else D_S3
    D_H1 = [D_H1] if isinstance(D_H1, (int, float)) else D_H1
    D_H2 = [D_H2] if isinstance(D_H2, (int, float)) else D_H2
    D_H3 = [D_H3] if isinstance(D_H3, (int, float)) else D_H3
    D_m1 = [D_m1] if isinstance(D_m1, (int, float)) else D_m1
    D_m2 = [D_m2] if isinstance(D_m2, (int, float)) else D_m2
    D_m3 = [D_m3] if isinstance(D_m3, (int, float)) else D_m3
    b1 = [b1] if isinstance(b1, (int, float)) else b1
    b2 = [b2] if isinstance(b2, (int, float)) else b2
    b3 = [b3] if isinstance(b3, (int, float)) else b3

    # 2. Velocities
    cu1 = [cu1] if isinstance(cu1, (int, float)) else cu1
    cu2 = [cu2] if isinstance(cu2, (int, float)) else cu2
    cu3 = [cu3] if isinstance(cu3, (int, float)) else cu3
    u1  = [u1]  if isinstance(u1,  (int, float)) else u1
    u2  = [u2]  if isinstance(u2,  (int, float)) else u2
    u3  = [u3]  if isinstance(u3,  (int, float)) else u3
    cm1 = [cm1] if isinstance(cm1, (int, float)) else cm1
    cm2 = [cm2] if isinstance(cm2, (int, float)) else cm2
    cm3 = [cm3] if isinstance(cm3, (int, float)) else cm3

    # 3. Thermo & Energetics
    delta_h_t = [delta_h_t] if isinstance(delta_h_t, (int, float)) else delta_h_t
    T_t1 = [T_t1] if isinstance(T_t1, (int, float)) else T_t1
    T_t2 = [T_t2] if isinstance(T_t2, (int, float)) else T_t2
    T_t3 = [T_t3] if isinstance(T_t3, (int, float)) else T_t3
    p_t1 = [p_t1] if isinstance(p_t1, (int, float)) else p_t1
    p_t2 = [p_t2] if isinstance(p_t2, (int, float)) else p_t2
    p_t3 = [p_t3] if isinstance(p_t3, (int, float)) else p_t3


    # --- DEBUGGING CHECK ---
    debug_log.debug(f"DEBUG LOOP START: stage_to_calc={compressor_gui_data.stages_to_calc}")
    debug_log.debug(f"DEBUG TYPE CHECK: b1 is {type(b1)}, cu1 is {type(cu1)}, cm1 is {type(cm1)}")
    
    radial_data_S = {}
    radial_data_R = {}

    for s in range(1, compressor_gui_data.stages_to_calc + 1):
        debug_log.debug(f"--- Processing Stage {s} ---")
        # Verify indexing will work
        debug_log.debug(f"DEBUG Stage {s}: b1[s-1]={b1[s-1]}")

        compressor_gui_data.stage = s

        
        
        (h_rel_s, l_S_s, c_m_S_in_s, c_m_S_out_s, c_u_S_in_s, c_u_S_out_s, c_S_out_s,
        T_S_in_s, T_S_out_s, p_S_in_s, p_S_out_s, alpha_S_in_s, beta_S_in_s, 
        alpha_S_out_s, beta_blade_S_in_s, beta_blade_S_out_s, D_S_s) = radial_equilibrium_S(
            s, approach, constant_r_parameter,
            D_S1[s-1], D_S2[s-1], D_S3[s-1],
            D_H1[s-1], D_H2[s-1], D_H3[s-1],
            D_m1[s-1], D_m2[s-1], D_m3[s-1],
            b1[s-1], b2[s-1], b3[s-1],
            cu1[s-1], cu2[s-1], cu3[s-1],
            u1[s-1], u2[s-1], u3[s-1],
            cm1[s-1], cm2[s-1], cm3[s-1],
            delta_h_t[s-1], T_t1[s-1], T_t2[s-1], T_t3[s-1],
            p_t1[s-1], p_t2[s-1], p_t3[s-1],
            compressor_gui_data)
        
        radial_data_S[s] = {
            'h_rel': h_rel_s, 'l_S': l_S_s, 'c_m_S_in': c_m_S_in_s,
            'c_m_S_out': c_m_S_out_s, 'c_u_S_in': c_u_S_in_s, 'c_u_S_out': c_u_S_out_s,
            'c_S_out': c_S_out_s, 'T_S_in': T_S_in_s, 'T_S_out': T_S_out_s,
            'p_S_in': p_S_in_s, 'p_S_out': p_S_out_s, 'alpha_S_in': alpha_S_in_s,
            'beta_S_in': beta_S_in_s, 'alpha_S_out': alpha_S_out_s,
            'beta_blade_S_in': beta_blade_S_in_s, 'beta_blade_S_out': beta_blade_S_out_s,
            'D_S': D_S_s
        }

        (h_rel_r, l_R_r, r_R_out_r, c_m_R_in_r, c_m_R_out_r, c_u_R_in_r, c_u_R_out_r,
        c_R_out_r, u_R_in_r, u_R_out_r, T_R_in_r, T_R_out_r, p_R_in_r, p_R_out_r,
        Ma_abs_R_in_r, Ma_rel_R_in_r, roh_R_in_r, alpha_R_in_r, beta_R_in_r,
        alpha_R_out_r, beta_R_out_r, beta_blade_R_in_r, beta_blade_R_out_r, D_R_r) = radial_equilibrium_R(
            s, approach, constant_r_parameter,
            D_S1[s-1], D_S2[s-1], D_S3[s-1],
            D_H1[s-1], D_H2[s-1], D_H3[s-1],
            D_m1[s-1], D_m2[s-1], D_m3[s-1],
            b1[s-1], b2[s-1], b3[s-1],
            cu1[s-1], cu2[s-1], cu3[s-1],
            u1[s-1], u2[s-1], u3[s-1],
            cm1[s-1], cm2[s-1], cm3[s-1],
            delta_h_t[s-1], T_t1[s-1], T_t2[s-1], T_t3[s-1],
            p_t1[s-1], p_t2[s-1], p_t3[s-1],
            compressor_gui_data)

        radial_data_R[s] = {
            'h_rel': h_rel_r, 'l_R': l_R_r, 'r_R_out': r_R_out_r,
            'c_m_R_in': c_m_R_in_r, 'c_m_R_out': c_m_R_out_r,
            'c_u_R_in': c_u_R_in_r, 'c_u_R_out': c_u_R_out_r,
            'c_R_out': c_R_out_r, 'u_R_in': u_R_in_r, 'u_R_out': u_R_out_r,
            'T_R_in': T_R_in_r, 'T_R_out': T_R_out_r,
            'p_R_in': p_R_in_r, 'p_R_out': p_R_out_r,
            'Ma_abs_R_in': Ma_abs_R_in_r, 'Ma_rel_R_in': Ma_rel_R_in_r,
            'roh_R_in': roh_R_in_r, 'alpha_R_in': alpha_R_in_r,
            'beta_R_in': beta_R_in_r, 'alpha_R_out': alpha_R_out_r,
            'beta_R_out': beta_R_out_r, 'beta_blade_R_in': beta_blade_R_in_r,
            'beta_blade_R_out': beta_blade_R_out_r, 'D_R': D_R_r
        }

    all_done_msg = "Successfully calculated meanline and radial equilibrium for all stages"
    print(all_done_msg)
    debug_log.debug(all_done_msg, context="run_main_logic")
    ### Debugging Screen to verify correct stage wise implementation of correct calling order
    
    debug_log.debug(f"VERIFY radial_data_R keys: {list(radial_data_R.keys())}")
    for s in radial_data_R:
        debug_log.debug(f"stage {s}: l_R[10]={radial_data_R[s]['l_R'][10]:.2f}", context="run_main_logic")
    
    debug_log.section("Radial Equilibrium Results")
    debug_log.debug(f"radial_equilibrium_S Results (Last Stage Calculated: {s})", context="run_main_logic")

    # Use the variables ending in _s as they represent the data from the last loop iteration
    debug_vars = {
        "Geometry": {"h_rel": h_rel_s, "l_S": l_S_s, "D_S_param": D_S_s},
        "Velocities (cm)": {"c_m_S_in": c_m_S_in_s, "c_m_S_out": c_m_S_out_s},
        "Velocities (cu/c)": {"c_u_S_in": c_u_S_in_s, "c_u_S_out": c_u_S_out_s, "c_S_out": c_S_out_s},
        "Thermodynamics": {"T_S_in": T_S_in_s, "T_S_out": T_S_out_s, "p_S_in": p_S_in_s, "p_S_out": p_S_out_s},
        "Angles (Deg)": {"alpha_S_in": alpha_S_in_s, "alpha_S_out": alpha_S_out_s, "beta_S_in": beta_S_in_s},
        "Blade Angles": {"beta_blade_S_in": beta_blade_S_in_s, "beta_blade_S_out": beta_blade_S_out_s}
    }

    for category, vars_dict in debug_vars.items():
        debug_log.debug(f"[{category}]", context="run_main_logic")
        for name, value in vars_dict.items():
            if isinstance(value, (list, np.ndarray)) and len(value) > 0:
                debug_log.debug(f"  {name:20}: {value[0]:.4f} ... {value[-1]:.4f} (len: {len(value)})", context="run_main_logic")
            else:
                debug_log.debug(f"  {name:20}: {value}", context="run_main_logic")

    # main_choice = new_adjustment_data.get('main_choice', 'default')
    main_choice = new_adjustment_data['main_choice']
    #path = settings.get("output_folder", ".")
    #NROW = int(settings.get("nrow", 2))
    #levels_input = new_adjustment_data.get("levels", "0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.00")
    
    
    levels_input = new_adjustment_data.get("levels", [0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.00])

    # Handle both string and list input
    if isinstance(levels_input, str):
        levels_input = [float(x.strip()) for x in levels_input.split(',')]
    elif isinstance(levels_input, list):
        levels_input = [float(x) for x in levels_input]
    
    
    h_H = [0.0, 0.2, 0.5, 0.8, 1.0] # Standard Werte für die Abschnitte
    

    #levels_input = [float(x.strip()) for x in levels_input.split(',')] # Liest die Levels ein und wandelt sie in eine Liste von Float-Werten um
    
    #chord_length_R = np.interp(h_H, h_rel, l_R) # Interpoliert die Sehnenlänge für die Standard Abschnitte
    #chord_length_S = np.interp(h_H, h_rel, l_S) 

    
    if main_choice == 'adjust': # Adjustment of Bezier points
        try:
            
            section_idx_str = new_adjustment_data['adjust_section_idx']
            section_idx_float = float(section_idx_str)
            
            # Base heights
            h_H_base = [0.0, 0.2, 0.5, 0.8, 1.0] # Why hardcoded?
            section_idx = h_H_base.index(section_idx_float)
            
            row_str = new_adjustment_data['adjust_row']
            parameter_str = new_adjustment_data['adjust_parameter']
            h_val = h_H_base[section_idx] 
            
            is_rotor = (row_str == 'Rotor')
            row_num = 1 if is_rotor else 2
            blade_key = "rotor" if is_rotor else "stator"
            angle_key = "beta_S" if is_rotor else "alpha_S"

            with open(json_path, 'r') as file:
                data = json.load(file)
                
            b_data = data.get("Bezier_point_data", {}).get(blade_key, {})
            if not b_data:
                err_msg = f"Error: No bezier data found for {row_str}. Please generate profiles first."
                print(err_msg)
                debug_log.debug(err_msg, context="adjust_bezier")
                return
                
            angles_flat = b_data.get(angle_key, [0]*20)
            d_l_flat = b_data.get("d/l", [0]*20)
            
            debug_log.debug(f"Selected parameter is: {parameter_str}", context="adjust_bezier")

            if parameter_str == 'Angle':
                adj_msg = f"Adjustments for Angle in row {row_str}, section: {h_val}"
                print(adj_msg)
                debug_log.debug(adj_msg, context="adjust_bezier")

                original_points = [angles_flat[section_idx + i*5] for i in range(4)]
                

                new_points = adjustBezierCurve_beta(original_points) 
                

                for i in range(4):
                    angles_flat[section_idx + i*5] = new_points[i]
                b_data[angle_key] = angles_flat
    
            elif parameter_str == 'Thickness':
                adj_msg = f"Adjustments for Thickness in row {row_str}, section: {h_val}"
                print(adj_msg)
                debug_log.debug(adj_msg, context="adjust_bezier")
                chord, *_ = calculation_of_section(h_val, row_num) 
                
                original_points = [d_l_flat[section_idx + i*5] for i in range(4)]
                new_points = adjustBezierCurve_d(original_points, chord)
                
                for i in range(4):
                    d_l_flat[section_idx + i*5] = new_points[i]
                b_data["d/l"] = d_l_flat 

            data["Bezier_point_data"][blade_key] = b_data
            with open(json_path, "w") as file:
                json.dump(data, file, indent=4)

            if hasattr(compressor_gui_data, "prepop_bezier_point_rotor"):
                if is_rotor:
                    compressor_gui_data.prepop_bezier_point_rotor = b_data
                else:
                    compressor_gui_data.prepop_bezier_point_stator = b_data
            
                
            save_adj_msg = f"Adjustments successfully saved to JSON for {row_str}!"
            print(save_adj_msg)
            debug_log.debug(save_adj_msg, context="adjust_bezier")
                               
        except Exception as e:
            err_msg = f"Error during adjustment: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="adjust_bezier")
            return


    
#area to change rotor:
# length = []
# h = [0.0 , 0.2, 0.5, 0.8, 1.0]
# row = 1
# for k in range(len(h)):
#     i = h[k]
#     chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
#     length.append(chord)

# #print(f"chordlength of 5 segments of rotor (approx):{length}")


# if use_default_rotor_bezier == 1:
#     bezier_control_points("bezier_control_points_R.txt", 1, beta_blade_R_in, beta_blade_R_out, length)

# if use_default_stator_bezier == 1:
#     bezier_control_points("bezier_control_points_S.txt", 2, beta_blade_S_in, beta_blade_S_out, length)





# #metal angle Bezierpoint for the new rotor design: 
# beta_S_BP_R_new = [[] for _ in range(5)]
# d_l_BP_R_new = [[] for _ in range(5)]

# with open('bezier_control_points_R.txt', 'r') as file:
#     beta_S_read = [[] for _ in range(4)] 
#     d_l_read = [[] for _ in range(4)]  

#     csv_reader = csv.reader(file)
    
#     # Skip all non-relevant lines (descriptive text)
#     for row in csv_reader:
#         if row and row[0].strip().startswith("1st to 4th control points for beta_S"):
#             break

#     # Read the next 4 rows for beta_S (control points)
#     for i in range(4):
#         row = next(csv_reader)
#         beta_S_read[i] = [float(val) for val in row]

#     for i in range(5):
#         beta_S_BP_R_new[i] = [beta_S_read[0][i], beta_S_read[1][i], beta_S_read[2][i], beta_S_read[3][i]]

#     # Skip until reaching d/l section
#     for row in csv_reader:
#         if row and row[0].strip().startswith("1st to 4th control points for d/l"):
#             break

#     # Read the next 4 rows for d/l (control points)
#     for i in range(4):
#         row = next(csv_reader)
#         d_l_read[i] = [float(val) for val in row]

#     for i in range(5):
#         d_l_BP_R_new[i] = [d_l_read[0][i], d_l_read[1][i], d_l_read[2][i], d_l_read[3][i]]

# if adjust_rotor_thickness == 1:
#     for i in range(5):
#         d_l_BP_R_new[i] = adjustBezierCurve_d(d_l_BP_R_new[i], length[i])

# if adjust_rotor_angle == 1:
#     for i in range(5):
#         beta_S_BP_R_new[i] = adjustBezierCurve_beta(beta_S_BP_R_new[i])

# with open('bezier_control_points_R.txt', "w+") as file:
#     file.write("For each level h/H = [0, 0.2, 0.5, 0.8, 1.0], there are four control points for the blade angle beta_S and the thickness d/l. The first and last control points for the blade angle beta_S are determined by radial equilibrium.\n\n")

#     file.write("1st to 4th control points for beta_S for all levels:\n")
#     for i in range(4):
#         file.write(f"{beta_S_BP_R_new[0][i]},{beta_S_BP_R_new[1][i]},{beta_S_BP_R_new[2][i]},{beta_S_BP_R_new[3][i]},{beta_S_BP_R_new[4][i]}\n")

#     file.write("\n")
#     file.write("1st to 4th control points for d/l for all levels:\n")

#     for i in range(4):
#         file.write(f"{d_l_BP_R_new[0][i]},{d_l_BP_R_new[1][i]},{d_l_BP_R_new[2][i]},{d_l_BP_R_new[3][i]},{d_l_BP_R_new[4][i]}\n")
                    
#     file.write("\n")
#     file.write("m* for all levels:\n")
    
#     file.write("0.0, 0.0, 0.0, 0.0, 0.0\n")
#     file.write("0.3, 0.3, 0.3, 0.3, 0.3\n")
#     file.write("0.7, 0.7, 0.7, 0.7, 0.7\n")
#     file.write("1.0, 1.0, 1.0, 1.0, 1.0\n")
    

#     # area to change stator:
#     length = []
#     row = 2
#     for k in range(len(h)):
#         i = h[k]
#         chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
#         length.append(chord)

#     #print(f"Chordlength of 5 segments of stator (approx):{length}")

#     #metal angle Bezierpoint for the new stator design: 
#     beta_S_BP_S_new = [[] for _ in range(5)]
#     d_l_BP_S_new = [[] for _ in range(5)]

#     with open('bezier_control_points_S.txt', 'r') as file:
#         beta_S_read = [[] for _ in range(4)] 
#         d_l_read = [[] for _ in range(4)]  

#         csv_reader = csv.reader(file)
        
#         # Skip all non-relevant lines (descriptive text)
#         for row in csv_reader:
#             if row and row[0].strip().startswith("1st to 4th control points for alpha_S"):
#                 break

#         # Read the next 4 rows for beta_S (control points)
#         for i in range(4):
#             row = next(csv_reader)
#             beta_S_read[i] = [float(val) for val in row]

#         for i in range(5):
#             beta_S_BP_S_new[i] = [beta_S_read[0][i], beta_S_read[1][i], beta_S_read[2][i], beta_S_read[3][i]]

#         # Skip until reaching d/l section
#         for row in csv_reader:
#             if row and row[0].strip().startswith("1st to 4th control points for d/l"):
#                 break

#         # Read the next 4 rows for d/l (control points)
#         for i in range(4):
#             row = next(csv_reader)
#             d_l_read[i] = [float(val) for val in row]

#         for i in range(5):
#             d_l_BP_S_new[i] = [d_l_read[0][i], d_l_read[1][i], d_l_read[2][i], d_l_read[3][i]]

#     if adjust_stator_thickness == 1:
#         for i in range(5):
#             d_l_BP_S_new[i] = adjustBezierCurve_d(d_l_BP_S_new[i], length[i])

#     if adjust_stator_angle == 1:
#         for i in range(5):
#             beta_S_BP_S_new[i] = adjustBezierCurve_beta(beta_S_BP_S_new[i])

#     with open('bezier_control_points_S.txt', "w+") as file:
#         file.write("For each level h/H = [0, 0.2, 0.5, 0.8, 1.0], there are four control points for the blade angle beta_S and the thickness d/l. The first and last control points for the blade angle beta_S are determined by radial equilibrium.\n\n")

#         file.write("1st to 4th control points for alpha_S for all levels:\n")
#         for i in range(4):
#             file.write(f"{beta_S_BP_S_new[0][i]},{beta_S_BP_S_new[1][i]},{beta_S_BP_S_new[2][i]},{beta_S_BP_S_new[3][i]},{beta_S_BP_S_new[4][i]}\n")

#         file.write("\n")
#         file.write("1st to 4th control points for d/l for all levels:\n")

#         for i in range(4):
#             file.write(f"{d_l_BP_S_new[0][i]},{d_l_BP_S_new[1][i]},{d_l_BP_S_new[2][i]},{d_l_BP_S_new[3][i]},{d_l_BP_S_new[4][i]}\n")
                        
#         file.write("\n")
#         file.write("m* for all levels:\n")
        
#         file.write("0.0, 0.0, 0.0, 0.0, 0.0\n")
#         file.write("0.3, 0.3, 0.3, 0.3, 0.3\n")
#         file.write("0.7, 0.7, 0.7, 0.7, 0.7\n")
#         file.write("1.0, 1.0, 1.0, 1.0, 1.0\n")

#     # 0: all sections or any number between 1 and NSECS
#     section = 0   
#     print(f"rotor_patches = {rotor_patches_data}")
                                                           


# general values, ellipis of LE and TE
def overall_values(row, z_R, l_R, l_S):    
  
    if row % 2 != 0:
        z = z_R
        # lenth of rotor blade h_rel = 50%
        s_1D = round(l_R[10]/1000, 4)                   
        s_0_5 = s_1D
        elipse_LE = 3
        elipse_TE = 3
    
    elif row % 2 == 0:
        z = z_S
        # lenth of rotor blade h_rel = 50%
        s_1D = round(l_S[10]/1000, 4)                      
        s_0_5 = s_1D
        elipse_LE = 3
        elipse_TE = 4
    
    # beginning of LE
    x_LE = []
    for i in range(len(h_H)):
        x_LE.append(round((-2*LE_shift*h_H[i]+LE_shift),5))  

    return z, s_1D, s_0_5, x_LE, elipse_LE, elipse_TE

'''
Old bezier control points from csv read
# Bézier control points from csv file
def blade_metal_BP(ROW):
    beta_M_e, beta_M_2, beta_M_3, beta_M_a, d_l_e, d_l_2, d_l_3, d_l_a = [], [], [], [], [], [], [], []   #beta_M_e: Liste mit Schaufeleintrittswinkel (Metall) für alle relativen Höhen aus h/H 
    m_star_BP = [[], [], [], []]
    if ROW == 1:
        BCPfile = "bezier_control_points_R.txt"
    elif ROW == 2:
        BCPfile = "bezier_control_points_S.txt"
    
    with open(BCPfile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader):
            if i == 3:
                for value in row:
                    beta_M_e.append(float(value))
            elif i == 4:
                for value in row:
                    beta_M_2.append(float(value))
            elif i == 5:
                for value in row:
                    beta_M_3.append(float(value))            
            elif i == 6:
                for value in row:
                    beta_M_a.append(float(value))
            elif i == 9:
                for value in row:
                    d_l_e.append(float(value))
            elif i == 10:
                for value in row:
                    d_l_2.append(float(value))
            elif i == 11:
                for value in row:
                    d_l_3.append(float(value))
            elif i == 12:
                for value in row:
                    d_l_a.append(float(value))
            elif i == 15:
                for value in row:
                    m_star_BP[0].append(float(value))
            elif i == 16:
                for value in row:
                    m_star_BP[1].append(float(value))
            elif i == 17:
                for value in row:
                    m_star_BP[2].append(float(value))
            elif i == 18:
                for value in row:
                    m_star_BP[3].append(float(value))

    return beta_M_a, beta_M_2, beta_M_3,  beta_M_e, d_l_a, d_l_2, d_l_3, d_l_e, m_star_BP
'''

# Bézier control points from csv file new# Bézier control points directly from JSON (ersetzt die alte .txt Version)
#OLD-VERSION
'''def blade_metal_BP(row):
    global ACTIVE_JSON_PATH
    json_path = ACTIVE_JSON_PATH
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error while reading JSON file: {e}")
        return [], [], [], [], [], [], [], [], [[], [], [], []]
        
    blade_key = "rotor" if row % 2 != 0 else "stator"
    angle_key = "beta_S" if row % 2 != 0 else "alpha_S"
    
    b_data = data.get("Bezier_point_data", {}).get(blade_key, {})
    if not b_data:
        print(f"No bezier data found for{blade_key} !")
        return [], [], [], [], [], [], [], [], [[], [], [], []]
        
    angles = b_data.get(angle_key, [0]*20)
    d_l = b_data.get("d/l", [0]*20)
    m_star = b_data.get("m*", [0]*20)

    beta_M_e = angles[0:5]    
    beta_M_2 = angles[5:10]   
    beta_M_3 = angles[10:15]  
    beta_M_a = angles[15:20]  
    
    d_l_e = d_l[0:5]
    d_l_2 = d_l[5:10]
    d_l_3 = d_l[10:15]
    d_l_a = d_l[15:20]
    
    m_star_BP = [
        m_star[0:5],
        m_star[5:10],
        m_star[10:15],
        m_star[15:20]
    ]
    
    return beta_M_a, beta_M_2, beta_M_3, beta_M_e, d_l_a, d_l_2, d_l_3, d_l_e, m_star_BP'''
''' 
### OLD ###
def blade_metal_BP(ROW):
    # beta_M_e, beta_M_2, beta_M_3, beta_M_a = [], [], [], []
    # d_l_e, d_l_2, d_l_3, d_l_a = [], [], [], []
    # m_star_BP = [[], [], [], []] 
    
    
    
    if ROW == 1:
        BCPfile = "bezier_control_points_R.txt"
        angle_header = "1st to 4th control points for beta_S for all levels:"
    elif ROW == 2:
        BCPfile = "bezier_control_points_S.txt"
        angle_header = "1st to 4th control points for alpha_S for all levels:"
    else:
        return [], [], [], [], [], [], [], [], [[], [], [], []]
        
    
    try:
        with open(BCPfile, 'r') as file:
            lines = file.readlines()
    except (FileNotFoundError) as e:
        print(f"Fehler beim lesen {BCPfile}: {e}")
        return [], [], [], [], [], [], [], [], [[], [], [], []]
    
    def find_and_read_data(header_text):
        data_block = []
        header_found_at = -1
        
        
        for i, line in enumerate(lines):
            if line.strip() == header_text:
                header_found_at = i
      
                break
            
        
        if header_found_at != -1 and len(lines) >= header_found_at + 5:
            for i in range(1, 5):
                data_row = [float(val) for val in lines[header_found_at + i].strip().split(',')]
                data_block.append(data_row)
            
        return data_block
    
    
    angle_data = find_and_read_data(angle_header)
    d_l_data = find_and_read_data("1st to 4th control points for d/l for all levels:") 
    m_star_data = find_and_read_data("m* for all levels:")
    
    beta_M_e, beta_M_2, beta_M_3, beta_M_a = (angle_data + [[]]*4)[:4] # stellt sicher, dass immer 4 Listen zurückgegeben werden, wenn weniger als 4 vorhanden sind wird aufgefüllt mit leeren Listen
    d_l_e, d_l_2, d_l_3, d_l_a = (d_l_data + [[]]*4)[:4]
    m_star_BP = (m_star_data + [[]]*4)[:4]
    
    return beta_M_a, beta_M_3, beta_M_2, beta_M_e, d_l_a, d_l_3, d_l_2, d_l_e, m_star_BP 
'''
def blade_metal_BP(row):
    """
    Read Bezier control points for blade row `row` from JSON.
 
    Row numbering (1-based, interleaved):
        1 = rotor  stage 1
        2 = stator stage 1
        3 = rotor  stage 2
        4 = stator stage 2
        …
    """
    global ACTIVE_JSON_PATH
    json_path = ACTIVE_JSON_PATH
 
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        json_err = f"Error while reading JSON file: {e}"
        print(json_err)
        debug_log.debug(json_err, context="blade_metal_BP")
        return [], [], [], [], [], [], [], [], [[], [], [], []]
  
    # Derive stage number and blade type from the row index
    stage_num = (row - 1) // 2 + 1
    is_rotor  = (row % 2 != 0)
 
    blade_key = f"rotor_stage_{stage_num}"  if is_rotor else f"stator_stage_{stage_num}"
    angle_key = "beta_S"                    if is_rotor else "alpha_S"
 
    bezier_store = data.get("Bezier_point_data", {})
 
    b_data = bezier_store.get(blade_key)
    if b_data is None:
        fallback_key = "rotor" if is_rotor else "stator"
        b_data = bezier_store.get(fallback_key)
        if b_data is not None:
            legacy_warn = (
                f"Warning: per-stage key '{blade_key}' not found – "
                f"falling back to legacy key '{fallback_key}'. "
                f"Re-generate profiles to fix this."
            )
            print(legacy_warn)
            debug_log.debug(legacy_warn, context="blade_metal_BP")
  
    if not b_data:
        no_data_msg = f"No bezier data found for '{blade_key}'!"
        print(no_data_msg)
        debug_log.debug(no_data_msg, context="blade_metal_BP")
        return [], [], [], [], [], [], [], [], [[], [], [], []]
 
    angles  = b_data.get(angle_key, [0] * 20)
    d_l     = b_data.get("d/l",     [0] * 20)
    m_star  = b_data.get("m*",      [0] * 20)
 
    beta_M_e = angles[0:5]
    beta_M_2 = angles[5:10]
    beta_M_3 = angles[10:15]
    beta_M_a = angles[15:20]

    blade_type = "ROTOR" if is_rotor else "STATOR"
    # Log the raw (pre-clamp) values from JSON
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] JSON_raw beta_M_e (LE): {[round(v, 2) for v in beta_M_e]}", context="blade_metal_raw")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] JSON_raw beta_M_2:      {[round(v, 2) for v in beta_M_2]}", context="blade_metal_raw")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] JSON_raw beta_M_3:      {[round(v, 2) for v in beta_M_3]}", context="blade_metal_raw")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] JSON_raw beta_M_a (TE): {[round(v, 2) for v in beta_M_a]}", context="blade_metal_raw")

    # Clamp angles to prevent Bezier curve from crossing 90 deg,
    # which causes 1/tan(beta) to change sign (INVALID Rtheta).
    if not is_rotor:
        # Stator: reflect ALL control points > 90 deg to [0, 90] interval
        beta_M_a = [180.0 - v if v > 90.0 else v for v in beta_M_a]
        beta_M_3 = [180.0 - v if v > 90.0 else v for v in beta_M_3]
        beta_M_2 = [180.0 - v if v > 90.0 else v for v in beta_M_2]
        beta_M_e = [180.0 - v if v > 90.0 else v for v in beta_M_e]
    else:
        # Rotor: if ALL 5 LE values > 90°, reflect ALL TE-side CPs < 90° to > 90°
        # Using span-consistent logic to avoid per-section discontinuities.
        le_all_above_90 = all(v > 90.0 for v in beta_M_e)
        if le_all_above_90:
            for i in range(5):
                for cp in [beta_M_a, beta_M_3, beta_M_2]:
                    if cp[i] < 90.0:
                        cp[i] = 180.0 - cp[i]

    d_l_e = d_l[0:5]
    d_l_2 = d_l[5:10]
    d_l_3 = d_l[10:15]
    d_l_a = d_l[15:20]

    blade_type = "ROTOR" if is_rotor else "STATOR"
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] beta_M_e (LE): {[round(v, 2) for v in beta_M_e]}", context="blade_metal_angles")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] beta_M_2:      {[round(v, 2) for v in beta_M_2]}", context="blade_metal_angles")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] beta_M_3:      {[round(v, 2) for v in beta_M_3]}", context="blade_metal_angles")
    debug_log.debug(f"  blade_metal_BP [{blade_type} row {row} stage {stage_num}] beta_M_a (TE): {[round(v, 2) for v in beta_M_a]}", context="blade_metal_angles")

    m_star_BP = [
        m_star[0:5],
        m_star[5:10],
        m_star[10:15],
        m_star[15:20],
    ]
 
    return beta_M_a, beta_M_2, beta_M_3, beta_M_e, d_l_a, d_l_2, d_l_3, d_l_e, m_star_BP
#Section to fix center of gravity for all sections
#Calculation for h/H = 0.5 cut
def calculation_of_section_0_5(row):
    rel_h = 0.5
    
    '''
    Defining coordinates for all stages
    '''
    stage_to_calc = (row - 1) // 2 + 1
    x0 = channel_data[stage_to_calc]['x0']
    
    #print(f"  VERIFY calc_0_5 [row={row}, stage={stage}]: x0[2]={x0[2]:.4f}") # Debug to see if stage per stage calls are working 

    beta_M_a, beta_M_2, beta_M_3,  beta_M_e, d_l_a, d_l_2, d_l_3, d_l_e, m_star_BP= blade_metal_BP(row)
    
    
    
    '''
    ### Chaning the calling for the calculation of the overall values from scalar first stage values to values that are depending on the current stage.
    For that using the row numbering to calcualte the current stage to be calculated and accesing the correct values of the current stage
    '''
    stage = (row - 1) // 2 + 1
    _l_R = radial_data_R[stage]['l_R']
    _l_S = radial_data_S[stage]['l_S']
    _z_R = radial_data_R[stage].get('z_R', z_R)  # fallback to global if not in dict
    _z_S = radial_data_S[stage].get('z_S', z_S)
    z, s_1D, s_0_5, x_LE, elipse_LE, elipse_TE = overall_values(row, _z_R, _l_R, _l_S)
    debug_log.debug(f"  VERIFY overall_values [row={row}]: s_1D={s_1D:.4f}") # Temporary Debug call 
    
    
    # Old logic z, s_1D, s_0_5, x_LE, elipse_LE, elipse_TE = overall_values(row, z_R, l_R, l_S)
    
    LE_TE_fac_1 = [0.0, 2.0, 5.0, 9.0, 15.0, 22.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
     
    LE_TE_fac_2 = LE_TE_fac_1.copy()
    LE_TE_fac_2.reverse()

    k = 125-2*len(LE_TE_fac_1)
    Nulls = [0.0]*k
    LE_TE_fac = LE_TE_fac_1 + Nulls + LE_TE_fac_2

    m_BP = []
    for i in range(4): 
        m_BP.append(cubspline(3, rel_h, h_H, m_star_BP[i]))

    beta_BP = []    
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_e))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_2))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_3))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_a))

    debug_log.debug(f"  calc_section_0_5 [row={row}, rel_h={rel_h}]: beta_BP (interpolated) = {[round(v, 2) for v in beta_BP]}", context="camber_angles")

    d_l_BP =[]
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_e)/200)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_2)/200)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_3)/200)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_a)/200)
    
    FAK_m_LE = elipse_LE*d_l_BP[0]/bezier(4, elipse_LE*d_l_BP[0], m_BP)
    FAK_m_TE = (1-elipse_TE*d_l_BP[3])/bezier(4, 1-elipse_TE*d_l_BP[3], m_BP)
    
    t_LE = []
    for i in range(len(LE_TE_fac_1)):
        t_LE.append((1-math.cos(Pi*LE_TE_fac_1[i]/180))*elipse_LE*d_l_BP[0]*FAK_m_LE)

    t_TE = []
    for i in range(len(LE_TE_fac_2)):
        t_TE.append((1-(1-math.cos(Pi*LE_TE_fac_2[i]/180))*elipse_TE*d_l_BP[3]*FAK_m_TE))

    Dt = (round(t_TE[0], 3)-round(t_LE[12], 3))/100

    t = []
    t = t_LE
    for i in range(len(Nulls)):
        t.append(t[-1]+Dt)

    t += t_TE 

    m_prime = []      
    for i in range(len(t)):
        m_prime.append(bezier(4, t[i], m_BP))

    beta_S = []
    for i in range(len(t)):
        beta_S.append(bezier(4, m_prime[i], beta_BP))

    R_theta_s_prime = [0.0]
    for i in range(len(t)-1):
        R_theta_s_prime.append(R_theta_s_prime[-1]+1/math.tan((beta_S[i] + beta_S[i+1])/2*Pi/180) *(m_prime[i+1]-m_prime[i]))

    s_star = math.sqrt(1+R_theta_s_prime[124]**2)

    p = (len(LE_TE_fac_1)-1)
    q = (len(Nulls))
    
    d_l = []
    for i in range(len(m_prime)):
        if i <= p:
            d_l.append(bezier(4,m_prime[i], d_l_BP)*math.sin(Pi*LE_TE_fac[i]/180))
        elif i > p and i <= p+q+1:
            d_l.append(bezier(4, m_prime[i], d_l_BP))
        elif i > p+q+1:
            d_l.append(bezier(4, m_prime[i], d_l_BP)*math.sin(Pi*LE_TE_fac[i]/180))
        
    m_prime_u, m_prime_l =[], []
    for i in range(0, len(m_prime)):
        if i == 0:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
        elif i>0 and i<124:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
        elif i == 124:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))

    R_theta_s_prime_u, R_theta_s_prime_l = [], []
    for i in range(len(m_prime)):
        if i == 0:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i+1]-m_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i+1]-m_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
        elif i>0 and i<124:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i+1]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i+1]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
        elif i == 124:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))

    # section for new calculation of upper/lower side coordinates 
    def min_max(m_prime):
        m_prime_min = float('inf') 
        pos_m_prime_min = 0
        m_prime_max = float('-inf')  
        pos_m_prime_max = 0
        
        for i in range(len(m_prime_u)):
            if m_prime[i] <= m_prime_min:
                m_prime_min = m_prime[i]
                pos_m_prime_min = i
            elif m_prime[i] >= m_prime_max:
                m_prime_max = m_prime[i]
                pos_m_prime_max = i
            
        return pos_m_prime_min, pos_m_prime_max

    pos_m_prime_min_u, pos_m_prime_max_u = min_max(m_prime_u)        
    pos_m_prime_min_l, pos_m_prime_max_l = min_max(m_prime_l)        

    def global_maxima(pos_m_prime_min_u, pos_m_prime_min_l, pos_m_prime_max_u, pos_m_prime_max_l):
        pos_m_prime_min = float('inf')  
        pos_m_prime_max = float('-inf')

        m_prime_min = min(m_prime_u[pos_m_prime_min_u], m_prime_l[pos_m_prime_min_l])
        m_prime_max = max(m_prime_u[pos_m_prime_max_u], m_prime_l[pos_m_prime_max_l])
        
        return pos_m_prime_min, pos_m_prime_max, m_prime_min, m_prime_max

    pos_m_prime_min, pos_m_prime_max, m_prime_min, m_prime_max = global_maxima(pos_m_prime_min_u, pos_m_prime_min_l, pos_m_prime_max_u, pos_m_prime_max_l)
    
    if m_prime_min == m_prime_u[pos_m_prime_min_u]:
        pos_m_prime_min = pos_m_prime_min_u
        
        if m_prime_max == m_prime_u[pos_m_prime_max_u]:    
            pos_m_prime_max = pos_m_prime_max_u
            
            #supporting lists:
            helping_list_m = m_prime_u[0:pos_m_prime_min+1]
            helping_list_m.reverse()
            helping_list_m2 = m_prime_u[pos_m_prime_max:]
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_u[0:pos_m_prime_min+1]
            helping_list_R.reverse()
            helping_list_R2 = R_theta_s_prime_u[pos_m_prime_max:]
            helping_list_R2.reverse()
            
            #new upper side
            m_prime_u = m_prime_u[pos_m_prime_min:pos_m_prime_max+1]
            R_theta_s_prime_u = R_theta_s_prime_u[pos_m_prime_min:pos_m_prime_max+1]
            
            #new lower side
            m_prime_l = helping_list_m + m_prime_l+ helping_list_m2
            R_theta_s_prime_l = helping_list_R + R_theta_s_prime_l + helping_list_R2
            
        elif m_prime_max == m_prime_l[pos_m_prime_max_l]:
            pos_m_prime_max = pos_m_prime_max_l 
            
            #supporting list:
            helping_list_m = m_prime_u[0:pos_m_prime_min]
            helping_list_m.reverse()   
            helping_list_R = R_theta_s_prime_u[0:pos_m_prime_min]
            helping_list_R.reverse()   

            #upper side
            m_prime_u = m_prime_u[pos_m_prime_min:]+m_prime_l[pos_m_prime_max:]
            R_theta_s_prime_u = R_theta_s_prime_u[pos_m_prime_min:] +R_theta_s_prime_u[pos_m_prime_max:]

            #lower side
            m_prime_l = helping_list_m + m_prime_l[0:pos_m_prime_max]
            R_theta_s_prime_l = helping_list_R + R_theta_s_prime_l[0:pos_m_prime_max]
            debug_log.debug("blade section 2 selected (upper side)", context="blade_geometry")

    elif m_prime_min == m_prime_l[pos_m_prime_min_l]:
        pos_m_prime_min = pos_m_prime_min_l
        if m_prime_max == m_prime_u[pos_m_prime_max_u]:
            pos_m_prime_max = pos_m_prime_max_u

            #supporting lists:
            helping_list_m = m_prime_l[0:pos_m_prime_min_l+1] 
            helping_list_m.reverse()

            helping_list_m2 = m_prime_u[pos_m_prime_max:] 
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_l[0:pos_m_prime_min_l+1]
            helping_list_R.reverse()

            helping_list_R2 = R_theta_s_prime_u[pos_m_prime_max:]
            helping_list_R2.reverse()
            
            helping_list_d = d_l[1:pos_m_prime_min_l]
            helping_list_d.reverse()

            #upper side
            m_prime_u = helping_list_m + m_prime_u[0:pos_m_prime_max+1]
            R_theta_s_prime_u = helping_list_R + R_theta_s_prime_u[0:pos_m_prime_max+1]
            
            #lower side
            m_prime_l = m_prime_l[pos_m_prime_min:] + helping_list_m2
            R_theta_s_prime_l = R_theta_s_prime_l[pos_m_prime_min:] + helping_list_R2

        elif m_prime_max == m_prime_l[pos_m_prime_max_l]:
            pos_m_prime_max = pos_m_prime_max_l
            
            #supporting lists:
            helping_list_m = m_prime_l[0:pos_m_prime_min_l+1] 
            helping_list_m2 = m_prime_l[pos_m_prime_max:-1] 
            helping_list_m.reverse()
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_l[0:pos_m_prime_min_l+1]
            helping_list_R2 = R_theta_s_prime_l[pos_m_prime_max:-1] 
            helping_list_R.reverse()
            helping_list_R2.reverse()

            helping_list_d = d_l[1:pos_m_prime_min_l]
            helping_list_d2 = d_l[pos_m_prime_max:-1] 
            helping_list_d.reverse()
            helping_list_d2.reverse()

            #upper side
            m_prime_u = helping_list_m + m_prime_u + helping_list_m2  
            R_theta_s_prime_u = helping_list_R + R_theta_s_prime_u + helping_list_R2

            #lower side
            m_prime_l = m_prime_l[pos_m_prime_min:pos_m_prime_max+1]
            R_theta_s_prime_l = R_theta_s_prime_l[pos_m_prime_min:pos_m_prime_max+1]

    # check if first coordinate of upper and lower side are the same 
    if m_prime_l[0]!=m_prime_u[0]:
        debug_log.debug("first coordinates of upper/lower side not equal", context="blade_geometry")

    dif_list_len_u = len(m_prime_u)-125
    
    if dif_list_len_u > 0:
        for i in range(dif_list_len_u):
            k = 15+i*4
            del m_prime_u[k]
            del R_theta_s_prime_u[k]

    elif dif_list_len_u < 0:
        for i in range(abs(dif_list_len_u)):
            k = 15+i*4
            new_m_value = m_prime_u[k]+(m_prime_u[k+1]-m_prime_u[k])/2
            m_prime_u.insert(k+1, new_m_value)
            new_Rtheta_value = R_theta_s_prime_u[k]+(R_theta_s_prime_u[k+1]-R_theta_s_prime_u[k])/2
            R_theta_s_prime_u.insert(k+1, new_Rtheta_value)

    dif_list_len_l = len(m_prime_l)-125
    
    if dif_list_len_l > 0:
        for i in range(dif_list_len_l):
            k = 15+i*4
            del m_prime_l[k]
            del R_theta_s_prime_l[k]

    elif dif_list_len_l < 0:
        for i in range(abs(dif_list_len_l)):
            k = 15+i*4
            new_m_value = m_prime_l[k]+(m_prime_l[k+1]-m_prime_l[k])/2
            m_prime_l.insert(k+1, new_m_value)
            new_Rtheta_value = R_theta_s_prime_l[k]+(R_theta_s_prime_l[k+1]-R_theta_s_prime_l[k])/2
            R_theta_s_prime_l.insert(k+1, new_Rtheta_value)
    
    # calculation of center of area 
    coa1, coa2, coa3 = [], [], []
    for i in range(len(m_prime)-1):
        coa1.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2*(m_prime[i+1]+m_prime[i])/2)
        coa2.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2*(R_theta_s_prime[i+1]+R_theta_s_prime[i])/2)
        coa3.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2)

    coa1.append(sum(coa1))   
    coa2.append(sum(coa2))  
    coa3.append(sum(coa3))

    m_prime_cntr = coa1[124]/coa3[124]
    Rtet_prime_cntr = coa2[124]/coa3[124]

    if row % 2 != 0:
        k = 2
    elif row % 2 == 0:
        k = 5

    m_cntr_0_5 = m_prime_cntr*s_0_5/s_star*1000+x0[k]                               #m*cntr
    
    return  m_cntr_0_5, m_prime_cntr

# calculation of LE and TE coordinates
def mLE_TE_cntr(row):
    '''
    Defining coordinates for all stages
    '''
    stage_to_calc = (row - 1) // 2 + 1
    x0 = channel_data[stage_to_calc]['x0']
    debug_log.debug(f"  VERIFY mLE_TE_cntr [row={row}, stage={stage_to_calc}]: x0[2]={x0[2]:.4f}, m_LE_0_5 will be={x0[2 if row%2!=0 else 5]:.4f}") # Same verification for correct implemntation of stage by stage calling
    
    if row % 2 != 0:
        k = 2
    elif row % 2 == 0:
        k = 5
    
    m_cntr_0_5, m_prime_cntr = calculation_of_section_0_5(row)

    m_LE_0_5 = x0[k]
    m_TE_0_5 = m_cntr_0_5 + (m_cntr_0_5-m_LE_0_5)*(1-m_prime_cntr)/m_prime_cntr

    return m_LE_0_5, m_TE_0_5, m_cntr_0_5, m_prime_cntr

# calculation of a section coordiantes of a single row
def calculation_of_section(rel_h, row):
    
    '''
    Defining coordinates for all stages
    '''
    stage = (row - 1) // 2 + 1
    r_values = channel_data[stage]['r_values']
    m_prime_values = channel_data[stage]['m_prime_values']

    m_LE_0_5, m_TE_0_5, m_cntr_0_5, m_prime_cntr = mLE_TE_cntr(row)
    beta_M_a, beta_M_2, beta_M_3,  beta_M_e, d_l_a, d_l_2, d_l_3, d_l_e, m_star_BP= blade_metal_BP(row)
    
    '''
    ### Chaning the calling for the calculation of the overall values from scalar first stage values to values that are depending on the current stage.
    For that using the row numbering to calcualte the current stage to be calculated and accesing the correct values of the current stage
    '''
    stage = (row - 1) // 2 + 1
    _l_R = radial_data_R[stage]['l_R']
    _l_S = radial_data_S[stage]['l_S']
    _z_R = radial_data_R[stage].get('z_R', z_R)  # fallback to global if not in dict
    _z_S = radial_data_S[stage].get('z_S', z_S)
    z, s_1D, s_0_5, x_LE, elipse_LE, elipse_TE = overall_values(row, _z_R, _l_R, _l_S)
    debug_log.debug(f"  VERIFY overall_values [row={row}]: s_1D={s_1D:.4f}") # Temporary Debug call 
    
    # Old logic z, s_1D, s_0_5, x_LE, elipse_LE, elipse_TE = overall_values(row, z_R, l_R, l_S)
    
    LE_TE_fac_1 = [0.0, 2.0, 5.0, 9.0, 15.0, 22.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    
    LE_TE_fac_2 = LE_TE_fac_1.copy()
    LE_TE_fac_2.reverse()

    k = 125-2*len(LE_TE_fac_1)
    Nulls = [0.0]*k
    LE_TE_fac = LE_TE_fac_1 + Nulls + LE_TE_fac_2
    

    m_BP = []
    for i in range(4): 
        m_BP.append(cubspline(3, rel_h, h_H, m_star_BP[i]))

    beta_BP = []    
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_e))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_2))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_3))
    beta_BP.append(cubspline(3, rel_h, h_H, beta_M_a))

    debug_log.debug(f"  calc_section [row={row}, rel_h={rel_h:.2f}]: beta_BP (interpolated) = {[round(v, 2) for v in beta_BP]}", context="camber_angles")

    d_l_BP =[]
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_e)/100)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_2)/100)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_3)/100)
    d_l_BP.append(cubspline(3, rel_h, h_H, d_l_a)/100)
    

    FAK_m_LE = elipse_LE*d_l_BP[0]/bezier(4, elipse_LE*d_l_BP[0], m_BP)
    FAK_m_TE = (1-elipse_TE*d_l_BP[3])/bezier(4, 1-elipse_TE*d_l_BP[3], m_BP)

    t_LE = []
    for i in range(len(LE_TE_fac_1)):
        t_LE.append((1-math.cos(Pi*LE_TE_fac_1[i]/180))*elipse_LE*d_l_BP[0]*FAK_m_LE)
    
    t_TE = []
    for i in range(len(LE_TE_fac_2)):
        t_TE.append((1-(1-math.cos(Pi*LE_TE_fac_2[i]/180))*elipse_TE*d_l_BP[3]*FAK_m_TE))

    Dt = (round(t_TE[0], 3)-round(t_LE[12], 3))/100

    t = []
    t = t_LE
    for i in range(len(Nulls)):
        t.append(t[-1]+Dt)
    t += t_TE 
    
    m_prime = []                              
    for i in range(len(t)):
        m_prime.append(float(bezier(4, t[i], m_BP)))

    beta_S = []
    for i in range(len(t)):
        beta_S.append(bezier(4, m_prime[i], beta_BP))

    R_theta_s_prime = [0.0]
    for i in range(len(t)-1):
        R_theta_s_prime.append(R_theta_s_prime[-1]+1/math.tan((beta_S[i] + beta_S[i+1])/2*Pi/180) *(m_prime[i+1]-m_prime[i]))

    debug_log.debug(f"  calc_section [row={row}, rel_h={rel_h:.2f}]: R_theta_s_prime[0]={R_theta_s_prime[0]:.6f} (LE), R_theta_s_prime[124]={R_theta_s_prime[124]:.6f} (TE)", context="Rtheta_integration")
    debug_log.debug(f"  calc_section [row={row}, rel_h={rel_h:.2f}]: beta_S[0]={beta_S[0]:.2f} deg (LE), beta_S[124]={beta_S[124]:.2f} deg (TE)", context="Rtheta_integration")

    #Chordlength
    s_star = math.sqrt(1+R_theta_s_prime[124]**2)       
    p = (len(LE_TE_fac_1)-1)
    q = (len(Nulls))
    
    d_l = []
    for i in range(len(m_prime)):
        if i <= p:
            d_l.append(bezier(4,m_prime[i], d_l_BP)*math.sin(Pi*LE_TE_fac[i]/180))
        elif i > p and i <= p+q+1:
            d_l.append(bezier(4, m_prime[i], d_l_BP))
        elif i > p+q+1:
            d_l.append(bezier(4, m_prime[i], d_l_BP)*math.sin(Pi*LE_TE_fac[i]/180))


    m_prime_u, m_prime_l =[], []
    for i in range(len(m_prime)):
        if i == 0:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
        elif i>0 and i<124:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i+1]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
        elif i == 124:
            m_prime_u.append(m_prime[i]-d_l[i]*(R_theta_s_prime[i]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))
            m_prime_l.append(m_prime[i]+d_l[i]*(R_theta_s_prime[i]-R_theta_s_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))


    R_theta_s_prime_u, R_theta_s_prime_l = [], []
    for i in range(len(m_prime)):
        if i == 0:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i+1]-m_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i+1]-m_prime[i])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i])**2+(m_prime[i+1]-m_prime[i])**2))
        elif i>0 and i<124:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i+1]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i+1]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i+1]-R_theta_s_prime[i-1])**2+(m_prime[i+1]-m_prime[i-1])**2))
        elif i == 124:
            R_theta_s_prime_u.append(R_theta_s_prime[i]+s_star*d_l[i]*(m_prime[i]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))
            R_theta_s_prime_l.append(R_theta_s_prime[i]-s_star*d_l[i]*(m_prime[i]-m_prime[i-1])/math.sqrt((R_theta_s_prime[i]-R_theta_s_prime[i-1])**2+(m_prime[i]-m_prime[i-1])**2))

    coa1, coa2, coa3 = [], [], []
    for i in range(len(m_prime)-1):
        coa1.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2*(m_prime[i+1]+m_prime[i])/2)
        coa2.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2*(R_theta_s_prime[i+1]+R_theta_s_prime[i])/2)
        coa3.append(math.sqrt((m_prime[i+1]-m_prime[i])**2+(R_theta_s_prime[i+1]-R_theta_s_prime[i])**2)*2*s_star*(d_l[i+1]+d_l[i])/2)

    coa1.append(sum(coa1))   
    coa2.append(sum(coa2))  
    coa3.append(sum(coa3))

    m_prime_cntr = coa1[124]/coa3[124]
    Rtet_prime_cntr = coa2[124]/coa3[124]    

   
    def min_max(m_prime):
        m_prime_min = float('inf') 
        pos_m_prime_min = 0
        m_prime_max = float('-inf')  
        pos_m_prime_max = 0
        
        for i in range(len(m_prime_u)):
            if m_prime[i] <= m_prime_min:
                m_prime_min = m_prime[i]
                pos_m_prime_min = i
            elif m_prime[i] >= m_prime_max:
                m_prime_max = m_prime[i]
                pos_m_prime_max = i
            
        return pos_m_prime_min, pos_m_prime_max

    pos_m_prime_min_u, pos_m_prime_max_u = min_max(m_prime_u)        
    #print(pos_m_prime_min_u, pos_m_prime_max_u)
    #plt.scatter(m_prime_u[pos_m_prime_min_u], R_theta_s_prime_u[pos_m_prime_min_u], s = 50)
    #plt.scatter(m_prime_u[pos_m_prime_max_u], R_theta_s_prime_u[pos_m_prime_max_u], s = 50)

    pos_m_prime_min_l, pos_m_prime_max_l = min_max(m_prime_l)        
    #print(pos_m_prime_min_l, pos_m_prime_max_l)
    #plt.scatter(m_prime_l[pos_m_prime_min_l], R_theta_s_prime_l[pos_m_prime_min_l], s = 50)
    #plt.scatter(m_prime_l[pos_m_prime_max_l], R_theta_s_prime_l[pos_m_prime_max_l], s = 50)

    def global_maxima(pos_m_prime_min_u, pos_m_prime_min_l, pos_m_prime_max_u, pos_m_prime_max_l):
        pos_m_prime_min = float('inf')  
        pos_m_prime_max = float('-inf')

        m_prime_min = min(m_prime_u[pos_m_prime_min_u], m_prime_l[pos_m_prime_min_l])
        m_prime_max = max(m_prime_u[pos_m_prime_max_u], m_prime_l[pos_m_prime_max_l])
        
        return pos_m_prime_min, pos_m_prime_max, m_prime_min, m_prime_max

    pos_m_prime_min, pos_m_prime_max, m_prime_min, m_prime_max = global_maxima(pos_m_prime_min_u, pos_m_prime_min_l, pos_m_prime_max_u, pos_m_prime_max_l)
    
    if m_prime_min == m_prime_u[pos_m_prime_min_u]:
        pos_m_prime_min = pos_m_prime_min_u
        
        if m_prime_max == m_prime_u[pos_m_prime_max_u]:    
            pos_m_prime_max = pos_m_prime_max_u
            
            #supporting lists:
            helping_list_m = m_prime_u[0:pos_m_prime_min+1]
            helping_list_m.reverse()
            helping_list_m2 = m_prime_u[pos_m_prime_max:]
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_u[0:pos_m_prime_min+1]
            helping_list_R.reverse()
            helping_list_R2 = R_theta_s_prime_u[pos_m_prime_max:]
            helping_list_R2.reverse()
            
            #new upper side
            m_prime_u = m_prime_u[pos_m_prime_min:pos_m_prime_max+1]
            R_theta_s_prime_u = R_theta_s_prime_u[pos_m_prime_min:pos_m_prime_max+1]
            
            #new lower side
            m_prime_l = helping_list_m + m_prime_l+ helping_list_m2
            R_theta_s_prime_l = helping_list_R + R_theta_s_prime_l + helping_list_R2
            
        elif m_prime_max == m_prime_l[pos_m_prime_max_l]:
            pos_m_prime_max = pos_m_prime_max_l 
            
            #supporting list:
            helping_list_m = m_prime_u[0:pos_m_prime_min]
            helping_list_m.reverse()   
            helping_list_R = R_theta_s_prime_u[0:pos_m_prime_min]
            helping_list_R.reverse()   

            #upper side
            m_prime_u = m_prime_u[pos_m_prime_min:]+m_prime_l[pos_m_prime_max:]
            R_theta_s_prime_u = R_theta_s_prime_u[pos_m_prime_min:] +R_theta_s_prime_u[pos_m_prime_max:]
            
            #lower side
            m_prime_l = helping_list_m + m_prime_l[0:pos_m_prime_max]
            R_theta_s_prime_l = helping_list_R + R_theta_s_prime_l[0:pos_m_prime_max]
            debug_log.debug("blade section 2 selected (upper side)", context="blade_geometry")

    elif m_prime_min == m_prime_l[pos_m_prime_min_l]:
        pos_m_prime_min = pos_m_prime_min_l
        if m_prime_max == m_prime_u[pos_m_prime_max_u]:
            pos_m_prime_max = pos_m_prime_max_u

            #supporting lists:
            helping_list_m = m_prime_l[0:pos_m_prime_min_l+1] 
            helping_list_m.reverse()

            helping_list_m2 = m_prime_u[pos_m_prime_max:] 
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_l[0:pos_m_prime_min_l+1]
            helping_list_R.reverse()

            helping_list_R2 = R_theta_s_prime_u[pos_m_prime_max:]
            helping_list_R2.reverse()
            
            helping_list_d = d_l[1:pos_m_prime_min_l]
            helping_list_d.reverse()

            #upper side
            m_prime_u = helping_list_m + m_prime_u[0:pos_m_prime_max+1]
            R_theta_s_prime_u = helping_list_R + R_theta_s_prime_u[0:pos_m_prime_max+1]
            
            #lower side
            m_prime_l = m_prime_l[pos_m_prime_min:] + helping_list_m2
            R_theta_s_prime_l = R_theta_s_prime_l[pos_m_prime_min:] + helping_list_R2

        elif m_prime_max == m_prime_l[pos_m_prime_max_l]:
            pos_m_prime_max = pos_m_prime_max_l
            
            #supporting lists:
            helping_list_m = m_prime_l[0:pos_m_prime_min_l+1] 
            helping_list_m2 = m_prime_l[pos_m_prime_max:-1] 
            helping_list_m.reverse()
            helping_list_m2.reverse()

            helping_list_R = R_theta_s_prime_l[0:pos_m_prime_min_l+1]
            helping_list_R2 = R_theta_s_prime_l[pos_m_prime_max:-1] 
            helping_list_R.reverse()
            helping_list_R2.reverse()

            helping_list_d = d_l[1:pos_m_prime_min_l]
            helping_list_d2 = d_l[pos_m_prime_max:-1] 
            helping_list_d.reverse()
            helping_list_d2.reverse()

            #upper side
            m_prime_u = helping_list_m + m_prime_u + helping_list_m2  
            R_theta_s_prime_u = helping_list_R + R_theta_s_prime_u + helping_list_R2

            #lower side
            m_prime_l = m_prime_l[pos_m_prime_min:pos_m_prime_max+1]
            R_theta_s_prime_l = R_theta_s_prime_l[pos_m_prime_min:pos_m_prime_max+1]

    if m_prime_l[0]!=m_prime_u[0]:
        debug_log.debug("first coordinates of upper/lower side not equal (stator)", context="blade_geometry")

    # activate for plotting of blade geometry
    """
    plt.scatter(m_prime_u, R_theta_s_prime_u, s = 3)
    plt.plot(m_prime_u, R_theta_s_prime_u) 
    plt.scatter(m_prime, R_theta_s_prime, s = 3)
    plt.plot(m_prime_l, R_theta_s_prime_l)
    plt.scatter(m_prime_l, R_theta_s_prime_l, s = 3)
    plt.plot(m_prime, R_theta_s_prime)
    plt.xlabel("m' [-]")
    plt.ylabel("R\u03b8 [-]")
    plt.xlim(-0.005,0.015)
    plt.ylim(-0.01,0.0025)
    plt.axis('equal')
    plt.show()
    """
    
    dif_list_len_u = len(m_prime_u)-125
    
    if dif_list_len_u > 0:
        for i in range(dif_list_len_u):
            k = 20+i*5
            del m_prime_u[k]
            del R_theta_s_prime_u[k]

    elif dif_list_len_u < 0:
        for i in range(abs(dif_list_len_u)):
            k = 20+i*5
            new_m_value = m_prime_u[k]+(m_prime_u[k+1]-m_prime_u[k])/2
            m_prime_u.insert(k+1, new_m_value)
            new_Rtheta_value = R_theta_s_prime_u[k]+(R_theta_s_prime_u[k+1]-R_theta_s_prime_u[k])/2
            R_theta_s_prime_u.insert(k+1, new_Rtheta_value)

    dif_list_len_l = len(m_prime_l)-125
    
    if dif_list_len_l > 0:
        for i in range(dif_list_len_l):
            k = 20+i*5
            del m_prime_l[k]
            del R_theta_s_prime_l[k]

    elif dif_list_len_l < 0:
        for i in range(abs(dif_list_len_l)):
            k = 20+i*5
            new_m_value = m_prime_l[k]+(m_prime_l[k+1]-m_prime_l[k])/2
            m_prime_l.insert(k+1, new_m_value)
            new_Rtheta_value = R_theta_s_prime_l[k]+(R_theta_s_prime_l[k+1]-R_theta_s_prime_l[k])/2
            R_theta_s_prime_l.insert(k+1, new_Rtheta_value)
    
    # calculation of the second blade row
    m_LE = m_cntr_0_5-(m_cntr_0_5-m_LE_0_5)*(1+cubspline(3, rel_h, h_H, x_LE))
    m_TE = m_cntr_0_5+(m_cntr_0_5-m_LE)*(1-m_prime_cntr)/m_prime_cntr
    
    s = (m_TE-m_LE)*s_star

    R_LE = intpol(m_LE, len(m_prime_values[0]), m_prime_values[0], r_values[0]) + 0.5*(intpol(m_LE,len(m_prime_values[4]), m_prime_values[4], r_values[4]) -intpol(m_LE, len(m_prime_values[0]), m_prime_values[0], r_values[0])) 
    t_s_s_star = s_star*2*Pi*R_LE/(z[0]*s)
    m_star, m_star_u, m_star_l, R_theta_s_star, R_theta_s_star_u, R_theta_s_star_l = [], [], [], [], [], []
    for i in range(len(m_prime)):
        m_star.append((m_prime[i]-m_prime_cntr)*s/s_star+m_cntr_0_5)
        m_star_u.append((m_prime_u[i]-m_prime[i])*s/s_star+m_star[i])
        m_star_l.append((m_prime_l[i]-m_prime[i])*s/s_star+m_star[i])
        R_theta_s_star.append((R_theta_s_prime[i]-Rtet_prime_cntr)*s/s_star)
        R_theta_s_star_u.append((R_theta_s_prime_u[i]-Rtet_prime_cntr)*s/s_star)
        R_theta_s_star_l.append((R_theta_s_prime_l[i]-Rtet_prime_cntr)*s/s_star)
    
    chord = math.sqrt((m_TE-m_LE)**2+(R_theta_s_star[0]-R_theta_s_star[-1])**2)
   
    R_theta_s_prime_2, R_theta_s_prime_2_u, R_theta_s_prime_2_l = [], [], []
    for i in range(len(R_theta_s_prime_u)):
        R_theta_s_prime_2.append(R_theta_s_prime[i]-t_s_s_star)
        R_theta_s_prime_2_u.append(R_theta_s_prime_u[i]-t_s_s_star)
        R_theta_s_prime_2_l.append(R_theta_s_prime_l[i]-t_s_s_star)
    
    R_theta_s_star_2, R_theta_s_star_u_2, R_theta_s_star_l_2 = [], [], []
    for i in range(len(m_prime)):
        R_theta_s_star_2.append((R_theta_s_prime_2[i]-Rtet_prime_cntr)*s/s_star)
        R_theta_s_star_u_2.append((R_theta_s_prime_2_u[i]-Rtet_prime_cntr)*s/s_star)
        R_theta_s_star_l_2.append((R_theta_s_prime_2_l[i]-Rtet_prime_cntr)*s/s_star) 

    return chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2

#R, x, y, and z coordinates for h/H = [0.0, 0.2, 0.5, 0.8, 1.0] 
def coordinates(row):
    
    '''
    Defining coordinates for all stages
    '''
    stage = (row - 1) // 2 + 1
    x_values = channel_data[stage]['x_values']
    r_values = channel_data[stage]['r_values']
    m_prime_values = channel_data[stage]['m_prime_values']
    
    
    R_u, x_u, y_u, z_u, R_l, x_l, y_l, z_l = [], [], [], [], [], [], [], []
    R_theta_s_star_u, R_theta_s_star_l, beta_S, m_star_l,m_star_u = [], [], [], [], []

    for i in range(len(h_H)):
        if h_H[i] == 0.0:
            k = 0
        elif h_H[i] == 0.2:
            k = 1
        elif h_H[i] == 0.5:
            k = 2
        elif h_H[i] == 0.8:
            k = 3
        elif h_H[i] == 1.0:
            k = 4

        chord, m_star_i, R_theta_s_star_i, m_star_u_i, R_theta_s_star_u_i, m_star_l_i, R_theta_s_star_l_i, m_prime, m_prime_u, m_prime_l, m_BP, beta_S_i, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(h_H[i], row)
        R_theta_s_star_u.extend(R_theta_s_star_u_i)
        R_theta_s_star_l.extend(R_theta_s_star_l_i)
        beta_S.extend(beta_S_i)
        

        for j in range(len(m_star_u_i)):
            R_u.append(intpol(m_star_u_i[j], len(r_values[k]), m_prime_values[k], r_values[k]))
            R_l.append(intpol(m_star_l_i[j], len(r_values[k]), m_prime_values[k], r_values[k]))
            x_u.append(intpol(m_star_u_i[j], len(x_values[k]), m_prime_values[k], x_values[k]))
            x_l.append(intpol(m_star_l_i[j], len(x_values[k]), m_prime_values[k], x_values[k]))
            y_u.append(R_u[-1] * math.cos(R_theta_s_star_u_i[j] / R_u[-1]))
            y_l.append(R_l[-1] * math.cos(R_theta_s_star_l_i[j] / R_l[-1]))
            z_u.append(R_u[-1] * math.sin(R_theta_s_star_u_i[j] / R_u[-1]))
            z_l.append(R_l[-1] * math.sin(R_theta_s_star_l_i[j] / R_l[-1]))
    debug_log.debug(f"  TRACE coordinates [{row}]: x_values[0][0]={x_values[0][0]:.4f} x_values[0][-1]={x_values[0][-1]:.4f}  r_values[0][0]={r_values[0][0]:.6f} r_values[0][-1]={r_values[0][-1]:.6f}  r_values[4][0]={r_values[4][0]:.6f} r_values[4][-1]={r_values[4][-1]:.6f}")
    debug_log.debug(f"  TRACE coordinates [{row}]: R_u[0]={R_u[0]:.6f} R_u[124]={R_u[124]:.6f} R_u[125]={R_u[125]:.6f} R_u[499]={R_u[499]:.6f} R_u[500]={R_u[500]:.6f} R_u[624]={R_u[624]:.6f}")
    debug_log.debug(f"  TRACE coordinates [{row}]: x_u[0]={x_u[0]:.4f} x_u[124]={x_u[124]:.4f} x_u[125]={x_u[125]:.4f} x_u[499]={x_u[499]:.4f} x_u[500]={x_u[500]:.4f} x_u[624]={x_u[624]:.4f}")
    
    return x_u, R_theta_s_star_u, x_l, R_theta_s_star_l, R_u, beta_S

#calculation of stage_new.dat values
def calculate_m_prime_new(j_prime):
    poly_expression = 7.5613 * (j_prime ** 6) - 19.232 * (j_prime ** 5) + 14.97 * (j_prime ** 4) - 3.2001 * (j_prime ** 3) + 0.6354 * (j_prime ** 2) + 0.2687 * j_prime
    return min(poly_expression, 1)

#for Multall, we need j_prime_max sets of values of the blade by interpolation 
def calculation_blade_coordinates(j_prime_max, row):

    n_B = []                                                            
    for i in range(1, j_prime_max + 1):
        n_B.append(float(i))

    j_prime, m_prime_new = [], []
    for i in range(len(n_B)):
        j_prime.append((n_B[i]-1)/(j_prime_max-1))
        m_prime_new.append(calculate_m_prime_new(j_prime[i]))
     
    x_u, R_theta_s_star_u, x_l, R_theta_s_star_l, R_u, beta_S = coordinates(row) 
    debug_log.debug(f"  DEBUG calculation_blade_coordinates [{row}]: x_u[0]={x_u[0]:.4f}, x_u[124]={x_u[124]:.4f}, x_u[125]={x_u[125]:.4f}, len(x_u)={len(x_u)}")
    
    
    x_sec, Rtheta_sec, d_sec, R_sec = [], [], [], []
    for i in range(len(h_H)):
        x_sec.append([])
        Rtheta_sec.append([])
        d_sec.append([])
        R_sec.append([])
        
    for i in range(len(h_H)):          
        chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u_, m_star_l, R_theta_s_star_l_, m_prime_0_0, m_prime_u, m_prime_l, m_BP, beta_S_0_0, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2= calculation_of_section(h_H[i], row)
        
        delt_x_u = m_prime_u[-1]-m_prime_u[0]
        delt_x_l = m_prime_l[-1]-m_prime_l[0]
        m_prime_upper, m_prime_lower = [], []
        for k in range(len(m_prime_u)):    
            mu0 = m_prime_u[0]
            m_prime_upper.append((m_prime_u[k]-mu0)/delt_x_u) 
            ml0 = m_prime_l[0]
            m_prime_lower.append((m_prime_l[k]-ml0)/delt_x_l)

        for j in range(0, j_prime_max):
            a = int(125*i)
            b = int(125+125*i)

            x_sec_value = intpol(m_prime_new[j], len(m_prime_upper), m_prime_upper, x_u[a:b])/1000
            Rtheta_sec_value = intpol(m_prime_new[j], len(m_prime_upper), m_prime_upper, R_theta_s_star_u[a:b])/1000

            # DIAGNOSTIC: check intpol for out-of-range (sentinel -99999)
            if x_sec_value < -99990:
                debug_log.debug(f"  DIAG: intpol x_sec FAIL at i={i} j={j} row={row} m_prime_new={m_prime_new[j]:.6f} range=[{m_prime_upper[0]:.6f},{m_prime_upper[-1]:.6f}]")
                x_sec_value = 0.0  # fallback
            if Rtheta_sec_value < -99990:
                debug_log.debug(f"  DIAG: intpol Rtheta_sec FAIL at i={i} j={j} row={row} m_prime_new={m_prime_new[j]:.6f} range=[{m_prime_upper[0]:.6f},{m_prime_upper[-1]:.6f}]")
                Rtheta_sec_value = 0.0

            x_sec[i].append(x_sec_value)
            Rtheta_sec[i].append(Rtheta_sec_value)

            lower_intpol = intpol(m_prime_new[j], len(m_prime_lower), m_prime_lower, R_theta_s_star_l[a:b])/1000
            if lower_intpol < -99990:
                debug_log.debug(f"  DIAG: intpol Rtheta_lower FAIL at i={i} j={j} row={row} m_prime_new={m_prime_new[j]:.6f} range=[{m_prime_lower[0]:.6f},{m_prime_lower[-1]:.6f}]")
                lower_intpol = Rtheta_sec[i][j]  # fallback => d_sec=0
            d_sec_value = Rtheta_sec[i][j] - lower_intpol

            if d_sec_value < 0:
                debug_log.debug(f"  DIAG: NEGATIVE d_sec at row={row} i={i} j={j} d_sec={d_sec_value:.10f} Rtheta_sec={Rtheta_sec[i][j]:.10f} lower={lower_intpol:.10f} m_prime_new={m_prime_new[j]:.6f}")

            R_sec_value = intpol(m_prime_new[j], len(m_prime_upper), m_prime_upper, R_u[a:b])/1000
            if R_sec_value < -99990:
                debug_log.debug(f"  DIAG: intpol R_sec FAIL at i={i} j={j} row={row} m_prime_new={m_prime_new[j]:.6f} range=[{m_prime_upper[0]:.6f},{m_prime_upper[-1]:.6f}]")
                R_sec_value = 0.0

            d_sec[i].append(d_sec_value)
            R_sec[i].append(R_sec_value)
    
    for i in range(len(h_H)):
        d_max = max(d_sec[i])
        d_max_idx = d_sec[i].index(d_max)
        d_mid = d_sec[i][len(d_sec[i])//2]
        debug_log.debug(f"  TRACE calc_blade_coords [{row}] section {i}: x_sec[0]={x_sec[i][0]:.6f} x_sec[-1]={x_sec[i][-1]:.6f}  d_sec max={d_max:.6f} at idx={d_max_idx} mid={d_mid:.6f}  Rtheta_sec[0]={Rtheta_sec[i][0]:.6f} Rtheta_sec[-1]={Rtheta_sec[i][-1]:.6f}")

    return x_sec, d_sec, R_sec, Rtheta_sec, beta_S, j_prime_max

# calculation of inlet coordinates
def inlet_coordinates(row, num_planes, n_max_in, l_inlet, x_sec, d_sec, R_sec, Rtheta_sec, beta_S, j_prime_max):   
    
    '''
    Defining coordinates for all stages
    '''
    stage = (row - 1) // 2 + 1
    x0 = channel_data[stage]['x0']    
    x_values = channel_data[stage]['x_values']
    r_values = channel_data[stage]['r_values']
    
     
    
    DX_in, DX1_in = [], []

    Rtheta_in_BP, Rtheta_in, Rtheta_prime_in_BP, Rtheta_prime_in, dx_in, l_in, x_in, R_in, d_in = [], [], [], [], [], [], [], [], []
    for _ in range(num_planes):
        Rtheta_in_BP.append([])
        Rtheta_in.append([])
        Rtheta_prime_in_BP.append([])
        Rtheta_prime_in.append([])
        dx_in.append([])
        l_in.append([])
        x_in.append([])
        R_in.append([])
        d_in.append([])
    
    if  row % 2 != 0:
        k = 0
    elif row % 2 == 0:
        k = 3

    # First pass: compute raw DX_in
    for i in range(num_planes):
        DX_in.append(x0[k]/1000 - x_sec[i][0])
        DX1_in.append(x_sec[i][1] - x_sec[i][0])

    # Clamp DX_in for internal stages where x0[0]=x0[1] (no inlet duct).
    # Without this, DX_in ≈ 0 causes division by zero in a_in and
    # Rtheta_prime_in_BP. The clamped value guarantees the cosine-bunching
    # formula works while keeping the overlap negligible (~5 mm per stage).
    for i in range(num_planes):
        chord_approx = abs(x_sec[i][-1] - x_sec[i][0])  # blade chord in meters
        min_inlet = max(chord_approx * 0.05, 0.005)     # at least 5 mm or 5% chord
        if abs(DX_in[i]) < min_inlet:
            DX_in[i] = -min_inlet   # negative = upstream of LE

    # Second pass: compute Rtheta_prime_in_BP using adjusted DX_in
    for i in range(num_planes):
        x = max(Rtheta_sec[0][0], Rtheta_sec[4][0])*2.2
        Rtheta_in_BP[i].append(x)
        Rtheta_in_BP[i].append(x)
        Rtheta_in_BP[i].append(Rtheta_sec[i][0])
        Rtheta_prime_in_BP[i].append(Rtheta_in_BP[i][0]/abs(DX_in[i]))
        Rtheta_prime_in_BP[i].append(Rtheta_in_BP[i][0]/abs(DX_in[i]))
        y = Rtheta_in_BP[i][2]/abs(DX_in[i])
        Rtheta_prime_in_BP[i].append(y+1/math.tan(beta_S[0+125*i]/180*Pi)*(-1/3))       
        Rtheta_prime_in_BP[i].append(y)

    for i in range(num_planes):
        for j in range(n_max_in):
            d_in[i].append(0.0)

    a_in, b_in = [], []
    for i in range(num_planes): 
        a_in.append(abs(DX1_in[i]/DX_in[i]))
        b_in.append(2*((l_inlet-a_in[i])/(n_max_in-2)-a_in[i]))

    n_in = []                                                            
    for i in range(1, n_max_in + 1):
        n_in.append(float(i))

    n_in_prime = []
    for i in range(len(n_in)):
        n_in_prime.append((n_in[i]-1)/(n_max_in-1))

    for i in range(num_planes):
        for j in range(len(n_in)):
            dx_in[i].append(a_in[i]+0.5*(1-math.cos(Pi*(1-n_in_prime[j])))*b_in[i])

    for i in range(num_planes):
        l_in[i].append(0.0)
        for j in range(1, len(n_in)):
            l_in[i].append(dx_in[i][j]+l_in[i][-1])

    for i in range(num_planes):
        for j in range(len(n_in)):
            Rtheta_in[i].append(bezier(4, l_in[i][j], Rtheta_prime_in_BP[i])*abs(DX_in[i]))
            x_in[i].append(x_sec[i][0]+DX_in[i]*(1-l_in[i][j]))
            R_in[i].append(intpol(round(x_in[i][j]*1000, 10), len(x_values[i]), x_values[i], r_values[i])/1000)  

    for i in range(num_planes):
        x_in[i] = x_in[i][:-1] 
        R_in[i] = R_in[i][:-1] 
        d_in[i] = d_in[i][:-1] 
        Rtheta_in[i] = Rtheta_in[i][:-1] 

    for i in range(num_planes):
        dx_val = DX_in[i] if i < len(DX_in) else 0
        debug_log.debug(f"  TRACE inlet_coords [{row}] plane {i}: DX_in={dx_val:.6f}  x_in[0]={x_in[i][0]:.6f} x_in[-1]={x_in[i][-1]:.6f}  R_in[0]={R_in[i][0]:.6f} R_in[-1]={R_in[i][-1]:.6f}  Rtheta_in[0]={Rtheta_in[i][0]:.6f} Rtheta_in[-1]={Rtheta_in[i][-1]:.6f}  d_in all zero={all(v==0.0 for v in d_in[i])}")
    
    return x_in, d_in, R_in, Rtheta_in

# calculation of outlet coordinates
def outlet_coordinates(row, n_max_out, l_outlet, num_planes, x_sec, Rtheta_sec, beta_S):
    '''
    Defining coordinates for all stages
    '''
    stage = (row - 1) // 2 + 1
    x0 = channel_data[stage]['x0']
    x_values = channel_data[stage]['x_values']
    r_values = channel_data[stage]['r_values']
    
    
    
    
    DX_out, DX1_out = [], []
    Rtheta_out_BP, Rtheta_out, Rtheta_prime_out_BP, Rtheta_prime_out, dx_out, l_out, x_out, R_out, d_out = [], [], [], [], [], [], [], [], []
    for _ in range(num_planes):
        Rtheta_out_BP.append([])
        Rtheta_out.append([])
        Rtheta_prime_out_BP.append([])
        Rtheta_prime_out.append([])
        dx_out.append([])
        l_out.append([])
        x_out.append([])
        R_out.append([])
        d_out.append([])

    if row % 2 != 0:
        k = 3       
    elif row % 2 == 0:
        k = 6    

    # Full x0 array for channel geometry overview
    debug_log.debug(
        f"DX_out row={row} stage={stage} k={k}: "
        f"x0={[round(v,1) for v in x0]}  "
        f"x0[{k}]={x0[k]:.1f}mm  "
        f"n_max_out={n_max_out}  l_outlet={l_outlet}",
        context="outlet_debug")

    # DIAGNOSTIC: compare blade chord vs channel chord for stators
    if row % 2 == 0:
        _l_S = radial_data_S[stage]['l_S']
        debug_log.debug(
            f"  CHORD DIAG row={row}: l_S[10]={_l_S[10]:.3f}mm  "
            f"x0[5]={x0[5]:.1f} x0[6]={x0[6]:.1f}  "
            f"channel_axial={x0[6]-x0[5]:.1f}mm  "
            f"blade_TE_midspan={x0[5]+_l_S[10]:.1f}mm  "
            f"overshoot={x0[5]+_l_S[10]-x0[6]:+.1f}mm",
            context="outlet_debug")
    elif row % 2 != 0:
        _l_R = radial_data_R[stage]['l_R']
        debug_log.debug(
            f"  CHORD DIAG row={row}: l_R[10]={_l_R[10]:.3f}mm  "
            f"x0[2]={x0[2]:.1f} x0[3]={x0[3]:.1f}  "
            f"channel_axial={x0[3]-x0[2]:.1f}mm  "
            f"blade_TE_midspan={x0[2]+_l_R[10]:.1f}mm  "
            f"overshoot={x0[2]+_l_R[10]-x0[3]:+.1f}mm",
            context="outlet_debug")

    for i in range(num_planes):
        s = len(x_sec[i])-1
        
        DX_out.append(x0[k]/1000-x_sec[i][s])
        DX1_out.append(x_sec[i][s]-x_sec[i][s-1])

        d_val = DX_out[-1]
        x_sec_last_mm = x_sec[i][s] * 1000
        status = ""
        if d_val < 0:
            status = " *** NEGATIVE: blade TE past channel exit ***"
        elif d_val < 0.005:
            status = f" *** VERY SMALL: only {d_val*1000:.1f}mm for {n_max_out} outlet points ***"
        debug_log.debug(
            f"DX_out row={row} sec={i}: "
            f"x0[{k}]={x0[k]:.1f}mm  x_sec_TE={x_sec_last_mm:.3f}mm  "
            f"DX_out={d_val*1000:.3f}mm  n_max_out={n_max_out}{status}",
            context="outlet_debug")
        x = Rtheta_sec[i][s]
        Rtheta_out_BP[i].append(x)
        Rtheta_out_BP[i].append(x+1/math.tan(beta_S[124+125*i]/180*Pi)*DX_out[i])
        Rtheta_prime_out_BP[i].append(Rtheta_out_BP[i][0]/abs(DX_out[i]))
        Rtheta_prime_out_BP[i].append(Rtheta_out_BP[i][1]/abs(DX_out[i]))

    for i in range(num_planes):
        for j in range(n_max_out):
            d_out[i].append(0.0)

    a_out, b_out = [], []
    for i in range(num_planes): 
        a_out.append(abs(DX1_out[i]/DX_out[i]))
        b_out.append(2*((l_outlet-a_out[i])/(n_max_out-2)-a_out[i]))

    n_out = []                                                            
    for i in range(1, n_max_out + 1):
        n_out.append(float(i))

    n_out_prime = []
    for i in range(len(n_out)):
        n_out_prime.append((n_out[i]-1)/(n_max_out-1))

    for i in range(num_planes):
        for j in range(len(n_out)):
            dx_out[i].append(a_out[i]+0.5*(1-math.cos(Pi*n_out_prime[j]))*b_out[i])

    for i in range(num_planes):
        l_out[i].append(0.0)
        for j in range(len(n_out)-1):
            l_out[i].append(dx_out[i][j]+l_out[i][-1])

    for i in range(num_planes):
        for j in range(len(n_out)):
            Rtheta_out[i].append((Rtheta_out_BP[i][1] - Rtheta_out_BP[i][0])*l_out[i][j] + Rtheta_out_BP[i][0])
            x_out[i].append(x_sec[i][s] + DX_out[i]*l_out[i][j])
            R_out[i].append(intpol(round(x_out[i][j]*1000, 10), len(r_values[i]), x_values[i], r_values[i])/1000) 
     
    for i in range(num_planes):
        x_out[i] = x_out[i][1:] 
        R_out[i] = R_out[i][1:]
        d_out[i] = d_out[i][1:]
        Rtheta_out[i] = Rtheta_out[i][1:]

    for i in range(num_planes):
        debug_log.debug(f"  TRACE outlet_coords [{row}] plane {i}: DX_out={DX_out[i]:.6f}  x_out[0]={x_out[i][0]:.6f} x_out[-1]={x_out[i][-1]:.6f}  R_out[0]={R_out[i][0]:.6f} R_out[-1]={R_out[i][-1]:.6f}  Rtheta_out[0]={Rtheta_out[i][0]:.6f} Rtheta_out[-1]={Rtheta_out[i][-1]:.6f}")
    
    return x_out, d_out, R_out, Rtheta_out

# merging of inlet, blade and outlet coordinates
def merge_coordinates(num_planes, j_prime_max, n_max_in, x_in, x_sec, x_out, d_in, d_sec, d_out, R_in, R_sec, R_out, Rtheta_in, Rtheta_sec, Rtheta_out):
    #Now all values from inlet, blade and outlet are put in one list
    x, Rtheta, d, R =  [], [], [], []
    x_sec_s, Rtheta_sec_s = [], []
    for _ in range(num_planes):
        x.append([])
        Rtheta.append([])
        d.append([])
        R.append([])
        x_sec_s.append([])
        Rtheta_sec_s.append([])

    for i in range(5):
        for j in range(len(x_sec[i])):
            x_sec_s[i].append(x_sec[i][j]*1000)     
            Rtheta_sec_s[i].append(Rtheta_sec[i][j]*1000)     
    
    sehnenlaenge = []
    for i in range(5):
        sehnenlaenge.append(math.sqrt((x_sec[i][0]-x_sec[i][-1])**2+(Rtheta_sec[i][0]-Rtheta_sec[i][-1])**2)*1000)

    for i in range(num_planes):
        x[i] = x_in[i]+x_sec[i]+x_out[i]
        Rtheta[i] = Rtheta_in[i]+Rtheta_sec[i]+Rtheta_out[i]
        d[i] = d_in[i]+d_sec[i]+d_out[i]
        R[i] = R_in[i]+R_sec[i]+R_out[i]
    
    return x, d, R, Rtheta 

# There are 5 sets of coordinates. For better interpolation, we create two additional sets, one at the hub and one at the shroud.
def additional_section(Z_H, Z_S, x, d, R, Rtheta):
    R_0_05, X_0_05, Rtheta_0_05, d_0_05 = [], [], [], [] 
    for i in range(len(R[0])):
        XN = [R[0][i], R[1][i]]
        N = len(XN)
        Z = (R[4][i]-R[0][i])*Z_H + R[0][i]
        A = [x[0][i], x[1][i]]
        B = [Rtheta[0][i], Rtheta[1][i]]
        C = [d[0][i], d[1][i]]
        D = [R[0][i], R[1][i]]
        X_0_05.append(intp_new(2, N, XN, A, Z))
        Rtheta_0_05.append(intp_new(2, N, XN, B, Z))
        d_0_05.append(intp_new(2 ,N, XN, C, Z))
        R_0_05.append(intp_new(2, N, XN, D, Z))

    R_0_95, X_0_95, Rtheta_0_95, d_0_95 = [], [], [], [] 
    Z_S = 0.95
    for i in range(len(R[0])):
        XN = [R[3][i], R[4][i]]
        N = len(XN)
        Z = (R[4][i]-R[0][i])*Z_S + R[0][i]
        A = [x[3][i], x[4][i]]
        B = [Rtheta[3][i], Rtheta[4][i]]
        C = [d[3][i], d[4][i]]
        D = [R[3][i], R[4][i]]  
        X_0_95.append(intp_new(2, N, XN, A, Z))
        Rtheta_0_95.append(intp_new(2, N, XN, B, Z))
        d_0_95.append(intp_new(2 ,N, XN, C, Z))
        R_0_95.append(intp_new(2, N, XN, D, Z))

    #Inserts the new two planes in the old lists
    # Z_H (h=0.05) goes between hub (h=0.0, idx 0) and section 1 (h=0.20, idx 1)
    x.insert(1, X_0_05)
    Rtheta.insert(1, Rtheta_0_05)
    d.insert(1, d_0_05)
    R.insert(1, R_0_05)
    # After the Z_H insert, sections are: [0]=h0.0, [1]=h0.05, [2]=h0.20, [3]=h0.50, [4]=h0.80, [5]=h1.0
    # Z_S (h=0.95) goes between h=0.80 (idx 4) and h=1.0 (idx 5) → insert at index 5
    x.insert(5, X_0_95)
    Rtheta.insert(5, Rtheta_0_95)
    d.insert(5, d_0_95)
    R.insert(5, R_0_95)

    for i in range(len(R)):
        radii_at_inlet = [R[sec][0] for sec in range(len(R))]
        radii_monotonic = all(radii_at_inlet[k] <= radii_at_inlet[k+1] for k in range(len(radii_at_inlet)-1))
        if i == 0:
            debug_log.debug(f"  Section ordering: radii at inlet = {[f'{r:.4f}' for r in radii_at_inlet]}  monotonic={radii_monotonic}")
    
    return x, d, R, Rtheta

# coordinates for every selected value in levels by interpolation
def coordinates_levels(levels, x, d, R, Rtheta):
    #creating new liste for all interpolated sections
    x_new, Rtheta_new, d_new, R_new = [], [], [], []
    for _ in range(len(levels)):
        x_new.append([])
        Rtheta_new.append([])
        d_new.append([])
        R_new.append([])

    #calculation of new sections:
    for j in range(len(levels)):
        element = levels[j]        
        for i in range(len(R[0])):
            XN = [R[0][i], R[1][i], R[2][i], R[3][i], R[4][i], R[5][i], R[6][i]]
            N = len(XN)
            Z = (R[6][i]-R[0][i])*element + R[0][i]
            A = [x[0][i], x[1][i], x[2][i], x[3][i], x[4][i], x[5][i], x[6][i]]
            B = [Rtheta[0][i], Rtheta[1][i], Rtheta[2][i], Rtheta[3][i], Rtheta[4][i],Rtheta[5][i], Rtheta[6][i]]
            C = [d[0][i], d[1][i], d[2][i], d[3][i], d[4][i], d[5][i], d[6][i]]
            D = [R[0][i], R[1][i], R[2][i], R[3][i], R[4][i], R[5][i], R[6][i]]
            x_new[j].append(intp_new(2, N, XN, A, Z))
            Rtheta_new[j].append(intp_new(2, N, XN, B, Z))
            d_new[j].append(intp_new(2, N, XN, C, Z))
            R_new[j].append(intp_new(2, N, XN, D, Z))
        
    return x_new, d_new, R_new, Rtheta_new

# function for calculation of blade row coordinates. It just activates other functions
def calc_blade_row_coordinates(row, j_prime_max, num_planes, n_max_in, l_inlet, n_max_out, l_outlet, Z_H, Z_S, levels):
    x_sec, d_sec, R_sec, Rtheta_sec, beta_S, j_prime_max = calculation_blade_coordinates(j_prime_max, row) 
    x_in, d_in, R_in, Rtheta_in = inlet_coordinates(row, num_planes, n_max_in, l_inlet, x_sec, d_sec, R_sec, Rtheta_sec, beta_S, j_prime_max) 
    x_out, d_out, R_out, Rtheta_out = outlet_coordinates(row, n_max_out, l_outlet, num_planes, x_sec, Rtheta_sec, beta_S)
    x, d, R, Rtheta = merge_coordinates(num_planes, j_prime_max, n_max_in, x_in, x_sec, x_out, d_in, d_sec, d_out, R_in, R_sec, R_out, Rtheta_in, Rtheta_sec, Rtheta_out)
    
    for i in range(num_planes):
        debug_log.debug(f"  TRACE merged [{row}] plane {i}: x[0]={x[i][0]:.6f} x[-1]={x[i][-1]:.6f}  R[0]={R[i][0]:.6f} R[-1]={R[i][-1]:.6f}  d[0]={d[i][0]:.6f} d[-1]={d[i][-1]:.6f}  Rtheta[0]={Rtheta[i][0]:.6f} Rtheta[-1]={Rtheta[i][-1]:.6f}")
    
    x, d, R, Rtheta = additional_section(Z_H, Z_S, x, d, R, Rtheta)
    x_new, d_new, R_new, Rtheta_new = coordinates_levels(levels, x, d, R, Rtheta )
    
    for j in range(len(levels)):
        stats = []
        for name, arr in [('x', x_new[j]), ('d', d_new[j]), ('R', R_new[j]), ('Rt', Rtheta_new[j])]:
            n_nan = sum(1 for v in arr if v != v)
            n_inf = sum(1 for v in arr if v == float('inf') or v == -float('inf'))
            if n_nan or n_inf:
                stats.append(f"{name}:{len(arr)}pts nan={n_nan} inf={n_inf}")
            n_neg = sum(1 for v in arr if v < 0)
            if name != 'Rt' and n_neg:
                stats.append(f"{name}:{len(arr)}pts neg={n_neg}")
        if stats:
            debug_log.debug(f"  TRACE final [{row}] level {j}: *** INVALID *** {' | '.join(stats)}", context="INVALID")
        else:
            debug_log.debug(f"  TRACE final [{row}] level {j}: x[0]={x_new[j][0]:.6f} x[-1]={x_new[j][-1]:.6f}  R[0]={R_new[j][0]:.6f} R[-1]={R_new[j][-1]:.6f}  d[0]={d_new[j][0]:.6f} d[-1]={d_new[j][-1]:.6f}  Rtheta[0]={Rtheta_new[j][0]:.6f} Rtheta[-1]={Rtheta_new[j][-1]:.6f}")
            # Log negative Rtheta count as informational (not INVALID) — negative Rtheta
            # is physically correct when the blade turns past the zero-Rtheta reference
            n_neg_rt = sum(1 for v in Rtheta_new[j] if v < 0)
            if n_neg_rt:
                debug_log.debug(f"  TRACE final [{row}] level {j}: Rt negative count={n_neg_rt}/{len(Rtheta_new[j])} (informational — physically correct for blades turning past zero reference)", context="Rt_negative_info")
    
    return x_new, d_new, R_new, Rtheta_new


## Functions that write the file for MULTALL
#writes coordinates in the right format
def write_values_in_block(section, liste, file, JM):
    for k in range(0, JM, 8):
        zeile = liste[section][k:k+8]
        file.write(' ')
        for element in zeile:
            if element < 0.0:
                file.write(f"{element:.6f} ")
            else:
                file.write(' ')
                file.write(f"{element:.6f} ")
        file.write('\n')  

# MULTALL section geometry writer for a blade row.
# MULTALL format expects per section:
#   1. x-coordinates
#   2. 1.000000  0.000000
#   3. d-surface-1 (R*theta for one blade surface, e.g. upper/suction)
#   4. 1.000000
#   5. d-surface-2 (R*theta for the OTHER blade surface, e.g. lower/pressure)
#   6. 1.000000  0.000000
# ===== DEAD CODE =====
# This function is superseded by grid_generator.py:337 write_coordinates()
# which correctly writes blade thickness d in block 5 (as MULTALL expects).
# The version below wrote rtheta_lower (= upper - thickness) instead, which
# caused MULTALL to interpret thickness as a second surface, breaking the
# passage width calculation. See grid_generator.py for the active implementation.
# =====================
# def write_coordinates(x, rtheta, d, r, file, row, a, b, JM):
#     rtheta_lower = []
#     for sec_idx in range(len(rtheta)):
#         rtheta_lower.append([rtheta[sec_idx][k] - d[sec_idx][k] for k in range(len(rtheta[sec_idx]))])
#     
#     with open(file, "a") as file:
#         for i in range(a, b):       
#             file.write(" ***************************************************************\n")
#             file.write(f"  ROW NUMBER           {row}  SECTION NUMBER            {i+1}\n           0           0           0  IF_DESIGN etc \n   1.00000   0.00000    0\n")
#             write_values_in_block(i, x, file, JM)
#             file.write("  1.000000  0.000000\n")
#             write_values_in_block(i, rtheta, file, JM)
#             file.write("  1.000000\n")
#             write_values_in_block(i, rtheta_lower, file, JM)
#             file.write("  1.000000  0.000000\n")
#             write_values_in_block(i, r, file, JM)

# (dead code — Q3D_information moved to grid_generator.py)
# def Q3D_information(file):
#     with open(file, "a") as file:
#         file.write("  DATA FOR STREAM SURFACE THICKNESS\n")
#         file.write("   1.00000000      Q3DFORCE\n")
#         file.write("           5  A UNIFORM  SS THICKNESS IS INITIALLY SET\n")
#         file.write("   0.00000000      0.250000000      0.500000000      0.750000000      1.00000000\n")
#         file.write("   1.00000000      1.00000000      1.00000000      1.00000000      1.00000000\n")     

# writes head of the file
def write_head_file(file, NSEC, NROW, section, enable_bleed_air):
    if enable_bleed_air == True:
        bleed_air = 1
    else: 
        bleed_air = 0
    with open(file, "w+") as file:
        file.write(" DATA SET FOR \"multall\" . GENERATED BY \"stagen\" .                       \n")
        file.write("    CP   and   GAMMA \n")
        file.write(f" {cp}    {kappa}\n")
        file.write("       ITIMST \n")
        file.write("         3\n")
        file.write("     CFL,    DAMP,    MACHLIM,    F_PDOWN \n")
        file.write("  0.320000 9.000000  2.000000  0.000000\n")
        file.write("  IF_RESTART \n")
        file.write("         0\n")
        file.write("  NSTEPS_MAX, CONLIM\n")
        if section == 0:
            file.write("      9000  0.005000\n")
        else: 
            file.write("      60000  0.005000\n")
        file.write("   SFX,      SFT,      FAC_4TH,     NCHANGE \n")
        file.write("  0.005000  0.005000  0.800000      1000\n")
        file.write("       NUMBER OF BLADE ROWS \n")
        file.write(f"         {NROW}\n")
        file.write("        IM        KM \n")
        
        if section == 0:
            file.write("        37        37\n")
        else:
            file.write("        37        2\n")
        
        file.write("  FP(I),I=1,IMM1 \n")
        file.write("  1.000000  1.250000  1.562500  1.953125  2.441406  3.051758  3.814697  4.768372\n")
        file.write("  5.960464  7.450581  9.313226 11.641532 14.551915 18.189894 20.000000 20.000000\n")
        file.write(" 20.000000 20.000000 20.000000 20.000000 20.000000 20.000000 18.189894 14.551915\n")
        file.write(" 11.641532  9.313226  7.450581  5.960464  4.768372  3.814697  3.051758  2.441406\n")
        file.write("  1.953125  1.562500  1.250000  1.000000\n")
        
        if section == 0:
            file.write("  FR(K),K=1,KMM1 \n")
            file.write("  1.000000  1.250000  1.562500  1.953125  2.441406  3.051758  3.814697  4.768372\n")
            file.write("  5.960464  7.450581  9.313226 11.641532 14.551915 18.189894 20.000000 20.000000\n")
            file.write(" 20.000000 20.000000 20.000000 20.000000 20.000000 20.000000 18.189894 14.551915\n")
            file.write(" 11.641532  9.313226  7.450581  5.960464  4.768372  3.814697  3.051758  2.441406\n")
            file.write("  1.953125  1.562500  1.250000  1.000000\n")
        else:
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
        file.write("  800000.0     0.500     0.000  1000.000       1.0     0.000\n")
        file.write("   YPLAM      YPTURB \n")
        file.write("  5.000000 25.000000\n")
        file.write("      ISHIFT    NEXTRAP_LE  NEXTRAP_TE \n")
        file.write("         2        10        10\n")
        file.write("  (NSTG(N),N=1,NROWS) \n")
        file.write("         1         1\n")
        file.write("  5  TIME STEPS FOR PRINTOUT \n")
        file.write("      9000      9000      9000      9000      9000\n")
        file.write("  MARKER FOR VARIABLES TO BE SENT TO THE OUTPUT FILE.\n")
        file.write(" 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
        file.write("  STREAM SURFACES ON WHICH RESULTS ARE TO BE SENT TO   THE OUTPUT FILE \n")
        file.write(" 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")

# writes head of the row
def write_head_row(file, row, JM, JLE, JTE, RPM, section, NSEC):
    
    
    '''
    ### Parameters were used as globals values and never reassigned the value. So calling the writing for the second or third stage the global parameters were still using stage one values thus writing completly wrong values 
    '''
    
    stage = (row - 1) // 2 + 1                          # ADD
    _rad = radial_data_R[stage] if row % 2 != 0 else radial_data_S[stage]  # ADD
    h_rel   = _rad['h_rel']     # shadows the global
    p_R_in  = _rad.get('p_R_in',  p_R_in)
    p_R_out = _rad.get('p_R_out', p_R_out)
    p_S_in  = _rad.get('p_S_in',  p_S_in)
    p_S_out = _rad.get('p_S_out', p_S_out)
    
    
    if section == 0:
        if row % 2 != 0:
            x = round(p_1[0], 1)
            y = round(p_2[0], 1)
            z = RPM[0]
            blades = z_R[0]
        elif row % 2 == 0:
            x = round(p_2[0], 1)
            y = round(p_3[0], 1)
            z = 0.0
            blades = z_S[0]
    else:
        if row % 2 != 0 :
            i = levels[section-1]
            for j in range(len(h_rel)):
                if round(h_rel[j],2) == i:
                    x = round(p_R_in[j], 1)
                    y = round(p_R_out[j], 1)

            z = RPM[0]
            blades = z_R[0]
        elif row % 2 == 0:
            i = levels[section-1]
            for j in range(len(h_rel)):
                if round(h_rel[j],2) == i:
                    x = round(p_S_in[j], 1)
                    y = round(p_S_out[j], 1)
            
            blades = z_S[0]
            z = 0.0

    with open(file, "a") as file:
        file.write(" ***************************************************************\n")
        file.write(" ************STARTING THE INPUT FOR EACH BLADE ROW**************\n")
        file.write(f"  BLADE ROW NUMBER =        {row}                                           \n")
        file.write("    NUMBER OF BLADES IN ROW \n")
        file.write(f"        {blades}\n")                                       
        file.write("        JM        JLE       JTE \n")
        file.write(f"       {JM}        {JLE}        {JTE}\n")
        file.write("      KTIPSTART  KTIPEND \n")
        file.write("         0         0\n")
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

# writes end of the file 
def write_end_file(row, file, section):
    
    if row % 2 != 0 :
        x = round(p_R_out[0], 1)
        y = round(p_R_out[len(h_rel)-1], 1)
        t = round(T_t1[0], 4)
        p = round(p_t1[0], 1)
        um = round(cm1[0], 4)
    
    elif row % 2 == 0:
        x = round(p_S_out[0], 1)
        y = round(p_S_out[len(h_rel)-1], 1)
        t = round(T_t1[0], 4)
        p = round(p_t1[0], 1)
        um = round(cm1[0], 4)
        
    with open(file, "a") as file:
        if section == 0:
            file.write("  STARTING INLET BOUNDARY CONDITION DATA .\n")
            file.write("  NUMBER OF POINTS FOR INLET BOUNDARY CONDITIONS \n")
            file.write("        37\n")
            file.write("  SPACING OF INLET BOUNDARY CONDITION POINTS \n")
            file.write("  1.000000  1.250000  1.562500  1.953125  2.441406  3.051758  3.814697  4.768372\n")
            file.write("  5.960464  7.450581  9.313226 11.641532 14.551915 18.189894 20.000000 20.000000\n")
            file.write(" 20.000000 20.000000 20.000000 20.000000 20.000000 20.000000 18.189894 14.551915\n")
            file.write(" 11.641532  9.313226  7.450581  5.960464  4.768372  3.814697  3.051758  2.441406\n")
            file.write("  1.953125  1.562500  1.250000  1.000000\n")
            file.write("   INLET STAGNATION PRESSURES \n")
            file.write(f"  {p}  {p}  {p}  {p}  {p}  {p}  {p}  {p}\n")
            file.write(f"  {p}  {p}  {p}  {p}  {p}  {p}  {p}  {p}\n")
            file.write(f"  {p}  {p}  {p}  {p}  {p}  {p}  {p}  {p}\n")
            file.write(f"  {p}  {p}  {p}  {p}  {p}  {p}  {p}  {p}\n")
            file.write(f"  {p}  {p}  {p}  {p}  {p}\n")
            file.write("   INLET STAGNATION TEMPERATURES \n")
            file.write(f"  {t}  {t}  {t}  {t}  {t}  {t}  {t}  {t}\n")
            file.write(f"  {t}  {t}  {t}  {t}  {t}  {t}  {t}  {t}\n")
            file.write(f"  {t}  {t}  {t}  {t}  {t}  {t}  {t}  {t}\n")
            file.write(f"  {t}  {t}  {t}  {t}  {t}  {t}  {t}  {t}\n")
            file.write(f"  {t}  {t}  {t}  {t}  {t}\n")
            file.write("   INLET ABSOLUTE TANGENTIAL VELOCITY \n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("   INLET MERIDIONAL VELOCITY \n")
            file.write(f"  {um}  {um}  {um}  {um}  {um}  {um}  {um}  {um}\n")
            file.write(f"  {um}  {um}  {um}  {um}  {um}  {um}  {um}  {um}\n")
            file.write(f"  {um}  {um}  {um}  {um}  {um}  {um}  {um}  {um}\n")
            file.write(f"  {um}  {um}  {um}  {um}  {um}  {um}  {um}  {um}\n")
            file.write(f"  {um}  {um}  {um}  {um}  {um}\n")
            file.write("   INLET MERIDIONAL YAW ANGLE \n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("   INLET PITCH ANGLE \n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("    0.0000    0.0000    0.0000    0.0000    0.0000\n")
            file.write("   PDOWN_HUB   PDOWN_TIP \n")
            file.write(f"  {x}  {y}\n")
            file.write(" MIXING LENGTH LIMITS ON ALL BLADE ROWS\n")
            file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            file.write("  0.030000  0.030000  0.030000  0.030000  0.030000  0.020000\n")
            file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS \n")
            file.write("   2.00000 1000\n")
        else:         
            if row % 2 != 0:
                i = levels[section-1]
                for j in range(len(h_rel)):
                    if round(h_rel[j],2) == i:
                        x = round(p_R_out[j], 1)
                        y = round(p_R_out[j], 1)

            elif row % 2 == 0:
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
            file.write("  0.030000 0.030000 0.030000 0.030000 0.030000 0.020000\n")
            file.write("  0.030000 0.030000 0.030000 0.030000 0.030000 0.020000\n")
            file.write("  FACTOR TO INCREASE THE TURBULENT VISCOSITY OVER THE FIRST NMIXUP STEPS\n")
            file.write("   2.00000 1000\n")


#Plots the x-Rtheta of all sections in 3D:
def xRtheta_plot(Rtheta_new, R_new, x_new):
    fig = plt.figure(figsize=(10, 8))
    theta_radians = np.deg2rad(Rtheta_new)
    y_values = [r * np.cos(theta) for r, theta in zip(R_new, Rtheta_new)]
    z_values = [r * np.sin(theta) for r, theta in zip(R_new, Rtheta_new)]
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(x_new, y_values, z_values, c='r', marker='o')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()
    
# Write the Bleed Air Cards for the Multall Input File
def create_bleed_air_card(NROW, file, rotor_data, stator_data):
    debug_log.debug(f"Writing bleed air to file={file}", context="create_bleed_air_card")
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


# Class to create Tooltips
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25  
        y += self.widget.winfo_rooty() + 25     
        
        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = Label(self.tooltip_window, text = self.text, background = '#ffffe0', relief = 'solid', borderwidth = 1, font=("tahoma", '11', 'normal'), wraplength=500)
        label.pack(ipadx=1) 
        
    def hide_tooltip(self, event = None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
    

class CompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Settings for MULTALL file")
        self.meanline_data = None
        
        # Add a dictionary for storing bleedair data
        self.bleed_air_data = {
            'rotor': {'patches': [], 'count': 0},
            'stator': {'patches': [], 'count': 0}
        }
        
        # Potential error fix for attribute error
        self.rotor_patch_entries = []
        self.stator_patch_entries = []
        
        # Variables for Inlet and Outlet Adjustment
        self.inlet_area_var = tk.DoubleVar()
        self.inlet_dist_var = tk.DoubleVar()
        self.outlet_area_var = tk.DoubleVar()
        self.outlet_dist_var = tk.DoubleVar()
        
        # Create notebook for multiple pages
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create frames for each section
        self.parameters_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.parameters_frame, text="Parameters")

        self.plot_options_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_options_frame, text="Plot Options")
        
        self.bleed_air_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bleed_air_frame, text="Bleed Air")
        
        # Creat container frame for inputs for the bleed air
        self.bleed_input_container = ttk.Frame(self.bleed_air_frame)
        self.bleed_input_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.inlet_outlet_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inlet_outlet_frame, text="Define Inlet and Outlet")

        self.output_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.output_frame, text="Output")

        # Parameters Page
        self.use_default_rotor_bezier_var = tk.BooleanVar()
        self.use_default_rotor_bezier_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Use default Bezier points for rotor", variable=self.use_default_rotor_bezier_var).grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.adjust_rotor_thickness_var = tk.BooleanVar()
        self.adjust_rotor_thickness_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Adjust Bezier points of rotor for thickness distribution", variable=self.adjust_rotor_thickness_var).grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.adjust_rotor_angle_var = tk.BooleanVar()
        self.adjust_rotor_angle_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Adjust Bezier points of rotor for blade angle distribution", variable=self.adjust_rotor_angle_var).grid(row=2, column=0, padx=5, pady=5, sticky='w')

        # Add spacing between rotor and stator parameters
        ttk.Label(self.parameters_frame, text="").grid(row=3, column=0, pady=20)

        self.use_default_stator_bezier_var = tk.BooleanVar()
        self.use_default_stator_bezier_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Use default Bezier points for stator", variable=self.use_default_stator_bezier_var).grid(row=4, column=0, padx=5, pady=5, sticky='w')

        self.adjust_stator_thickness_var = tk.BooleanVar()
        self.adjust_stator_thickness_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Adjust Bezier points of stator for thickness distribution", variable=self.adjust_stator_thickness_var).grid(row=5, column=0, padx=5, pady=5, sticky='w')

        self.adjust_stator_angle_var = tk.BooleanVar()
        self.adjust_stator_angle_var.set(False)
        ttk.Checkbutton(self.parameters_frame, text="Adjust Bezier points of stator for blade angle distribution", variable=self.adjust_stator_angle_var).grid(row=6, column=0, padx=5, pady=5, sticky='w')

        # Plot Options Page
        self.show_section_plot_var = tk.BooleanVar()
        self.show_section_plot_var.set(False)
        ttk.Checkbutton(self.plot_options_frame, text="Show section plot", variable=self.show_section_plot_var).grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.show_angle_distribution_plots_var = tk.BooleanVar()
        self.show_angle_distribution_plots_var.set(False)
        ttk.Checkbutton(self.plot_options_frame, text="Show angle distribution plots", variable=self.show_angle_distribution_plots_var).grid(row=1, column=0, padx=5, pady=5, sticky='w')

        
        # Inlet and Outlet Area Definition Page
        
        
        # Bleed Air Page
        # self.enable_bleed_air_var = tk.BooleanVar(value=False)
        # self.enable_bleed_air_var.trace_add("write", self.update_bleed_air_display)
        # self.enable_bleed_air_checkbox = ttk.Checkbutton(self.bleed_air_frame, text="Enable Bleed Air", variable=self.enable_bleed_air_var)
        # self.enable_bleed_air_checkbox.pack(padx=10, pady=10, anchor='w', side='top')
        
        bleed_air_container = ttk.Frame(self.bleed_air_frame)
        bleed_air_container.pack(padx=10, pady=10, anchor='w', side='top')
        
        self.enable_bleed_air_var = tk.BooleanVar(value=False)
        self.enable_bleed_air_var.trace_add("write", self.update_bleed_air_display)
        self.enable_bleed_air_checkbox = ttk.Checkbutton(bleed_air_container, text="Enable Bleed Air", variable= self.enable_bleed_air_var)
        self.enable_bleed_air_checkbox.pack(side='left')
        
        # Add Tooltip Questionmark
        help_button = ttk.Label(bleed_air_container, text="?", cursor="question_arrow")
        help_button.pack(side='left', padx=(5, 0))
        help_text = "Coordinate Explaination"
        Tooltip(help_button, help_text)
        
        # Output Page
        output_folder_label = ttk.Label(self.output_frame, text="Output Folder Path:")
        output_folder_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.output_folder_entry = ttk.Entry(self.output_frame, width=50)
        self.output_folder_entry.grid(row=0, column=1, padx=5, pady=5)

        output_folder_browse_button = ttk.Button(self.output_frame, text="Browse", command=self.browse_output_folder)
        output_folder_browse_button.grid(row=0, column=2, padx=5, pady=5)

        levels_label = ttk.Label(self.output_frame, text="Levels:")
        levels_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        self.levels_entry = ttk.Entry(self.output_frame, width=50)
        self.levels_entry.grid(row=1, column=1, padx=5, pady=5)

        nrow_label = ttk.Label(self.output_frame, text="Number of Rows [only Rotor: '1' or 1st Stage: '2']")
        nrow_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
        
        self.nrow_entry = ttk.Entry(self.output_frame, width=10)
        self.nrow_entry.insert(0, "2")
        self.nrow_entry.grid(row=2, column=1, padx=5, pady=5)

        save_button_parameters = ttk.Button(self.parameters_frame, text="Save", command=self.save_and_initialize)
        save_button_parameters.grid(row=7, columnspan=2)

        save_button_plot_options = ttk.Button(self.plot_options_frame, text="Save", command=self.save_and_initialize)
        save_button_plot_options.grid(row=2, columnspan=2)
        
        save_button_bleed_air = ttk.Button(self.bleed_air_frame, text="Save", command=self.save_and_initialize)
        save_button_bleed_air.pack(pady=10, side='bottom')

        save_button_output_options = ttk.Button(self.output_frame, text="Save", command=self.save_and_initialize)
        save_button_output_options.grid(row=3, columnspan=3)
        
        # Define Inlet and Outlet Page
        
        inlet_outlet_title_frame = ttk.Frame(self.inlet_outlet_frame)
        inlet_outlet_title_frame.pack(fill='x', padx=10, pady=10)
        
        inlet_outlet_title_label = ttk.Label (inlet_outlet_title_frame, text="Inlet and Outlet Geometry Definition")
        inlet_outlet_title_label.pack(side='left', padx= (0, 5))
        
        inlet_outlet_help = ttk.Label(inlet_outlet_title_frame, text= "?", cursor="question_arrow")
        inlet_outlet_help.pack(side='left', padx=(5, 0))
        inlet_outlet_help_text = "Define the geometry parameters of the Inlet and Outlet Area"
        Tooltip(inlet_outlet_help, inlet_outlet_help_text)
        
        inlet_frame = ttk.LabelFrame(self.inlet_outlet_frame, text="Inlet Area Definition")
        inlet_frame.pack(fill='x', padx=10, pady=10)
        
        # Inlet 
        inlet_area_label = ttk.Label(inlet_frame, text="Inlet Area")
        inlet_area_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        # Area
        inlet_area_help = ttk.Label(inlet_frame, text= "?", cursor="question_arrow")
        inlet_area_help.grid(row=0, column=2, padx=(5, 0))
        inlet_area_help_text = "Enter the Size of the Inlet as a factor of the Diameter of the first Blade Row. Default = 1 (same Size as the Diameter of the first Blade Row)"
        Tooltip(inlet_area_help, inlet_area_help_text)
        
        self.inlet_area_entry = ttk.Entry(inlet_frame, width=10, textvariable=self.inlet_area_var)
        self.inlet_area_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Distanz
        inlet_dist_label = ttk.Label(inlet_frame, text="Inlet Distance")
        inlet_dist_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        inlet_dist_help = ttk.Label(inlet_frame, text= "?", cursor="question_arrow")
        inlet_dist_help.grid(row=1, column=2, padx=(5, 0))
        inlet_dist_help_text = "Enter the Distanz of the Inlet to the first stage as a factor of the first Blade length. Default = 2 (length between the Inlet and the first Blade Row is equal to two times the Blade length) "
        Tooltip(inlet_dist_help, inlet_dist_help_text)
        
        self.inlet_dist_entry = ttk.Entry(inlet_frame, width=10, textvariable=self.inlet_dist_var)
        self.inlet_dist_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Outlet        
        outlet_frame = ttk.LabelFrame(self.inlet_outlet_frame, text="Outlet Area Definition")
        outlet_frame.pack(fill='x', padx=10, pady=10)
        
        # Area
        outlet_area_label = ttk.Label(outlet_frame, text="Outlet Area")
        outlet_area_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        outlet_area_help = ttk.Label(outlet_frame, text= "?", cursor="question_arrow")
        outlet_area_help.grid(row=0, column=2, padx=(5, 0))
        outlet_area_help_text = "Enter the Size of the Outlet as a factor of the Diameter of the last Blade Row. Default = 1 (same Size as the Diameter of the last Blade Row)"
        Tooltip(outlet_area_help, outlet_area_help_text)
        
        self.outlet_area_entry = ttk.Entry(outlet_frame, width=10, textvariable=self.outlet_area_var)
        self.outlet_area_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Distanz
        outlet_dist_label = ttk.Label(outlet_frame, text="Outlet Distance")
        outlet_dist_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        outlet_dist_help = ttk.Label(outlet_frame, text= "?", cursor="question_arrow")
        outlet_dist_help.grid(row=1, column=2, padx=(5, 0))
        outlet_dist_help_text = "Enter the Distanz of the last Blade row to the Outlet as a factor of the last Blade length. Default = 2 (length between the last Blade Row and the Output is equal to two times the Blade length) "
        Tooltip(outlet_dist_help, outlet_dist_help_text)
        
        self.outlet_dist_entry = ttk.Entry(outlet_frame, width=10, textvariable=self.outlet_dist_var)
        self.outlet_dist_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Save Button
        save_button_inlet_outlet = ttk.Button(self.inlet_outlet_frame, text="Save", command=self.save_and_initialize)
        save_button_inlet_outlet.pack(pady=10, side='bottom')

        # Load last output folder path and levels if available
        try:
            with open('Setting.txt', 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('output_folder = '):
                        last_output_folder = line[16:].strip()
                        self.output_folder_entry.insert(0, last_output_folder)
                    elif line.startswith('levels = '):
                        last_levels = line[8:].strip()
                        self.levels_entry.delete(0)
                        self.levels_entry.insert(0, last_levels)
                    elif line.startswith('use_default_rotor_bezier'):
                        self.use_default_rotor_bezier_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('use_default_stator_bezier'):
                        self.use_default_stator_bezier_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('adjust_rotor_thickness'):
                        self.adjust_rotor_thickness_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('adjust_rotor_angle'):
                        self.adjust_rotor_angle_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('adjust_stator_thickness'):
                        self.adjust_stator_thickness_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('adjust_stator_angle'):
                        self.adjust_stator_angle_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('show_section_plot'):
                        self.show_section_plot_var.set(line.split('=')[1].strip() == 'True')
                    elif line.startswith('show_angle_distribution_plots'):
                        self.show_angle_distribution_plots_var.set(line.split('=')[1].strip() == 'True')
                    # Read Saved Bleed Air Settings
                    elif line.startswith('enable_bleed_air'):
                        self.enable_bleed_air_var.set(line.split('=')[1].strip()=='True')
                    # Read Number of Patches and its Coordinates
                    elif line.startswith('rotor_patches = '):
                        self.bleed_air_data['rotor']['count'] = int(line.split('=')[1].strip())
                    elif line.startswith('stator_patches = '):
                        self.bleed_air_data['stator']['count'] = int(line.split('=')[1].strip())
                    elif line.startswith('rotor_patches_'):
                        try:
                            values = [v.strip() for v in line.split('=')[1].strip().split(',')]
                            self.bleed_air_data['rotor']['patches'].append(values)
                        except (ValueError, IndexError) as e:
                            err_msg = f"Error parsing Rotor patchline: line={line}. Error: {e}"
                            print(err_msg)
                            debug_log.debug(err_msg, context="load_parameters")
                    elif line.startswith('stator_patches_'):
                        try:
                            values = [v.strip() for v in line.split('=')[1].strip().split(',')]
                            self.bleed_air_data['stator']['patches'].append(values)
                        except (ValueError, IndexError) as e:
                            err_msg = f"Error parsing Stator patchline: line={line}. Error: {e}"
                            print(err_msg)
                            debug_log.debug(err_msg, context="load_parameters")    
                    elif line.startswith('inlet_area = '):
                        self.inlet_area_var.set(float(line.split('=')[1].strip()))
                    elif line.startswith('inlet_dist = '):
                        self.inlet_dist_var.set(float(line.split('=')[1].strip()))
                    elif line.startswith('outlet_area = '):
                        self.outlet_area_var.set(float(line.split('=')[1].strip()))
                    elif line.startswith('outlet_dist = '):
                        self.outlet_dist_var.set(float(line.split('=')[1].strip()))



        except FileNotFoundError:
            info_msg = "No previous parameters found. Starting with defaults."
            print(info_msg)
            debug_log.debug(info_msg, context="load_parameters")
        
        # Initial call to set up the Bleed AIr Tab based on loaded values
        self.update_bleed_air_display()
        
    def update_bleed_air_display(self, *args):
        if self.enable_bleed_air_var.get():
            self.bleed_input_container.pack(fill='both', expand=True, padx=10, pady=10)
            self.create_bleed_input_widget()
        else:
            self.bleed_input_container.pack_forget()
            
    def create_bleed_input_widget(self):
        # Clear existing Widgets
        for widget in self.bleed_input_container.winfo_children():
            widget.destroy()
            
        # Split window into two sides for Rotor and Stator
        self.rotor_frame = ttk.Frame(self.bleed_input_container)
        self.rotor_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        self.stator_frame = ttk.Frame(self.bleed_input_container)
        self.stator_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Add lables for both Rows
        ttk.Label(self.rotor_frame, text="Rotor Bleed Air", style="Bold.TLabel").pack(anchor='w')
        ttk.Label(self.stator_frame, text="Stator Bleed Air", style="Bold.TLabel").pack(anchor='w')
        
        # Add input for number of patches
        self.rotor_patches_frame = ttk.Frame(self.rotor_frame)
        self.rotor_patches_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(self.rotor_patches_frame, text="Number of Bleed Air Patches").pack(side='left')
        q_label_patches_rotor = ttk.Label(self.rotor_patches_frame, text="?", cursor="question_arrow")
        q_label_patches_rotor.pack(side='left', padx=(5, 5))
        Tooltip(q_label_patches_rotor, " Enter the number of Bleed air patches. Each patch is an area where a specific amout of air is bled from")
        self.rotor_patches_entry = ttk.Entry(self.rotor_patches_frame, width=5)
        self.rotor_patches_entry.pack(side='left')
        self.rotor_patches_entry.bind('<Return>', lambda event: self.update_patches('rotor'))
        # Insert loaded Patches
        self.rotor_patches_entry.insert(0, str(self.bleed_air_data['rotor']['count']))
        
        self.stator_patches_frame = ttk.Frame(self.stator_frame)
        self.stator_patches_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(self.stator_patches_frame, text="Number of Bleed Air Patches").pack(side='left')
        q_label_patches_stator = ttk.Label(self.stator_patches_frame, text="?", cursor="question_arrow")
        q_label_patches_stator.pack(side='left', padx=(5, 5))
        Tooltip(q_label_patches_stator, " Enter the number of Bleed air patches. Each patch is an area where a specific amout of air is bled from")
        self.stator_patches_entry = ttk.Entry(self.stator_patches_frame, width=5)
        self.stator_patches_entry.pack(side='left')
        self.stator_patches_entry.bind('<Return>', lambda event: self.update_patches('stator'))
        # Insert loaded Patches
        self.stator_patches_entry.insert(0, str(self.bleed_air_data['stator']['count']))
        
        # Call update_patches to create coordinates in fields upon loading
        self.update_patches('rotor')
        self.update_patches('stator')
        
    def update_patches(self, blade_type):
        if blade_type == 'rotor':
            num_patches_str = self.rotor_patches_entry.get()
            parent_frame = self.rotor_frame
            # Save patches data in dedicated list
            self.rotor_patch_entries.clear()
            patches_data = self.bleed_air_data['rotor']['patches']
        else:
            num_patches_str = self.stator_patches_entry.get()
            parent_frame = self.stator_frame
            # Save patches data in dedicated list
            self.stator_patch_entries.clear()
            patches_data = self.bleed_air_data['stator']['patches']
            
        try:
            num_patches = int(num_patches_str)
            if num_patches < 0:
                raise ValueError
        except (ValueError, IndexError):
            num_patches = 0
            
        # Remove previouse Patch Frames
        for widget in parent_frame.winfo_children():
            # Check if widget is in a patch inputframe
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()
        
        # Creat new Input widget for each Patch
        for i in range(num_patches):
            patch_frame = ttk.LabelFrame(parent_frame, text=f"Bleed Air Patch {i+1}")
            patch_frame.pack(fill='x',padx=5, pady=5)
            
            patch_entries = []
            
            # I coordinates
            i_label = ttk.Label(patch_frame, text="I start/end:")
            i_label.grid(row=0,column=0,padx=5, pady=2, sticky='w')
            i_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            i_q_label.grid(row=0, column=3, padx=2, pady=2, sticky='w')
            Tooltip(i_q_label, " The I-Coordinates define the Spanwise direction. Choose Values between 1 and 37. If you want to have bleed air over the whole spane enter 1 and 37")
            i_start_entry = ttk.Entry(patch_frame, width=5)
            i_start_entry.grid(row=0, column=1, padx=5, pady=2)
            i_end_entry = ttk.Entry(patch_frame, width=5)
            i_end_entry.grid(row=0, column=2, padx=5, pady=2)
            
            # J coordinates
            j_label = ttk.Label(patch_frame, text="J start/end:")
            j_label.grid(row=1,column=0,padx=5, pady=2, sticky='w')
            j_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            j_q_label.grid(row=1, column=3, padx=2, pady=2, sticky='w')
            Tooltip(j_q_label, f"The J-Coordinates define the Axial direction. 1 is defined as the start of the Blade while {JTE} is defined as the End of the blade")
            j_start_entry = ttk.Entry(patch_frame, width=5)
            j_start_entry.grid(row=1, column=1, padx=5, pady=2)
            j_end_entry = ttk.Entry(patch_frame, width=5)
            j_end_entry.grid(row=1, column=2, padx=5, pady=2)
            
            # K coordinates
            k_label = ttk.Label(patch_frame, text="K start/end:")
            k_label.grid(row=2,column=0,padx=5, pady=2, sticky='w')
            k_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            k_q_label.grid(row=2, column=3, padx=2, pady=2, sticky='w')
            Tooltip(k_q_label, "The K-Coordinate is defined as the Radial direction with 1 being the Hub wall and 37 being the Shroud wall. If you only want Bleed air to be extracted from one of the wall enter 1 and 1 or 37 and 37. It is also possible to extract Bleed air from the Stators and Rotors")
            k_start_entry = ttk.Entry(patch_frame, width=5)
            k_start_entry.grid(row=2, column=1, padx=5, pady=2)
            k_end_entry = ttk.Entry(patch_frame, width=5)
            k_end_entry.grid(row=2, column=2, padx=5, pady=2)
            
            # Massflow
            mflow_label = ttk.Label(patch_frame, text="Extraced Bleed Air (kg/s):")
            mflow_label.grid(row=3, column=0, padx=5, pady=2, sticky='w')
            mflow_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            mflow_q_label.grid(row=3, column=3, padx=2, pady=2, sticky='w')
            Tooltip(mflow_q_label, "The massflow rate is defined in kg/s. Specify how much Bleed air you want to be extracted in this Bleed air patch")
            massflow_entry = ttk.Entry(patch_frame, width=10)
            massflow_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=2)
            
            # Store Enter entries
            patch_entries.extend([i_start_entry, i_end_entry, j_start_entry, j_end_entry, k_start_entry, k_end_entry, massflow_entry])
            
            # Insert loaded values if exisiting
            if i < len(patches_data):
                for idx, entry in enumerate(patch_entries):
                    if idx < len(patches_data[i]):
                        entry.insert(0,patches_data[i][idx])
                        
            if blade_type == 'rotor':
                self.rotor_patch_entries.append(patch_entries)
            else: 
                self.stator_patch_entries.append(patch_entries)
            

    def browse_output_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, path)

    def save_and_initialize(self):
        use_default_rotor_bezier = self.use_default_rotor_bezier_var.get()
        use_default_stator_bezier = self.use_default_stator_bezier_var.get()
        adjust_rotor_thickness = self.adjust_rotor_thickness_var.get()
        adjust_rotor_angle = self.adjust_rotor_angle_var.get()
        adjust_stator_thickness = self.adjust_stator_thickness_var.get()
        adjust_stator_angle = self.adjust_stator_angle_var.get()
        output_folder = self.output_folder_entry.get()
        
        levels = self.levels_entry.get()
        nrow = self.nrow_entry.get()
        
        show_section_plot = self.show_section_plot_var.get()
        show_angle_distribution_plots = self.show_angle_distribution_plots_var.get()
        
        inlet_area = self.inlet_area_var.get()
        inlet_dist = self.inlet_dist_var.get()
        outlet_area = self.outlet_area_var.get()
        outlet_dist = self.outlet_dist_var.get()
        
        # Get bleed Air Settings
        enable_bleed_air = self.enable_bleed_air_var.get()

        with open('Setting.txt', 'w') as file:
            file.write(f"use_default_rotor_bezier = {use_default_rotor_bezier}\n")
            file.write(f"use_default_stator_bezier = {use_default_stator_bezier}\n")
            file.write(f"adjust_rotor_thickness = {adjust_rotor_thickness}\n")
            file.write(f"adjust_rotor_angle = {adjust_rotor_angle}\n")
            file.write(f"adjust_stator_thickness = {adjust_stator_thickness}\n")
            file.write(f"adjust_stator_angle = {adjust_stator_angle}\n")
            file.write(f"output_folder = {output_folder}\n")
            file.write(f"levels = {levels}\n")
            file.write(f"nrow = {nrow}\n")
            file.write(f"show_section_plot = {show_section_plot}\n")
            file.write(f"show_angle_distribution_plots = {show_angle_distribution_plots}\n")
            # Save Bleed Air data
            file.write(f"enable_bleed_air = {enable_bleed_air}\n")
            if enable_bleed_air:
                file.write(f"rotor_patches = {len(self.rotor_patch_entries)}\n")
                for i, entries in enumerate(self.rotor_patch_entries):
                    i_start = entries[0].get()
                    i_end= entries[1].get()
                    j_start = entries[2].get()
                    j_end= entries[3].get()
                    k_start = entries[4].get()
                    k_end= entries[5].get()
                    massflow = entries[6].get()
                    file.write(f"rotor_patch_{i+1} = {i_start}, {i_end}, {j_start}, {j_end}, {k_start}, {k_end}, {massflow}\n")
                    
                file.write(f"stator_patches = {len(self.stator_patch_entries)}\n")
                for i, entries in enumerate(self.stator_patch_entries):
                    i_start = entries[0].get()
                    i_end= entries[1].get()
                    j_start = entries[2].get()
                    j_end= entries[3].get()
                    k_start = entries[4].get()
                    k_end= entries[5].get()
                    massflow = entries[6].get()
                    file.write(f"stator_patch_{i+1} = {i_start}, {i_end}, {j_start}, {j_end}, {k_start}, {k_end}, {massflow}\n")
                    
            file.write(f"inlet_area = {inlet_area}\n")
            file.write(f"inlet_dist = {inlet_dist}\n")
            file.write(f"outlet_area = {outlet_area}\n")
            file.write(f"outlet_dist = {outlet_dist}\n")

        save_msg = "Parameters saved successfully."
        print(save_msg)
        debug_log.debug(save_msg, context="save_parameters")

if __name__ == "__main__":
    
    root = tk.Tk() 
    app = CompressorGUI(root) 
    root.mainloop()



def read_parameters_from_file(filename):
    global use_default_rotor_bezier, use_default_stator_bezier
    global adjust_rotor_thickness, adjust_rotor_angle
    global adjust_stator_thickness, adjust_stator_angle
    global output_folder, levels, nrow
    global show_section_plot, show_angle_distribution_plots
    global enable_bleed_air, rotor_patches_data, stator_patches_data
    global inlet_area, inlet_dist, outlet_area, outlet_dist

    # Initialize default values
    use_default_rotor_bezier = 0
    use_default_stator_bezier = 0
    adjust_rotor_thickness = 0
    adjust_rotor_angle = 0
    adjust_stator_thickness = 0
    adjust_stator_angle = 0
    output_folder = ""
    levels = []
    nrow = 2
    show_section_plot = 0
    show_angle_distribution_plots = 0
    enable_bleed_air = False
    rotor_patches_data = []
    stator_patches_data = []
    inlet_area = 0 
    inlet_dist = 0
    outlet_area = 0
    outlet_dist = 0

    try:
        with open(filename, 'r') as file:
            # Read all lines simultaneously to handle patches easily
            lines = file.readlines()
            # Use a state machine to parse bleed air patches
        is_reading_rotor = False
        is_reading_stator = False
        for line in lines:
            line = line.strip()
            if line.startswith('use_default_rotor_bezier'):
                is_reading_rotor = False
                is_reading_stator = False
                use_default_rotor_bezier = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('use_default_stator_bezier'):
                is_reading_rotor = False
                is_reading_stator = False
                use_default_stator_bezier = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('adjust_rotor_thickness'):
                is_reading_rotor = False
                is_reading_stator = False
                adjust_rotor_thickness = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('adjust_rotor_angle'):
                is_reading_rotor = False
                is_reading_stator = False
                adjust_rotor_angle = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('adjust_stator_thickness'):
                is_reading_rotor = False
                is_reading_stator = False
                adjust_stator_thickness = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('adjust_stator_angle'):
                is_reading_rotor = False
                is_reading_stator = False
                adjust_stator_angle = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('output_folder'):
                is_reading_rotor = False
                is_reading_stator = False
                output_folder = line.split('=')[1].strip()
            elif line.startswith('levels'):
                is_reading_rotor = False
                is_reading_stator = False
                levels_input = line.split('=')[1].strip()
                levels = [float(x) for x in levels_input.split(',')]  # Convert levels to list of floats
            elif line.startswith('nrow'):
                is_reading_rotor = False
                is_reading_stator = False
                nrow = int(line.split('=')[1].strip())
            elif line.startswith('show_section_plot'):
                is_reading_rotor = False
                is_reading_stator = False
                show_section_plot = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('show_angle_distribution_plots'):
                is_reading_rotor = False
                is_reading_stator = False
                show_angle_distribution_plots = 1 if line.split('=')[1].strip() == 'True' else 0
            elif line.startswith('enable_bleed_air'):
                enable_bleed_air = line.split('=')[1].strip() == 'True'
            elif line.startswith('rotor_patches = '):
                is_reading_rotor = True
            elif line.startswith('stator_patches = '):
                is_reading_rotor = False
                is_reading_stator = True
            elif is_reading_rotor and line.startswith('rotor_patch_'):
                values_str = line.split('=')[1].strip().split(',')
                rotor_patches_data.append([v.strip() for v in values_str])
            elif is_reading_stator and line.startswith('stator_patch_'):
                values_str = line.split('=')[1].strip().split(',')
                stator_patches_data.append([v.strip() for v in values_str])
            elif line.startswith('inlet_area = '):
                is_reading_rotor = False
                is_reading_stator = False
                inlet_area = line.split('=')[1].strip()
            elif line.startswith('inlet_dist = '):
                is_reading_rotor = False
                is_reading_stator = False
                inlet_dist = line.split('=')[1].strip()
            elif line.startswith('outlet_area = '):
                is_reading_rotor = False
                is_reading_stator = False
                outlet_area = line.split('=')[1].strip()
            elif line.startswith('outlet_dist = '):
                is_reading_rotor = False
                is_reading_stator = False
                outlet_dist = line.split('=')[1].strip()
                   
            print(f"Levels = {levels}")
            print(f"Folder = {output_folder}")
            
        return use_default_rotor_bezier, use_default_stator_bezier, adjust_rotor_thickness, adjust_rotor_angle, adjust_stator_thickness, adjust_stator_angle, \
        output_folder, levels, nrow, show_section_plot, show_angle_distribution_plots, enable_bleed_air, rotor_patches_data, stator_patches_data, \
        inlet_area, inlet_dist, outlet_area, outlet_dist   

    except FileNotFoundError:
        print("File not found. Please ensure the Setting.txt exists.")
'''
#read_parameters_from_file('Setting.txt')
NROW = nrow

# values from channel calculation
global x_values, r_values, m_prime_values, x0 
#x_values, r_values, m_prime_values, x0 = channel(h_H,stage, float(inlet_area), float(inlet_dist), float(outlet_area), float(outlet_dist), fixed_radius_type)

path = output_folder
'''

# functions for adjusting bezier point
def adjustBezierCurve_d_l(BezierPoints):

    d_lB = BezierPoints
    mB = [0.0, 0.3, 0.7, 1.0] 
    t = np.arange(0, 1.01, 0.01)

    x = bezier(4, t, mB)
    y = bezier(4, t, d_lB)

    # Create the plot
    fig, ax = plt.subplots(num='Thickness Distribution')
    plt.subplots_adjust(bottom=0.5)  # Leave more space for the sliders

    # Plot the points
    points, = plt.plot(mB, d_lB, 'o-', label="Points")
    curve, = plt.plot(x,y)
    plt.title("Thickness Distribution - Béziercurve")
    plt.xlabel("x/l [-]")
    plt.ylabel("d/l [%]")


    # Set axis limits
    ax.set_xlim(0, 1)

    d_l_min = 0.0
    d_l_max = 10.0

    ax.set_ylim(d_l_min, d_l_max)

    # Add sliders for each point
    sliders = []  # Store slider objects
    slider_axes = []  # Store axes for sliders

    for i in range(4):  # Create one slider for each point
        ax_slider = plt.axes([0.2, 0.25 - i * 0.05, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'Point {i + 1}', d_l_min, d_l_max, valinit=d_lB[i])
        sliders.append(slider)
        slider_axes.append(ax_slider)

    # Define update function for sliders
    def update(val):
        for i, slider in enumerate(sliders):
            d_lB[i] = slider.val  # Update y-coordinate for each point
        
        y = bezier(4, t, d_lB)
        curve.set_ydata(y)
        points.set_ydata(d_lB)  # Update the plot
        fig.canvas.draw_idle()

    # Connect sliders to the update function
    for slider in sliders:
        slider.on_changed(update)

    # Show the interactive plot
    plt.show()
    for i in range(len(d_lB)):
        d_lB[i] = round(d_lB[i], 2)

    debug_log.debug(f"New Bézier Point: {d_lB}", context="adjustBezierCurve_beta")
    
    return BezierPoints

def adjustBezierCurve_d(BezierPoints, cordlenght):

    d_lB = [point * cordlenght / 100 for point in BezierPoints]
    mB = [0.0, 0.3, 0.7, 1.0] 
    t = np.arange(0, 1.01, 0.01)

    x = bezier(4, t, mB)
    y = bezier(4, t, d_lB)

    # Create the plot
    fig, ax = plt.subplots(num='Thickness Distribution')
    plt.subplots_adjust(bottom=0.5)  # Leave more space for the sliders

    # Plot the points
    points, = plt.plot(mB, d_lB, 'o-', label="Points")
    curve, = plt.plot(x,y)
   # plt.figure(num='This is the title');
    plt.title("Thickness Distribution - Béziercurve")
    plt.xlabel("x/l [-]")
    plt.ylabel("d [mm]")
    plt.grid('on')


    # Set axis limits
    ax.set_xlim(0, 1)

    dmin = 0.0
    dmax = 5.0

    ax.set_ylim(dmin, dmax)

    # Add sliders for each point
    sliders = []  # Store slider objects
    slider_axes = []  # Store axes for sliders

    for i in range(4):  # Create one slider for each point
        ax_slider = plt.axes([0.2, 0.25 - i * 0.05, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'Point {i + 1}', dmin, dmax, valinit=d_lB[i])
        sliders.append(slider)
        slider_axes.append(ax_slider)

    # Define update function for sliders
    def update(val):
        for i, slider in enumerate(sliders):
            d_lB[i] = slider.val  # Update y-coordinate for each point
        
        y = bezier(4, t, d_lB)
        curve.set_ydata(y)
        points.set_ydata(d_lB)  # Update the plot
        fig.canvas.draw_idle()

    # Connect sliders to the update function
    for slider in sliders:
        slider.on_changed(update)

    # Show the interactive plot
    plt.show()
    for i in range(len(d_lB)):
        d_lB[i] = round(d_lB[i]*100/cordlenght, 2)

    
    debug_log.debug(f"New Bézier Point: {d_lB}", context="adjustBezierCurve_d")
    return d_lB

def adjustBezierCurve_beta(BezierPoints):

    beta = BezierPoints

    mB = [0.0, 0.3, 0.7, 1.0] 
    t = np.arange(0, 1.01, 0.01)

    x = bezier(4, t, mB)
    y = bezier(4, t, beta)

    # Create the plot
    fig, ax = plt.subplots(num='Blade Angle Distribution')
    plt.subplots_adjust(bottom=0.5)  # Leave more space for the sliders

    # Plot the points
    points, = plt.plot(mB, beta, 'o-', label="Points")
    curve, = plt.plot(x,y)
    plt.title("Blade Angle Distribution - Béziercurve")
    plt.xlabel("x/l [-]")
    plt.ylabel("blade angle [°]")


    # Set axis limits
    ax.set_xlim(0, 1)

    beta_min = 0.0
    beta_max = 170

    ax.set_ylim(beta_min, beta_max)

    # Add sliders for each point
    sliders = []  # Store slider objects
    slider_axes = []  # Store axes for sliders

    for i in range(4):  # Create one slider for each point
        ax_slider = plt.axes([0.2, 0.25 - i * 0.05, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'Point {i + 1}', beta_min, beta_max, valinit=beta[i])
        sliders.append(slider)
        slider_axes.append(ax_slider)

    # Define update function for sliders
    def update(val):
        for i, slider in enumerate(sliders):
            beta[i] = slider.val  # Update y-coordinate for each point
        
        y = bezier(4, t, beta)
        curve.set_ydata(y)
        points.set_ydata(beta)  # Update the plot
        fig.canvas.draw_idle()

    # Connect sliders to the update function
    for slider in sliders:
        slider.on_changed(update)

    # Show the interactive plot
    plt.show()
    for i in range(len(beta)):
        beta[i] = round(beta[i], 2)

    debug_log.debug(f"New Bézier Point: {beta}", context="adjustBezierCurve_beta")
    return BezierPoints



# section to create a plot of geometry, blade angle and thickniss distribution 
def show_plots():
    global z_R, l_R, l_S, i_st, show_section_plot, show_angle_distribution_plots
    global length, row, h, farben
    
    if show_section_plot == 1:
        length = []
        row = 1
        for k in range(len(h)):
                h = [0.0 , 0.2, 0.5, 0.8, 1.0]
                farben = ["pink", "blue", "green", "red", "black"]
                i = h[k]
                chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
                plt.plot(m_star_u, R_theta_s_star_u, color = farben[k], label = f"{h[k]*100}%")
                plt.plot(m_star_l, R_theta_s_star_l, color = farben[k])
                plt.legend()  

        
        if NROW == 2:    
            length = []
            row = 2
            for k in range(len(h)):
                h = [0.0 , 0.2, 0.5, 0.8, 1.0]
                farben = ["pink", "blue", "green", "red", "black"]
                i = h[k]
                chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
                #length.append(chord)
                plt.plot(m_star_u, R_theta_s_star_u, color = farben[k], label = f"{h[k]*100}%")
                plt.plot(m_star_l, R_theta_s_star_l, color = farben[k])
        
        plt.xlabel("x [mm]")
        plt.ylabel("R\u03b8 [mm]") 
                
        plt.show()

    if show_angle_distribution_plots == 1:
        row = 1
        for k in range(len(h)):
                h = [0.0 , 0.2, 0.5, 0.8, 1.0]
                farben = ["pink", "blue", "green", "red", "black"]
                i = h[k]
                chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
                plt.plot(m_prime, beta_S, label = f"{h[k]*100}%", color = farben[k])
                plt.scatter(m_BP, beta_BP, color = farben[k])
                plt.legend() 
        
        if NROW == 2:    
            length = []
            row = 2
            for k in range(len(h)):
                h = [0.0 , 0.2, 0.5, 0.8, 1.0]
                farben = ["pink", "blue", "green", "red", "black"]
                i = h[k]
                chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
                plt.plot(m_prime, beta_S, label = f"{h[k]*100}%", color = farben[k])
                plt.scatter(m_BP, beta_BP, color = farben[k])
                

        plt.xlabel('x/s [%]')
        plt.ylabel("blade angle [°]")           
        plt.show()

