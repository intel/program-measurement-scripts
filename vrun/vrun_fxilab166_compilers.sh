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
  if [[ $(basename $codelet) == "matmul_de" ]]; then
    echo "${repetition} ${datasize}" > ./codelet.data
  elif [[ $(basename $codelet) == "matmul-block_de" ]]; then
      echo "${repetition} $(echo ${datasize}|sed 's/:/ /g')" > ./codelet.data
  else
    echo "${repetition} $(echo ${datasize}|sed 's/:/ /g')" > ./codelet.data
  fi
  echo -e "arraysize\n${datasize}" > arguments.csv
  echo ""
}

get_compilers () {
	codelet_path="$1"
	# Checking codelet source language
	codelet_lang=$( grep "language value" "$( readlink -f "$codelet_path" )/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
	echo "Codelet Language: ${codelet_lang}" >&2
	if [ $codelet_lang == "Fortran" ] || [ $codelet_lang == "2" ]; then
		compilers="Intel GNU"
	elif [[ $codelet_lang == "CPP" ]]; then
		compilers="Intel GNU LLVM"
	elif [ $codelet_lang == "C" ] || [ $codelet_lang == "1" ]; then
		compilers="Intel GNU LLVM"
	else
		echo "Error: .conf file has invalid language value" >&2
		compilers="default"
	fi
	echo $compilers
}

build_codelet () {
	codelet_folder=$( readlink -f "$1" )
	codelet_name="$2"
	build_folder=$( readlink -f "$3" )
	curr_compiler="$4"
	declare -gA fortran_compiler
	declare -gA C_compiler
	declare -gA CPP_compiler
	declare -gA fortran_flags
	declare -gA C_flags
	declare -gA CPP_flags

	fortran_compiler[Intel]="ifort"
	fortran_compiler[GNU]="gfortran"

	C_compiler[Intel]="icc"
	C_compiler[GNU]="gcc"
	C_compiler[LLVM]="clang"

	CPP_compiler[Intel]="icpc"
	CPP_compiler[GNU]="g++"
	CPP_compiler[LLVM]="clang++"

	fortran_flags[Intel]="-g -O3 -align array64byte"
	fortran_flags[GNU]="-g -O3"

	C_flags[Intel]="-g -O3 -xHOST"
	C_flags[GNU]="-g -O3"
	C_flags[LLVM]="-g -O3"

	CPP_flags[Intel]="-g -O3 -xHOST"
	CPP_flags[GNU]="-g -O3"
	CPP_flags[LLVM]="-g -O3"

	codelet_lang=$( grep "language value" "$( readlink -f "$codelet_folder" )/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
	if [ $codelet_lang == "Fortran" ] || [ $codelet_lang == "2" ]; then
		curr_compiler_driver=${fortran_compiler[${curr_compiler}]}
		for flag in ${fortran_flags[${curr_compiler}]}; do
			curr_compiler_flags+=${flag}
			curr_compiler_flags+=" "
		done
		make_vars=(CF=${curr_compiler_driver} FFLAGS="${curr_compiler_flags}")
	elif [[ $codelet_lang == "CPP" ]]; then
		curr_compiler_driver=${CPP_compiler[${curr_compiler}]}
		for flag in ${CPP_flags[${curr_compiler}]}; do
			curr_compiler_flags+=${flag}
			curr_compiler_flags+=" "
		done
		make_vars=(CXX=${curr_compiler_driver} CXXFLAGS="${curr_compiler_flags}")
	elif [ $codelet_lang == "C" ] || [ $codelet_lang == "1" ]; then
		curr_compiler_driver=${C_compiler[${curr_compiler}]}
		for flag in ${C_flags[${curr_compiler}]}; do
			curr_compiler_flags+=${flag}
			curr_compiler_flags+=" "
		done
		make_vars=(CC=${curr_compiler_driver} CFLAGS="${curr_compiler_flags}")
	else
		echo "Error: Cannot find compiler (${curr_compiler}) for the specified language (${codelet_lang})"
		exit -1
	fi

	echo MAKE CONFIG: ${make_vars}

	echo mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
	mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

  # Simple codelet compilation
  binary_name=$( grep "binary name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
  echo -e "Binary name \t'$binary_name'"
  # ensured it is at the same level as codelet_folder so that relative paths in Makefile is preserved it will be moved to the build_folder
  # after generating original
  build_tmp_folder=$(mktemp -d --tmpdir=${codelet_folder}/..)


  echo "Generating codelet '$codelet_folder/$codelet_name'..."

  echo "Compiler information using -v flags"
  ${curr_compiler_driver} -v

  build_files=$(find ${codelet_folder} -maxdepth 1 -type f -o -type l)
  cp ${build_files} ${build_tmp_folder}

  cd ${build_tmp_folder}
  if [[ "$ENABLE_SEP" == "1" ]]; then
    echo make "${make_vars[@]}" clean ENABLE_SEP=sep ${emon_api_flags} all
    make "${make_vars[@]}" clean ENABLE_SEP=sep ${emon_api_flags} all
  else
	  echo make "${make_vars[@]}" LIBPATH="${BASE_PROBE_FOLDER}" clean all
	  make "${make_vars[@]}" LIBPATH="${BASE_PROBE_FOLDER}" clean all
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

	#add Compiler to compiler.csv
	echo -e "compiler,compiler_flags\n${curr_compiler_driver},${curr_compiler_flags}" > ${build_tmp_folder}/compiler.csv

  echo "Codelet generation was successful."
  mv ${build_tmp_folder} "${build_folder}"

	cp ${build_folder}/"$codelet_name" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
	res=$?
	if [[ "$res" != "0" ]]; then
		echo "ERROR! Copy of binary to binary folder failed"
		exit -1
	fi
}

export -f parameter_set_decoding
export -f build_codelet
export -f get_compilers

run() {
	runId=$@

	variants="ORG"

	linear_clda_sizes="1000"
	ubmk_sizes="100000 200000"
	linear_sizes="10000"
	quadratic_sizes="100"
	memory_loads="0"
	num_cores="1"
	prefetchers="0"
	frequencies="2400000"

	linear_codelets=""
	quadratic_codelets=""
	ptr_codelets=""

	#prefix="/nfs/fx/home/cwong29/working/NR-scripts"
	prefix=$(readlink -f ../..)
	ubmkprefix="${prefix}/nr-codelets/bws"
	nr_prefix="${prefix}/nr-codelets/numerical_recipes"
	saeed_prefix="${prefix}/intel_codelets"
	andy_prefix="${prefix}/andy_codelets/invitro"
	galois_prefix="${prefix}/galois_codelets"

	lin_s1_prefix="${nr_prefix}/1D_loop-Stride_1"
	lin_slda_prefix="${nr_prefix}/1D_loop-Stride_LDA"
	lin_sclda_prefix="${nr_prefix}/1D_loop-Stride_CLDA"
	quad_s1_prefix="${nr_prefix}/2D_loop-Stride_1"
	quad_slda_prefix="${nr_prefix}/2D_loop-Stride_LDA"
	quadt_s1_prefix="${nr_prefix}/2DT_loop-Stride_1"

	saeed_lin_s1_prefix="${saeed_prefix}/1D_loop-Stride_1"
	andy_lin_s1_prefix="${andy_prefix}/1D_loop-Stride_1"
	andy_quad_s1_prefix="${andy_prefix}/2D_loop-Stride_1"
	galois_lonestar_prefix="${galois_prefix}/lonestar"

	# SR runs (including some original)
	declare -gA name2path
	declare -gA name2sizes
	declare -ga run_codelets

	fill_codelet_maps "${lin_s1_prefix}" "${linear_sizes}"
	fill_codelet_maps "${saeed_lin_s1_prefix}" "${linear_sizes}"
	fill_codelet_maps "${andy_lin_s1_prefix}" "${linear_sizes}"
	fill_codelet_maps "${andy_quad_s1_prefix}" "${linear_sizes}"
	fill_codelet_maps "${galois_lonestar_prefix}" "${linear_sizes}"
	fill_codelet_maps ${lin_slda_prefix} "${linear_sizes}"
	fill_codelet_maps ${lin_sclda_prefix} "${linear_clda_sizes}"
	fill_codelet_maps ${quad_s1_prefix} "${quadratic_sizes}"
	fill_codelet_maps ${quad_slda_prefix} "${quadratic_sizes}"
	fill_codelet_maps ${quadt_s1_prefix} "${quadratic_sizes}"
	fill_codelet_maps ${ubmkprefix} "${ubmk_sizes}"

	name2sizes[balanc_3_de]="200000"
	name2sizes[balanc_3_sVS_de]="200000"
	name2sizes[elmhes_10_de]="200000"
	name2sizes[elmhes_10_sVS_de]="200000"
	name2sizes[elmhes_11_de]="10000"
	name2sizes[elmhes_11_sVS_de]="10000"
	name2sizes[four1_2_me]="200000"
	name2sizes[hqr_15_se]="6000"
	name2sizes[hqr-sq_12_se]="544"
	name2sizes[hqr-sq_12_sVS_se]="544"
	name2sizes[lop_13_de]="354"
	name2sizes[lop_13_sVS_de]="354"
	name2sizes[ludcmp-sq_4_se]="544"
	name2sizes[ludcmp-sq_4_sVS_se]="544"
	name2sizes[matadd-flb_16_de]="352"
	name2sizes[matadd-flb_16_sVS_de]="352"
	name2sizes[mprove_8_me]="400"
	name2sizes[mprove_8_sVS_me]="400"
	name2sizes[mprove_9_de]="200000"
	name2sizes[mprove_9_sVS_de]="200000"
	name2sizes[ptr1_movaps_branch]="10000"
	name2sizes[realft_4_de]="200000"
	name2sizes[relax2_26_de]="306"
	name2sizes[relax2_26_sVS_de]="306"
	name2sizes[rstrct_29_de]="355"
	name2sizes[rstrct_29_sVS_de]="355"
	name2sizes[s1244_se]="59961"
	name2sizes[s1244_sVS_se]="59961"
	name2sizes[s319_se]="60000"
	name2sizes[s319_sVS_se]="60000"
	name2sizes[svbksb_3_se]="400"
	name2sizes[svbksb_3_sVS_se]="400"
	name2sizes[svdcmp_11_de]="10000"
	name2sizes[svdcmp_11_sVS_de]="10000"
	name2sizes[svdcmp_13_de]="200000"
	name2sizes[svdcmp_13_sVS_de]="200000"
	name2sizes[svdcmp_14_de]="200000"
	name2sizes[svdcmp_14_sVS_de]="200000"
	name2sizes[svdcmp_6_de]="10000"
	name2sizes[svdcmp_6_sVS_de]="10000"
	name2sizes[toeplz_1_de]="100001"
	name2sizes[toeplz_1_sVS_de]="100001"
	name2sizes[toeplz_2_de]="200000"
	name2sizes[toeplz_4_de]="200000"
	name2sizes[tridag_1_de]="10000"
	name2sizes[tridag_2_de]="200000"

	run_codelets=(
#		balanc_3_de
#		balanc_3_sVS_de
#		elmhes_10_de
#		elmhes_10_sVS_de
#		elmhes_11_de
#		elmhes_11_sVS_de
#		four1_2_me
#		hqr_15_se
#		hqr-sq_12_se
#		hqr-sq_12_sVS_se
#		lop_13_de
#		lop_13_sVS_de
#		ludcmp-sq_4_se
#		ludcmp-sq_4_sVS_se
#		matadd-flb_16_de
#		matadd-flb_16_sVS_de
#		mprove_8_me
#		mprove_8_sVS_me
#		mprove_9_de
#		mprove_9_sVS_de
#		ptr1_vmovaps_branch
#		realft_4_de
#		relax2_26_de
#		relax2_26_sVS_de
#		rstrct_29_de
#		rstrct_29_sVS_de
#		s1244_se
#		s1244_sVS_se
#		s319_se
#		s319_sVS_se
#		svbksb_3_se
#		svbksb_3_sVS_se
#		svdcmp_11_de
#		svdcmp_11_sVS_de
#		svdcmp_13_de
#		svdcmp_13_sVS_de
#		svdcmp_14_de
#		svdcmp_14_sVS_de
#		svdcmp_6_de
#		svdcmp_6_sVS_de
#		toeplz_1_de
#		toeplz_1_sVS_de
#		toeplz_2_de
#		toeplz_4_de
		tridag_1_de
		tridag_2_de
	)

	runId="${runId}" variants="$variants" memory_loads="$memory_loads" frequencies="$frequencies"  num_cores="$num_cores" prefetchers="$prefetchers" counter_list_override="RESOURCE=1,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=1,MEM_ROWBUFF=0,MEM_TRAFFIC=1,MEM_HIT=1,TLB=1,LSD=0" runLoop

	return
}
launchIt $0 run "$@"
