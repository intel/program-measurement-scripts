#!/bin/bash 

# This script will find out the average iterations per core for all loops executed by a function provided on number of cores
# There are three cases:
# 1) For sequential runs, only one core is running a program, so 
#   a) we just run the program on one core
#   b) determine the number of iterations executed by individual loop
# 2) For throughput runs (MC_RUNS=1), we normally run the same program on $num_cores.  We expect all cores will execute the 
#    same number of iterations.  The ave iterations per core will be ($num_cores* <iteration executed by 1 core>/$num_cores), so
#    it will be simply <iteration executed by 1 core>.  To speedup/simplify process, we just neeed to
#   a) run the program on one core
#   b) determine the number of iterations executed by individual loop
#   So essentially the same as 1)
# 3) For true prallel runs (IF_PARALLEL=1), we have to run the program in parallel mode.  The data collection (MAQAO/SEP/VTUNE) 
#   is expected to collect all iterations from all cores, so
#   a) we run the program in parallel mode.
#   b) determine the number of iterations executed by individual all cores
#   c) divide the counts by $num_cores.
source $CLS_FOLDER/const.sh

if [[ "$nb_args" -lt "4" ]]; then
	echo "ERROR! Invalid arguments (need the binary's path, function's name,data size, number of repetitions, and (optionally) number of cores)."
	exit -1
fi

set -x
binary_path=$( readlink -f "$1" )
binary_folder=$( dirname "$binary_path" )
function_name="$2"
data_size="$3"
repetition="$4"
num_cores="$5"
set +x

declare -A count_values

if [[ -z "$num_cores" ]]; then
  num_cores="1"
fi
#echo "Generation of splitncount for '$binary_path' ('$function_name')"

cd $binary_folder

command_line_args=$(parameter_set_decoding "$binary_path" "$data_size" "$repetition" )

# Create the datasize file for codelet run
#echo "${repetition} ${data_size}" > ./codelet.data

# No need to provide below.  Handled in the parameter_set_decoding function
# creating string to pass into program for case of passing through command line
#if [ -n "${rep_prefix}" ]; then
#    repappend="${rep_prefix}${repetition}"
#else
#    repappend=""
#fi

# Ensure basic probe is used
LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH}

if [[ "$USE_OLD_DECAN" == "0" ]]; then
    # Filling new MAQAO implementation
    # Get a list of loop id for the codelet
    loop_ids=$( $MAQAO analyze -ll $binary_path "${command_line_args}" fct=$function_name loop-depth=innermost | sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- "----" | sed 's/.*|[ ]\+\([^ ]*\) .*/\1/' )
    echo CMD loop_ids="\$( $MAQAO analyze -ll $binary_path "${command_line_args}" fct=$function_name loop-depth=innermost | sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- \"----\" | sed 's/.*|[ ]\+\([^ ]*\) .*/\1/' )" 1>&2
    #echo ${loop_ids[*]}
else
    $DECAN_CONFIGURATOR "$DECAN_FOLDER/" "$binary_path" "${command_line_args}" "$function_name" "splitncount" "$UARCH" &>/dev/null
    $DECAN "$DECAN_CONFIGURATION" &>/dev/null
    
    echo HERE > /tmp/count.out.txt
    echo $DECAN "$DECAN_CONFIGURATION" >> /tmp/count.out.txt
    echo ${LD_LIBRARY_PATH} >> /tmp/count.out.txt
    cat $PWD/$DECAN_REPORT >> /tmp/count.out.txt
    decan_variants=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
    
    # Here decan_variants are the variants to count loop iterations , not DECAN varaint for CLS runs
    # Also the loop ids are encoded to the decan variant names
    if [[ "$decan_variants" == "" ]]; then
	echo "ERROR! No loop could be identified!" 1>&2
	exit -1
    fi
    rm -f $PWD/$DECAN_REPORT
    echo DONE >> /tmp/count.out.txt
    # This *is* used at the end in iterating to compute final_res
    loop_ids=$( echo "$decan_variants" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )
    
    #echo "$decan_variants" &>blabla
    #for loop_id in $loop_ids
    #do
    #	echo "Found loop '$loop_id'" &> /tmp/blabli
    #done
fi

if [[ "$LOOP_ITER_COUNTER" == "MAQAO" ]]; then
  # Get the count for each loop id

  if [[ "$USE_OLD_DECAN" == "0" ]]; then
      for loop_id in $loop_ids; do
        #$MAQAO vprof lid=$loop_id -- $binary_path "${command_line_args}" >/tmp/out.$loop_id
        #count_values[$loop_id]=$( grep Total /tmp/out.$loop_id |cut -f3 -d'|' |tr -d [:blank:] )
        echo count_values[$loop_id]="\$( $MAQAO vprof lid=$loop_id -- $binary_path "${command_line_args}" |grep Total|cut -f3 -d'|' |tr -d [:blank:] )" 1>&2
        count_values[$loop_id]=$( $MAQAO vprof lid=$loop_id i=iterations -- $binary_path "${command_line_args}" |grep Total|cut -f3 -d'|' |tr -d [:blank:] )
        echo "COUNT: " ${count_values[$loop_id]} 1>&2
        done
  else
      for decan_variant in $decan_variants; do
    #"./$decan_variant"
        "./$decan_variant" &> "$decan_variant.dprof"
		loop_id=$( echo "$decan_variant" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )
        count_values[$loop_id]=$( cat "$decan_variant.dprof" | grep TOTAL_LOOP_CALLS -A 1 | sed -n "2p" | cut -f 2 -d ',' )
        cat "$decan_variant.dprof" 1>&2
        echo "COUNT: " ${count_values[$loop_id]} 1>&2
        rm -f "$decan_variant" "$decan_variant.dprof"
      done
  fi

  # Got all counts saved in ${count_values[*]}
elif [[ "$LOOP_ITER_COUNTER" == "SEP" ]]; then
    # Use sep to count iterations
    maqao_extra_info=$( $MAQAO analyze -ll --show-extra-info $binary_path "${command_line_args}"  fct=$function_name loop-depth=innermost )

    # Do the counting using sep
    if [[ ${command_line_args} == "" ]]; then
	echo sep -start -ec BR_INST_RETIRED.ALL_BRANCHES_PS:sa=${LOOP_ITER_SEP_COUNTER_SAV} -app $binary_path -out sep_counts 1>&2
	sep -start -ec BR_INST_RETIRED.ALL_BRANCHES_PS:sa=${LOOP_ITER_SEP_COUNTER_SAV} -app $binary_path -out sep_counts
# TODO: DO true parallel run
    else
	sep -start -ec BR_INST_RETIRED.ALL_BRANCHES_PS:sa=${LOOP_ITER_SEP_COUNTER_SAV} -app $binary_path -args "${command_line_args}" -out sep_counts
# TODO: DO true parallel run
    fi
    base_binary_name=$(basename $binary_path)
    for loop_id in $loop_ids; do
	last_asm_addr=$( echo "$maqao_extra_info" | grep asm|sed -n 's/.*[ ]\+'${loop_id}'[ ]\+\[depth.*asm: .*\;0x\([^ ]*\)\].*/\1/p' |tr '[:lower:]' '[:upper:]' )
	sample_count=$(sfdump sep_counts.tb7 -samples |grep ${base_binary_name} |sed -n '/.*\t.\+:0x0*'${last_asm_addr}'\t.*/p'|wc -l)
	count_values[$loop_id]=$(((sample_count * LOOP_ITER_SEP_COUNTER_SAV)))
	echo count_values[$loop_id]="\$(sfdump sep_counts.tb7 -samples |grep "${base_binary_name}" |sed -n '/.*\t.\+:0x0*'"${last_asm_addr}"'\t.*/p'|wc -l)" 1>&2
	echo "COUNT: " ${count_values[$loop_id]} 1>&2
    done

    # Got all counts saved in ${count_values[*]}
else
  if [[ "$VTUNE" != "" ]]; then
    #first get loop ids
    #loop_ids=$( $MAQAO analyze -ll $binary_path "${command_line_args}" fct=$function_name loop=innermost | sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- "----" | sed 's/.*| \([^ ]*\) .*/\1/' )
    # Below two lines are commented out because loop_ids determination is factored out
    #loop_ids=$( $MAQAO analyze -ll $binary_path "${command_line_args}" fct=$function_name loop=innermost | grep -E "[0-9]+" | grep -v "${function_name}" | sed 's/.*| \([^ ]*\) .*/\1/' )
    #echo CMD loop_ids="\$( $MAQAO analyze -ll $binary_path "${command_line_args}" fct=$function_name loop=innermost | sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- \"----\" | sed 's/.*| \([^ ]*\) .*/\1/' )" 1>&2
    loop_ids_src_line=$( $MAQAO analyze -ll --show-extra-info $binary_path "${command_line_args}"  fct=$function_name loop-depth=innermost | grep -E "[0-9]+" | grep -v "${function_name}" | sed 's/.*:\([^ ]*\)-.*/\1/' )
    echo loop_ids: $loop_ids 1>&2
    echo loop_ids_src_line: $loop_ids_src_line 1>&2
    echo Using VTune to get estimation of iteration count 1>&2
    #cd ../..
    make count >/dev/null
    echo $VTUNE -loop-mode=loop-only -collect advanced-hotspots -data-limit=8192 -k sampling-interval=0.1 -k collection-detail=stack-call-and-tripcount -k analyze-openmp=true -- ./convf32_count 1>&2
# TODO: Hardcoded run of ./convf32_count here!! VTUNE counting does not work for other code!
# TODO: DO true parallel run
    $VTUNE -loop-mode=loop-only -collect advanced-hotspots -data-limit=8192 -k sampling-interval=0.1 -k collection-detail=stack-call-and-tripcount -k analyze-openmp=true -- ./convf32_count >/dev/null
    echo $VTUNE -report hw-events -group-by source-function -r r000ah -report-output tmp_vtune.csv -format csv -csv-delimiter comma 1>&2
    $VTUNE -report hw-events -group-by source-function -r r000ah -report-output tmp_vtune.csv -format csv -csv-delimiter comma >/dev/null
    vtune_loop_src_line=$(tail -n+2 tmp_vtune.csv | head -n1 | awk 'BEGIN {FS =","} ; {print $1}' | sed 's/.* \([0-9]*\) .*/\1/')
    echo vtune_loop_src_line: $vtune_loop_src_line 1>&2
    vtune_loop_id=-2
    idx_src_line=0
    for line in $loop_ids_src_line; do
      ((idx_src_line+=1))
      if [[ "$line" == "$vtune_loop_src_line" ]]; then
        break
      fi
    done
    idx_loop=0
    for loop in $loop_ids; do
      ((idx_loop+=1))
      if [[ "$idx_loop" == "$idx_src_line" ]]; then
        vtune_loop_id=$loop
      fi
    done
    vtune_field=$(grep "Hardware Event Count:ITERATION_COUNT" tmp_vtune.csv | awk '{print}' RS="Hardware Event Count:ITERATION_COUNT" | sed 2d | tr -dc ',' | wc -c)
    ((vtune_field+=1))
    #echo count_values[-2]="\$(tail -n+2 tmp_vtune.csv | head -n1 | awk -v vtune_field=\"\$vtune_field\" 'BEGIN {FS =\",\"} ; {print \$vtune_field}')" 1>&2
    count_values[$vtune_loop_id]=$(tail -n+2 tmp_vtune.csv | head -n1 | awk -v vtune_field="$vtune_field" 'BEGIN {FS =","} ; {print $vtune_field}') 
    echo count_values[$vtune_loop_id]="${count_values[$vtune_loop_id]}" 1>&2
    rm -f convf32_count
    rm -rf r000ah
    rm -f tmp_vtune.csv
  else
    echo "Using VTune for iteration count but VTune is not found!" 1>&2
    echo "Exiting ..." 1>&2
    exit 1
  fi
  loop_ids=( $vtune_loop_id )
fi

cd $CLS_FOLDER
final_res=""
# For each loop in loop_ids
for loop_id in $loop_ids; do
  # Grab the corresponding iteration count
  tmp_iter=$( echo "${count_values[$loop_id]}" )
  # Divide the number of iterations by the number of cores for true parallel runs
  if [[ "$IF_PARALLEL" == "1" ]]; then
    tmp_iter=$(($tmp_iter / $num_cores))
  fi
  # If the iterations count is non-empty, append it to final_res
  if [[ "$tmp_iter" != "" ]]; then
    final_res=$( echo -e "$loop_id"${DELIM}"$tmp_iter"${DELIM}"\n$final_res" )
  fi
done
echo "$final_res" | sort -k2nr,2nr -t ${DELIM}
exit 0
