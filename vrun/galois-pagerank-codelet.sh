#!/bin/bash -l

source ../base/const.sh
source ../base/vrun_launcher.sh

#module load atc/1.5

parameter_set_decoding () {
	codelet=$1
	datasize=$2
	repetition=$3

	# : => ' ' using sed
	cmdlineargs=$(echo $datasize | sed 's/:/ /g')

	# output csv of command line arguments
	printf "" > " ./arguments.csv"

	for label in ${CMDLINELABELS}; do
		printf "%s," "${label}" >> " ./arguments.csv"
	done

	printf "\n" >> " ./arguments.csv"

	for value in ${cmdlineargs}; do
		printf "%s," "${value}" >> " ./arguments.csv"
	done

	echo $cmdlineargs -runs=$repetition
}

build_codelet () {
	codelet_folder="$1"
	codelet_name="$2"
	build_folder="$3"

	# attempts to find BUILD_SCRIPT in conf file (signifies a custom build script)
	grep "BUILD_SCRIPT" "$codelet_folder/codelet.conf" &> /dev/null
	BUILD_SCRIPT_FOUND=$?


	if [ $BUILD_SCRIPT_FOUND == "0" ]; then
		# codelet has specific build script located in build directory; use it
		echo "Moving to codelet directory and using codelet-defined build_codelet.sh script"

		# move to that directory and run
		pushd ${codelet_folder}
		${codelet_folder}/build_codelet.sh ${codelet_folder}/${CLS_RES_FOLDER}
		popd

		echo "Moving built codelet to correct directory"

		echo mkdir ${build_folder}
		mkdir ${build_folder} &> /dev/null

		# move binary to correct spot and prep "build folder" as well
		mv ${codelet_folder}/${codelet_name} ${build_folder}
		res=$?
		if [[ "$res" != "0" ]]; then
			echo "ERROR! Move did not succeed."
			exit -1
		fi

		#   echo "Copying binary folder to a build folder"
		#   # copy binary folder to a "build" folder
		#   cp -r $codelet_folder/$CLS_RES_FOLDER/${BINARIES_FOLDER} ${build_folder}
		#   res=$?
		#   if [[ "$res" != "0" ]]; then
		#     echo "ERROR! Copy of binary to build8 failed"
		#     exit -1
		#   fi
	fi
}


export -f parameter_set_decoding
export -f build_codelet

run() {
	runId=$@

	variants="ORG"
	linear_sizes="0"
	memory_loads="0"
	num_cores="1"
	prefetchers="0"
	frequencies="2200000"

	prefix=$(readlink -f ../..)
	galois_prefix="${prefix}/galois-codelets/build"
	galois_lonestar_prefix="${galois_prefix}/lonestar/codelets"
	#echo ${galois_lonestar_prefix}

	# SR runs (including some original)
	declare -gA name2path
	declare -gA name2sizes
	declare -ga run_codelets

	fill_codelet_maps "${galois_lonestar_prefix}" "${linear_sizes}"

	# name2sizes must be specified for correctness/backward compatibility purposes
	# (script only executes if something exists in name2sizes)
	#  name2sizes[pagerank_pull_codelet]="-t=28 /net/ohm/export/iss/dist-inputs/transpose/rmat15.tgr;-t=14 /net/ohm/export/iss/dist-inputs/transpose/rmat15.tgr"
	# Easiest just to have data sizes space delimited following bash convention and bring back command line spacing in parameter_set_decoding()
	name2sizes[pagerank_pull_codelet]="-t=28:/net/ohm/export/iss/dist-inputs/transpose/rmat15.tgr -t=14:/net/ohm/export/iss/dist-inputs/transpose/rmat15.tgr"

	# specify that i want to use the command line arguments functionality
	USECMDLINE="1"
	# specify the prefix to use when specifying repetitions
	REPPREFIX="-runs="

	# lables for the command lines above
	CMDLINELABELS="threads graph_name"

	run_codelets=( pagerank_pull_codelet )

	runLoop "${runId}" "$variants" "$memory_loads" "$frequencies" "$num_cores" \
		"$prefetchers" \
		"RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0"

	return
}

launchIt $0 run "$@"
