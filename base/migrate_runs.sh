#!/bin/bash

if [[ $# < 5 ]]; then
  echo "Usage: $0 <old cls prefix> <new cls prefix> <old rundir> <new rundir> <run#1> ... <run#n> "
  exit -1
fi

old_prefix=$(readlink -f "$1")
new_prefix=$(readlink -f "$2")
old_rundir=$(readlink -f "$3")
new_rundir=$(readlink -f "$4")
shift 4
runs="$@"

function chk_dir_exist() {
    local dir="$1"
    if [[ ! -d $dir ]]; then
	echo $dir not exist
	exit -1
    fi
}

# 4 cases
# 1) same old/new prefix, same old/new rundir - nothing to do
# 2) same old/new prefix, diff old/new rundir - migrate rundir preserving link to cls_*
# 3) diff old/new prefix, same old/new rundir - migrate cls_* directories, update link to cls_*
# 4) diff old/new prefix, diff old/new rundir - migrate cls_* directories, migrate rundir, update link to cls_*

# Check old/new prefix first , if different (Case 3, Case 4),
#   migrate cls_* and update link to cls_*
# then check old/new rundir , if different (Case 2, Case 4),
#   migrate rundir  preserve link to cls_* (For Case 4, preserving link updated in last step)
# Done (Case 1)

echo "CLS    :: $old_prefix => $new_prefix"
echo "RUNDIR :: $old_rundir => $new_rundir"
echo
# Check directory existence
chk_dir_exist $old_prefix 
chk_dir_exist $old_rundir 

if [[ $old_prefix != $new_prefix ]]; then
# cls_* migration
    mkdir -p $new_prefix
    for run in $runs; do
	cnt_run_dir=$old_rundir/$run
	for cls in $cnt_run_dir/cls*; do
	    real_dir=$(readlink $cls)
	    real_dir_less_prefix=${real_dir#${old_prefix}/}
	    echo "Processing $cls"
	    echo -e "\t\t=> $real_dir_less_prefix"
	    if [[ $real_dir == $real_dir_less_prefix ]]; then
		# skip this one because prefix not match
		echo Skipping $real_dir for mismatched old prefix ${old_prefix}
		continue
	    fi 

	    echo "$real_dir_less_prefix::"
	    echo -e "\t\t$old_prefix => $new_prefix"

	    pushd $old_prefix > /dev/null
	    cp --parents -R $real_dir_less_prefix $new_prefix
	    popd > /dev/null
	    rm $cls
	    ln -s $new_prefix/$real_dir_less_prefix $cls
	    old_real_dir=$old_prefix/$real_dir_less_prefix
	    rm -rf $old_real_dir
	    rmdir --ignore-fail-on-non-empty -p $(dirname $old_real_dir)
	done
    done
fi

if [[ $old_rundir != $new_rundir ]]; then
# rundir migration
    mkdir -p $new_rundir
    pushd $old_rundir > /dev/null
    for run in $runs; do
	cp -R $run $new_rundir/$run
	if [[ $? == 0 ]]; then
	    rm -rf $run
	fi
    done
    popd > /dev/null
    rmdir --ignore-fail-on-non-empty -p $old_rundir
fi
