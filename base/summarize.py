#!/usr/bin/python3
import csv, re
import sys
import traceback

from operator import attrgetter
from openpyxl import Workbook
from openpyxl import load_workbook
from capelib import succinctify
from collections import OrderedDict
from argparse import ArgumentParser
from enum import Enum
import tempfile
import os
import pandas as pd
import warnings

# At least Python version 3.6 is required
assert sys.version_info >= (3,6)

args = None
variants = {}
short_names = {}
field_names = [ 'Name', 'Short Name', 'Variant', 'Num. Cores','DataSet/Size','prefetchers','Repetitions', 'Vec. Type', 'Time (s)',
                'O=Inst. Count (GI)', 'C=Inst. Rate (GI/s)',
                'Total PKG Energy (J)', 'Total PKG Power (W)',
                'E[PKG]/O (J/GI)', 'C/E[PKG] (GI/Js)', 'CO/E[PKG] (GI2/Js)',
                'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                'E[DRAM]/O (J/GI)', 'C/E[DRAM] (GI/Js)', 'CO/E[DRAM] (GI2/Js)',
                'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                'E[PKG+DRAM]/O (J/GI)', 'C/E[PKG+DRAM] (GI/Js)', 'CO/E[PKG+DRAM] (GI2/Js)',
                '%Misp. Branches', 'Issued/Retired Uops',
                'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
                'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GI/s)',
                'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)',
                '%PRF','%SB','%PRF','%RS','%LB','%ROB','%LM','%ANY','%FrontEnd' ]

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

def find_vector_ext(row):
    def is_vt_insn(field, ext):
        return field.endswith(ext) and \
            (field.startswith("Nb_FP_insn") or field.startswith('Nb_insn'))
    xmm_vec = sum(getter(row, col) for col in row.keys() if is_vt_insn(col, 'XMM'))
    ymm_vec = sum(getter(row, col) for col in row.keys() if is_vt_insn(col, 'YMM'))
    zmm_vec = sum(getter(row, col) for col in row.keys() if is_vt_insn(col, 'ZMM'))
    fma_vec = getter(row, 'Nb_FLOP_fma') if 'Nb_FLOP_fma' in row.keys() else None
    # For conditons below, need to check against 0 explicitlty to handle nan's correctly
    if zmm_vec > 0:
        return 'AVX512'
    elif ymm_vec >0 and fma_vec > 0:
        return 'AVX2'
    elif ymm_vec > 0:
        return 'AVX'
    elif xmm_vec > 0:
        return 'SSE'
    else:
        return 'SC'



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
    out_row['Variant'] = variants[out_row['Name']] if out_row['Name'] in variants \
        else getter(in_row, 'decan_variant.name', type=str)

def calculate_expr_settings(out_row, in_row):
    out_row['Num. Cores']=getter(in_row, 'decan_experimental_configuration.num_core')
    out_row['DataSet/Size']=getter(in_row, 'decan_experimental_configuration.data_size', type=str)
    out_row['prefetchers']=getter(in_row, 'prefetchers')
    out_row['Repetitions']=getter(in_row, 'Repetitions')
    out_row['Vec. Type']=find_vector_ext(in_row)

def calculate_iterations_per_rep(in_row):
    try:
        return getter(in_row, 'Iterations') / getter(in_row, 'Repetitions')
    except:
        # For Oneview there is no Repetitions just return Iterations
        return getter(in_row, 'Iterations') 

def print_iterations_per_rep_formula(formula_file):
    formula_file.write('iterations_per_rep = Iterations / Repetitions\n')

def calculate_time(out_row, in_row, iterations_per_rep):
    time = ((getter(in_row, 'CPU_CLK_UNHALTED_REF_TSC') * iterations_per_rep) /
            (getter(in_row, 'cpu.nominal_frequency', 'decan_experimental_configuration.frequency') * 1e3 *
             getter(in_row, 'decan_experimental_configuration.num_core')))
    out_row['Time (s)'] = time
    return time

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

    try:
        out_row['FLOP Rate (GFLOP/s)'], flops_sc, flops_xmm, flops_ymm, flops_zmm = calculate_gflops(in_row, iterations_per_rep, time)
    except:
        pass

    try:
        out_row['IOP Rate (GIOP/s)'], iops_sc, iops_xmm, iops_ymm, iops_zmm = calculate_giops(in_row, iterations_per_rep, time)
    except:
        pass
    

    return (insts_per_rep, ops_per_sec)

def print_num_ops_formula(formula_file):
    formula_file.write( \
        'Inst. Count(GI) = (INST_RETIRED_ANY * iterations_per_rep) / 1E9\n')

def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            return type_(in_row[arg] if in_row[arg] else default_)
    raise IndexError(', '.join(map(str, argv)))

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
        reg_gp_addr_rw = getter(in_row, 'Bytes_GP_addr_read') + getter(in_row, 'Bytes_GP_addr_write')
        reg_gp_data_rw = getter(in_row, 'Bytes_GP_data_read') + getter(in_row, 'Bytes_GP_data_write')
        reg_simd_rw = getter(in_row, 'Bytes_SIMD_read') + getter(in_row, 'Bytes_SIMD_write')
        rates = [ num_cores * iterations_per_rep * x / (1E9 * time_per_rep) for x in [ \
                                                                                       reg_gp_addr_rw, reg_gp_data_rw, reg_simd_rw \
                                                                                   ]]
        return rates + [ sum(rates) ]

    try:
        arch = arch_helper(in_row)

        L2_rc_per_it  = counter_sum(in_row, L2R_TrafficDict[arch])
        L2_wc_per_it  = counter_sum(in_row, L2W_TrafficDict[arch])
        L3_rc_per_it  = counter_sum(in_row, L3R_TrafficDict[arch])
        L3_wc_per_it  = counter_sum(in_row, L3W_TrafficDict[arch])

        ram_rc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_RD', 'UNC_IMC_DRAM_DATA_READS')
        ram_wc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_WR', 'UNC_IMC_DRAM_DATA_WRITES')


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


def calculate_giops(in_row, iters_per_rep, time_per_rep):
    def calculate_iops(iops_per_instr, instr_template, itypes):
        ans = 0
        for itype in itypes:
            ans += (iops_per_instr * getter(in_row, instr_template.format(itype)))
        return ans
        
    iops = 0
    itypes = ['ADD_SUB', 'CMP', 'MUL' ]
    iops_sc = calculate_iops(0.5, 'Nb_scalar_INT_arith_insn_{}', itypes)
    iops_xmm = calculate_iops(2, 'Nb_INT_arith_insn_{}_XMM', itypes)
    iops_ymm = calculate_iops(4, 'Nb_INT_arith_insn_{}_YMM', itypes)
    iops_zmm = calculate_iops(8, 'Nb_INT_arith_insn_{}_ZMM', itypes)    
        

    itypes = ['AND', 'XOR', 'OR', 'SHIFT']
    iops_sc += calculate_iops(0.5, 'Nb_scalar_INT_logic_insn_{}', itypes)
    iops_xmm += calculate_iops(2, 'Nb_INT_logic_insn_{}_XMM', itypes)
    iops_ymm += calculate_iops(4, 'Nb_INT_logic_insn_{}_YMM', itypes)
    iops_zmm += calculate_iops(8, 'Nb_INT_logic_insn_{}_ZMM', itypes)    
    
    # try to add the TEST, ANDN, FMA and SAD counts (they have not scalar count)
    iops_xmm += (2 * getter(in_row, 'Nb_INT_logic_insn_ANDN_XMM') + 2 * getter(in_row, 'Nb_INT_logic_insn_TEST_XMM') + 4 * getter(in_row, 'Nb_INT_arith_insn_FMA_XMM'))
    iops_ymm += (4 * getter(in_row, 'Nb_INT_logic_insn_ANDN_YMM') + 4 * getter(in_row, 'Nb_INT_logic_insn_TEST_YMM') + 8 * getter(in_row, 'Nb_INT_arith_insn_FMA_YMM'))
    iops_zmm += (8 * getter(in_row, 'Nb_INT_logic_insn_ANDN_ZMM') + 8 * getter(in_row, 'Nb_INT_logic_insn_TEST_ZMM') + 16 * getter(in_row, 'Nb_INT_arith_insn_FMA_ZMM'))
    # For 128bit (XMM) SAD instructions, 1 instruction does
    # 1) 32 8-bit SUB
    # 2) 32 8-bit ABS
    # 3) 24 16-bit ADD
    # Ignoring 2), 1 XMM instruction generates/processes 32*8+24*16=640 bits = 10 DP element(64-bit)
    # Similar scaling, YMM = 20 DP, ZMM = 40DP
    iops_xmm += (10 * getter(in_row, 'Nb_INT_arith_insn_SAD_XMM'))
    iops_ymm += (20 * getter(in_row, 'Nb_INT_arith_insn_SAD_YMM'))
    iops_zmm += (40 * getter(in_row, 'Nb_INT_arith_insn_SAD_ZMM'))

    iops = iops_sc + iops_xmm + iops_ymm + iops_zmm
    return tuple((ops * getter(in_row, 'decan_experimental_configuration.num_core') * iters_per_rep) / (1E9 * time_per_rep)
                 for ops in [iops,iops_sc, iops_xmm, iops_ymm, iops_zmm])


def calculate_gflops(in_row, iters_per_rep, time_per_rep):
    def calculate_flops(flops_per_sp_inst, flops_per_dp_inst, sp_inst_template, dp_inst_template):
        itypes = ['ADD_SUB', 'DIV', 'MUL', 'SQRT', 'RSQRT', 'RCP']
        ans=0
        for itype in itypes:
            ans += (flops_per_sp_inst * getter(in_row, sp_inst_template.format(itype)) + flops_per_dp_inst * getter(in_row, dp_inst_template.format(itype)))
        return ans
        
    flops = 0

    try:
        # try to use counters if collected.  The count should already be across all cores.
        flops_sc = 0.5 * getter(in_row, 'FP_ARITH_INST_RETIRED_SCALAR_SINGLE') + 1 * getter(in_row, 'FP_ARITH_INST_RETIRED_SCALAR_DOUBLE') 
        flops_xmm = 2 * getter(in_row, 'FP_ARITH_INST_RETIRED_128B_PACKED_SINGLE') + 2 * getter(in_row, 'FP_ARITH_INST_RETIRED_128B_PACKED_DOUBLE')
        flops_ymm = 4 * getter(in_row, 'FP_ARITH_INST_RETIRED_256B_PACKED_SINGLE') + 4 * getter(in_row, 'FP_ARITH_INST_RETIRED_256B_PACKED_DOUBLE')
        flops_zmm = 8 * getter(in_row, 'FP_ARITH_INST_RETIRED_512B_PACKED_SINGLE') + 8 * getter(in_row, 'FP_ARITH_INST_RETIRED_512B_PACKED_DOUBLE')
        flops = flops_sc + flops_xmm + flops_ymm + flops_zmm
        results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm)
        
    except:
        flops_sc = calculate_flops(0.5, 1, 'Nb_FP_insn_{}SS', 'Nb_FP_insn_{}SD')
        flops_xmm = calculate_flops(2, 2, 'Nb_FP_insn_{}PS_XMM', 'Nb_FP_insn_{}PD_XMM')
        flops_ymm = calculate_flops(4, 4, 'Nb_FP_insn_{}PS_YMM', 'Nb_FP_insn_{}PD_YMM')
        flops_zmm = calculate_flops(8, 8, 'Nb_FP_insn_{}PS_ZMM', 'Nb_FP_insn_{}PD_ZMM')


        # try to add the FMA counts
        flops_sc +=  (1 * getter(in_row, 'Nb_FP_insn_FMASS') + 2 * getter(in_row, 'Nb_FP_insn_FMASD'))
        flops_xmm += (4 * getter(in_row, 'Nb_FP_insn_FMAPS_XMM') + 4 * getter(in_row, 'Nb_FP_insn_FMAPD_XMM'))
        flops_ymm += (8 * getter(in_row, 'Nb_FP_insn_FMAPS_YMM')  + 8 * getter(in_row, 'Nb_FP_insn_FMAPD_YMM'))
        flops_zmm += (16 * getter(in_row, 'Nb_FP_insn_FMAPS_ZMM') + 16 * getter(in_row, 'Nb_FP_insn_FMAPD_ZMM'))
        flops = flops_sc + flops_xmm + flops_ymm + flops_zmm
        results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm)
        # Multiple to get count for all cores
        results = results * getter(in_row, 'decan_experimental_configuration.num_core')
    return tuple([(ops * iters_per_rep) / (1E9 * time_per_rep) for ops in results])


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

def calculate_stall_percentages(res, row):
    if args.skip_stalls:
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

def calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec):
    if args.skip_energy:
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
        out_row['E[{}]/O (J/GI)'.format(kind)] = energy / num_ops
        out_row['C/E[{}] (GI/Js)'.format(kind)] = ops_per_sec / energy
        out_row['CO/E[{}] (GI2/Js)'.format(kind)] = (ops_per_sec * num_ops) / energy

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
        out_row['Issued/Retired Uops']=getter(in_row, 'UOPS_ISSUED_ANY') / getter(in_row, 'UOPS_RETIRED_ALL')
    except:
        return


def build_row_output(in_row, user_op_column_name_dict):
    out_row = {}
    calculate_codelet_name(out_row, in_row)
    calculate_expr_settings(out_row, in_row)
    iterations_per_rep = calculate_iterations_per_rep(in_row)
    time = calculate_time(out_row, in_row, iterations_per_rep)
    num_ops, ops_per_sec = calculate_num_insts(out_row, in_row, iterations_per_rep, time)
    calculate_user_op_rate(out_row, in_row, time, user_op_column_name_dict)
    calculate_speculation_ratios (out_row, in_row)
    calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec)

    calculate_data_rates(out_row, in_row, iterations_per_rep, time)
    calculate_stall_percentages(out_row, in_row)
    if args.succinct:
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
    
def summary_report(inputfiles, outputfile, input_format, user_op_file):
    print('Inputfile Format: ', input_format)
    print('Inputfiles: ', inputfiles)
    print('Outputfile: ', outputfile)
    print('User Op file: ', user_op_file)

    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        print(inputfile)
        if (input_format == 'csv'):
            input_data_source = sys.stdin if (inputfile == '-') else inputfile
            cur_df = pd.read_csv(input_data_source, delimiter=',')
        else:
            # Very subtle differnce between read_csv and read_excel about input files so need to call read() for stdin
            input_data_source = sys.stdin.buffer.read() if (inputfile == '-') else inputfile
            cur_df = pd.read_excel(input_data_source, sheet_name='QPROF_full')
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
    print(field_names)

    df.columns = unify_column_names(df.columns)
    output_rows = list(df.apply(build_row_output, user_op_column_name_dict=user_op_col_name_dict, axis=1))

    if (outputfile == '-'):
        output_csvfile = sys.stdout
    else:
        output_csvfile = open (outputfile, 'w', newline='')

    output_fields = succinctify(field_names) if args.succinct else field_names
    output_fields = list(filter(field_has_values(output_rows), output_fields))
    csvwriter = csv.DictWriter(output_csvfile, fieldnames=output_fields)
    csvwriter.writeheader()
    for output_row in output_rows:
        csvwriter.writerow(enforce(output_row, output_fields))
    if (outputfile != '-'):
        output_csvfile.close()

def summary_formulas(formula_file_name):
    with open (formula_file_name, 'w') as formula_file:
        print_formulas(formula_file)

def read_short_names(filename):
    with open(filename, 'r') as infile:
        rows = list(csv.DictReader(infile, delimiter=','))
        for row in rows:
            if 'short_name' in row:
                short_names[row['name']] = row['short_name']
            if 'variant' in row:
                variants[row['name']] = row['variant']

parser = ArgumentParser(description='Generate summary sheets from raw CAPE data.')
parser.add_argument('-i', nargs='+', help='the input csv file', required=True, dest='in_files')
parser.add_argument('-f', nargs='?', default='csv', help='format of input file (default csv can change to xlsx)', choices=['csv', 'xlsx'], dest='in_file_format')
parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
parser.add_argument('-u', nargs='?', help='a user-defined operation count csv file', dest='user_op_file')
parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
parser.add_argument('--succinct', action='store_true', help='generate underscored, lowercase column names')
args = parser.parse_args()

if args.name_file:
    read_short_names(args.name_file)

summary_report(args.in_files, args.out_file, args.in_file_format, args.user_op_file)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
