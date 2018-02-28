#!/bin/bash

if [[ "$#" -lt 5 ]]; then
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
# First copy cls_*
# Check copy was successful (ie. content the same)
# Update cls links and rm old cls_*.

    mkdir -p $new_prefix

# Copy
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
		exit -1
		continue
	    fi 

	    echo "Copying $real_dir_less_prefix::"
	    echo -e "\t\t$old_prefix => $new_prefix"

	    pushd $old_prefix > /dev/null
	    cp --parents -R $real_dir_less_prefix $new_prefix
	    popd > /dev/null
	done
    done

# Check    
    for run in $runs; do
	cnt_run_dir=$old_rundir/$run
	for cls in $cnt_run_dir/cls*; do
	    real_dir=$(readlink $cls)
	    real_dir_less_prefix=${real_dir#${old_prefix}/}
	    echo "Checking $cls"
	    echo -e "\t\t=> $real_dir_less_prefix"
	    if [[ $real_dir == $real_dir_less_prefix ]]; then
		# skip this one because prefix not match
		echo Skipping $real_dir for mismatched old prefix ${old_prefix}
		exit -1
		continue
	    fi 

	    echo "Checking $real_dir_less_prefix::"
	    echo -e "\t\t$old_prefix => $new_prefix"
	    diff -r $real_dir $new_prefix/$real_dir_less_prefix
	    if [[ $? != 0 ]]; then
		echo "Directory check failed"
		exit -1
	    fi
	done
    done
#Check passed
    for run in $runs; do
	cnt_run_dir=$old_rundir/$run
	for cls in $cnt_run_dir/cls*; do
	    real_dir=$(readlink $cls)
	    real_dir_less_prefix=${real_dir#${old_prefix}/}
	    echo "Switching reference of $cls"
	    echo -e "\t\t=> $real_dir_less_prefix"
	    if [[ $real_dir == $real_dir_less_prefix ]]; then
		# skip this one because prefix not match
		echo Skipping $real_dir for mismatched old prefix ${old_prefix}
		exit -1
		continue
	    fi 

	    echo "$real_dir_less_prefix::"
	    echo -e "\t\t$old_prefix => $new_prefix"

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
# Copy, check, then remove


    mkdir -p $new_rundir
# Copy
    pushd $old_rundir > /dev/null
    for run in $runs; do
	cp -R $run $new_rundir/$run
    done
    popd > /dev/null

# Check
    pushd $old_rundir > /dev/null
    for run in $runs; do
	diff -r $run $new_rundir/$run
	if [[ $? != 0 ]]; then
	    echo "Directory check failed"
	    exit -1
	fi
    done
    popd > /dev/null
# Deleting old directory
    pushd $old_rundir > /dev/null
    for run in $runs; do
	rm -rf $run
    done
    popd > /dev/null
    rmdir --ignore-fail-on-non-empty -p $old_rundir
fi

