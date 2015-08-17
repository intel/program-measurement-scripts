#!/bin/bash -l

source $(dirname $0)/const.sh
source ./vrun_launcher.sh

run() {
    runId=$@




#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
#variants="REF LS FP"
variants="ORG"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#memory_loads="0 99999"
memory_loads="0"
frequencies="1200000"
frequencies="1200000 2500000"
frequencies="2500000"

linear_codelets=""
quadratic_codelets=""

prefix="/localdisk/amazouz/NR_DW"
ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks"
nr_prefix="${prefix}/nr-codelets/numerical_recipes"
saeed_prefix="${prefix}/intel_codelets/1D_loop-Stride_1"

lin_s1_prefix="${nr_prefix}/1D_loop-Stride_1"
lin_slda_prefix="${nr_prefix}/1D_loop-Stride_LDA"
lin_sclda_prefix="${nr_prefix}/1D_loop-Stride_CLDA"
quad_s1_prefix="${nr_prefix}/2D_loop-Stride_1"
quad_slda_prefix="${nr_prefix}/2D_loop-Stride_LDA"
quadt_s1_prefix="${nr_prefix}/2DT_loop-Stride_1"

#linear_sizes="2000 10000 400000 8000000"
#quadratic_sizes="208 240 400 2500 3000"

linear_sizes="1000 2000 8000 10000 100000 200000"
quadratic_sizes="208 240 304 352 400 528"
ptr_sizes="200 400 1000 2000 10000 20000"

linear_codelets=""
quadratic_codelets=""
ptr_codelets=""

linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_de"
linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_de"
linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_me"
linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_de"
linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_de"
linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_de"
linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_de"
linear_codelets+=" ${saeed_prefix}/s319/s319_se"
linear_codelets+=" ${saeed_prefix}/s1244/s1244_se"
quadratic_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_se"
quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_de"
quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_me"
quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_se"
quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_de"
quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_de"
quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_de"
quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_se"
quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_se"
quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_se"

linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_sVS_de"
quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sVS_de"
quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sVS_se"
quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sVS_de"
quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sVS_de"

ptr_codelets+=" ${ubmkprefix}/ptr_ld_branch"

#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_dx"
#linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_dx"
#linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_mx"
#linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_dx"
#linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_dx"
#linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_dx"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_dx"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_dx"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_dx"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_dx"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_dx"
#linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_dx"
#linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_dx"
#linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_dx"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_dx"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_dx"
#quadratic_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_sx"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_dx"
#quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_mx"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sx"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_dx"
#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sx"

linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro_de"
linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_ro_de"
linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_ro_me"
linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_ro_de"
linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_ro_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_ro_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_ro_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_3/toeplz_3_ro_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_ro_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_ro_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_ro_de"
linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_ro_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_ro_de"
quadratic_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_ro_se"
quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_ro_de"
quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_ro_me"
quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_ro_se"
quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_ro_de"
quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_ro_de"
quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_ro_de"
quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_ro_se"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro1r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro2r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro3r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro5r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro6r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro7r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro8r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro9r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro10r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro11r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro12r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro24r_de"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro36r_de"
########################################################################
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
linear_sizes="8000 200000"
linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sr_de"
linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_sr_de"
linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_sr_de"
linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_sr_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_sr_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_sr_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_sr_de"
linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_sr_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_sr_de"
linear_codelets+=" ${saeed_prefix}/s1244/s1244_sr_se"

linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sr_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_sr_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_sr_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_sr_sVS_de"
linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_sr_sVS_de"
linear_codelets+=" ${saeed_prefix}/s1244/s1244_sr_sVS_se"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
linear_sizes="2000 100000"
linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_de"
linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_sr_de"
linear_codelets+=" ${saeed_prefix}/s319/s319_sr_se"
linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_sVS_de"
linear_codelets+=" ${saeed_prefix}/s319/s319_sr_sVS_se"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
linear_sizes="10000 200000"
linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_sr_me"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
linear_sizes="1000 10000"
linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_sr_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_sr_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_de"
ptr_codelets+=" ${ubmkprefix}/ptr_ld_branch"
linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_sr_sVS_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_sr_sVS_de"
linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_sVS_de"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
linear_sizes="208 528"
quadratic_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_rs_se"

quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_se"
quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sr_se"
quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sVS_se"
quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sr_sVS_se"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
quadratic_sizes="100 240"

quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sr_de"
quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sr_de"
quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sr_sVS_de"
quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sr_sVS_de"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
quadratic_sizes="100 352"
quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_sr_de"
quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sr_de"
quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_sr_sVS_de"
quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sr_sVS_de"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
quadratic_sizes="100 400"
quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_sr_me"
quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sr_se"
quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_sr_sVS_me"
quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sr_sVS_se"

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
########################################################################
linear_codelets=""
quadratic_codelets=""
ptr_codelets=""
########################################################################

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

for codelet in $ptr_codelets
do
	${LOGGER_SH} ${runId} "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$ptr_sizes" "$memory_loads" "$frequencies"  "${runId}" | tee "$codelet/cls.log"
	# &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done


}

launchIt $0 run "$@"


