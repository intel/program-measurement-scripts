#!/bin/bash -l

launchIt () {
    source $(dirname $0)/const.sh

    if [[ "$nb_args" > "3" ]]
	then
	echo "ERROR! Invalid arguments (need: launch script, launch fn, run description (optional))."
	exit -1
    fi

    launch_script="$1"
    launch_fn="$2"

    if [[ "$nb_args" < "3" ]]
	then
	read -p "Enter a brief desc for this run: " rundesc
    else
	rundesc="$3"
    fi


    START_VRUN_SH=$(date '+%s')

    run_dir=${RUN_FOLDER}/${START_VRUN_SH}
    mkdir -p ${run_dir}

    ${LOGGER_SH} ${START_VRUN_SH} "${launch_script} started at $(date --date=@${START_VRUN_SH})"
    ${LOGGER_SH} ${START_VRUN_SH} "Purpose of run: ${rundesc}"
    ${LOGGER_SH} ${START_VRUN_SH} "Hostname: ${HOSTNAME}"
    
    ${launch_fn} ${START_VRUN_SH}

# Combining all run cape data
    for f in $( find -L ${run_dir} -name *.cape.csv ) 
    do
      cat $f >> ${run_dir}/cape.csv
    done


    END_VRUN_SH=$(date '+%s')
    ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))
    
    ${LOGGER_SH} ${START_VRUN_SH} "${launch_script} finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) at $(date --date=@${END_VRUN_SH})"     
    

}