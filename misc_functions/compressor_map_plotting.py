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

# DATA PARSING LOGIC 
def make_valid_name(name):
    return str(name).strip()

def parse_data_file(filename):
    results = collections.defaultdict(dict)
    current_main_cat = None
    header_template = "Name\tMflow\tTPR\teta_s\teta_p"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line: continue
        if stripped_line.upper().startswith("TITLE:"):
            current_main_cat = make_valid_name(stripped_line.split(':', 1)[1])
            continue
        if not current_main_cat: continue
        if header_template in stripped_line:
            raw_table_title = ""
            for j in range(i - 1, -1, -1):
                prev_line = lines[j].strip()
                if prev_line:
                    raw_table_title = prev_line
                    break
            if not raw_table_title: continue
            data_rows, header_parts = [], [h for h in stripped_line.split('\t') if h]
            num_data_cols = len(header_parts) - 1
            for k in range(i + 1, len(lines)):
                data_line = lines[k].strip()
                if not data_line: continue
                parts = data_line.split('\t')
                if parts and parts[0].isdigit():
                    numeric_parts_to_process = parts[2 : 2 + num_data_cols]
                    row_data = []
                    for p in numeric_parts_to_process:
                        p_clean = p.replace(',', '.').strip()
                        try:
                            row_data.append(float(p_clean))
                        except (ValueError, TypeError):
                            row_data.append(None)
                    data_rows.append(row_data)
                else:
                    break
            if data_rows:
                df_columns = header_parts[1:]
                num_cols = len(df_columns)
                padded_data = [row[:num_cols] + [None]*(num_cols - len(row)) for row in data_rows]
                df = pd.DataFrame(padded_data, columns=df_columns)
                df.dropna(how='all', inplace=True)
                if not df.empty:
                    table_key = make_valid_name(raw_table_title)
                    results[current_main_cat][table_key] = df
    return dict(results)

# MAIN PLOTTING APPLICATION 
class PlottingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Data Plotter")
        self.geometry("1400x950")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.data, self.column_headers, self.style_vars = None, [], {}
        self.sync_active = tk.BooleanVar(value=False)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        ttk.Label(top_frame, text="Data File:").pack(side=tk.LEFT, padx=5)
        self.filepath_label = ttk.Label(top_frame, text="No file loaded.", relief="sunken", padding=5)
        self.filepath_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.load_button = ttk.Button(top_frame, text="Load Data File...", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        sync_button = ttk.Checkbutton(top_frame, text="Sync Selections", variable=self.sync_active, style='Toolbutton')
        sync_button.pack(side=tk.LEFT, padx=5)

        plots_frame = ttk.Frame(main_frame)
        plots_frame.pack(fill=tk.BOTH, expand=True)
        plots_frame.columnconfigure(0, weight=1), plots_frame.columnconfigure(1, weight=1)
        plots_frame.rowconfigure(0, weight=1)
        self.plot1 = self.create_plot_widget(plots_frame, "Graph 1")
        self.plot1['frame'].grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        self.plot2 = self.create_plot_widget(plots_frame, "Graph 2")
        self.plot2['frame'].grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

    def on_closing(self):
        self.quit(), self.destroy()

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _bind_mousewheel(self, event, canvas):
        self.bind_all("<MouseWheel>", lambda e, c=canvas: self._on_mousewheel(e, c))
    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    def create_plot_widget(self, parent, title):
        container = ttk.LabelFrame(parent, text=title, padding="10")
        container.columnconfigure(0, weight=1), container.rowconfigure(0, weight=1)
        fig, ax = plt.subplots(figsize=(7, 5))
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        controls_frame = ttk.Frame(container, padding=5)
        controls_frame.grid(row=1, column=0, sticky="ew")
        notebook = ttk.Notebook(controls_frame)
        notebook.pack(fill="x", expand=True, pady=5)
        
        data_tab = ttk.Frame(notebook, padding=10)
        notebook.add(data_tab, text="Datasets & Styles")
        canvas_scroll = tk.Canvas(data_tab, height=200, highlightthickness=0)
        scrollbar = ttk.Scrollbar(data_tab, orient="vertical", command=canvas_scroll.yview)
        scrollable_frame = ttk.Frame(canvas_scroll)
        scrollable_frame.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.bind('<Enter>', lambda e, c=canvas_scroll: self._bind_mousewheel(e, c))
        canvas_scroll.bind('<Leave>', self._unbind_mousewheel)
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        settings_tab = ttk.Frame(notebook, padding=10)
        notebook.add(settings_tab, text="Axes & Titles")
        axis_frame = ttk.Frame(settings_tab)
        axis_frame.pack(fill='x', expand=True, pady=(5,10))
        x_var, y_var = tk.StringVar(), tk.StringVar()
        ttk.Label(axis_frame, text="X-Axis:").grid(row=0, column=0, padx=5, sticky='w')
        x_combo = ttk.Combobox(axis_frame, textvariable=x_var, state="readonly", width=15)
        x_combo.grid(row=0, column=1, padx=5)
        ttk.Label(axis_frame, text="Y-Axis:").grid(row=0, column=2, padx=5, sticky='w')
        y_combo = ttk.Combobox(axis_frame, textvariable=y_var, state="readonly", width=15)
        y_combo.grid(row=0, column=3, padx=5)
        title_frame = ttk.Frame(settings_tab)
        title_frame.pack(fill='x', expand=True, pady=5)
        title_var, xlabel_var, ylabel_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(title_frame, text="Plot Title:").grid(row=0, column=0, sticky='w')
        ttk.Entry(title_frame, textvariable=title_var, width=60).grid(row=0, column=1, sticky='ew')
        ttk.Label(title_frame, text="X-Axis Label:").grid(row=1, column=0, sticky='w')
        ttk.Entry(title_frame, textvariable=xlabel_var, width=60).grid(row=1, column=1, sticky='ew')
        ttk.Label(title_frame, text="Y-Axis Label:").grid(row=2, column=0, sticky='w')
        ttk.Entry(title_frame, textvariable=ylabel_var, width=60).grid(row=2, column=1, sticky='ew')
        title_frame.columnconfigure(1, weight=1)
        limits_frame = ttk.Frame(settings_tab)
        limits_frame.pack(fill='x', expand=True, pady=(10,5))
        auto_scale_var = tk.BooleanVar(value=True)
        xlim_min_var, xlim_max_var, ylim_min_var, ylim_max_var = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        limit_entries = [ ttk.Entry(limits_frame, textvariable=v, width=8, state='disabled') for v in [xlim_min_var, xlim_max_var, ylim_min_var, ylim_max_var] ]
        ttk.Label(limits_frame, text="X Min:").grid(row=0, column=1), limit_entries[0].grid(row=0, column=2)
        ttk.Label(limits_frame, text="X Max:").grid(row=0, column=3), limit_entries[1].grid(row=0, column=4, padx=(0,20))
        ttk.Label(limits_frame, text="Y Min:").grid(row=0, column=5), limit_entries[2].grid(row=0, column=6)
        ttk.Label(limits_frame, text="Y Max:").grid(row=0, column=7), limit_entries[3].grid(row=0, column=8)
        def toggle_limits_state():
            state = 'disabled' if auto_scale_var.get() else 'normal'
            for entry in limit_entries: entry.config(state=state)
        auto_scale_check = ttk.Checkbutton(limits_frame, text="Auto-scale Axes", variable=auto_scale_var, command=toggle_limits_state)
        auto_scale_check.grid(row=0, column=0, padx=5)
        
        legend_tab = ttk.Frame(notebook, padding=10)
        notebook.add(legend_tab, text="Legend")
        legend_pos_var = tk.StringVar(value='best')
        legend_pos_frame = ttk.Frame(legend_tab)
        legend_pos_frame.pack(fill='x', expand=True, pady=(0,5))
        ttk.Label(legend_pos_frame, text="Legend Position:").pack(side='left')
        pos_combo = ttk.Combobox(legend_pos_frame, textvariable=legend_pos_var, state='readonly', values=[
            'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 
            'center left', 'center right', 'lower center', 'upper center', 'center'
        ])
        pos_combo.pack(side='left', padx=5)
        legend_canvas_scroll = tk.Canvas(legend_tab, height=200, highlightthickness=0)
        legend_scrollbar = ttk.Scrollbar(legend_tab, orient="vertical", command=legend_canvas_scroll.yview)
        legend_scrollable_frame = ttk.Frame(legend_canvas_scroll)
        legend_scrollable_frame.bind("<Configure>", lambda e: legend_canvas_scroll.configure(scrollregion=legend_canvas_scroll.bbox("all")))
        legend_canvas_scroll.create_window((0, 0), window=legend_scrollable_frame, anchor="nw")
        legend_canvas_scroll.configure(yscrollcommand=legend_scrollbar.set)
        legend_canvas_scroll.bind('<Enter>', lambda e, c=legend_canvas_scroll: self._bind_mousewheel(e, c))
        legend_canvas_scroll.bind('<Leave>', self._unbind_mousewheel)
        
        plot_widget_data = {
            'frame': container, 'fig': fig, 'ax': ax, 'canvas': canvas, 'x_var': x_var, 
            'y_var': y_var, 'checkbox_frame': scrollable_frame, 'checkbox_vars': {}, 
            'title_var': title_var, 'xlabel_var': xlabel_var, 'ylabel_var': ylabel_var, 
            'x_combo': x_combo, 'y_combo': y_combo, 'auto_scale_var': auto_scale_var, 
            'xlim_min_var': xlim_min_var, 'xlim_max_var': xlim_max_var, 
            'ylim_min_var': ylim_min_var, 'ylim_max_var': ylim_max_var,
            'legend_entries': [], 'legend_frame': legend_scrollable_frame, 'legend_pos_var': legend_pos_var
        }
        
        add_legend_button = ttk.Button(legend_pos_frame, text="Add Entry", command=lambda pw=plot_widget_data: self._add_legend_entry(pw))
        add_legend_button.pack(side='left', padx=10)
        legend_canvas_scroll.pack(side="left", fill="both", expand=True)
        legend_scrollbar.pack(side="right", fill="y")
        update_button = ttk.Button(settings_tab, text="Update Plot", command=lambda: self.update_plot(plot_widget_data))
        update_button.pack(pady=10)
        x_combo.bind("<<ComboboxSelected>>", lambda e: xlabel_var.set(x_var.get()))
        y_combo.bind("<<ComboboxSelected>>", lambda e: ylabel_var.set(y_var.get()))
        pos_combo.bind("<<ComboboxSelected>>", lambda e, pw=plot_widget_data: self.update_plot(pw))
        
        return plot_widget_data

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if not filepath: return
        self.data = parse_data_file(filepath)
        cleaned_data = {}
        if self.data:
            for main_cat_name, tables in self.data.items():
                valid_tables = { name: df for name, df in tables.items() if not df.empty and not df.isnull().all().all() }
                if valid_tables: cleaned_data[main_cat_name] = valid_tables
        self.data = cleaned_data
        self.filepath_label.config(text=filepath)
        if not self.data:
            print("Failed to parse data or no valid tables found after cleaning.")
            self.setup_plot_controls(self.plot1, clear_only=True)
            self.setup_plot_controls(self.plot2, clear_only=True)
            return
        self._initialize_styles()
        try:
            first_df = next(iter(next(iter(self.data.values())).values()))
            self.column_headers = first_df.columns.tolist()
        except StopIteration:
            self.column_headers = []
            print("Warning: Loaded file, but no valid data tables were found.")
        self.setup_plot_controls(self.plot1)
        self.setup_plot_controls(self.plot2)
        print("Data loaded successfully.")

    def _initialize_styles(self):
        """Create the central, shared style dictionary with smart defaults."""
        self.style_vars.clear()
        default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        default_markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
        default_linestyles = ['-', '--', '-.', ':']
        
        for i, (main_cat_name, tables) in enumerate(self.data.items()):
            self.style_vars[main_cat_name] = {}
            marker = default_markers[i % len(default_markers)]
            linestyle = default_linestyles[i % len(default_linestyles)]
            for j, table_name in enumerate(tables.keys()):
                self.style_vars[main_cat_name][table_name] = {
                    'color': tk.StringVar(value=default_colors[j % len(default_colors)]),
                    'linestyle': tk.StringVar(value=linestyle),
                    'marker': tk.StringVar(value=marker),
                    'sort_by': tk.StringVar(value='Default (X-Axis)'),
                    'size': tk.StringVar(value='2'), # NEW: Add size variable
                    'color_buttons': [], 
                }

    def _update_both_plots(self):
        self.update_plot(self.plot1), self.update_plot(self.plot2)

    def _toggle_children(self, plot_widget, main_cat_name):
        is_checked = plot_widget['checkbox_vars'][main_cat_name]['main_var'].get()
        if self.sync_active.get():
            other_plot = self.plot2 if plot_widget is self.plot1 else self.plot1
            other_plot['checkbox_vars'][main_cat_name]['main_var'].set(is_checked)
        for table_name in plot_widget['checkbox_vars'][main_cat_name]['tables']:
            plot_widget['checkbox_vars'][main_cat_name]['tables'][table_name]['var'].set(is_checked)
            if self.sync_active.get():
                other_plot['checkbox_vars'][main_cat_name]['tables'][table_name]['var'].set(is_checked)
        self._update_both_plots()
        
    def _choose_color(self, color_var, buttons_list):
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=color_var.get())
        if color_code and color_code[1]:
            color_var.set(color_code[1])
            if isinstance(buttons_list, list):
                 for btn in buttons_list: btn.config(bg=color_code[1])
            else:
                 buttons_list.config(bg=color_code[1])
            self._update_both_plots()

    def _on_checkbox_click(self, clicked_plot_widget, main_cat_name, table_name):
        self.update_plot(clicked_plot_widget)
        if self.sync_active.get():
            state = clicked_plot_widget['checkbox_vars'][main_cat_name]['tables'][table_name]['var'].get()
            other_plot = self.plot2 if clicked_plot_widget is self.plot1 else self.plot1
            other_plot['checkbox_vars'][main_cat_name]['tables'][table_name]['var'].set(state)
            self.update_plot(other_plot)

    def _add_legend_entry(self, plot_widget):
        entry_data = {
            'text_var': tk.StringVar(value=f"Entry {len(plot_widget['legend_entries']) + 1}"),
            'color_var': tk.StringVar(value='#333333'),
            'linestyle_var': tk.StringVar(value='-'),
            'marker_var': tk.StringVar(value='None'),
        }
        plot_widget['legend_entries'].append(entry_data)
        frame = ttk.Frame(plot_widget['legend_frame'])
        frame.pack(fill='x', expand=True, pady=2)
        entry_data['frame'] = frame
        remove_btn = ttk.Button(frame, text="X", width=2, command=lambda pw=plot_widget, ed=entry_data: self._remove_legend_entry(pw, ed))
        remove_btn.pack(side='left')
        entry = ttk.Entry(frame, textvariable=entry_data['text_var'])
        entry.pack(side='left', fill='x', expand=True, padx=5)
        color_btn = tk.Button(frame, text="Color", width=5, bg=entry_data['color_var'].get())
        color_btn.config(command=lambda cv=entry_data['color_var'], b=color_btn: self._choose_color(cv, b))
        color_btn.pack(side='left', padx=5)
        ls_combo = ttk.Combobox(frame, textvariable=entry_data['linestyle_var'], values=['-', '--', '-.', ':', 'None'], width=4, state='readonly')
        ls_combo.bind("<<ComboboxSelected>>", lambda e, pw=plot_widget: self.update_plot(pw))
        ls_combo.pack(side='left', padx=5)
        m_combo = ttk.Combobox(frame, textvariable=entry_data['marker_var'], values=['None', 'o', 's', '^', 'D'], width=5, state='readonly')
        m_combo.bind("<<ComboboxSelected>>", lambda e, pw=plot_widget: self.update_plot(pw))
        m_combo.pack(side='left')
        self.update_plot(plot_widget)

    def _remove_legend_entry(self, plot_widget, entry_data):
        plot_widget['legend_entries'].remove(entry_data)
        entry_data['frame'].destroy()
        self.update_plot(plot_widget)

    def setup_plot_controls(self, plot_widget, clear_only=False):
        checkbox_frame = plot_widget['checkbox_frame']
        for widget in checkbox_frame.winfo_children(): widget.destroy()
        plot_widget['checkbox_vars'].clear()
        
        if plot_widget is self.plot1 and self.style_vars:
            for main_cat in self.style_vars.values():
                for table_style in main_cat.values():
                    table_style['color_buttons'] = []

        x_combo, y_combo = plot_widget['x_combo'], plot_widget['y_combo']
        if clear_only:
            x_combo['values'], y_combo['values'] = [], []
            plot_widget['x_var'].set(''), plot_widget['y_var'].set('')
            self.update_plot(plot_widget)
            return
        
        x_combo['values'] = self.column_headers
        y_combo['values'] = self.column_headers
        if self.column_headers:
            default_x = 'Mflow'
            default_y = 'TPR' if plot_widget is self.plot1 else 'eta_s'
            x_val = default_x if default_x in self.column_headers else self.column_headers[0]
            y_val = default_y if default_y in self.column_headers else (self.column_headers[1] if len(self.column_headers) > 1 else '')
            plot_widget['x_var'].set(x_val), plot_widget['y_var'].set(y_val)
            plot_widget['title_var'].set(f"{y_val} vs. {x_val}")
            plot_widget['xlabel_var'].set(x_val), plot_widget['ylabel_var'].set(y_val)
            
        linestyles = ['-', '--', '-.', ':']
        markers = ['None', 'o', 's', '^', 'D', 'v', 'P', 'X', '*']
        sort_options = ['Default (X-Axis)'] + self.column_headers
        size_options = ['1', '2', '3', '4', '6', '8']
        
        for main_cat_name, tables in self.data.items():
            vars_dict = {'main_var': tk.BooleanVar(value=False), 'tables': {}}
            plot_widget['checkbox_vars'][main_cat_name] = vars_dict
            main_cb = ttk.Checkbutton(checkbox_frame, text=main_cat_name, variable=vars_dict['main_var'],
                                      command=lambda pw=plot_widget, mcn=main_cat_name: self._toggle_children(pw, mcn))
            main_cb.pack(anchor='w', padx=5, pady=3)

            for table_name in tables.keys():
                shared_style = self.style_vars[main_cat_name][table_name]
                local_style_dict = {'var': tk.BooleanVar(value=False)}
                vars_dict['tables'][table_name] = local_style_dict
                row_frame = ttk.Frame(checkbox_frame)
                row_frame.pack(fill='x', expand=True, padx=20, pady=1)
                row_frame.columnconfigure(0, weight=1)
                table_cb = tk.Checkbutton(row_frame, text=table_name, variable=local_style_dict['var'],
                                          wraplength=200, justify='left', anchor='w',
                                          command=lambda pw=plot_widget, mcn=main_cat_name, tn=table_name: self._on_checkbox_click(pw, mcn, tn))
                table_cb.grid(row=0, column=0, sticky='w')
                style_frame = ttk.Frame(row_frame)
                style_frame.grid(row=0, column=1, sticky='e')
                color_btn = tk.Button(style_frame, text="Color", width=5, bg=shared_style['color'].get())
                color_btn.config(command=lambda m=main_cat_name, t=table_name: self._choose_color(self.style_vars[m][t]['color'], self.style_vars[m][t]['color_buttons']))
                shared_style['color_buttons'].append(color_btn)
                color_btn.pack(side='left', padx=2)
                ls_combo = ttk.Combobox(style_frame, textvariable=shared_style['linestyle'], values=linestyles, width=4, state='readonly')
                ls_combo.bind("<<ComboboxSelected>>", lambda e: self._update_both_plots())
                ls_combo.pack(side='left', padx=2)
                m_combo = ttk.Combobox(style_frame, textvariable=shared_style['marker'], values=markers, width=5, state='readonly')
                m_combo.bind("<<ComboboxSelected>>", lambda e: self._update_both_plots())
                m_combo.pack(side='left', padx=2)
                sort_combo = ttk.Combobox(style_frame, textvariable=shared_style['sort_by'], values=sort_options, width=12, state='readonly')
                sort_combo.bind("<<ComboboxSelected>>", lambda e: self._update_both_plots())
                sort_combo.pack(side='left', padx=2)
                size_combo = ttk.Combobox(style_frame, textvariable=shared_style['size'], values=size_options, width=3, state='readonly')
                size_combo.bind("<<ComboboxSelected>>", lambda e: self._update_both_plots())
                size_combo.pack(side='left', padx=2)
        
        self.update_plot(plot_widget)

    def update_plot(self, plot_widget):
        ax = plot_widget['ax']
        x_col, y_col = plot_widget['x_var'].get(), plot_widget['y_var'].get()
        ax.clear()
        if self.data and x_col and y_col:
            for main_cat_name, main_cat_vars in plot_widget['checkbox_vars'].items():
                for table_name, style in main_cat_vars['tables'].items():
                    if style['var'].get():
                        try:
                            df = self.data[main_cat_name][table_name]
                            shared_style = self.style_vars[main_cat_name][table_name]
                            plot_df = df.dropna(subset=[x_col, y_col])
                            sort_col = shared_style['sort_by'].get()
                            if sort_col != 'Default (X-Axis)' and sort_col in plot_df.columns:
                                plot_df = plot_df.sort_values(by=sort_col, ignore_index=True)
                            else:
                                plot_df = plot_df.sort_values(by=x_col, ignore_index=True)
                            if not plot_df.empty:
                                marker = shared_style['marker'].get()
                                if marker == 'None': marker = None
                                size = float(shared_style['size'].get())
                                ax.plot(plot_df[x_col], plot_df[y_col],
                                        color=shared_style['color'].get(),
                                        linestyle=shared_style['linestyle'].get(),
                                        marker=marker,
                                        linewidth=size,
                                        markersize=size + 2) # Slightly larger markers
                        except (KeyError, ValueError):
                            continue
            
            ax.set_title(plot_widget['title_var'].get())
            ax.set_xlabel(plot_widget['xlabel_var'].get())
            ax.set_ylabel(plot_widget['ylabel_var'].get())
            if not plot_widget['auto_scale_var'].get():
                try: xmin, xmax = float(plot_widget['xlim_min_var'].get()), float(plot_widget['xlim_max_var'].get())
                except (ValueError, TypeError): xmin, xmax = None, None
                try: ymin, ymax = float(plot_widget['ylim_min_var'].get()), float(plot_widget['ylim_max_var'].get())
                except (ValueError, TypeError): ymin, ymax = None
                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)

            legend_handles, legend_labels = [], []
            for entry in plot_widget['legend_entries']:
                ls, marker = entry['linestyle_var'].get(), entry['marker_var'].get()
                if ls == 'None': ls = ' '
                if marker == 'None': marker = None
                handle = Line2D([0], [0], color=entry['color_var'].get(), linestyle=ls, marker=marker)
                legend_handles.append(handle)
                legend_labels.append(entry['text_var'].get())
            if legend_handles:
                ax.legend(handles=legend_handles, labels=legend_labels, loc=plot_widget['legend_pos_var'].get())
        else:
            ax.set_title("Select a data file and axes")
        ax.grid(True)
        plot_widget['canvas'].draw()

if __name__ == "__main__":
    app = PlottingApp()
    app.mainloop()