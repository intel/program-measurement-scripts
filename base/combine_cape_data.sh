#!/bin/bash 
source $CLS_FOLDER/const.sh

# Combining all run cape data

run_dir=$1
#START_VRUN_SH=$1
START_VRUN_SH=$(basename $run_dir)

ofiles=($( find -L ${run_dir} -name *.cape.csv| sort ))
combined_raw_json=${run_dir}/cape_${START_VRUN_SH}.json
combined_raw_ofile=${run_dir}/cape_${START_VRUN_SH}.csv
combined_summary_ofile=${run_dir}/cape_summary_${START_VRUN_SH}.csv

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
    csvjson -I --stream $f >> $combined_raw_json
done
in2csv --format ndjson $combined_raw_json > ${combined_raw_ofile}

echo "Running post-processing script to summarize raw data..."
$CLS_FOLDER/report_summary.py -i ${combined_raw_ofile} -o ${combined_summary_ofile}
${LOGGER_SH} ${START_VRUN_SH} "Cape raw data saved in: ${combined_raw_ofile}"
${LOGGER_SH} ${START_VRUN_SH} "Cape summary data saved in : ${combined_summary_ofile}"