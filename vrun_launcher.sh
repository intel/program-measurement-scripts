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
    ${LOGGER_SH} ${START_VRUN_SH} "Hostname: ${HOSTNAME} (${REALHOSTNAME})"
    
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

launchAll() {
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
    ${LOGGER_SH} ${START_VRUN_SH} "Hostname: ${HOSTNAME} (${REALHOSTNAME})"
    
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


runLoop() {
    local runId="$1"
    local variants="$2"
    local memory_loads="$3"
    local frequencies="$4"

# uses global variables assumed below
# declare -gA name2path
# declare -gA name2sizes
# declare -ga run_codelets

    

    set -o pipefail # make sure pipe of tee would not reset return code.
    
    
    echo RUN codelets : ${run_codelets[@]}

    count=0
    
    for codelet in ${run_codelets[@]}
      do
      codelet_path=${name2path[${codelet}]}
      sizes=${name2sizes[${codelet}]}
#  echo ${codelet_path}
#  ls ${codelet_path}
#  echo "SS: ${sizes}"
      ((count++))
      echo "Launching CLS on $codelet_path  (${count} of ${#run_codelets[@]}) ...for sizes $sizes"
      
      ${LOGGER_SH} ${runId} "Launching CLS on '$codelet_path'..."
      
      ./cls.sh "$codelet_path" "$variants" "${sizes}" "$memory_loads" "$frequencies"  "${runId}" | tee "$codelet_path/cls.log"
      res=$?
      if [[ "$res" != "0" ]]
	  then
#      echo -e "\tAn error occured! Check '$codelet_path/cls.log' for more information."
	  ${LOGGER_SH} ${runId} "FAILED: Check '${codelet_path}/cls.log' for more information."
      fi
    done
    
}