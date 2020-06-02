#!/usr/bin/python3

import sys
import pandas as pd
from argparse import ArgumentParser

# Need to source advixe-vars.sh in shell
# More API info: {advisor_dir}/pythonapi/documentation
# Metric list: {advisor_dir}/pythonapi/examples/columns.txt
import advisor


def summary_report(input):    
    out = pd.DataFrame()
    numeric_in_cols=['thread_count', 'self_time', 'self_all_instructions', 'self_gflops', 'self_gintops', \
                     'self_vector_compute_with_memory', 'self_vector_compute', 'self_vector_memory', 'self_fma', \
                     'self_memory', 'self_loaded_gb', 'self_stored_gb', 'self_l2_loaded_gb','self_l2_stored_gb', \
                     'self_l3_loaded_gb', 'self_l3_stored_gb', 'self_dram_loaded_gb', 'self_dram_stored_gb']
    input[numeric_in_cols]=input[numeric_in_cols].apply(pd.to_numeric, errors='coerce', axis=1)
    out['Name']=input['source_location']
    out['Num. Cores']=input['thread_count']
    out['Time (s)']=input['self_time']
    time = out['Time (s)']
    instrs=input['self_all_instructions']
    out['O=Inst. Count (GI)']=instrs/1e9
    out['C=Inst. Rate (GI/s)']=out['O=Inst. Count (GI)']/time
    out['L1 Rate (GB/s)']=(input['self_loaded_gb'] + input['self_stored_gb'])/time
    out['L2 Rate (GB/s)']=(input['self_l2_loaded_gb'] + input['self_l2_stored_gb'])/time
    out['L3 Rate (GB/s)']=(input['self_l3_loaded_gb'] + input['self_l3_stored_gb'])/time
    out['RAM Rate (GB/s)']=(input['self_dram_loaded_gb'] + input['self_dram_stored_gb'])/time
    out['Load+Store Rate (GI/s)']=input['self_memory']/1e9/time
    out['FLOP Rate (GFLOP/s)']=input['self_gflops']
    out['IOP Rate (GIOP/s)']=input['self_gintops']
    # Does not have enough information to do Ops normalization
#    out['%Ops[Vec]']=0
    out['%Inst[Vec]']=(input['self_vector_compute']+input['self_vector_memory'])/instrs
#    out['%Ops[FMA]']=0
    out['%Inst[FMA]']=input['self_fma']/instrs

    return out


if __name__ == '__main__':
    parser = ArgumentParser(description='Generate summary sheets from Advisor data.')
    parser.add_argument('-i', nargs='+', help='the input csv file', required=True, dest='in_files')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
    parser.add_argument('-u', nargs='?', help='a user-defined operation count csv file', dest='user_op_file')
    parser.add_argument('--succinct', action='store_true', help='generate underscored, lowercase column names')
    args = parser.parse_args()


    out_df = pd.DataFrame()
    for proj in args.in_files:
        project = advisor.open_project(proj)
        survey = project.load(advisor.SURVEY)

        all_rows=(list(survey.bottomup))
        row0 = all_rows[0]
        keys=[ key for key in row0 ]
        dict={k:[v[k] for v in all_rows] for k in keys}
        df=pd.DataFrame.from_dict(dict)
        # df.to_csv('/tmp/test.csv')

        cur_out=summary_report(df)
        out_df = out_df.append(cur_out, ignore_index=True)
    print(out_df)

