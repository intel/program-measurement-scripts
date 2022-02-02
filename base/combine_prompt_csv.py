#!/usr/bin/python3
# Combine PrOMPT metrics from par_region.csv which may contain measurements from multiple
# parallel regions in the same measurement function.
#
# 1) Timing measurement (*_sum): add them up
# 2) Timing measurement (*_min): take the min
# 3) Timing measurement (*_max): take the max
# 4) Parallel overhead: Recompute using aggregated time and following formula (from PrOMPT README)
#    - parallelism_overhead: (100 * 'sync_time_sum') / ('time_sum' * 'requested_parallelism')
# 5) Added/Rename metric wall_time_sum: use the time_sum metrics of first row of par_regions.csv
# Also will check whether requested_parallelism and nb_instances are the same.
# - will refuse to generate output if not true, so CapeScripts will consider this as no output.
# Below is a sample of par_region.csv
#
# module_name_offset	parent_reg_module_name_offset	level	ancestor_thread_num	invoker	parallel_or_teams	requested_parallelism	sync_time_sum	wait_time_sum	parallelism_overhead	time_sum	time_min	time_max	nb_instances	fct_name	src_file_line
#ALL										1.216692					
#/host/localdisk/cwong29/working/tmp/tmp/compiler-evaluation-experiments/LoopGen/matmul-var-data/matmul-var-data.c/matmul-var-data.c_de/cls_res_fxhaswell-server_1643827694_1643827566/build/wrapper:0x40137d	NA	0	0	runtime	parallel	4	0.557261624	0.469827878	29.477169	0.472621396	0.00000168	0.000166498	250000	core	/host/localdisk/cwong29/working/tmp/tmp/compiler-evaluation-experiments/LoopGen/matmul-var-data/matmul-var-data.c/matmul-var-data.c_de/cls_res_fxhaswell-server_1643827694_1643827566/build/core.c:16
#/host/localdisk/cwong29/working/tmp/tmp/compiler-evaluation-experiments/LoopGen/matmul-var-data/matmul-var-data.c/matmul-var-data.c_de/cls_res_fxhaswell-server_1643827694_1643827566/build/wrapper:0x401471	NA	0	0	runtime	parallel	4	0.548314994	0.456887622	28.963157	0.473286627	0.000001663	0.00015079	250000	core	/host/localdisk/cwong29/working/tmp/tmp/compiler-evaluation-experiments/LoopGen/matmul-var-data/matmul-var-data.c/matmul-var-data.c_de/cls_res_fxhaswell-server_1643827694_1643827566/build/core.c:24

import os
import warnings
import pandas as pd
from argparse import ArgumentTypeError
from argparse import ArgumentParser

def combine_prompt_data(in_file, out_file, fn_name):
    in_prompt_df = pd.read_csv(in_file, delimiter=',')
    # Get the time_sum of row "ALL".
    # TODO: Check with UVSQ team about multiple ALL w.r.t. different functions as currently this defintion implies ALL 
    #       will include wall time other than measurement function.
    wall_time = in_prompt_df.loc[in_prompt_df['module_name_offset'] == 'ALL', 'time_sum'].item()
    prompt_for_fn_df = in_prompt_df[in_prompt_df['fct_name'] == fn_name]
    unique_values = prompt_for_fn_df.agg({ 'requested_parallelism': 'nunique', 'nb_instances': 'nunique'})
    if unique_values['requested_parallelism'] != 1.0 or unique_values['nb_instances'] != 1.0:
        # abort aggregations when parallelism and nb_instances are not consistent
        warnings.warn("Expecting constant requested_parallelism and nb_instances values but found varying.  Abort aggregation.")
        return
    # After the unique check, simply use 'min' to get the unique values of requested_paralleism and nb_instances
    agg_prompt_values = prompt_for_fn_df.agg({'sync_time_sum': 'sum', 'wait_time_sum': 'sum',
                                              'time_sum': 'sum', 'time_min': 'min', 'time_max': 'max',
                                              'requested_parallelism': 'min', 'nb_instances': 'min'})
    agg_prompt_values['parallelism_overhead'] = (100 * agg_prompt_values['sync_time_sum']) / (agg_prompt_values['time_sum'] * agg_prompt_values['requested_parallelism'])
    agg_prompt_df = pd.DataFrame([agg_prompt_values.drop(['nb_instances', 'requested_parallelism'])])
    agg_prompt_df.to_csv(out_file, index=False)

def check_file_ext(param):
    _, ext = os.path.splitext(param)
    if ext.lower() != '.csv':
        raise ArgumentTypeError('Only accept CSV file format')
    return param

if __name__ == '__main__':
    parser = ArgumentParser(description='Combine PrOMPT metrics for the same measurement function.')
    parser.add_argument('-i', nargs='?', help='the input csv file', required=True, dest='in_file', type=check_file_ext)
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file', type=check_file_ext)
    parser.add_argument('-n', nargs='?', help='the name of measurement function', dest='fn_name')
    args = parser.parse_args()
    combine_prompt_data(args.in_file, args.out_file, args.fn_name)