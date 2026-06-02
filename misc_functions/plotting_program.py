import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
from io import StringIO
import collections

# --- DATA PARSING LOGIC ---
def make_valid_name(name):
    return str(name).strip()

def parse_data_file(filename):
    """A rule-based parser that strictly follows the user's file format."""
    results = collections.defaultdict(dict)
    current_main_cat = None
    header_template = "Name\tMflow\tTPR\teta_s"
    try:
        with open(filename, 'r', encoding='utf-8') as f: lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}"); return None

    # --- FIX: Use a while loop to correctly advance through the file ---
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        if not stripped_line:
            i += 1
            continue

        if stripped_line.upper().startswith("TITLE:"):
            current_main_cat = make_valid_name(stripped_line.split(':', 1)[1])
            i += 1
            continue

        if not current_main_cat:
            i += 1
            continue
            
        if header_template in stripped_line:
            raw_table_title = ""
            for j in range(i - 1, -1, -1):
                prev_line = lines[j].strip()
                if prev_line: raw_table_title = prev_line; break
            
            if not raw_table_title:
                i += 1
                continue

            data_rows, header_parts = [], [h for h in stripped_line.split('\t') if h]
            num_data_cols = len(header_parts) - 1
            
            k = i + 1
            while k < len(lines):
                data_line = lines[k].strip()
                if not data_line:
                    k += 1
                    continue
                
                parts = data_line.split('\t')
                if parts and parts[0].isdigit():
                    numeric_parts = parts[2 : 2 + num_data_cols]
                    row_data = []
                    for p in numeric_parts:
                        try: row_data.append(float(p.replace(',', '.').strip()))
                        except (ValueError, TypeError): row_data.append(None)
                    data_rows.append(row_data)
                    k += 1
                else:
                    break
            
            if data_rows:
                df = pd.DataFrame(data_rows, columns=header_parts[1:])
                df.dropna(how='all', inplace=True)
                if not df.empty: results[current_main_cat][make_valid_name(raw_table_title)] = df
            
            i = k # Continue searching from where the data block ended
            continue

        i += 1 # Default increment if nothing was found

    return dict(results)

# MAIN PLOTTING APPLICATION 
class PlottingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Data Plotter")
        self.geometry("1600x900")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.data, self.column_headers, self.style_vars = None, [], {}
        self.checkbox_vars, self.legend_entries = {}, []

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)
        main_frame.rowconfigure(0, weight=1)

        plots_area_frame = ttk.Frame(main_frame)
        plots_area_frame.grid(row=0, column=0, sticky="nsew")
        plots_area_frame.rowconfigure(0, weight=1)
        plots_area_frame.rowconfigure(1, weight=1)
        plots_area_frame.columnconfigure(0, weight=1)

        container1 = ttk.LabelFrame(plots_area_frame, text="Graph 1 (Top)", padding=5)
        container1.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=container1)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        container2 = ttk.LabelFrame(plots_area_frame, text="Graph 2 (Bottom)", padding=5)
        container2.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=container2)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        controls_area_frame = ttk.Frame(main_frame, width=500)
        controls_area_frame.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        controls_area_frame.pack_propagate(False)

        load_frame = ttk.Frame(controls_area_frame)
        load_frame.pack(fill='x', expand=False, pady=5)
        self.filepath_label = ttk.Label(load_frame, text="No file loaded.", relief="sunken", padding=5)
        self.filepath_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.load_button = ttk.Button(load_frame, text="Load...", command=self.load_file, width=8)
        self.load_button.pack(side=tk.LEFT)

        notebook = ttk.Notebook(controls_area_frame)
        notebook.pack(fill="both", expand=True)

        self.x_var, self.y1_var, self.y2_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.title1_var, self.title2_var = tk.StringVar(), tk.StringVar()
        self.xlabel_var = tk.StringVar()
        self.ylabel1_var, self.ylabel2_var = tk.StringVar(), tk.StringVar()
        self.auto_scale_var = tk.BooleanVar(value=True)
        self.xlim_min, self.xlim_max = tk.StringVar(), tk.StringVar()
        self.y1lim_min, self.y1lim_max = tk.StringVar(), tk.StringVar()
        self.y2lim_min, self.y2lim_max = tk.StringVar(), tk.StringVar()
        self.legend_pos_var = tk.StringVar(value='best')

        self._create_datasets_tab(notebook)
        self._create_axes_tab(notebook)
        self._create_legend_tab(notebook)

    def on_closing(self):
        self.quit(); self.destroy()

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _bind_mousewheel(self, event, canvas):
        self.bind_all("<MouseWheel>", lambda e, c=canvas: self._on_mousewheel(e, c))
    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def _create_datasets_tab(self, notebook):
        data_tab = ttk.Frame(notebook, padding=10)
        notebook.add(data_tab, text="Datasets")
        canvas_scroll = tk.Canvas(data_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(data_tab, orient="vertical", command=canvas_scroll.yview)
        self.datasets_frame = ttk.Frame(canvas_scroll)
        self.datasets_frame.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=self.datasets_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.bind('<Enter>', lambda e, c=canvas_scroll: self._bind_mousewheel(e, c))
        canvas_scroll.bind('<Leave>', self._unbind_mousewheel)
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_axes_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Axes & Titles")
        axis_frame = ttk.LabelFrame(tab, text="Axis Selection", padding=5)
        axis_frame.pack(fill='x', expand=True, pady=5)
        ttk.Label(axis_frame, text="Shared X-Axis:").grid(row=0, column=0, sticky='w', pady=2)
        self.x_combo = ttk.Combobox(axis_frame, textvariable=self.x_var, state="readonly")
        self.x_combo.grid(row=0, column=1, columnspan=3, sticky='ew', pady=2)
        ttk.Label(axis_frame, text="Top Plot Y-Axis:").grid(row=1, column=0, sticky='w', pady=2)
        self.y1_combo = ttk.Combobox(axis_frame, textvariable=self.y1_var, state="readonly")
        self.y1_combo.grid(row=1, column=1, columnspan=3, sticky='ew', pady=2)
        ttk.Label(axis_frame, text="Bottom Plot Y-Axis:").grid(row=2, column=0, sticky='w', pady=2)
        self.y2_combo = ttk.Combobox(axis_frame, textvariable=self.y2_var, state="readonly")
        self.y2_combo.grid(row=2, column=1, columnspan=3, sticky='ew', pady=2)
        
        title_frame = ttk.LabelFrame(tab, text="Titles and Labels", padding=5)
        title_frame.pack(fill='x', expand=True, pady=5)
        ttk.Label(title_frame, text="Top Title:").grid(row=0, column=0, sticky='w', pady=2)
        ttk.Entry(title_frame, textvariable=self.title1_var).grid(row=0, column=1, sticky='ew', pady=2)
        ttk.Label(title_frame, text="Bottom Title:").grid(row=1, column=0, sticky='w', pady=2)
        ttk.Entry(title_frame, textvariable=self.title2_var).grid(row=1, column=1, sticky='ew', pady=2)
        ttk.Label(title_frame, text="X-Axis Label:").grid(row=2, column=0, sticky='w', pady=2)
        ttk.Entry(title_frame, textvariable=self.xlabel_var).grid(row=2, column=1, sticky='ew', pady=2)
        ttk.Label(title_frame, text="Top Y-Axis Label:").grid(row=3, column=0, sticky='w', pady=2)
        ttk.Entry(title_frame, textvariable=self.ylabel1_var).grid(row=3, column=1, sticky='ew', pady=2)
        ttk.Label(title_frame, text="Bottom Y-Axis Label:").grid(row=4, column=0, sticky='w', pady=2)
        ttk.Entry(title_frame, textvariable=self.ylabel2_var).grid(row=4, column=1, sticky='ew', pady=2)
        title_frame.columnconfigure(1, weight=1)
        
        limits_frame = ttk.LabelFrame(tab, text="Axis Limits", padding=5)
        limits_frame.pack(fill='x', expand=True, pady=5)
        limit_entries = [ ttk.Entry(limits_frame, textvariable=v, width=8, state='disabled') for v in 
                          [self.xlim_min, self.xlim_max, self.y1lim_min, self.y1lim_max, self.y2lim_min, self.y2lim_max] ]
        ttk.Label(limits_frame, text="X:").grid(row=1, column=0), ttk.Label(limits_frame, text="Min").grid(row=0, column=1), ttk.Label(limits_frame, text="Max").grid(row=0, column=2)
        limit_entries[0].grid(row=1, column=1), limit_entries[1].grid(row=1, column=2)
        ttk.Label(limits_frame, text="Y (Top):").grid(row=2, column=0), limit_entries[2].grid(row=2, column=1), limit_entries[3].grid(row=2, column=2)
        ttk.Label(limits_frame, text="Y (Bot):").grid(row=3, column=0), limit_entries[4].grid(row=3, column=1), limit_entries[5].grid(row=3, column=2)
        def toggle_limits_state():
            state = 'disabled' if self.auto_scale_var.get() else 'normal'
            for entry in limit_entries: entry.config(state=state)
        auto_scale_check = ttk.Checkbutton(limits_frame, text="Auto-scale Axes", variable=self.auto_scale_var, command=toggle_limits_state)
        auto_scale_check.grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Button(tab, text="Update Plots", command=self._update_all_plots).pack(pady=10)

    def _create_legend_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=10)
        notebook.add(tab, text="Legend")
        pos_frame = ttk.Frame(tab)
        pos_frame.pack(fill='x', expand=True, pady=(0,5))
        ttk.Label(pos_frame, text="Position:").pack(side='left')
        pos_combo = ttk.Combobox(pos_frame, textvariable=self.legend_pos_var, state='readonly', values=[
            'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 
            'center left', 'center right', 'lower center', 'upper center', 'center'
        ])
        pos_combo.pack(side='left', padx=5)
        pos_combo.bind("<<ComboboxSelected>>", lambda e: self._update_all_plots())
        ttk.Button(pos_frame, text="Add Entry", command=self._add_legend_entry).pack(side='left', padx=10)
        canvas_scroll = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas_scroll.yview)
        self.legend_frame = ttk.Frame(canvas_scroll)
        self.legend_frame.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=self.legend_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.bind('<Enter>', lambda e, c=canvas_scroll: self._bind_mousewheel(e, c))
        canvas_scroll.bind('<Leave>', self._unbind_mousewheel)
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if not filepath: return
        self.data = parse_data_file(filepath)
        cleaned_data = { mcn: {tn: df for tn, df in tables.items() if not df.empty and not df.isnull().all().all()}
                         for mcn, tables in self.data.items() }
        self.data = {mcn: tables for mcn, tables in cleaned_data.items() if tables}
        self.filepath_label.config(text=filepath)
        if not self.data:
            print("No valid tables found after cleaning.")
            self._setup_controls(clear=True)
            return
        self._initialize_styles()
        try:
            self.column_headers = next(iter(next(iter(self.data.values())).values())).columns.tolist()
        except StopIteration:
            self.column_headers = []
        self._setup_controls()
        print("Data loaded successfully.")

    def _initialize_styles(self):
        self.style_vars.clear()
        colors, markers, linestyles = plt.rcParams['axes.prop_cycle'].by_key()['color'], ['o','s','^','D','v','P','X','*'], ['-','--',':','-.']
        for i, (mcn, tables) in enumerate(self.data.items()):
            self.style_vars[mcn] = {}
            for j, tn in enumerate(tables.keys()):
                self.style_vars[mcn][tn] = {
                    'color': tk.StringVar(value=colors[j % len(colors)]),
                    'linestyle': tk.StringVar(value=linestyles[i % len(linestyles)]),
                    'marker': tk.StringVar(value=markers[i % len(markers)]),
                    'sort_by': tk.StringVar(value='Default (X-Axis)'),
                    'size': tk.StringVar(value='2'),
                }

    def _setup_controls(self, clear=False):
        for widget in self.datasets_frame.winfo_children(): widget.destroy()
        self.checkbox_vars.clear()
        
        axes_combos = [self.x_combo, self.y1_combo, self.y2_combo]
        for combo in axes_combos: combo['values'] = [] if clear else self.column_headers
        if clear: self.x_var.set(''), self.y1_var.set(''), self.y2_var.set(''); self._update_all_plots(); return
        
        if self.column_headers:
            self.x_var.set('Mflow' if 'Mflow' in self.column_headers else self.column_headers[0])
            self.y1_var.set('TPR' if 'TPR' in self.column_headers else self.column_headers[1])
            self.y2_var.set('eta_s' if 'eta_s' in self.column_headers else self.column_headers[1])
            
        linestyles, markers = ['-', '--', '-.', ':'], ['None', 'o', 's', '^', 'D', 'v', 'P', 'X', '*']
        sort_options, size_options = ['Default (X-Axis)'] + self.column_headers, ['1', '2', '3', '4', '6', '8']
        
        for mcn, tables in self.data.items():
            self.checkbox_vars[mcn] = {'main_var': tk.BooleanVar(value=False), 'tables': {}}
            main_cb = ttk.Checkbutton(self.datasets_frame, text=mcn, variable=self.checkbox_vars[mcn]['main_var'],
                                      command=lambda m=mcn: self._toggle_children(m))
            main_cb.pack(anchor='w', padx=5, pady=3)

            for tn in tables.keys():
                style = self.style_vars[mcn][tn]
                self.checkbox_vars[mcn]['tables'][tn] = {'var': tk.BooleanVar(value=False)}
                row_frame = ttk.Frame(self.datasets_frame)
                row_frame.pack(fill='x', expand=True, padx=20, pady=1)
                row_frame.columnconfigure(0, weight=1)
                
                cb = tk.Checkbutton(row_frame, text=tn, variable=self.checkbox_vars[mcn]['tables'][tn]['var'],
                                    wraplength=200, justify='left', anchor='w', command=self._update_all_plots)
                cb.grid(row=0, column=0, rowspan=2, sticky='w')
                
                style_frame_top = ttk.Frame(row_frame)
                style_frame_top.grid(row=0, column=1, sticky='e')
                style_frame_bottom = ttk.Frame(row_frame)
                style_frame_bottom.grid(row=1, column=1, sticky='e', pady=(2,0))

                color_btn = tk.Button(style_frame_top, text="Color", width=5, bg=style['color'].get())
                color_btn.config(command=lambda s=style: self._choose_color_from_palette(s['color'], color_btn))
                
                widgets_top = [
                    (color_btn, 2),
                    (ttk.Combobox(style_frame_top, textvariable=style['linestyle'], values=linestyles, width=4, state='readonly'), 2),
                    (ttk.Combobox(style_frame_top, textvariable=style['marker'], values=markers, width=5, state='readonly'), 2),
                    (ttk.Combobox(style_frame_top, textvariable=style['size'], values=size_options, width=3, state='readonly'), 2)
                ]
                for widget, pad in widgets_top:
                    if isinstance(widget, ttk.Combobox):
                        widget.bind("<<ComboboxSelected>>", lambda e: self._update_all_plots())
                    widget.pack(side='left', padx=pad)
                
                ttk.Label(style_frame_bottom, text="Sort By:").pack(side='left')
                sort_combo = ttk.Combobox(style_frame_bottom, textvariable=style['sort_by'], values=sort_options, width=15, state='readonly')
                sort_combo.bind("<<ComboboxSelected>>", lambda e: self._update_all_plots())
                sort_combo.pack(side='left', padx=2)
        
        self._update_all_plots()

    def _toggle_children(self, mcn):
        is_checked = self.checkbox_vars[mcn]['main_var'].get()
        for table_vars in self.checkbox_vars[mcn]['tables'].values():
            table_vars['var'].set(is_checked)
        self._update_all_plots()

    def _choose_color(self, color_var, button):
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=color_var.get())
        if color_code and color_code[1]:
            color_var.set(color_code[1])
            button.config(bg=color_code[1])
            self._update_all_plots()

    def _choose_color_from_palette(self, color_var, button):
        popup = tk.Toplevel(self)
        popup.title("Select a Color")
        PRESET_COLORS = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            '#bcbd22', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94'
        ]
        def on_color_select(color):
            color_var.set(color)
            button.config(bg=color)
            self._update_all_plots()
            popup.destroy()
        for i, color in enumerate(PRESET_COLORS):
            row, col = divmod(i, 4)
            btn = tk.Button(popup, bg=color, width=4, height=2, command=lambda c=color: on_color_select(c))
            btn.grid(row=row, column=col, padx=2, pady=2)
        popup.transient(self); popup.grab_set()

    def _add_legend_entry(self):
        entry_data = { 'text_var': tk.StringVar(value=f"Entry {len(self.legend_entries)+1}"), 'color_var': tk.StringVar(value='#333333'),
                       'linestyle_var': tk.StringVar(value='-'), 'marker_var': tk.StringVar(value='None') }
        self.legend_entries.append(entry_data)
        frame = ttk.Frame(self.legend_frame)
        frame.pack(fill='x', expand=True, pady=2)
        entry_data['frame'] = frame
        ttk.Button(frame, text="X", width=2, command=lambda ed=entry_data: self._remove_legend_entry(ed)).pack(side='left')
        ttk.Entry(frame, textvariable=entry_data['text_var']).pack(side='left', fill='x', expand=True, padx=5)
        color_btn = tk.Button(frame, text="Color", width=5, bg=entry_data['color_var'].get())
        color_btn.config(command=lambda cv=entry_data['color_var'], b=color_btn: self._choose_color_from_palette(cv, b))
        color_btn.pack(side='left', padx=5)
        for cfg in [('linestyle_var', ['-', '--', '-.', ':', 'None'], 4), ('marker_var', ['None', 'o', 's', '^', 'D'], 5)]:
            combo = ttk.Combobox(frame, textvariable=entry_data[cfg[0]], values=cfg[1], width=cfg[2], state='readonly')
            combo.bind("<<ComboboxSelected>>", lambda e: self._update_all_plots())
            combo.pack(side='left', padx=5)
        self._update_all_plots()

    def _remove_legend_entry(self, entry_data):
        self.legend_entries.remove(entry_data)
        entry_data['frame'].destroy()
        self._update_all_plots()

    def _update_all_plots(self):
        self._draw_plot(self.ax1, self.canvas1, self.x_var.get(), self.y1_var.get(),
                        self.title1_var, self.xlabel_var, self.ylabel1_var,
                        self.y1lim_min, self.y1lim_max)
        self._draw_plot(self.ax2, self.canvas2, self.x_var.get(), self.y2_var.get(),
                        self.title2_var, self.xlabel_var, self.ylabel2_var,
                        self.y2lim_min, self.y2lim_max)

    def _draw_plot(self, ax, canvas, x_col, y_col, title_var, xlabel_var, ylabel_var, ylim_min_var, ylim_max_var):
        ax.clear()
        if self.data and x_col and y_col:
            for mcn, mcn_vars in self.checkbox_vars.items():
                for tn, style in mcn_vars['tables'].items():
                    if style['var'].get():
                        try:
                            df, shared_style = self.data[mcn][tn], self.style_vars[mcn][tn]
                            plot_df = df.dropna(subset=[x_col, y_col])
                            sort_col = shared_style['sort_by'].get()
                            sort_by = x_col if sort_col == 'Default (X-Axis)' or sort_col not in plot_df.columns else sort_col
                            plot_df = plot_df.sort_values(by=sort_by, ignore_index=True)
                            if not plot_df.empty:
                                marker, size = shared_style['marker'].get(), float(shared_style['size'].get())
                                ax.plot(plot_df[x_col], plot_df[y_col], color=shared_style['color'].get(),
                                        linestyle=shared_style['linestyle'].get(), marker=None if marker == 'None' else marker,
                                        linewidth=size, markersize=size + 2)
                        except (KeyError, ValueError): continue
            
            ax.set_title(title_var.get()), ax.set_xlabel(xlabel_var.get()), ax.set_ylabel(ylabel_var.get())
            if not self.auto_scale_var.get():
                try: xmin, xmax = float(self.xlim_min.get()), float(self.xlim_max.get())
                except (ValueError, TypeError): xmin, xmax = None, None
                try: ymin, ymax = float(ylim_min_var.get()), float(ylim_max_var.get())
                except (ValueError, TypeError): ymin, ymax = None, None
                ax.set_xlim(xmin, xmax), ax.set_ylim(ymin, ymax)

            legend_handles, legend_labels = [], []
            for entry in self.legend_entries:
                ls, marker = entry['linestyle_var'].get(), entry['marker_var'].get()
                handle = Line2D([0], [0], color=entry['color_var'].get(), linestyle=' ' if ls == 'None' else ls,
                                marker=None if marker == 'None' else marker)
                legend_handles.append(handle), legend_labels.append(entry['text_var'].get())
            if legend_handles:
                ax.legend(handles=legend_handles, labels=legend_labels, loc=self.legend_pos_var.get())
        else:
            ax.set_title("Select a file and axes")
        ax.grid(True)
        canvas.draw()

if __name__ == "__main__":
    app = PlottingApp()
    app.mainloop()