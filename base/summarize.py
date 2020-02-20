#!/usr/bin/python3
import csv, re
import traceback

from collections import OrderedDict
from argparse import ArgumentParser

args = None
variants = {}
short_names = {}
field_names = [ 'Name', 'Short Name', 'Variant', 'Time (s)',
                'O (Giga instructions)', 'C=GIPS',
                'Total PKG Energy (J)', 'Total PKG Power (W)',
                'E(PKG)/O', 'C/E(PKG)', 'CO/E(PKG)',
                'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                'E(DRAM)/O', 'C/E(DRAM)', 'CO/E(DRAM)',
                'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                'E(PKG+DRAM)/O', 'C/E(PKG+DRAM)', 'CO/E(PKG+DRAM)',
                'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
                'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GIPS)',
                'GFLOPS' ]

def calculate_codelet_name(out_row, in_row):
    return '{0}: {1}'.format(
        getter(in_row, 'application.name', type=str),
        getter(in_row, 'codelet.name', type=str))

def calculate_iterations_per_rep(in_row):
    return getter(in_row, 'Iterations') / getter(in_row, 'Repetitions')

def print_iterations_per_rep_formula(formula_file):
    formula_file.write('iterations_per_rep = Iterations / Repetitions\n')

def calculate_time(in_row, iterations_per_rep):
    return ((getter(in_row, 'CPU_CLK_UNHALTED_REF_TSC') * iterations_per_rep) /
            (getter(in_row, 'cpu.nominal_frequency', 'decan_experimental_configuration.frequency') * 1e3 *
             getter(in_row, 'decan_experimental_configuration.num_core')))

def print_time_formula(formula_file):
    formula_file.write('Time (s) = (CPU_CLK_UNHALTED_THREAD * iterations_per_rep) /' +
                                         ' (decan_experimental_configuration.frequency * 1E3)\n')

def calculate_total_pkg_energy(in_row, iterations_per_rep):
    package_energy = getter(in_row, 'UNC_PKG_ENERGY_STATUS', 'FREERUN_PKG_ENERGY_STATUS')
    return (package_energy * getter(in_row, 'energy.unit') * iterations_per_rep)

def print_total_pkg_energy_formula(formula_file):
    formula_file.write('Total PKG Energy (J) = (UNC_PKG_ENERGY_STATUS or FREERUN_PKG_ENERGY_STATUS) * energy.unit *' +
                                         ' iterations_per_rep\n')

def calculate_total_dram_energy(in_row, iterations_per_rep):
    dram_energy = getter(in_row, 'UNC_DDR_ENERGY_STATUS', 'FREERUN_DRAM_ENERGY_STATUS', default=-1)
    return (dram_energy * getter(in_row, 'energy.unit') * iterations_per_rep)

def print_total_dram_energy_formula(formula_file):
    formula_file.write('Total DRAM Energy (J) = (UNC_DDR_ENERGY_STATUS or FREERUN_DRAM_ENERGY_STATUS) * energy.unit *' +
                                         ' iterations_per_rep\n')

def calculate_num_ops(in_row, iterations_per_rep):
    return ((getter(in_row, 'INST_RETIRED_ANY') * iterations_per_rep) / (1e9))

def print_num_ops_formula(formula_file):
    formula_file.write( \
        'O(Giga instructions) = (INST_RETIRED_ANY * iterations_per_rep) / 1E9\n')

def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            return type_(in_row[arg] if in_row[arg] else default_)
    raise IndexError(', '.join(map(str, argv)))

def calculate_mem_rates(in_row, iterations_per_rep, time_per_rep):
    L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * getter(in_row, 'decan_experimental_configuration.num_core')
    L1_wb_per_it  = getter(in_row, 'Bytes_stored') * getter(in_row, 'decan_experimental_configuration.num_core')
    L2_rc_per_it  = getter(in_row, 'L1D_REPLACEMENT', 'L1D_REPLACEMENT_ND')
    L2_wc_per_it  = getter(in_row, 'L2_TRANS_L1D_WB', 'L2_TRANS_L1D_WB_ND')
    L3_rc_per_it  = getter(in_row, 'L2_RQSTS_MISS', 'L2_RQSTS_MISS_ND')
    L3_wc_per_it  = getter(in_row, 'L2_TRANS_L2_WB', 'L2_TRANS_L2_WB_ND')
    ram_rc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_RD', 'UNC_IMC_DRAM_DATA_READS')
    ram_wc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_WR', 'UNC_IMC_DRAM_DATA_WRITES')
    L1_rwb_per_it  = (L1_rb_per_it  + L1_wb_per_it)
    L2_rwb_per_it  = (L2_rc_per_it  + L2_wc_per_it) * 64
    L3_rwb_per_it  = (L3_rc_per_it  + L3_wc_per_it) * 64
    ram_rwb_per_it = (ram_rc_per_it + ram_wc_per_it) * 64
    L1_GB_s  = (L1_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    L2_GB_s  = (L2_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    L3_GB_s  = (L3_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    ram_GB_s = (ram_rwb_per_it * iterations_per_rep) / (1E9 * time_per_rep)
    return (L1_GB_s, L2_GB_s, L3_GB_s, ram_GB_s)

def calculate_register_bandwidth(in_row, iterations_per_rep, time_per_rep):
    num_cores = getter(in_row, 'decan_experimental_configuration.num_core')
    reg_gp_addr_rw = getter(in_row, 'Bytes_GP_addr_read') + getter(in_row, 'Bytes_GP_addr_write')
    reg_gp_data_rw = getter(in_row, 'Bytes_GP_data_read') + getter(in_row, 'Bytes_GP_data_write')
    reg_simd_rw = getter(in_row, 'Bytes_SIMD_read') + getter(in_row, 'Bytes_SIMD_write')
    rates = [ num_cores * iterations_per_rep * x / (1E9 * time_per_rep) for x in [ \
        reg_gp_addr_rw, reg_gp_data_rw, reg_simd_rw \
    ]]
    return rates + [ sum(rates) ]

def calculate_load_store_rate(in_row, iterations_per_rep, time_per_rep):
    try:
        load_per_it  = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
        store_per_it = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
    except:
        load_per_it  = in_row['Nb_8_bits_loads'] + in_row['Nb_16_bits_loads'] \
                     + in_row['Nb_32_bits_loads'] + in_row['Nb_64_bits_loads'] + in_row['Nb_128_bits_loads'] \
                     + in_row['Nb_256_bits_loads'] + in_row['Nb_MOVH_LPS_D_loads']
        store_per_it = in_row['Nb_8_bits_stores'] + in_row['Nb_16_bits_stores'] \
                     + in_row['Nb_32_bits_stores'] + in_row['Nb_64_bits_stores'] + in_row['Nb_128_bits_stores'] \
                     + in_row['Nb_256_bits_stores'] + in_row['Nb_MOVH_LPS_D_stores']
    return ((load_per_it + store_per_it) * iterations_per_rep) / (1E9 * time_per_rep)

def calculate_gflops(in_row, iters_per_rep, time_per_rep):
    flops = 0.5 * getter(in_row, 'Nb_insn_ADD/SUBSS') + 2 * getter(in_row, 'Nb_insn_ADD/SUBPS_XMM') + 4 * getter(in_row, 'Nb_insn_ADD/SUBPS_YMM') + 8 * getter(in_row, 'Nb_insn_ADD/SUBPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_ADD/SUBSD') + 2 * getter(in_row, 'Nb_insn_ADD/SUBPD_XMM') + 4 * getter(in_row, 'Nb_insn_ADD/SUBPD_YMM') + 8 * getter(in_row, 'Nb_insn_ADD/SUBPD_ZMM') + \
                    0.5 * getter(in_row, 'Nb_insn_DIVSS') + 2 * getter(in_row, 'Nb_insn_DIVPS_XMM') + 4 * getter(in_row, 'Nb_insn_DIVPS_YMM') + 8 * getter(in_row, 'Nb_insn_DIVPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_DIVSD') + 2 * getter(in_row, 'Nb_insn_DIVPD_XMM') + 4 * getter(in_row, 'Nb_insn_DIVPD_YMM') + 8 * getter(in_row, 'Nb_insn_DIVPD_ZMM') + \
                    0.5 * getter(in_row, 'Nb_insn_MULSS') + 2 * getter(in_row, 'Nb_insn_MULPS_XMM') + 4 * getter(in_row, 'Nb_insn_MULPS_YMM') + 8 * getter(in_row, 'Nb_insn_MULPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_MULSD') + 2 * getter(in_row, 'Nb_insn_MULPD_XMM') + 4 * getter(in_row, 'Nb_insn_MULPD_YMM') + 8 * getter(in_row, 'Nb_insn_MULPD_ZMM') + \
                    0.5 * getter(in_row, 'Nb_insn_SQRTSS') + 2 * getter(in_row, 'Nb_insn_SQRTPS_XMM') + 4 * getter(in_row, 'Nb_insn_SQRTPS_YMM') + 8 * getter(in_row, 'Nb_insn_SQRTPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_SQRTSD') + 2 * getter(in_row, 'Nb_insn_SQRTPD_XMM') + 4 * getter(in_row, 'Nb_insn_SQRTPD_YMM') + 8 * getter(in_row, 'Nb_insn_SQRTPD_ZMM') + \
                    0.5 * getter(in_row, 'Nb_insn_RSQRTSS') + 2 * getter(in_row, 'Nb_insn_RSQRTPS_XMM') + 4 * getter(in_row, 'Nb_insn_RSQRTPS_YMM') + 8 * getter(in_row, 'Nb_insn_RSQRTPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_RSQRTSD') + 2 * getter(in_row, 'Nb_insn_RSQRTPD_XMM') + 4 * getter(in_row, 'Nb_insn_RSQRTPD_YMM') + 8 * getter(in_row, 'Nb_insn_RSQRTPD_ZMM') + \
                    0.5 * getter(in_row, 'Nb_insn_RCPSS') + 2 * getter(in_row, 'Nb_insn_RCPPS_XMM') + 4 * getter(in_row, 'Nb_insn_RCPPS_YMM') + 8 * getter(in_row, 'Nb_insn_RCPPS_ZMM') + \
                    1 * getter(in_row, 'Nb_insn_RCPSD') + 2 * getter(in_row, 'Nb_insn_RCPPD_XMM') + 4 * getter(in_row, 'Nb_insn_RCPPD_YMM') + 8 * getter(in_row, 'Nb_insn_RCPPD_ZMM')
    try:
        # try to add the FMA counts
        flops += 1 * getter(in_row, 'Nb_insn_FMASS') + 4 * getter(in_row, 'Nb_insn_FMAPS_XMM') + 8 * getter(in_row, 'Nb_insn_FMAPS_YMM') + 16 * getter(in_row, 'Nb_insn_FMAPS_ZMM') + \
                         2 * getter(in_row, 'Nb_insn_FMASD') + 4 * getter(in_row, 'Nb_insn_FMAPD_XMM') + 8 * getter(in_row, 'Nb_insn_FMAPD_YMM') + 16 * getter(in_row, 'Nb_insn_FMAPD_ZMM')
    except:
        pass
    return (flops * getter(in_row, 'decan_experimental_configuration.num_core') * iters_per_rep) / (1E9 * time_per_rep)


def shorten_stall_counter(field):
    field = field[(len('RESOURCE_STALLS') + 1):]
    if field == '_ALL_PRF_CONTROL':
        return '%PRF'
    elif field == '_PHT_FULL':
        return '%PHT'
    elif field == 'LOAD_MATRIX':
        return '%LM'
    else:
        return '%' + field.upper()

def calculate_stall_percentages(row):
    res = OrderedDict()
    unhlt = getter(row, 'CPU_CLK_UNHALTED_THREAD')
    for col in row:
        if col == 'RESOURCE_STALLS_FPCW_OR_MXCSR' or \
            col == 'RESOURCE_STALLS_LB_SB':
            continue
        if col.startswith('RESOURCE_STALLS'):
            res[shorten_stall_counter(col)] = \
                getter(row, col) / unhlt
    res['%FrontEnd'] = getter(row, 'Front_end_(cycles)') / unhlt
    return res

def build_row_output(in_row):
    out_row = {}
    out_row['Name'] = calculate_codelet_name(out_row, in_row)
    if out_row['Name'] in short_names:
        out_row['Short Name'] = short_names[out_row['Name']]
    iterations_per_rep = calculate_iterations_per_rep(in_row)
    time = calculate_time(in_row, iterations_per_rep)
    out_row['Time (s)'] = time
    out_row['Variant'] = variants[out_row['Name']] if out_row['Name'] in variants \
        else getter(in_row, 'decan_variant.name', type=str)
    num_ops = calculate_num_ops(in_row, iterations_per_rep)
    out_row['O (Giga instructions)'] = num_ops
    ops_per_sec = num_ops / time
    out_row['C=GIPS'] = ops_per_sec
    if not args.skip_energy:
        total_pkg_energy = calculate_total_pkg_energy(in_row, iterations_per_rep)
        out_row['Total PKG Energy (J)'] = total_pkg_energy
        out_row['Total PKG Power (W)'] = total_pkg_energy / time
        out_row['E(PKG)/O'] = total_pkg_energy / num_ops
        out_row['C/E(PKG)'] = ops_per_sec / total_pkg_energy
        out_row['CO/E(PKG)'] = (ops_per_sec * num_ops) / total_pkg_energy
        total_dram_energy = calculate_total_dram_energy(in_row, iterations_per_rep)
    else:
        total_dram_energy = -1.0
    if (total_dram_energy >=  0.0):
        out_row['Total DRAM Energy (J)'] = total_dram_energy
        out_row['Total DRAM Power (W)'] = total_dram_energy / time
        out_row['E(DRAM)/O'] = total_dram_energy / num_ops
        if total_dram_energy:
            out_row['C/E(DRAM)'] = ops_per_sec / total_dram_energy
            out_row['CO/E(DRAM)'] = (ops_per_sec * num_ops) / total_dram_energy
        total_energy = total_pkg_energy + total_dram_energy
        out_row['Total PKG+DRAM Energy (J)'] = total_energy
        out_row['Total PKG+DRAM Power (W)'] = total_energy / time
        out_row['E(PKG+DRAM)/O'] = total_energy / num_ops
        out_row['C/E(PKG+DRAM)'] = ops_per_sec / total_energy
        out_row['CO/E(PKG+DRAM)'] = (ops_per_sec * num_ops) / total_energy
    else:
        pass
    try:
        out_row['L1 Rate (GB/s)'], out_row['L2 Rate (GB/s)'], out_row['L3 Rate (GB/s)'], out_row['RAM Rate (GB/s)'] = \
            calculate_mem_rates(in_row, iterations_per_rep, time)
    except:
        pass
    try:
        out_row['Load+Store Rate (GIPS)'] = calculate_load_store_rate(in_row, iterations_per_rep, time)
    except:
        pass
    try:
        out_row['Register ADDR Rate (GB/s)'], out_row['Register DATA Rate (GB/s)'], \
        out_row['Register SIMD Rate (GB/s)'], out_row['Register Rate (GB/s)'], = \
            calculate_register_bandwidth(in_row, iterations_per_rep, time)
    except:
        pass
    try:
        out_row['GFLOPS'] = calculate_gflops(in_row, iterations_per_rep, time)
    except:
        pass
    try:
        if not args.skip_stalls:
            stalls = calculate_stall_percentages(in_row)
            out_row.update(stalls)
            for field in stalls:
                if field not in field_names:
                    field_names.append(field)
    except:
        pass
    return out_row

def print_formulas(formula_file):
    print_iterations_per_rep_formula(formula_file)
    print_time_formula(formula_file)
    print_num_ops_formula(formula_file)
    formula_file.write('C(GIPS) = O(Giga instructions) / Time(s)\n')
    print_total_pkg_energy_formula(formula_file)
    formula_file.write('Total PKG Power(W) = Total PKG Energy (J)/ Time(s)\n')
    formula_file.write('E(PKG)/O = Total PKG Energy (J) / O(Giga instructions)\n')
    formula_file.write('C/E(PKG) = C(GIPS) / Total PKG Energy(J)\n')
    formula_file.write('CO/E(PKG) = (C(GIPS) * O(Giga instructions)) / Total PKG Energy(J)\n')
    print_total_dram_energy_formula(formula_file)
    formula_file.write('Total DRAM Power(W) = Total DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E(DRAM)/O = Total DRAM Energy (J) / O(Giga instructions)\n')
    formula_file.write('C/E(DRAM) = C(GIPS) / Total DRAM Energy(J)\n')
    formula_file.write('CO/E(DRAM) = (C(GIPS) * O(Giga instructions)) / Total DRAM Energy(J)\n')
    formula_file.write('Total PKG+DRAM Energy (J) = Total PKG Energy (J) + Total DRAM Energy (J)\n')
    formula_file.write('Total PKG+DRAM Power(W) = Total PKG+DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E(PKG+DRAM)/O = Total PKG+DRAM Energy (J) / O(Giga instructions)\n')
    formula_file.write('C/E(PKG+DRAM) = C(GIPS) / Total PKG+DRAM Energy(J)\n')
    formula_file.write('CO/E(PKG+DRAM) = (C(GIPS) * O(Giga instructions)) / Total PKG+DRAM Energy(J)\n')

def field_has_values(rows):
    def tmp_(field):
        return not all(field not in row for row in rows)
    return tmp_

def enforce(d, field_names):
    return { x : d.get(x, None) for x in field_names }

def summary_report(inputfile, outputfile):
    print('Inputfile: ', inputfile)
    print('Outputfile: ', outputfile)
    with open (inputfile, 'r') as input_csvfile:
        csvreader = csv.DictReader(input_csvfile, delimiter=',')
        with open (outputfile, 'w', newline='') as output_csvfile:
            output_rows = list(map(build_row_output, csvreader))
            output_fields = list(filter(field_has_values(output_rows), field_names))
            csvwriter = csv.DictWriter(output_csvfile, fieldnames=output_fields)
            csvwriter.writeheader()
            for output_row in output_rows:
                csvwriter.writerow(enforce(output_row, output_fields))

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
parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
args = parser.parse_args()

if args.name_file:
    read_short_names(args.name_file)

summary_report(args.in_file, args.out_file)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
