#!/bin/bash -l


variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
memory_loads="0 99999"
frequencies="1200000 2500000"

linear_codelets=""
quadratic_codelets=""


#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s1244/s1244_sp/s1244_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s1244/s1244_sp/s1244_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s1244/s1244_sp/s1244_1_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s1244/s1244_sp/s1244_1_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s211/s211_sp/s211_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s211/s211_sp/s211_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s211/s211_sp/s211_1_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s211/s211_sp/s211_1_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s261/s261_sp/s261_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s261/s261_sp/s261_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s261/s261_sp/s261_1_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s261/s261_sp/s261_1_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_1_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_1_sp_sse_icc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_2_sp_sse_gcc"
#linear_codelets="$linear_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s319/s319_sp/s319_2_sp_sse_icc"
#quadratic_codelets="$quadratic_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s231/s231_sp/s231_sp_sse_gcc"
#quadratic_codelets="$quadratic_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s231/s231_sp/s231_sp_sse_icc"
#quadratic_codelets="$quadratic_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s231/s231_sp/s231_1_sp_sse_gcc"
#quadratic_codelets="$quadratic_codelets /localdisk/vincent/intel_codelets/saeed_codelets/dongarra_up/nr_format/s231/s231_sp/s231_1_sp_sse_icc"


#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_mp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_mp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_dp_avx"
##linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_3/toeplz_3_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_dp_sse"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_dp_avx"
#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_dp_sse"

#linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_dp_avx"
linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_dp_sse"
linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_dp_avx"
linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_dp_sse"
linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_6/svdcmp_6_dp_avx"
linear_codelets="$linear_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_6/svdcmp_6_dp_sse"

##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_sp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_sp_sse"

##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_dp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_dp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_mp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_mp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sp_sse"

##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_dp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_dp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_dp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_dp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_dp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_dp_sse"

##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sp_sse"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sp_avx"
##quadratic_codelets="$quadratic_codelets /localdisk/vincent/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sp_sse"


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
