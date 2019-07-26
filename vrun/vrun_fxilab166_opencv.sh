#!/bin/bash -l
export CAPE_DIR="/nfs/site/proj/alac/members/ashivam/cape-experiment-scripts/"
export OCV_DIR="/nfs/site/proj/alac/members/ashivam/opencv-4.1.0+contrib/codelets/"
source ${CAPE_DIR}/base/const.sh
source ${CAPE_DIR}/base/vrun_launcher.sh

#PUT compiler source stuff here
#source /nfs/site/proj/openmp/compilers/intel/19.0/Linux/intel64/load.sh

parameter_set_decoding () {
	codelet=$1
	datasize=$2
	repetition=$3
	rundir=$4
	if [[ $codelet == *"canny"* ]]; then
		# Create the datasize file for codelet run
		#echo "${repetition} ${datasize}" > ./codelet.data
		#echo -e "arraysize\n${datasize}" > arguments.csv
		if [ -z "$3" ]; then
			echo "-img=$2" #default 1 repetition
		else
			echo "-img=$2 -rep=$3"
		fi
	elif [[ $codelet == *"accumulate"* ]]; then 
		if [ -z "$3" ]; then
			echo "-img=$2" #default 1 repetition
		else
			echo "-img=$2 -rep=$3"
		fi
	elif [[ $codelet == *"warp"* ]]; then 
		if [ -z "$3" ]; then
			echo "-img=$2" #default 1 repetition
		else
			echo "-img=$2 -rep=$3"
		fi
	elif [[ $codelet == *"HOG"* ]]; then
		# -fn=<.yml file> -tv=<videofile> -rep=<#>
		IFS=':' read -r -a argv <<< "$2"
		if [ -z "$3" ]; then
			echo "-fn=${argv[0]} -tv=${argv[1]}" #default 1 repetition
		else
			echo "-fn=${argv[0]} -tv=${argv[1]} -rep=$3"
		fi
	fi
}

build_codelet () {
	codelet_folder="$1"
	codelet_name="$2"
	build_folder="$3"

	# Simple codelet compilation
	binary_name=$( grep "binary name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
	echo -e "Binary name \t'$binary_name'"
	# ensured it is at the same level as codelet_folder so that relative paths in Makefile is preserved it will be moved to the build_folder
	# after generating original
	build_tmp_folder=$(mktemp -d --tmpdir=${codelet_folder}/..)


	echo "Generating codelet '$codelet_folder/$codelet_name'..."

	echo "Compiler information using -v flags"
	ifort -v
	icc -v
	icpc -v

	build_files=$(find ${codelet_folder} -maxdepth 1 -type f -o -type l)
	cp ${build_files} ${build_tmp_folder}

	cd ${build_tmp_folder}

	if [[ "$ENABLE_SEP" == "1" ]]; then
		echo "SEP ENABLED MODE"
		make clean ENABLE_SEP=sep ${emon_api_flags} all
	else
		echo "EMON (NOT SEP) ENABLED MODE"
		# if [[ "$ACTIVATE_EMON_API" == "1" ]]
		# then
		# 	if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then
		# 	    make clean LIBS="measure_emon_api_dca.lib prog_api.lib" LIBPATH="-LIBPATH:../../../../../cape-common/lib -LIBPATH:z:/software/DCA/EMON_DCA_engineering_build_v01/lib64" all
		# 	else
		# 	    make clean LIBS="-lmeasure_emon_api -lprog_api -L/opt/intel/sep/bin64" LIBPATH="${PROBE_FOLDER}" all
		# 	fi
		# 	if [[ "$?" != "0" ]]
		# 	    then
		# 	    echo "ERROR! Make did not succeed in creating EMON API instrumented codelet."
		# 	    exit -1
		# 	fi
		# 	mv "$binary_name" "$codelet_name"_emon_api
		# 	cp "$codelet_name"_emon_api "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
		# fi
		# The above build steps would be outdated but preserve for reference (esp. for windows verions)
		make LIBPATH="${BASE_PROBE_FOLDER}" clean all
	fi

	# &> /dev/null
	res=$?

	if [[ "$res" != "0" ]]; then
		echo "ERROR! Make did not succeed."
		exit -1
	fi

	mv "$binary_name" "$codelet_name"
	res=$?

	if [[ "$res" != "0" ]]; then
		echo "ERROR! Move did not succeed."
		exit -1
	fi


	if [[ -e "codelet.o" ]]; then
		cp "codelet.o" "$codelet_folder/$CLS_RES_FOLDER/"
	fi

	# Should be safe because $binary_name was already renamed to $codelet_name
	make clean &> /dev/null

	echo "Codelet generation was successful."
	mv ${build_tmp_folder} "${build_folder}"
}

export -f parameter_set_decoding
export -f build_codelet

run() {
	runId=$@

	variants="ORG"
	if [[ "$ENABLE_SEP" == "1" ]]; then
		echo "SEP ENABLED MODE"
	else
		echo "EMON (NOT SEP) ENABLED MODE"
	fi

  #memory_loads="0 99999"
	memory_loads="0"
	#num_cores="2 4 8"
	num_cores="1"
	#prefetchers="0 15"
	prefetchers="0"
	#frequencies="1200000 1300000 1400000 1500000 1700000 1800000 1900000 2000000 2100000 2200000 2300000 2500000 2600000 2700000 2800000"
	frequencies="2400000"

	prefix=$(readlink -f ../..)
	ocv_prefix="${OCV_DIR}"
	# SR runs (including some original)
	declare -ga run_codelets
	declare -gA name2path
	declare -gA name2sizes

	fill_codelet_maps "${OCV_DIR}"

	name2path[canny_grad]="${OCV_DIR}/canny_grad"
	name2sizes[canny_grad]="${OCV_DIR}/data/messi5.jpg"

	name2path[canny_nograd]="${OCV_DIR}/canny_nograd"
	name2sizes[canny_nograd]="${OCV_DIR}/data/messi5.jpg"

	name2path[accumulate]="${OCV_DIR}/accumulate"
	name2sizes[accumulate]="${OCV_DIR}/data/messi5.jpg"

	name2path[accumulate_square]="${OCV_DIR}/accumulate_square"
	name2sizes[accumulate_square]="${OCV_DIR}/data/messi5.jpg"

	name2path[accumulate_product]="${OCV_DIR}/accumulate_product"
	name2sizes[accumulate_product]="${OCV_DIR}/data/messi5.jpg"

	name2path[accumulate_weighted]="${OCV_DIR}/accumulate_weighted"
	name2sizes[accumulate_weighted]="${OCV_DIR}/data/messi5.jpg"
	
	name2path[warp_affine]="${OCV_DIR}/warp_affine"
	name2sizes[warp_affine]="${OCV_DIR}/data/messi5.jpg"

	name2path[warp_perspective]="${OCV_DIR}/warp_perspective"
	name2sizes[warp_perspective]="${OCV_DIR}/data/messi5.jpg"

	name2path[HOG_detect]="${OCV_DIR}/HOG_detect"
	name2sizes[HOG_detect]="${OCV_DIR}/data/HOG_detector.yml:${OCV_DIR}/data/walkingPeople.avi"

	run_codelets=(
#		canny_grad
#		canny_nograd
		accumulate
		accumulate_square
		accumulate_product
		accumulate_weighted
#		warp_affine
#		warp_perspective
#		HOG_detect
	)

	#runLoop "${runId}" "$variants" "$memory_loads" "$frequencies"  "$num_cores" "$prefetchers" "RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0"
	# Could be shorten by exporting the variables instead
	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" \
          counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=1,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0" runLoop
	return
#	set -o pipefail # make sure pipe of tee would not reset return code.
#	echo RUN codelets : ${run_codelets[@]}
#	for codelet in ${run_codelets[@]}
#	do
#		echo PATH : ${OCV_DIR}/${codelet}
#		codelet_path=${OCV_DIR}/${codelet}
#		sizes=${name2sizes[${codelet}]}
#    input_args="${name2inputs[${codelet}]}"
#		#  echo ${codelet_path}
#		#  ls ${codelet_path}
#		#  echo "SS: ${sizes}"
#
#		echo "Launching CLS on $codelet_path...for sizes $sizes"
#		exit 1
#		${LOGGER_SH} ${runId} "Launching CLS on '$codelet_path'..."
#
#		./cls.sh "$codelet_path" "$variants" "${sizes}" "${input_args}"  "$memory_loads" "$frequencies"  "${runId}" | tee "$codelet_path/cls.log"
#		res=$?
#		if [[ "$res" != "0" ]]
#		then
#			#      echo -e "\tAn error occured! Check '$codelet_path/cls.log' for more information."
#			${LOGGER_SH} ${runId} "FAILED: Check '${codelet_path}/cls.log' for more information."
#		fi
#	done

}

launchIt $0 run "$@"
