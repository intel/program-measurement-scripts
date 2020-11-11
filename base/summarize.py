#!/usr/bin/env python3
import csv, re
import sys
import traceback
from datetime import datetime

from operator import attrgetter
from openpyxl import Workbook
from openpyxl import load_workbook
from capelib import calculate_all_rate_and_counts
from capelib import getter
from capelib import calculate_energy_derived_metrics
from capelib import add_mem_max_level_columns
from capelib import compute_speedup
from collections import OrderedDict

from argparse import ArgumentParser
from enum import Enum
import tempfile
import math
import os
import pandas as pd
import warnings

from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

# At least Python version 3.6 is required
assert sys.version_info >= (3,6)

args = None
variants = {}
short_names = {}
field_names = [  NAME, SHORT_NAME, VARIANT, NUM_CORES,DATA_SET,PREFETCHERS, REPETITIONS, COUNT_VEC_TYPE_OPS_PCT, TIME_LOOP_S, RECIP_TIME_LOOP_MHZ,
                COUNT_INSTS_GI, RATE_INST_GI_P_S,
                E_PKG_J, P_PKG_W,
                EPO_PKG_INST_J_P_GI, RPE_INST_PKG_GI_P_JS, ROPE_INST_PKG_GI2_P_JS,
                E_DRAM_J, P_DRAM_W,
                EPO_DRAM_INST_J_P_GI, RPE_INST_DRAM_GI_P_JS, ROPE_INST_DRAM_GI2_P_JS,
                E_PKGDRAM_J, P_PKGDRAM_W,
                EPO_PKGDRAM_INST_J_P_GI, RPE_INST_PKGDRAM_GI_P_JS, ROPE_INST_PKGDRAM_GI2_P_JS,
                BRANCHES_MISP_PCT, EXE_PER_RET_UOPS,
                RATE_REG_ADDR_GB_P_S, RATE_REG_DATA_GB_P_S, RATE_REG_SIMD_GB_P_S, RATE_REG_GB_P_S,
                RATE_L1_GB_P_S, RATE_L2_GB_P_S, RATE_L3_GB_P_S, RATE_RAM_GB_P_S, RATE_LDST_GI_P_S,
                RATE_FP_GFLOP_P_S, RATE_INT_GIOP_P_S, COUNT_OPS_VEC_PCT, COUNT_INSTS_VEC_PCT, COUNT_OPS_FMA_PCT,COUNT_INSTS_FMA_PCT,
                COUNT_OPS_DIV_PCT, COUNT_INSTS_DIV_PCT, COUNT_OPS_SQRT_PCT, COUNT_INSTS_SQRT_PCT, COUNT_OPS_RSQRT_PCT, COUNT_INSTS_RSQRT_PCT, COUNT_OPS_RCP_PCT, COUNT_INSTS_RCP_PCT,
                STALL_PRF_PCT, STALL_SB_PCT, STALL_RS_PCT, STALL_LB_PCT, STALL_ROB_PCT, STALL_LM_PCT, STALL_ANY_PCT, STALL_FE_PCT, TIME_APP_S, COVERAGE_PCT, SPEEDUP_VEC, SPEEDUP_DL1,
                ARRAY_EFFICIENCY_PCT ]


L2R_TrafficDict={'SKL': ['L1D_REPLACEMENT'], 'HSW': ['L1D_REPLACEMENT'], 'IVB': ['L1D_REPLACEMENT'], 'SNB': ['L1D_REPLACEMENT'] }
L2W_TrafficDict={'SKL': ['L2_TRANS_L1D_WB'], 'HSW': ['L2_TRANS_L1D_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L1D_WB_RQST_ALL'], 'SNB': ['L1D_WB_RQST_ALL'] }
L3R_TrafficDict={'SKL': ['L2_RQSTS_MISS'], 'HSW': ['L2_RQSTS_MISS', 'SQ_MISC_FILL_DROPPED'], 'IVB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'], 'SNB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'] }
L3W_TrafficDict={'SKL': ['L2_TRANS_L2_WB'], 'HSW': ['L2_TRANS_L2_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS'], 'SNB':  ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS']}

StallDict={'SKL': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_PHT_FULL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FE':'Front_end_(cycles)' },
           'HSW': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FE':'Front_end_(cycles)' },
           'IVB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FE':'Front_end_(cycles)' },
           'SNB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS2_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FE':'Front_end_(cycles)' }}

LFBFields = [MetricName.busyLfbPct(i) for i in range(0,11)]
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
    out_row[NAME] = '{0}: {1}'.format(
        getter(in_row, 'application.name', type=str),
        getter(in_row, 'codelet.name', type=str))
    name_key = (out_row[NAME], in_row[TIMESTAMP])
    name_key = name_key if name_key in short_names else out_row[NAME]
    # Short Name is default set to actual name
    out_row[SHORT_NAME] = short_names.get(name_key, out_row[NAME])
    default_variant = getter(in_row, 'decan_variant.name', type=str)
    default_variant = 'ORIG' if default_variant == 'ORG' else default_variant
    out_row[VARIANT] = variants.get(name_key, default_variant)        


def calculate_expr_settings(out_row, in_row):
    out_row[NUM_CORES]=getter(in_row, 'decan_experimental_configuration.num_core')
    out_row[DATA_SET]=getter(in_row, 'decan_experimental_configuration.data_size', type=str)
    try:
        out_row[PREFETCHERS]=getter(in_row, 'prefetchers')
    except:
        out_row[PREFETCHERS]='unknown'
    try:
        out_row[REPETITIONS]=getter(in_row, REPETITIONS)
    except:        
        out_row[REPETITIONS]=1

def calculate_iterations_per_rep(in_row):
    try:
        return getter(in_row, 'Iterations') / getter(in_row, REPETITIONS)
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
    time_s = time * iterations_per_rep/(getter(in_row, 'cpu.nominal_frequency', 'decan_experimental_configuration.frequency') * 1e3)
    out_row[TIME_LOOP_S] = time_s
    out_row[RECIP_TIME_LOOP_MHZ] = (1 / time_s) / 1e6 
    return out_row[TIME_LOOP_S]

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
    out_row[COUNT_INSTS_GI] = insts_per_rep
    ops_per_sec = insts_per_rep / time
    out_row[RATE_INST_GI_P_S] = ops_per_sec

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

        out_row[RATE_L2_GB_P_S]  = (L2_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row[RATE_L3_GB_P_S]  = (L3_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row[RATE_RAM_GB_P_S] = (ram_rwb_per_it * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['Load+Store Rate (GI/S)'] = calculate_load_store_rate()
    except:
        pass

    try:
        L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_wb_per_it  = getter(in_row, 'Bytes_stored') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_rwb_per_it  = (L1_rb_per_it  + L1_wb_per_it)
        out_row[RATE_L1_GB_P_S]  = (L1_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    except:
        # This is just estimation an load if fetching 8B (64 bit)
        warnings.warn("No CQA L1 metrics, use LS instruction rate instead.")
        out_row[RATE_L1_GB_P_S]  = out_row['Load+Store Rate (GI/S)'] * 8

    
    try:
        out_row[RATE_REG_ADDR_GB_P_S], out_row[RATE_REG_DATA_GB_P_S], \
        out_row[RATE_REG_SIMD_GB_P_S], out_row[RATE_REG_GB_P_S] = calculate_register_bandwidth()
    except:
        pass




    


# def shorten_stall_counter(field):
#     if field == 'RESOURCE_STALLS2_ALL_PRF_CONTROL':
#         return STALL_PRF_PCT
#     field = field[(len('RESOURCE_STALLS') + 1):]
#     if field == '_ALL_PRF_CONTROL':
#         return STALL_PRF_PCT
#     elif field == '_PHT_FULL':
#         return '%PHT'
#     elif field == 'LOAD_MATRIX':
#         return STALL_LM_PCT
#     else:
#         return '%' + field.upper()

def calculate_stall_percentages(res, row, skip_stalls):
    if skip_stalls:
        return
    try:
        arch = arch_helper(row)
        unhlt = getter(row, 'CPU_CLK_UNHALTED_THREAD')
        for buf in ['RS', 'LB', 'SB', 'ROB', 'PRF', 'LM', 'ANY']:
            res[MetricName.stallPct(buf)] = 100 * getter(row, StallDict[arch][buf]) / unhlt
        try:
            res[STALL_FE_PCT] = 100 * getter(row, StallDict[arch]['FE']) / unhlt
        except:
            warnings.warn("No CQA FrontEnd metrics, use unhlt - ANY instead.")
            res[STALL_FE_PCT] = 100 * (unhlt - getter(row, StallDict[arch]['ANY'])) / unhlt
            
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
        out_row[MetricName.energy(kind)] = energy
        out_row[MetricName.power(kind)] = energy / time
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
        out_row[BRANCHES_MISP_PCT] = 100 * getter(in_row, 'BR_MISP_RETIRED_ALL_BRANCHES') / getter(in_row, 'BR_INST_RETIRED_ALL_BRANCHES')
    except:
        pass
    try:
        out_row[EXE_PER_RET_UOPS] = getter(in_row, 'UOPS_EXECUTED_CORE', 'UOPS_EXECUTED_THREAD') / getter(in_row, 'UOPS_RETIRED_ALL')
    except:
        return

def calculate_lfb_histogram(out_row, row, enable_lfb):
    if not enable_lfb:
        return
    try:
        clk = "CPU_CLK_UNHALTED_THREAD"
        fmt = "L1D_PEND_MISS_PENDING:c%s"
        # ofmt = "%%lfb:k%d"
        prv = clk
        for x in range(1,11): 
            i = ("0x%x" if x > 9 else "%x") % x 
            cnt = fmt % i
            out_row[MetricName.busyLfbPct(x-1)] = 100 * max(0, getter(row, prv) - getter(row, cnt)) / getter(row, clk)
            prv = cnt
        out_row[MetricName.busyLfbPct(x)] = 100 * getter(row, prv) / getter(row, clk)
    except:
        pass

def calculate_array_efficiency(out_rows, in_rows):
    try:
        num_all_streams = in_rows['Nb_streams_stride_0'].values + in_rows['Nb_streams_stride_1'].values \
            + in_rows['Nb_streams_stride_n'].values + in_rows['Nb_streams_unknown_stride'].values + in_rows['Nb_streams_indirect'].values
        out_rows.loc[num_all_streams > 0, ARRAY_EFFICIENCY_PCT] = 100 * ( in_rows['Nb_streams_stride_0'].values + in_rows['Nb_streams_stride_1'].values \
            + 0.75 * in_rows['Nb_streams_stride_n'].values + 0.5 * in_rows['Nb_streams_unknown_stride'].values \
                + 0 * in_rows['Nb_streams_indirect'].values ) / num_all_streams[num_all_streams>0]
    except:
        pass

def calculate_app_time_coverage(out_rows, in_rows):
    in_cols = in_rows.columns
    # Note: need to use .values to be more robust and not index dependent
    if 'Time(Second)' in in_cols:
        out_rows[TIME_APP_S] = in_rows['Time(Second)'].values
    else:
        # Just use codelet time if no App time provided from measurement (e.g. CapeScripts measurements)
        out_rows[TIME_APP_S] = out_rows[TIME_LOOP_S].values
    if 'Coverage(Percent)' in in_cols:
        # Coverage info provide, go ahead to use it
        out_rows[COVERAGE_PCT] = in_rows['Coverage(Percent)'].values
    else:
        # No coverage info provided, try to compute using AppTime
        totalAppTime = sum(out_rows[TIME_APP_S].values)
        out_rows[COVERAGE_PCT] = 100 * out_rows[TIME_APP_S].values/totalAppTime

def add_trawl_data(out_rows, in_rows):
    # initialize to None and set to correct values
    out_rows[SPEEDUP_VEC] = None
    out_rows[SPEEDUP_DL1] = None
    try:
        out_rows[SPEEDUP_VEC] = in_rows['potential_speedup.if_fully_vectorized'].values
    except:
        if_fully_cycles = (in_rows['(L1)_Nb_cycles_if_fully_vectorized_min'].values + in_rows['(L1)_Nb_cycles_if_fully_vectorized_max'].values)/2
        dl1_cycles = (in_rows['(L1)_Nb_cycles_min'].values + in_rows['(L1)_Nb_cycles_max'].values)/2
        out_rows[SPEEDUP_VEC] = dl1_cycles / if_fully_cycles

    try:
        out_rows[SPEEDUP_DL1] = in_rows['time(ORIG) / time(DL1)'].values
    except:
        # Go ahead to use the dl1_cycles (assuming exception was thrown when computing what-if vectorization speedup)
        # use core cycles instead of ref or CPI so timing not affected by TurboBoost
        out_rows[SPEEDUP_DL1] = in_rows['CPU_CLK_UNHALTED_THREAD'].values / dl1_cycles

def build_row_output(in_row, user_op_column_name_dict, use_cpi, skip_energy, \
        skip_stalls, enable_lfb, incl_meta_data):
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
    if incl_meta_data:
        out_row[TIMESTAMP] = in_row['Timestamp#']
        out_row[SRC_NAME] = in_row['Source Name']
    return out_row

# TODO: Delete this as likely out of sync with updated metric names and formula calculation.
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

# moved to capelib.py
# def compute_speedup(output_rows, mapping_df):
#     keyColumns=[NAME, TIMESTAMP]
#     timeColumns=[TIME_LOOP_S, TIME_APP_S]
#     rateColumns=[RATE_FP_GFLOP_P_S]
#     perf_df = output_rows[keyColumns + timeColumns + rateColumns]

#     new_mapping_df = pd.merge(mapping_df, perf_df, left_on=['Before Name', 'Before Timestamp'], 
#                               right_on=keyColumns, how='left')
#     new_mapping_df = pd.merge(new_mapping_df, perf_df, left_on=['After Name', 'After Timestamp'], 
#                               right_on=keyColumns, suffixes=('_before', '_after'), how='left')
#     for timeColumn in timeColumns: 
#         new_mapping_df['Speedup[{}]'.format(timeColumn)] = \
#             new_mapping_df['{}_before'.format(timeColumn)] / new_mapping_df['{}_after'.format(timeColumn)]
#     for rateColumn in rateColumns: 
#         new_mapping_df['Speedup[{}]'.format(rateColumn)] = \
#             new_mapping_df['{}_after'.format(rateColumn)] / new_mapping_df['{}_before'.format(rateColumn)]
#     # Remove those _after and _before columns
#     retainColumns = filter(lambda a: not a.endswith('_after'), new_mapping_df.columns)
#     retainColumns = filter(lambda a: not a.endswith('_before'), list(retainColumns))
#     return new_mapping_df[retainColumns]
    
def summary_report_df(inputfiles, input_format, user_op_file, no_cqa, use_cpi, skip_energy,
                   skip_stalls, name_file, enable_lfb, incl_meta_data, mapping_df):
    if name_file:
        read_short_names(name_file)

    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for index, inputfile in enumerate(inputfiles):
        print(inputfile, file=sys.stderr)
        if (input_format[index] == 'csv'):
            input_data_source = sys.stdin if (inputfile == '-') else inputfile
            cur_df = pd.read_csv(input_data_source, delimiter=',')
            # For CapeScripts data, just use experiment timestamp as the time stamp
            cur_df['Timestamp#'] = cur_df['Expr TS#']
            cur_df['Source Name'] = None
        else:
            # Very subtle differnce between read_csv and read_excel about input files so need to call read() for stdin
            input_data_source = sys.stdin.buffer.read() if (inputfile == '-') else inputfile
            cur_df = pd.read_excel(input_data_source, sheet_name='QPROF_full')
            # For Oneview output, needs to read the 'Experiment_Summary' tab for Timestamp
            expr_summ_df = pd.read_excel(input_data_source, sheet_name='Experiment_Summary')
            ts_row = expr_summ_df[expr_summ_df.iloc[:,0]=='Timestamp']
            ts_string = ts_row.iloc[0,1]
            date_time_obj = datetime.strptime(ts_string, '%Y-%m-%d %H:%M:%S')
            cur_df['Timestamp#'] = int(date_time_obj.timestamp())
            cur_df['Source Name']=cur_df['code.name']

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
                skip_stalls=skip_stalls, enable_lfb=enable_lfb, incl_meta_data=incl_meta_data)))

    # Compute App Time and Coverage.  Need to do it here after build_row_output() computed Codelet Time
    # For CapeScript runs, will add up Codelet Time and consider it AppTime.
    node_list = [RATE_L1_GB_P_S, RATE_L2_GB_P_S, RATE_L3_GB_P_S, RATE_RAM_GB_P_S]
    #metric_to_memlevel = lambda v: re.sub(r" Rate \(.*\)", "", v)
    metric_to_memlevel = lambda v: v.extractComponent()
    add_mem_max_level_columns(output_rows, node_list, RATE_MAXMEM_GB_P_S, metric_to_memlevel)
    calculate_app_time_coverage(output_rows, df)
    calculate_array_efficiency(output_rows, df)
    # Add y-value data for TRAWL Plot
    add_trawl_data(output_rows, df)
    # Retain rows with non-empty performance measurments (provided by TIME_LOOP_S")
    output_rows = output_rows[~output_rows[TIME_LOOP_S].isnull()]
    new_mapping_df = mapping_df
    if mapping_df is not None and not mapping_df.empty:
        # Make sure Variant columns are in mapping_df
        if not 'Before Variant' in mapping_df.columns:
            mapping_df = pd.merge(mapping_df, output_rows[[NAME, TIMESTAMP, VARIANT]], \
                left_on=['Before Name', 'Before Timestamp'], right_on=[NAME, TIMESTAMP], \
                how='inner').drop(columns=[NAME, TIMESTAMP]).rename(columns={VARIANT:'Before Variant'})
        if not 'After Variant' in mapping_df.columns:
            mapping_df = pd.merge(mapping_df, output_rows[[NAME, TIMESTAMP, VARIANT]], \
                left_on=['After Name', 'After Timestamp'], right_on=[NAME, TIMESTAMP],  \
                how='inner').drop(columns=[NAME, TIMESTAMP]).rename(columns={VARIANT:'After Variant'})
        new_mapping_df = compute_speedup(output_rows, mapping_df)
    return output_rows, new_mapping_df


def summary_report(inputfiles, outputfile, input_format, user_op_file, no_cqa, use_cpi, skip_energy,
                   skip_stalls, name_file, enable_lfb=False, incl_meta_data=False, mapping_file=None):
    print('Inputfile Format: ', input_format, file=sys.stderr)
    print('Inputfiles: ', inputfiles, file=sys.stderr)
    print('Outputfile: ', outputfile, file=sys.stderr)
    print('User Op file: ', user_op_file, file=sys.stderr)
    print('Name file: ', name_file, file=sys.stderr)
    print('Mapping file: ', mapping_file, file=sys.stderr)
    print('Skip Energy: ', skip_energy, file=sys.stderr)
    print('Enable LFB: ', enable_lfb, file=sys.stderr)

    mapping_df = pd.read_csv(mapping_file, delimiter=',') if mapping_file is not None else None
    output_rows, new_mapping_df = summary_report_df(inputfiles, input_format, user_op_file, no_cqa, use_cpi, skip_energy, \
        skip_stalls, name_file, enable_lfb, incl_meta_data, mapping_df)

    outputfile = sys.stdout if outputfile == '-' else outputfile
    output_rows.to_csv(outputfile, index=False)

    if new_mapping_df is not None:
        outdir = os.path.dirname(outputfile)
        out_new_mapping_file = os.path.join(outdir, os.path.splitext(os.path.basename(mapping_file))[0]+'.speedup.csv')
        new_mapping_df.to_csv(out_new_mapping_file, index=False)
        

    # if (outputfile == '-'):
    #     output_csvfile = sys.stdout
    # else:
    #     output_csvfile = open (outputfile, 'w', newline='')

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
            name = getter(row, NAME, 'name', type=str)
            timestamp = int(row.get(TIMESTAMP, None))
            name_key = (name, timestamp) if timestamp is not None else name
            try:
                short_names[name_key] = getter(row, 'ShortName', SHORT_NAME, type=str)
            except:
                pass
            try:
                variants[name_key] = getter(row, 'variant', VARIANT, type=str)
            except:
                pass             

if __name__ == '__main__':
    parser = ArgumentParser(description='Generate summary sheets from raw CAPE data.')
    parser.add_argument('-i', nargs='+', help='the input csv file', required=True, dest='in_files')
    parser.add_argument('-f', nargs='?', default='csv', help='format of input file (default csv can change to xlsx)', choices=['csv', 'xlsx'], dest='in_file_format')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
    parser.add_argument('-u', nargs='?', help='a user-defined operation count csv file', dest='user_op_file')
    parser.add_argument('-m', nargs='?', help='the input mapping/transition csv file for speedup computation', dest='mapping_file')
    parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
    parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
    parser.add_argument('--no-cqa', action='store_true', help='ignore CQA metrics in raw data')
    parser.add_argument('--use-cpi', action='store_true', help='use CPI metrics to compute time')
    parser.add_argument('--enable-lfb', action='store_true', help='include lfb counters in the output', dest='enable_lfb')
    parser.add_argument('--enable-meta', action='store_true', help='include meta data in the output', dest='enable_meta')
    args = parser.parse_args()
    if (args.mapping_file is not None and not args.enable_meta):
        parser.error("The -m argument requires the --enable-meta argument")

    summary_report(args.in_files, args.out_file, [args.in_file_format] * len(args.in_files), args.user_op_file, args.no_cqa, args.use_cpi, args.skip_energy, args.skip_stalls,
                   args.name_file, args.enable_lfb, args.enable_meta, args.mapping_file)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
