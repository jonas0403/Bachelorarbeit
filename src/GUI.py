import tkinter as tk
import numpy as np
import matplotlib as plt
import matplotlib.pyplot as plt
import os 
import shutil
import json
import sys
import subprocess


#from tkinter import filedialog
from tkinter import messagebox
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, filedialog, Label, Toplevel
from pathlib import Path
#from matplotlib.widgets import Slider

from Stage_v3_working_with_bleedair import create_default_profiles, calculation_of_section, run_main_logic
from Cubspline_function_v2 import cubspline
from Thermodynamic_calc_GUI import Thermo
from Fixed_radii_Meanline_GUI_v4 import meanline
import var_Grid as VG
import debug_log


current_dir = Path(__file__).parent.parent
static_folder = current_dir/ "static"
json_file = 'Populated_data.json'
json_path = static_folder / json_file


#Shouldnt be in use
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
                    
    

class CompressorGui:
    '''
    Load all data once and save into different class data dicts
    Data gets prepopulated with rendering of the gui
    '''
    def loading_prepopulated_data(self):
        
        
        with open(json_path, 'r') as file:
            data = json.load(file)

            self.prepop_thermo_data = data['Thermodynamic_input_data']
            self.prepop_meanline_input_data = data['Meanline_input_data']
            self.prepop_diameter_data = data['Diameter_data']
            # self.prepop_bezier_point_stator = data['Bezier_point_data']['stator']
            # self.prepop_bezier_point_rotor = data['Bezier_point_data']['rotor']
            self.prepop_metadata = data['Metadata'] 
            self.prepop_grid_data = data['Grid_data'] 
            self.prepop_bleed_air_data = data['Bleed_air_data']
            self.prepop_intake_outtake_area_data = data['Intake_Outtake_area']
            
        bezier_store = data.get('Bezier_point_data', {})

        # Support both new per-stage keys (rotor_stage_1 …) and the old single keys
        if 'rotor_stage_1' in bezier_store:
            self.prepop_bezier_point_rotor  = bezier_store['rotor_stage_1']
            self.prepop_bezier_point_stator = bezier_store.get('stator_stage_1', {})
        else:
            # Legacy fallback – JSON was written before the multi-stage patch
            self.prepop_bezier_point_rotor  = bezier_store.get('rotor',  {})
            self.prepop_bezier_point_stator = bezier_store.get('stator', {})
        
    '''
    Function and population of first tab
    Entryboxes for the first 0 Dimensional Thermodynamic calculation
    Can be read through the json file or through entry in entryboxes   
    '''
    def zeroD_tab(self, window):
        '''
        Thermodynamic Parameters Tab
        '''
        ttk.Label(window, text="This is the 0D Settings tab").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='w')

        # old not used
        #read_initial_values(static_folder/ "Thermo_Initial_Values.txt") 
        #params = ['p_t_in', 'T_t_in', 'mflow', 'R', 'cp', 'TPR'] 
        #window.add(window, text="Thermodynamic Parameters")  
        #path = os.getcwd()
        #print(path)

        entries = {}
        params = list(self.prepop_thermo_data.keys())
        gui_names = ['p_t_in [Pa]', 'T_t_in [K]', 'mflow [kg/s]', 'R [J/kg*K]', 'cp [J/kg*K]', 'TPR [-]']
        
        for i, param in enumerate(params):
            ttk.Label(window, text=f"{gui_names[i]}:").grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
            
            entry = ttk.Entry(window, width=15)
            entry.insert(0, str(self.prepop_thermo_data[param]))
            entry.grid(row=i+1, column=1, padx=5, pady=5)
            entries[param]= entry

        def save_and_initialize():
            try:
                with open(json_path, 'r') as file:
                    all_json_data = json.load(file)
                                    
                new_thermo_values = {}
                for param in params:
                    new_thermo_values[param] = float(entries[param].get())

                all_json_data['Thermodynamic_input_data'] = new_thermo_values
                
                with open(json_path, 'w') as file:
                    json.dump(all_json_data, file, indent=4)
                 
                self.prepop_thermo_data = new_thermo_values
                    
                thermo_msg = "Thermodynamic Parameters saved and initialized."
                print(thermo_msg)
                debug_log.debug(thermo_msg, context="zeroD_tab")

                
                self.Thermodata =  Thermo(
                    new_thermo_values['p_t_in'],
                    new_thermo_values['T_t_in'],
                    new_thermo_values['mflow'],
                    new_thermo_values['R'],
                    new_thermo_values['cp'],
                    new_thermo_values['TPR'],
                    self.stage
                )
                calc_msg = "Calculation of Thermodynamic Data completed."
                print(calc_msg)
                debug_log.debug(calc_msg, context="zeroD_tab")
            except ValueError:
                val_err = "Please enter valid numbers for all conditions."
                print(val_err)
                debug_log.debug(val_err, context="zeroD_tab")
                
            
            

        save_button = ttk.Button(window, text="Save and Initialize Parameters", command=save_and_initialize)
        save_button.grid(row=len(params)+1, column=0, columnspan=2, pady=10)
        save_and_initialize()   
            
            
    '''
    Function and population of second tab
    Here meanline calculation values can be entered through boxes or through the reading of the json file
    Creating an extra gui for the entry and definition of the channel contours. Can also be read through json file  
    '''
    def oneD_tab(self, parent_frame, i_st_val):
            
        '''
        Define Names for Settings json 
        Defines Variable Mapping and GUI Names for reading of setting file
        '''
        parameters_sections = {
        'General Parameters': ['n', 'psi_h', 'phi_1', 'phi_2', 'phi_3'],
        'Rotor Parameters': ['z_R', 'l_R', 'd_R_l_R', 'd_Cl_R', 'd_TE_R', 'incidence_R'],
        'Stator Parameters': ['z_S', 'l_S', 'd_S_l_S', 'd_TE_S', 'd_CL_S', 'incidence_S']}
        # Define mapping between variable names and GUI names
        var_name_to_gui_map = {
            'n': 'n [rpm]',
            'psi_h': 'psi_h [-]',
            'phi_1': 'phi_1 [-]',
            'phi_2': 'phi_2 [-]',
            'phi_3': 'phi_3 [-]',
            'z_R': 'z" [-]',
            'l_R': 'l" [mm]',
            'd_R_l_R': 'd"/l" [-]',
            'd_Cl_R': 'd_cl" [mm]',
            'd_TE_R': 'd_TE" [mm]',
            'incidence_R': 'i" [°]',
            'z_S': "z' [-]",
            'l_S': "l' [mm]",
            'd_S_l_S': "d'/l' [-]",
            'd_TE_S': "d_TE' [mm]",
            'd_CL_S': "d_CL' [mm]",
            'incidence_S': "i' [°]"}
              
        
        '''
        Not in use
        '''
        #region not in used/obsolet functions and variables
        # Create reverse mapping 
        # currently not needed
        #gui_to_var_map = {v: k for k, v in var_name_to_gui_map.items()}
        
        # Obsolet
        #LOCK_FILE = static_folder/"settings.lock"
        #SETTINGS_FILE = static_folder/"Diameter_Values.txt"  
          
        def create_input_window(i_st_val):
            # Creates Gui to Input the fixed Diameters and the type of fixed Diameters

            # Initialize Variables
            D_f1_result = [0.508]*i_st_val 
            D_f2_result = [0.508]*i_st_val
            D_f3_result = [0.508]*i_st_val
            fixed_radius_type = "none"# "shroud" , "mean" , "hub" , "none"
            
            plot_channel_contour = False # Default to False
            
            # List to hold StringVar objexts for each diameter entry
            D_f1_entry_vars = [] 
            D_f2_entry_vars = []
            D_f3_entry_vars = []
            
            def on_save():
                nonlocal fixed_radius_type, D_f1_result, D_f2_result, D_f3_result, plot_channel_contour

                selected_type = type_var.get()
                if not selected_type:
                    
                    messagebox.showerror("Input Error", "Please select a fixed radius type.")
                    return

                # Validate and parse D_f entries
                try:
                    # Iterate through D_f_entry_vars to get values for each stage
                    temp_D_f1 = []
                    temp_D_f2 = []
                    temp_D_f3 = []
                    
                    for i in range(i_st_val):
                        temp_D_f1.append(float(D_f1_entry_vars[i].get().strip()))
                        temp_D_f2.append(float(D_f2_entry_vars[i].get().strip()))
                        temp_D_f3.append(float(D_f3_entry_vars[i].get().strip()))
                    
                    D_f1_result = temp_D_f1
                    D_f2_result = temp_D_f2
                    D_f3_result = temp_D_f3
                    
                    fixed_radius_type = selected_type
                    plot_channel_contour = plot_var.get() # Get checkbox value
                    root.destroy() # Close the window
                except ValueError:
                    messagebox.showerror("Input Error", "Please enter numerical values for D_f, separated by commas.")
                except Exception as e:
                    messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                
                
            def update_default_diameters(args):
                # This function is called when the fixed_radius_type changes
                current_type = type_var.get()
                default_val = "0.508" # Default for shroud/hub, adjust as needed

                if current_type == "shroud":
                    default_val = "0.740"
                elif current_type == "hub":
                    default_val = "0.274" # Example: different default for hub
                elif current_type == "mean":
                    default_val = "0.508" # Example: different default for mean
                elif current_type == "none":
                    default_val = "0.0" # Example: default to zero if 'none' fixed
                
                # Update the entry fields with the new default values
                for i in range(i_st_val):
                    D_f1_entry_vars[i].set(default_val)
                    D_f2_entry_vars[i].set(default_val)
                    D_f3_entry_vars[i].set(default_val)    
                    
            #Function to toggle entry state
            def toggle_diameter_entries():
                state = "disabled" if use_default_var.get() else "normal"
                for i in range(i_st_val):
                    D_f1_entries[i].config(state=state)
                    D_f2_entries[i].config(state=state)
                    D_f3_entries[i].config(state=state)

                # If default is selected, apply default values
                if use_default_var.get():
                    update_default_diameters()
            
            def on_closing():
                root.destroy()
        
            root = tk.Tk()
            root.title("Channel Contour Window")
            
            # Select Fixed Radius Type
            tk.Label(root, text="Select Fixed Radius Type:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
            type_var = tk.StringVar(root)
            type_options = ["shroud", "mean", "hub", "none"]
            type_var.set(type_options[0]) # default value
            type_menu = tk.OptionMenu(root, type_var, *type_options)
            type_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew", columnspan=i_st_val)
            
            # Bind the update function to the type_var
            type_var.trace_add("write", update_default_diameters)
            
            # Add text Window 
            message_frame = tk.LabelFrame(root, text="Important Note", padx=10, pady=10, relief="groove", borderwidth=2)
            message_frame.grid(row=1, column=0, columnspan=1+i_st_val, padx=10, pady=10, sticky="ew")
            
            tk.Label(message_frame, 
                    text="D_f3 of each but the last stage must be equal to D_f1 of the following stage", 
                    font=("TkDefaultFont", 10, "bold"), 
                    fg="blue", # Optional: make text blue for emphasis
                    wraplength=400, # Wrap text if it's too long
                    justify="center").grid(row=0, column=0, padx=5, pady=5)
            
            
            # StringVars for entry fields
            D_f1_entries = []
            D_f2_entries = []
            D_f3_entries = []
            
            # Dynamic creation of D_f input fileds
            # Start row for D_f inputs, adjusted for new checkbox and message frame
            current_row = 2
            
            # Add column headers for each stage
            tk.Label(root, text="").grid(row=current_row,column=0) # Empty label for alligning over the text boxes
            
            for i in range(i_st_val):
                tk.Label(root,text=f"Stage {i+1}", font=("TkDefaultFont",10, "bold")).grid(row=current_row, column=1+i, padx=5, pady=2, sticky="ew")
                
            current_row += 1
            
            tk.Label(root, text=f"Enter D_f1 ").grid(row=current_row, column=0, padx=10, pady=2, sticky="w")
            tk.Label(root, text=f"Enter D_f2 ").grid(row=current_row+1, column=0, padx=10, pady=2, sticky="w")
            tk.Label(root, text=f"Enter D_f3 ").grid(row=current_row+2, column=0, padx=10, pady=2, sticky="w")
            
            for i in range(i_st_val):
                # D_f1 Input
                D_f1_var=tk.StringVar(root)
                entry_D_f1 = tk.Entry(root, width=15, textvariable=D_f1_var)
                entry_D_f1.grid(row=current_row, column=1+i, padx=5, pady=2, sticky="ew")
                D_f1_entry_vars.append(D_f1_var)
                D_f1_entries.append(entry_D_f1) 
                
                # D_f2 Input
                D_f2_var=tk.StringVar(root)
                entry_D_f2 = tk.Entry(root, width=15, textvariable=D_f2_var)
                entry_D_f2.grid(row=current_row+1, column=1+i, padx=5, pady=2, sticky="ew")
                D_f2_entry_vars.append(D_f2_var)
                D_f2_entries.append(entry_D_f2) 
                
                # D_f3 Input
                D_f3_var=tk.StringVar(root)
                entry_D_f3 = tk.Entry(root, width=15, textvariable=D_f3_var)
                entry_D_f3.grid(row=current_row+2, column=1+i, padx=5, pady=2, sticky="ew")
                D_f3_entry_vars.append(D_f3_var)
                D_f3_entries.append(entry_D_f3) 


            # Initialize entry fields with default values based on the initial type_var
            update_default_diameters() # Call once to set initial defaults
            
            
            
            # Checkbox for the "Use default Diameters"
            use_default_var = tk.BooleanVar(root)
            use_default_var.set(False) # Defaults to unchecked
            checkbutton_use_default = tk.Checkbutton(root, text= "Use default Diameters for the fixed radius type", variable=use_default_var, command=toggle_diameter_entries)
            checkbutton_use_default.grid(row=current_row+3, column=0, columnspan=1+i_st_val, pady=5)
        
            # Checkbutton for plotting channel contour
            plot_var = tk.BooleanVar(root)
            plot_var.set(True) # Default to checked (True)
            checkbutton_plot = tk.Checkbutton(root, text="Plot Channel Contour", variable=plot_var)
            checkbutton_plot.grid(row=current_row +4, column=0, columnspan=1+i_st_val, pady=5)

            # Closing of the window
            root.protocol("WM_DELETE_WINDOW", on_closing)

            # Save Button
            save_button = tk.Button(root, text="Save and Continue", command=on_save)
            save_button.grid(row=current_row+5, column=0, columnspan=1+i_st_val, pady=10)

            # Make the window modal (optional, but good practice for input dialogs)
            root.grab_set()
            
            toggle_diameter_entries()
            
            root.wait_window()
            
            debug_log.debug("diameter_gui close callback called", context="oneD_tab")
            write_diameters(self, fixed_radius_type, D_f1_result, D_f2_result, D_f3_result, plot_channel_contour)
            return fixed_radius_type, D_f1_result, D_f2_result, D_f3_result, plot_channel_contour


        '''
        Maybe in use
        Not in use
        ''' 
        #endregion

        '''
        ' Helping functions for the meanline gui creation.
        ' 
        '''
        def create_scrollable_frame(container):
            canvas = tk.Canvas(container)
            scrollbar = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.pack(fill='both', expand=True)
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(frame_id, width=e.width))
            
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Bind Mouswheel
            def _on_mousewheel(event):
                if event.num == 4 or event.delta > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5 or event.delta < 0:
                    canvas.yview_scroll(1, "units")
                    
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            return canvas, scrollbar, scrollable_frame

        class diameter_gui:
            def __init__(self, root, i_st_val, on_close_callback, initial_diamter_data):
                
                debug_log.debug(f"initial_data: {initial_diamter_data}", context="diameter_gui")
                
                self.root = root
                self.on_close_callback = on_close_callback
                self.num_stages = i_st_val
                self.num_points = 2 * i_st_val + 1
                
                
                # Standard values for the different fixed radius types
                self.default_values = {
                    "shroud": [0.800] * self.num_points,
                    "mean": [0.508] * self.num_points,
                    "hub": [0.274] * self.num_points
                }
                
                # Initial slider Values loaded out of the settings file 
                self.initial_type = initial_diamter_data.get("fixed_radius_type", "mean")
                self.initial_D_f1 = initial_diamter_data.get("D_f1", [])
                self.initial_D_f2 = initial_diamter_data.get("D_f2", [])
                self.initial_D_f3 = initial_diamter_data.get("D_f3", [])
                self.initial_plot_contour = initial_diamter_data.get("plot_channel_contour", False)
                debug_log.debug(f"plot_channel_contour={self.initial_plot_contour}", context="diameter_gui")
                
                # Initialize this data
                self.cubspline_points = []
                if self.initial_D_f1 and self.initial_D_f2:
                    for i in range(len(self.initial_D_f1)):
                        if i == 0:
                            self.cubspline_points.append(self.initial_D_f1[0])
                            self.cubspline_points.append(self.initial_D_f2[0])
                            self.cubspline_points.append(self.initial_D_f3[0])
                        else:   #if i == len(self.initial_D_f1)-1: 
                            self.cubspline_points.append(self.initial_D_f2[i])
                            self.cubspline_points.append(self.initial_D_f3[i])
                else: 
                    self.cubspline_points = [1] * self.num_points
                
                self.t = np.arange(0, 1.01, 0.01)
                debug_log.debug(f"self.cubspline_points={self.cubspline_points}", context="diameter_gui")
                
                # Define x-cood for Bezier-Points
                self.mB = np.linspace(0.0, 1.0, self.num_points)
                
                # Define slider limits based on fixed Radius type 
                self.limits = {
                    "shroud": (0.4, 1.2),
                    "mean": (0.25, 0.8),
                    "hub": (0.05, 0.6)
                }
                
                self.root.title("Choose Channel Contour Diameter")
                self.root.geometry("600x800")
                
                # Create main Frames
                self.top_frame = tk.Frame(root)
                self.top_frame.pack(side='top', fill='x', padx=10, pady=10)
                
                self.plot_frame = tk.Frame(root)
                self.plot_frame.pack(side='top', fill='both', expand=True)
                
                self.bottom_frame = tk.Frame(root)
                self.bottom_frame.pack(side='bottom', fill='both', expand=True)
                
                # Dropdown Menu 
                tk.Label(self.top_frame, text="Select fixed Radius type: ").pack(padx=10, pady=5, anchor='w')
                self.type_var = tk.StringVar(root)
                self.type_options = list(self.limits.keys())
                self.type_var.set(self.initial_type)
                self.type_menu = tk.OptionMenu(self.top_frame, self.type_var, *self.type_options, command=self.update_slider_limit)
                self.type_menu.pack(padx=10, pady=5, fill='x', expand=True)
                
                # Checkbox for Plot Contour Channel
                self.plot_channel_var = tk.BooleanVar(value=self.initial_plot_contour)
                self.plot_channel_checkbox = tk.Checkbutton(self.top_frame, text="Plot the channel contour", variable=self.plot_channel_var)
                self.plot_channel_checkbox.pack(padx=10, pady=5, anchor='w')
                
                # Plot
                self.fig, self.ax = plt.subplots(figsize=(5,4))
                self.ax.set_title("Fixed Diameter Contour")
                self.ax.set_xlabel("x / channel length")
                self.ax.set_ylabel("D [m]")
                self.ax.set_xlim(0, 1)
                self.ax.set_ylim(self.limits[self.type_var.get()])
                self.curve, = self.ax.plot([], [], 'b-')
                self.points, = self.ax.plot([], [], 'o', color='red', label="Control Points")
                
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill='both', expand=True)
                
                # Use Scrollable Frame 
                self.slider_canvas, self.slider_scrollbar, self.slider_frame = create_scrollable_frame(self.bottom_frame)
                self.slider_scrollbar.pack(side='right', fill= 'y')
                self.slider_canvas.pack(side='left', fill='both', expand=True)
                
                # Frame for Sliders
                #self.sliders_frame = tk.Frame(self.bottom_frame)
                #self.sliders_frame.pack(side='top', fill='both', expand=True)
                
                # SLiders and the Enrtybox
                self.sliders = []
                self.entries = []
                self.entry_vars = []
                                
                for i in range(self.num_points):
                    row_frame = tk.Frame(self.slider_frame)
                    row_frame.pack(padx=5, pady=5, fill='x')
                    
                    # Label
                    label = tk.Label(row_frame, text=f"Points {i+1}")
                    label.pack(side='left', padx=(0, 5))
                    
                    # Entrybox
                    entry_var = tk.DoubleVar(value=self.cubspline_points[i])
                    entry = tk.Entry(row_frame, width=8, textvariable=entry_var)
                    entry.pack(side='right')
                    entry.bind('<Return>', lambda event, idx=i: self.update_from_box(idx))
                    self.entries.append(entry)
                    self.entry_vars.append(entry_var)
                    
                    # SLiders
                    min_val, max_val = self.limits[self.type_var.get()]
                    slider = tk.Scale(row_frame, from_=min_val, to=max_val, orient='horizontal', resolution=0.01)
                    slider.set(self.cubspline_points[i])
                    slider.configure(command=lambda val, idx=i: self.update_from_slider(float(val), idx))
                    slider.pack(side='left', fill='x', expand=True)
                    self.sliders.append(slider)
                
                # Button Frame   
                self.button_frame = tk.Frame(self.slider_frame)
                self.button_frame.pack(side='top', fill='x', padx= 5, pady=10)
                
                self.save_button = tk.Button(self.button_frame, text="Save and Exit", command=self.save_and_exit)
                self.save_button.pack(side='left', padx=5, expand=True, fill='x')
                
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
                # Initial plot setup
                self.update_plot()
                
            def update_plot(self):
                # Updates Plot and the curve in it
                x_points = self.mB.tolist()
                y_points = self.cubspline_points
                
                y = [cubspline(1, xi, x_points, y_points) for xi in self.t.tolist()]
                self.curve.set_xdata(self.t)
                self.curve.set_ydata(y)
                self.points.set_xdata(self.mB)
                self.points.set_ydata(self.cubspline_points)
                self.fig.canvas.draw_idle()
                
            def update_slider_limit(self, selected_type):
                # Updates Slider Range base on the fixed Radius type
                min_val, max_val = self.limits[selected_type]
                self.ax.set_ylim(min_val, max_val)
                
                new_val = self.default_values.get(selected_type, [])
                
                for i, slider in enumerate(self.sliders):
                    slider.configure(from_=min_val, to=max_val)
                    # Update slider position on fixed radius type change
                    if i < len(new_val):
                        slider.set(new_val[i])
                        self.cubspline_points[i] = new_val[i]
                        self.entries[i].delete(0, tk.END)
                        self.entries[i].insert(0, f"{new_val[i]:.4f}")
                
                # Update Plot to change Plot
                self.update_plot()
            
            def update_from_slider(self, val, idx):
                # Updates sliders and synchronizes entryboxes
                self.cubspline_points[idx] = val
                self.entries[idx].delete(0, tk.END)
                self.entries[idx].insert(0, f"{val:.4f}")
                self.update_plot()
                
            def update_from_box(self, idx):
                # Updates Entrybox and synchonizes slider
                try:
                    val = float(self.entries[idx].get())
                    min_val = self.sliders[idx].cget("from")
                    max_val = self.sliders[idx].cget("to")
                    
                    if min_val <= val <= max_val:
                        self.sliders[idx].set(val)
                        self.cubspline_points[idx] = val
                        self.update_plot()
                    else:
                        messagebox.showerror("Invalid Input", f"Value must be between {min_val:.4f} and {max_val:.4f}")
                        self.entries[idx].delete(0, tk.END)
                        self.entries[idx].insert(0, f"{self.sliders[idx].get():.4f}")
                
                except:
                    messagebox.showerror("Invalid Input", "Please enter a Valid Number")
                    self.entries[idx].delete(0, tk.END)
                    self.entries[idx].insert(0, f"{self.sliders[idx].get():.4f}")
                    
            def save_and_exit(self):
                self.on_closing()
                    
            def on_closing(self):
                # Called when window is closed
                # Returns all points
                
                # Saving all Data
                D_f1, D_f2, D_f3 = [0] * self.num_stages,  [0] * self.num_stages,  [0] * self.num_stages
                
                
                
                for i in range(self.num_stages):
                    if i == 0:
                        D_f1[i] = self.cubspline_points[0]
                        D_f2[i] = self.cubspline_points[1]
                        D_f3[i] = self.cubspline_points[2]
                    elif i == self.num_stages - 1:
                        D_f1[i] = self.cubspline_points[len(self.cubspline_points)-3]
                        D_f2[i] = self.cubspline_points[len(self.cubspline_points)-2]
                        D_f3[i] = self.cubspline_points[len(self.cubspline_points)-1]
                    else:
                        D_f1[i] = self.cubspline_points[i*2]
                        D_f2[i] = self.cubspline_points[i*2+1]
                        D_f3[i] = self.cubspline_points[i*2+2]
                        
                    
                # Call writing function
                fixed_radius_type = self.type_var.get()
                plot_channel_contour = self.plot_channel_var.get()
                
                self.changed_channel_contour_data = {
                    
                    "D_f1": D_f1,
                    "D_f2": D_f2,
                    "D_f3": D_f3,
                    "fixed_radius_type": fixed_radius_type,
                    "plot_channel_contour": plot_channel_contour
                }
                debug_log.debug(f"self.changed_channel_contour_data: {self.changed_channel_contour_data}", context="diameter_gui")
                
                #self.save_and_initialize_meanline(plot_channel_contour) 
                self.on_close_callback(self.changed_channel_contour_data)
                self.root.destroy()
                plt.close(self.fig)
                
        def run_diameter_gui(i_st, initial_data, save_callback = None):
            root = tk.Tk()
            D_f1, D_f2, D_f3 = [],  [],  []
            fixed_radius_type = ""
            plot_channel_contour = False
            
            def on_close(changed_diamtere_data):
                
                D_f1 = changed_diamtere_data["D_f1"]
                D_f2 = changed_diamtere_data["D_f2"]
                D_f3 = changed_diamtere_data["D_f3"]

                fixed_radius_type = changed_diamtere_data["fixed_radius_type"]
                plot_channel_contour = changed_diamtere_data["plot_channel_contour"]
                
                try:
                    with open(json_path, 'r') as file:
                        all_json_data = json.load(file)
                    new_diameter_data = {}
                    '''
                    if self.meanline_data["fixed_radius_type"] == "shroud":
                        new_diameter_data["D_f1"] = self.meanline_data["D_S1"]
                        new_diameter_data["D_f2"] = self.meanline_data["D_S2"]
                        new_diameter_data["D_f3"] = self.meanline_data["D_S3"]
                    elif self.meanline_data["fixed_radius_type"] == "mean":
                        new_diameter_data["D_f1"] = self.meanline_data["D_M1"]
                        new_diameter_data["D_f2"] = self.meanline_data["D_M2"]
                        new_diameter_data["D_f3"] = self.meanline_data["D_M3"]
                    elif self.meanline_data["fixed_radius_type"] == "hub":
                        new_diameter_data["D_f1"] = self.meanline_data["D_H1"]
                        new_diameter_data["D_f2"] = self.meanline_data["D_H2"]
                        new_diameter_data["D_f3"] = self.meanline_data["D_H3"]   
                    '''
                    new_diameter_data["D_f1"] = D_f1
                    new_diameter_data["D_f2"] = D_f2
                    new_diameter_data["D_f3"] = D_f3
                    
                    debug_log.debug(f"Debug plot_chanel_contour: {plot_channel_contour}", context="diameter_gui")
                        
                    new_diameter_data["fixed_radius_type"] = fixed_radius_type
                    new_diameter_data["plot_channel_contour"] = plot_channel_contour
                    
                    all_json_data['Diameter_data'] = new_diameter_data
                        
                    
                    # The data to be saved is already in self.prepop_diameter_data,
                    # which was updated by run_diameter_gui.

                    with open(json_path, 'w') as file:
                        json.dump(all_json_data, file, indent=4)
                    status_msg = "Diameter data saved to JSON successfully."
                    print(status_msg)
                    debug_log.debug(status_msg, context="diameter_gui")
                    
                    self.prepop_diameter_data = new_diameter_data
                    debug_log.debug(f"D_f1={D_f1}, D_f2={D_f2}, D_f3={D_f3}, fixed_radius_type = {fixed_radius_type}, plot_channel_contour = {plot_channel_contour}", context="diameter_gui")
                    self.meanline_data = meanline(self.Thermodata, self.prepop_meanline_input_data, self.prepop_diameter_data, plot_channel_contour)
                except Exception as e:
                    err_msg = f"Error during JSON write in write_diameters: {e}"
                    print(err_msg)
                    debug_log.debug(err_msg, context="diameter_gui")
                
                
                
                
            # Read Initial Data from File   
            diameter_gui(root, i_st, on_close, initial_data)
            root.mainloop()
            debug_log.debug(f"D_f1={D_f1}, D_f2={D_f2}, D_f3={D_f3}, fixed_radius_type={fixed_radius_type}, plot_channel_contour={plot_channel_contour}", context="diameter_gui")
            
            self.prepop_diameter_data["D_f1"] = D_f1
            self.prepop_diameter_data["D_f2"] = D_f2
            self.prepop_diameter_data["D_f3"] = D_f3
            self.prepop_diameter_data["fixed_radius_type"] = fixed_radius_type  
            self.prepop_diameter_data["plot_channel_contour"] = plot_channel_contour
            
            debug_log.debug(f"UPDATED prepop_diameter_data: {self.prepop_diameter_data}", context="diameter_gui")
            
            if save_callback:
                debug_log.debug("Calling save_callback...", context="diameter_gui")
                save_callback()#save_callback(show_plot=plot_channel_contour)
            
            return D_f1, D_f2, D_f3, fixed_radius_type, plot_channel_contour
                            
        

        def write_diameters():
            debug_log.debug("Writing using the write_diameters function", context="diameter_gui")
            debug_log.debug("Writing diameter data to JSON...", context="diameter_gui")
            plot_channel_contour=False
            self.meanline_data = meanline(self.Thermodata, self.prepop_meanline_input_data, self.prepop_diameter_data, plot_channel_contour)
            '''
            try: 
               
        def write_diameters(**kwargs):
            """
            Writes the diameter data, which has been updated in self.prepop_diameter_data,
            to the JSON file. This function is called as a callback after the diameter GUI is closed.
            """
            '''
            
            try:
                with open(json_path, 'r') as file:
                    all_json_data = json.load(file)
                new_diameter_data = {}
                
                if self.meanline_data["fixed_radius_type"] == "shroud":
                    new_diameter_data["D_f1"] = self.meanline_data["D_S1"]
                    new_diameter_data["D_f2"] = self.meanline_data["D_S2"]
                    new_diameter_data["D_f3"] = self.meanline_data["D_S3"]
                elif self.meanline_data["fixed_radius_type"] == "mean":
                    new_diameter_data["D_f1"] = self.meanline_data["D_M1"]
                    new_diameter_data["D_f2"] = self.meanline_data["D_M2"]
                    new_diameter_data["D_f3"] = self.meanline_data["D_M3"]
                elif self.meanline_data["fixed_radius_type"] == "hub":
                    new_diameter_data["D_f1"] = self.meanline_data["D_H1"]
                    new_diameter_data["D_f2"] = self.meanline_data["D_H2"]
                    new_diameter_data["D_f3"] = self.meanline_data["D_H3"]   
                    
                new_diameter_data["fixed_radius_type"] = self.meanline_data["fixed_radius_type"]
                new_diameter_data["plot_channel_contour"] = self.meanline_data["plot_channel_contour"]
                
                all_json_data['Diameter_data'] = new_diameter_data
                    

                # The data to be saved is already in self.prepop_diameter_data,
                # which was updated by run_diameter_gui.
                all_json_data['Diameter_data'] = self.prepop_diameter_data

                with open(json_path, 'w') as file:
                    json.dump(all_json_data, file, indent=4)
                status_msg = "Diameter data saved to JSON successfully."
                print(status_msg)
                debug_log.debug(status_msg, context="diameter_gui")
            except Exception as e:
                err_msg = f"Error during JSON write in write_diameters: {e}"
                print(err_msg)
                debug_log.debug(err_msg, context="diameter_gui")
                
                self.prepop_diameter_data = new_diameter_data
                
                status_msg = "Parameters saved and initialized."
                print(status_msg)
                debug_log.debug(status_msg, context="oneD_tab")
            
            except ValueError as e: 
                err_msg = f"Error: {e}"
                print(err_msg)
                debug_log.debug(err_msg, context="oneD_tab")  

        def create_gui():
            
            global entries
            root = parent_frame
            '''
            Reading and saveing dict data from perpopulated data json
            '''
            entries = {}
            params = list(self.prepop_meanline_input_data.keys())

            #ttk.Label(root, text="Meanline Parameter Initialization").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='w')
            #root.Label(self, text="Meanline Parameter Initialization").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='w')
            #root.label("Meanline Parameters Initialization")

            notebook = ttk.Notebook(root)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)

            entries = {}

            for section, params in parameters_sections.items():
                frame = ttk.Frame(notebook)
                notebook.add(frame, text=section)

                for i, param in enumerate(params):
                    gui_name = var_name_to_gui_map[param]
                    ttk.Label(frame, text=f"{gui_name}:").grid(row=i, column=0, padx=5, pady=5, sticky='w')
                    entries[param] = []
                    values = self.prepop_meanline_input_data[param]
                    
                    if param == 'n':
                        entry = ttk.Entry(frame, width=10)
                        entry.insert(0, str(values[0]))  # asks for only one RPM value
                        entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
                        num_stages = self.stage 
                        for _ in range(num_stages):
                            entries[param].append(entry)
                    else:
                        for j, value in enumerate(values):
                            entry = ttk.Entry(frame, width=10)
                            entry.insert(0, str(value))
                            entry.grid(row=i, column=j+1, padx=5, pady=5)
                            entries[param].append(entry)
                    '''
                    # Old. RPM should only be one input box because the value is const over that whole compressor
                    for j, value in enumerate(values):
                        entry = ttk.Entry(frame, width=10)
                        entry.insert(0, str(value))
                        entry.grid(row=i, column=j+1, padx=5, pady=5)
                        entries[param].append(entry)
                    '''
            def save_and_initialize_meanline(show_plot):
                debug_log.debug(f"Writing using the save_and_initialize function. Show_plot = {show_plot}", context="oneD_tab")
                
                ''' 
                Run meanline function to calculate channelcontour   
                ''' 
                self.meanline_data = meanline(self.Thermodata, self.prepop_meanline_input_data, self.prepop_diameter_data, show_plot)

                '''  
                # Load settings from JSON
                try:
                    with open(json_path, 'r') as file:
                        all_json_data = json.load(file)
                    
                    # Load Metadata
                    if 'Metadata' in all_json_data:
                        metadata = all_json_data['Metadata']
                        
                        if 'output_folder' in metadata:
                            self.output_folder_entry.delete(0, tk.END)
                            self.output_folder_entry.insert(0, metadata['output_folder'])
                        
                        if 'levels' in metadata:
                            # Convert list back to comma-separated string
                            levels_str = ', '.join(str(x) for x in metadata['levels'])
                            self.levels_entry.delete(0, tk.END)
                            self.levels_entry.insert(0, levels_str)
                        
                        if 'use_default_rotor_bezier' in metadata:
                            self.use_default_rotor_bezier_var.set(metadata['use_default_rotor_bezier'])
                        
                        if 'use_default_stator_bezier' in metadata:
                            self.use_default_stator_bezier_var.set(metadata['use_default_stator_bezier'])
                        
                        if 'adjust_rotor_thickness' in metadata:
                            self.adjust_rotor_thickness_var.set(metadata['adjust_rotor_thickness'])
                        
                        if 'adjust_rotor_angle' in metadata:
                            self.adjust_rotor_angle_var.set(metadata['adjust_rotor_angle'])
                        
                        if 'adjust_stator_thickness' in metadata:
                            self.adjust_stator_thickness_var.set(metadata['adjust_stator_thickness'])
                        
                        if 'adjust_stator_angle' in metadata:
                            self.adjust_stator_angle_var.set(metadata['adjust_stator_angle'])
                        
                        if 'show_section_plot' in metadata:
                            self.show_section_plot_var.set(metadata['show_section_plot'])
                        
                        if 'show_angle_distribution_plots' in metadata:
                            self.show_angle_distribution_plots_var.set(metadata['show_angle_distribution_plots'])
                    
                    # Load Grid_data
                    if 'Grid_data' in all_json_data:
                        grid_data = all_json_data['Grid_data']
                        
                        if 'nrow' in grid_data:
                            self.nrow_entry.delete(0, tk.END)
                            self.nrow_entry.insert(0, str(grid_data['nrow']))
                    
                    # Load Bleed_air_data
                    if 'Bleed_air_data' in all_json_data:
                        bleed_data = all_json_data['Bleed_air_data']
                        
                        if 'enable_bleed_air' in bleed_data:
                            self.enable_bleed_air_var.set(bleed_data['enable_bleed_air'])
                        
                        if 'rotor_patches' in bleed_data:
                            self.bleed_air_data['rotor']['count'] = bleed_data['rotor_patches']
                        
                        if 'stator_patches' in bleed_data:
                            self.bleed_air_data['stator']['count'] = bleed_data['stator_patches']
                        
                        # Load rotor patches
                        for i in range(bleed_data.get('rotor_patches', 0)):
                            patch_key = f'rotor_patch_{i+1}'
                            if patch_key in bleed_data:
                                self.bleed_air_data['rotor']['patches'].append(bleed_data[patch_key])
                        
                        # Load stator patches
                        for i in range(bleed_data.get('stator_patches', 0)):
                            patch_key = f'stator_patch_{i+1}'
                            if patch_key in bleed_data:
                                self.bleed_air_data['stator']['patches'].append(bleed_data[patch_key])
                    print(f"self.bleed_air_data: {self.bleed_air_data}")
                    
                    # Load Intale_Outtake_area
                    if 'Intale_Outtake_area' in all_json_data:
                        intake_data = all_json_data['Intale_Outtake_area']
                        
                        if 'inlet_area' in intake_data:
                            self.inlet_area_var.set(intake_data['inlet_area'])
                        
                        if 'inlet_dist' in intake_data:
                            self.inlet_dist_var.set(intake_data['inlet_dist'])
                        
                        if 'outlet_area' in intake_data:
                            self.outlet_area_var.set(intake_data['outlet_area'])
                        
                        if 'outlet_dist' in intake_data:
                            self.outlet_dist_var.set(intake_data['outlet_dist'])
                    
                    # Store prepopulated data
                    self.prepop_metadata = all_json_data.get('Metadata', {})
                    self.prepop_grid_data = all_json_data.get('Grid_data', {})
                    self.prepop_bleed_air_data = all_json_data.get('Bleed_air_data', {})
                    self.prepop_intake_outtake = all_json_data.get('Intale_Outtake_area', {})
                    
                    print("Settings loaded successfully from JSON.")

                except FileNotFoundError:
                    print("No previous parameters found. Starting with defaults.")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON file: {e}")
                except Exception as e:
                    print(f"Error loading settings: {e}")

                '''
                try:
                    with open(json_path, 'r') as file:
                        all_json_data = json.load(file)
                                        
                    new_meanline_input_data = {}
                    all_params = [p for params_list in parameters_sections.values() for p in params_list]
                    for param in all_params:
                        if param in ['z_R', 'z_S']:
                            new_meanline_input_data[param] = [int(entry.get()) for entry in entries[param]]
                        else:
                            new_meanline_input_data[param] = [float(entry.get()) for entry in entries[param]]
                    #new_meanline_input_data[param] = float(entries[param].get())

                    all_json_data['Meanline_input_data'] = new_meanline_input_data
                    
                    with open(json_path, 'w') as file:
                        json.dump(all_json_data, file, indent=4)
                    
                    self.prepop_meanline_input_data = new_meanline_input_data
                        
                    status_msg = "Meanline Parameters saved and initialized."
                    print(status_msg)
                    debug_log.debug(status_msg, context="oneD_tab")
                except ValueError:
                    err_msg = "Please enter valid numbers for all conditions. z_R and z_S must be integers."
                    print(err_msg)
                    debug_log.debug(err_msg, context="oneD_tab")
                
                '''
                # Not old used in wrong spot???
                try:
                    with open(json_path, 'r') as file:
                        all_json_data = json.load(file)
                                        
                    new_meanline_input_data = {}
                    all_params = [p for params_list in parameters_sections.values() for p in params_list]
                    for param in all_params:
                        if param in ['z_R', 'z_S']:
                            new_meanline_input_data[param] = [int(entry.get()) for entry in entries[param]]
                        else:
                            new_meanline_input_data[param] = [float(entry.get()) for entry in entries[param]]
                    #new_meanline_input_data[param] = float(entries[param].get())

                    all_json_data['Meanline_input_data'] = new_meanline_input_data
                    
                    with open(json_path, 'w') as file:
                        json.dump(all_json_data, file, indent=4)
                    
                    self.prepop_meanline_input_data = new_meanline_input_data
                        
                    print("Parameters saved and initialized.")
                except ValueError:
                    print("Please enter valid numbers for all conditions. z_R and z_S must be integers.")
                '''

            debug_log.debug(f"self.prepop_diameter_data: {self.prepop_diameter_data}", context="oneD_tab")
            ttk.Button(root, text="Save and Initialize Parameters", command=lambda: save_and_initialize_meanline(show_plot=self.prepop_diameter_data["plot_channel_contour"])).pack(pady=10)
            #ttk.Button(root, text="Save and Initialize Parameters", command=save_and_initialize(show_plot=self.prepop_diameter_data["Plot Channel Contour"])).pack(pady=10)
            ttk.Button(root, text="Change the Channelcontour", command=lambda: run_diameter_gui(i_st_val, self.prepop_diameter_data, write_diameters)).pack(pady=10)
            save_and_initialize_meanline(show_plot = False)
        
        
        # Starts and creates the meanline gui inside of the window
        create_gui()
    
    '''
    3D-Tab and related functions
    '''    
    # region 3D Helper Methods (3D-Tab and related functions)
    
               
    def threeD_tab(self, parent_frame):
    
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
        
        # Misc Variable s
        self.output_folder_entry = tk.Entry()
        self.show_angle_dist_plot_var = tk.BooleanVar()
        

        
        self.main_choice = tk.StringVar(value="default")
        self.specs = {
        "section_idx": tk.StringVar(),
        "row": tk.StringVar(),
        "parameter": tk.StringVar()
        }
        
        self.show_section_plot_var = tk.BooleanVar(value=False) 
        self.show_angle_dist_plot_var = tk.BooleanVar(value=False) 
        
        self.use_default_rotor_bezier_var = tk.BooleanVar(value=False)
        self.use_default_stator_bezier_var = tk.BooleanVar(value=False)
        self.adjust_rotor_thickness_var = tk.BooleanVar(value=False)
        self.adjust_rotor_angle_var = tk.BooleanVar(value=False)
        self.adjust_stator_thickness_var = tk.BooleanVar(value=False)
        self.adjust_stator_angle_var = tk.BooleanVar(value=False)
        
        self.enable_bleed_air_var = tk.BooleanVar(value=False)
        self.enable_bleed_air_var.trace_add("write", self.update_bleed_air_display)
        
        ttk.Label(parent_frame, text="3D Profile Generation and Visualization").pack(pady=10)
        self.sub_notebook = ttk.Notebook(parent_frame)
        self.sub_notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.parameters_frame = ttk.Frame(self.sub_notebook, padding=10)
        self.plot_options_frame = ttk.Frame(self.sub_notebook, padding=10)
        self.bleed_air_frame = ttk.Frame(self.sub_notebook, padding=10)
        self.inlet_outlet_frame = ttk.Frame(self.sub_notebook, padding=10)
        self.output_frame = ttk.Frame(self.sub_notebook, padding=10)
        
        self.sub_notebook.add(self.parameters_frame, text="Profile Parameters")
        self.sub_notebook.add(self.plot_options_frame, text="Plot Options")
        self.sub_notebook.add(self.bleed_air_frame, text="Bleed Air")
        self.sub_notebook.add(self.inlet_outlet_frame, text="Inlet/Outlet")
        #self.sub_notebook.add(self.output_frame, text="Output Settings")
        
        # Creat container frame for inputs for the bleed air
        self.bleed_input_container = ttk.Frame(self.bleed_air_frame)
        self.bleed_input_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        
        # Loading Data for the bleed air and the variable Intake and Outtake Area 
        self.load_bleed_air_and_area_change() 
        
        
        self.setup_parameters_tab()
        self.setup_plot_options_tab()
        self.create_bleed_input_widget()
        self.setup_inlet_outlet_tab()
        
        # Save button for the whole of the 3D-Tab, saving all entered data in these tabs
        # Sits below all of the four tabs
        self.save_button_inlet_outlet = ttk.Button(parent_frame, text="Save", command=self.save_and_initialize_3D_tab)
        self.save_button_inlet_outlet.pack(pady=10, side='bottom')
        
        
        # --- Can Not be ignored ---
        # --- Must be under her (I think) ---
        # Initial call to set up the Bleed AIr Tab based on loaded values
        parent_frame.after(100, lambda: self.update_bleed_air_display())

        
        
        # We dont need this button there is nothing to save there
        # self.save_button = ttk.Button(self.parameters_frame, text="Save and Initialize", command=self.run_action_and_stay_open) 
        # self.save_button.pack(pady=10, padx=10, fill='x')
        
        #self.load_settings()
        
        #self.check_button_states()

    def load_bleed_air_and_area_change(self):
        # Load settings from JSON
        debug_log.debug("Loading settings from json bleed air and co gets called", context="threeD_tab")
        
        try:
            with open(json_path, 'r') as file:
                all_json_data = json.load(file)
            
            # Load Metadata
            if 'Metadata' in all_json_data:
                metadata = all_json_data['Metadata']
                
                
                # Because there is a new Outputfolder definiton 
                if 'output_folder' in metadata:
                    self.output_folder_entry.delete(0, tk.END)
                    self.output_folder_entry.insert(0, metadata['output_folder'])
                
                '''
                # Not needed gets read in in grid defintion function
                if 'levels' in metadata:
                    # Convert list back to comma-separated string
                    
                    levels_str = ', '.join(str(x) for x in metadata['levels'])
                    self.levels_entry.delete(0, tk.END)
                    self.levels_entry.insert(0, levels_str)
                
                if 'levels' in metadata:
                    # Convert list back to comma-separated string
                    levels_str = ', '.join(str(x) for x in metadata['levels'])
                    
                    print(f"[DEBUG] levels_str = {levels_str}")
                    print(f"[DEBUG] self = {self}")
                    print(f"[DEBUG] hasattr levels_entry: {hasattr(self, 'levels_entry')}")
                    print(f"[DEBUG] self.__dict__ keys: {list(self.__dict__.keys())}")
                    
                    if hasattr(self, 'levels_entry'):
                        print(f"[DEBUG] levels_entry widget: {self.levels_entry}")
                        print(f"[DEBUG] levels_entry type: {type(self.levels_entry)}")
                        self.levels_entry.delete(0, tk.END)
                        self.levels_entry.insert(0, levels_str)
                    else:
                        print("[DEBUG] ERROR: levels_entry does not exist on self!")
                        print("[DEBUG] This means the widget was never created or was created on a different instance.")
                       
                        
                if 'levels' in metadata:
                    levels_str = ', '.join(str(x) for x in metadata['levels'])
                    
                    # Debug: check if you have a list of bleed row objects
                    print(f"[DEBUG] dir(self) levels-related: {[x for x in dir(self) if 'level' in x.lower() or 'bleed' in x.lower() or 'row' in x.lower() or 'patch' in x.lower()]}")
                    
                    # Check rotor/stator patch entries since those exist on self
                    print(f"[DEBUG] rotor_patch_entries: {self.rotor_patch_entries}")
                    print(f"[DEBUG] stator_patch_entries: {self.stator_patch_entries}")
                    for i, entry in enumerate(self.rotor_patch_entries):
                        print(f"[DEBUG] rotor_patch_entries[{i}] type: {type(entry)}, attrs: {[x for x in dir(entry) if 'level' in x.lower()]}")
                    for i, entry in enumerate(self.stator_patch_entries):
                        print(f"[DEBUG] stator_patch_entries[{i}] type: {type(entry)}, attrs: {[x for x in dir(entry) if 'level' in x.lower()]}")
                
                ''' 
                
                        
                if 'use_default_rotor_bezier' in metadata:
                    self.use_default_rotor_bezier_var.set(metadata['use_default_rotor_bezier'])
                
                if 'use_default_stator_bezier' in metadata:
                    self.use_default_stator_bezier_var.set(metadata['use_default_stator_bezier'])
                
                if 'adjust_rotor_thickness' in metadata:
                    self.adjust_rotor_thickness_var.set(metadata['adjust_rotor_thickness'])
                
                if 'adjust_rotor_angle' in metadata:
                    self.adjust_rotor_angle_var.set(metadata['adjust_rotor_angle'])
                
                if 'adjust_stator_thickness' in metadata:
                    self.adjust_stator_thickness_var.set(metadata['adjust_stator_thickness'])
                
                if 'adjust_stator_angle' in metadata:
                    self.adjust_stator_angle_var.set(metadata['adjust_stator_angle'])
                
                if 'show_section_plot' in metadata:
                    self.show_section_plot_var.set(metadata['show_section_plot'])
                
                if 'show_angle_distribution_plots' in metadata:
                    self.show_angle_dist_plot_var.set(metadata['show_angle_distribution_plots'])
            
            # Load Grid_data
            if 'Grid_data' in all_json_data:
                grid_data_not_in_use_yet = all_json_data['Grid_data']
                '''
                # Potential Addition to Prepopulted Grid Gui Tab with the last used values
                if 'nrow' in grid_data:
                    self.nrow_entry.delete(0, tk.END)
                    self.nrow_entry.insert(0, str(grid_data['nrow']))
                '''
            # Load Bleed_air_data
            if 'Bleed_air_data' in all_json_data:
                bleed_data = all_json_data['Bleed_air_data']
                
                if 'enable_bleed_air' in bleed_data:
                    self.enable_bleed_air_var.set(bleed_data['enable_bleed_air'])
                
                if 'rotor_patches' in bleed_data:
                    self.bleed_air_data['rotor']['count'] = bleed_data['rotor_patches']
                
                if 'stator_patches' in bleed_data:
                    self.bleed_air_data['stator']['count'] = bleed_data['stator_patches']
                
                # Load rotor patches
                for i in range(bleed_data.get('rotor_patches', 0)):
                    patch_key = f'rotor_patch_{i+1}'
                    if patch_key in bleed_data:
                        self.bleed_air_data['rotor']['patches'].append(bleed_data[patch_key])
                
                # Load stator patches
                for i in range(bleed_data.get('stator_patches', 0)):
                    patch_key = f'stator_patch_{i+1}'
                    if patch_key in bleed_data:
                        self.bleed_air_data['stator']['patches'].append(bleed_data[patch_key])
            debug_log.debug(f"self.bleed_air_data: {self.bleed_air_data}", context="threeD_tab")
            
            # Load Intake_Outtake_area
            if 'Intake_Outtake_area' in all_json_data:
                intake_data = all_json_data['Intake_Outtake_area']
                
                if 'inlet_area' in intake_data:
                    self.inlet_area_var.set(intake_data['inlet_area'])
                
                if 'inlet_dist' in intake_data:
                    self.inlet_dist_var.set(intake_data['inlet_dist'])
                
                if 'outlet_area' in intake_data:
                    self.outlet_area_var.set(intake_data['outlet_area'])
                
                if 'outlet_dist' in intake_data:
                    self.outlet_dist_var.set(intake_data['outlet_dist'])
            
            # Store prepopulated data
            self.prepop_metadata = all_json_data.get('Metadata', {})
            self.prepop_grid_data = all_json_data.get('Grid_data', {})
            self.prepop_bleed_air_data = all_json_data.get('Bleed_air_data', {})
            self.prepop_intake_outtake = all_json_data.get('Intake_Outtake_area', {})
            
            status_msg = "Settings loaded successfully from JSON."
            print(status_msg)
            debug_log.debug(status_msg, context="load_settings")
            debug_log.debug("", context="load_settings")
        except FileNotFoundError:
            status_msg = "No previous parameters found. Starting with defaults."
            print(status_msg)
            debug_log.debug(status_msg, context="load_settings")
        except json.JSONDecodeError as e:
            err_msg = f"Error parsing JSON file: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="load_settings")
        except Exception as e:
            err_msg = f"Error loading settings: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="load_settings")

        
    def setup_inlet_outlet_tab(self):
        self.inlet_outlet_title_frame = ttk.Frame(self.inlet_outlet_frame)
        self.inlet_outlet_title_frame.pack(fill='x', padx=10, pady=10)
        
        self.inlet_outlet_title_label = ttk.Label (self.inlet_outlet_title_frame, text="Inlet and Outlet Geometry Definition")
        self.inlet_outlet_title_label.pack(side='left', padx= (0, 5))
        
        self.inlet_outlet_help = ttk.Label(self.inlet_outlet_title_frame, text= "?", cursor="question_arrow")
        self.inlet_outlet_help.pack(side='left', padx=(5, 0))
        self.inlet_outlet_help_text = "Define the geometry parameters of the Inlet and Outlet Area"
        Tooltip(self.inlet_outlet_help, self.inlet_outlet_help_text)
        
        self.inlet_frame = ttk.LabelFrame(self.inlet_outlet_frame, text="Inlet Area Definition")
        self.inlet_frame.pack(fill='x', padx=10, pady=10)
        
        # Inlet 
        self.inlet_area_label = ttk.Label(self.inlet_frame, text="Inlet Area")
        self.inlet_area_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        # Area
        self.inlet_area_help = ttk.Label(self.inlet_frame, text= "?", cursor="question_arrow")
        self.inlet_area_help.grid(row=0, column=2, padx=(5, 0))
        self.inlet_area_help_text = "Enter the Size of the Inlet as a factor of the Diameter of the first Blade Row. Default = 1 (same Size as the Diameter of the first Blade Row)"
        Tooltip(self.inlet_area_help, self.inlet_area_help_text)
        
        self.inlet_area_entry = ttk.Entry(self.inlet_frame, width=10, textvariable=self.inlet_area_var)
        self.inlet_area_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Distance
        self.inlet_dist_label = ttk.Label(self.inlet_frame, text="Inlet Distance")
        self.inlet_dist_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        self.inlet_dist_help = ttk.Label(self.inlet_frame, text= "?", cursor="question_arrow")
        self.inlet_dist_help.grid(row=1, column=2, padx=(5, 0))
        self.inlet_dist_help_text = "Enter the Distanz of the Inlet to the first stage as a factor of the first Blade length. Default = 2 (length between the Inlet and the first Blade Row is equal to two times the Blade length) "
        Tooltip(self.inlet_dist_help, self.inlet_dist_help_text)
        
        self.inlet_dist_entry = ttk.Entry(self.inlet_frame, width=10, textvariable=self.inlet_dist_var)
        self.inlet_dist_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Outlet        
        self.outlet_frame = ttk.LabelFrame(self.inlet_outlet_frame, text="Outlet Area Definition")
        self.outlet_frame.pack(fill='x', padx=10, pady=10)
        
        # Area
        self.outlet_area_label = ttk.Label(self.outlet_frame, text="Outlet Area")
        self.outlet_area_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.outlet_area_help = ttk.Label(self.outlet_frame, text= "?", cursor="question_arrow")
        self.outlet_area_help.grid(row=0, column=2, padx=(5, 0))
        self.outlet_area_help_text = "Enter the Size of the Outlet as a factor of the Diameter of the last Blade Row. Default = 1 (same Size as the Diameter of the last Blade Row)"
        Tooltip(self.outlet_area_help, self.outlet_area_help_text)
        
        debug_log.debug(f"self.outlet_area_var: {self.outlet_area_var.get()}", context="threeD_tab")
        self.outlet_area_entry = ttk.Entry(self.outlet_frame, width=10, textvariable=self.outlet_area_var)
        self.outlet_area_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Distanz
        self.outlet_dist_label = ttk.Label(self.outlet_frame, text="Outlet Distance")
        self.outlet_dist_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        
        self.outlet_dist_help = ttk.Label(self.outlet_frame, text= "?", cursor="question_arrow")
        self.outlet_dist_help.grid(row=1, column=2, padx=(5, 0))
        outlet_dist_help_text = "Enter the Distanz of the last Blade row to the Outlet as a factor of the last Blade length. Default = 2 (length between the last Blade Row and the Output is equal to two times the Blade length) "
        Tooltip(self.outlet_dist_help, outlet_dist_help_text)
        
        self.outlet_dist_entry = ttk.Entry(self.outlet_frame, width=10, textvariable=self.outlet_dist_var)
        self.outlet_dist_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Save Button
        '''
        # Save button moves to below all tabs
        self.save_button_inlet_outlet = ttk.Button(self.inlet_outlet_frame, text="Save", command=self.save_and_initialize_3D_tab)
        self.save_button_inlet_outlet.pack(pady=10, side='bottom')
        '''
        
        
    def update_bleed_air_display(self, *args):
        # 1. Safety Check: Does the widget exist in the Tcl interpreter?
        try:
            if not self.bleed_input_container.winfo_exists():
                return
        except (AttributeError, tk.TclError):
            # If the attribute isn't set yet or Tcl can't find the path, stop here
            return

        # 2. Logic to show or hide the container
        if self.enable_bleed_air_var.get():
            # Check if it's already visible to avoid redundant 'packing'
            if not self.bleed_input_container.winfo_ismapped():
                self.bleed_input_container.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Call your widget creation/update logic
            self.create_bleed_input_widget()
        else:
            # Safely hide it if it's currently visible
            if self.bleed_input_container.winfo_ismapped():
                self.bleed_input_container.pack_forget()    
        
    ''' 
    # Old: newone above to fix timing issue of rendering children  
    def update_bleed_air_display(self, *args):
        
        
        if self.enable_bleed_air_var.get():
            self.bleed_input_container.pack(fill='both', expand=True, padx=10, pady=10)
            self.create_bleed_input_widget()
        else:
            self.bleed_input_container.pack_forget()
    '''         
    def create_bleed_input_widget(self):
            # Clear existing Widgets
            for widget in self.bleed_air_frame.winfo_children():
                widget.destroy()
                
            # Split window into two sides for Rotor and Stator
            self.rotor_frame = ttk.Frame(self.bleed_air_frame)
            self.rotor_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            
            self.stator_frame = ttk.Frame(self.bleed_air_frame)
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
            num_patches_entry = self.rotor_patches_entry
            #num_patches_str = self.rotor_patches_entry.get()
            parent_frame = self.rotor_frame
            # Save patches data in dedicated list
            self.rotor_patch_entries.clear()
            patches_data = self.bleed_air_data['rotor']['patches']
        else:
            num_patches_entry = self.stator_patches_entry
            #num_patches_str = self.stator_patches_entry.get()
            parent_frame = self.stator_frame
            # Save patches data in dedicated list
            self.stator_patch_entries.clear()
            patches_data = self.bleed_air_data['stator']['patches']
        
        # Get the count we actually have in our data
        loaded_count = self.bleed_air_data[blade_type]['count']
        
        # If the UI says 0 (or is empty) but we have data, update the UI first
        current_ui_val = num_patches_entry.get()
        if (not current_ui_val or current_ui_val == "0") and loaded_count > 0:
            num_patches_entry.delete(0, tk.END)
            num_patches_entry.insert(0, str(loaded_count))

        num_patches_str = num_patches_entry.get()
         
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
        
        # Building stage list from self.stage  for the dropdown to choose which stage 
        stage_options = [f"Stage {i+1}" for i in range(self.stage)] if hasattr(self, 'stage') and self.stage > 0 else ["Stage 1"]
        
        # Creat new Input widget for each Patch
        for i in range(num_patches):
            patch_frame = ttk.LabelFrame(parent_frame, text=f"Bleed Air Patch {i+1}")
            patch_frame.pack(fill='x',padx=5, pady=5)
            
            patch_entries = []
            
            
            # Stage selection Dropdown menu at the top of each patch
            stage_label = ttk.Label(patch_frame, text="Stage:")
            stage_label.grid(row=0,column=0,padx=5, pady=2, sticky='w')
            stage_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            stage_q_label.grid(row=0, column=3, padx=2, pady=2, sticky='w')
            Tooltip(stage_q_label, "Select which stage this bleed air patch applies to")
            stage_var = tk.StringVar(value=stage_options[0])
            stage_dropdown = ttk.Combobox(patch_frame, textvariable=stage_var, values=stage_options, state="readonly", width=10)
            stage_dropdown.grid(row=0, column=1, columnspan=2, padx=5, pady=2)
            

            
            # I coordinates
            i_label = ttk.Label(patch_frame, text="I start/end:")
            i_label.grid(row=1,column=0,padx=5, pady=2, sticky='w')
            i_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            i_q_label.grid(row=1, column=3, padx=2, pady=2, sticky='w')
            Tooltip(i_q_label, " The I-Coordinates define the Spanwise direction. If using standard Grid and Blade settings, choose Values between 1 and 37. If you want to have bleed air over the whole spane enter 1 and 37")
            i_start_entry = ttk.Entry(patch_frame, width=5)
            i_start_entry.grid(row=1, column=1, padx=5, pady=2)
            i_end_entry = ttk.Entry(patch_frame, width=5)
            i_end_entry.grid(row=1, column=2, padx=5, pady=2)
            
            # J coordinates
            j_label = ttk.Label(patch_frame, text="J start/end:")
            j_label.grid(row=2,column=0,padx=5, pady=2, sticky='w')
            j_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            j_q_label.grid(row=2, column=3, padx=2, pady=2, sticky='w')
            Tooltip(j_q_label, f"The J-Coordinates define the Axial direction. With default Gird and Bladevalues 1 is defined as the start of the Blade while 96 is defined as the End of the blade")
            j_start_entry = ttk.Entry(patch_frame, width=5)
            j_start_entry.grid(row=2, column=1, padx=5, pady=2)
            j_end_entry = ttk.Entry(patch_frame, width=5)
            j_end_entry.grid(row=2, column=2, padx=5, pady=2)
            
            # K coordinates
            k_label = ttk.Label(patch_frame, text="K start/end:")
            k_label.grid(row=3,column=0,padx=5, pady=2, sticky='w')
            k_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            k_q_label.grid(row=3, column=3, padx=2, pady=2, sticky='w')
            Tooltip(k_q_label, "The K-Coordinate is defined as the Radial direction with 1 being the Hub wall and 37 being the Shroud wall (for the standard Grid and channel Settings). If you only want Bleed air to be extracted from one of the wall enter 1 and 1 or 37 and 37. It is also possible to extract Bleed air from the Stators and Rotors")
            k_start_entry = ttk.Entry(patch_frame, width=5)
            k_start_entry.grid(row=3, column=1, padx=5, pady=2)
            k_end_entry = ttk.Entry(patch_frame, width=5)
            k_end_entry.grid(row=3, column=2, padx=5, pady=2)
            
            # Massflow
            mflow_label = ttk.Label(patch_frame, text="Extraced Bleed Air (kg/s):")
            mflow_label.grid(row=4, column=0, padx=5, pady=2, sticky='w')
            mflow_q_label = ttk.Label(patch_frame, text="?", cursor="question_arrow")
            mflow_q_label.grid(row=4, column=3, padx=2, pady=2, sticky='w')
            Tooltip(mflow_q_label, "The massflow rate is defined in kg/s. Specify how much Bleed air you want to be extracted in this Bleed air patch")
            massflow_entry = ttk.Entry(patch_frame, width=10)
            massflow_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=2)
            
            # Store Enter entries
            patch_entries.extend([stage_var, i_start_entry, i_end_entry, j_start_entry, j_end_entry, k_start_entry, k_end_entry, massflow_entry])
            
            
            debug_log.debug(f"patch_entries: {patch_entries}", context="threeD_tab")
            # Insert loaded values if exisiting
            if i < len(patches_data):
                saved_patch = patches_data[i]
                # Load stage (index 0)
                if len(saved_patch) > 0 and saved_patch[0] in stage_options:
                    stage_var.set(saved_patch[0])
                # Load remaining entries (indices 1-7 in saved data into entries index 1-7)
                for idx, entry in enumerate(patch_entries[1:], start=1):
                    if idx < len(saved_patch):
                        entry.insert(0, saved_patch[idx])
                        
            if blade_type == 'rotor':
                self.rotor_patch_entries.append(patch_entries)
            else: 
                self.stator_patch_entries.append(patch_entries)
            

    '''
    def check_button_states(self):
        rotor_exists = os.path.exists("bezier_control_points_R.txt")
        stator_exists = os.path.exists("bezier_control_points_S.txt")
    
        # Enable or disable buttons based on file existence
        if rotor_exists and stator_exists:
            self.create_profiles_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.NORMAL)
        else:
            self.create_profiles_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.DISABLED)
    '''
        
    def create_profiles_and_update_gui(self):
        create_default_profiles(self, json_path)
        #self.check_button_states()

    
    def setup_parameters_tab(self):
    
        # main_frame = ttk.Frame(self.root, padding="10")
        # main_frame.pack(fill="both", expand=True) # Gruppierungscontainer
    
        choice_frame = ttk.LabelFrame(self.parameters_frame, text="Bezier Profile Import / Export")
        choice_frame.pack(fill='x', padx=5, pady=5)
        
        self.create_profiles_button = ttk.Button(choice_frame, text="Create Default Profile(s)", command=self.create_profiles_and_update_gui) # Button zum Erstellen der Profile
        self.create_profiles_button.pack(pady=5, padx=10, fill='x')
        
        self.load_rotor_button = ttk.Button(choice_frame, text="Load Rotor Profile", command=lambda: self.import_bezier_from_txt('rotor')) # Selection for loading profile
        self.load_rotor_button.pack(fill='x', padx=10, pady=5)
        self.load_stator_button = ttk.Button(choice_frame, text="Load Stator Profile", command=lambda: self.import_bezier_from_txt('stator')) # Selection for loading profile
        self.load_stator_button.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(choice_frame, text="Export Profiles to TXT", command=self.export_bezier_to_txt).pack(fill='x', padx=10, pady=5)

        adjust_frame = ttk.LabelFrame(self.parameters_frame, text="Adjust Profiles")
        adjust_frame.pack(fill='x', padx=5, pady=5)
        self.adjust_profiles_button = ttk.Button(adjust_frame, text="Make a specific adjustment", command= self.open_specification_window)
        self.adjust_profiles_button.pack(pady=5, padx=10, fill='x')

        
        
        # Is this needed?
        def save_adjustments_to_json(self, new_adjust_values):
        
            try:
                with open(json_path, 'r') as file:
                    all_json_data = json.load(file)
                    
                new_adjust_values = {}
                all_json_data['Adjust_Settings'] = new_adjust_values
                
                with open(json_path, 'w') as file:
                    json.dump(all_json_data, file, indent=4)
                    
                status_msg = "Adjust settings successfully saved to JSON."
                print(status_msg)
                debug_log.debug(status_msg, context="threeD_tab")
                
                self.prepop_adjust_data = new_adjust_values
                
            except Exception as e:
                err_msg = f"Error saving adjust settings to JSON: {e}"
                print(err_msg)
                debug_log.debug(err_msg, context="threeD_tab")
                
    
    def export_bezier_to_txt(self):
        import json
        import os
        from tkinter import filedialog, messagebox

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            bezier_data = data.get("Bezier_point_data", {})
            if not bezier_data:
                messagebox.showerror("Error", "No Bezier data found in JSON! Please generate profiles first.")
                return
                
            export_dir = filedialog.askdirectory(title="Choose a folder to save the TXT files")
            if not export_dir:
                return
                
            for blade_type in ["rotor", "stator"]:
                if blade_type in bezier_data:
                    b_data = bezier_data[blade_type]
                    angle_key = "beta_S" if blade_type == "rotor" else "alpha_S"
                    filename = f"bezier_control_points_{'R' if blade_type == 'rotor' else 'S'}.txt"
                    filepath = os.path.join(export_dir, filename)
                    
                    with open(filepath, "w") as f:
                        f.write(f"For each level h/H = [0, 0.2, 0.5, 0.8, 1.0]\n\n")
                        f.write(f"1st to 4th control points for {angle_key} for all levels:\n")
                        
                        angles = b_data.get(angle_key, [0]*20)
                        for i in range(4):
                            row_vals = angles[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
                        f.write("\n1st to 4th control points for d/l for all levels:\n")
                        thicks = b_data.get("d/l", [0]*20)
                        for i in range(4):
                            row_vals = thicks[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
                        f.write("\nm* for all levels:\n")
                        mstars = b_data.get("m*", [0.0]*5 + [0.3]*5 + [0.7]*5 + [1.0]*5)
                        for i in range(4):
                            row_vals = mstars[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
            messagebox.showinfo("Success", f"Profil successfully exported to:\n{export_dir}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Export gone wrong: {e}")

    


    def setup_plot_options_tab(self):
        rotor_frame = ttk.LabelFrame(self.plot_options_frame, text="Rotor Profile")
        rotor_frame.pack(fill='x', padx=5, pady=5)
        
        stator_frame = ttk.LabelFrame(self.plot_options_frame, text="Stator Profile")
        stator_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(rotor_frame, text="Show geometry plot", command=self.show_plots_section_rotor).pack(fill='x', padx=10, pady=10)
        ttk.Button(rotor_frame, text="Show angle distribution plot", command=self.show_plots_angle_rotor).pack(fill='x', padx=10, pady=10)
        ttk.Button(rotor_frame, text="Show thickness distribution plot", command=self.show_plots_thickness_rotor).pack(fill='x', padx=10, pady=10)
        
        ttk.Button(stator_frame, text="Show geometry plot", command=self.show_plots_section_stator).pack(fill='x', padx=10, pady=10)
        ttk.Button(stator_frame, text="Show angle distribution plot", command=self.show_plots_angle_stator).pack(fill='x', padx=10, pady=10)
        ttk.Button(stator_frame, text="Show thickness distribution plot", command=self.show_plots_thickness_stator).pack(fill='x', padx=10, pady=10)
        
        
    def export_bezier_to_txt(self):
        import json
        import os
        from tkinter import filedialog, messagebox

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            bezier_data = data.get("Bezier_point_data", {})
            if not bezier_data:
                messagebox.showerror("Error", "No Bezier data found in JSON! Please generate profiles first.")
                return
                
            export_dir = filedialog.askdirectory(title="Select the folder to save the TXT files")
            if not export_dir:
                return
                
            # Writes both files (Rotor and Stator) into the selected directory
            for blade_type in ["rotor", "stator"]:
                if blade_type in bezier_data:
                    b_data = bezier_data[blade_type]
                    angle_key = "beta_S" if blade_type == "rotor" else "alpha_S"
                    filename = f"bezier_control_points_{'R' if blade_type == 'rotor' else 'S'}.txt"
                    filepath = os.path.join(export_dir, filename)
                    
                    with open(filepath, "w") as f:
                        f.write(f"For each level h/H = [0, 0.2, 0.5, 0.8, 1.0]\n\n")
                        f.write(f"1st to 4th control points for {angle_key} for all levels:\n")
                        
                        angles = b_data.get(angle_key, [0]*20)
                        for i in range(4):
                            row_vals = angles[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
                        f.write("\n1st to 4th control points for d/l for all levels:\n")
                        thicks = b_data.get("d/l", [0]*20)
                        for i in range(4):
                            row_vals = thicks[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
                        f.write("\nm* for all levels:\n")
                        mstars = b_data.get("m*", [0.0]*5 + [0.3]*5 + [0.7]*5 + [1.0]*5)
                        for i in range(4):
                            row_vals = mstars[i*5:(i+1)*5]
                            f.write(", ".join(map(str, row_vals)) + "\n")
                            
            messagebox.showinfo("Success", f"Profiles successfully exported to:\n{export_dir}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Export failed: {e}")

    def import_bezier_from_txt(self, blade_type):
        import json
        from tkinter import filedialog, messagebox

        # Opens the file dialog to select the .txt file
        filepath = filedialog.askopenfilename(title=f"Select the {blade_type.capitalize()} TXT file", filetypes=[("Text files", "*.txt")])
        if not filepath:
            return
            
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
                
            angle_key = "beta_S" if blade_type == "rotor" else "alpha_S"
            
            # Helper function to extract exactly the 4 lines below a specific header
            def extract_block(header_text):
                block = []
                idx = -1
                for i, line in enumerate(lines):
                    if header_text in line:
                        idx = i
                        break
                if idx != -1:
                    for i in range(1, 5):
                        vals = [float(v.strip()) for v in lines[idx+i].split(",")]
                        block.extend(vals)
                return block
                
            angles = extract_block(f"1st to 4th control points for {angle_key}")
            thicks = extract_block("1st to 4th control points for d/l")
            mstars = extract_block("m* for all levels")
            
            if len(angles) != 20 or len(thicks) != 20:
                messagebox.showerror("Error", "The file does not have the expected format! Values are missing.")
                return
                
            # Silently saves the newly extracted TXT data into the JSON
            with open(json_path, "r") as f:
                data = json.load(f)
                
            if "Bezier_point_data" not in data:
                data["Bezier_point_data"] = {}
            if blade_type not in data["Bezier_point_data"]:
                data["Bezier_point_data"][blade_type] = {}
                
            data["Bezier_point_data"][blade_type]["h/H"] = [0.0, 0.2, 0.5, 0.8, 1.0]
            data["Bezier_point_data"][blade_type][angle_key] = angles
            data["Bezier_point_data"][blade_type]["d/l"] = thicks
            data["Bezier_point_data"][blade_type]["m*"] = mstars
            
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
                
            # Update the GUI instance memory so the program knows about the new values immediately
            if blade_type == "rotor":
                self.prepop_bezier_point_rotor = data["Bezier_point_data"][blade_type]
            else:
                self.prepop_bezier_point_stator = data["Bezier_point_data"][blade_type]
                
            messagebox.showinfo("Success", f"The {blade_type.capitalize()} profile was successfully imported into the JSON! The script will now use these values for calculation.")
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Import failed: {e}")
        
    
    def open_specification_window(self):

        def apply_adjustments():
            settings_adjustments = {
                'main_choice': 'adjust',
                'adjust_section_idx': self.specs["section_idx"].get().split(" ")[0],
                'adjust_row': self.specs["row"].get(),
                'adjust_parameter': self.specs["parameter"].get(),
                'levels': self.levels_entry.get(),
                'nrow': 1 if self.nrow_combo.get() == "Rotor Only" else 2
            }
            run_main_logic(settings_adjustments, self, json_path)
        
        spec_window = tk.Toplevel(self.root)
        spec_window.title("Adjustments")
        spec_window.transient(self.root) # Fenster bleibt im Vordergrund
        spec_window.grab_set() # Prevents changes to the sub-window
    
        frame = ttk.Frame(spec_window, padding="15")
        frame.pack(expand=True, fill="both")
    
        # Creates a dropdown menu 
        ttk.Label(frame, text="Section Plan to change:").grid(row=0, column=0, sticky='w', pady=5)
        
        section_combo = ttk.Combobox(frame, textvariable=self.specs["section_idx"], values=['0.0', '0.2', '0.5', '0.8', '1.0'], state="readonly")
        section_combo.grid(row=0, column=1, pady=5)
        section_combo.current(2)
    
        ttk.Label(frame, text="Blade Row:").grid(row=1, column=0, sticky='w', pady=5)
        row_combo = ttk.Combobox(frame, textvariable=self.specs["row"], value=['Rotor', 'Stator'], state="readonly")
        row_combo.grid(row=1, column=1, pady=5)
        row_combo.current(0)
    
        ttk.Label(frame, text="Parameter to Adjust:").grid(row=2, column=0, sticky='w', pady=5)
        parameter_combo = ttk.Combobox(frame, textvariable=self.specs["parameter"], value=['Angle', 'Thickness'], state="readonly")
        parameter_combo.grid(row=2, column=1, pady=5)
        parameter_combo.current(0)
    
        ttk.Button(frame, text="Adjust Profile", command=apply_adjustments).grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(frame, text="Close", command=spec_window.destroy).grid(row=4, column=0, columnspan=2, pady=15)
        
    def browse_output_folder(self):
        path = filedialog.askdirectory()
        if path:  
            # Glaube das sollte nicht klappen weil du hast dein outputfolder anders genannt in deiner gui als in der originalen GUI          
            self.output_folder_entry.delete(0, tk.END) # Deletes old contents
            self.output_folder_entry.insert(0, path) # Neuer Pfad

    def load_rotor_settings(self):
    
        filepath = filedialog.askopenfilename(title="Select Rotor Bezier Points File", filetypes=[("Text Files", "*.txt")])
        if filepath:
            
            try:
                if os.path.samefile(filepath, "bezier_control_points_R.txt"):
                    msg = "This file already exists."
                    print(msg)
                    debug_log.debug(msg, context="threeD_tab")
                    return
            except FileNotFoundError:
                pass
            
            shutil.copy(filepath, "bezier_control_points_R.txt")
            msg = f"Rotor Profile loaded: {filepath}"
            print(msg)
            debug_log.debug(msg, context="threeD_tab")

        
    def load_stator_settings(self):
        filepath = filedialog.askopenfilename(title="Select Stator Bezier Points File", filetypes=[("Text Files", "*.txt")])
        if filepath:
                        
            try:
                if os.path.samefile(filepath, "bezier_control_points_S.txt"):
                    msg = "This file already exists."
                    print(msg)
                    debug_log.debug(msg, context="threeD_tab")
                    return
            except FileNotFoundError:
                pass
            
            shutil.copy(filepath, "bezier_control_points_S.txt")
            msg = f"Stator Profile loaded: {filepath}"
            print(msg)
            debug_log.debug(msg, context="threeD_tab")

    '''
    # not in use anymore
    def save_and_initialize_old(self):
        
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
        show_angle_distribution_plots = self.show_angle_dist_plot_var.get()
        
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

        print("Parameters saved successfully.")
    '''
    # --- Used for the saving of the 3D tab currently located in the Area change tab of the 3 d tab ---
        
    def save_and_initialize_3D_tab(self):
        try:
            # Read existing JSON data
            with open(json_path, 'r') as file:
                all_json_data = json.load(file)
            
            # Parse levels string to list of floats
            levels_str = self.levels_entry.get()
            levels_list = [float(x.strip()) for x in levels_str.split(',')]
            
            # Save Metadata
            new_metadata = {
                "output_folder": self.output_folder_entry.get(),
                "main_choice": "default",
                "levels": levels_list,
                "use_default_rotor_bezier": self.use_default_rotor_bezier_var.get(),
                "use_default_stator_bezier": self.use_default_stator_bezier_var.get(),
                "adjust_rotor_thickness": self.adjust_rotor_thickness_var.get(),
                "adjust_rotor_angle": self.adjust_rotor_angle_var.get(),
                "adjust_stator_thickness": self.adjust_stator_thickness_var.get(),
                "adjust_stator_angle": self.adjust_stator_angle_var.get(),
                "show_section_plot": self.show_section_plot_var.get(),
                "show_angle_distribution_plots": self.show_angle_dist_plot_var.get()
            }
            all_json_data['Metadata'] = new_metadata
            
            '''
            # Grid data can be ignored here
            # Save Grid_data
            new_grid_data = {
                "nrow": int(self.nrow_entry.get())
            }
            
            all_json_data['Grid_data'] = new_grid_data
            '''
            
            # Save Bleed_air_data
            enable_bleed_air = self.enable_bleed_air_var.get()
            new_bleed_air_data = {
                "enable_bleed_air": enable_bleed_air,
                "rotor_patches": len(self.rotor_patch_entries) if enable_bleed_air else 0,
                "stator_patches": len(self.stator_patch_entries) if enable_bleed_air else 0
            }
            
            if enable_bleed_air:
                # Save rotor patches
                for i, entries in enumerate(self.rotor_patch_entries):
                    patch_data = [
                        entries[0].get(),
                        int(entries[1].get()),
                        int(entries[2].get()),
                        int(entries[3].get()),
                        int(entries[4].get()),
                        int(entries[5].get()),
                        int(entries[6].get()),
                        float(entries[7].get())
                    ]
                    new_bleed_air_data[f"rotor_patch_{i+1}"] = patch_data
                
                # Save stator patches
                for i, entries in enumerate(self.stator_patch_entries):
                    patch_data = [
                        entries[0].get(),
                        int(entries[1].get()),
                        int(entries[2].get()),
                        int(entries[3].get()),
                        int(entries[4].get()),
                        int(entries[5].get()),
                        int(entries[6].get()),
                        float(entries[7].get())
                    ]
                    new_bleed_air_data[f"stator_patch_{i+1}"] = patch_data
            
            all_json_data['Bleed_air_data'] = new_bleed_air_data
            
            # Save Intake_Outtake_area
            new_intake_outtake = {
                "inlet_area": float(self.inlet_area_var.get()),
                "inlet_dist": float(self.inlet_dist_var.get()),
                "outlet_area": float(self.outlet_area_var.get()),
                "outlet_dist": float(self.outlet_dist_var.get())
            }
            all_json_data['Intake_Outtake_area'] = new_intake_outtake
            
            # Write back to JSON
            with open(json_path, 'w') as file:
                json.dump(all_json_data, file, indent=4)
            
            # Update prepopulated data 
            self.prepop_metadata = new_metadata
            #self.prepop_grid_data = new_grid_data not saving grid data here
            self.prepop_bleed_air_data = new_bleed_air_data
            self.prepop_intake_outtake = new_intake_outtake
            
            status_msg = "3D-Parameters saved and initialized."
            print(status_msg)
            debug_log.debug(status_msg, context="threeD_tab")
            
        except ValueError as e:
            err_msg = f"Error: Please enter valid numbers. {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="threeD_tab")
        except Exception as e:
            err_msg = f"Error saving settings: {e}"
            print(err_msg)
            debug_log.debug(err_msg, context="threeD_tab")
        
    def save_settings(self):
        with open('Settings.txt', 'w') as file:
            file.write(f"main_choice = {self.main_choice.get()}\n") # Holt sich die User Auswahl aus dem Radiobutton
        
            if self.main_choice.get() == 'adjust': # only if Adjust was selected
                section_str = self.specs["section_idx"].get().split(" ")[0] 
                section_map = {'0.0': 0, '0.2': 1, '0.5': 2, '0.8': 3, '1.0': 4}
                file.write(f"adjust_section_idx = {section_map.get(section_str, 2)}\n")
                file.write(f"adjust_row = {self.specs['row'].get()}\n")
                file.write(f"adjust_parameter = {self.specs['parameter'].get()}\n")
            
            file.write(f"levels = {self.levels_entry.get()}\n")
        print("Settings saved")
        debug_log.debug("Settings saved", context="save_settings")
    
    # def load_settings(self):
    #     try:
    #         settings = {}
    #         with open('Settings.txt', 'r') as file:
    #             for line in file:
    #                 line = line.strip()
    #                 if ' = ' in line:
    #                     try:
    #                         key, value = line.split(' = ', 1)
    #                         settings[key] = value
    #                     except ValueError:
    #                         continue    
                
    #         self.show_section_plot_var.set(settings.get('show_section_plot', "False"))
    #         self.show_angle_dist_plot_var.set(settings.get('show_angle_dist_plot', "False")) 
            
    #         self.levels_entry.insert(0, settings.get('levels', '0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.00'))
    #         nrow_value = int(settings.get('nrow', 2))
    #         self.nrow_combo.set("Rotor Only" if nrow_value == 1 else "Complete Stage (Rotor & Stator)")
    #     except FileNotFoundError:
    #         self.levels_entry.insert(0, '0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.00')
    #         self.nrow_combo.set("Complete Stage (Rotor & Stator)")
### Everything above still needs to be replaced by a load method. Copied here only for functionality

    # def run_action_and_stay_open(self): # Saves everything and does not close the window
    #     settings = {
    #         "main_choice": self.main_choice.get(),
    #     }

    #     nrow_choice = self.nrow_combo.get()
    #     settings["nrow"] = 1 if nrow_choice == "Rotor Only" else 2
        
    #     settings["levels"] = self.levels_entry.get()
        
    #     if settings["main_choice"] == "adjust":
    #         section_str = self.specs["section_idx"].get()
    #         section_map = {'0.0': 0, '0.1':1, '0.2': 2, '0.3': 3, '0.4': 4, '0.5': 5, '0.6': 6, '0.7': 7, '0.8': 8, '0.9': 9, '1.0': 10}
    #         settings["adjust_section_idx"] = section_map.get(section_str, 2)
    #         settings["adjust_row"] = self.specs['row'].get()
    #         settings["adjust_parameter"] = self.specs['parameter'].get()
            
        
    #     run_main_logic_result = run_main_logic(settings, self)
    #     if run_main_logic_result is not None:
    #         self.stage_data = run_main_logic_result
    #         print("stage_data saved sucessfully")
        
    #     self.save_settings() # Speichert die Einstellungen in der Settings.txt
    
    def _bezier_data_ready(self) -> bool:
        """Return True when at least stage-1 bezier data exists in the JSON."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            store = data.get("Bezier_point_data", {})
            has_new    = "rotor_stage_1" in store and "stator_stage_1" in store
            has_legacy = "rotor" in store and "stator" in store
            return has_new or has_legacy
        except Exception:
            return False  

    def show_plots_section_rotor(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage - 1          # rotor row for this stage
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_star_u, R_theta_s_star_u, color=farben[k], label=label)
                plt.plot(m_star_l, R_theta_s_star_l, color=farben[k])
        plt.xlabel("x [mm]")
        plt.ylabel("Rθ [mm]")
        plt.title("Rotor Geometry – all stages")
        plt.legend()
        plt.axis('equal')
        plt.show()

    def show_plots_section_stator(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage              # stator row for this stage
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_star_u, R_theta_s_star_u, color=farben[k], label=label)
                plt.plot(m_star_l, R_theta_s_star_l, color=farben[k])
        plt.xlabel("x [mm]")
        plt.ylabel("Rθ [mm]")
        plt.title("Stator Geometry – all stages")
        plt.legend()
        plt.axis('equal')
        plt.show()

    # ── angle-distribution plots ──────────────────────────────────────────────────
    def show_plots_angle_rotor(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage - 1
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, _, _, _, _, m_prime, _, _, m_BP, beta_S, beta_BP, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_prime, beta_S, color=farben[k], label=label)
                plt.scatter(m_BP, beta_BP, color=farben[k])
        plt.xlabel("x/s [%]")
        plt.ylabel("Blade angle [°]")
        plt.title("Blade Angle Distribution – Rotor, all stages")
        plt.legend()
        plt.show()

    def show_plots_angle_stator(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, _, _, _, _, m_prime, _, _, m_BP, beta_S, beta_BP, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_prime, beta_S, color=farben[k], label=label)
                plt.scatter(m_BP, beta_BP, color=farben[k])
        plt.xlabel("x/s [%]")
        plt.ylabel("Blade angle [°]")
        plt.title("Blade Angle Distribution – Stator, all stages")
        plt.legend()
        plt.show()

    # ── thickness-distribution plots ──────────────────────────────────────────────
    def show_plots_thickness_rotor(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage - 1
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, _, _, _, _, m_prime, _, _, m_BP, _, _, d_l, d_l_BP, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_prime, d_l, color=farben[k], label=label)
                plt.scatter(m_BP, d_l_BP, color=farben[k])
        plt.xlabel("x/s [%]")
        plt.ylabel("Thickness d [mm]")
        plt.title("Thickness Distribution – Rotor, all stages")
        plt.legend()
        plt.show()

    def show_plots_thickness_stator(self):
        if not self._bezier_data_ready():
            messagebox.showwarning("Missing data",
                "No Bezier profile data found.\n"
                "Please click 'Create Default Profile(s)' first.")
            return
        farben = ["pink", "blue", "green", "red", "black"]
        for stage in range(1, self.stages_to_calc + 1):
            row = 2 * stage
            for k, h_val in enumerate([0.0, 0.2, 0.5, 0.8, 1.0]):
                _, _, _, _, _, _, _, m_prime, _, _, m_BP, _, _, d_l, d_l_BP, *_ = \
                    calculation_of_section(h_val, row)
                label = f"Stage {stage} – {int(h_val*100)}%" if k == 2 else None
                plt.plot(m_prime, d_l, color=farben[k], label=label)
                plt.scatter(m_BP, d_l_BP, color=farben[k])
        plt.xlabel("x/s [%]")
        plt.ylabel("Thickness d [mm]")
        plt.title("Thickness Distribution – Stator, all stages")
        plt.legend()
        plt.show()        
    '''    
    def show_plots_section_rotor(self):
        NROW = 1
        
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
        
        if not os.path.exists("bezier_control_points_R.txt") or not os.path.exists("bezier_control_points_S.txt"):
            print("Bezier control point files are missing. Please load or create them first.")
            return

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
            plt.title("Rotor Geometry")
        
        plt.xlabel("x [mm]")
        plt.ylabel("R\u03b8 [mm]") 
            
        plt.show()
    

        
    def show_plots_section_stator(self):
        NROW = 2   
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
            
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
            plt.legend()
            plt.title("Stator Geometry")
            
        plt.xlabel("x [mm]")
        plt.ylabel("R\u03b8 [mm]") 
            
        plt.show()

    def show_plots_angle_rotor(self):
        NROW = 1
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
        
        if not os.path.exists("bezier_control_points_R.txt") or not os.path.exists("bezier_control_points_S.txt"):
            print("Bezier control point files are missing. Please load or create them first.")
            return

        row = 1
        for k in range(len(h)):
            h = [0.0 , 0.2, 0.5, 0.8, 1.0]
            farben = ["pink", "blue", "green", "red", "black"]
            i = h[k]
            chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
            plt.plot(m_prime, beta_S, label = f"{h[k]*100}%", color = farben[k])
            plt.scatter(m_BP, beta_BP, color = farben[k])
            plt.legend()
            plt.title("Blade Angle Distribution Rotor")
            
        plt.xlabel('x/s [%]')
        plt.ylabel("blade angle [°]")           
        plt.show() 
    
    def show_plots_angle_stator(self):
        NROW = 2
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
        
        if not os.path.exists("bezier_control_points_R.txt") or not os.path.exists("bezier_control_points_S.txt"):
            print("Bezier control point files are missing. Please load or create them first.")
            return

        length = []
        row = 2
        for k in range(len(h)):
            h = [0.0 , 0.2, 0.5, 0.8, 1.0]
            farben = ["pink", "blue", "green", "red", "black"]
            i = h[k]
            chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
            plt.plot(m_prime, beta_S, label = f"{h[k]*100}%", color = farben[k])
            plt.scatter(m_BP, beta_BP, color = farben[k])
            plt.legend()
            plt.title("Blade Angle Distribution Stator")
            
        plt.xlabel('x/s [%]')
        plt.ylabel("blade angle [°]")           
        plt.show()

    def show_plots_thickness_rotor(self):
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
        
        if not os.path.exists("bezier_control_points_R.txt") or not os.path.exists("bezier_control_points_S.txt"):
            print("Bezier control point files are missing. Please load or create them first.")
            return

        row = 1
        for k in range(len(h)):
            h = [0.0 , 0.2, 0.5, 0.8, 1.0]
            farben = ["pink", "blue", "green", "red", "black"]
            i = h[k]
            chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
            plt.plot(m_prime, d_l, label = f"{h[k]*100}%", color = farben[k])
            plt.scatter(m_BP, d_l_BP, color = farben[k])
            plt.legend()
            plt.title("Thickness Distribution Rotor")
        
        plt.xlabel('x/s [%]')
        plt.ylabel("thickness d [mm]")           
        plt.show() 
    
    def show_plots_thickness_stator(self):
        h = [0.0 , 0.2, 0.5, 0.8, 1.0]
        if not os.path.exists("bezier_control_points_R.txt") or not os.path.exists("bezier_control_points_S.txt"):
            print("Bezier control point files are missing. Please load or create them first.")
            return
        
        NROW = 2 
        length = []
        row = 2
        for k in range(len(h)):
            h = [0.0 , 0.2, 0.5, 0.8, 1.0]
            farben = ["pink", "blue", "green", "red", "black"]
            i = h[k]
            chord, m_star, R_theta_s_star, m_star_u, R_theta_s_star_u, m_star_l, R_theta_s_star_l, m_prime, m_prime_u, m_prime_l, m_BP, beta_S, beta_BP, d_l, d_l_BP, R_theta_s_prime, R_theta_s_prime_u, R_theta_s_prime_l, Rtet_prime_cntr, R_theta_s_prime_2, R_theta_s_prime_2_l, R_theta_s_prime_2_u, R_theta_s_star_2, R_theta_s_star_l_2, R_theta_s_star_u_2 = calculation_of_section(i, row)
            plt.plot(m_prime, d_l, label = f"{h[k]*100}%", color = farben[k])
            plt.scatter(m_BP, d_l_BP, color = farben[k])
            plt.legend()
            plt.title("Thickness Distribution Stator")

        plt.xlabel('x/s [%]')
        plt.ylabel("thickness d [mm]")           
        plt.show()
    '''
    # endregion
    
    def grid_definition_tab(self, parent_frame):


        '''
        # --- Main Grid Settings  ---
        '''    
        
        
        grid_data = { # Lade die Standartwerte
            'nrow': tk.IntVar(value=2),
            'im_selection' : tk.StringVar(value=37),   # Default value for IM
            'km_selection' : tk.StringVar(value=37),   # Default value for KM
            'ref_chord_length': tk.DoubleVar(value=134.4),  # Default value for reference chord length
            'JM_grid_density': tk.IntVar(value=200),  # Default value for reference grid points
            'tip_clearance_rotor': tk.DoubleVar(value=1.3),  # Standardwert von 1.3mm
            'inlet_percentage': tk.DoubleVar(value=0.2),  # Standardwert von 20%
            'outlet_percentage': tk.DoubleVar(value=0.15),  # Standardwert von 15%
            'output_folder': tk.StringVar(value='Run_Multall'),  # Default value for output
            'show_plot': tk.BooleanVar(value=False),  # Default value for showing the plot
            'Q3D_mode': tk.BooleanVar(value=False),  # Default value for Q3D mode
            'ref_chord_length_mode': tk.BooleanVar(value=False),  # Default value for reference chord length mode
            'SA_mode': tk.BooleanVar(value=False)  # Default value for SA turbulence model
        }
        
        km_options = ["5", "21", "25", "29", "33", "37", "41", "45", "49", "53", "57", "61", "65", "69", "73", "77", "81", "89"]
        im_options = ["5", "13", "21", "29", "37", "45", "53", "71", "79", "86", "94"]
        jm_options = [str(i) for i in range(8, 800, 8)]
        
        ui_config = [
            {
                "key": "ref_chord_length",
                "label": "Reference Chord Length [mm]:",
                "type": "entry",
                "help": "Reference value for the chord length...",
                "state_key": "ref_chord_length_mode" 
            },
            {
                "key": "km_selection",
                "label": "Grid Dimension (KM):",
                "type": "combobox",
                "values": km_options,
                "help": "Points of Grid in Radial Direction..."
            },
            {
                "key": "im_selection",
                "label": "Grid Dimension (IM):",
                "type": "combobox",
                "values": im_options,
                "help": "Points of Grid in Circumferential Direction..."
            },
            {
                "key": "JM_grid_density",
                "label": "Fineness (Reference Points):",
                "type": "combobox",
                "values": jm_options,
                "help": "Points of Grid in Axial Direction..."
            },
            {
                "key": "inlet_percentage",
                "label": "Inlet Points (% of JM):",
                "type": "entry",
                "help": "Percentage of points at the inlet..."
            },
            {
                "key": "outlet_percentage",
                "label": "Outlet Points (% of JM):",
                "type": "entry",
                "help": "Percentage of points at the outlet..."
            },
            {
                "key": "tip_clearance_rotor",
                "label": "Tip clearance (mm):",
                "type": "entry",
                "help": "Distance between blade tip and shroud..."
            }
        ]   
           
        main_frame = ttk.Frame(parent_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        nrow_frame = ttk.LabelFrame(main_frame, text="Blade Rows")
        nrow_frame.pack(fill='x', padx=5, pady=5, anchor='n')
        
        inner_nrow_frame = ttk.Frame(nrow_frame)
        inner_nrow_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(inner_nrow_frame, text="Number of Blade Rows:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.nrow_combo = ttk.Combobox(inner_nrow_frame, values=["Complete Stage (Rotor & Stator)", "Rotor Only"], state="readonly")
        self.nrow_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # CHANGE: question mark label to the right of combobox, same pattern as bleed air tooltips
        nrow_q_label = ttk.Label(inner_nrow_frame, text="?", cursor="question_arrow")
        nrow_q_label.grid(row=0, column=2, padx=2, pady=5, sticky='w')
        Tooltip(nrow_q_label, "Multi-stage analysis requires both Rotor and Stator components for continuity.")

        loaded_nrow = self.prepop_grid_data.get('nrow')

        # CHANGE: lock combobox if stages_to_calc > 1
        if self.stages_to_calc > 1:
            self.nrow_combo.set("Complete Stage (Rotor & Stator)")
            self.nrow_combo.config(state="disabled")
        else:
            if loaded_nrow == 1:
                self.nrow_combo.set("Rotor Only")
            else:
                self.nrow_combo.set("Complete Stage (Rotor & Stator)")
        
        '''
        ttk.Label(inner_nrow_frame, text="Number of Blade Rows:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.nrow_combo = ttk.Combobox(inner_nrow_frame, values=["Complete Stage (Rotor & Stator)", "Rotor Only"], state="readonly")
        
        loaded_nrow = self.prepop_grid_data.get('nrow')
        
        # locking the combobox to select if only the rotor were to be calculated if sages to calc is larger than one
        if self.stages_to_calc != 1:
            # Force "Complete Stage" regardless of loaded data if stages > 1
            self.nrow_combo.set("Complete Stage (Rotor & Stator)")
            self.nrow_combo.config(state="disabled") # Lock the box
            
            # Add a small Tooltip to explain why it is locked
            row_label = inner_nrow_frame.winfo_children()[-2] # Accessing the Label
            Tooltip(row_label, "Multi-stage analysis requires both Rotor and Stator components for continuity.")
        else:
            # Normal behavior for single stage: use the loaded value
            if loaded_nrow == 1:
                self.nrow_combo.set("Rotor Only")
            else:
                self.nrow_combo.set("Complete Stage (Rotor & Stator)")
        
        if loaded_nrow == 1:
            self.nrow_combo.set("Rotor Only")
        else:
            self.nrow_combo.set("Complete Stage (Rotor & Stator)")
        '''
        self.nrow_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(inner_nrow_frame, text= "Levels for Output:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.levels_entry = ttk.Entry(inner_nrow_frame)
        
        loaded_levels = self.prepop_metadata.get('levels', [0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.0])
        levels_str = ", ".join(map(str, loaded_levels))
        self.levels_entry.insert(0, levels_str)
        
        self.levels_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(inner_nrow_frame, text="Output:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.output_entry = ttk.Entry(inner_nrow_frame)

        loaded_output = self.prepop_metadata.get('output_folder', '')
        self.output_entry.insert(0, loaded_output)
        
        self.output_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        def browse_grid_output():
            from tkinter import filedialog
            path = filedialog.askdirectory(title="Select Output Folder")
            if path:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, path)
        
        ttk.Button(inner_nrow_frame, text="Browse", command=browse_grid_output).grid(row=2, column=2, padx=5, pady=5)
        inner_nrow_frame.grid_columnconfigure(1, weight=1)  
        
        self.settings_frame = ttk.LabelFrame(main_frame, text="Grid Configuration")
        self.settings_frame.pack(side="top" ,fill="x", anchor="n", pady=5)
        
        self.turbulence_model_frame = ttk.LabelFrame(main_frame, text="Turbulence Model")
        self.turbulence_model_frame.pack(side="top", fill="x", pady=5)
        
        self.widgets = {}
        
        def toggle_ref_chord():
            entry_widget = self.widgets['ref_chord_length']
            
            is_acativated = grid_data['ref_chord_length_mode'].get()
            
            if is_acativated:
                # when activated:
                entry_widget.configure(state="normal")
            else:
                # when deactivated:
                entry_widget.configure(state="disabled")
                
                grid_data['ref_chord_length'].set(134.4)  
        
        # --- Helper Funktion for Q3D Logic ---
        def toggle_Q3D():
            KM_combobox = self.widgets['km_selection']
            if grid_data['Q3D_mode'].get():
                grid_data['km_selection'].set(2) 
                KM_combobox.config(state=tk.DISABLED) 
            else:
                KM_combobox.config(state=tk.NORMAL) 
                grid_data['km_selection'].set(37)  
                
        def toggle_SA():
            if grid_data['SA_mode'].get():
                SA_mode = True #  SA Turbulence Model
                SA_model = 1
            else:
                SA_mode = False #  Standart Turbulence Model
                SA_model =0
            
            debug_log.debug(f"SA_model: {SA_model}", context="grid_tab")
            
        def save_and_initialize_grid():

            debug_log.debug("Saving Parameter...", context="grid_tab")
            grid_data_save = {}
            
            for key, tk_variable in grid_data.items():
                grid_data_save[key] = tk_variable.get()
                
            nrow_choice = self.nrow_combo.get()
            grid_data_save['nrow'] = 1 if nrow_choice == "Rotor Only" else 2
                
            try:
                all_json_data = {}
                
                try:
                    with open(json_path, 'r') as file:
                        all_json_data = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
                
                all_json_data['Grid_data'] = grid_data_save 
                
                levels_input = self.levels_entry.get()
                levels_list = [float(x.strip()) for x in levels_input.split(',')]
                output_value = self.output_entry.get()
                
                if 'Metadata' not in all_json_data:
                    all_json_data['Metadata'] = {}
                    
                all_json_data['Metadata']['levels'] = levels_list
                all_json_data['Metadata']['output_folder'] = output_value
                
                with open(json_path, 'w') as file:
                    json.dump(all_json_data, file, indent=4)
                    
                status_msg = "Parameters saved successfully to JSON."
                print(status_msg)
                debug_log.debug(status_msg, context="grid_tab")

                self.prepop_grid_data = grid_data_save
                
                if not hasattr(self, 'prepop_metadata'):
                    self.prepop_metadata = {}
                self.prepop_metadata['levels'] = levels_list
                self.prepop_metadata['output_folder'] = output_value
                
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Eingabefehler", "Bitte überprüfe die Eingabe bei 'Levels'. Die Zahlen müssen mit Komma getrennt sein (z.B. 0.0, 0.5, 1.0).")
            except Exception as e:
                err_msg = f"An error occurred while saving: {e}"
                print(err_msg)
                debug_log.debug(err_msg, context="grid_tab")
        
        def generate_grid():
            
            debug_log.debug("Saving Grid...", context="grid_tab")
            save_and_initialize_grid()
            # current_grid_settings = {}
            # for key, widget in self.widgets.items():
            #     current_grid_settings[key] = widget.get() 

            # try:
            #     gd = self.prepop_grid_data
            #     nrow_wert         = int(gd.get('nrow', 2))
            #     KM_grid_density   = int(gd.get('km_selection', 37))
            #     IM_grid_density   = int(gd.get('im_selection', 37))
            #     JM_grid_density   = int(gd.get('JM_grid_density', 200))
            #     inlet_percentage  = float(gd.get('inlet_percentage', 0.2))
            #     outlet_percentage = float(gd.get('outlet_percentage', 0.15))
            #     ref_chord_length  = float(gd.get('ref_chord_length', 134.4))
            #     tip_clearance_mm  = float(gd.get('tip_clearance_rotor', 1.3))
            #     Q3D_value         = bool(gd.get('Q3D_mode', False))
            #     do_plot           = bool(gd.get('show_plot', False))
            #     output_path       = gd.get('output_folder', '.')
                
            #     if not hasattr(self, 'meanline_results') or not self.meanline_results:
            #         messagebox.showerror("Error", "No Meanline-Data found. Please calculate '1D-Settings' first!")
            #         return
                
            #     if hasattr(self, 'prepop_metadata') and 'levels' in self.prepop_metadata:
            #         stage_levels = self.prepop_metadata['levels']
            #     else:
            #         # Fallback, in case Metadata is empty
            #         stage_levels = [0.0, 0.05, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 0.95, 1.0]

            #     if Q3D_value:
            #         KM_grid_density = 2

            #     D_S1 = self.meanline_results['D_S1']
            #     D_H1 = self.meanline_results['D_H1']
            #     total_height = (D_S1[0] - D_H1[0]) / 2.0 
            #     tip_clearance_multall = tip_clearance_mm / (total_height * 1000)

            #     print("Starting Grid calculations...")
                
            #     grid_data_list, grid_data_list_plot, JM_dynamic, JM = VG.generate_and_plot_grid(
            #         nrow_wert, IM_grid_density, KM_grid_density,
            #         0.5, JM_grid_density,
            #         inlet_percentage, outlet_percentage,
            #         ref_chord_length, stage_levels,
            #         self.meanline_results 
            #     )

            #     if do_plot:
            #         VG.plot_all(grid_data_list_plot, JM_dynamic)

            #     if Q3D_value:
            #         output_name = f"multall_grid_Q3D_IM_{IM_grid_density}_JM_{JM_dynamic}_rows_{nrow_wert}.dat"
            #     else:
            #         output_name = f"multall_grid_IM_{IM_grid_density}_KM_{KM_grid_density}_JM_{JM_dynamic}_rows_{nrow_wert}.dat"

            #     full_output_path = os.path.join(output_path, output_name)
            #     enable_bleed_air = self.meanline_results.get('enable_bleed_air', False)

            #     VG.write_head_file(KM_grid_density, IM_grid_density, full_output_path,
            #                        0, nrow_wert, len(stage_levels), Q3D_value, enable_bleed_air, 
            #                        self.meanline_results)
                
            #     for data in grid_data_list:
            #         self.JTE = data['JTE']
            #         VG.multall_grid_data_head_row(
            #             full_output_path, len(data['x_new']), data['row_num'],
            #             data['JLE'], data['JM'], data['JTE'],
            #             KM_grid_density, tip_clearance_multall, stage_levels,
            #             self.meanline_results
            #         )
            #         VG.write_coordinates(
            #             data['x_new'], data['Rtheta_new'], data['d_new'], data['R_new'],
            #             full_output_path, data['row_num'], 0, len(data['x_new']), data['JM']
            #         )

            #     VG.write_end_file(nrow_wert, full_output_path, 0, KM_grid_density, stage_levels, self.meanline_results)

            #     messagebox.showinfo("Erfolg", f"Gitter generiert:\n{full_output_path}")

            # except Exception as e:
            #     print(e)
            #     messagebox.showerror("Fehler", f"Fehler: {e}")
            '''
            # ============================================================
            # TODO (other branch): The following was an alternative simpler
            # approach from branch b7c0ba - please review and decide if
            # VG.process_grid_data(json_path) should replace the above.
            # ============================================================
              There was a merge conflict. Top not commented out version is 
              the more completed one
              Review lower commented out section to see if this is the correct
              merged version
            # ============================================================
            '''
            debug_log.debug("Grid is saved.", context="grid_tab")
            debug_log.open_file(os.path.join(os.path.dirname(__file__), "..", "Docs", "Output", "debug.txt"))
            # Why is this called twice for the same button?
            try:
                run_main_logic({'main_choice': 'default'}, self, json_path)
            except Exception as e:
                import traceback
                err_msg = "\n--- Error Loading the 1-D Data ---"
                print(err_msg)
                debug_log.debug(err_msg, context="grid_tab")
                traceback.print_exc()
                messagebox.showerror("Error", "Please calculate and save the Meanline data first!")
                return
            
            debug_log.debug("Generating Grid...", context="grid_tab")
            VG.process_grid_data(json_path, self)
            status_msg = "Grid is generated."
            print(status_msg)
            debug_log.debug(status_msg, context="grid_tab")
            
        
        '''
        GUI Logic
        '''
        
        for row_index, config in enumerate(ui_config):
            
            ttk.Label(self.settings_frame, text=config["label"]).grid(row=row_index, column=0, sticky="w", pady=5)
            
            current_var = grid_data[config["key"]]
            widget = None
            
            if config["type"] == "entry":
                widget = ttk.Entry(self.settings_frame, textvariable=current_var, width=10)
            elif config["type"] == "combobox":
                widget = ttk.Combobox(self.settings_frame, textvariable=current_var, values=config["values"], state="readonly", width=8)   

            if widget:
                widget.grid(row=row_index, column=1, sticky="w", pady=5, padx=5)
                self.widgets[config["key"]] = widget
                
            help_label = ttk.Label(self.settings_frame, text="?", cursor="question_arrow")
            help_label.grid(row=row_index, column=2, padx=(5, 0))
            Tooltip(help_label, config["help"])
        
            if config["key"] == "ref_chord_length":
                ttk.Checkbutton(
                    self.settings_frame, 
                    text="Change reference Chord length", 
                    variable=grid_data['ref_chord_length_mode'], 
                    command=toggle_ref_chord
                ).grid(row=row_index, column=3, padx=10) 
                
        last_row = len(ui_config)
        ttk.Checkbutton(
            self.settings_frame,
            text="Activate Q3D Mode (Sets KM to 2)",
            variable=grid_data['Q3D_mode'],
            command=toggle_Q3D
        ).grid(row=last_row, column=0, columnspan=2, sticky="w", pady=10)

        # SA Model Checkbutton
        ttk.Checkbutton(
            self.turbulence_model_frame,
            text="Use Spalart-Allmaras Turbulence Model",
            variable=grid_data['SA_mode'],
            command=toggle_SA
        ).grid(row=0, column=0, sticky="w")

        # Save Button
        #save_button = ttk.Button(main_frame, text="Save and Initialize Parameters", command=save_and_initialize_grid)
        #save_button.pack(pady=20)
        
        ttk.Button(main_frame, text="Generate Grid", command=generate_grid).pack(pady=5)   
        #save_button.pack(pady=20)   
            
             
    
        toggle_ref_chord()
        toggle_Q3D()
    
    
   
        
    def start_Multall(self):
        popup_multall = tk.Toplevel()
        popup_multall.title("Do you want to start Multall?")
        popup_multall.geometry("300x150")
        tk.Label(popup_multall, text="Do you want to start Multall with the current settings?", wraplength=280).pack(pady=20)
        
        def start_multall_and_exit():
            status_msg = "Starting Multall..."
            print(status_msg)
            debug_log.debug(status_msg, context="multall")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "run_multall.py")
            
            subprocess.Popen([sys.executable, script_path])
            
            popup_multall.destroy()
            self.root.destroy()
            sys.exit()
        
        def cancel_and_exit():
            status_msg = "Multall start cancelled."
            print(status_msg)
            debug_log.debug(status_msg, context="multall")
            popup_multall.destroy()
            self.root.destroy()
            sys.exit()
        
        ttk.Button(popup_multall, text="No", command=cancel_and_exit, style="danger.TButton", width=10).pack(side="left", padx=20, pady=10)
        ttk.Button(popup_multall, text="Yes", command=start_multall_and_exit, style="success.TButton", width= 10).pack(side="right", padx=20, pady=10)
    
    def show_startup_dialog(self):
        dialog = tk.Tk()
        dialog.title("Startup")
        dialog.resizable(True, True)
        
        # Configure grid weights so content stays centered/fills space 
        dialog.columnconfigure(0, weight=1)
        dialog.columnconfigure(1, weight=1)
        for i in range(4): dialog.rowconfigure(i, weight=1)

        # Asks for the amount of stages
        ttk.Label(dialog, text="Number of Stages:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        stage_var = tk.IntVar(value=3)
        stage_entry = ttk.Entry(dialog, textvariable=stage_var, width=5)
        stage_entry.grid(row=0, column=1, padx=10, pady=10)
        # Changing amount of stages cant be done at this very moment. Box entry cant be modified
        stage_entry.config(state='readonly')

        # Asks for the amount of stages to be calculated
        ttk.Label(dialog, text="Stages to Calculate:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        
        stages_to_calc_var = tk.IntVar(value=3)
        stages_to_calc_entry = ttk.Entry(dialog, textvariable=stages_to_calc_var, width=5)
        stages_to_calc_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # error label incase of stages_to_calc_entry > stage_entry
        error_label = ttk.Label(dialog, text="", foreground="red")
        error_label.grid(row=2, columnspan=2)
        
        def save_and_start():
            try:
                num_stages = int(stage_entry.get())
                num_to_calc = int(stages_to_calc_entry.get())
                
                if num_to_calc > num_stages:
                    error_label.config(text=f"Stages to calculate ({num_to_calc}) cannot exceed total stages ({num_stages})!")
                    return
                
                if num_to_calc < 1:
                    error_label.config(text="Stages to calculate must be at least 1!")
                    return
                
                self.stage = num_stages
                self.stages_to_calc = num_to_calc
                dialog.destroy()
                self.render_gui()
            except ValueError:
                error_label.config(text="Please enter a valid integer!")

        ttk.Button(dialog, text="Save and Start GUI", command=save_and_start).grid(row=3, columnspan=2, pady=10)

        dialog.mainloop() 
    
    
    def render_gui(self):
                
        self.root = tk.Tk()
        self.root.title("GUI Example")
                
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.start_Multall)
                    
        # Insert tab list
        notebook = ttk.Notebook(main_frame)  
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
                    
        zeroD = ttk.Frame(notebook, padding=10)
        oneD = ttk.Frame(notebook, padding=10)
        threeD = ttk.Frame(notebook, padding=10)
        grid = ttk.Frame(notebook, padding=10)
        multall_data = ttk.Frame(notebook, padding=10)
        other = ttk.Frame(notebook, padding=10)
                    
        notebook.add(zeroD, text="0D-Settings")
        notebook.add(oneD, text="1D-Settings")
        notebook.add(threeD, text="3D-Settings")
        notebook.add(grid, text="Grid-Settings")
        notebook.add(other, text="Other-Settings")
                
        self.zeroD_tab(zeroD)
        self.oneD_tab(oneD, self.stage)
        self.threeD_tab(threeD)
        self.grid_definition_tab(grid)
        #self.write_multall_data_tab(multall_data)
        #self.other_settings_tab(other)
                
                
                

        main_frame.mainloop()




'''
Class to help render Tooltips for the Gui 

logic as follow:
        name_help = ttk.Label(where_questionmark_will_be_in_renderd_frame, text= "?", cursor="question_arrow")
        name_help.pack(side='left', padx=(5, 0))
        name_help_text = "Text to appear when hovering over tooltip"
        Tooltip(name_help, name_help_text)
'''
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
    
if __name__ == "__main__":
    my_gui = CompressorGui()
    my_gui.loading_prepopulated_data()
    my_gui.show_startup_dialog()
    
    
    
    
    
    
    '''
    1. Press Generating Gird
     --> give all data such as meanline thermo and all json data to the outputgenerating file
     --> Stage_starte_gui(self, self.meanline, self.thermo)
     
    2. In Generating Grid (var_grid.py)
        def Stage_starte_gui(mygui:json_data, meanline_data, thermo_data)
            all data is here to find
    
    '''