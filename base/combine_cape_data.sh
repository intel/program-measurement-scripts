#!/bin/bash
source $CLS_FOLDER/const.sh

# Combining all run cape data

run_dir=$1
#START_VRUN_SH=$1
START_VRUN_SH=$(basename $run_dir)

ofiles=($( find -L ${run_dir}/cls* -name *.cape.csv| sort ))
combined_raw_json=${run_dir}/cape_${START_VRUN_SH}.json
combined_raw_ofile=${run_dir}/cape_${START_VRUN_SH}.csv
combined_summary_ofile=${run_dir}/cape_summary_${START_VRUN_SH}.csv
combined_formatted_summary_ofile=${run_dir}/cape_summary_${START_VRUN_SH}.xlsx
combined_qplot_ofile=${run_dir}/cape_qplot_${START_VRUN_SH}.xlsx
combined_qplot_html=${run_dir}/cape_qplot_${START_VRUN_SH}_html
si_training_set_ifile=${CLS_FOLDER}/../analyzer/clusters/LORE-Optimal.csv
si_summary_ifile=${run_dir}/si_summary_ip_${START_VRUN_SH}.csv
si_summary_ofile=${run_dir}/si_summary_op_${START_VRUN_SH}.csv

# Use csvkit instead
#head -1 ${ofiles[0]} > ${combined_raw_ofile}
#tail -n +2 -q ${ofiles[@]:0} >> ${combined_raw_ofile}
#     for f in ${ofiles[@]}
#       do
#       cat $f >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     done

# Normally csvstack should provide the functionality to merge csvs
# Due to a bug/limitation reported in https://github.com/wireservice/csvkit/issues/245
# csvstack cannot be used directly but there a workaround is proposed
# To combine two csv files, first convert and append them to JSON, then convert back from JSON.
# csvjson --stream file_1.csv >> combined.jsonl
# csvjson --stream file_2.csv >> combined.jsonl
# in2csv --format ndjson combined.jsonl >> combined.csv
touch $combined_raw_json
for f in ${ofiles[@]}; do
	#    csvjson -I --stream $f
	csvjson -I --stream $f >> $combined_raw_json
done
#in2csv -I --format ndjson $combined_raw_json
in2csv -I --format ndjson $combined_raw_json > ${combined_raw_ofile}

echo "Running post-processing script to summarize raw data..."
$CLS_FOLDER/summarize.py -i ${combined_raw_ofile} -o ${combined_summary_ofile}
$CLS_FOLDER/summarize.py -i ${combined_raw_ofile} -o ${combined_formatted_summary_ofile}
# Don't generate QPLOT HTML now with new tool
#echo "Running Qplot generator to generate QPlot HTML ..."
#$CLS_FOLDER/qplot_data_generation.py -i ${combined_raw_ofile} -o ${combined_qplot_ofile} -q ${combined_qplot_html}
${LOGGER_SH} ${START_VRUN_SH} "Cape raw data saved in: ${combined_raw_ofile}"
${LOGGER_SH} ${START_VRUN_SH} "Cape summary data saved in : ${combined_summary_ofile}"
${LOGGER_SH} ${START_VRUN_SH} "Cape formatted summary data saved in : ${combined_formatted_summary_ofile}"
${LOGGER_SH} ${START_VRUN_SH} "Cape QPLOT HTML data saved in : ${combined_qplot_html}"
echo "Running SI Analysis script..."
$CLS_FOLDER/summarize.py -i ${combined_raw_ofile} -o ${si_summary_ifile} --enable-meta
$CLS_FOLDER/sat_analysis.py -m ${si_training_set_ifile} -t ${si_summary_ifile} -o ${si_summary_ofile}

