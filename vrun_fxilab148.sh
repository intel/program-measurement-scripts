#!/bin/bash -l

source $(dirname $0)/const.sh
source ./vrun_launcher.sh

run() {
    runId=$@

#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
#variants="REF LS FP"
#variants="REF"
variants="ORG"
#variants="REF_SAN"
#variants="FP"
#variants="LS"
#linear_sizes="2000 10000000"
#linear_sizes="1000 2000"

#linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"

#linear_sizes="2000 8000 80000 200000 600000 1000000"
#linear_sizes="2000 10000 400000 8000000"
#linear_sizes="2000 8000 400000"
# Even small datasizes for LDA code (like svd11)
#linear_sizes="600 800 1000"
#linear_sizes="1000"
#linear_sizes="400 2000 10000"
linear_clda_sizes="1000 10000"
#ptr_sizes="400 2000 10000 800000"
#ptr_sizes="10000 800000"
#ptr_sizes="800000"
#ptr_sizes="100 200 400 600 800 1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000"
#ptr_sizes="600 1000"
ptr_sizes="200 1000 10000"
#linear_sizes="400000"
#linear_sizes="200000 400000 600000 800000"
#linear_sizes="2000 10000"
#linear_sizes="1000 10000"
#linear_sizes="10000"
# Will check size problem below for hqr13 and toe3
#linear_sizes="100 1000 10000 400000"
#linear_sizes="3000 4000 5000"
linear_sizes="1000 10000 400000"


#linear_sizes="800000"
#linear_sizes="100 200 400 600 800"
#linear_sizes="1100 1200 1400 1600 1800"
#linear_sizes="1000000 2000000 4000000 6000000 8000000 10000000"
#linear_sizes="1000000 4000000 8000000 10000000"
#linear_sizes="1000 2000 4000 8000 20000  60000 100000  400000 800000 1000000  10000000"
#linear_sizes="100000  400000 800000 1000000  10000000"
#linear_sizes="1000 2000 1000000  10000000"
#linear_sizes="2000 100000 1000000  10000000"
#linear_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
# for ubmk branch_de
#linear_sizes="48 104 208 304 328 344 352 360 368 376 384 392 400 432 456 504 600 800 1440 2000 3000 30000"

#linear_sizes="6 13"
#linear_sizes="6 13 26 38 41 43 44 45 46 47 48 49 50 54 57 63 75 100 180 250 375 3750"


#linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000"
#quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#quadratic_sizes="800"
#quadratic_sizes="1500 3000 6000"
#quadratic_sizes="208 304 528  1500 3000"
#quadratic_sizes="208 352 608 928 1200 1500 2000 3000"
#quadratic_sizes="208 352 608 928 1300 2500"
#quadratic_sizes="208 240 400 2500 3000"
#quadratic_sizes="400"
#quadratic_sizes="928 1008 1100"
#quadratic_sizes="928"
#quadratic_sizes="10 30 100 400 630 928"
#quadratic_sizes="100 400"
# try to follow Hafid's sizes
#quadratic_sizes="100 208 240 352 400 528"
#quadratic_sizes="100"
#quadratic_sizes="10 30 100 400"
quadratic_sizes="208 400 528"

#quadratic_sizes="400 2500"
#memory_loads="0 99999"
memory_loads="0"
#frequencies="1200000 2800000"
frequencies="2800000"
#frequencies="1200000 2000000 2800000"
#frequencies="1200000 1300000 1400000 1500000 1700000 1800000 1900000 2000000 2100000 2200000 2300000 2500000 2600000 2700000 2800000"
#frequencies="1200000"

linear_codelets=""
quadratic_codelets=""
ptr_codelets=""


prefix="/nfs/fx/home/cwong29/working/NR-scripts"
ubmkprefix="${prefix}/nr-codelets/bws/nr_ubmks"
nr_prefix="${prefix}/nr-codelets/numerical_recipes"
saeed_prefix="${prefix}/intel_codelets"   

lin_s1_prefix="${nr_prefix}/1D_loop-Stride_1"
lin_slda_prefix="${nr_prefix}/1D_loop-Stride_LDA"
lin_sclda_prefix="${nr_prefix}/1D_loop-Stride_CLDA"
quad_s1_prefix="${nr_prefix}/2D_loop-Stride_1"
quad_slda_prefix="${nr_prefix}/2D_loop-Stride_LDA"
quadt_s1_prefix="${nr_prefix}/2DT_loop-Stride_1"

saeed_lin_s1_prefix="${saeed_prefix}/1D_loop-Stride_1"




#linear_codelets="${ubmkprefix}/*"

#linear_codelets+=" ${ubmkprefix}/balanc_3_1_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/balanc_3_1_ubmk_stonly_de"
#linear_codelets+=" ${ubmkprefix}/s319_ls_se"
#linear_codelets+=" ${ubmkprefix}/s319_st_only_se"
#linear_codelets+=" ${ubmkprefix}/s319_st_1sonly_se"
#linear_codelets+=" ${ubmkprefix}/s319_ld_1sonly_se"
#linear_codelets+=" ${ubmkprefix}/s319_ld_bigstride_1sonly_se"


#linear_codelets+=" ${ubmkprefix}/s319_st_bigstride_1sonly_se"

#linear_codelets+=" ${ubmkprefix}/s319_ldst_1sonly_se"
#linear_codelets+=" ${ubmkprefix}/s319_ldst_no_pxor_1sonly_se"
#linear_codelets+=" ${ubmkprefix}/s319_se"
#linear_codelets+=" ${ubmkprefix}/mprove_9_ubmk_de"

#linear_codelets+=" ${saeed_lin_s1_prefix}/s319/s319_se"
#linear_codelets+=" ${saeed_lin_s1_prefix}/s1244/s1244_se"


#linear_codelets+=" ${ubmkprefix}/tridag_2r_de"
#linear_codelets+=" ${ubmkprefix}/tridag_2r_1a_de"
#linear_codelets+=" ${ubmkprefix}/tridag_2r_1a_1_de"
#ptr_codelets+=" ${ubmkprefix}/ptr_ld_branch"

#linear_codelets+=" ${ubmkprefix}/svdcmp_14_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/svdcmp_14_break_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/svdcmp_14_rename_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/svdcmp_14_loopinv_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/svdcmp_14_rename1_ubmk_de"
#linear_codelets+=" ${ubmkprefix}/branch_de"
#quadratic_codelets+=" ${ubmkprefix}/rstrct_29_simplified_de"


#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_wo_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro1r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro2r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro3r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro5r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro6r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro7r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro8r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro9r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro10r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro11r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro12r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro24r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_ro36r_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_wo1w_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_wo4w_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_dx"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_mulsd_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_mulmovsd_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_2mulmovsd_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_3mulmovsd_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_4mulmovsd_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sU1_sVS_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sU4_sVS_de"
#linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_sU4_sVS_Svec_de"
#linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_de"
#linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/elmhes_10/elmhes_10_dx"
#linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_me"
#linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_ro_me"
#linear_codelets+=" ${lin_s1_prefix}/four1_2/four1_2_mx"
# bugged
#linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_de"
#linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_de"

#linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_de"
#linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/realft_4/realft_4_dx"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_de"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_sU1_sVS_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_3/toeplz_3_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_de"
#linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_de"
#linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_de"

# more RO ones
#linear_codelets+=" ${lin_s1_prefix}/mprove_9/mprove_9_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_13/svdcmp_13_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/svdcmp_14/svdcmp_14_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_2/toeplz_2_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_3/toeplz_3_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/toeplz_4/toeplz_4_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/tridag_1/tridag_1_ro_de"
#linear_codelets+=" ${lin_s1_prefix}/tridag_2/tridag_2_ro_de"

#linear_codelets+=" ${saeed_lin_s1_prefix}/s319/s319_ro_se"
#linear_codelets+=" ${saeed_lin_s1_prefix}/s1244/s1244_ro_se"



#linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_de"
#linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_ro_de"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_de"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_de"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_ro_de"
#linear_codelets+=" ${lin_sclda_prefix}/elmhes_11/elmhes_11_dx"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_dx"
#linear_codelets+=" ${lin_sclda_prefix}/svdcmp_11/svdcmp_11_dx"



#linear_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_se"

# more RO ones
# somehow broken - need to fix script.
#linear_codelets+=" ${lin_slda_prefix}/hqr_15/hqr_15_ro_se"



#quadratic_codelets+=" ${quad_s1_prefix}/hqr_12sq/hqr_12sq_se"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_de"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sU1_sVS_dx"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sVS_dx"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sU1_sVS_de"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sU1_sVS_de"
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_sVS_de"
#quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_me"
#quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_mx"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_se"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sU1_sVS_se"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sVS_se"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sU1_sVS_sx"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_sVS_sx"

# more RO ones
#quadratic_codelets+=" ${quad_s1_prefix}/matadd_16/matadd_16_ro_de"
#quadratic_codelets+=" ${quad_s1_prefix}/mprove_8/mprove_8_ro_me"
#quadratic_codelets+=" ${quad_s1_prefix}/svbksb_3/svbksb_3_ro_se"


#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13s_de"

#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_de"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sU1_sVS_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sVS_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sU1_sVS_de"
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_sVS_de"
#quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_de"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_de"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sU1_sVS_de"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sVS_de"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sU1_sVS_dx"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_sVS_dx"

# more RO ones
#quadratic_codelets+=" ${quad_slda_prefix}/lop_13/lop_13_ro_de"
#quadratic_codelets+=" ${quad_slda_prefix}/relax2_26/relax2_26_ro_de"
#quadratic_codelets+=" ${quad_slda_prefix}/rstrct_29/rstrct_29_ro_de"


#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sU1_sVS_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sVS_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sU1_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sU1_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sU1_sVS_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_sVS_sx"


# more RO ones
#quadratic_codelets+=" ${quadt_s1_prefix}/ludcmp_4/ludcmp_4_ro_se"


# Should never run jacobi again (duplicated code)
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_sU1_sVS_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_sVS_sx"
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_sU1_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_sVS_se"
#quadratic_codelets+=" ${quadt_s1_prefix}/jacobi_5/jacobi_5_se"
# Skip 2D loops for now.
#quadratic_codelets=""


# SR runs (including some original)
declare -A name2path
declare -A name2sizes


lin_s1_codelets=(
    "balanc_3/balanc_3_sr_de" "balanc_3/balanc_3_sr_sVS_de" 
    "elmhes_10/elmhes_10_sr_de" "elmhes_10/elmhes_10_sr_sVS_de" 
    "four1_2/four1_2_sr_me"
    "hqr_13/hqr_13_de" "hqr_13/hqr_13_sVS_de"
    "mprove_9/mprove_9_sr_de" "mprove_9/mprove_9_sr_sVS_de"
    "realft_4/realft_4_sr_de"
    "svdcmp_13/svdcmp_13_sr_de" "svdcmp_13/svdcmp_13_sr_sVS_de"
    "svdcmp_14/svdcmp_14_sr_de" "svdcmp_14/svdcmp_14_sr_sVS_de"
    "toeplz_1/toeplz_1_de" "toeplz_1/toeplz_1_sVS_de"
    "toeplz_2/toeplz_2_sr_de"
    "toeplz_4/toeplz_4_sr_de"
    "tridag_1/tridag_1_sr_de"
    "tridag_2/tridag_2_sr_de"
)

saeed_lin_s1_codelets=(
    "s1244/s1244_sr_se" "s1244/s1244_sr_sVS_se"
    "s319/s319_sr_se" "s319/s319_sr_sVS_se"
)

lin_sclda_codelets=(
    "elmhes_11/elmhes_11_sr_de" "elmhes_11/elmhes_11_sr_sVS_de"
    "svdcmp_11/svdcmp_11_sr_de" "svdcmp_11/svdcmp_11_sr_sVS_de"
    "svdcmp_6/svdcmp_6_de" "svdcmp_6/svdcmp_6_sVS_de"
)

lin_slda_codelets=( "hqr_15/hqr_15_sr_se" )

quad_s1_codelets=(
    "matadd_16/matadd_16_sr_de" "matadd_16/matadd_16_sr_sVS_de"
    "mprove_8/mprove_8_sr_me" "mprove_8/mprove_8_sr_sVS_me"
    "svbksb_3/svbksb_3_sr_se" "svbksb_3/svbksb_3_sr_sVS_se"
)

quad_slda_codelets=(
    "lop_13/lop_13_sr_de" "lop_13/lop_13_sr_sVS_de"
    "relax2_26/relax2_26_sr_de" "relax2_26/relax2_26_sr_sVS_de"
    "rstrct_29/rstrct_29_sr_de" "rstrct_29/rstrct_29_sr_sVS_de"
)

quadt_s1_codelets=(
    "hqr_12/hqr_12_se" "hqr_12/hqr_12_sVS_se"
    "ludcmp_4/ludcmp_4_sr_se" "ludcmp_4/ludcmp_4_sr_sVS_se"
)

ubmk_codelets=("ptr_ld_branch")

fill_codelet_maps()
{
    cnt_prefix="$1"
    cnt_sizes="$2"
    cnt_codelets=($3)

    cnt_codelets=(${cnt_codelets[@]/#/${cnt_prefix}\/})

    for codelet_path in ${cnt_codelets[@]}
    do
      codelet_name=$(basename ${codelet_path})
#      echo ${codelet_name}
#      echo ${codelet_path}
#      echo ${cnt_sizes}
      name2path+=([${codelet_name}]=${codelet_path})
      name2sizes+=([${codelet_name}]=${cnt_sizes})
    done

}


fill_codelet_maps "${lin_s1_prefix}" "${linear_sizes}" "$(IFS=' '; echo ${lin_s1_codelets[@]})"
fill_codelet_maps "${saeed_lin_s1_prefix}" "${linear_sizes}" "$(IFS=' '; echo ${saeed_lin_s1_codelets[@]})"
fill_codelet_maps ${lin_slda_prefix} "${linear_sizes}" "$(IFS=' '; echo ${lin_slda_codelets[@]})"
fill_codelet_maps ${lin_sclda_prefix} "${linear_clda_sizes}" "$(IFS=' '; echo ${lin_sclda_codelets[@]})"
fill_codelet_maps ${quad_s1_prefix} "${quadratic_sizes}" "$(IFS=' '; echo ${quad_s1_codelets[@]})"
fill_codelet_maps ${quad_slda_prefix} "${quadratic_sizes}" "$(IFS=' '; echo ${quad_slda_codelets[@]})"
fill_codelet_maps ${quadt_s1_prefix} "${quadratic_sizes}" "$(IFS=' '; echo ${quadt_s1_codelets[@]})"
fill_codelet_maps ${ubmkprefix} "${ptr_sizes}" "$(IFS=' '; echo ${ubmk_codelets[@]})"

name2sizes[toeplz_1_de]="1000 4000 10000 400000"
name2sizes[toeplz_1_sVS_de]="1000 4000 10000 400000"



# #linear_codelets+=" ${lin_s1_prefix}/balanc_3/balanc_3_de"
# nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_sr_sVS_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/elmhes_10/elmhes_10_sr_sVS_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/four1_2/four1_2_sr_me
# #linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_de"
# #linear_codelets+=" ${lin_s1_prefix}/hqr_13/hqr_13_sVS_de"
# nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_sr_sVS_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/realft_4/realft_4_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_13/svdcmp_13_sr_sVS_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/svdcmp_14/svdcmp_14_sr_sVS_de
# #linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_de"
# #linear_codelets+=" ${lin_s1_prefix}/toeplz_1/toeplz_1_sVS_de"
# nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_2/toeplz_2_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/toeplz_4/toeplz_4_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_1/tridag_1_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_1/tridag_2/tridag_2_sr_de

# linear_codelets+=" ${saeed_lin_s1_prefix}/s1244/s1244_sr_se"
# linear_codelets+=" ${saeed_lin_s1_prefix}/s1244/s1244_sr_sVS_se"
# linear_codelets+=" ${saeed_lin_s1_prefix}/s319/s319_sr_se"
# linear_codelets+=" ${saeed_lin_s1_prefix}/s319/s319_sr_sVS_se"


# nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/elmhes_11/elmhes_11_sr_sVS_de
# nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_sr_de
# nr-codelets/numerical_recipes/1D_loop-Stride_CLDA/svdcmp_11/svdcmp_11_sr_sVS_de
# #linear_codelets+=" ${lin_sclda_prefix}/svdcmp_6/svdcmp_6_de"

# nr-codelets/numerical_recipes/1D_loop-Stride_LDA/hqr_15/hqr_15_sr_se

# nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sr_de
# nr-codelets/numerical_recipes/2D_loop-Stride_1/matadd_16/matadd_16_sr_sVS_de
# nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_sr_me
# nr-codelets/numerical_recipes/2D_loop-Stride_1/mprove_8/mprove_8_sr_sVS_me
# nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sr_se
# nr-codelets/numerical_recipes/2D_loop-Stride_1/svbksb_3/svbksb_3_sr_sVS_se

# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sr_de
# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/lop_13/lop_13_sr_sVS_de
# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_sr_de
# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/relax2_26/relax2_26_sr_sVS_de
# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sr_de
# nr-codelets/numerical_recipes/2D_loop-Stride_LDA/rstrct_29/rstrct_29_sr_sVS_de

# #quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_se"
# #quadratic_codelets+=" ${quadt_s1_prefix}/hqr_12/hqr_12_sVS_se"
# nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sr_se
# nr-codelets/numerical_recipes/2DT_loop-Stride_1/ludcmp_4/ludcmp_4_sr_sVS_se

run_codelets=(
    balanc_3_sr_de balanc_3_sr_sVS_de elmhes_10_sr_de elmhes_10_sr_sVS_de four1_2_sr_me 
    hqr_13_de hqr_13_sVS_de mprove_9_sr_de mprove_9_sr_sVS_de realft_4_sr_de
    svdcmp_13_sr_de svdcmp_13_sr_sVS_de svdcmp_14_sr_de svdcmp_14_sr_sVS_de
    toeplz_1_de toeplz_1_sVS_de toeplz_2_sr_de toeplz_4_sr_de
    tridag_1_sr_de tridag_2_sr_de
    s1244_sr_se s1244_sr_sVS_se s319_sr_se s319_sr_sVS_se
    elmhes_11_sr_de elmhes_11_sr_sVS_de svdcmp_11_sr_de svdcmp_11_sr_sVS_de svdcmp_6_de svdcmp_6_sVS_de
    hqr_15_sr_se
    matadd_16_sr_de matadd_16_sr_sVS_de mprove_8_sr_me mprove_8_sr_sVS_me svbksb_3_sr_se svbksb_3_sr_sVS_se
    lop_13_sr_de lop_13_sr_sVS_de relax2_26_sr_de relax2_26_sr_sVS_de rstrct_29_sr_de rstrct_29_sr_sVS_de
    hqr_12_se hqr_12_sVS_se ludcmp_4_sr_se ludcmp_4_sr_sVS_se
    ptr_ld_branch
)

run_codelets=(
    ptr_ld_branch
)

for codelet in ${run_codelets[@]}
do
  codelet_path=${name2path[${codelet}]}
  sizes=${name2sizes[${codelet}]}
#  echo ${codelet_path}
#  ls ${codelet_path}
#  echo "SS: ${sizes}"

  echo "Launching CLS on $codelet_path...for sizes $sizes"


  ${LOGGER_SH} ${runId} "Launching CLS on '$codelet_path'..."
  ./cls.sh "$codelet_path" "$variants" "${sizes}" "$memory_loads" "$frequencies"  "${runId}" | tee "$codelet_path/cls.log"
  res=$?
  if [[ "$res" != "0" ]]
      then
#      echo -e "\tAn error occured! Check '$codelet_path/cls.log' for more information."
      ${LOGGER_SH} ${runId} "FAILED: Check '${codelet_path}/cls.log' for more information."
  fi
done


exit



### Added above

for codelet in $linear_codelets
do
	${LOGGER_SH} ${runId} "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies"  "${runId}" | tee "$codelet/cls.log"
	#./cls_get_metrics.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" "${runId}" | tee "$codelet/cls.log"
	# &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done

for codelet in $quadratic_codelets
do
	${LOGGER_SH} ${runId} "Launching CLS on '$codelet'..."
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


#END_VRUN_SH=$(date '+%s')
#ELAPSED_VRUN_SH=$((${END_VRUN_SH} - ${START_VRUN_SH}))

#${LOGGER_SH} ${START_VRUN_SH} "$0 finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_VRUN_SH}) at $(date --date=@${END_VRUN_SH})" 