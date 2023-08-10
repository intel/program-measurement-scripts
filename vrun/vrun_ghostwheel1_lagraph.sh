#!/bin/bash -l


#PUT compiler source stuff here
#source ${COMPILER_ROOT}/compilers/intel/16.0/Linux/intel64/load0.sh
# Order important below.  Let later sources take higher precedence
source /opt/intel/sep/sep_vars.sh > /dev/null
source /workspace/dwong/intel/bin/compilervars.sh intel64
source /workspace/dwong/working/NR-scripts/galois/src/scripts/iss_load_modules.sh
module load gcc/7.2
module load boost/1.69

export DISABLE_CQA=1
source ../base/const.sh
source ../base/vrun_launcher.sh


BIN_DIR=/workspace/dwong/working/NR-scripts/galois/apps

#export GRAPH_DIR=/nfs/site/proj/alac/data/graph-algorithms-data/Galois/GaloisBLAS/Galois.clean.version/lonestar/graphBLASwrapper/test_inputs
export GRAPH_DIR=/workspace/dwong/working/NR-scripts/galois/inputs
CODELET_DIR=$(dirname $(readlink -f $0))/codelets
export GALOIS_DO_NOT_BIND_THREADS=1


parameter_set_decoding () {
	codelet=$1
	datasize=$2
	repetition=$3
	rundir=$4
	num_cores=$5

	# Create the datasize file for codelet run
	sn=$(cat ${GRAPH_DIR}/${datasize}.source)
	gd=${GRAPH_DIR}
	
	
	echo "${repetition} ${datasize}" > ./codelet.data
	echo -e "arraysize\n${datasize}" > arguments.csv
	
        if [[ ${datasize} == 'road-USA-W' || ${datasize} == 'road-USA' ]]; then
	    ktrussNum=4
        else
	    ktrussNum=7
        fi
	
        if [[ $(basename $codelet) == "galBFS" || $(basename $codelet) == "grbSSSP" || $(basename $codelet) == "grbSSSP64" ]]; then
            echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition}"
        elif [[ $(basename $codelet) == 'grbBFS' ]]; then
	    if [[ ${datasize} == road-* ]]; then
		echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition} -m=1"
	    elif [[ ${datasize} == 'eukarya' || ${datasize} == 'uk2007' ]]; then
		echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition} -m=2"
	    else
		echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition}"
	    fi
        elif [[ $(basename $codelet) == 'galSSSP' || $(basename $codelet) == 'galSSSP64' || $(basename $codelet) == 'galSSSPdeltaStep' || $(basename $codelet) == 'galSSSPtopo' ]]; then
	    if [[ ${datasize} == 'eukarya' ]]; then
		echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition} -delta=20"
	    else
		echo "${gd}/${datasize}.cgr -startNode=${sn} -t=${num_cores} -rep=${repetition}"
	    fi
        elif [[ $(basename $codelet) == 'grbKTruss' ]]; then
	    if [[ ${datasize} == road-* ]]; then
		echo "${gd}/${datasize}.cgr -k=${ktrussNum} -t=${num_cores} -rep=${repetition} -m=1"
	    else
		echo "${gd}/${datasize}.cgr -k=${ktrussNum} -t=${num_cores} -rep=${repetition} -m=0"
	    fi
        elif [[ $(basename $codelet) == 'galKTruss' ]]; then
            echo "${gd}/${datasize}.csgr -trussNum=${ktrussNum} -t=${num_cores} -rep=${repetition}"
        elif [[ $(basename $codelet) == 'galPR' || $(basename $codelet) == 'galPRinv' || $(basename $codelet) == 'galPRaos' ]]; then
            echo "${gd}/${datasize}.ctgr -t=${num_cores} -rep=${repetition}"
        elif [[ $(basename $codelet) == 'galCC' || $(basename $codelet) == 'galCCedgeTileAsync' ]]; then
            echo "${gd}/${datasize}.csgr -t=${num_cores} -rep=${repetition}"
        elif [[ $(basename $codelet) == 'galTri' || $(basename $codelet) == 'galTriNS' ]]; then
	    echo "${gd}/${datasize}.csgr -t=${num_cores} -rep=${repetition}"
        else
            echo "${gd}/${datasize}.cgr -t=${num_cores} -rep=${repetition}"
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
	num_cores="56"
	prefetchers="0"
	# Use turbo boost
	frequencies="2201000"


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

	# Need to add friendster and twitter40 and uk2007

	name2sizes[grbBFS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[grbSSSP]="rmat22 indochina-2004 rmat26 road-USA road-USA-W"
        name2sizes[grbSSSP64]="eukarya"
        name2sizes[grbCC]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[grbPRorig]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[grbTri]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[grbKTruss]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"


	name2sizes[galBFS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galSSSP]="rmat22 indochina-2004 rmat26 road-USA road-USA-W"
        name2sizes[galSSSP64]="eukarya"
        name2sizes[galCC]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galPR]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galPRinv]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galTri]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galTriNS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"
        name2sizes[galKTruss]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W"


	name2sizes[grbBFS]="livejournal"
        name2sizes[grbSSSP]="livejournal"
        name2sizes[grbSSSP64]="livejournal"
        name2sizes[grbCC]="livejournal"
        name2sizes[grbPRorig]="livejournal"
        name2sizes[grbTri]="livejournal"
        name2sizes[grbKTruss]="livejournal"

	name2sizes[galBFS]="livejournal"
        name2sizes[galSSSP]="livejournal"
        name2sizes[galSSSP64]="livejournal"
        name2sizes[galCC]="livejournal"
        name2sizes[galPR]="livejournal"
        name2sizes[galPRinv]="livejournal"
        name2sizes[galTri]="livejournal"
        name2sizes[galTriNS]="livejournal"
        name2sizes[galKTruss]="livejournal"

	# name2sizes[grbBFS]="twitter40"
        # name2sizes[grbSSSP]="twitter40"
        # name2sizes[grbSSSP64]="twitter40"
        # name2sizes[grbCC]="twitter40"
        # name2sizes[grbPRorig]="twitter40"
        # name2sizes[grbTri]="twitter40"
        # name2sizes[grbKTruss]="twitter40"

	# name2sizes[galBFS]="twitter40"
        # name2sizes[galSSSP]="twitter40"
        # name2sizes[galSSSP64]="twitter40"
        # name2sizes[galCC]="twitter40"
        # name2sizes[galPR]="twitter40"
        # name2sizes[galPRinv]="twitter40"
        # name2sizes[galTri]="twitter40"
        # name2sizes[galTriNS]="twitter40"
        # name2sizes[galKTruss]="twitter40"

	# name2sizes[grbBFS]="friendster"
        # name2sizes[grbSSSP]="friendster"
        # name2sizes[grbSSSP64]="friendster"
        # name2sizes[grbCC]="friendster"
        # name2sizes[grbPRorig]="friendster"
        # name2sizes[grbTri]="friendster"
        # name2sizes[grbKTruss]="friendster"

	# name2sizes[galBFS]="friendster"
        # name2sizes[galSSSP]="friendster"
        # name2sizes[galSSSP64]="friendster"
        # name2sizes[galCC]="friendster"
        # name2sizes[galPR]="friendster"
        # name2sizes[galPRinv]="friendster"
        # name2sizes[galTri]="friendster"
        # name2sizes[galTriNS]="friendster"
        # name2sizes[galKTruss]="friendster"

	# name2sizes[grbBFS]="uk2007"
        # name2sizes[grbSSSP]="uk2007"
        # name2sizes[grbSSSP64]="uk2007"
        # name2sizes[grbCC]="uk2007"
        # name2sizes[grbPRorig]="uk2007"
        # name2sizes[grbTri]="uk2007"
        # name2sizes[grbKTruss]="uk2007"

	# name2sizes[galBFS]="uk2007"
        # name2sizes[galSSSP]="uk2007"
        # name2sizes[galSSSP64]="uk2007"
        # name2sizes[galCC]="uk2007"
        # name2sizes[galPR]="uk2007"
        # name2sizes[galPRinv]="uk2007"
        # name2sizes[galTri]="uk2007"
        # name2sizes[galTriNS]="uk2007"
        # name2sizes[galKTruss]="uk2007"


	name2sizes[grbBFS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbSSSP]="rmat22 indochina-2004 rmat26 road-USA road-USA-W twitter40 friendster uk2007"
        name2sizes[grbSSSP64]="eukarya"
        name2sizes[grbCC]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbPRorig]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbTri]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbTri7]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbTri_sorted]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbTri7_sorted]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[grbKTruss]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"


	name2sizes[galBFS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galSSSP]="rmat22 indochina-2004 rmat26 road-USA road-USA-W twitter40 friendster uk2007"
        name2sizes[galSSSP64]="eukarya"
        name2sizes[galCC]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galPR]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galPRinv]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galTri]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galTriNS]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"

        name2sizes[galCCedgeTileAsync]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galPRaos]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galSSSPdeltaStep]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galSSSPtopo]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"
        name2sizes[galSSSPtopo]="indochina-2004 twitter40"
        name2sizes[grbPRResidual]="rmat22 indochina-2004 rmat26 road-USA eukarya road-USA-W twitter40 friendster uk2007"

        name2sizes[galPR]="rmat22 indochina-2004 road-USA eukarya road-USA-W"
        name2sizes[galPRinv]="rmat22 indochina-2004 road-USA eukarya road-USA-W"

	run_codelets=(
            # grbBFS
	    # grbSSSP
	    # grbSSSP64
	    # grbCC
            # grbPRorig
	    # grbTri
	    # grbTri7
	    # grbTri_sorted
	    # grbTri7_sorted


	    # galCCedgeTileAsync
	    # galPRaos
	    # galSSSPdeltaStep
	    # grbPRResidual

	    galSSSPtopo

            # galBFS
	    # galSSSP
	    # galSSSP64
	    # galCC
            # galPR
            # galPRinv
	    # galTri
	    # galTriNS

	    # grbKTruss	    
	    # galKTruss
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
#	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0,FLOP=1,UOP_ISSUE_RETIRE=1" runLoop
	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0,FLOP=0,UOP_ISSUE_RETIRE=1" runLoop
#	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0,FLOP=0,UOP_ISSUE_RETIRE=1" runLoop


	return


}

launchIt $0 run "$@"


