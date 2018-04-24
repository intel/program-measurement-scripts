#!/bin/bash 
source $CLS_FOLDER/const.sh

# Combining all run cape data

run_dir=$1
#START_VRUN_SH=$1
START_VRUN_SH=$(basename $run_dir)

ofiles=($( find -L ${run_dir} -name *.cape.csv| sort ))
combined_raw_ofile=${run_dir}/cape_${START_VRUN_SH}.csv
combined_summary_ofile=${run_dir}/cape_summary_${START_VRUN_SH}.csv

head -1 ${ofiles[0]} > ${combined_raw_ofile}
tail -n +2 -q ${ofiles[@]:0} >> ${combined_raw_ofile}
#     for f in ${ofiles[@]}
#       do
#       cat $f >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     done
echo "Running post-processing script to summarize raw data..."
$CLS_FOLDER/report_summary.py -i ${combined_raw_ofile} -o ${combined_summary_ofile}
${LOGGER_SH} ${START_VRUN_SH} "Cape raw data saved in: ${combined_raw_ofile}"
${LOGGER_SH} ${START_VRUN_SH} "Cape summary data saved in : ${combined_summary_ofile}"