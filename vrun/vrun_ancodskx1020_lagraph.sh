#!/bin/bash -l

source ../base/const.sh
source ../base/vrun_launcher.sh

#PUT compiler source stuff here
source ${COMPILER_ROOT}/compilers/intel/16.0/Linux/intel64/load0.sh

BIN_DIR=/localdisk/cwong29/working/NR-scripts/galois/cls-build6/lonestar/experimental/lagraph/apps

#export GRAPH_DIR=/nfs/site/proj/alac/data/graph-algorithms-data/Galois/GaloisBLAS/Galois.clean.version/lonestar/graphBLASwrapper/test_inputs
export GRAPH_DIR=/nfs/site/proj/alac/data/graph-algorithms-data/graphblas-inputs
CODELET_DIR=$(dirname $(readlink -f $0))/codelets
export GALOIS_DO_NOT_BIND_THREADS=1


parameter_set_decoding () {
	codelet=$1
	datasize=$2
	repetition=$3
	rundir=$4
	num_cores=$5

	# Create the datasize file for codelet run
	gd=${GRAPH_DIR}/${datasize}
	sn=$(cat ${gd}/${datasize}.source)
	echo "${repetition} ${datasize}" > ./codelet.data
	echo -e "arraysize\n${datasize}" > arguments.csv
	if [[ $(basename $codelet) == 'grbBFS' || $(basename $codelet) == 'grbBF' ]]; then
			echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition}"
	elif [[ $(basename $codelet) == 'grbKTruss' ]]; then
			if [[ ${datasize} == 'road-USA-W' || ${datasize} == 'road-USA' ]]; then
					echo "${gd}/${datasize}.cgr -k=4 -t=${num_cores} -rep=${repetition}"
			else
					echo "${gd}/${datasize}.cgr -k=7 -t=${num_cores} -rep=${repetition}"
			fi
	else
			echo "${gd}/${datasize}.cgr  -t=${num_cores} -rep=${repetition}"
	fi
}

build_codelet () {
	codelet_folder="$1"
	codelet_name="$2"
	build_folder="$3"

	# Simple codelet copying for prebuilt app
	# below returns full path name
	build_tmp_folder=$(mktemp -d --tmpdir=${codelet_folder}/..)

	echo "Copying codelet '$codelet_folder/$codelet_name'..."

	build_files=${codelet_folder}/${codelet_name}
	cp ${build_files} ${build_tmp_folder}
	cd ${build_tmp_folder}


	echo "Codelet generation was successful."
	echo ${build_tmp_folder}
#	read -p "wait"
	mv ${build_tmp_folder} "${build_folder}"
}

export -f parameter_set_decoding
export -f build_codelet

run() {
	runId=$@


	variants="REF LS FP DL1 FES"
	variants="ORG"
	linear_sizes="10000"




	memory_loads="0"
	num_cores="1"
	num_cores="1 14 28"
	num_cores="28"
	prefetchers="0"
	frequencies="2200000"


	#prefix="/nfs/fx/home/cwong29/working/NR-scripts"
	prefix=$(readlink -f ../../..)
	nr_prefix="${prefix}/nr-codelets/numerical_recipes"
	galois_prefix="${prefix}/galois_codelets"

	lin_s1_prefix="${nr_prefix}/1D_loop-Stride_1"


	galois_lonestar_prefix="${galois_prefix}/lonestar"


	declare -gA name2path
	declare -gA name2sizes
	declare -ga run_codelets



#	fill_codelet_maps "${lin_s1_prefix}" "${linear_sizes}"
#	fill_codelet_maps "${galois_lonestar_prefix}" "${linear_sizes}"


	# Get rid of peel
	name2sizes[balanc_3_de]="8000"
	name2sizes[grbBFS]="livejournal indochina-2004 rmat24 road-USA twitter40"
	name2sizes[grbBFS]="livejournal"

	name2sizes[grbPR]="livejournal indochina-2004 rmat24 road-USA twitter40"
#	name2sizes[grbPR]="livejournal"
	name2sizes[grbTri]="livejournal indochina-2004 rmat24 road-USA twitter40"
#	name2sizes[grbTri]="twitter40"
	name2sizes[grbTri]="road-USA"

	name2sizes[grbBFS]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"
	name2sizes[grbPRorig]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"
	name2sizes[grbTri]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"
	name2sizes[grbKTruss]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"
	name2sizes[grbBF]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"
	name2sizes[grbTri]="rmat20 indochina-2004 rmat26 road-USA twitter40 friendster"


	run_codelets=(
#			grbBFS
			grbPRorig
#			grbCC
#			grbTri
#			grbKTruss
#			grbBF
	)

	for codelet_name in ${run_codelets[@]}; do

			codelet_folder=${CODELET_DIR}/${codelet_name}
			name2path+=([${codelet_name}]=${codelet_folder})
			if [ ! -d ${codelet_folder} ]; then
					mkdir -p ${codelet_folder}
					pushd ${codelet_folder}
					cp ${BIN_DIR}/${codelet_name} .

					first_fun_called=$(objdump -D ${codelet_name}  |sed -n '/callq.*measure_start_/,/callq.*measure_stop_/{/callq.*measure_start_/b;/callq.*measure_stop_/b;p}' |grep callq |head -1|sed -e 's/.*<\(.*\)>.*/\1/g')

					cat <<- EOFEND >> codelet.conf
					<?xml version="1.0" ?>
					<codelet>
					    <language value="C++"/>
					    <label name="${codelet_name}"/>
					    <function name="${first_fun_called}"/>
					    <binary name="${codelet_name}"/>
					</codelet>
					EOFEND

					cat <<- EOFEND >> codelet.meta
					application name=GRAPH_ALGO
					batch name=GaloisBLAS
					code name=${codelet_name}
					codelet name=${codelet_name}
					EOFEND

					popd
			fi
	done


#runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0" runLoop
	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0,FLOP=1" runLoop
#	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0,FLOP=0" runLoop



	return


}

launchIt $0 run "$@"


