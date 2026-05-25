import os


def create_run_batch(folder_path, file_suffix='.dat', batch_title='multall_run', batch_filename='run_multall_files.bat', exclude_files=None, results_dir=None):
    if exclude_files is None:
        exclude_files = []

    try:
        filenames = [f for f in os.listdir(folder_path) if f.endswith(file_suffix)]
    except FileNotFoundError:
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    filenames = [f for f in filenames if f not in exclude_files]
    if not filenames:
        return 0

    filenames.sort()

    if results_dir:
        abs_results = os.path.abspath(results_dir)
        os.makedirs(abs_results, exist_ok=True)
        rel_results = os.path.relpath(abs_results, os.path.abspath(folder_path))
    else:
        rel_results = '.'

    batch_lines = [
        '@echo off',
        f'@title {batch_title}',
        '@rem Automatically generated batch script',
        ''
    ]

    for fname in filenames:
        base_name = os.path.splitext(fname)[0]
        if rel_results != '.':
            out_dir = f'"{rel_results}"'
            copy_flow_out = f'copy flow_out     {out_dir}\\flow_out-{base_name}.csv'
            copy_data_out = f'copy data_out.csv {out_dir}\\data_out-{base_name}.csv'
            copy_flow_avr = f'copy flow_avr.tec {out_dir}\\flow_avr-{base_name}.tec'
            copy_global   = f'copy global.dat     {out_dir}\\global-{base_name}.csv'
        else:
            copy_flow_out = f'copy flow_out     flow_out-{base_name}.csv'
            copy_data_out = f'copy data_out.csv data_out-{base_name}.csv'
            copy_flow_avr = f'copy flow_avr.tec flow_avr-{base_name}.tec'
            copy_global   = f'copy global.dat     global-{base_name}.csv'
        block = f"""
multall.exe<            {fname}
multall2py.exe<run2py.dat
{copy_flow_out}
cd Output
{copy_data_out}
{copy_flow_avr}
{copy_global}
cd ..
"""
        batch_lines.append(block)

    full_output_path = os.path.join(folder_path, batch_filename)
    with open(full_output_path, 'w') as f:
        f.write('\n'.join(batch_lines))

    return len(filenames)
