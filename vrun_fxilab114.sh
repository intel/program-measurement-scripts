#!/bin/bash -l

#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
variants="DL1 FP"
variants="ORG"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
linear_sizes="1000000 2000000 4000000 6000000 8000000 10000000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#memory_loads="0 99999"
memory_loads="0"
frequencies="800000 3500000"

linear_codelets=""
quadratic_codelets=""

prefix="/nfs/site/home/amazouz/local_disk/NR"
ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks/low_freq"
ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks"
nrsprefix="${prefix}/nr-codelets/numerical_recipes"

#linear_codelets="$linear_codelets ${ubmkprefix}/balanc_3_1_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/loads_1Sx4-movaps"

linear_codelets=""
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/four1_2/four1_2_me"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/realft_4/realft_4_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_2/toeplz_2_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_4/toeplz_4_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/tridag_1/tridag_1_de"
linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/tridag_2/tridag_2_de"

#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/four1_2/four1_2_mx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/realft_4/realft_4_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_2/toeplz_2_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_4/toeplz_4_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/tridag_1/tridag_1_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/tridag_2/tridag_2_dx"

#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_de"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_sVS_de"
#
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/balanc_3/balanc_3_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/elmhes_10/elmhes_10_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/hqr_13/hqr_13_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/mprove_9/mprove_9_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_dx"
#linear_codelets="$linear_codelets ${nrsprefix}/1D_loop-Stride_1/toeplz_1/toeplz_1_sVS_dx"

for codelet in $linear_codelets
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" | tee "$codelet/cls.log"
	# &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done

for codelet in $quadratic_codelets
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$quadratic_sizes" "$memory_loads" "$frequencies" | tee "$codelet/cls.log"
	# &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done
