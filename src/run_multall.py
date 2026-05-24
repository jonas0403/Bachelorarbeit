import os
import subprocess
import ttkbootstrap as ttk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import debug_log

class MultallSimulation:
    def __init__(self, master_window, status_label):
        self.master = master_window
        self.status_label = status_label
        
        self.full_file_path = ""
        self.multall_file_path = ""
        self.working_dir = ""
        self.data_name = ""
        
    def choose_file_multall(self):
        self.full_file_path = tk.filedialog.askdirectory(title="Select a Multall directory")
        
        if self.full_file_path:
            
            self.working_dir = self.full_file_path
            
            print(f"Multall executable path: {self.working_dir}")
            debug_log.debug(f"Multall executable path: {self.working_dir}", context="run_multall")
            print(f"Data name: {self.data_name}")
            debug_log.debug(f"Data name: {self.data_name}", context="run_multall")
            
            self.status_label.config(text=f"Selected Multall Path: {self.working_dir}", foreground="green")
        
        else:
            self.status_label.config(text="Please Select Multall Path first", foreground="red")    
            
    def choose_file(self):
        self.full_file_path = tk.filedialog.askopenfilename(title="Select a file", filetypes=[("All files", "*.*")])
        
        if self.full_file_path:
            
            self.data_name = self.full_file_path
            
            print(f"Selected file: {self.full_file_path}")
            debug_log.debug(f"Selected file: {self.full_file_path}", context="run_multall")
            print(f"Data name: {self.data_name}")
            debug_log.debug(f"Data name: {self.data_name}", context="run_multall")
            
            self.status_label.config(text=f"Selected file: {self.data_name}", foreground="green")
        
        else:
            self.status_label.config(text="No file selected", foreground="red")    
            
    def cmd_control(self):
        if not self.full_file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return

        try:
            execcutable = self.working_dir
            cmd = f'multall.exe < "{self.data_name}"'
            full_cmd = f'start "Multall calculations" cmd /k "{cmd}"'

            
            subprocess.Popen(full_cmd, shell=True, cwd=self.working_dir)
            
            self.master.destroy()
        
        except Exception as e:
            messagebox.showerror("Error has occured", str(e))
        
        window.destroy()

if __name__ == "__main__": 
   
    window = tk.Tk()
    window.title("Multall Launcher")
    tk.Label(window, text="Multall Launcher", font=("Arial", 16)).pack(pady=10)
    window.geometry("400x250")

    main_frame = ttk.Frame(window, padding="10")
    main_frame.pack(fill="both", expand=True)
    
    file_status_label = tk.Label(main_frame, text="No file selected", font=("Arial", 10), foreground="red")
    file_status_label.pack(pady=10)

    sim = MultallSimulation(window, file_status_label)
    
    btn_multall = tk.Button(main_frame, text="Select a Multall directory", command=sim.choose_file_multall)
    btn_multall.pack(pady=5, fill='x')

    btn_select = tk.Button(main_frame, text="Select File to calculate", command=sim.choose_file)
    btn_select.pack(pady=5, fill='x')
    
    btn_start = tk.Button(main_frame, text="Start Multall", command=sim.cmd_control)
    btn_start.pack(pady=5, fill='x')

    window.mainloop()
        