#!/bin/bash

source $CLS_FOLDER/const.sh

# MAX_ROWS=30

nb_args=$#

if [[ $nb_args -lt 1 ]]
then
	#	echo "ERROR! Invalid arguments (need: CLS res's folder, real machine name, variants)."
	echo "ERROR! Invalid arguments (need: CLS res's folder)."
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
cpu_nominal_freq_kHz="$(cat $cls_res_folder/nominal_freq_kHz)"

gen_codelet_mach_info () {
	local nr="$1"
	local of="$2"
	echo "application.name"${DELIM}"batch.name"${DELIM}"code.name"${DELIM}"codelet.name"${DELIM}"binary_loop.id"${DELIM}"machine.name"${DELIM}"real.machine.name"> $of
	yes $(echo "$application_name"${DELIM}"$batch_name"${DELIM}"$code_name"${DELIM}"$codelet_name"${DELIM}"$binary_loop_id"${DELIM}"$machine_name"${DELIM}"$real_machine_name") | head -n $nr >> $of
}

gen_filler_info() {
	local nr="$1"
	local of="$2"
	echo "decan_experimental_configuration.instance_id"${DELIM}"decan_experimental_configuration.nb_threads"${DELIM}"Timestamp"${DELIM}"cpu.generation"${DELIM}"cpu.nominal_frequency"${DELIM}"energy.unit"${DELIM}"Expr Timestamp"${DELIM}"TS#"${DELIM}"Expr TS#" > $of
	yes $(echo "$instance_id"${DELIM}"$nb_threads"${DELIM}"$ClsTimestamp"${DELIM}"$cpu_generation"${DELIM}"$cpu_nominal_freq_kHz"${DELIM}"$energy_unit"${DELIM}"$ExprTimestamp"${DELIM}"$cls_timestamp_val"${DELIM}"$run_timestamp_val") | head -n $nr >> $of
}

combine_csv() {
	local files="$1"
	local outcsv="$2"

	if [[ ( -z $files ) || ($(ls $files 2>/dev/null|wc -l) == "0") ]]; then
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

# run the analytics script and generate an analytics file
code_path="$codelet_folder/$code_name"
analytics_file="${cls_res_folder}/${codelet_name}_analytics.csv"
$CLS_FOLDER/generate_analytics.sh $code_path $analytics_file

tmprep=$(mktemp -d --tmpdir=$cur_dir tmp.XXXXXXXXXX)

counter_nv_files=$(find $cls_res_folder -name ${COUNTER_FNAME}'.csv')
combine_csv "$counter_nv_files" $tmprep/counters.csv

cpi_iteration_rep_nv_files=$(echo "$counter_nv_files" |sed 's/'${COUNTER_FNAME}'/cpi_nv/g')
combine_csv "$cpi_iteration_rep_nv_files" $tmprep/cpi_iteration_rep.csv

arguments_files=$(echo "$counter_nv_files" |sed 's/'${COUNTER_FNAME}'/arguments/g')
combine_csv "$arguments_files" $tmprep/arguments.csv

compiler_files=$(echo "$counter_nv_files" |sed 's/'${COUNTER_FNAME}'/compiler/g')
combine_csv "$compiler_files" $tmprep/compiler.csv

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
runinfo_names=,$runinfo_names
echo $runinfo_names
for m in ${!nameMap[@]};
do
	runinfo_names=$(echo "$runinfo_names" |sed 's|,'$m'|;'${nameMap[$m]}'|g')
done
runinfo_names=$(echo "$runinfo_names" |sed 's|;|,|g; s|^,||g')
echo $runinfo_names

echo "$runinfo_names" |uniq > $tmprep/runinfo.csv
echo "$runinfo_values" >> $tmprep/runinfo.csv

#Finally, get the stan report (if any)
# Pickup the variant_... from runinfo and use that to construct the path to stan report
stan_infiles=$(echo "$runinfo" | sed 's|.*/variant_\([^/]*\)/.*|'$cls_res_folder/binaries/${codelet_name}'_\1.stan_full.csv|g')
combine_csv "$stan_infiles" $tmprep/stan.csv

if [ -f $tmprep/stan.csv ]; then
	# Below only fix the first line which is the header
	#stan_names=$(echo $stan_names |sed "s/[ :-]/_/g"|sed "s/_\+/_/g"|sed "s/\[/(/g"|sed "s/\]/)/g") # Also converted various naming of stan metrics to follow final format
	sed -i "1 s/[ :-]/_/g; 1 s/_\+/_/g; 1 s/\[/(/g; 1 s/\]/)/g; 1 s|ADD/SUB|ADD_SUB|g" $tmprep/stan.csv # Converted various naming of stan metrics to follow final format
	# Some renaming of metrics due to difference in CQA output and Oneview outputs
	sed 's/Bytes_if_\([a-zA-Z_]*\)_vectorized_prefetch/Bytes_prefetched_if_\1_vectorized/g' -i $tmprep/stan.csv
	sed 's/Bytes_if_\([a-zA-Z_]*\)_vectorized_load/Bytes_loaded_if_\1_vectorized/g' -i $tmprep/stan.csv
	sed 's/Bytes_if_\([a-zA-Z_]*\)_vectorized_store/Bytes_stored_if_\1_vectorized/g' -i $tmprep/stan.csv
	cp $tmprep/stan.csv /tmp

	echo Extracting stan columns only specified in stan metric file: ${STAN_METRICS_FILE}
	# IFS=$'\n' need_stan_cols=($(cat ${STAN_METRICS_FILE}|sed "s/,/\n/g"))
	IFS=$'\n' need_stan_cols=($(cat ${STAN_METRICS_FILE}))
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
all_csv_files=$(ls -f $tmprep/codelet_mach_info.csv $tmprep/filler_info.csv $tmprep/runinfo.csv $tmprep/arguments.csv $tmprep/compiler.csv $tmprep/pgm.csv $tmprep/cpi_iteration_rep.csv $tmprep/counters.csv $tmprep/stan_trimmed.csv ${analytics_file} 2>/dev/null)
paste -d${DELIM} $all_csv_files > $cape_file

echo Deleting TMPDIR $tmprep
rm -R $tmprep


exit
