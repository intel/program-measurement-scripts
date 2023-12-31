#!/bin/bash -l

source $(dirname $0)/const.sh
source ./vrun_launcher.sh

run() {
	runId=$@




	#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
	variants="REF LS FP DL1 FES"
	linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000
	10000000 20000000 40000000 60000000 80000000 100000000"
	quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
	#memory_loads="0 99999"
	memory_loads="0"
	frequencies="800000 3200000"

	linear_codelets=""
	quadratic_codelets=""


	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_me"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_mx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_sVS_dx"
	inear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_sU1_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_sU1_sVS_dx"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_sVS_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_sVS_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_dx"
	linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_de"
	##linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_dx"

	#linear_codelets="$linear_codelets /localdisk/amazouz/intel_codelets/1D_loop-Stride_1/s1244/s1244_se"
	#linear_codelets="$linear_codelets /localdisk/amazouz/intel_codelets/1D_loop-Stride_1/s1244/s1244_sVS_se"
	#linear_codelets="$linear_codelets /localdisk/amazouz/intel_codelets/1D_loop-Stride_1/s319/s319_se"
	#linear_codelets="$linear_codelets /localdisk/amazouz/intel_codelets/1D_loop-Stride_1/s319/s319_sVS_se"
	#
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_de"
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_dx"
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_de"
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_dx"
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_6/svdcmp_6_de"
	#linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_6/svdcmp_6_dx"

	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_sx"

	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_me"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_mx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_dx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_de"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_dx"

	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_se"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_sx"
	#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sx"


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

}

launchIt $0 run "$@"


