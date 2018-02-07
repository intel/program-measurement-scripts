#!/bin/bash 

# Combining all run cape data

run_dir=$1
#START_VRUN_SH=$1
START_VRUN_SH=$(basename $run_dir)

ofiles=($( find -L ${run_dir} -name *.cape.csv| sort ))
head -1 ${ofiles[0]} > ${run_dir}/cape_${START_VRUN_SH}.csv
tail -n +2 -q ${ofiles[@]:0} >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     for f in ${ofiles[@]}
#       do
#       cat $f >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     done
