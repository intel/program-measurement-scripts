#!/bin/bash

nb_args="$#"
if [[ "$nb_args" != "3" ]]; then
	echo "ERROR! Got $nb_args arguments, expected: source file, function name and output path"
	echo "Got: $*"
	exit -1
fi

# get the absolute path for the arguments
# code_path contains path to folder containing source file
code_path="$(realpath $1)"
function_name="$2"
output_path="$(realpath $3)"

# The output format of ctags is
# <symbol> <type> <line number> <filename> <source>
# So below check for column 1 for function name and then return column 4 which is filename
code_file=$(ctags -x ${code_path}/*  |grep -E "function|subroutine" |awk '$1 == "'${function_name}'" {print $4}')


# fail if the extension does not match expectation
if [[ "$output_path" != *csv ]]; then
	echo "ERROR! $0 generates a CSV file!"
	exit -1
fi

# clean the output path
rm -f $output_path

# validate we're operating with a supported file extension
code_name="$(basename $code_file | tr '[:upper:]' '[:lower:]')" 
#if [[ "$code_name" != *c ]] && [[ "$code_name" != *cc ]] && [[ "$code_name" != *cpp ]]; then
#	exit 0
#fi

if [[ ! -f $code_file ]]; then
    exit 0
fi

# TODO should this come from an environment variable?
utils_path="/share/rose-utils"
unitool_path="${utils_path}/unitool"

if [[ -f "$unitool_path/batch_run.py" ]]; then
    # unitool may be limited to running under its own path
    cd $unitool_path
    # it outputs a csv to stdout, that we redirect to the output path
    unset LD_LIBRARY_PATH
    python3 batch_run.py --rhs $code_file > $output_path
fi
