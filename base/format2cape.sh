#!/bin/bash

source $CLS_FOLDER/const.sh

# MAX_ROWS=30

nb_args=$#

if [[ $nb_args -lt 1 ]]
then
	echo "ERROR! Invalid arguments (need: CLS res's folder, real machine name, variants)."
#	echo "ERROR! Invalid arguments (need: CLS res's folder)."
	exit -1
fi

# pcr_metrics.sh uses $1
source $CLS_FOLDER/pcr_metrics.sh


# Get codelet's res folder
cls_res_folder=$( readlink -f "$1" )
#real_machine_name="$2"
real_machine_name="$(hostname)"
#variants="$3"
#num_cores="$4"

codelet_folder=$( echo $cls_res_folder | sed 's:/cls_res_.*::' )
#machine_name=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_[0-9]+)/\2/p' )
machine_name=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\2/p' )
cls_timestamp_val=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\4/p' )
run_timestamp_val=$( echo $cls_res_folder | sed -n -E 's/(.*cls_res_)(.*)(_)([0-9]+)(_)([0-9]+)/\6/p' )
#machine_name="$2"
ClsTimestamp=$( date -d @${cls_timestamp_val} +'%F %T' )
ExprTimestamp=$( date -d @${run_timestamp_val} +'%F %T' )

DATE=$( date +'%F_%T' )

echo "format2cape.sh invoked under res folder: ${cls_res_folder}"

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
num_core="0"
arg1=" "
arg2=" "
arg3=" "
arg4=" "
arg5=" "
arg6=" "
nb_threads=" "
# follow constants are used below to start picking up counter data in counter.csv (including the CPI column), datasize, numcore, iteration and repetition respectively.
# This is hardcoded and related to cpi.csv generation in run_codelet.sh and cpi.csv is copied to counters.csv in format_counters.sh
# TODO: avoid hardcoding
BEGIN_COUNTER_DATA_COLS=9
DATASIZE_COL=2
ITERATIONS_COL=6
REPETITIONS_COL=7
NUMCORE_COL=5

cpu_generation="$(cat $cls_res_folder/uarch)"
energy_unit="$(cat $cls_res_folder/energy_units)"


gen_codelet_mach_info () {
    local nr="$1"
    local of="$2"
    echo "application.name"${DELIM}"batch.name"${DELIM}"code.name"${DELIM}"codelet.name"${DELIM}"binary_loop.id"${DELIM}"machine.name"${DELIM}"real.machine.name"> $of
    yes $(echo "$application_name"${DELIM}"$batch_name"${DELIM}"$code_name"${DELIM}"$codelet_name"${DELIM}"$binary_loop_id"${DELIM}"$machine_name"${DELIM}"$real_machine_name") | head -n $nr >> $of
}

gen_filler_info() {
   local nr="$1"
   local of="$2"
   echo "decan_experimental_configuration.instance_id"${DELIM}"decan_experimental_configuration.nb_threads"${DELIM}"Timestamp"${DELIM}"cpu.generation"${DELIM}"energy.unit"${DELIM}"Expr Timestamp"${DELIM}"TS#"${DELIM}"Expr TS#" > $of
   yes $(echo "$instance_id"${DELIM}"$nb_threads"${DELIM}"$ClsTimestamp"${DELIM}"$cpu_generation"${DELIM}"$energy_unit"${DELIM}"$ExprTimestamp"${DELIM}"$cls_timestamp_val"${DELIM}"$run_timestamp_val") | head -n $nr >> $of
}

combine_csv() {
    local files="$1"
    local outcsv="$2"

    if [[ $(ls $files 2>/dev/null|wc -l) == "0" ]]; then
	# no file, nothing to do, don't generate $outcsv
	return
    fi

    names=$(head -1 -q $files|uniq)
    if [[ $(echo "$names" | wc -l) != "1" ]]
    then
	echo "Unexpected corrupted csv data collection, exiting"
	exit -1
    fi
    echo "$names" > $outcsv
    blanks=$(echo "$names"|sed "s/[^'${DELIM}']//g")
    # below need to be fault tolerance to insert empty rows for empty data
    for f in $files; do
	values=$(tail -n +2 -q $f)
	if [ x"$values" != x ]; then
	    echo "$values" >> $outcsv
	else
	    echo "$blanks" >> $outcsv
	fi
    done
}

tmprep=$(mktemp -d --tmpdir=$cur_dir tmp.XXXXXXXXXX)

counter_nv_files=$(find $cls_res_folder -name ${COUNTER_FNAME}'.csv')
combine_csv "$counter_nv_files" $tmprep/counters.csv

cpi_iteration_rep_nv_files=$(echo "$counter_nv_files" |sed 's/'${COUNTER_FNAME}'/cpi_nv/g')
combine_csv "$cpi_iteration_rep_nv_files" $tmprep/cpi_iteration_rep.csv

pgm_metrics_files=$(echo "$counter_nv_files" |sed 's/'${COUNTER_FNAME}'/pgm_metrics/g')
combine_csv "$pgm_metrics_files" $tmprep/pgm.csv

# <same repeated machine/filler info> below
num_rows=$(echo "$counter_nv_files" | wc -l)
gen_codelet_mach_info $num_rows $tmprep/codelet_mach_info.csv
gen_filler_info $num_rows $tmprep/filler_info.csv # including timestamp and cpu generation info

# <per run setting info> below, collected from path to counter value files
runinfo=$(echo "$counter_nv_files" |sed 's|'$cls_res_folder'||g')  # Used '|' as delimiter as cls_res_folder contains slash
runinfo=$(echo "$runinfo" |sed 's|/'${COUNTER_FNAME}'\.csv||g') 
runinfo_values=$(echo "$runinfo" |sed 's|/[^_]*_|,|g'|sed 's|^,||g')  # get rid of <setting name>_, then leading comma

runinfo_names=$(echo "$runinfo" |sed 's|_[^/]*|,|g' |sed 's|/||g' | sed 's|,$||g')  # get rid of _<setting value> , then remove slashes and last comma
# convert name using map defined in const.sh
for m in ${!nameMap[@]};
do
    runinfo_names=$(echo "$runinfo_names" |sed 's|'$m'|'${nameMap[$m]}'|g')
done


echo "$runinfo_names" |uniq > $tmprep/runinfo.csv
echo "$runinfo_values" >> $tmprep/runinfo.csv
 
#Finally, get the stan report (if any)
# Pickup the variant_... from runinfo and use that to construct the path to stan report
stan_infiles=$(echo "$runinfo" | sed 's|.*/variant_\([^/]*\)/.*|'$cls_res_folder/binaries/${codelet_name}'_\1.stan_full.csv|g')
combine_csv "$stan_infiles" $tmprep/stan.csv

if [ -f $tmprep/stan.csv ]; then
    # Below only fix the first line which is the header
    #stan_names=$(echo $stan_names |sed "s/[ :-]/_/g"|sed "s/_\+/_/g"|sed "s/\[/(/g"|sed "s/\]/)/g") # Also converted various naming of stan metrics to follow final format
    sed -i "1 s/[ :-]/_/g; 1 s/_\+/_/g; 1 s/\[/(/g; 1 s/\]/)/g" $tmprep/stan.csv # Converted various naming of stan metrics to follow final format


    echo Extracting stan columns only specified in stan metric file: ${STAN_METRICS_FILE}
    IFS=$'\n' need_stan_cols=($(cat ${STAN_METRICS_FILE}|sed "s/,/\n/g"))
    IFS=$'\n' stan_cols_in_file=($(head -1 $tmprep/stan.csv|sed "s/,/\n/g")) # Also converted various naming of stan metrics to follow final format
    declare -A stan_col_index
    si=0
    while [ $si -lt ${#stan_cols_in_file[@]} ]
    do
	#    echo ${stan_cols_in_file[$si]} is $si
	(( stan_col_index[${stan_cols_in_file[$si]}]=si+1 ))  # indendedly using the si+1 because cut indices starts from 1
	(( si++ ))
    done
    #echo "TRIMMING STAN FLIE"
    #Use the index to find out the indices of needed stan cols
    need_indices=()
    echo > $tmprep/stan_trimmed.csv
    for sc in ${need_stan_cols[@]}
    do
	idx=${stan_col_index[$sc]}
	#    echo $sc is $idx
	if [ x"$idx" != x ]; then
	    # Idx not empty
	    paste -d${DELIM} $tmprep/stan_trimmed.csv <(cut -d${DELIM} -f$idx $tmprep/stan.csv) > $tmprep/tmp.csv
	    mv $tmprep/tmp.csv $tmprep/stan_trimmed.csv
	fi
    done 
    sed -i "s/^,//g" $tmprep/stan_trimmed.csv # Remove the leading comma
fi


# format is pretty much:
#   <same repeated machine/filler info> <per run setting obtained from run_info> <counters> <stan data>
# Collect all csv files skipping non-existing files
all_csv_files=$(ls  -f $tmprep/codelet_mach_info.csv $tmprep/filler_info.csv $tmprep/runinfo.csv $tmprep/pgm.csv $tmprep/cpi_iteration_rep.csv $tmprep/counters.csv $tmprep/stan_trimmed.csv 2>/dev/null)
paste -d${DELIM} $all_csv_files > $cape_file

echo Deleting TMPDIR $tmprep
rm -R $tmprep


exit
# Old code below to be deleted later


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





for variant in $variants
do
	# Building the stan metrics section
	stan_infile="$cls_res_folder/binaries/${codelet_name}_${variant}.stan_full.csv"
	if [ -f $stan_infile ]; then
	    #	cp $stan_infile /tmp/xxx
	    cat $stan_infile | sed -n '1p;11p'  | tr ${DELIM} '\n' | tr "=" ":"  > $tmprep/stanh.csv			
	    #	cp $tmprep/stanh.csv /tmp/yyy
	    cat $stan_infile | sed -n '2p;12p'  | tr ${DELIM} '\n'               > $tmprep/stanv.csv
	    #	cp $tmprep/stanv.csv /tmp/zzz
	else
	    # Create dummy empty file so below will have all metrics becoming zero
	    touch $tmprep/stanh.csv $tmprep/stanv.csv
	fi

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

    
    for path_to_counter in $(find $cls_res_folder -name 'counter_values.csv')
    do
	counter_dir=$(dirname $path_to_counter)
	run_info=${counter_dir#$cls_res_folder}
	echo ri $run_info
	echo $run_info |sed 's/\/[^_]*_/'${DELIM}'/g'  # remove the ..._ part and replaced by ${DELIM}
    done
	

    for variant in $variants
    do
	#	cp $tmprep/stan_report_${variant}.csv /tmp/tt2
	for frequency in $frequency_list
	do
	    for num_core in $num_cores
	    do
		infile=$cls_res_folder/counters/"counters_"$variant"_0MBs_"$frequency"kHz_${num_core}cores.csv"
		outfile=$tmprep/$codelet_name"_counters_"$variant"_0MBs_"$frequency"kHz_${num_core}cores.csv"

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
#		cat $infile | grep $codelet_name | sed '$ d' | cut -d${DELIM} -f ${BEGIN_COUNTER_DATA_COLS}-$ncols  >> $tmprep/counters.csv
		# Slightly diff implmeentation than above line which assume last line is the extra line 
		# with codelet name, which will fail if we ignore loop detection error and don't dump assembly
		cat $infile | grep ${codelet_name}${DELIM} | cut -d${DELIM} -f ${BEGIN_COUNTER_DATA_COLS}-$ncols  >> $tmprep/counters.csv
		nrows=$(tail -n +2 $tmprep/counters.csv | wc -l)
		# Merging the stan and counters sections

		gen_codelet_mach_info $nrows $tmprep/codelet_mach_info.csv
		# echo "application.name"${DELIM}"batch.name"${DELIM}"code.name"${DELIM}"codelet.name"${DELIM}"binary_loop.id"${DELIM}"decan_variant.name"${DELIM}"machine.name"${DELIM}"real.machine.name"> $tmprep/codelet_mach_info.csv
		# yes $(echo "$application_name"${DELIM}"$batch_name"${DELIM}"$code_name"${DELIM}"$codelet_name"${DELIM}"$binary_loop_id"${DELIM}"$variant"${DELIM}"$machine_name"${DELIM}"$real_machine_name") | head -n $nrows >> $tmprep/codelet_mach_info.csv

		echo "decan_experimental_configuration.data_size"${DELIM}"decan_experimental_configuration.num_core"${DELIM}"Iterations"${DELIM}"Repetitions" > $tmprep/ds_itr_rep_cols.csv
		cat $infile | cut -d${DELIM} -f${DATASIZE_COL},${NUMCORE_COL},${ITERATIONS_COL},${REPETITIONS_COL} | tail -n +2 | head -n $nrows >> $tmprep/ds_itr_rep_cols.csv

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

    done
    head -n 1     $tmprep/${codelet_name}_counters_${variant}_0MBs_${frequency}kHz_${num_core}cores.csv > ${cape_file}

    tail -q -n +2 $tmprep/${codelet_name}_counters_*_0MBs_*kHz_*cores.csv >> ${cape_file}
fi

rm -R $tmprep
