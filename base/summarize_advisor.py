#!/usr/bin/python3

import sys
import pandas as pd
from collections import defaultdict 
from argparse import ArgumentParser

# Need to source advixe-vars.sh in shell
# More API info: {advisor_dir}/pythonapi/documentation
# Metric list: {advisor_dir}/pythonapi/examples/columns.txt
import advisor

#from capelib import succinctify
#from capelib import calculate_all_rate_and_counts
import capelib
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)


# "MEMORY" or "COMPUTE" or "UNKNOWN"
def get_insn_type(insn, opcode):
    if opcode == "UNKNOWN":
        return "UNKNOWN"
    if "MEMORY" in insn['instruction_type']:
        return "MEMORY"
    return "COMPUTE"

def get_insn_data_type(insn):
    type_dict={'': -1, 'ubyte':0, 'int': 1, 'float': 2}
    rev_type_dict={-1: "UNKNOWN", 0: "INT", 1: "INT", 2: "FP"}

    operands=insn['operands']
    data_type = -1
    for operand in operands:
#        print(operand['type_name'])
        data_type = max(data_type, type_dict[operand['type_name']])
#    print("TYPE:", rev_type_dict[data_type])
    return rev_type_dict[data_type]

def get_insn_opcode(insn, inst_map):
    inst_name = insn['instruction_name']
    opcode = inst_map.loc[inst_map['instruction'] == inst_name, 'opcode'].tolist()
    opcode = str(opcode[0]) if opcode else "UNKNOWN"
#    print(inst_name, "=>", opcode)
    return opcode

def get_operand_bits(insn):
    operands=insn['operands']
    operand_width = 0
    for operand in operands:
#        print(operand['operand_width'])
        operand_width = max(operand_width, int(operand['operand_width']))
    return operand_width

def get_mem_insn_bits(insn):
    return get_operand_bits(insn)

# "scalar" or "XMM" or "YMM" or "ZMM"
def get_insn_vec_type(insn):
    vec_type_dict=defaultdict(lambda: "scalar")
    vec_type_dict[128]="XMM"
    vec_type_dict[256]="YMM"
    vec_type_dict[512]="ZMM"
    operand_width = get_operand_bits(insn)
    return vec_type_dict[operand_width]

# "S", "D" or error
def get_fpinsn_precision(insn):
    precision_dict={32: "S", 64: "D"}

    operands=insn['operands']
    type_width = 0
    for operand in operands:
        type_width = max(type_width, int(operand['type_width']))
#    print("PRECIS:", precision_dict[type_width])
    return precision_dict[type_width]

# "loads" or "stores"
def get_mem_insn_access_type(instruction):
    if "LOAD" in instruction['instruction_type']:
        return "loads"
    elif "STORE" in instruction['instruction_type']:
        return "stores"
    else:
        return "UNKNOWN"


# "logic" or "arith" or "UNKNOWN"
def get_int_insn_kind(opcode):
    logic_opcodes=['AND', 'XOR', 'OR', 'SHIFT', 'ANDN', 'TEST' ]
    arith_opcodes=['ADD_SUB', 'CMP', 'MUL', 'FMA', 'SAD' ]
    return "arith"

# This function attempts to parse the instruction information to generate CQA counts
# Currently approximated after looking at instruction family information in ./asm/x86_64/x86_64_arch.c
# TODO: Emmanuel can help to correct this.
def build_cqa_like_counts(instruction, cqa_row, inst_map):
    isVectorized = True if "VECTORIZED" in instruction['instruction_type'] else False
    isLoad = True if "LOAD" in instruction['instruction_type'] else False
    isStore = True if "STORE" in instruction['instruction_type'] else False

    #     print(instruction['instruction_type'])    
    print(instruction['asm'])
#     print(instruction['operands'])

#    print("Type: {}".format(instruction['instruction_type']))
    opcode = get_insn_opcode(instruction, inst_map)

    # "MEMORY" or "COMPUTE" or "UNKNOWN"
    insn_type = get_insn_type(instruction, opcode)
    # "FP" or "INT" or "UNKNOWN"
    data_type = get_insn_data_type(instruction)
    # "scalar" or "XMM" or "YMM" or "ZMM"
    vec_type = get_insn_vec_type(instruction)


    if insn_type == "COMPUTE":
        if data_type == "FP":
            # "S", "D" or error
            precision = get_fpinsn_precision(instruction)
            if vec_type == "scalar":
                cqa_metric_name="Nb_FP_insn_{}S{}".format(opcode, precision)
            else:
                cqa_metric_name="Nb_FP_insn_{}P{}_{}".format(opcode, precision, vec_type)
        else:
            # "logic" or "arith" or "UNKNOWN"
            int_insn_kind = get_int_insn_kind(opcode)
            if vec_type == "scalar":
                cqa_metric_name="Nb_scalar_INT_{}_insn_{}".format(int_insn_kind, opcode)
            else:
                cqa_metric_name="Nb_INT_{}_insn_{}_{}".format(int_insn_kind, opcode, vec_type)
    elif insn_type == "MEMORY":
        # "loads" or "stores"
        access_type = get_mem_insn_access_type(instruction)
        if opcode == "MOVH/LPS/D":
            cqa_metric_name="Nb_MOVH/LPS/D_{}".format(access_type)
        else:
            bits = get_mem_insn_bits(instruction)
            cqa_metric_name="Nb_{}_bits_{}".format(bits, access_type)
    else:
        # "UNKNOWN"
        cqa_metric_name = "UNKNOWN"

    cqa_row[cqa_metric_name] += 1


def to_float(str):
    try:
        return float(str)
    except:
        return 0

def build_inst_map():
    cqa_data = pd.read_csv('metrics_data/cqa_insn_families.csv')
    cqa_data['opcode'] = "UNKNOWN"

    # FM_ADD and FM_SUB => "ADD_SUB"
    # FM_DIV => "DIV"
    # FM_MUL => "MUL"
    # FM_SQRT => "SQRT"
    # FM_RSQRT => "RSQRT"
    # FM_RCP => "RCP"
    # FM_FMA => "FMA"
    # FM_CMP => "CMP" with exception that TEST instructions will be "TEST"
    # FM_AND => "AND" with exception that ANDN instructions will be "ANDN" and TEST instruction will be "TEST"
    # FM_XOR => "XOR"
    # FM_OR => "OR"
    # FM_SHIFT => "SHIFT"
    # FM_DSP => "SAD"
    # FM_MOV => "MOV" with exception that MOVH* and MOVL* instructions will be "MOVH/LPS/D"
    # First set the regular cases
    opcodes = cqa_data['opcode']
    opcodes[cqa_data['cqa family'] == "FM_ADD"] = "ADD_SUB"
    opcodes[cqa_data['cqa family'] == "FM_SUB"] = "ADD_SUB"
    opcodes[cqa_data['cqa family'] == "FM_DIV"] = "DIV"
    opcodes[cqa_data['cqa family'] == "FM_MUL"] = "MUL"
    opcodes[cqa_data['cqa family'] == "FM_SQRT"] = "SQRT"
    opcodes[cqa_data['cqa family'] == "FM_RSQRT"] = "RSQRT"
    opcodes[cqa_data['cqa family'] == "FM_RCP"] = "RCP"
    opcodes[cqa_data['cqa family'] == "FM_FMA"] = "FMA"
    cmpMask = cqa_data['cqa family'] == "FM_CMP"
    opcodes[cmpMask] = "CMP"
    andMask = cqa_data['cqa family'] == "FM_AND"
    opcodes[andMask] = "AND"
    opcodes[cqa_data['cqa family'] == "FM_XOR"] = "XOR"
    opcodes[cqa_data['cqa family'] == "FM_OR"] = "OR"
    opcodes[cqa_data['cqa family'] == "FM_SHIFT"] = "SHIFT"
    opcodes[cqa_data['cqa family'] == "FM_DSP"] = "SAD"
    movMask = cqa_data['cqa family'] == "FM_MOV"
    opcodes[movMask] = "MOV"
    # Then set the exceptions
    opcodes[cmpMask & cqa_data['instruction'].str.contains("TEST")] = "TEST"
    opcodes[andMask & cqa_data['instruction'].str.contains("TEST")] = "TEST"
    opcodes[andMask & cqa_data['instruction'].str.contains("ANDN")] = "ANDN"
    opcodes[movMask & cqa_data['instruction'].str.contains("MOVH")] = "MOVH/LPS/D"
    opcodes[movMask & cqa_data['instruction'].str.contains("MOVL")] = "MOVH/LPS/D"    
#    cqa_data.to_csv('/tmp/cqa.csv')
#    print(cqa_data)
    return cqa_data
    
def init_cqa_row(thread_count):
    cqa_row=defaultdict(lambda: 0)
    cqa_row['decan_experimental_configuration.num_core'] = thread_count
    itypes = ['ADD_SUB', 'DIV', 'MUL', 'SQRT', 'RSQRT', 'RCP', 'FMA']
    for itype in itypes:
        for precision in ['S', 'D']:
            cqa_row['Nb_FP_insn_{}S{}'.format(itype, precision)]=0
            for register in ['XMM', 'YMM' , 'ZMM']:
                cqa_row['Nb_FP_insn_{}P{}_{}'.format(itype, precision, register)]=0
                
    itypes = ['ADD_SUB', 'CMP', 'MUL' ]
    for itype in itypes:
        cqa_row['Nb_scalar_INT_arith_insn_{}'.format(itype)] = 0
        for register in ['XMM', 'YMM' , 'ZMM']:
            cqa_row['Nb_INT_arith_insn_{}_{}'.format(itype, register)] = 0
            
    itypes = ['AND', 'XOR', 'OR', 'SHIFT']
    for itype in itypes:
        cqa_row['Nb_scalar_INT_logic_insn_{}'.format(itype)] = 0
        for register in ['XMM', 'YMM' , 'ZMM']:
            cqa_row['Nb_INT_logic_insn_{}_{}'.format(itype, register)] = 0
    itypes = ['ANDN', 'TEST']
    for itype in itypes:
        for register in ['XMM', 'YMM' , 'ZMM']:
#            print('Nb_INT_logic_insn_{}_{}'.format(itype, register))
            cqa_row['Nb_INT_logic_insn_{}_{}'.format(itype, register)] = 0
            
    itypes = ['FMA', 'SAD']
    for itype in itypes:
        for register in ['XMM', 'YMM' , 'ZMM']:
            cqa_row['Nb_INT_arith_insn_{}_{}'.format(itype, register)] = 0
            
    itypes = ['loads', 'stores']
    for itype in itypes:
        cqa_row['Nb_MOVH/LPS/D_{}'.format(itype)] = 0
        for bits in [8, 16,32,64, 128, 256, 512]:
            cqa_row['Nb_{}_bits_{}'.format(bits, itype)] = 0
    
    return cqa_row

def calculate_num_insts(loop_function_ids, survey, out):
    inst_map=build_inst_map()
    asm = []
    cqa_out = pd.DataFrame()
    for entry in survey.bottomup:
        loop_function_id = entry['loop_function_id']
        print(loop_function_id)
        if entry['loop_function_id'] in loop_function_ids:            
            time = to_float(entry['self_time'])
            iterations_per_rep=to_float(entry['trip_count_total'])
            print(iterations_per_rep)
            iterations_per_rep=to_float(iterations_per_rep)
            asm += ["{:54.54} ".format(entry['function_call_sites_and_loops']), " "*54]
            # Create a row and iterate instructions to gather count.
            cqa_row=init_cqa_row(to_float(entry['thread_count']))

            out_row=defaultdict(lambda: 0)
            for instruction in entry.assembly:
                build_cqa_like_counts(instruction, cqa_row, inst_map)

                #                    asm.append("{:4.4}{:50.50} ".format(isVectorized, instruction['asm']))
#                print(cqa_row)

                asm.append("")
            capelib.calculate_all_rate_and_counts(out_row, cqa_row,iterations_per_rep, time)
            out_row['loop_function_id']=loop_function_id            
            cqa_out = cqa_out.append(pd.DataFrame.from_dict([out_row]))

    print(cqa_out)
    print(out.columns)
    print(cqa_out.columns)
    trim_cols=[col for col in out.columns if col not in cqa_out.columns]
    trim_cols.append('loop_function_id')  # Add back key column
    out=pd.merge(out[trim_cols], cqa_out, how='left', on=['loop_function_id'])
    print(out)

#            
#print(out[out.loop_function_id == loop_function_id])

#            print(out_df.columns)
            #            out.loc[out.loop_function_id == loop_function_id, out_df.columns] = 0
            #            out.loc[out.loop_function_id == loop_function_id, list(out_df.columns)] = 0
#            ll = list(out_df.columns)
#            ll = [l for l in out_df.columns]
#            print(out_df[ll])
#            out.loc[out.loop_function_id == loop_function_id, ['foo']] = 0

#             for col in out_df.columns:
#                 print(col, out_df[col])
#                 print(out[out.loop_function_id == loop_function_id][col])
#                 out.loc[out.loop_function_id == loop_function_id, col] = out_df[col]
                
#            print(out.loc[out.loop_function_id == loop_function_id])
#            sys.exit()
#            out=pd.merge(out, out_df, how='left', on=['loop_function_id'])
#            print(out)
#            print(out_df)
#            print("OUT2")
    return out




def summary_report(input, survey):    
    out = pd.DataFrame()
    numeric_in_cols=['thread_count', 'self_time', 'trip_count_total', 'self_all_instructions', 'self_gflops', 'self_gintops', \
                     'self_vector_compute_with_memory', 'self_vector_compute', 'self_vector_memory', 'self_fma', \
                     'self_memory', 'self_loaded_gb', 'self_stored_gb', 'self_l2_loaded_gb','self_l2_stored_gb', \
                     'self_l3_loaded_gb', 'self_l3_stored_gb', 'self_dram_loaded_gb', 'self_dram_stored_gb']
    input[numeric_in_cols]=input[numeric_in_cols].apply(pd.to_numeric, errors='coerce', axis=1)
    out[NAME]=input['source_location']
    out[NUM_CORES]=input['thread_count']
    out[TIME_LOOP_S]=input['self_time']
    time = out[TIME_LOOP_S]
    instrs=input['self_all_instructions']
    out[COUNT_INSTS_GI]=instrs/1e9
    out[RATE_INST_GI_P_S]=out[COUNT_INSTS_GI]/time
    out[RATE_L1_GB_P_S]=(input['self_loaded_gb'] + input['self_stored_gb'])/time
    out[RATE_L2_GB_P_S]=(input['self_l2_loaded_gb'] + input['self_l2_stored_gb'])/time
    out[RATE_L3_GB_P_S]=(input['self_l3_loaded_gb'] + input['self_l3_stored_gb'])/time
    out[RATE_RAM_GB_P_S]=(input['self_dram_loaded_gb'] + input['self_dram_stored_gb'])/time
    out[RATE_LDST_GI_P_S]=input['self_memory']/1e9/time
    out[RATE_FP_GFLOP_P_S]=input['self_gflops']
    out[RATE_INT_GIOP_P_S]=input['self_gintops']
    # Does not have enough information to do Ops normalization
#    out[COUNT_OPS_VEC_PCT]=0
    out[COUNT_INSTS_VEC_PCT]=(input['self_vector_compute']+input['self_vector_memory'])/instrs
#    out[COUNT_OPS_FMA_PCT]=0
    out[COUNT_INSTS_FMA_PCT]=input['self_fma']/instrs
    out['loop_function_id']=input['loop_function_id']

    mask = time > 0

    out = calculate_num_insts(list(input[mask]['loop_function_id']), survey, out)

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
        mydict={k:[v[k] for v in all_rows] for k in keys}
        df=pd.DataFrame.from_dict(mydict)
        # df.to_csv('/tmp/test.csv')

        cur_out=summary_report(df, survey)
        out_df = out_df.append(cur_out, ignore_index=True)

        
    print(out_df)
    out_df.to_csv('/tmp/test.csv')
