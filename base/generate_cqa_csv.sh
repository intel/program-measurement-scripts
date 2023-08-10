#!/bin/bash
# By default, CQA always generate ';' separated CSV.  Use this wrapper to invoke CQA to ensure
# the right delimiter is used for CSV format.

source $CLS_FOLDER/const.sh

if [[ "$nb_args" < "3" ]]
then
	echo "ERROR! Invalid arguments (need: cqa uarch, bin_path, loop_id, more_args)."
	exit -1
fi

cqa_uarch="$1"
bin_path="$2"
loop_id="$3"
if [[ "$nb_args" < "4" ]]
then
	more_args="-max-paths=50"
else
	more_args="$4"
fi

# Some previous use cases:
#"$MAQAO" module=cqa uarch="$local_uarch" bin="$bin_folder/$codelet_name" loop=$loop_id   of=csv -ext
#"$MAQAO" module=cqa uarch="$local_uarch" bin="$variant_path"             loop=$lid       of=csv -ext
#"$MAQAO" module=cqa uarch=SANDY_BRIDGE   bin="$bin_path"                 loop="$loop_id" of=csv -ext im=$mode $option_arg

#cmd="$MAQAO" module=cqa uarch="${uarch}" bin="$bin_path" loop="$loop_id" of=csv -ext ${more_args}
cmd="\"$MAQAO\" cqa proc=\"${cqa_uarch}\" bin=\"$bin_path\" loop=\"$loop_id\" of=csv ud=${MAQAO_FOLDER}/csv_ext_ia32_x86_64_userdata.lua -ext ${more_args}"
echo Loop information collection: Executing CMD: \'$cmd\'
bash -c "$cmd"
# Generated loops.csv
cp loops.csv /tmp

if [[ ${DELIM} != ';' ]]
then
	# Only need to do if the desired delimiter is not ';
	# Replace the ${DELIM} by ${CONFLICT_DELIM} first and then replace ';' by ${DELIM}
	#    cat loops.csv | tr ',' '#' | tr ';' ','
	tmpfile=$(mktemp)
	cat loops.csv | tr ${DELIM} ${CONFLICT_DELIM} | tr ';' ${DELIM} > ${tmpfile}
	mv ${tmpfile} loops.csv
fi

# if more than one path, then average all the paths
loops_paths=$(wc -l loops.csv | cut -f1 -d' ')
if (( "$((loops_paths))" > "2" )); then
	echo "Averaging multiple path stats from CQA"
	$CLS_FOLDER/cqa_multipath_combine.py
	mv loops_avg.csv loops.csv
fi

