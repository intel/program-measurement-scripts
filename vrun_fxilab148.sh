#!/bin/bash -l

source $(dirname $0)/const.sh

START_VRUN_SH=$(date '+%s')

#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
variants="REF LS FP"
#variants="REF"
variants="ORG"
#variants="REF_SAN"
#variants="FP"
#linear_sizes="2000 10000000"
#linear_sizes="1000 2000"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
#linear_sizes="1000000 2000000 4000000 6000000 8000000 10000000"
#linear_sizes="1000000 4000000 8000000 10000000"
#linear_sizes="1000 2000 4000 8000 20000  60000 100000  400000 800000 1000000  10000000"
#linear_sizes="1000 2000 1000000  10000000"
#linear_sizes="2000 100000 1000000  10000000"
#linear_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
# for ubmk branch_de
#linear_sizes="48 104 208 304 328 344 352 360 368 376 384 392 400 432 456 504 600 800 1440 2000 3000 30000"

#linear_sizes="6 13"
#linear_sizes="6 13 26 38 41 43 44 45 46 47 48 49 50 54 57 63 75 100 180 250 375 3750"


#linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#quadratic_sizes="208 304 528  1500 3000"
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
#linear_codelets="$linear_codelets ${ubmkprefix}/balanc_3_1_ubmk_stonly_de"
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

###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_de"
##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_de"
##linear_codelets="$linear_codelets ${prefix}/intel_codelets/1D_loop-Stride_1/s319/s319_se"
#linear_codelets="$linear_codelets ${prefix}/intel_codelets/1D_loop-Stride_1/s1244/s1244_se"

##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/hqr_13/hqr_13_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_de"
##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_de"
##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_me"
###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_de"
###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_1/toeplz_1_sU1_sVS_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sU1_sVS_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_1a_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/tridag_2r_1a_1_de"
###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_6/svdcmp_6_de"
###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_de"
###linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_de"

##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_de"
#linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_de"
##linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/svdcmp_14_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/svdcmp_14_break_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/svdcmp_14_rename_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/svdcmp_14_loopinv_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/svdcmp_14_rename1_ubmk_de"
#linear_codelets="$linear_codelets ${ubmkprefix}/branch_de"

#linear_codelets="$linear_codelets ${ubmkprefix}/ptr_ld_branch"

linear_codelets="$linear_codelets ${prefix}/nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_se"





#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_de"

#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sVS_dx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sVS_sx"

#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sVS_dx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sU1_sVS_dx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sVS_dx"

#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sU1_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sVS_sx"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_de"

# selected 2D loops
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_de"
###quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_me"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_se"

#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_de"
quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_de"
###quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_de"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_1/hqr_12sq/hqr_12sq_se"

###quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/hqr_12/hqr_12_se"
#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/jacobi_5/jacobi_5_se"
quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_se"





#quadratic_codelets="$quadratic_codelets ${prefix}/nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_de"



#quadratic_codelets="$quadratic_codelets ${ubmkprefix}/rstrct_29_simplified_de"


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
echo "$0 finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) ."
