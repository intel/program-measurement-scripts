#!/bin/bash

source const.sh

# MAX_ROWS=30

nb_args=$#

if [[ $nb_args -lt 3 ]]
then
	echo "ERROR! Invalid arguments (need: CLS res's folder, real machine name, variants)."
#	echo "ERROR! Invalid arguments (need: CLS res's folder)."
	exit -1
fi

# pcr_metrics.sh uses $1
source pcr_metrics.sh


# Get codelet's res folder
cls_res_folder=$( readlink -f "$1" )
real_machine_name="$2"
variants="$3"

codelet_folder=$( echo $cls_res_folder | sed 's:/cls_res_.*::' )
#machine_name=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_[0-9]+)/\2/p' )
machine_name=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\2/p' )
cls_timestamp_val=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\4/p' )
run_timestamp_val=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\6/p' )
#machine_name="$2"
ClsTimestamp=$( date -d @${cls_timestamp_val} +'%F %T' )
ExprTimestamp=$( date -d @${run_timestamp_val} +'%F %T' )

DATE=$( date +'%F_%T' )

echo "run format2cape.sh at res folder: ${cls_res_folder}"

# Set meta data of codelet
codelet_meta="$codelet_folder/codelet.meta"
application_name=$(grep "application name" $codelet_meta | cut -d'=' -f2)
batch_name=$(grep "batch name" $codelet_meta | cut -d'=' -f2)
code_name=$(grep "code name" $codelet_meta | cut -d'=' -f2)
codelet_name=$(grep "codelet name" $codelet_meta | cut -d'=' -f2)
#cape_file=${cls_res_folder}/counters/${codelet_name}_metrics.cape.csv
cape_file=${cls_res_folder}/${codelet_name}_metrics.cape.csv
function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )_

# Set general metrics
binary_loop_id="$( cat $cls_res_folder/loop_id)"
instance_id=" "
memory_load="0"
arg1=" "
arg2=" "
arg3=" "
arg4=" "
arg5=" "
arg6=" "
nb_threads=" "
# follow constants are used below to start picking up counter data in counter.csv (including the CPI column), datasize, iteration and repetition respectively.
# This is hardcoded and related to cpi.csv generation in run_codelet.sh and cpi.csv is copied to counters.csv in format_counters.sh
# TODO: avoid hardcoding
BEGIN_COUNTER_DATA_COLS=8
DATASIZE_COL=2
ITERATIONS_COL=5
REPETITIONS_COL=6

cpu_generation="$(cat $cls_res_folder/uarch)"


gen_codelet_mach_info () {
    local nr="$1"
    local of="$2"
    echo "application.name"${DELIM}"batch.name"${DELIM}"code.name"${DELIM}"codelet.name"${DELIM}"binary_loop.id"${DELIM}"decan_variant.name"${DELIM}"machine.name"${DELIM}"real.machine.name"> $of
    yes $(echo "$application_name"${DELIM}"$batch_name"${DELIM}"$code_name"${DELIM}"$codelet_name"${DELIM}"$binary_loop_id"${DELIM}"$variant"${DELIM}"$machine_name"${DELIM}"$real_machine_name") | head -n $nr >> $of
}

# Get variant and frequency lists
for variant in "$cls_res_folder"/data_*/memload_*/freq_*/variant_*
do
	some_variant_path="$variant"
	variant=$( basename "$variant" )
#	variant_list=$( echo -e "$variant\n$variant_list" )
done
#variant_list=$( echo "$variant_list" | sort --uniq | tr "\n" " " | sed "s/variant_//g" )


cur_dir="$PWD"
#tmprep=$cur_dir/tmp
#mkdir -p $tmprep


tmprep=$(mktemp -d --tmpdir=$cur_dir tmp.XXXXXXXXXX)


for variant in $variants
do
	# Building the stan metrics section
	stan_infile="$cls_res_folder/binaries/${codelet_name}_${variant}.stan_full.csv"
#	cp $stan_infile /tmp/xxx
	cat $stan_infile | sed -n '1p;11p'  | tr ${DELIM} '\n' | tr "=" ":"  > $tmprep/stanh.csv			
#	cp $tmprep/stanh.csv /tmp/yyy
	cat $stan_infile | sed -n '2p;12p'  | tr ${DELIM} '\n'               > $tmprep/stanv.csv
#	cp $tmprep/stanv.csv /tmp/zzz
	cat $tmprep/stanh.csv | sed 's/ /_/g' | sed 's/,//g' | sed 's/\[/(/g'	| sed 's/\]/)/g' | sed 's/-/_/g' | sed 's/\.//g' | sed 's/:/_/g' | sed 's/__/_/g' | sed 's/__/_/g' | sed 's/__/_/g'| sed 's/__/_/g'	|sed 's/__/_/g' > $tmprep/tmp.csv
#	cp $tmprep/tmp.csv /tmp/aaa
	mv $tmprep/tmp.csv $tmprep/stanh.csv
	paste -d${DELIM} $tmprep/stanh.csv $tmprep/stanv.csv > $tmprep/stan.csv
#	cp $tmprep/stan.csv /tmp/bbb
	# Note the ',' is hardcoded here because ${STAN_METRICS_FILE} was hardcoded to use ',' as delimiters
	nbsm=$(cat ${STAN_METRICS_FILE} | tr ',' '\n' | wc -l )
	stan_metric=""
	for ((m=1; m<=$nbsm; m++))
	do
		metric_name=$(cat ${STAN_METRICS_FILE} | cut -d',' -f $m)
#		cp $tmprep/stan.csv /tmp/ttt${m}
		metric_value=$(cat $tmprep/stan.csv | grep -w "^$metric_name" | cut -d${DELIM} -f2 | tr ',' '&')
		if [[ "$metric_value" == "" ]] ; then
			stan_metric="$stan_metric"${DELIM}"0"
		else
			metric_value=$(echo $metric_value | sed 's/NA/0/g')
			stan_metric="$stan_metric"${DELIM}"$metric_value"
		fi
	done

	if [[ "$DELIM" != "," ]]
	    then
	    cat ${STAN_METRICS_FILE} | tr ${DELIM} ${CONFLICT_DELIM} | tr ',' ${DELIM} > $tmprep/stan_report_${variant}.h.csv
	else
	    cat ${STAN_METRICS_FILE}  > $tmprep/stan_report_${variant}.h.csv
	fi
	stan_metric=$( echo $stan_metric | sed 's/'${DELIM}'\(.*\)/\1/')
	echo $stan_metric > $tmprep/stan_report_${variant}.v.csv
	#yes $stan_metric | head -n $nrows >> $tmprep/stan_report_${variant}.csv
#	yes $stan_metric | head -n $MAX_ROWS >> $tmprep/stan_report_${variant}.csv
done

if [[ ${ACTIVATE_EXPERIMENTS} == "0" ]]
then
    for variant in $variants
    do
	outfile=$tmprep/$codelet_name"_norun_"$variant".csv"
	gen_codelet_mach_info 1 $tmprep/codelet_mach_info.csv

	echo "Timestamp"${DELIM}"cpu.generation"${DELIM}"Expr Timestamp"${DELIM}"TS#"${DELIM}"Expr TS#" > $tmprep/decan_cpu_run_info.csv
	echo "$ClsTimestamp"${DELIM}"$cpu_generation"${DELIM}"$ExprTimestamp"${DELIM}"$cls_timestamp_val"${DELIM}"$run_timestamp_val" >> $tmprep/decan_cpu_run_info.csv

	paste -d${DELIM} $tmprep/codelet_mach_info.csv $tmprep/decan_cpu_run_info.csv > $tmprep/codelet_struct.csv  

	cat $tmprep/stan_report_${variant}.h.csv > $tmprep/stan_report_${variant}.csv
	#		yes $stan_metric | head -n $nrows >> $tmprep/stan_report_${variant}.csv
	cat $tmprep/stan_report_${variant}.v.csv  >> $tmprep/stan_report_${variant}.csv

	paste -d${DELIM} $tmprep/codelet_struct.csv $tmprep/stan_report_${variant}.csv > $outfile
    done
    head -n 1     $tmprep/${codelet_name}_norun_${variant}.csv > ${cape_file}
    tail -q -n +2 $tmprep/${codelet_name}_norun_*.csv >> ${cape_file}
else
    #frequency_list=$(ls $cls_res_folder/counters/counters_*kHz.csv | sed 's:.*MBs_::;s:kHz.csv::' | sort --uniq)
    # use cpi instead as we may not enable counters
    frequency_list=$(ls $cls_res_folder/cpis/cpi_*kHz.csv | sed 's:.*MBs_::;s:kHz.csv::' | sort --uniq)

    for variant in $variants
    do
	#	cp $tmprep/stan_report_${variant}.csv /tmp/tt2
	for frequency in $frequency_list
	do
	    infile=$cls_res_folder/counters/"counters_"$variant"_0MBs_"$frequency"kHz.csv"
	    outfile=$tmprep/$codelet_name"_counters_"$variant"_0MBs_"$frequency"kHz.csv"

	    # Building the counters metrics section
	    ncols=$(head -n 1 $infile | tr ${DELIM} '\n' | wc -l)
	    #		converted_metrics=$(convert_metric $( head -n 1 $infile | cut -d${DELIM} -f6 ))
	    converted_metrics=()
	    for ((m=${BEGIN_COUNTER_DATA_COLS}; m<=$ncols; m++))
	    do
		metric=$(head -n 1 $infile | cut -d${DELIM} -f $m)
		metric=$( convert_metric $metric )
		#			converted_metrics="$converted_metrics $metric"
		converted_metrics+=($metric)
	    done
	    #		echo $converted_metrics | tr ' ' ','                     > $tmprep/counters.csv
	    #		echo $converted_metrics | tr ' ' ${DELIM}                     > $tmprep/counters.csv
	    # See http://mywiki.wooledge.org/BashFAQ/100 for info of this trick to convert array to delimited string
	    (IFS=${DELIM}; echo "${converted_metrics[*]}")           > $tmprep/counters.csv
	    #tail -n +2 $infile | cut -d${DELIM} -f 6-$ncols | tr ';' ',' >> $tmprep/counters.csv
	    #		cat $infile | grep $codelet_name | sed '$ d' | cut -d';' -f 6-$ncols | tr ';' ',' >> $tmprep/counters.csv
	    cat $infile | grep $codelet_name | sed '$ d' | cut -d${DELIM} -f ${BEGIN_COUNTER_DATA_COLS}-$ncols  >> $tmprep/counters.csv
	    nrows=$(tail -n +2 $tmprep/counters.csv | wc -l)
	    # Merging the stan and counters sections

	    gen_codelet_mach_info $nrows $tmprep/codelet_mach_info.csv
	    # echo "application.name"${DELIM}"batch.name"${DELIM}"code.name"${DELIM}"codelet.name"${DELIM}"binary_loop.id"${DELIM}"decan_variant.name"${DELIM}"machine.name"${DELIM}"real.machine.name"> $tmprep/codelet_mach_info.csv
	    # yes $(echo "$application_name"${DELIM}"$batch_name"${DELIM}"$code_name"${DELIM}"$codelet_name"${DELIM}"$binary_loop_id"${DELIM}"$variant"${DELIM}"$machine_name"${DELIM}"$real_machine_name") | head -n $nrows >> $tmprep/codelet_mach_info.csv

	    echo "decan_experimental_configuration.data_size"${DELIM}"Iterations"${DELIM}"Repetitions" > $tmprep/ds_itr_rep_cols.csv
	    cat $infile | cut -d${DELIM} -f${DATASIZE_COL},${ITERATIONS_COL},${REPETITIONS_COL} | tail -n +2 | head -n $nrows >> $tmprep/ds_itr_rep_cols.csv

	    echo "decan_experimental_configuration.instance_id"${DELIM}"decan_experimental_configuration.frequency"${DELIM}"decan_experimental_configuration.memory_load"${DELIM}"decan_experimental_configuration.arg1"${DELIM}"decan_experimental_configuration.arg2"${DELIM}"decan_experimental_configuration.arg3"${DELIM}"decan_experimental_configuration.arg4"${DELIM}"decan_experimental_configuration.arg5"${DELIM}"decan_experimental_configuration.arg6"${DELIM}"decan_experimental_configuration.nb_threads"${DELIM}"Timestamp"${DELIM}"cpu.generation"${DELIM}"Expr Timestamp"${DELIM}"TS#"${DELIM}"Expr TS#" > $tmprep/decan_cpu_run_info.csv
	    yes $(echo "$instance_id"${DELIM}"$frequency"${DELIM}"$memory_load"${DELIM}"$arg1"${DELIM}"$arg2"${DELIM}"$arg3"${DELIM}"$arg4"${DELIM}"$arg5"${DELIM}"$arg6"${DELIM}"$nb_threads"${DELIM}"$ClsTimestamp"${DELIM}"$cpu_generation"${DELIM}"$ExprTimestamp"${DELIM}"$cls_timestamp_val"${DELIM}"$run_timestamp_val") | head -n $nrows >> $tmprep/decan_cpu_run_info.csv


	    paste -d${DELIM} $tmprep/codelet_mach_info.csv $tmprep/ds_itr_rep_cols.csv $tmprep/decan_cpu_run_info.csv > $tmprep/codelet_struct.csv  

	    cat $tmprep/stan_report_${variant}.h.csv > $tmprep/stan_report_${variant}.csv
	    #		yes $stan_metric | head -n $nrows >> $tmprep/stan_report_${variant}.csv
	    yes $(cat $tmprep/stan_report_${variant}.v.csv) | head -n $nrows >> $tmprep/stan_report_${variant}.csv

	    paste -d${DELIM} $tmprep/codelet_struct.csv $tmprep/counters.csv $tmprep/stan_report_${variant}.csv > $outfile


	    #		extra_rows=$(($nrows + 2))
	    #		cp $tmprep/stan_report_${variant}.csv /tmp/tt
	    # Following ',' is not delimiter
	    #	    sed -i "$extra_rows,$ d" $outfile


	done

    done
    head -n 1     $tmprep/${codelet_name}_counters_${variant}_0MBs_${frequency}kHz.csv > ${cape_file}
    tail -q -n +2 $tmprep/${codelet_name}_counters_*_0MBs_*kHz.csv >> ${cape_file}
fi

rm -R $tmprep
