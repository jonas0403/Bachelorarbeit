# Author: Jonas Scholz (modified by Luca De Francesco)
# Based on Code by Marco Wiens
# Version: 17.07.2025
# Meanline calculation 1-Dimensional
# Program for meanline calculation and iterating the geometry and contour of the channel 


import math
import tkinter as tk
import numpy as np
import matplotlib as plt
import matplotlib.pyplot as plt
import os 
import sys
import atexit
import debug_log
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Slider

wdpath = os.getcwd()
scriptpath = os.path.dirname(sys.argv[0])
os.chdir(scriptpath)

#from thermodynamic_calculation import Thermo
from plot_channel import plot_channel
from loss_models import xi_ac_pro, xi_ac_te, xi_a_cl, xi_ac_inc, xi_a_sec, xi_ac_ma, diffusion, angle_blade_in, angle_blade_out, Re 
from cubic_spline import cubspline

Pi = math.pi

# from OD-Thermo: 
# GUI 
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

# Create reverse mapping
gui_to_var_map = {v: k for k, v in var_name_to_gui_map.items()}


#LOCK_FILE = 'settings.lock'
#SETTINGS_FILE = 'Diameter_Values.txt'


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
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
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
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            
            
    def update_default_diameters(*args):
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
        if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
   
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
             justify="center").pack()
    
    
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

    # Delete LOCK-File on closing of the window
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Save Button
    save_button = tk.Button(root, text="Save and Continue", command=on_save)
    save_button.grid(row=current_row+5, column=0, columnspan=1+i_st_val, pady=10)

    # Make the window modal (optional, but good practice for input dialogs)
    root.grab_set()
    
    toggle_diameter_entries()
    
    root.wait_window()
    
    write_diameters(SETTINGS_FILE,fixed_radius_type, D_f1_result, D_f2_result, D_f3_result, plot_channel_contour)
    return fixed_radius_type, D_f1_result, D_f2_result, D_f3_result, plot_channel_contour

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
    def __init__(self, root, i_st_val, on_close_callback, initial_data):
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
        self.initial_type, self.initial_D_f1, self.initial_D_f2, self.initial_D_f3, self.initial_plot_contour = initial_data
        
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
        debug_log.debug(f"self.cubspline_points={self.cubspline_points}", context="DiameterGUI")
        
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
        #write_diameters(SETTINGS_FILE, fixed_radius_type, D_f1, D_f2, D_f3, plot_channel_contour)    
        
        self.on_close_callback(D_f1, D_f2, D_f3, fixed_radius_type, plot_channel_contour)
        self.root.destroy()
        plt.close(self.fig)
        
def run_diameter_gui(i_st):
    root = tk.Tk()
    D_f1, D_f2, D_f3 = [],  [],  []
    fixed_radius_type = ""
    plot_channel_contour = False
    
    def on_close(d1, d2, d3, type_var, plot_var):
        nonlocal D_f1, D_f2, D_f3, fixed_radius_type, plot_channel_contour
        D_f1 = d1
        D_f2 = d2
        D_f3 = d3
        fixed_radius_type = type_var
        plot_channel_contour = plot_var
        
    # Read Initial Data from File
    initial_data = read_diameter(SETTINGS_FILE)    
    diameter_gui(root, i_st, on_close, initial_data)
    root.mainloop()
    debug_log.debug(f"D_f1={D_f1}, D_f2={D_f2}, D_f3={D_f3}, fixed_radius_type={fixed_radius_type}, plot_channel_contour={plot_channel_contour}", context="diameter_gui")
    return D_f1, D_f2, D_f3, fixed_radius_type, plot_channel_contour
              
    
def read_diameter(filename):
    
    fixed_radius_typ = None
    D_f1 = None
    D_f2 = None
    D_f3 = None
    plot_channel_contour = None

    with open(filename,'r') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            if line.startswith('Fixed Radius Typ ='):
                fixed_radius_typ = line.split('=')[1].strip(" '[]\n").replace("'","") 
            elif line.startswith('D_f1 ='):
                D_f1 = [float(x) for x in line.split('=')[1].strip('[] ').split(',')]
            elif line.startswith('D_f2 ='):
                D_f2 = [float(x) for x in line.split('=')[1].strip('[] ').split(',')]
            elif line.startswith('D_f3 ='):
                D_f3 = [float(x) for x in line.split('=')[1].strip('[] ').split(',')]
            elif line.startswith('Plot Channel Contour ='):
                plot_channel_contour = line.split('=')[1].strip(" '[]\n").replace("'","") 

    return fixed_radius_typ, D_f1, D_f2, D_f3, plot_channel_contour

def write_diameters(filename,fixed_radius_typ, D_f1, D_f2, D_f3, plot_channel_contour):
    # Check if there is a Lock File. Lock file is created to signal that the GUI and Diameters_values.txt was writen/modified 
    if os.path.exists(LOCK_FILE):
        lock_msg = "Lock File was found. Reading Diameters_Values.txt"
        print(lock_msg)
        debug_log.debug(lock_msg, context="write_diameters")
        return
    # If no Lock File exists create one
    try:
        with open(LOCK_FILE,'w') as f:
            f.write("running")
        # Registers a function to delete the Lock File if Programm is exited normally

        debug_log.debug(f"D_f1={D_f1}, D_f2={D_f2}, D_f3={D_f3}, fixed_radius_type={fixed_radius_typ}, plot_channel_contour={plot_channel_contour}", context="write_diameters")
        with open(filename, 'w') as file:
            file.write(f'Fixed Radius Typ = {fixed_radius_typ}\n')
            file.write(f'D_f1 = {D_f1}\n')
            file.write(f'D_f2 = {D_f2}\n')
            file.write(f'D_f3 = {D_f3}\n')
            file.write(f'Plot Channel Contour = {plot_channel_contour}')
        settings_msg = "Settings were written successfully."
        print(settings_msg)
        debug_log.debug(settings_msg, context="write_diameters")

    except Exception as e:
        write_err = f"Error writing Diameters_Values.txt: {e}"
        print(write_err)
        debug_log.debug(write_err, context="write_diameters")
        # Delete Lock File in case of an error
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

def read_initial_values(filename):
    global n, psi_h, phi_1, phi_2, phi_3
    global z_R, l_R, d_R_l_R, d_Cl_R, d_TE_R, incidence_R
    global z_S, l_S, d_S_l_S, d_TE_S, d_CL_S, incidence_S

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('n = '):
                n = [float(x) for x in line[4:].strip('[]').split(',')]
            elif line.startswith('psi_h = '):
                psi_h = [float(x) for x in line[8:].strip('[]').split(',')]
            elif line.startswith('phi_1 = '):
                phi_1 = [float(x) for x in line[8:].strip('[]').split(',')]
            elif line.startswith('phi_2 = '):
                phi_2 = [float(x) for x in line[8:].strip('[]').split(',')]
            elif line.startswith('phi_3 = '):
                phi_3 = [float(x) for x in line[8:].strip('[]').split(',')]
            elif line.startswith('z_R = '):
                z_R = [int(x) for x in line[6:].strip('[]').split(',')]
            elif line.startswith('l_R = '):
                l_R = [float(x) for x in line[6:].strip('[]').split(',')]
            elif line.startswith('d_R_l_R = '):
                d_R_l_R = [float(x) for x in line[11:].strip('[]').split(',')]
            elif line.startswith('d_Cl_R = '):
                d_Cl_R = [float(x) for x in line[10:].strip('[]').split(',')]
            elif line.startswith('d_TE_R = '):
                d_TE_R = [float(x) for x in line[10:].strip('[]').split(',')]
            elif line.startswith('incidence_R = '):
                incidence_R = [float(x) for x in line[14:].strip('[]').split(',')]
            elif line.startswith('z_S = '):
                z_S = [int(x) for x in line[6:].strip('[]').split(',')]
            elif line.startswith('l_S = '):
                l_S = [float(x) for x in line[6:].strip('[]').split(',')]
            elif line.startswith('d_S_l_S = '):
                d_S_l_S = [float(x) for x in line[11:].strip('[]').split(',')]
            elif line.startswith('d_TE_S = '):
                d_TE_S = [float(x) for x in line[10:].strip('[]').split(',')]
            elif line.startswith('d_CL_S = '):
                d_CL_S = [float(x) for x in line[10:].strip('[]').split(',')]
            elif line.startswith('incidence_S = '):
                incidence_S = [float(x) for x in line[14:].strip('[]').split(',')]

def create_gui():
    global entries
    read_initial_values('Meanline_Initial_Values.txt')

    root = tk.Tk()
    root.title("Meanline Parameters Initialization")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    entries = {}

    for section, params in parameters_sections.items():
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=section)

        for i, param in enumerate(params):
            gui_name = var_name_to_gui_map[param]
            ttk.Label(frame, text=f"{gui_name}:").grid(row=i, column=0, padx=5, pady=5, sticky='w')
            entries[param] = []  # Use param as the key
            for j, value in enumerate(globals()[param]):
                entry = ttk.Entry(frame, width=10)
                entry.insert(0, str(value))
                entry.grid(row=i, column=j+1, padx=5, pady=5)
                entries[param].append(entry)

    def save_and_initialize():
        try:
            for var_name in entries.keys():  # Iterate over the keys in entries
                if var_name in ['z_R', 'z_S']:
                    globals()[var_name] = [int(entry.get()) for entry in entries[var_name]]
                else:
                    globals()[var_name] = [float(entry.get()) for entry in entries[var_name]]

            with open('Meanline_Initial_Values.txt', 'w') as file:
                file.write(f"n = {n}\n")
                file.write(f"psi_h = {psi_h}\n")
                file.write(f"phi_1 = {phi_1}\n")
                file.write(f"phi_2 = {phi_2}\n")
                file.write(f"phi_3 = {phi_3}\n")
                file.write(f"z_R = {z_R}\n")
                file.write(f"l_R = {l_R}\n")
                file.write(f"d_R_l_R = {d_R_l_R}\n")
                file.write(f"d_Cl_R = {d_Cl_R}\n")
                file.write(f"d_TE_R = {d_TE_R}\n")
                file.write(f"incidence_R = {incidence_R}\n")
                file.write(f"z_S = {z_S}\n")
                file.write(f"l_S = {l_S}\n")
                file.write(f"d_S_l_S = {d_S_l_S}\n")
                file.write(f"d_TE_S = {d_TE_S}\n")
                file.write(f"d_CL_S = {d_CL_S}\n")
                file.write(f"incidence_S = {incidence_S}\n")

            params_msg = "Parameters saved and initialized."
            print(params_msg)
            debug_log.debug(params_msg, context="meanline_parameters")
        except ValueError:
            val_err = "Please enter valid numbers for all conditions. z_R and z_S must be integers."
            print(val_err)
            debug_log.debug(val_err, context="meanline_parameters")

    ttk.Button(root, text="Save and Initialize Parameters", command=save_and_initialize).pack(pady=10)

    root.mainloop()

def meanline(thermo_data, meanline_data, diameter_data, plot_channel_contour):
       
    n = meanline_data["n"]
    psi_h = meanline_data["psi_h"]
    phi_1 = meanline_data["phi_1"]
    phi_2 = meanline_data["phi_2"]
    phi_3 = meanline_data['phi_3']
    z_R = meanline_data["z_R"]
    l_R = meanline_data["l_R"]  
    d_R_l_R = meanline_data["d_R_l_R"]
    d_Cl_R = meanline_data["d_Cl_R"]
    d_TE_R = meanline_data["d_TE_R"]
    incidence_R = meanline_data["incidence_R"]
    z_S = meanline_data["z_S"]
    l_S = meanline_data["l_S"]
    d_S_l_S = meanline_data["d_S_l_S"]
    d_TE_S = meanline_data["d_TE_S"]
    d_CL_S = meanline_data["d_CL_S"]
    incidence_S = meanline_data["incidence_S"]
    
    fixed_radius_type = diameter_data["fixed_radius_type"]
    D_f1 = diameter_data["D_f1"]
    D_f2 = diameter_data["D_f2"]
    D_f3 = diameter_data["D_f3"]
    
    '''
    #meter values
    D_f1_meter = diameter_data["D_f1"]
    D_f2_meter = diameter_data["D_f2"]
    D_f3_meter = diameter_data["D_f3"]
    
    D_f1 = D_f1_meter/1000
    D_f2 = D_f2_meter/1000
    D_f3 = D_f3_meter/1000
    ''' 
    
    mflow = thermo_data["mflow"]
    p_t_in = thermo_data["p_t_in"]
    T_t_in = thermo_data["T_t_in"]
    kappa = thermo_data["kappa"]
    R = thermo_data["R"]
    cp = thermo_data["cp"]
    h_R = thermo_data["h_R"]
    h_S = thermo_data["h_S"]
    i_st = thermo_data["i_st"]
    design_TPR = thermo_data["TPR"]

    '''
    #?????????
    if thermo_data is not None:
        print("No thermo_data provided. Please enter the required thermodynamic data.")

        try:
            (mflow, p_t_in, T_t_in, kappa, R, cp, h_R, h_S, i_st, design_TPR) = thermo_data
            
            if kappa is None or kappa == 0: # warum kappa berechnen????
                    kappa = cp / (cp - R)
        except ValueError as e:
            print(f"Error in thermo_data: {e}")
            from thermodynamic_calculation import Thermo
            mflow, p_t_in, T_t_in, kappa, R, cp, h_R, h_S, i_st, design_TPR = Thermo() # warum das zwei mal machen??
    else:
        print("No thermo_data provided. Please enter the required thermodynamic data through the GUI.")
        from thermodynamic_calculation import Thermo
        mflow, p_t_in, T_t_in, kappa, R, cp, h_R, h_S, i_st, design_TPR = Thermo()
    '''
    #read_initial_values("Meanline_Initial_Values.txt")
    
    # Iteration Parameters Outer Iteration loop
    iter_count_TPR = 0
    max_iter_steps_TPR = 50
    conv_limit_TPR = 0.01
    
    # Preallocate TPR-Iteration Variables
    n_history = []
    TPR_history = []   
    n_history.append(n[0])
    
    
    relaxation_factor = 0.5 # Kleinere Werte stabilisieren mehr, aber verlangsamen.
                            # Größere Werte sind schneller, aber ggf. instabiler.
                            
    # Initialize fixed Radius type and Diameter 
    '''
    # should be obsolet with new gui method
    if GUI_On == 1 and not os.path.exists(LOCK_FILE) :

        root = create_gui()
        #root.mainloop()
        D_f1, D_f2, D_f3, fixed_radius_type, plot_channel_contour = run_diameter_gui(i_st)
        #fixed_radius_type, D_f1, D_f2, D_f3, plot_channel_contour = create_input_window(i_st)
        write_diameters(SETTINGS_FILE, fixed_radius_type, D_f1, D_f2, D_f3, plot_channel_contour)


    else:
        print("Lock File was found. Reading Diameters_Values.txt")
        fixed_radius_type, D_f1, D_f2, D_f3, plot_channel_contour = read_diameter(SETTINGS_FILE)
    '''
            
    #region Preallocating Variables
          
    D_S1 = [0.0] * i_st
    D_S2 = [0.0] * i_st
    D_S3 = [0.0] * i_st
    D_M1 = [0.0] * i_st
    D_M2 = [0.0] * i_st
    D_M3 = [0.0] * i_st
    D_H1 = [0.0] * i_st
    D_H2 = [0.0] * i_st
    D_H3 = [0.0] * i_st
    
    D_m_initial_guess = 0.508


    # This will hold the *iterating* mean diameter guess for each 'i'
    next_guess1 = [D_m_initial_guess]*i_st 
    next_guess2 = [D_m_initial_guess]*i_st
    next_guess3 = [D_m_initial_guess]*i_st
    
    q = [0]*i_st
    
    
    
    alpha_1 = [90]*i_st
    alpha_3 = [90]*i_st

    # --- Pre-allocate lists for calculated flow properties ---
    # These will be populated stage by stage in the main loop
    u1, u2, u3, u1_u2, u2_u2= [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    h_R_l_R, t_R, l_R_t_R = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    t_S, l_S_t_S, h_S_l_S = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    c1_u2, cu1_u2, c3_u2, cu2_u2, c2_u2 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    alpha_2, delta_alpha = [0.0]*i_st, [0.0]*i_st
    c1, c2, c3, cu3_u2, wu1_u2, wu2_u2, w1_u2, w1, w2_u2, w2, c_m1, c_m2, c_m3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    cu1, cu2, cu3, cm1, cm2, cm3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    cu1, cu2, cu3, cm1, cm2, cm3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    beta_1, beta_2, delta_beta, a, delta_h_t = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    
    # Inlet total temperature for the first stage
    T_t1 = [0.0] * i_st
    T_t1[0] = T_t_in
    T_t3, T_t2, T_1, T_2, T_3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    
    # Inlet total pressure for the first stage
    p_t1 = [0.0] * i_st
    p_t1[0] = p_t_in
    p_1, p_2, p_3, p_t3, p_t2 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    roh_1, roh_2, roh_3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st

    Re_l_R, Re_l_S = [0.0]*i_st, [0.0]*i_st
    
    beta_blade_1, beta_blade_2, delta_beta_in, delta_beta_out = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    xi_R_pro, xi_R_cl, xi_R_sec, xi_R_inc, xi_R_ma, xi_R_te, xi_R = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    Ma_w1, Ma_w2, Ma_c1, Ma_c2, Ma_c3, Ma_m1, Ma_m2, Ma_m3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    alpha_blade_2, alpha_blade_3, delta_alpha_in, delta_alpha_out = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    w2_w1, B_R, c_L_R, D_R = [0.0]*i_st, [00]*i_st, [0.0]*i_st, [0.0]*i_st
    c3_c2, B_S, c_L_S, D_S_diff = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st # Renamed D_S to D_S_diff to avoid conflict with D_S1, D_S2, D_S3
    T_2is = [0.0]*i_st
    xi_S_pro, xi_S_cl, xi_S_sec, xi_S_inc, xi_S_ma, xi_S_te, xi_S = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    eta_s = [0.0]*i_st
    TPR, roh_h_des = [0.0]*i_st, [0.0]*i_st
    delta_h, delta_h_R, delta_h_S, delta_h_loss, delta_h_loss_R, delta_h_loss_S = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    eta_sC_tt, eta_pC_tt = [0.0]*i_st, [0.0]*i_st
    
    # Stage geometry related lists (some might be filled later)
    # b1, b2, b3 represent span at various stations - if used in formula they also need to be pre-allocated.
    b1, b2, b3 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    nue_in, delta_D_target_12, delta_D_target_23 = [0.0]*i_st, [0.0]*i_st, [0.0]*i_st
    
    #endregion

    # --- MAINLOOP ---
    # Iterating over the stages
    while iter_count_TPR < max_iter_steps_TPR:        
        
        # Calculate all Stages
        for i in range(i_st):
            
                
            current_D_M1_guess=next_guess1[i] 
            current_D_M2_guess=next_guess2[i]
            current_D_M3_guess=next_guess3[i]

            iteration_count=0
            max_iteration_steps=1000
            tolerance=0.0005

            stage_msg = f"\n--- Starting calculation for Stage {i+1}/{i_st} ---"
            print(stage_msg)
            debug_log.debug(stage_msg, context="meanline")

            if fixed_radius_type == "hub":
                D_H1[i]=D_f1[i]
                D_H2[i]=D_f2[i]
                D_H3[i]=D_f3[i]

            elif fixed_radius_type == "shroud":
                D_S1[i]=D_f1[i]
                D_S2[i]=D_f2[i]
                D_S3[i]=D_f3[i]
            elif fixed_radius_type == "mean":
                D_M1[i]=D_f1[i]
                D_M2[i]=D_f2[i]
                D_M3[i]=D_f3[i]
            else:
                raise ValueError("Invalid fixed_radius_type specified.")
            
            
            # --- Inner Iteration Loop: Solves for the Channel Diameters ---
            # Runs until all Diameters are calculated or max Iteration count is reached
            while iteration_count < max_iteration_steps:
                # Saves previous Guesses
                old_D_M1_guess=current_D_M1_guess
                old_D_M2_guess=current_D_M2_guess
                old_D_M3_guess=current_D_M3_guess

                # Calculates the Circumferential Speeds (u)
                u1[i]=(2*Pi*n[i])/60*current_D_M1_guess/2
                u2[i]=(2*Pi*n[i])/60*current_D_M2_guess/2
                
                
                
                if i > 0 :
                    u3[i-1]=u2[i] 
                else:
                    u3[i] = 0
                    
                u1_u2[i]=u1[i]/u2[i]
                u2_u2[i]=u2[i]/u2[i]
                #u3_u2[i]=u3[i]/u2[i] # Stators dont move


                #region Calculates the flow Properties 

                #Rotor
                h_R_l_R[i]=h_R[i]/l_R[i]
                t_R[i]=round(Pi*current_D_M2_guess/z_R[i]*1000,2)
                l_R_t_R[i]=l_R[i]/t_R[i] 

                #Stator
                h_S_l_S[i]=h_S[i]/l_S[i]
                t_S[i]=round(Pi*current_D_M2_guess/z_S[i]*1000,2)
                l_S_t_S[i]=l_S[i]/t_S[i] 

                # Non Dimensinal Velocities
                c1_u2[i]=phi_1[i]/math.sin(math.radians(alpha_1[i])) if math.sin(math.radians(alpha_1[i]))!=0 else float('inf')
                cu1_u2[i]=c1_u2[i]*math.cos(math.radians(alpha_1[i]))
                c3_u2[i]=phi_3[i]/math.sin(math.radians(alpha_3[i])) if math.sin(math.radians(alpha_3[i]))!=0 else float('inf')
                cu2_u2[i]=u1_u2[i]*cu1_u2[i]+psi_h[i]/2-q[i]/u2[i]**2+c3_u2[i]**2/2-c1_u2[i]**2/2
                c2_u2[i]=math.sqrt(phi_2[i]**2+cu2_u2[i]**2)

                alpha_2[i]=math.degrees(math.acos(cu2_u2[i]/c2_u2[i]))
                delta_alpha[i]=alpha_2[i]-alpha_3[i]


                # Absolut and Relative Velocities
                c1[i]=c1_u2[i]*u2[i]
                c2[i]=c2_u2[i]*u2[i]
                c3[i]=c3_u2[i]*u2[i]
                cu3_u2[i]=c3_u2[i]*math.cos(math.radians(alpha_3[i]))
                wu1_u2[i]=cu1_u2[i]-u1_u2[i]
                wu2_u2[i]=cu2_u2[i]-u2_u2[i]
                w1_u2[i]=math.sqrt(phi_1[i]**2+wu1_u2[i]**2)
                w1[i]=w1_u2[i]*u2[i]
                w2_u2[i]=math.sqrt(phi_2[i]**2+wu2_u2[i]**2)
                w2[i]=w2_u2[i]*u2[i]

                # Angles and Enthalpy
                # Überprüfe Argumente für math.acos, um Domain-Fehler zu vermeiden (-1 <= x <= 1)
                
                # potential error source:
                '''
                beta_1_arg=wu1_u2[i]/w1_u2[i] if w1_u2[i]!=0 else 0.0
                beta_1_arg=max(-1.0, min(1.0, beta_1_arg)) # Clamping
                beta_1[i]=math.degrees(math.acos(beta_1_arg))
                beta_2_arg=wu2_u2[i]/w2_u2[i] if w2_u2[i]!=0 else 0.0
                beta_2_arg=max(-1.0, min(1.0, beta_2_arg)) # Clamping
                beta_2[i]=math.degrees(math.acos(beta_2_arg))
                '''
                beta_1[i]=math.degrees(math.acos(wu1_u2[i]/w1_u2[i]))
                beta_2[i]=math.degrees(math.acos(wu2_u2[i]/w2_u2[i]))
                delta_beta[i]=beta_2[i]-beta_1[i]

                a[i]=(cu2_u2[i]-u1_u2[i]*cu1_u2[i])*u2[i]**2 
                delta_h_t[i]=a[i]+q[i]

                # Total and Static Temperatures
                if i>0:
                    T_t1[i]=T_t3[i-1]# Rotor Inlet temperature is equal to stator exit Temperatur
                    p_t1[i]=p_t3[i-1]# Rotor Inlet pressure is equal to stator exit Temperatur

                T_t3[i]=T_t1[i]+delta_h_t[i]/cp
                T_t2[i]=T_t3[i]# For stator inlet

                T_1[i]=T_t1[i]-c1[i]**2/(2*cp)
                
                T_2[i]=T_t2[i]-c2[i]**2/(2*cp)

                T_3[i]=T_t3[i]-c3[i]**2/(2*cp)
        

                # Static and Total pressure and Density
                p_1[i]=p_t1[i]*(T_1[i]/T_t1[i])**(kappa/(kappa-1))
                if i > 0:
                    roh_1[i]=roh_3[i-1]
                else:
                    roh_1[i]=p_1[i]/(R*T_1[i])

                # Blade Angles, Reynoldsnumbers, Machnumbers and Losses

                
                debug_log.debug(f"beta_blade_1[i]={beta_blade_1[i]}=angle_blade_in(...)", context="meanline")

                Re_l_R[i]=Re(roh_1[i],w1[i],l_R[i],T_1[i])
                beta_blade_1[i]=angle_blade_in(beta_1[i], beta_2[i], w1[i], w2[i], T_1[i], T_2[i], l_R_t_R[i], d_R_l_R[i], incidence_R[i], R, kappa)
                beta_blade_2[i]=angle_blade_out(beta_1[i], beta_2[i], w1[i], w2[i], T_1[i], T_2[i], l_R_t_R[i], d_R_l_R[i], incidence_R[i], R, kappa)
                delta_beta_in[i]=beta_blade_1[i]-beta_1[i]
                delta_beta_out[i]=beta_2[i]-beta_blade_2[i]

                # Rotor Losses

                xi_R_pro[i]=xi_ac_pro(beta_1[i],beta_2[i], l_R_t_R[i])
                xi_R_cl[i]=xi_a_cl(beta_1[i], beta_2[i], l_R_t_R[i], d_Cl_R[i], h_R[i])
                xi_R_sec[i]=xi_a_sec(beta_1[i], beta_2[i], l_R_t_R[i], t_R[i], h_R[i])
                xi_R_inc[i]=xi_ac_inc(beta_1[i], beta_2[i],incidence_R[i])
                xi_R_ma[i]=xi_ac_ma(w1[i], T_1[i])
                xi_R_te[i]=xi_ac_te(beta_1[i], beta_2[i], l_R_t_R[i], t_R[i], d_TE_R[i], Re_l_R[i])
                xi_R[i]=xi_R_pro[i] + xi_R_te[i] + xi_R_cl[i] + xi_R_sec[i] + xi_R_inc[i] + xi_R_ma[i]

                # Machnumbers

                Ma_w1[i]=w1[i]/math.sqrt(kappa*R*T_1[i])
                Ma_w2[i]=w2[i]/math.sqrt(kappa*R*T_2[i])
                Ma_c1[i]=c1[i]/math.sqrt(kappa*R*T_1[i])
                Ma_c2[i]=c2[i]/math.sqrt(kappa*R*T_2[i])
                Ma_c3[i]=c3[i]/math.sqrt(kappa*R*T_3[i])
                Ma_m1[i]=phi_1[i]*u2[i]/math.sqrt(kappa*R*T_1[i])
                Ma_m2[i]=phi_2[i]*u2[i]/math.sqrt(kappa*R*T_2[i])
                Ma_m3[i]=phi_3[i]*u2[i]/math.sqrt(kappa*R*T_3[i])


                alpha_blade_2[i]=angle_blade_in(alpha_2[i], alpha_3[i], c2[i], c3[i], T_2[i], T_3[i], l_S_t_S[i], d_S_l_S[i], incidence_S[i], R, kappa)
                alpha_blade_3[i]=angle_blade_out(alpha_2[i], alpha_3[i], c2[i], c3[i], T_2[i], T_3[i], l_S_t_S[i], d_S_l_S[i], incidence_S[i], R, kappa)
                delta_alpha_in[i]=alpha_2[i]-alpha_blade_2[i]
                delta_alpha_out[i]=alpha_blade_3[i]-alpha_3[i]
                

                # Rotor design Parameters

                w2_w1[i]=w2_u2[i]/w1_u2[i]
                B_R[i]=2*abs(wu2_u2[i]-wu1_u2[i])/((w2_u2[i]+w1_u2[i])/2)
                c_L_R[i]=B_R[i]/l_R_t_R[i]
                D_R[i]=diffusion(beta_1[i], beta_2[i], w1[i], w2[i], l_R_t_R[i])


                # Stator deign parameters

                c3_c2[i]=c3_u2[i]/c2_u2[i]
                B_S[i]=2*abs(cu3_u2[i] - cu2_u2[i])/((c3_u2[i] + c2_u2[i])/2)
                c_L_S[i]=B_S[i]/l_S_t_S[i]
                D_S_diff[i]=diffusion(alpha_2[i], alpha_3[i], c2[i], c3[i], l_R_t_R[i]) # ????? diffusion has to be calculated with l_S_t_S
                


                # Pressures, Densities and losses continued

                T_2is[i]=T_2[i]-xi_R[i]*w1[i]**2/(2*cp)
                p_2[i]=p_1[i]*(T_2is[i]/T_1[i])**(kappa/(kappa-1))
                roh_2[i]=p_2[i]/(T_2[i]*R)

                Re_l_S[i]=Re(roh_2[i], c2[i], l_S[i], T_2[i])

                xi_S_pro[i]=xi_ac_pro(alpha_2[i],alpha_3[i], l_S_t_S[i])
                xi_S_cl[i]=xi_a_cl(alpha_2[i], alpha_3[i], l_S_t_S[i], d_CL_S[i], h_S[i])
                xi_S_sec[i]=xi_a_sec(alpha_2[i], alpha_3[i], l_S_t_S[i], t_S[i], h_S[i])
                xi_S_inc[i]=xi_ac_inc(alpha_2[i], alpha_3[i] ,incidence_S[i])
                xi_S_ma[i]=xi_ac_ma(c2[i], T_2[i])
                xi_S_te[i]=xi_ac_te(alpha_2[i], alpha_3[i], l_S_t_S[i], t_S[i], d_TE_S[i], Re_l_S[i])
                xi_S[i]=xi_S_pro[i] + xi_S_te[i] + xi_S_cl[i] + xi_S_sec[i] + xi_S_inc[i] + xi_S_ma[i]

                eta_s[i]=(psi_h[i]-xi_R[i]*w1_u2[i]**2-xi_S[i]*c2_u2[i]**2)/psi_h[i]
                p_t3[i]=p_t1[i]*(eta_s[i]*(T_t3[i]/T_t1[i]-1)+1)**(kappa/(kappa-1))
                p_3[i]=p_t3[i]*(T_3[i]/T_t3[i])**(kappa/(kappa-1))
                roh_3[i]=p_3[i]/(T_3[i]*R)

                TPR[i]=p_t3[i]/p_t1[i]
                p_t2[i]=p_2[i]*(T_t2[i]/T_2[i])**(kappa/(kappa-1))
                roh_h_des[i]=(2*(cu2_u2[i]-u1_u2[i]*cu1_u2[i])-(cu2_u2[i]**2-cu1_u2[i]**2))/(2*(cu2_u2[i]-u1_u2[i]*cu1_u2[i])-(c3_u2[i]**2-c1_u2[i]**2))

                delta_h[i]=psi_h[i]*u2[i]**2/2
                delta_h_R[i]=delta_h[i]*roh_h_des[i]
                delta_h_S[i]=delta_h[i]-delta_h_R[i] 
                delta_h_loss_R[i]=xi_R[i]*w1[i]**2/2
                delta_h_loss_S[i]=xi_S[i]*c2[i]**2/2
                delta_h_loss[i]=delta_h_loss_R[i]+delta_h_loss_S[i]

                eta_sC_tt[i]=eta_s[i]
                eta_pC_tt[i]=R*math.log(TPR[i],math.e)/(cp*math.log(T_t3[i]/T_t1[i],math.e))

                # endregion
                
                # Calculating C_m for the Diameter Calculation to Gurantee Continuity        
                if i > 0:
                    c_m1[i] = c_m3[i-1]
                else:
                    c_m1[i] = phi_1[i]*u2[i]
                    
                c_m2[i] = phi_2[i]*u2[i]
                c_m3[i] = phi_3[i]*u2[i]

                # Calculates the new Diameter based on massflow
                if fixed_radius_type == "hub":
                    # D_H1[i] is fixed
                    under_sqrt1=D_H1[i]**2+(4*mflow)/(Pi*roh_1[i]*c_m1[i])
                    under_sqrt2=D_H2[i]**2+(4*mflow)/(Pi*roh_2[i]*c_m2[i])
                    under_sqrt3=D_H3[i]**2+(4*mflow)/(Pi*roh_3[i]*c_m3[i])
                    
                    # print(f"Stage:{i+1}    under_sqrt1({under_sqrt1})=D_H3[i]({D_H1[i]})**2+(4*mflow({mflow}))/(Pi*roh_3[i]({roh_1[i]})*c_m3[i]({c_m1[i]}))")
                    # print(f"Stage:{i+1}    under_sqrt3({under_sqrt3})=D_H3[i]({D_H3[i]})**2+(4*mflow({mflow}))/(Pi*roh_3[i]({roh_3[i]})*c_m3[i]({c_m3[i]}))")

                    if under_sqrt1 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_S1 at stage {i} is negative. Setting D_S1[i] = D_H1[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_S1[i]=D_H1[i]
                    else:
                        D_S1[i]=math.sqrt(under_sqrt1)
                    new_D_M1_guess=(D_H1[i]+D_S1[i])/2

                    if under_sqrt2 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_S2 at stage {i} is negative. Setting D_S2[i] = D_H2[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_S2[i]=D_H2[i]
                    else:
                        D_S2[i]=math.sqrt(under_sqrt2)
                    new_D_M2_guess=(D_H2[i]+D_S2[i])/2

                    if under_sqrt3 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_S3 at stage {i} is negative. Setting D_S3[i] = D_H3[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_S3[i]=D_H3[i]
                    else:
                        D_S3[i]=math.sqrt(under_sqrt3)
                    new_D_M3_guess=(D_H3[i]+D_S3[i])/2

                    # Update next_guess with the current converged Values
                    D_M1[i]=new_D_M1_guess
                    D_M2[i]=new_D_M2_guess
                    D_M3[i]=new_D_M3_guess

                if fixed_radius_type == "shroud":
                    # D_S1[i] is fixed 
                    
                    #val_to_subtract1 = (4 * mflow) / (Pi * roh_1[i] * phi_1[i] * u1[i])
                    #print(f"DEBUG: Stage {i+1} - D_S1[i]^2: {D_S1[i]**2:.6f}")
                    #print(f"DEBUG: Stage {i+1} - 4*mflow/(Pi*roh_1*phi*u1): {val_to_subtract1:.6f}")
                    #under_sqrt1 = D_S1[i]**2 - val_to_subtract1
                    #print(f"DEBUG: Stage {i+1} - under_sqrt1: {under_sqrt1:.6f}")
                    
                    #print(f"roh={roh_3[i]}")
                    #print(f"phi={phi_3[i]}")
                    #print(f"u2={u2}")
                    #print(f"u={u3}")
                    under_sqrt1=D_S1[i]**2-(4*mflow)/(Pi*roh_1[i]*c_m1[i])
                    under_sqrt2=D_S2[i]**2-(4*mflow)/(Pi*roh_2[i]*c_m2[i])
                    under_sqrt3=D_S3[i]**2-(4*mflow)/(Pi*roh_3[i]*c_m3[i])
                    
                    if under_sqrt1 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_H1 at stage {i} is negative. Setting D_H1[i] = D_S1[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_H1[i]=D_S1[i]
                    else:
                        D_H1[i]=math.sqrt(under_sqrt1)
                    new_D_M1_guess=(D_H1[i]+D_S1[i])/2

                    if under_sqrt2 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_H2 at stage {i} is negative. Setting D_H2[i] = D_S2[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_H2[i]=D_S2[i]
                    else:
                        D_H2[i]=math.sqrt(under_sqrt2)
                    new_D_M2_guess=(D_H2[i]+D_S2[i])/2

                    if under_sqrt3 < 0:
                        warn_msg = f"Warning: Term under sqrt for D_H3 at stage {i} is negative. Setting D_H3[i] = D_S3[i]."
                        print(warn_msg)
                        debug_log.debug(warn_msg, context="meanline")
                        D_H3[i]=D_S3[i]
                    else:
                        D_H3[i]=math.sqrt(under_sqrt3)
                    new_D_M3_guess=(D_H3[i]+D_S3[i])/2
                    
                    # Update next_guess with the current converged Values
                    D_M1[i]=new_D_M1_guess
                    D_M2[i]=new_D_M2_guess
                    D_M3[i]=new_D_M3_guess
                    
                if fixed_radius_type == "mean":
                    # D_M1[i] is fixed
                    # Calculate Channel height
                    b1[i]=mflow/(roh_1[i]*phi_1[i]*u2[i]*Pi*D_M1[i])
                    b2[i]=mflow/(roh_2[i]*phi_2[i]*u2[i]*Pi*D_M2[i])
                    b3[i]=mflow/(roh_3[i]*phi_3[i]*u2[i]*Pi*D_M3[i])
                    
                    # Calculate Shroud Diameter 
                    D_S1[i]=D_M1[i]+b1[i]
                    D_S2[i]=D_M2[i]+b2[i]
                    D_S3[i]=D_M3[i]+b3[i]
                    
                    # Calculate Hub Diameter
                    D_H1[i]=D_M1[i]-b1[i]
                    D_H2[i]=D_M2[i]-b2[i]
                    D_H3[i]=D_M3[i]-b3[i]
                    
                    # Overwrite D_M guesses to check for convergence
                    new_D_M1_guess=D_M1[i]
                    new_D_M2_guess=D_M2[i]
                    new_D_M3_guess=D_M3[i]
                    
                    # Set converged to True because fixed mean line does not need to be iteratated
                    converged = True
                    
                    
                    
                # Appling relaxation factor
                # Used for the stability of an non-linear system
                # Only use when not in meanline fixed design

                if fixed_radius_type != "mean":
                    current_D_M1_guess=old_D_M1_guess*(1-relaxation_factor)+new_D_M1_guess*relaxation_factor
                    current_D_M2_guess=old_D_M2_guess*(1-relaxation_factor)+new_D_M2_guess*relaxation_factor
                    current_D_M3_guess=old_D_M3_guess*(1-relaxation_factor)+new_D_M3_guess*relaxation_factor
                else:
                    # Wenn fixed_radius_type "mean" ist, übernehmen wir die fixierten Werte
                    current_D_M1_guess=D_M1[i]
                    current_D_M2_guess=D_M2[i]
                    current_D_M3_guess=D_M3[i]


                # Update the mealine diameters

                D_M1[i]=current_D_M1_guess
                D_M2[i]=current_D_M2_guess
                D_M3[i]=current_D_M3_guess


                if fixed_radius_type == "hub":
                    # D_H ist fest, D_S muss sich anpassen
                    D_S1[i]=2*D_M1[i]-D_H1[i]
                    D_S2[i]=2*D_M2[i]-D_H2[i]
                    D_S3[i]=2*D_M3[i]-D_H3[i]
                elif fixed_radius_type == "shroud":
                    # D_S ist fest, D_H muss sich anpassen
                    D_H1[i]=2*D_M1[i]-D_S1[i]
                    D_H2[i]=2*D_M2[i]-D_S2[i]
                    D_H3[i]=2*D_M3[i]-D_S3[i]
                    
                    
                # Update the Rotor and Stator Height
                h_S[i]=((D_S2[i]-D_H2[i])+(D_S3[i]-D_H3[i]))/4*1000
                h_R[i]=((D_S1[i]-D_H1[i])+(D_S2[i]-D_H2[i]))/4*1000

                # Check for Convergence
                converged=(abs(new_D_M1_guess-old_D_M1_guess)<tolerance and abs(new_D_M2_guess-old_D_M2_guess)<tolerance and abs(new_D_M3_guess-old_D_M3_guess)<tolerance)
                #print(f"\n in Iteration {iteration_count} the convergend is {new_D_M1_guess} {old_D_M1_guess} ")

                # Debug-Prints useful for debugging
                if iteration_count % 10 == 0 or converged: # Every 10 iterations or at convergence
                    debug_log.debug(f"Stage {i+1}, Iteration {iteration_count+1}: D_M1={current_D_M1_guess:.4f}, D_M2={current_D_M2_guess:.4f}, D_M3={current_D_M3_guess:.4f}", context="meanline")
                    debug_log.debug(f"Changes: dD_M1={abs(current_D_M1_guess - old_D_M1_guess):.6f}, dD_M2={abs(current_D_M2_guess - old_D_M2_guess):.6f}, dD_M3={abs(current_D_M3_guess - old_D_M3_guess):.6f} (Tol: {tolerance})", context="meanline")
                    debug_log.debug(f"Diameters: D_S1={D_S1[i]:.4f} D_M1={D_M1[i]:.4f} D_H1={D_H1[i]:.4f}  D_S2={D_S2[i]:.4f} D_M2={D_M2[i]:.4f} D_H2={D_H2[i]:.4f}  D_S3={D_S3[i]:.4f} D_M3={D_M3[i]:.4f} D_H3={D_H3[i]:.4f}", context="meanline")
                    debug_log.debug(f"T_t1={T_t1[i]:.2f}K p_t1={p_t1[i]:.2f}Pa roh_1={roh_1[i]:.4f}  Ma_w1={Ma_w1[i]:.3f} Ma_c1={Ma_c1[i]:.3f}  eta_s={eta_s[i]:.3f} TPR={TPR[i]:.3f}", context="meanline")


                if converged:
                    conv_msg = f"Stage {i+1}: Converged in {iteration_count+1} iterations."
                    print(conv_msg)
                    debug_log.debug(conv_msg, context="meanline")
                    if fixed_radius_type == "hub" and i < i_st:
                        current_D_M1_guess = current_D_M3_guess
                    elif fixed_radius_type == "shroud" and i < i_st:
                        current_D_M1_guess = current_D_M3_guess
                    #elif fixed_radius_type == "mean" and i < i_st:
                    #    current_D_M1_guess = current_D_M3_guess
                    break # Exit the iteration loop for this stage
            

                # Update Iteration Count
                iteration_count += 1
                #print(f"TPR={TPR}")
                
                

            else: # This 'else' block executes if the while loop completes WITHOUT a 'break'
                nonconv_msg = f"Warning: Diameters for stage {i} did not converge after {max_iteration_steps} iterations."
                print(nonconv_msg)
                debug_log.debug(nonconv_msg, context="meanline")
                # The last calculated values are stored in D_M1[i], D_S1[i] etc.


            # Gurantee the Contunity of the diameters between stages
            
            # if i > 0:
            #     if fixed_radius_type == 'hub':
            #         D_S3[i-1]=D_S1[i]
            #     elif fixed_radius_type == 'shroud':
            #         D_H3[i-1]=D_H1[i] 
                
            
            #  Important: The initial Guess for the next sate (i+1) have to be the converged D_M of the current stage (i)
            
            if i < i_st - 1: # Only do this if it is not the last stage 
                next_guess1[i+1] = D_M1[i] 
                next_guess2[i+1] = D_M2[i]
                next_guess3[i+1] = D_M3[i]

        # Overall Mashine Performance
        TPR_M=p_t3[i_st-1]/p_t1[0]# TPR over all stages
        TPR_history.append(TPR_M)
        debug_log.debug(f"TPR_M={TPR_history}", context="meanline_TPR")
        debug_log.debug(f"iter count = {iter_count_TPR}", context="meanline_TPR")
        debug_log.debug(f"length TPR_history 1 = {len(TPR_history)}", context="meanline_TPR")

        
        # Initialize both secant values
        if len(n_history) == 1: 
            # Adjust RPM to change TPR to match designed TPR
            if TPR_M < design_TPR:
                # reduce RPM
                
                if iter_count_TPR == 0:
                    n_history.append(n_history[0]*1.05)
                
            elif TPR_M > design_TPR:
                # increase RPM
                
                if iter_count_TPR == 0:
                    n_history.append(n_history[0]*0.95)
        
          
        # Secant Method to Calculate the next RPM 
        if len(TPR_history) >= 2:
            # Set current and old TPR Value for the Calculation
            curr_TPR = TPR_history[-1]
            old_TPR = TPR_history[-2]
            
            # Set current and old n Value for the Calculation
            curr_n = n_history[-1]
            old_n = n_history[-2]
            
            # Secante Calculation
            if abs(curr_TPR - old_TPR) > 1e-6: # Prevent Division by Zero
                next_n = curr_n - (curr_TPR - design_TPR) * (curr_n - old_n) / ((curr_TPR-design_TPR) - (old_TPR-design_TPR))
            else:
                # Fallback strategy in case of no or very small TPR changes but not near the Design TPR
                tpr_warn = "Warning: No significant TPR changes. Applying a small linear adjustment."
                print(tpr_warn)
                debug_log.debug(tpr_warn, context="meanline_TPR")
                if curr_TPR < design_TPR:
                    next_n = curr_n * 1.02
                else:
                    next_n = curr_n * 0.98
        
        else:
            # First iteration not enough values to calculate using the secant methode
            # Using second RPM value instead
            next_n = n_history[iter_count_TPR + 1]
        
        # Set the old mean Diameter as the next guess for the inner loop for faster iterations
        # next_guess1 = D_M1
        # next_guess2 = D_M2
        # next_guess3 = D_M3
                    
        # Update the List for the next Iteration
        n_history.append(next_n)
            
        # Set global RPM to current guess
            
        n = [next_n] * i_st
            
        # Increase Iteration Count
        iter_count_TPR +=1
            
            
            
            
            

        if abs(TPR_M - design_TPR) < conv_limit_TPR:
            tpr_done = f"\nTotal Pressure Ratio has converged after {iter_count_TPR} iterations. TPR = {TPR_M:.3f} at RPM = {n[0]:.0f}, massflow = {mflow}"
            print(tpr_done)
            debug_log.debug(tpr_done, context="meanline_TPR")
            n = [curr_n] * i_st
            break
    else: # This 'else' block executes if the while loop completes WITHOUT a 'break'
        tpr_fail = f"Warning: Total Pressure Ratio did not converge after {max_iter_steps_TPR} iterations."
        print(tpr_fail)
        debug_log.debug(tpr_fail, context="meanline_TPR")


    



    # BUGFIX
    # print(f"Stg:{i} D_S3={D_S3[i]} D_M3={D_M3[i]} D_H3={D_H3[i]} ")
    # if i < i_st:
    #     print(f"Stg:{i+1} D_S1={D_S1[i]} D_M1={D_M1[i]} D_H1={D_H1[i]} ")

    # --- Calculation after all Diameters converged ---
    
    
    # Convert all Diameters to mm
    
    D_H1_mm=[val*1000 for val in D_H1]
    D_H2_mm=[val*1000 for val in D_H2]
    D_H3_mm=[val*1000 for val in D_H3]
    D_M1_mm=[val*1000 for val in D_M1]
    D_M2_mm=[val*1000 for val in D_M2]
    D_M3_mm=[val*1000 for val in D_M3]
    D_S1_mm=[val*1000 for val in D_S1]
    D_S2_mm=[val*1000 for val in D_S2]
    D_S3_mm=[val*1000 for val in D_S3]
    

    
   
    # Check for T_t3[i_st-1] - T_t_in > 0 to avoid division by zero
    if (T_t3[i_st-1] - T_t_in) != 0:
        eta_sC_tt_M=(TPR_M**((kappa-1)/kappa)-1)/((T_t3[i_st-1]/T_t_in)-1)
        eta_pC_tt_M=R*math.log(TPR_M, math.e)/(cp*math.log((T_t3[i_st-1]/T_t_in), math.e))
    else:
        eta_sC_tt_M=0.0 # Or handle as an error
        eta_pC_tt_M=0.0 # Or handle as an error


    eta_sC_tt, eta_pC_tt = [], []
    for i in range(i_st):
        eta_sC_tt.append(eta_s[i])
        eta_pC_tt.append(R*math.log(TPR[i], math.e)/(cp*math.log((T_t3[i]/T_t1[i]), math.e)))

    #Stage geometry
    # Calculating Span (b) based on channel geometry

    for i in range(i_st):
        # Only calculate Channel hight if meanline is not fixed because it was calculated earlier
        if fixed_radius_type != "mean":
            # Using the actual D_M values from calculation 
            b1[i]=mflow/(roh_1[i]*phi_1[i]*u2[i]*Pi*D_M1[i])*1000
            b2[i]=mflow/(roh_2[i]*phi_2[i]*u2[i]*Pi*D_M2[i])*1000
            b3[i]=mflow/(roh_3[i]*phi_3[i]*u2[i]*Pi*D_M3[i])*1000
    
    for i in range(i_st):
        nue_in.append(D_H1[i]/D_S1[i])
        delta_D_target_12.append(D_S1[i]-D_S2[i])
        delta_D_target_23.append(D_S2[i]-D_S3[i])
        
        
        # Specific Values for the radial Equlibrium
        cu1[i]=cu1_u2[i]*u2[i]
        cu2[i]=cu2_u2[i]*u2[i]
        cu3[i]=cu3_u2[i]*u2[i]
        cm1[i]=phi_1[i]*u2[i]
        cm2[i]=phi_2[i]*u2[i]
        cm3[i]=phi_3[i]*u2[i]
        
    
    # Add last T_t3 value onto the T_t1 
    T_t1.append(T_t3[i_st-1])
    
    
    
    # Convert Span to mm 
    b1=[val*1000 for val in b1]
    b2=[val*1000 for val in b2]
    b3=[val*1000 for val in b3]
        
        
    if plot_channel_contour == True:
        debug_log.debug("plot incoming", context="meanline")
        plot_channel(D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_M1, D_M2, D_M3, i_st, l_R, l_S, beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3)
        
    
    for i in range(i_st):
        debug_log.debug(f"Stg:{i} D_S3={D_S3[i]} D_M3={D_M3[i]} D_H3={D_H3[i]}", context="meanline")
        if i < i_st:
            debug_log.debug(f"Stg:{i+1} D_S1={D_S1[i]} D_M1={D_M1[i]} D_H1={D_H1[i]}", context="meanline")


    '''
    # --- Return all calculated values ---
    '''
    result = {
        # Process- & Fluidparameter
        'mflow': mflow,
        'n': n,
        'kappa': kappa,
        'R': R,
        'cp': cp,
        'i_st': i_st,
        
        # Temperatures (Static & Total)
        'T_t1': T_t1,
        'T_t2': T_t2,
        'T_t3': T_t3,
        'T_1': T_1,
        'T_2': T_2,
        'T_3': T_3,
        
        # Pressures (Static & Total)
        'p_1': p_1,
        'p_2': p_2,
        'p_3': p_3,
        'p_t1': p_t1,
        'p_t2': p_t2,
        'p_t3': p_t3,
        
        # Gemoetrydiameters in Milimeters(Shroud, Hub, Mean)
        'D_S1_mm': D_S1_mm, 'D_S2_mm': D_S2_mm, 'D_S3_mm': D_S3_mm,
        'D_H1_mm': D_H1_mm, 'D_H2_mm': D_H2_mm, 'D_H3_mm': D_H3_mm,
        'D_M1_mm': D_M1_mm, 'D_M2_mm': D_M2_mm, 'D_M3_mm': D_M3_mm,
        
        # Gemoetrydiameters in Meters(Shroud, Hub, Mean)
        'D_S1': D_S1, 'D_S2': D_S2, 'D_S3': D_S3,
        'D_H1': D_H1, 'D_H2': D_H2, 'D_H3': D_H3,
        'D_M1': D_M1, 'D_M2': D_M2, 'D_M3': D_M3,
        
        # Velocity triangles & widths
        'b1': b1, 'b2': b2, 'b3': b3,
        'cu1': cu1, 'cu2': cu2, 'cu3': cu3,
        'u1': u1, 'u2': u2, 'u3': u3,
        'cm1': cm1, 'cm2': cm2, 'cm3': cm3,
        
        # Energetics- & Bladeparameters
        'delta_h_t': delta_h_t,
        'l_R': l_R,
        'l_S': l_S,
        'l_R_t_R': l_R_t_R,
        'l_S_t_S': l_S_t_S,
        'd_R_l_R': d_R_l_R,
        'd_S_l_S': d_S_l_S,
        'incidence_R': incidence_R,
        'incidence_S': incidence_S,
        'z_R': z_R,
        'z_S': z_S,
        
        # Angles & Efficienties
        'beta_blade_1': beta_blade_1,
        'beta_blade_2': beta_blade_2,
        'alpha_blade_2': alpha_blade_2,
        'alpha_blade_3': alpha_blade_3,
        'TPR_M': TPR_M,
        'eta_sC_tt_M': eta_sC_tt_M,
        'eta_pC_tt_M': eta_pC_tt_M,
        
        # Configurations
        'fixed_radius_type': fixed_radius_type,
        'plot_channel_contour': plot_channel_contour
    
    }
 
    return result
'''
mflow, n, kappa, R, cp, i_st, T_t1, T_t2, T_t3, T_1, T_2, T_3, p_1, p_2, p_3, \
           p_t1, p_t2, p_t3, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_M1, D_M2, D_M3, \
           b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, l_R, l_S, \
           l_R_t_R, l_S_t_S, d_R_l_R, d_S_l_S, incidence_R, incidence_S, z_R, z_S, \
           beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3, TPR_M, eta_sC_tt_M, eta_pC_tt_M, fixed_radius_type
'''          
           
           
if __name__ == "__main__":
    results = meanline(GUI_On = 1)
    #print(results)
    #print(b2)

    #print(b3)
    #print(mflow, n, kappa, R, cp, i_st, T_t1, T_t2, T_t3, T_1, T_2, T_3, p_1, p_2, p_3, p_t1, p_t2, p_t3, D_S1, D_S2, D_S3, D_H1, D_H2, D_H3, D_m1, D_m2, D_m3, b1, b2, b3, cu1, cu2, cu3, u1, u2, u3, cm1, cm2, cm3, delta_h_t, l_R, l_S, l_R_t_R, l_S_t_S, d_R_l_R, d_S_l_S, incidence_R, incidence_S, z_R, z_S, beta_blade_1, beta_blade_2, alpha_blade_2, alpha_blade_3)
    #print(D_S1)
    #print(D_H1)