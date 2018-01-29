#!/bin/bash -l

combineCapeData() {
# Combining all run cape data
    START_VRUN_SH=$1
    run_dir=$2

    ofiles=($( find -L ${run_dir} -name *.cape.csv| sort ))
    head -1 ${ofiles[0]} > ${run_dir}/cape_${START_VRUN_SH}.csv
    tail -n +2 -q ${ofiles[@]:0} >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     for f in ${ofiles[@]}
#       do
#       cat $f >> ${run_dir}/cape_${START_VRUN_SH}.csv
#     done
}

# This function should automatically add all the code information under the prefix path
fill_codelet_maps()
{
    cnt_prefix="$1"
    cnt_sizes="$2"
#    cnt_codelets=($3)

#    echo prefix ${cnt_prefix}

    # include trailing / to exclude files
    test ! -d ${cnt_prefix} && return     # Return if directory not exist
    all_codelets=($( ls -d ${cnt_prefix}/*/*/ ))
    # remove trailing /
    all_codelets=(${all_codelets[@]/%\//})

#    echo ALL codelets: ${all_codelets[@]}


#    cnt_codelets=(${cnt_codelets[@]/#/${cnt_prefix}\/})
#    echo CNT_codelets ${cnt_codelets[@]}

#    exit

#    for codelet_path in ${cnt_codelets[@]}
    for codelet_path in ${all_codelets[@]}
    do
      codelet_name=$(basename ${codelet_path})
#       echo CN ${codelet_name}
#       echo CP ${codelet_path}
#       echo CS ${cnt_sizes}
      name2path+=([${codelet_name}]=${codelet_path})
      name2sizes+=([${codelet_name}]=${cnt_sizes})
    done

}


launchIt () {
    source $CLS_FOLDER/const.sh

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

    #LOG_FOLDER=${CLS_FOLDER}/logs
    export LOG_FOLDER=$(dirname $(readlink -f $0))/logs
    export RUN_FOLDER=${LOG_FOLDER}/runs

    (
	echo "Pending executing ${launch_script} at $(date)..."
	flock 888 || exit 1;
	echo "Start executing ${launch_script} at $(date)..."

	START_VRUN_SH=$(date '+%s')

	run_dir=${RUN_FOLDER}/${START_VRUN_SH}
	mkdir -p ${run_dir}

	${LOGGER_SH} ${START_VRUN_SH} "${launch_script} started at $(date --date=@${START_VRUN_SH})"
	${LOGGER_SH} ${START_VRUN_SH} "Purpose of run: ${rundesc}"
	${LOGGER_SH} ${START_VRUN_SH} "Hostname: ${HOSTNAME} (${REALHOSTNAME})"
	${launch_fn} ${START_VRUN_SH}

	# Combining all run cape data
	combineCapeData ${START_VRUN_SH} ${run_dir}
# 	for f in $( find -L ${run_dir} -name *.cape.csv | sort ) 
# 	do
# 	    cat $f >> ${run_dir}/cape_${START_VRUN_SH}.csv
# 	done

	${LOGGER_SH} ${START_VRUN_SH} "Cape data saved in: ${run_dir}/cape_${START_VRUN_SH}.csv"


	END_VRUN_SH=$(date '+%s')
	ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))
	
	${LOGGER_SH} ${START_VRUN_SH} "${launch_script} finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) at $(date --date=@${END_VRUN_SH})"     
	
    ) 888>/tmp/vrun.lock
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
    combineCapeData ${START_VRUN_SH} ${run_dir}

    END_VRUN_SH=$(date '+%s')
    ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))
    
    ${LOGGER_SH} ${START_VRUN_SH} "${launch_script} finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) at $(date --date=@${END_VRUN_SH})"     
    

}


runLoop() {
    local runId="$1"
    local variants="$2"
    local memory_loads="$3"
    local frequencies="$4"
    local num_cores="$5"
    local prefetchers="$6"
    local counter_list_override="$7"

# uses global variables assumed below
# declare -gA name2path
# declare -gA name2sizes
# declare -ga run_codelets


    set -o pipefail # make sure pipe of tee would not reset return code.
    
    
    echo RUN codelets : ${run_codelets[@]}

    count=0

    start_codelet_loop_time=$(date '+%s')    
    num_codelets=0
    for codelet in ${run_codelets[@]}
      do
      sizes_arr=(${name2sizes[${codelet}]})
      ((num_codelets+=${#sizes_arr[@]}))
    done
    num_cores_arr=(${num_cores})
    ((num_codelets*=${#num_cores_arr[@]}))

    prefetchers_arr=(${prefetchers})
    ((num_codelets*=${#prefetchers_arr[@]}))

    frequencies_arr=(${frequencies})
    ((num_codelets*=${#frequencies_arr[@]}))



    codelet_id=0
    for codelet in ${run_codelets[@]}
      do
      codelet_path=${name2path[${codelet}]}
      sizes=${name2sizes[${codelet}]}
#  echo ${codelet_path}
#  ls ${codelet_path}
#  echo "SS: ${sizes}"
      ((count++))
echo here $(pwd)

      echo "Launching CLS on $codelet_path  (${count} of ${#run_codelets[@]}) ...for sizes $sizes"
      
      ${LOGGER_SH} ${runId} "Launching CLS on '$codelet_path'..."
      

    for sz in ${sizes[@]}
      do

       echo Executing CLS: $CLS_FOLDER/cls.sh \""$codelet_path"\" \""$variants"\" \""${sz}"\" \""$memory_loads"\" \""$frequencies"\"  \""${runId}"\" \""${start_codelet_loop_time}"\" \""${num_codelets}"\" \""${codelet_id}"\" \""${num_cores}"\" \""${prefetchers}"\" \"${counter_list_override}\"
      $CLS_FOLDER/cls.sh "$codelet_path" "$variants" "${sz}" "$memory_loads" "$frequencies"  "${runId}" "${start_codelet_loop_time}" "${num_codelets}" "${codelet_id}" "${num_cores}" "${prefetchers}" "${counter_list_override}"| tee "$codelet_path/cls.log"
      res=$?
      if [[ "$res" != "0" ]]
	  then
#      echo -e "\tAn error occured! Check '$codelet_path/cls.log' for more information."
	  ${LOGGER_SH} ${runId} "FAILED: Check '${codelet_path}/cls.log' for more information."
      fi
      ((codelet_id+=(${#num_cores_arr[@]}*${#prefetchers_arr[@]}*${#frequencies_arr[@]})))
    done

#      sizes_arr=(${sizes})

#      ((codelet_id+=${#sizes_arr[@]}))
#      ((codelet_id*=${#num_cores_arr[@]}))
#      ((codelet_id+=${#sizes_arr[@]}*${#num_cores_arr[@]}))
    done
    
}