#!/usr/bin/python3.6
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

# At least Python version 3.6 is required
assert sys.version_info >= (3,6)

args = None
variants = {}
short_names = {}
field_names = [ 'Name', 'Short Name', 'Variant', 'Time (s)',
                'O=Inst. Count (GI)', 'C=Inst. Rate (GI/s)',
                'Total PKG Energy (J)', 'Total PKG Power (W)',
                'E[PKG]/O (J/GI)', 'C/E[PKG] (GI/Js)', 'CO/E[PKG] (GI2/Js)',
                'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                'E[DRAM]/O (J/GI)', 'C/E[DRAM] (GI/Js)', 'CO/E[DRAM] (GI2/Js)',
                'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                'E[PKG+DRAM]/O (J/GI)', 'C/E[PKG+DRAM] (GI/Js)', 'CO/E[PKG+DRAM] (GI2/Js)',
                'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
                'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GIPS)',
                'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)',
                '%PRF','%SB','%PRF','%RS','%LB','%ROB','%LM','%ANY','%FrontEnd' ]

L2R_TrafficDict={'SKX': ['L1D_REPLACEMENT'], 'HSW': ['L1D_REPLACEMENT'], 'IVB': ['L1D_REPLACEMENT'], 'SNB': ['L1D_REPLACEMENT'] }
L2W_TrafficDict={'SKX': ['L2_TRANS_L1D_WB'], 'HSW': ['L2_TRANS_L1D_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L1D_WB_RQST_ALL'], 'SNB': ['L1D_WB_RQST_ALL'] }
L3R_TrafficDict={'SKX': ['L2_RQSTS_MISS'], 'HSW': ['L2_RQSTS_MISS', 'SQ_MISC_FILL_DROPPED'], 'IVB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'], 'SNB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'] }
L3W_TrafficDict={'SKX': ['L2_TRANS_L2_WB'], 'HSW': ['L2_TRANS_L2_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS'], 'SNB':  ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS']}

StallDict={'SKX': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_PHT_FULL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'HSW': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'IVB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'SNB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS2_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' }}


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

def calculate_num_insts(out_row, in_row, iterations_per_rep, time):
    insts_per_rep = ((getter(in_row, 'INST_RETIRED_ANY') * iterations_per_rep) / (1e9))
    out_row['O=Inst. Count (GI)'] = insts_per_rep
    ops_per_sec = insts_per_rep / time
    out_row['C=Inst. Rate (GI/s)'] = ops_per_sec

    try:
        out_row['FLOP Rate (GFLOP/s)'] = calculate_gflops(in_row, iterations_per_rep, time)
        out_row['IOP Rate (GIOP/s)'] = calculate_giops(in_row, iterations_per_rep, time)
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
        L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_wb_per_it  = getter(in_row, 'Bytes_stored') * getter(in_row, 'decan_experimental_configuration.num_core')
        arch = arch_helper(in_row)
        L2_rc_per_it  = counter_sum(in_row, L2R_TrafficDict[arch])
        L2_wc_per_it  = counter_sum(in_row, L2W_TrafficDict[arch])
        L3_rc_per_it  = counter_sum(in_row, L3R_TrafficDict[arch])
        L3_wc_per_it  = counter_sum(in_row, L3W_TrafficDict[arch])

        ram_rc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_RD', 'UNC_IMC_DRAM_DATA_READS')
        ram_wc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_WR', 'UNC_IMC_DRAM_DATA_WRITES')
        L1_rwb_per_it  = (L1_rb_per_it  + L1_wb_per_it)
        L2_rwb_per_it  = (L2_rc_per_it  + L2_wc_per_it) * 64
        L3_rwb_per_it  = (L3_rc_per_it  + L3_wc_per_it) * 64
        ram_rwb_per_it = (ram_rc_per_it + ram_wc_per_it) * 64
        out_row['L1 Rate (GB/s)']  = (L1_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['L2 Rate (GB/s)']  = (L2_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['L3 Rate (GB/s)']  = (L3_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['RAM Rate (GB/s)'] = (ram_rwb_per_it * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['Load+Store Rate (GIPS)'] = calculate_load_store_rate()
    except:
        pass
    try:
        out_row['Register ADDR Rate (GB/s)'], out_row['Register DATA Rate (GB/s)'], \
        out_row['Register SIMD Rate (GB/s)'], out_row['Register Rate (GB/s)'] = calculate_register_bandwidth()
    except:
        pass


def calculate_giops(in_row, iters_per_rep, time_per_rep):
    iops = 0
    itypes = ['ADD_SUB', 'CMP', 'MUL' ]

    for itype in itypes:
        iops += (0.5 * getter(in_row, 'Nb_scalar_INT_arith_insn_{}'.format(itype)))
        iops += (2 * getter(in_row, 'Nb_INT_arith_insn_{}_XMM'.format(itype)))
        iops += (4 * getter(in_row, 'Nb_INT_arith_insn_{}_YMM'.format(itype)))
        iops += (8 * getter(in_row, 'Nb_INT_arith_insn_{}_ZMM'.format(itype)))

    itypes = ['AND', 'XOR', 'OR', 'SHIFT']
    for itype in itypes:
        iops += (0.5 * getter(in_row, 'Nb_scalar_INT_logic_insn_{}'.format(itype)))
        iops += (2 * getter(in_row, 'Nb_INT_logic_insn_{}_XMM'.format(itype)))
        iops += (4 * getter(in_row, 'Nb_INT_logic_insn_{}_YMM'.format(itype)))
        iops += (8 * getter(in_row, 'Nb_INT_logic_insn_{}_ZMM'.format(itype)))

    # try to add the TEST, ANDN, FMA and SAD counts (they have not scalar count)
    iops += (2 * getter(in_row, 'Nb_INT_logic_insn_ANDN_XMM') + 4 * getter(in_row, 'Nb_INT_logic_insn_ANDN_YMM') + 8 * getter(in_row, 'Nb_INT_logic_insn_ANDN_ZMM'))
    iops += (2 * getter(in_row, 'Nb_INT_logic_insn_TEST_XMM') + 4 * getter(in_row, 'Nb_INT_logic_insn_TEST_YMM') + 8 * getter(in_row, 'Nb_INT_logic_insn_TEST_ZMM'))
    iops += (4 * getter(in_row, 'Nb_INT_arith_insn_FMA_XMM') + 8 * getter(in_row, 'Nb_INT_arith_insn_FMA_YMM') + 16 * getter(in_row, 'Nb_INT_arith_insn_FMA_ZMM'))
    iops += (4 * getter(in_row, 'Nb_INT_arith_insn_SAD_XMM') + 8 * getter(in_row, 'Nb_INT_arith_insn_SAD_YMM') + 16 * getter(in_row, 'Nb_INT_arith_insn_SAD_ZMM'))
    return (iops * getter(in_row, 'decan_experimental_configuration.num_core') * iters_per_rep) / (1E9 * time_per_rep)


def calculate_gflops(in_row, iters_per_rep, time_per_rep):
    flops = 0
    itypes = ['ADD_SUB', 'DIV', 'MUL', 'SQRT', 'RSQRT', 'RCP']
    for itype in itypes:
        flops += (0.5 * getter(in_row, 'Nb_FP_insn_{}SS'.format(itype)) + 1 * getter(in_row, 'Nb_FP_insn_{}SD'.format(itype)))
        flops += (2 * getter(in_row, 'Nb_FP_insn_{}PS_XMM'.format(itype)) + 2 * getter(in_row, 'Nb_FP_insn_{}PD_XMM'.format(itype)))
        flops += (4 * getter(in_row, 'Nb_FP_insn_{}PS_YMM'.format(itype)) + 4 * getter(in_row, 'Nb_FP_insn_{}PD_YMM'.format(itype)))
        flops += (8 * getter(in_row, 'Nb_FP_insn_{}PS_ZMM'.format(itype)) + 8 * getter(in_row, 'Nb_FP_insn_{}PD_ZMM'.format(itype)))

    # try to add the FMA counts
    flops += 1 * getter(in_row, 'Nb_FP_insn_FMASS') + 4 * getter(in_row, 'Nb_FP_insn_FMAPS_XMM') + 8 * getter(in_row, 'Nb_FP_insn_FMAPS_YMM') + 16 * getter(in_row, 'Nb_FP_insn_FMAPS_ZMM') + \
             2 * getter(in_row, 'Nb_FP_insn_FMASD') + 4 * getter(in_row, 'Nb_FP_insn_FMAPD_XMM') + 8 * getter(in_row, 'Nb_FP_insn_FMAPD_YMM') + 16 * getter(in_row, 'Nb_FP_insn_FMAPD_ZMM')
    return (flops * getter(in_row, 'decan_experimental_configuration.num_core') * iters_per_rep) / (1E9 * time_per_rep)


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
        for buf in ['RS', 'LB', 'SB', 'ROB', 'PRF', 'LM', 'FrontEnd']:
            res['%'+buf] = getter(row, StallDict[arch][buf]) / unhlt
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


def build_row_output(in_row):
    out_row = {}
    calculate_codelet_name(out_row, in_row)
    iterations_per_rep = calculate_iterations_per_rep(in_row)
    time = calculate_time(out_row, in_row, iterations_per_rep)
    num_ops, ops_per_sec = calculate_num_insts(out_row, in_row, iterations_per_rep, time)
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

def summary_report(inputfile, outputfile, input_format):
    print('Inputfile Format: ', input_format)
    print('Inputfile: ', inputfile)
    print('Outputfile: ', outputfile)

    if (input_format == 'csv'):
        input_data_source = sys.stdin if (inputfile == '-') else inputfile
        df = pd.read_csv(input_data_source, delimiter=',')
    else:
        # Very subtle differnce between read_csv and read_excel about input files so need to call read() for stdin
        input_data_source = sys.stdin.buffer.read() if (inputfile == '-') else inputfile
        df = pd.read_excel(input_data_source, sheet_name='QPROF_full')
    for index, row in df.iterrows():
        print(getter(row,'L1D_REPLACEMENT'))
    output_rows = list(df.apply(build_row_output, axis=1))

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
parser.add_argument('-i', help='the input csv file', required=True, dest='in_file')
parser.add_argument('-f', nargs='?', default='csv', help='format of input file (default csv can change to xlsx)', choices=['csv', 'xlsx'], dest='in_file_format')
parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
parser.add_argument('--succinct', action='store_true', help='generate underscored, lowercase column names')
args = parser.parse_args()

if args.name_file:
    read_short_names(args.name_file)
summary_report(args.in_file, args.out_file, args.in_file_format)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
