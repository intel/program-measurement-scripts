#!/bin/bash

source const.sh

MAX_ROWS=30

nb_args=$#

if [[ $nb_args -lt 2 ]]
then
	echo "ERROR! Invalid arguments (need: CLS res's folder, machine name)."
	exit -1
fi

# pcr_metrics.sh uses $1
source pcr_metrics.sh

# Get codelet's res folder
cls_res_folder=$( readlink -f "$1" )
codelet_folder=$( echo $cls_res_folder | sed 's:/cls_res_.*::' )
machine_name="$2"

DATE=$( date +'%F_%T' )

# Set meta data of codelet
codelet_meta="$codelet_folder/codelet.meta"
application_name=$(grep "application name" $codelet_meta | cut -d'=' -f2)
batch_name=$(grep "batch name" $codelet_meta | cut -d'=' -f2)
code_name=$(grep "code name" $codelet_meta | cut -d'=' -f2)
codelet_name=$(grep "codelet name" $codelet_meta | cut -d'=' -f2)
cape_file=${cls_res_folder}/counters/${codelet_name}_metrics.cape
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
Timestamp="2015-02-02 11:00:00"
cpu_generation="$(cat $cls_res_folder/uarch)"

# Get variant and frequency lists
for variant in "$cls_res_folder"/data_*/memload_*/freq_*/variant_*
do
	some_variant_path="$variant"
	variant=$( basename "$variant" )
	variant_list=$( echo -e "$variant\n$variant_list" )
done
variant_list=$( echo "$variant_list" | sort --uniq | tr "\n" " " | sed "s/variant_//g" )
frequency_list=$(ls $cls_res_folder/counters/counters_*kHz.csv | sed 's:.*MBs_::;s:kHz.csv::' | sort --uniq)


cur_dir="$PWD"
tmprep=$cur_dir/tmp
mkdir -p $tmprep

for variant in $variant_list
do

	# Building the stan metrics section
	stan_infile="$cls_res_folder/binaries/${codelet_name}_${variant}.stan_full.csv"
	cat $stan_infile | sed -n '1p;11p'  | tr ';' '\n' | tr "=" ":"  > $tmprep/stanh.csv			
	cat $stan_infile | sed -n '2p;12p'  | tr ';' '\n'               > $tmprep/stanv.csv
	cat $tmprep/stanh.csv | sed 's/ /_/g' | sed 's/,//g' | sed 's/\[/(/g'	| sed 's/\]/)/g' | sed 's/-/_/g' | sed 's/\.//g' | sed 's/:/_/g' | sed 's/__/_/g' | sed 's/__/_/g' | sed 's/__/_/g'| sed 's/__/_/g'	|sed 's/__/_/g' > $tmprep/tmp.csv
	mv $tmprep/tmp.csv $tmprep/stanh.csv
	paste -d';' $tmprep/stanh.csv $tmprep/stanv.csv > $tmprep/stan.csv
 
	nbsm=$(cat ${STAN_METRICS_FILE} | tr ',' '\n' | wc -l )
	stan_metric=""
	for ((m=1; m<=$nbsm; m++))
	do
		metric_name=$(cat ${STAN_METRICS_FILE} | cut -d',' -f $m)
		metric_value=$(cat $tmprep/stan.csv | grep -w "^$metric_name" | cut -d';' -f2 | tr ',' '&')
		if [[ "$metric_value" == "" ]] ; then
			stan_metric="$stan_metric,0"
		else
			metric_value=$(echo $metric_value | sed 's/NA/0/g')
			stan_metric="$stan_metric,$metric_value"
		fi
	done

	cat ${STAN_METRICS_FILE} > $tmprep/stan_report_${variant}.csv
	stan_metric=$( echo $stan_metric | sed 's/,\(.*\)/\1/')
	#yes $stan_metric | head -n $nrows >> $tmprep/stan_report_${variant}.csv
	yes $stan_metric | head -n $MAX_ROWS >> $tmprep/stan_report_${variant}.csv

	for frequency in $frequency_list
	do
		infile=$cls_res_folder/counters/"counters_"$variant"_0MBs_"$frequency"kHz.csv"
		outfile=$tmprep/$codelet_name"_counters_"$variant"_0MBs_"$frequency"kHz.csv"

		# Building the counters metrics section
		ncols=$(head -n 1 $infile | tr ';' '\n' | wc -l)
		converted_metrics=$(convert_metric $( head -n 1 $infile | cut -d';' -f6 ))
		for ((m=7; m<=$ncols; m++))
		do
			metric=$(head -n 1 $infile | cut -d';' -f $m)
			metric=$( convert_metric $metric )
			converted_metrics="$converted_metrics $metric"
		done
		echo $converted_metrics | tr ' ' ','                     > $tmprep/counters.csv
		#tail -n +2 $infile | cut -d';' -f 6-$ncols | tr ';' ',' >> $tmprep/counters.csv
		cat $infile | grep $codelet_name | sed '$ d' | cut -d';' -f 6-$ncols | tr ';' ',' >> $tmprep/counters.csv
		nrows=$(tail -n +2 $tmprep/counters.csv | wc -l)
		# Merging the stan and counters sections
		yes $(echo "$application_name,$batch_name,$code_name,$codelet_name,$binary_loop_id,$variant,$machine_name") | head -n $nrows > $tmprep/tmp1.csv
		cat $infile | cut -d';' -f2 | tail -n +2 | head -n $nrows > $tmprep/tmp2.csv
		yes $(echo "$instance_id,$frequency,$memory_load,$arg1,$arg2,$arg3,$arg4,$arg5,$arg6,$nb_threads,$Timestamp,$cpu_generation") | head -n $nrows > $tmprep/tmp3.csv
		echo "application.name,batch.name,code.name,codelet.name,binary_loop.id,decan_variant.name,machine.name,decan_experimental_configuration.data_size,decan_experimental_configuration.instance_id,decan_experimental_configuration.frequency,decan_experimental_configuration.memory_load,decan_experimental_configuration.arg1,decan_experimental_configuration.arg2,decan_experimental_configuration.arg3,decan_experimental_configuration.arg4,decan_experimental_configuration.arg5,decan_experimental_configuration.arg6,decan_experimental_configuration.nb_threads,Timestamp,cpu.generation" > $tmprep/codelet_struct.csv  
		paste -d',' $tmprep/tmp1.csv $tmprep/tmp2.csv $tmprep/tmp3.csv >> $tmprep/codelet_struct.csv  
		paste -d',' $tmprep/codelet_struct.csv $tmprep/counters.csv $tmprep/stan_report_${variant}.csv > $outfile
		extra_rows=$(($nrows + 2))
	    sed -i "$extra_rows,$ d" $outfile
	done
done
head -n 1     $tmprep/${codelet_name}_counters_${variant}_0MBs_${frequency}kHz.csv > ${cape_file}
tail -q -n +2 $tmprep/${codelet_name}_counters_*_0MBs_*kHz.csv >> ${cape_file}
rm -R $tmprep
