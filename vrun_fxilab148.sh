#!/bin/bash -l

#variants="REF LS FP DL1 NOLS-NOFP FP_SAN REF_SAN FES LS_FES FP_FES"
variants="REF LS FP DL1 FES"
variants="REF LS FP"
linear_sizes="1000 2000 4000 6000 8000 10000 20000 40000 60000 80000 100000 200000 400000 600000 800000 1000000 2000000 4000000 6000000 8000000 10000000"
quadratic_sizes="208 240 304 352 400 528 608 704 800 928 1008 1100 1200 1300 1400 1500 1600 1800 2000 2500 3000"
#memory_loads="0 99999"
memory_loads="0"
frequencies="1200000 2800000"
frequencies="2800000"

linear_codelets=""
quadratic_codelets=""


linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/balanc_3/balanc_3_de"
linear_codelets="$linear_codelets /localdisk/amazouz/ecr_codelets/nr-codelets/numerical_recipes/1D_loop-Stride_1/mprove_9/mprove_9_de"
linear_codelets="$linear_codelets /localdisk/amazouz/intel_codelets/1D_loop-Stride_1/s319/s319_se"

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
