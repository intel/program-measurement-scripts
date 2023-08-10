#!/bin/bash -l

source ../base/const.sh
source ../base/vrun_launcher.sh

#PUT compiler source stuff here
source ${COMPILER_ROOT}/compilers/intel/16.0/Linux/intel64/load0.sh

parameter_set_decoding () {
	codelet=$1
	datasize=$2
	repetition=$3
	rundir=$4

	# Create the datasize file for codelet run
	echo "${repetition} ${datasize}" > ./codelet.data
	echo -e "arraysize\n${datasize}" > arguments.csv
	echo ""
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
		make clean ENABLE_SEP=sep ${emon_api_flags} all
	else
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

	#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
	variants="REF LS FP DL1 FES"
	#variants="REF LS FP"
	#variants="REF"
	variants="ORG"

	linear_sizes="10000"



	memory_loads="0"

	#num_cores="1 2 4 8"
	num_cores="1"
	prefetchers="0"
	#prefetchers="0 15"
	#prefetchers="15"

	frequencies="2200000"

	#frequencies="1200000 1300000 1400000 1500000 1700000 1800000 1900000 2000000 2100000 2200000 2300000 2500000 2600000 2700000 2800000"


	#prefix="/nfs/fx/home/cwong29/working/NR-scripts"
	prefix=$(readlink -f ../../..)
	#ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks"
	ubmkprefix="${prefix}/nr-codelets/bws"
	nr_prefix="${prefix}/nr-codelets/numerical_recipes"

	lin_s1_prefix="${nr_prefix}/1D_loop-Stride_1"
	lin_slda_prefix="${nr_prefix}/1D_loop-Stride_LDA"
	lin_sclda_prefix="${nr_prefix}/1D_loop-Stride_CLDA"
	quad_s1_prefix="${nr_prefix}/2D_loop-Stride_1"
	quad_slda_prefix="${nr_prefix}/2D_loop-Stride_LDA"
	quadt_s1_prefix="${nr_prefix}/2DT_loop-Stride_1"


	# SR runs (including some original)
	declare -gA name2path
	declare -gA name2sizes
	declare -ga run_codelets


	fill_codelet_maps "${lin_s1_prefix}" "${linear_sizes}"

	# fill_codelet_maps ${lin_slda_prefix} "${linear_sizes}"
	# fill_codelet_maps ${lin_sclda_prefix} "${linear_clda_sizes}"
	# fill_codelet_maps ${quad_s1_prefix} "${quadratic_sizes}"
	# fill_codelet_maps ${quad_slda_prefix} "${quadratic_sizes}"
	# fill_codelet_maps ${quadt_s1_prefix} "${quadratic_sizes}"
	# fill_codelet_maps ${ubmkprefix} "${ubmk_sizes}"

	run_codelets=(
		balanc_3_de
	)



	name2sizes[balanc_3_de]="8000"

	#runLoop "${runId}" "$variants" "$memory_loads" "$frequencies"  "$num_cores" "$prefetchers" "RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0"
	# Could be shorten by exporting the variables instead
	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=0,TLB=0,LSD=0" runLoop



	return



}

launchIt $0 run "$@"
