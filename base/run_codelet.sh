#!/bin/bash 

source $CLS_FOLDER/const.sh
if [ -f /opt/intel/sep/sep_vars.sh ]; then
    source /opt/intel/sep/sep_vars.sh > /dev/null
fi


if [[ "$nb_args" != "10" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, codelet's name,  number of iterations, repetitions, and command line args)."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
codelet_name="$2"
iterations="$3"
repetitions="$4"
start_codelet_loop_time="$5"
num_codelets="$6"
cnt_codelet_idx="$7"
res_path="$8"
list_override="$9"

variant=$(echo $res_path | sed "s|.*/variant_\([^/]*\).*|\1|g")
num_core=$(echo $res_path | sed "s|.*/numcores_\([^/]*\).*|\1|g")
command_line_args="${10}"

nc_all_cores=${XP_ALL_CORES[@]:0:(${num_core}-1)}

sec_to_ddhhmmss() {
    secs="$1"
    echo $((${secs}/86400))"d "$(date -d "1970-01-01 + ${secs}sec" "+%H:%M:%S")
}

run_cygwin() {
    cc="$1"
    run_prog="$2"
    (( hexcc=1<<($cc + 1 - 1) )) # +1 because Windows CPU# starts from 1
    hexcc=$(printf "%x" $hexcc)
    echo cmd /c start /b /wait /affinity $hexcc ${run_prog}
    cmd /c start /b /wait /affinity $hexcc ${run_prog}
}


START_RUN_CODELETS_SH=$(date '+%s')
echo "run_codelets.sh started at $(date --date=@${START_RUN_CODELETS_SH})."
#echo "Xp: foler, ${codelet_folder},'$codelet_name', size '$data_size', memload '$memory_load', num_core '$num_core', prefetcher '$prefetcher', frequency '$frequency', variant '$variant', iterations '$iterations', repetitions '$repetitions'."

cd $codelet_folder
echo "Codelet folder: $codelet_folder"
#res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant/numcores_${num_core}"
#res_path="$codelet_folder/../prefetchers_$prefetcher/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant/numcores_${num_core}"
echo "Res folder: $res_path"

TASKSET=$( which taskset )
NUMACTL=$( which numactl )

rm -f time.out

echo "Computing CPI and record program dumped metrics..."
res=""
pgm_dumped_metric_values=""

# TO BE REMOVED 
# creating repetition command line argument if necessary
#if [ -n "${rep_prefix}" ]; then
#  repappend="${rep_prefix}${repetitions}"
#else
#  repappend=""
#fi



if [[ "${variant}" == "ORG" ]]; then
    # Run the original program
    run_prog="./${codelet_name} ${command_line_args}"


    #run_prog_emon_api="./${codelet_name}"_emon_api
    # Run the same program but with different LD_LIBRARY_PATH (below)
    run_prog_emon_api="./${codelet_name} ${command_line_args}"
else
# Run the DECAN generated program
    run_prog="./${codelet_name}_${variant}_hwc"
# See generate_variants.sh to see emon_api binary is used to generate this binary
    run_prog_emon_api="./${codelet_name}_${variant}_hwc"
fi

for i in $( seq $META_REPETITIONS ); do
    #res=$( taskset -c $XP_CORE ./${codelet_name}_${variant}_cpi | grep CYCLES -A 1 | tail -n 1 )$( echo -e "\n$res" )
    #taskset -c $XP_CORE ./${codelet_name}_${variant}_hwc 
    #${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ./${codelet_name}_${variant}_hwc 
    #echo ${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ${run_prog}

    if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then    
	if [[ "$MC_RUN" != "0" ]]; then
	    for cc in ${nc_all_cores}; do
		run_cygwin $cc ${run_prog}
	    done
	fi
	run_cygwin $XP_CORE ${run_prog}

    else
	if [[ "$MC_RUN" != "0" ]]; then
	    for cc in ${nc_all_cores}; do
		cmd="$NUMACTL -m $XP_NODE -C ${cc} ${run_prog}"
		echo $cmd
		bash -c "LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $cmd" >& /dev/null &
	    done
	fi
	cmd="${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ${run_prog}"
	echo -n $cmd
	bash -c "LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $cmd" >& /dev/null
    fi

    echo ", time.out :: " $(tail -1 time.out)
    res=$( tail -n 1 time.out | cut -d'.' -f1 )$( echo -e "\n$res" )
    if [ -f $PGM_METRIC_FILE ]; then
	pgm_dumped_metric_values=$( tail -n 1 $PGM_METRIC_FILE )$( echo -e "\n$pgm_dumped_metric_values" )
    fi
done

rm -f time.out

res=$( echo "$res" | sort -k1n,1n )
let "mean_line = ($META_REPETITIONS / 2) + 1"
mean=$( echo "$res" | awk "NR==$mean_line" )
echo MEAN: ${mean}
echo ITERATION: ${iterations}

normalized_mean=$( echo $mean | awk '{print $1 / '$iterations';}' )

echo -e "CPI \t'$normalized_mean'"
# Here the order of field is assumed by gather_results.sh
#echo "$codelet_name"${DELIM}"$data_size"${DELIM}"$memory_load"${DELIM}"$frequency"${DELIM}"$num_core"${DELIM}"$iterations"${DELIM}"$repetitions"${DELIM}"$variant"${DELIM}"$normalized_mean" > "$res_path/cpi.csv"
echo "Iterations"${DELIM}"Repetitions"${DELIM}"CPI" > "$res_path/cpi_nv.csv"
echo "$iterations"${DELIM}"$repetitions"${DELIM}"$normalized_mean" >> "$res_path/cpi_nv.csv"
#echo "$codelet_name"${DELIM}"$data_size"${DELIM}"$memory_load"${DELIM}"$frequency"${DELIM}"$variant"${DELIM}"$normalized_mean" > "$res_path/cpi.csv"

if [ -f $PGM_METRIC_FILE ]; then
    pgm_dumped_metric_names=$( head -n 1 $PGM_METRIC_FILE )
    echo "METRIC INFO: names"
    echo $pgm_dumped_metric_names
    echo "METRIC INFO: values"
    echo $pgm_dumped_metric_values
    pgm_metric_mean=$( echo "$pgm_dumped_metric_values" | awk "NR==$mean_line" )
    echo $pgm_dumped_metric_names > $res_path/pgm_metrics.csv
    echo $pgm_metric_mean >> $res_path/pgm_metrics.csv
fi

if [ -f arguments.csv ]; then
    cp arguments.csv  $res_path/arguments.csv
fi

echo "RES:"$res_path

#echo "Ld library path: '$LD_LIBRARY_PATH'"

if [[ "$ACTIVATE_COUNTERS" != "0" ]]
then
    echo "Running counters..."
    emon -v > "$res_path/emon_info" 
    #emon_counters=$( env -i ${CLS_FOLDER}/build_counter_list.sh "$res_path/emon_info" )
    echo Build counter list with cmd: ${CLS_FOLDER}/build_counter_list.sh "$res_path/emon_info" "$list_override"
    emon_counters=$( ${CLS_FOLDER}/build_counter_list.sh "$res_path/emon_info" "$list_override")
    echo "COUNTER LIST: " ${emon_counters}


    echo ${emon_counters} > "$res_path/${EMON_COUNTER_NAMES_FILE}"
    #echo "emon -qu -t0 -C\"($emon_counters)\" $TASKSET -c $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/emon_report"
    #emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $TASKSET -c $XP_CORE ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"

    START_COUNTER_RUN_TIME=$(date +%s)
    totalRunCnt=0
    eta="NA"
    eta_all="NA"

    for i in $( seq $META_REPETITIONS ); do
      if [[ "ENABLE_SEP" == "1" ]]; then
	  emon_counters_to_run=$(./split_counters.sh $emon_counters)
	  emon_counters_core=$(echo $emon_counters_to_run | tr '#' '\n' | head -n 1)
	  emon_counters_uncore=$(echo $emon_counters_to_run | tr '#' '\n' | tail -n 1)

	  echo $emon_counters_core >  "$res_path/core_events_list"
	  echo $emon_counters_uncore >  "$res_path/uncore_events_list"
	  
	  for events in $(echo $emon_counters_core  | tr ${DELIM} ' '); do
	    events_code=$(echo $events | cut -d':' -f1)
	    events=$(echo $events | cut -d':' -f2)
	    #$NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -count -app ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
	    LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -count -app ${run_prog} &> "$res_path/emon_execution_log"
	  done

	  for events in $(echo $emon_counters_uncore  | tr ${DELIM} ' '); do
	    events_code=$(echo $events | cut -d':' -f1)
	    events=$(echo $events | cut -d':' -f2)
	    #$NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -app ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
	    LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -app ${run_prog} &> "$res_path/emon_execution_log"
	  done
      else # enable sep else clause
	  #emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
	  #emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog} &> "$res_path/emon_execution_log"
	  if [[ "$ACTIVATE_EMON_API" != "0" ]]; then
	      # Using advanced control so need to generate the file for counters
	      # Split events into files
	      rm -f event.* emon_api.out
	      emon --dry-run -C"($emon_counters)" | csplit -z --quiet --prefix=event. - '/^\S/' '{*}'

	      uncore_evfiles=($(grep -l Uncore event.*))
	      core_evfiles=($(grep -L Uncore event.*))  # Note the oppose -L
	      num_uncore_evfiles=${#uncore_evfiles[@]}
   	      num_core_evfiles=${#core_evfiles[@]}

	      if (( ${num_uncore_evfiles} > ${num_core_evfiles} )); then
		while ((${#core_evfiles[@]}*2<num_uncore_evfiles)); do 
		    core_evfiles=(${core_evfiles[@]} ${core_evfiles[@]})
                done
		  ((diff=num_uncore_evfiles - ${#core_evfiles[@]}))
		  core_evfiles=(${core_evfiles[@]} ${core_evfiles[@]:0:$diff})
	      else
		while ((${#uncore_evfiles[@]}*2<num_core_evfiles)); do 
		    uncore_evfiles=(${uncore_evfiles[@]} ${uncore_evfiles[@]})
                done
		  ((diff=num_core_evfiles - ${#uncore_evfiles[@]}))
		  uncore_evfiles=(${uncore_evfiles[@]} ${uncore_evfiles[@]:0:$diff})
	      fi
	      num_uncore_evfiles=${#uncore_evfiles[@]}
	      num_core_evfiles=${#core_evfiles[@]}

	      if [[ ${num_uncore_evfiles} == ${num_core_evfiles} ]]; then
		  num_evfiles=${num_uncore_evfiles}
	      else
		  echo "Failed to match Uncore(${num_uncore_evfiles})/Core(${num_core_evfiles}) event files!"
		  exit -1
	      fi


	      # Now run instrumented code for each event set
	      numRuns=$num_evfiles

	      #numRuns=$( ls -l event.* |wc -l )
	      runCnt=0
	      #for evfile in event.*; do
	      for ((ei=0; ei<$num_evfiles; ei++)); do
		((runCnt++))
		((totalRunCnt++))


		echo -ne "CodeletDS: (${cnt_codelet_idx}/${num_codelets}); Meta: (${i}/${META_REPETITIONS}); CnterSet: (${runCnt}/${numRuns}); "
		echo -ne "ETA codelet:${eta}; ETA All:${eta_all}                      \r"

		evlist=($(tail -q -n  +2 ${core_evfiles[$ei]} ${uncore_evfiles[$ei]} |tr -d '\r'))
#		echo EVLIST is ${evlist[*]}
#		evlist=($(tail -n +2 ${evfile} |tr -d '\r'))
		if [[ -f /opt/intel/sep/config/emon_api/emon_api_config_file.xml ]]; then
		  # output beginning of emon config file
cat <<EOFBEGIN > emon_api_config_file
<?xml version="1.0"?>
<root>
 <emon_config>
EOFBEGIN
		# add events to emon config file
		for newev in ${evlist[*]}; do
		    echo "        <event>$newev</event>" >> emon_api_config_file
		done
		# output the end of the emon config file
cat <<EOFEND >> emon_api_config_file
        <duration>99999999999</duration>
        <start_paused>0</start_paused>
        <output_file>emon_api.out</output_file>
        <print_system_time>0</print_system_time>
    </emon_config>
</root>
EOFEND
		else
		evlist=$(IFS=','; echo "${evlist[*]}")
		cat <<EOF > emon_api_config_file
<EMON_CONFIG>
EVENTS = "${evlist}"
DURATION=99999999999
OUTPUT_FILE=emon_api.out
</EMON_CONFIG>
EOF
		fi
		#	   	emon -stop 2> /dev/null

    if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then    		
	## TODO: Need to double check how Cygwin handles shared library.  May break
        echo $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog_emon_api} &>> "$res_path/emon_execution_log"
	cat emon_api_config_file
	if [[ "$MC_RUN" != "0" ]]; then
	    for cc in ${nc_all_cores}; do
		run_cygwin ${cc} ${run_prog} &>> "$res_path/emon_execution_log.core=${cc}" &
	    done
	fi

	run_cygwin ${XP_CORE} ${run_prog_emon_api} &>> "$res_path/emon_execution_log.core=${cc}" &
	while ps -W|grep -i emon.exe > /dev/null; do sleep 1; done
	if [[ "$MC_RUN" != "0" ]]; then
	    while ps -W|grep -i $(basename ${codelet_name}) > /dev/null; do sleep 1; done	    
	fi
    else

        #echo $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog_emon_api} &>> "$res_path/emon_execution_log"

	if [[ "$MC_RUN" != "0" ]]; then
	    # without emon probe
	    for cc in ${nc_all_cores}; do
		LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $NUMACTL -m $XP_NODE -C ${cc} ${run_prog} &>> "$res_path/emon_execution_log.core=${cc}" &
	    done
	fi


	# with emon probe
        LD_LIBRARY_PATH=${EMON_API_PROBE_FOLDER}:${LD_LIBRARY_PATH} $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog_emon_api} &>> "$res_path/emon_execution_log"
	while pgrep -x emon -u $USER > /dev/null; do sleep 1; done;
	
	if [[ "$MC_RUN" != "0" ]]; then
	    while pgrep -x $(basename ${codelet_name}) -u $USER > /dev/null; do 
		sleep 1; 
	    done
	fi
    fi

#		mv emon_api_config_file emon_api_config_file.${evfile}
		mv emon_api_config_file emon_api_config_file.${ei}
		grep -v "Addition" emon_api.out |grep -v "^$" >> "$res_path/emon_report"
# Uncomment below to print res path
#echo $res_path
#		mv emon_api.out emon_api.out.${evfile}
		mv emon_api.out emon_api.out.${ei}

		remainingRunCnt=$(((${META_REPETITIONS}*${numRuns})-${totalRunCnt}))
		CURRENT_COUNTER_RUN_TIME=$(date +%s)
		eta=$((((${CURRENT_COUNTER_RUN_TIME}-${START_COUNTER_RUN_TIME})*${remainingRunCnt})/${totalRunCnt}))
		EST_CURRENT_FINISH_TIME=$((${CURRENT_COUNTER_RUN_TIME}+${eta}))
		remainingCodeletRunCnt=$((${num_codelets}-${cnt_codelet_idx}))
		eta_all=$(sec_to_ddhhmmss $((((${EST_CURRENT_FINISH_TIME}-${start_codelet_loop_time})*${remainingCodeletRunCnt})/${cnt_codelet_idx} + ${eta})))
		eta=$(sec_to_ddhhmmss $eta)
	      done # end event file loop
	  else # activate emon api else clause (i.e. emon api == 0)
	      if [[ "$MC_RUN" != "0" ]]; then
		  if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then		  
	  	      for cc in ${nc_all_cores}; do
			  (( hexcc=1<<($cc - 1) ))
			  hexcc=$(printf "%x" $hexcc)
			  echo cmd /c start /b /affinity $hexcc ${run_prog}
			  # TODO: Need to check how to get LD_LIBRARY_PATH works for Cygwin (e.g. whether below line works). 
			  LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} cmd /c start /b /affinity $hexcc ${run_prog}
	  	      done
		  else
		      for cc in ${nc_all_cores}; do
			  LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} $NUMACTL -m $XP_NODE -C ${cc} ${run_prog} &
	  	      done
		  fi
	      fi

	      ((totalRunCnt++))

	      echo -ne "CodeletDS: (${cnt_codelet_idx}/${num_codelets}); Meta: (${i}/${META_REPETITIONS}); "
	      echo -ne "ETA codelet:${eta}; ETA All:${eta_all}                      \r"

	      LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog} &> "$res_path/emon_execution_log"

	      remainingRunCnt=$(((${META_REPETITIONS}*1)-${totalRunCnt}))
	      CURRENT_COUNTER_RUN_TIME=$(date +%s)
	      eta=$((((${CURRENT_COUNTER_RUN_TIME}-${START_COUNTER_RUN_TIME})*${remainingRunCnt})/${totalRunCnt}))
	      EST_CURRENT_FINISH_TIME=$((${CURRENT_COUNTER_RUN_TIME}+${eta}))
	      remainingCodeletRunCnt=$((${num_codelets}-${cnt_codelet_idx}))

	      eta_all=$(sec_to_ddhhmmss $((((${EST_CURRENT_FINISH_TIME}-${start_codelet_loop_time})*${remainingCodeletRunCnt})/${cnt_codelet_idx} + ${eta})))
	      eta=$(sec_to_ddhhmmss $eta)

	  fi # activate emon api if end
      fi # enable sep if end
    done # meta repetitions done
    echo -ne '\n'
else
    echo "Skipping counters (not activated)."
fi

# if [[ "$ACTIVATE_COUNTERS" != "0" ]]
# then
# 	echo "Counter experiments done, proceeding to formatting."
# 	${FORMAT_COUNTERS_SH} "$codelet_name" $data_size $memory_load $frequency "$variant" "${iterations}" "${emon_counters}" ${res_path}
# fi

END_RUN_CODELETS_SH=$(date '+%s')
ELAPSED_RUN_CODELETS_SH=$((${END_RUN_CODELETS_SH} - ${START_RUN_CODELETS_SH}))
echo "run_codelets.sh finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_RUN_CODELETS_SH}) seconds at $(date --date=@${END_RUN_CODELETS_SH})."

exit 0
