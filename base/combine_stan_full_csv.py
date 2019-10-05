#!/usr/bin/python3
import io
import os
import re
import csv
import sys
import shlex
import subprocess
from collections import OrderedDict
# get the command line args
lid,loops,iters,fn_name=sys.argv[1:5]
lid=int(lid)
loops=list(map(int, loops.split("\n")))
iters=list(map(int, iters.split("\n")))
loop2iters=dict(zip(loops, iters))
iteration_total = sum(iters)
print(fn_name)

combine={}
rowkeys=[]

for loop in loops:
    tmp_file='{}.stan_full_{}.csv'.format(fn_name, loop)
    with open(tmp_file, 'r') as infile:

        if not combine:
            reader = csv.reader(infile)
            rowkeys=next(reader)
            for row in reader:
                combine=OrderedDict(zip(rowkeys, row))
                for key in rowkeys:
                    if ('Nb' in key) or ('Bytes' in key) or ('cycle' in key) or ('ratio' in key) \
                       or ('OoO' in key) or ('intensity' in key) or ('IPC' in key):
                        try:
                            # Try to convert data to float.  "NA" will fail and pass
                            val = float(combine[key])
                            combine[key]=val*loop2iters[loop]
                        except:
                            pass


        else:
            iters = csv.DictReader(infile, delimiter=',')
            for row in iters:
                for key in row.keys():
                    if ('Nb' in key) or ('Bytes' in key) or ('cycle' in key) or ('ratio' in key) \
                       or ('OoO' in key) or ('intensity' in key) or ('IPC' in key):
                        try:
                            # Try to convert data to float.  "NA" will fail and pass
                            val = float(row[key])
                            combine[key]=combine[key]+val*loop2iters[loop]
                        except:
                            pass

for key in combine.keys():
    if ('Nb' in key) or ('Bytes' in key) or ('cycle' in key) or ('ratio' in key) \
       or ('OoO' in key) or ('intensity' in key) or ('IPC' in key):
        try:
            # Try to convert data to float.  "NA" will fail and pass
            combine[key]=combine[key]/iteration_total
        except:
            pass

# write the composite loop to the STAN file
out_file='{}.stan_full.csv'.format(fn_name)
with open(out_file, mode='w') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=list(rowkeys))
    writer.writeheader()
    writer.writerow(combine)

#    for key in iters.keys():

sys.exit(0)


# if len(sys.argv) <= 4:
#     raise Exception('ERROR! Invalid number of args, usage is: %s <binary> <fn> <data_size> <reps>' % sys.argv[0])
# bin_path, fn_name, data_size, num_reps = sys.argv[1:5]
# bin_fldr = os.path.dirname(bin_path)
# # grab the cls folder and put it into the enviroment (for standalone runs)
# cls_fldr = os.path.dirname(os.path.abspath(__file__))
# os.putenv('CLS_FOLDER', cls_fldr)
# # import the desired variables from const.sh
# wanted = [ 'BASE_PROBE_FOLDER', 'LD_LIBRARY_PATH', 'MAQAO', 'MAQAO_FOLDER', 'DELIM', 'M_DELIM', 'UARCH', 'LOOP_ITER_COUNTER' ]
# com = shlex.split("env bash -c 'source %s && ( set -o posix ; set )'" % (os.path.join(cls_fldr, 'const.sh')))
# proc = subprocess.Popen(com, stdout=subprocess.PIPE)
# for line in io.TextIOWrapper(proc.stdout, encoding='utf-8'):
#     key, _, value = line.partition('=')
#     if key in wanted:
#         globals()[key] = str(value.rstrip())
# assert(not proc.poll())
# # map to a local uarch
# uarchs = {
#     'HASWELL': 'HASWELL',
#     'haswell_server': 'HASWELL',
#     'skylake_server': 'SKYLAKE'
# }
# uarch = uarchs[UARCH] if UARCH in uarchs else 'SANDY_BRIDGE'
# # fall-back on BASH version if not using MAQAO
# if LOOP_ITER_COUNTER != 'MAQAO':
#     print('WARNING! Unsupported loop iteration counter %s. Falling back to BASH version.' % LOOP_ITER_COUNTER, file=sys.stderr)
#     itercntr_path = os.path.join(cls_fldr, 'count_loop_iterations.sh')
#     com = [ itercntr_path, bin_path, fn_name, data_size, num_reps ]
#     print(*com, file=sys.stderr); sys.exit(subprocess.call(com))
# # setup environment
# os.chdir(bin_fldr)
# os.putenv('LD_LIBRARY_PATH', LD_LIBRARY_PATH + os.pathsep + BASE_PROBE_FOLDER)
# write codelet.data if it doesn't exist
# if not os.path.isfile('codelet.data'):
#     with open('codelet.data', 'w') as data_file:
#         data_file.write('%s %s' % (data_size, num_reps))
# # save flag indicates when to save the next line
# save = False
# com = [ MAQAO, 'cqa', 'fct-loops=%s' % fn_name, 'of=csv', 'depth=innermost', 'uarch=%s' % uarch, 'ud=%s/csv_ext_ia32_x86_64_userdata.lua' % MAQAO_FOLDER, bin_path ]
# print(*com, file=sys.stderr)
# proc = subprocess.Popen(com, stdout=sys.stderr)
# assert(not proc.wait())
# open the loops csv file
# with open('%s.csv' % fn_name, 'r') as infile:
#     loops = list(csv.DictReader(infile, delimiter=';'))
# # grab the loop ids
# lids = [ loop['ID'] for loop in loops ]
# # count the iterations across the loops
# tmp_file = "tmp.csv"
# com = [ MAQAO, 'vprof', 'instrument=iterations', 'lid=%s' % (','.join(lids)), 'of=csv', 'op=%s' % tmp_file, bin_path ]
# print(*com, file=sys.stderr)
# proc = subprocess.Popen(com, stdout=sys.stderr)
# assert(not proc.wait())
# # open the iterations csv file
# with open(tmp_file, 'r') as infile:
#     iters = list(csv.DictReader(infile, delimiter=','))
# # helper to find and update the iterations count of a loop
# def update_loop(lid, iteration_total):
#     loop = next(loop for loop in loops if loop['ID'] == lid)
#     loop['iteration_total'] = iteration_total
#     return loop
# # filter out the loops with no iterations and update the counts
# loops = [ update_loop(row['loop_id'], row['iteration_total']) for row in iters if int(row['iteration_total']) ]
# assert(len(loops))
# # count the total number of iterations
# iteration_total = sum(int(row['iteration_total']) for row in iters)
# # create the composite loop (weighted average across metrics)
# composite = {}
# composite['binary_loop.id'] = M_DELIM[1].join(loop['ID'] for loop in loops)
# composite['Iterations'] = iteration_total
# composite['Repetitions'] = num_reps
# for key in loops[0].keys():
#     if ('Nb' in key) or (key == 'Bytes loaded') or (key == 'Bytes stored'):
#         try:
#             composite[key] = sum(int(loop['iteration_total']) * float(loop[key]) for loop in loops) / iteration_total
#         except:
#             composite[key] = float('nan')
# # write the composite loop to the STAN file
# out_file = 'maqao.csv'
with open(out_file, mode='w') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=list(composite.keys()))
    writer.writeheader()
    writer.writerow(composite)
# print the number of iterations
#print(DELIM.join([ composite['binary_loop.id'], str(iteration_total) ]))
