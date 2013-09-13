#!/bin/bash -l


variants="time_reference as time_reference_pref as_pref dt1_rat fpi noas-nofpi_ratmb"
variants="dt1_rat time_reference_dos dt1_rat_dos fpi_dos"
variants="time_reference as"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
#linear_sizes="1000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#quadratic_sizes="208"
memory_loads="0"
frequencies="1200000 2700000"
#frequencies="2700000"

linear_codelets=""
quadratic_codelets=""


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/balanc_3/balanc_3_dp/balanc_3_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/balanc_3/balanc_3_dp/balanc_3_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_13/svdcmp_13_dp/svdcmp_13_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_13/svdcmp_13_dp/svdcmp_13_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_14/svdcmp_14_dp/svdcmp_14_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_14/svdcmp_14_dp/svdcmp_14_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/toeplz_1/toeplz_1_dp/toeplz_1_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/toeplz_1/toeplz_1_dp/toeplz_1_dp_sse"


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/four1_2/four1_2_mp/four1_2_mp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/four1_2/four1_2_mp/four1_2_mp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_sp/hqr_12_sp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_sp/hqr_12_sp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/lop_13/lop_13_dp/lop_13_dp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/lop_13/lop_13_dp/lop_13_dp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/ludcmp_4/ludcmp_4_sp/ludcmp_4_sp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/ludcmp_4/ludcmp_4_sp/ludcmp_4_sp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/relax2_26/relax2_26_dp/relax2_26_dp_avx"
quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/relax2_26/relax2_26_dp/relax2_26_dp_sse"
quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/relax2_26/relax2_26_dp/relax2_26_dp_ssev"


#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/hqr_15/hqr_15_sp/hqr_15_sp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/hqr_15/hqr_15_sp/hqr_15_sp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/jacobi_5/jacobi_5_sp/jacobi_5_sp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/jacobi_5/jacobi_5_sp/jacobi_5_sp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/matadd_16/matadd_16_dp/matadd_16_dp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/matadd_16/matadd_16_dp/matadd_16_dp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/mprove_8/mprove_8_mp/mprove_8_mp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/mprove_8/mprove_8_mp/mprove_8_mp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/rstrct_29/rstrct_29_dp/rstrct_29_dp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/rstrct_29/rstrct_29_dp/rstrct_29_dp_sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/svbksb_3/svbksb_3_sp/svbksb_3_sp_avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/svbksb_3/svbksb_3_sp/svbksb_3_sp_sse"


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_10/elmhes_10_dp/elmhes_10_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_10/elmhes_10_dp/elmhes_10_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_11/elmhes_11_dp/elmhes_11_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_11/elmhes_11_dp/elmhes_11_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/hqr_13/hqr_13_dp/hqr_13_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/hqr_13/hqr_13_dp/hqr_13_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/mprove_9/mprove_9_dp/mprove_9_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/mprove_9/mprove_9_dp/mprove_9_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/realft_4/realft_4_dp/realft_4_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/realft_4/realft_4_dp/realft_4_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_11/svdcmp_11_dp/svdcmp_11_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_11/svdcmp_11_dp/svdcmp_11_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_6/svdcmp_6_dp/svdcmp_6_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_6/svdcmp_6_dp/svdcmp_6_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_2/toeplz_2_dp/toeplz_2_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_2/toeplz_2_dp/toeplz_2_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_3/toeplz_3_dp/toeplz_3_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_3/toeplz_3_dp/toeplz_3_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_4/toeplz_4_dp/toeplz_4_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_4/toeplz_4_dp/toeplz_4_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_1/tridag_1_dp/tridag_1_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_1/tridag_1_dp/tridag_1_dp_sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_2/tridag_2_dp/tridag_2_dp_avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_2/tridag_2_dp/tridag_2_dp_sse"


for codelet in $linear_codelets
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$linear_sizes" "$memory_loads" "$frequencies" &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done

for codelet in $quadratic_codelets
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$quadratic_sizes" "$memory_loads" "$frequencies" &> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done


