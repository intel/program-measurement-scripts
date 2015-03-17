#!/bin/bash -l

START_VRUN_SH=$(date '+%s')

#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
variants="REF LS FP"
variants="REF"
#linear_sizes="2000 10000000"
#linear_sizes="1000 2000"
#linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
#linear_sizes="1000000 2000000 4000000 6000000 8000000 10000000"
linear_sizes="1000000 4000000 8000000 10000000"
#linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#memory_loads="0 99999"
memory_loads="0"
frequencies="1200000 2800000"
frequencies="2800000"

linear_codelets=""
quadratic_codelets=""


prefix="/nfs/fx/home/cwong29/working/NR-scripts"
ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks"

#linear_codelets="${ubmkprefix}/*"
#linear_codelets="$linear_codelets ${ubmkprefix}/balanc_3_1_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_ls_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_st_only_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_st_1sonly_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_ld_1sonly_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_ld_bigstride_1sonly_se"

#linear_codelets="$linear_codelets ${ubmkprefix}/s319_st_bigstride_1sonly_se"

#linear_codelets="$linear_codelets ${ubmkprefix}/s319_ldst_1sonly_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_ldst_no_pxor_1sonly_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/s319_se"
#linear_codelets="$linear_codelets ${ubmkprefix}/mprove_9_ubmk_de"

linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_de"
#linear_codelets="$linear_codelets ${prefix}/intel_codelets/1D_loop-Stride_1/s319/s319_se"

#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_me"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_1a_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_1a_1_de"








#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_de"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_de"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_de"

#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_dx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_dx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_dx"

#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_se"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_sx"




for codelet in $linear_codelets
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" | tee "$codelet/cls.log"
	#./cls_get_metrics.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" | tee "$codelet/cls.log"
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
END_VRUN_SH=$(date '+%s')
ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))
echo "$0 finished in ${ELAPSED_VRUN_SH} seconds."
