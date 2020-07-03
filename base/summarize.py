#!/usr/bin/python3
import csv, re
import sys
import traceback

from operator import attrgetter
from openpyxl import Workbook
from openpyxl import load_workbook
from capelib import succinctify
from capelib import calculate_all_rate_and_counts
from capelib import getter
from capelib import calculate_energy_derived_metrics
from collections import OrderedDict

from argparse import ArgumentParser
from enum import Enum
import tempfile
import math
import os
import pandas as pd
import warnings

# At least Python version 3.6 is required
assert sys.version_info >= (3,6)

args = None
variants = {}
short_names = {}
field_names = [ 'Name', 'Short Name', 'Variant', 'Num. Cores','DataSet/Size','prefetchers','Repetitions', 'VecType[Ops]', 'Time (s)',
                'O=Inst. Count (GI)', 'C=Inst. Rate (GI/s)',
                'Total PKG Energy (J)', 'Total PKG Power (W)',
                'E[PKG]/O (J/GI)', 'C/E[PKG] (GI/Js)', 'CO/E[PKG] (GI2/Js)',
                'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                'E[DRAM]/O (J/GI)', 'C/E[DRAM] (GI/Js)', 'CO/E[DRAM] (GI2/Js)',
                'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                'E[PKG+DRAM]/O (J/GI)', 'C/E[PKG+DRAM] (GI/Js)', 'CO/E[PKG+DRAM] (GI2/Js)',
                '%Misp. Branches', 'Executed/Retired Uops',
                'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
                'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GI/s)',
                'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)', '%Ops[Vec]', '%Inst[Vec]', '%Ops[FMA]','%Inst[FMA]',
                '%Ops[DIV]', '%Inst[DIV]', '%Ops[SQRT]', '%Inst[SQRT]', '%Ops[RSQRT]', '%Inst[RSQRT]', '%Ops[RCP]', '%Inst[RCP]',
                '%PRF','%SB','%PRF','%RS','%LB','%ROB','%LM','%ANY','%FrontEnd', 'AppTime (s)', '%Coverage', 'Color' ]


L2R_TrafficDict={'SKL': ['L1D_REPLACEMENT'], 'HSW': ['L1D_REPLACEMENT'], 'IVB': ['L1D_REPLACEMENT'], 'SNB': ['L1D_REPLACEMENT'] }
L2W_TrafficDict={'SKL': ['L2_TRANS_L1D_WB'], 'HSW': ['L2_TRANS_L1D_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L1D_WB_RQST_ALL'], 'SNB': ['L1D_WB_RQST_ALL'] }
L3R_TrafficDict={'SKL': ['L2_RQSTS_MISS'], 'HSW': ['L2_RQSTS_MISS', 'SQ_MISC_FILL_DROPPED'], 'IVB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'], 'SNB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'] }
L3W_TrafficDict={'SKL': ['L2_TRANS_L2_WB'], 'HSW': ['L2_TRANS_L2_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS'], 'SNB':  ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS']}

StallDict={'SKL': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_PHT_FULL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'HSW': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'IVB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'SNB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS2_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' }}

LFBFields = ['%lfb:k{}'.format(i) for i in range(0,11)]
field_names = field_names + LFBFields

def counter_sum(row, cols):
    sum = 0
    for col in cols:
        sum = sum + getter(row, col)
    return sum

def arch_helper(row):
    arch = row['cpu.generation'].lower()
    if 'skylake' in arch:
        return 'SKL'
    elif 'haswell' in arch:
        return 'HSW'
    elif 'ivy' in arch:
        return 'IVB'
    elif 'sandy' in arch:
        return 'SNB'
    else:
        return None


def calculate_codelet_name(out_row, in_row):
    out_row['Name'] = '{0}: {1}'.format(
        getter(in_row, 'application.name', type=str),
        getter(in_row, 'codelet.name', type=str))
    if out_row['Name'] in short_names:
        out_row['Short Name'] = short_names[out_row['Name']]
    else:
        out_row['Short Name'] = out_row['Name'] # Short Name is default set to actual name
    out_row['Variant'] = variants[out_row['Name']] if out_row['Name'] in variants \
        else getter(in_row, 'decan_variant.name', type=str)

def calculate_expr_settings(out_row, in_row):
    out_row['Num. Cores']=getter(in_row, 'decan_experimental_configuration.num_core')
    out_row['DataSet/Size']=getter(in_row, 'decan_experimental_configuration.data_size', type=str)
    try:
        out_row['prefetchers']=getter(in_row, 'prefetchers')
    except:
        out_row['prefetchers']='unknown'
    try:
        out_row['Repetitions']=getter(in_row, 'Repetitions')
    except:        
        out_row['Repetitions']=1

def calculate_iterations_per_rep(in_row):
    try:
        return getter(in_row, 'Iterations') / getter(in_row, 'Repetitions')
    except:
        # For Oneview there is no Repetitions just return Iterations
        return getter(in_row, 'Iterations') 

def print_iterations_per_rep_formula(formula_file):
    formula_file.write('iterations_per_rep = Iterations / Repetitions\n')

def calculate_time(out_row, in_row, iterations_per_rep, use_cpi):
    if use_cpi:
        time = getter(in_row, 'CPI')
    else:
        time = getter(in_row, 'CPU_CLK_UNHALTED_REF_TSC') / getter(in_row, 'decan_experimental_configuration.num_core')
    out_row['Time (s)'] = time * iterations_per_rep/(getter(in_row, 'cpu.nominal_frequency', 'decan_experimental_configuration.frequency') * 1e3)
    return out_row['Time (s)']

def print_time_formula(formula_file):
    formula_file.write('Time (s) = (CPU_CLK_UNHALTED_THREAD * iterations_per_rep) /' +
                                         ' (decan_experimental_configuration.frequency * 1E3)\n')



def print_total_pkg_energy_formula(formula_file):
    formula_file.write('Total PKG Energy (J) = (UNC_PKG_ENERGY_STATUS or FREERUN_PKG_ENERGY_STATUS) * energy.unit *' +
                       ' iterations_per_rep\n')

def print_total_dram_energy_formula(formula_file):
    formula_file.write('Total DRAM Energy (J) = (UNC_DDR_ENERGY_STATUS or FREERUN_DRAM_ENERGY_STATUS) * energy.unit *' +
                                         ' iterations_per_rep\n')

def user_op_to_rate_column_name(user_op_column):
    matchobj = re.search(r'(.+?) \((.+?)\)', user_op_column)
    op_name=matchobj.group(1)
    unit_name=matchobj.group(2)
    return "{} Rate (G{}/s)".format(op_name, unit_name)
        
    
def calculate_user_op_rate(out_row, in_row, time_per_rep, user_op_column_name_dict):
    for user_op_column, rate_column_name in user_op_column_name_dict.items():
        ops_per_rep = in_row[user_op_column]
        out_row[rate_column_name]=ops_per_rep/time_per_rep/1e9




def calculate_num_insts(out_row, in_row, iterations_per_rep, time):
    insts_per_rep = ((getter(in_row, 'INST_RETIRED_ANY') * iterations_per_rep) / (1e9))
    out_row['O=Inst. Count (GI)'] = insts_per_rep
    ops_per_sec = insts_per_rep / time
    out_row['C=Inst. Rate (GI/s)'] = ops_per_sec

    calculate_all_rate_and_counts(out_row, in_row, iterations_per_rep, time)
    return (insts_per_rep, ops_per_sec)

def print_num_ops_formula(formula_file):
    formula_file.write( \
        'Inst. Count(GI) = (INST_RETIRED_ANY * iterations_per_rep) / 1E9\n')


def calculate_data_rates(out_row, in_row, iterations_per_rep, time_per_rep):

    def calculate_load_store_rate():
        try:
            load_per_it  = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
            store_per_it = getter(in_row, 'MEM_INST_RETIRED_ALL_STORES', 'MEM_UOPS_RETIRED_ALL_STORES')
        except:
            load_per_it  = in_row['Nb_8_bits_loads'] + in_row['Nb_16_bits_loads'] \
                           + in_row['Nb_32_bits_loads'] + in_row['Nb_64_bits_loads'] + in_row['Nb_128_bits_loads'] \
                           + in_row['Nb_256_bits_loads'] + in_row['Nb_MOVH_LPS_D_loads']
            store_per_it = in_row['Nb_8_bits_stores'] + in_row['Nb_16_bits_stores'] \
                           + in_row['Nb_32_bits_stores'] + in_row['Nb_64_bits_stores'] + in_row['Nb_128_bits_stores'] \
                           + in_row['Nb_256_bits_stores'] + in_row['Nb_MOVH_LPS_D_stores']
        return ((load_per_it + store_per_it) * iterations_per_rep) / (1E9 * time_per_rep)

    def calculate_register_bandwidth():
        num_cores = getter(in_row, 'decan_experimental_configuration.num_core')
        reg_gp_addr_rw = getter(in_row, 'Bytes_GP_addr_read') \
            + getter(in_row, 'Bytes_GP_addr_write')
        reg_gp_data_rw = getter(in_row, 'Bytes_GP_data_read') \
            + getter(in_row, 'Bytes_GP_data_write')
        reg_simd_rw = getter(in_row, 'Bytes_SIMD_read') + getter(in_row, 'Bytes_SIMD_write')
        rates = [ num_cores * iterations_per_rep * x / (1E9 * time_per_rep) \
            for x in [ reg_gp_addr_rw, reg_gp_data_rw, reg_simd_rw ]]
        return rates + [ sum(rates) ]
    def get_dram_traffic_per_it(in_row, cas_count_name, alt_cas_count_sum_name):
        count = 0
        try:
            count = getter(in_row, cas_count_name, alt_cas_count_sum_name)
        except:
            # If it fails (happens to Oneview data), try to look at individual channel counts
            per_channel_cas_cnt_names = [n for n in list(in_row.keys()) \
                if n.startswith(cas_count_name+"_")]
            for name in per_channel_cas_cnt_names:
                count += getter(in_row, name)
        return count

    try:
        arch = arch_helper(in_row)

        L2_rc_per_it = counter_sum(in_row, L2R_TrafficDict[arch])
        L2_wc_per_it = counter_sum(in_row, L2W_TrafficDict[arch])
        L3_rc_per_it = counter_sum(in_row, L3R_TrafficDict[arch])
        L3_wc_per_it = counter_sum(in_row, L3W_TrafficDict[arch])

        ram_rc_per_it = get_dram_traffic_per_it(in_row, \
            'UNC_M_CAS_COUNT_RD', 'UNC_IMC_DRAM_DATA_READS')
        ram_wc_per_it = get_dram_traffic_per_it(in_row, \
            'UNC_M_CAS_COUNT_WR', 'UNC_IMC_DRAM_DATA_WRITES')

        L2_rwb_per_it  = (L2_rc_per_it  + L2_wc_per_it) * 64
        L3_rwb_per_it  = (L3_rc_per_it  + L3_wc_per_it) * 64
        ram_rwb_per_it = (ram_rc_per_it + ram_wc_per_it) * 64

        out_row['L2 Rate (GB/s)']  = (L2_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['L3 Rate (GB/s)']  = (L3_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['RAM Rate (GB/s)'] = (ram_rwb_per_it * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['Load+Store Rate (GI/S)'] = calculate_load_store_rate()
    except:
        pass

    try:
        L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_wb_per_it  = getter(in_row, 'Bytes_stored') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_rwb_per_it  = (L1_rb_per_it  + L1_wb_per_it)
        out_row['L1 Rate (GB/s)']  = (L1_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    except:
        # This is just estimation an load if fetching 8B (64 bit)
        warnings.warn("No CQA L1 metrics, use LS instruction rate instead.")
        out_row['L1 Rate (GB/s)']  = out_row['Load+Store Rate (GI/S)'] * 8

    
    try:
        out_row['Register ADDR Rate (GB/s)'], out_row['Register DATA Rate (GB/s)'], \
        out_row['Register SIMD Rate (GB/s)'], out_row['Register Rate (GB/s)'] = calculate_register_bandwidth()
    except:
        pass




    


# def shorten_stall_counter(field):
#     if field == 'RESOURCE_STALLS2_ALL_PRF_CONTROL':
#         return '%PRF'
#     field = field[(len('RESOURCE_STALLS') + 1):]
#     if field == '_ALL_PRF_CONTROL':
#         return '%PRF'
#     elif field == '_PHT_FULL':
#         return '%PHT'
#     elif field == 'LOAD_MATRIX':
#         return '%LM'
#     else:
#         return '%' + field.upper()

def calculate_stall_percentages(res, row, skip_stalls):
    if skip_stalls:
        return
    try:
        arch = arch_helper(row)
        unhlt = getter(row, 'CPU_CLK_UNHALTED_THREAD')
        for buf in ['RS', 'LB', 'SB', 'ROB', 'PRF', 'LM']:
            res['%'+buf] = getter(row, StallDict[arch][buf]) / unhlt
        try:
            res['%FrontEnd'] = getter(row, StallDict[arch]['FrontEnd']) / unhlt
        except:
            warnings.warn("No CQA FrontEnd metrics, use unhlt - ANY instead.")
            res['%FrontEnd'] = (unhlt - getter(row, StallDict[arch]['ANY'])) / unhlt
            
    except:
        pass

def calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec, skip_energy):
    if skip_energy:
        return
    def calculate_from_counter(counter, alt_counter):
        energy = getter(in_row, counter, alt_counter, default=None)
        return (energy * getter(in_row, 'energy.unit') * iterations_per_rep)

    def calculate_total_pkg_energy():
        return calculate_from_counter('UNC_PKG_ENERGY_STATUS', 'FREERUN_PKG_ENERGY_STATUS')
    def calculate_total_dram_energy():
        return calculate_from_counter('UNC_DDR_ENERGY_STATUS', 'FREERUN_DRAM_ENERGY_STATUS')

    def calculate_derived_metrics(kind, energy):
        out_row['Total {} Energy (J)'.format(kind)] = energy
        out_row['Total {} Power (W)'.format(kind)] = energy / time
        calculate_energy_derived_metrics(out_row, kind, energy, num_ops, ops_per_sec)

    # Can extend to report PP0, PP1 but ignore for now.
    total_pkg_energy = calculate_total_pkg_energy()
    calculate_derived_metrics('PKG', total_pkg_energy)

    try:
        total_dram_energy = calculate_total_dram_energy()
        calculate_derived_metrics('DRAM', total_dram_energy)
    except:
        return

    total_energy = total_pkg_energy + total_dram_energy
    calculate_derived_metrics('PKG+DRAM', total_energy)

def calculate_speculation_ratios(out_row, in_row):
    try:
        out_row['%Misp. Branches']=getter(in_row, 'BR_MISP_RETIRED_ALL_BRANCHES') / getter(in_row, 'BR_INST_RETIRED_ALL_BRANCHES')
    except:
        pass
    try:
        out_row['Executed/Retired Uops']=getter(in_row, 'UOPS_EXECUTED_CORE', 'UOPS_EXECUTED_THREAD') / getter(in_row, 'UOPS_RETIRED_ALL')
    except:
        return

def calculate_lfb_histogram(out_row, row, enable_lfb):
    if not enable_lfb:
        return
    try:
        clk = "CPU_CLK_UNHALTED_THREAD"
        fmt = "L1D_PEND_MISS_PENDING:c%s"
        ofmt = "%%lfb:k%d"
        prv = clk
        for x in range(1,11): 
            i = ("0x%x" if x > 9 else "%x") % x 
            cnt = fmt % i
            out_row[ofmt % (x-1)] = max(0, getter(row, prv) - getter(row, cnt)) / getter(row, clk)
            prv = cnt
        out_row[ofmt % x] = getter(row, prv) / getter(row, clk)
    except:
        pass

def calculate_app_time_coverage(out_rows, in_rows):
    in_cols = in_rows.columns
    if 'Time(Second)' in in_cols:
        out_rows['AppTime (s)']=in_rows['Time(Second)']
    else:
        # Just use codelet time if no App time provided from measurement (e.g. CapeScripts measurements)
        out_rows['AppTime (s)']=in_rows['Time (s)']
    if 'Coverage(Percent)' in in_cols:
        # Coverage info provide, go ahead to use it
        out_rows['%Coverage']=in_rows['Coverage(Percent)']/100
    else:
        # No coverage info provided, try to compute using AppTime
        totalAppTime = sum(out_rows['AppTime (s)'])
        out_rows['%Coverage']=in_rows['AppTime (s)']/totalAppTime

def build_row_output(in_row, user_op_column_name_dict, use_cpi, skip_energy, \
        skip_stalls, succinct, enable_lfb):
    out_row = {}
    calculate_codelet_name(out_row, in_row)
    calculate_expr_settings(out_row, in_row)
    iterations_per_rep = calculate_iterations_per_rep(in_row)
    time = calculate_time(out_row, in_row, iterations_per_rep, use_cpi)
    try:
        num_ops, ops_per_sec = calculate_num_insts(out_row, in_row, iterations_per_rep, time)
    except:
        num_ops, ops_per_sec = None, None
    calculate_user_op_rate(out_row, in_row, time, user_op_column_name_dict)
    calculate_speculation_ratios (out_row, in_row)
    calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec, skip_energy)
    calculate_data_rates(out_row, in_row, iterations_per_rep, time)
    calculate_stall_percentages(out_row, in_row, skip_stalls)

    calculate_lfb_histogram(out_row, in_row, enable_lfb)
    if succinct:
        out_row = { succinctify(k): v for k, v in out_row.items() }
    return out_row

def print_formulas(formula_file):
    print_iterations_per_rep_formula(formula_file)
    print_time_formula(formula_file)
    print_num_ops_formula(formula_file)
    formula_file.write('C=Inst. Rate (GI/s) = Inst. Count(GI) / Time(s)\n')
    print_total_pkg_energy_formula(formula_file)
    formula_file.write('Total PKG Power(W) = Total PKG Energy (J)/ Time(s)\n')
    formula_file.write('E[PKG]/O (J/GI) = Total PKG Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[PKG] (GI/Js) = Inst. Rate (GI/s) / Total PKG Energy(J)\n')
    formula_file.write('CO/E[PKG] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total PKG Energy(J)\n')
    print_total_dram_energy_formula(formula_file)
    formula_file.write('Total DRAM Power(W) = Total DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E[DRAM]/O (J/GI) = Total DRAM Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[DRAM] (GI/Js) = Inst. Rate (GI/s) / Total DRAM Energy(J)\n')
    formula_file.write('CO/E[DRAM] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total DRAM Energy(J)\n')
    formula_file.write('Total PKG+DRAM Energy (J) = Total PKG Energy (J) + Total DRAM Energy (J)\n')
    formula_file.write('Total PKG+DRAM Power(W) = Total PKG+DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E[PKG+DRAM]/O (J/GI) = Total PKG+DRAM Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[PKG+DRAM] (GI/Js) = Inst. Rate (GI/s) / Total PKG+DRAM Energy(J)\n')
    formula_file.write('CO/E[PKG+DRAM] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total PKG+DRAM Energy(J)\n')

def field_has_values(rows):
    def tmp_(field):
        return not all(field not in row for row in rows)
    return tmp_

def enforce(d, field_names):
    return { x : d.get(x, None) for x in field_names }

def unify_column_names(colnames):
    return colnames.map(lambda x: x.replace('ADD/SUB','ADD_SUB'))
    
def summary_report(inputfiles, outputfile, input_format, user_op_file, no_cqa, use_cpi, skip_energy,
                   skip_stalls, succinct, short_names_path, enable_lfb=False):
    print('Inputfile Format: ', input_format, file=sys.stderr)
    print('Inputfiles: ', inputfiles, file=sys.stderr)
    print('Outputfile: ', outputfile, file=sys.stderr)
    print('User Op file: ', user_op_file, file=sys.stderr)
    print('Short Names File: ', short_names_path, file=sys.stderr)
    print('Skip Energy: ', skip_energy, file=sys.stderr)
    print('Enable LFB: ', enable_lfb, file=sys.stderr)

    if short_names_path:
        read_short_names(short_names_path)

    # Each file has a different color associated with it (Current max of 4 files plotted together)
    colors = ['blue', 'red', 'green', 'yellow']
    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for index, inputfile in enumerate(inputfiles):
        print(inputfile, file=sys.stderr)
        if (input_format[index] == 'csv'):
            input_data_source = sys.stdin if (inputfile == '-') else inputfile
            cur_df = pd.read_csv(input_data_source, delimiter=',')
        else:
            # Very subtle differnce between read_csv and read_excel about input files so need to call read() for stdin
            input_data_source = sys.stdin.buffer.read() if (inputfile == '-') else inputfile
            cur_df = pd.read_excel(input_data_source, sheet_name='QPROF_full')
        cur_df['Color'] = colors[index]
        df = df.append(cur_df, ignore_index=True)

    df = df.sort_values(by=['codelet.name', 'decan_experimental_configuration.data_size', 'decan_experimental_configuration.num_core'])

    if user_op_file:
        key_columns=['codelet.name', 'decan_experimental_configuration.data_size']
        user_op_df = pd.read_csv(user_op_file, delimiter=',')
        user_op_columns = [col for col in user_op_df.columns if col not in key_columns]
        df = pd.merge(df, user_op_df, on=key_columns, how='left')
    else:
        user_op_columns = []

    user_op_col_name_dict={op_name: user_op_to_rate_column_name(op_name) for op_name in user_op_columns}
    field_names.extend(user_op_col_name_dict.values())

    df.columns = unify_column_names(df.columns)


    # Remove CQA columns if needed
    if no_cqa:
        script_dir=os.path.dirname(os.path.realpath(__file__))
        cqa_metric_file=os.path.join(script_dir, 'metrics_data','STAN')
        with open(cqa_metric_file) as f:
            cqa_metrics = f.read().splitlines()
            # Ignore error if extra CQA metrics in metrics_data/STAN
            df = df.drop(columns=cqa_metrics, errors='ignore')
        
    output_rows = pd.DataFrame(list(df.apply(build_row_output, user_op_column_name_dict=user_op_col_name_dict, \
                use_cpi=use_cpi, axis=1, skip_energy=skip_energy, \
                skip_stalls=skip_stalls, succinct=succinct, enable_lfb=enable_lfb)))

    # Compute App Time and Coverage.  Need to do it here after build_row_output() computed Codelet Time
    # For CapeScript runs, will add up Codelet Time and consider it AppTime.
    
    calculate_app_time_coverage(output_rows, df)
    # Set Corresponding color for each codelet
    df['Name'] = df['application.name'] + ': ' + df['codelet.name']
    color_df = df[['Name', 'Color']]
    output_rows = pd.merge(output_rows, color_df, how='inner', on='Name')

    outputfile = sys.stdout if outputfile == '-' else outputfile
    output_rows.columns = list(map(succinctify, output_rows.columns)) if succinct else output_rows.columns

    output_rows.to_csv(outputfile, index=False)

    # if (outputfile == '-'):
    #     output_csvfile = sys.stdout
    # else:
    #     output_csvfile = open (outputfile, 'w', newline='')

    # output_fields = succinctify(field_names) if succinct else field_names

    # output_fields = list(filter(field_has_values(output_rows), output_fields))
    # csvwriter = csv.DictWriter(output_csvfile, fieldnames=output_fields)
    # csvwriter.writeheader()
    # for output_row in output_rows:
    #     csvwriter.writerow(enforce(output_row, output_fields))
    # if (outputfile != '-'):
    #     output_csvfile.close()

def summary_formulas(formula_file_name):
    with open (formula_file_name, 'w') as formula_file:
        print_formulas(formula_file)

def read_short_names(filename):
    with open(filename, 'r', encoding='utf-8-sig') as infile:
        rows = list(csv.DictReader(infile, delimiter=','))
        for row in rows:
            if 'short_name' in row:
                short_names[row['name']] = row['short_name']
            if 'variant' in row:
                variants[row['name']] = row['variant']

if __name__ == '__main__':
    parser = ArgumentParser(description='Generate summary sheets from raw CAPE data.')
    parser.add_argument('-i', nargs='+', help='the input csv file', required=True, dest='in_files')
    parser.add_argument('-f', nargs='?', default='csv', help='format of input file (default csv can change to xlsx)', choices=['csv', 'xlsx'], dest='in_file_format')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
    parser.add_argument('-u', nargs='?', help='a user-defined operation count csv file', dest='user_op_file')
    parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
    parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
    parser.add_argument('--succinct', action='store_true', help='generate underscored, lowercase column names')
    parser.add_argument('--no-cqa', action='store_true', help='ignore CQA metrics in raw data')
    parser.add_argument('--use-cpi', action='store_true', help='use CPI metrics to compute time')
    parser.add_argument('--enable-lfb', action='store_true', help='include lfb counters in the output', dest='enable_lfb')
    args = parser.parse_args()


    summary_report(args.in_files, args.out_file, args.in_file_format, args.user_op_file, args.no_cqa, args.use_cpi, args.skip_energy, args.skip_stalls,
                   args.succinct, args.name_file, args.enable_lfb)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
