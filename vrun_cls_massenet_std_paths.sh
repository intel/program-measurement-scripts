#!/bin/bash -l


variants="time_reference as time_reference_pref as_pref dt1_rat fpi_ratmb as_ratmb noas-nofpi_ratmb noas-nofpi"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
memory_loads="0"
frequencies="1200000 2700000"

linear_codelets=""
quadratic_codelets=""


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/balanc_3/balanc_3_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/balanc_3/balanc_3_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_13/svdcmp_13_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_13/svdcmp_13_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_14/svdcmp_14_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/svdcmp_14/svdcmp_14_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/toeplz_1/toeplz_1_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch1/toeplz_1/toeplz_1_dp/sse"


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/four1_2/four1_2_mp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/four1_2/four1_2_mp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_sp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_square_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/hqr_12/hqr_12_square_sp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/lop_13/lop_13_dp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/lop_13/lop_13_dp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/ludcmp_4/ludcmp_4_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/ludcmp_4/ludcmp_4_sp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/relax2_26/relax2_26_dp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch2/relax2_26/relax2_26_dp/sse"


#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/hqr_15/hqr_15_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/hqr_15/hqr_15_sp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/jacobi_5/jacobi_5_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/jacobi_5/jacobi_5_sp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/matadd_16/matadd_16_dp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/matadd_16/matadd_16_dp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/mprove_8/mprove_8_mp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/mprove_8/mprove_8_mp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/rstrct_29/rstrct_29_dp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/rstrct_29/rstrct_29_dp/sse"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/svbksb_3/svbksb_3_sp/avx"
#quadratic_codelets="$quadratic_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch3/svbksb_3/svbksb_3_sp/sse"


#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_10/elmhes_10_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_10/elmhes_10_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_11/elmhes_11_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/elmhes_11/elmhes_11_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/hqr_13/hqr_13_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/hqr_13/hqr_13_dp/sse"
linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/mprove_9/mprove_9_dp/avx"
linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/mprove_9/mprove_9_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/realft_4/realft_4_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/realft_4/realft_4_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_11/svdcmp_11_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_11/svdcmp_11_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_6/svdcmp_6_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/svdcmp_6/svdcmp_6_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_2/toeplz_2_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_2/toeplz_2_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_3/toeplz_3_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_3/toeplz_3_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_4/toeplz_4_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/toeplz_4/toeplz_4_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_1/tridag_1_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_1/tridag_1_dp/sse"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_2/tridag_2_dp/avx"
#linear_codelets="$linear_codelets /home/users/vpalomares/nfs/codelets/NR_format/NRs/numerical_recipes/batch4/tridag_2/tridag_2_dp/sse"


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


