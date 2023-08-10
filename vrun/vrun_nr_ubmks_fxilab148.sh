#!/bin/bash -l

source $(dirname $0)/const.sh
source ./vrun_launcher.sh

run() {
	runId=$@




	START_VRUN_SH=$(date '+%s')

	variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
	variants="REF"
	linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
	#linear_sizes="2000 10000000"
	#linear_sizes="2000"
	quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
	memory_loads="0 99999"
	memory_loads="0"
	#frequencies="800000 3500000"
	#frequencies="1200000 2800000"
	frequencies="2800000"

	linear_codelets=""
	quadratic_codelets=""

	#prefix="/localdisk/vincent/ecr_codelets/nr-codelets"
	prefix="/nfs/fx/home/cwong29/working/NR-scripts/nr-codelets"
	#linear_codelets="${prefix}/bws/nr_ubmks/*"
	#linear_codelets="${prefix}/bws/nr_ubmks/balanc_3_1_ubmk_de"
	#linear_codelets="${prefix}/bws/nr_ubmks/s319_se"
	linear_codelets="${prefix}/bws/nr_ubmks/mprove_9_ubmk_de"

	for codelet in $linear_codelets
	do
		${LOGGER_SH} ${runId}  "Launching CLS on '$codelet'..."
		./cls.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" "${runId}" | tee "$codelet/cls.log"
		# &> "$codelet/cls.log"
		res=$?
		if [[ "$res" != "0" ]]
		then
			echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
		fi
	done

	for codelet in $quadratic_codelets
	do
		${LOGGER_SH} ${runId}  "Launching CLS on '$codelet'..."
		./cls.sh "$codelet" "$variants" "$quadratic_sizes" "$memory_loads" "$frequencies" "${runId}" | tee "$codelet/cls.log"
		# &> "$codelet/cls.log"
		res=$?
		if [[ "$res" != "0" ]]
		then
			echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
		fi
	done
	END_VRUN_SH=$(date '+%s')
	ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))
	#echo "$0 finished in ${ELAPSED_VRUN_SH} seconds."
	echo "$0 finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) ."

}

launchIt $0 run "$@"


