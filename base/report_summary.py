#!/usr/bin/env python

import re
import sys, getopt
import csv
import traceback

global num_cores
num_cores = 1 # TODO get actual number of cores

def output_fields():
  field_names = ['codelet.name', 'Time (s)',
                 'O (Giga instructions)', 'C=GIPS',
                 'Total PKG Energy (J)', 'Total PKG Power (W)',
                 'E(PKG)/O', 'C/E(PKG)', 'CO/E(PKG)',
                 'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                 'E(DRAM)/O', 'C/E(DRAM)', 'CO/E(DRAM)',
                 'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                 'E(PKG+DRAM)/O', 'C/E(PKG+DRAM)', 'CO/E(PKG+DRAM)',
                 'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GIPS)',
                 'GFLOPS']
  return field_names

def insert_codelet_name(out_row, in_row):
  if (not in_row.has_key('application.name')):
    print 'ERROR: Input CSV file does not have field \"application.name\"\n'
    sys.exit()
  if (not in_row.has_key('codelet.name')):
    print 'ERROR: Input CSV file does not have field \"codelet.name\"\n'
    sys.exit()
  out_row['codelet.name'] = in_row['application.name'] + ': '
  out_row['codelet.name'] += in_row['codelet.name']

def calculate_iterations_per_rep(in_row):
  if (not in_row.has_key('Iterations')):
    print 'ERROR: Input CSV file does not have field \"Iterations\"\n'
    sys.exit()
  if (not in_row.has_key('Repetitions')):
    print 'ERROR: Input CSV file does not have field \"Repetitions\"\n'
    sys.exit()
  return ((float)(in_row['Iterations']) / (float)(in_row['Repetitions']))

def print_iterations_per_rep_formula(formula_file):
  formula_file.write('iterations_per_rep = Iterations / Repetitions\n')

def calculate_time(in_row, iterations_per_rep):
  if (not in_row.has_key('CPU_CLK_UNHALTED_THREAD')):
    print 'ERROR: Input CSV file does not have field \"CPU_CLK_UNHALTED_THREAD\"\n'
    sys.exit()
  if (not in_row.has_key('decan_experimental_configuration.frequency')):
    print 'ERROR: Input CSV file does not have field \"decan_experimental_configuration.frequency\"\n'
    sys.exit()
  return (((float)(in_row['CPU_CLK_UNHALTED_THREAD']) * iterations_per_rep) /
          ((float)(in_row['decan_experimental_configuration.frequency']) * 1e3))

def print_time_formula(formula_file):
  formula_file.write('Time (s) = (CPU_CLK_UNHALTED_THREAD * iterations_per_rep) /' + 
                     ' (decan_experimental_configuration.frequency * 1E3)\n')

def calculate_total_pkg_energy(in_row, iterations_per_rep):
  if (in_row.has_key('UNC_PKG_ENERGY_STATUS')):
    package_energy = (float)(in_row['UNC_PKG_ENERGY_STATUS'])
  elif (in_row.has_key('FREERUN_PKG_ENERGY_STATUS')):
    package_energy = (float)(in_row['FREERUN_PKG_ENERGY_STATUS'])
  else:
    print 'ERROR: Input CSV file does not have field \"UNC_PKG_ENERGY_STATUS\" or \"FREERUN_PKG_ENERGY_STATUS\"\n'
    sys.exit()
  return (package_energy * (float)(in_row['energy.unit']) * iterations_per_rep)

def print_total_pkg_energy_formula(formula_file):
  formula_file.write('Total PKG Energy (J) = (UNC_PKG_ENERGY_STATUS or FREERUN_PKG_ENERGY_STATUS) * energy.unit *' +
                     ' iterations_per_rep\n')

def calculate_total_dram_energy(in_row, iterations_per_rep):
  if (in_row.has_key('UNC_DDR_ENERGY_STATUS')):
    dram_energy = (float)(in_row['UNC_DDR_ENERGY_STATUS'])
  elif (in_row.has_key('FREERUN_DRAM_ENERGY_STATUS')):
    dram_energy = (float)(in_row['FREERUN_DRAM_ENERGY_STATUS'])
  else:
    print 'WARNING: Input CSV file does not have field \"UNC_DDR_ENERGY_STATUS\" or \"FREERUN_DRAM_ENERGY_STATUS\"\n'
    print 'DRAM energy could not be calculated! Only Package energy will be reported\n'
    return (-1.0)
  return (dram_energy * (float)(in_row['energy.unit']) * iterations_per_rep)

def print_total_dram_energy_formula(formula_file):
  formula_file.write('Total DRAM Energy (J) = (UNC_DDR_ENERGY_STATUS or FREERUN_DRAM_ENERGY_STATUS) * energy.unit *' +
                     ' iterations_per_rep\n')

def calculate_num_ops(in_row, iterations_per_rep):
  if (not in_row.has_key('INST_RETIRED_ANY')):
    print 'ERROR: Input CSV file does not have field \"INST_RETIRED_ANY\"\n'
    sys.exit()
  return (((float)(in_row['INST_RETIRED_ANY']) * iterations_per_rep) / (1e9))

def print_num_ops_formula(formula_file):
  formula_file.write('O(Giga instructions) = (INST_RETIRED_ANY *' +
                     ' iterations_per_rep) / 1E9\n')

def getter(in_row, *argv):
  for arg in argv:
    if (arg in in_row):
      return float(in_row[arg])
  raise IndexError(", ".join(map(str, argv)))

def calculate_mem_rates(in_row, iterations_per_rep, time_per_rep):
  global num_cores
  L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * num_cores
  L1_wb_per_it  = getter(in_row, 'Bytes_stored') * num_cores
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

def calculate_load_store_rate(in_row, iterations_per_rep, time_per_rep):
  try:
    load_per_it  = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
    store_per_it = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
  except:
    load_per_it  = in_row['Nb_32_bits_loads'] + in_row['Nb_64_bits_loads'] + in_row['Nb_128_bits_loads'] \
                    + in_row['Nb_256_bits_loads'] + in_row['Nb_MOVH_LPS_D_loads']
    store_per_it = in_row['Nb_32_bits_stores'] + in_row['Nb_64_bits_stores'] + in_row['Nb_128_bits_stores'] \
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
  global num_cores
  return (flops * num_cores * iters_per_rep) / (1E9 * time_per_rep)

def build_row_output(in_row):
  out_row = {}
  insert_codelet_name(out_row, in_row)
  iterations_per_rep = calculate_iterations_per_rep(in_row)
  time = calculate_time(in_row, iterations_per_rep)
  out_row['Time (s)'] = time
  num_ops = calculate_num_ops(in_row, iterations_per_rep)
  out_row['O (Giga instructions)'] = num_ops
  ops_per_sec = num_ops / time
  out_row['C=GIPS'] = ops_per_sec
  total_pkg_energy = calculate_total_pkg_energy(in_row, iterations_per_rep)
  out_row['Total PKG Energy (J)'] = total_pkg_energy
  out_row['Total PKG Power (W)'] = total_pkg_energy / time
  out_row['E(PKG)/O'] = total_pkg_energy / num_ops
  out_row['C/E(PKG)'] = ops_per_sec / total_pkg_energy
  out_row['CO/E(PKG)'] = (ops_per_sec * num_ops) / total_pkg_energy
  total_dram_energy = calculate_total_dram_energy(in_row, iterations_per_rep)
  if (total_dram_energy >=  0.0):
    out_row['Total DRAM Energy (J)'] = total_dram_energy
    out_row['Total DRAM Power (W)'] = total_dram_energy / time
    out_row['E(DRAM)/O'] = total_dram_energy / num_ops
    if (total_dram_energy == 0.0):
      out_row['C/E(DRAM)'] = 'N/A'
      out_row['CO/E(DRAM)'] = 'N/A'
    else:
      out_row['C/E(DRAM)'] = ops_per_sec / total_dram_energy
      out_row['CO/E(DRAM)'] = (ops_per_sec * num_ops) / total_dram_energy
    total_energy = total_pkg_energy + total_dram_energy
    out_row['Total PKG+DRAM Energy (J)'] = total_energy
    out_row['Total PKG+DRAM Power (W)'] = total_energy / time
    out_row['E(PKG+DRAM)/O'] = total_energy / num_ops
    out_row['C/E(PKG+DRAM)'] = ops_per_sec / total_energy
    out_row['CO/E(PKG+DRAM)'] = (ops_per_sec * num_ops) / total_energy
  else:
    out_row['Total DRAM Energy (J)'] = 'N/A'
    out_row['Total DRAM Power (W)'] = 'N/A'
    out_row['E(DRAM)/O'] = 'N/A'
    out_row['C/E(DRAM)'] = 'N/A'
    out_row['CO/E(DRAM)'] = 'N/A'
    out_row['Total PKG+DRAM Energy (J)'] = 'N/A'
    out_row['Total PKG+DRAM Power (W)'] = 'N/A'
    out_row['E(PKG+DRAM)/O'] = 'N/A'
    out_row['C/E(PKG+DRAM)'] = 'N/A'
    out_row['CO/E(PKG+DRAM)'] = 'N/A'
  try:
    out_row['L1 Rate (GB/s)'], out_row['L2 Rate (GB/s)'], out_row['L3 Rate (GB/s)'], out_row['RAM Rate (GB/s)'] = \
      calculate_mem_rates(in_row, iterations_per_rep, time)
    out_row['Load+Store Rate (GIPS)'] = calculate_load_store_rate(in_row, iterations_per_rep, time)
  except:
    out_row['L1 Rate (GB/s)'] = 'N/A'
    out_row['L2 Rate (GB/s)'] = 'N/A'
    out_row['L3 Rate (GB/s)'] = 'N/A'
    out_row['RAM Rate (GB/s)'] = 'N/A'
    out_row['Load+Store Rate (GIPS)'] = 'N/A'
    print "WARNING: Could not compute MHU rates!"
  try:
    out_row['GFLOPS'] = calculate_gflops(in_row, iterations_per_rep, time)
  except:
    out_row['GFLOPS'] = 'N/A'
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

def summary_report(inputfile, outputfile):
  with open (inputfile, 'rU') as input_csvfile:
    csvreader = csv.DictReader(input_csvfile, delimiter=',')
    with open (outputfile, 'wb') as output_csvfile:
      csvwriter = csv.DictWriter(output_csvfile, fieldnames=output_fields())
      csvwriter.writeheader()
      for input_row in csvreader:
        try:
          output_row = build_row_output(input_row)
          csvwriter.writerow(output_row)
        except:
          # skip failures to generate partial reports
          print "WARNING: Unexpected error!"
          traceback.print_exc()
          continue

def summary_formulas(formula_file_name):
  with open (formula_file_name, 'w') as formula_file:
    print_formulas(formula_file)

def main(argv):
    if len(argv) != 4 and len(argv) != 2:
        print '\nERROR: Wrong number of arguments!\n'
        print 'Usage:\n  report_summary.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    inputfile = []
    outputfile = []
    try:
        opts, args = getopt.getopt(argv, "hi:o:")
    except getopt.GetoptError:
        print '\nERROR: Wrong argument(s)!\n'
        print 'Usage:\n  report_summary.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    if len(args) != 0:
        print '\nERROR: Wrong argument(s)!\n'
        print 'Usage:\n  report_summary.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage:\n  report_summary.py  -i <inputfile> (optionally) -o <outputfile>'
            sys.exit()
        elif opt == '-i':
            inputfile.append(arg)
            matchobj = re.search(r'(.+?)\.csv', arg)
            if not matchobj:
              print 'inputfile should be a *.csv file'
              sys.exit()
            if matchobj and len(argv) == 2:
              outputfile.append(str(matchobj.group(1)) + '_summary.csv')
        elif opt == '-o':
            outputfile.append(arg)
            matchobj = re.search(r'(.+?)\.csv', arg)
            if not matchobj:
              print 'outputfile should be a *.csv file'
              sys.exit()
    print 'Inputfile: ', inputfile[0]
    print 'Outputfile: ', outputfile[0]
    summary_report(inputfile[0], outputfile[0])
    formula_file_name = 'Formulas_used.txt'
    summary_formulas(formula_file_name)

if __name__ == "__main__":
    main(sys.argv[1:])
