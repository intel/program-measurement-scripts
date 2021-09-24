import sys
import stat
import subprocess
import parse
import os
import socket
from Cheetah.Template import Template
from argparse import ArgumentParser, FileType
from pathlib import Path

def is_executable(parser, arg):
  if os.access(arg, os.X_OK):
    return arg
  else:
    parser.error(f'Invalid executable file {arg}')

def is_directory(parser, arg):
  if os.path.isdir(arg):
    return arg
  else:
    parser.error(f'Invalid source directory tree {arg}')

def main(argv): 
  cmdParser = ArgumentParser(description='Generate CapeScript run scripts')
  cmdParser.add_argument('--script-name', nargs='?', help='the name of run', required=True, dest='name')
  group = cmdParser.add_mutually_exclusive_group(required=True)
  group.add_argument('--binary', type=lambda x: is_executable(cmdParser, x), metavar="EXECUTABLE", nargs='?', help='the path to binary to run', dest='binary_path')
  group.add_argument('--source-tree', type=lambda x: is_directory(cmdParser, x), metavar="DIRECTORY", nargs='?', help='the path to source tree', dest='source_tree_path')
  cmdParser.add_argument('--run-cmd', nargs='?', help='the run command', required=True, dest='cmd')
  cmdParser.add_argument('--app-name', nargs='?', help='the application name of this run', required=True, dest='app_name')
  cmdParser.add_argument('--batch-name', nargs='?', help='the name of batch of this run', required=True, dest='batch_name')
  cmdParser.add_argument('--kernel-function-name', nargs='?', help='the name of function containing the kernel to measure', required=True, dest='kernel_function_name')
  #cmdParser.add_argument('--parameters', action='append', help='the parameters for runs', dest='params')
  cmdParser.add_argument('--counters', nargs='+', help='the performance counters to collect for runs', dest='counters', 
    choices=['resource', 'sq', 'sq_histogram', 'topdown', 'lfb', 'mem_rowbuff', 'mem_traffic', 'mem_hit', 'tlb', 'lsd'], default=[])
  cmdParser.add_argument('--parameters', nargs='+', help='the parameters for runs', dest='params')


  cpufreq = subprocess.check_output('cpufreq-info -f', shell=True).decode('utf-8').strip()
  args = cmdParser.parse_args()
  hostname = socket.gethostname()
  script_dir=os.path.dirname(os.path.realpath(__file__))
  vrun_dir=os.path.join(script_dir, 'vrun')
  template_dir=os.path.join(vrun_dir, 'templates')

  vars=[]
  values=dict()
  for param in args.params:
    parsed = parse.parse('{PARAM}={VALUE}', param)
    vars += parsed['PARAM']
    values[parsed['PARAM']]=parsed['VALUE'].split(',')

  template_file = 'run_built_binary_fn.template' if args.binary_path else 'build_and_run_binary_fn.template'

  names = {
    'vars': vars, 'var_values': values, 'run_cmd': args.cmd, 
    'cpu_freq': cpufreq, 
    'app_name': args.app_name, 'batch_name': args.batch_name,
    'kernel_function': args.kernel_function_name, 'counters': args.counters,
    'template_dir': template_dir, 'template_file': template_file
    }
  commonClass = Template.compile(file=os.path.join(template_dir,'common.tmpl'))
  if args.binary_path:
    names.update({ 'binary': os.path.basename(args.binary_path), 'binary_path': args.binary_path })
    templateClass = commonClass.subclass(file=os.path.join(template_dir,'run_built_binary.tmpl'))
  else:
    #for path in Path(args.source_tree_path).rglob('codelet.conf'):
    #  print(path.parent.match('**/cls_res_*/**'))
    #  print(path)
    #  print(path.parent.name)
    #binaries = [path.parent.name for path in Path(args.source_tree_path).rglob('codelet.conf') if not path.parent.match('**/cls_res_*/**')]
    binary_to_path = {path.parent.name:path.parent for path in Path(args.source_tree_path).rglob('codelet.conf') if not path.parent.match('**/cls_res_*/**')}
    binaries = binary_to_path.keys()
    names.update({ 'binaries': binaries, 'source_tree_path': args.source_tree_path, 'binary_to_path': binary_to_path})
    templateClass = commonClass.subclass(file=os.path.join(template_dir,'build_and_run_binary.tmpl'))

  templateDef=templateClass(searchList=[names])

  outfile_name = os.path.join(vrun_dir, f'vrun_{hostname}_{args.name}.sh')
  print(f'Generated run script: {outfile_name}')
  print(templateDef, file=open(outfile_name, 'w'))
  os.chmod(outfile_name, stat.S_IRWXU)
  pass

if __name__ == "__main__": 
  main(sys.argv[1:])