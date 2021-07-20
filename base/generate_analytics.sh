#!/bin/bash

nb_args="$#"
if [[ "$nb_args" != "2" ]]; then
	echo "ERROR! Got $nb_args arguments, expected: source file and output path"
	exit -1
fi

# get the absolute path for the arguments
code_path="$(realpath $1)"
output_path="$(realpath $2)"

# fail if the extension does not match expectation
if [[ "$output_path" != *csv ]]; then
	echo "ERROR! $0 generates a CSV file!"
	exit -1
fi

# clean the output path
rm -f $output_path

# validate we're operating with a supported file extension
code_name="$(basename $code_path | tr '[:upper:]' '[:lower:]')" 
if [[ "$code_name" != *c ]] && [[ "$code_name" != *cc ]] && [[ "$code_name" != *cpp ]]; then
	exit 0
fi

if [[ ! -f $code_path ]]; then
    exit 0
fi

# TODO should this come from an environment variable?
utils_path="/share/rose-utils"
unitool_path="${utils_path}/unitool"

if [[ -f "$unitool_path/batch_run.py" ]]; then
    # unitool may be limited to running under its own path
    cd $unitool_path
    # it outputs a csv to stdout, that we redirect to the output path
    ./batch_run.py $code_path > $output_path
fi
