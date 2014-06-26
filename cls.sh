#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "5" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, variants, data sizes, memory loads, frequencies)."
	exit -1
fi


codelet_folder=$( readlink -f "$1" )
variants="$2"
data_sizes="$3"
memory_loads="$4"
frequencies="$5"


echo "------------------------------------------------------------"
echo "CLS"
echo -e "Hostname \t'$HOSTNAME' [$UARCH]"
echo -e "Codelet \t'$codelet_folder'"
echo -e "Variants \t'$variants'"
echo -e "Data sizes \t'$data_sizes'"
echo -e "Memory loads \t'$memory_loads'"
echo -e "Frequencies \t'$frequencies'"
echo -e "Meta repets\t'$META_REPETITIONS'"

echo "------------------------------------------------------------"
echo "Reading codelet.conf"
codelet_name=$( grep "label name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
binary_name=$( grep "binary name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )_
#function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
echo -e "Codelet name \t'$codelet_name'"
echo -e "Binary name \t'$binary_name'"
echo -e "Function name \t'$function_name'"

echo "------------------------------------------------------------"
echo "Removing older results (if any)..."
rm -R -f "$codelet_folder/$CLS_RES_FOLDER"
echo "Recreating results folder..."
mkdir "$codelet_folder/$CLS_RES_FOLDER" &> /dev/null
echo "$codelet_name" > "$codelet_folder/$CLS_RES_FOLDER/codelet_name"
echo "$META_REPETITIONS" > "$codelet_folder/$CLS_RES_FOLDER/meta_repetitions"
echo "$PRETTY_UARCH" > "$codelet_folder/$CLS_RES_FOLDER/uarch"

echo "------------------------------------------------------------"
echo "Compiling the codelet..."
./generate_original.sh $codelet_folder $binary_name $codelet_name
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi

echo "------------------------------------------------------------"
echo "Identifying the main loop..."
loop_info=$( ./count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" )
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi
loop_info=$( echo -e "$loop_info" | head -n 1 )
loop_id=$( echo "$loop_info" | cut -f1 -d';' )
loop_iterations=$( echo "$loop_info" | cut -f2 -d';' )
echo -e "Loop id \t'$loop_id'"
echo -e "Iterations \t'$loop_iterations'"
echo "$loop_id" > "$codelet_folder/$CLS_RES_FOLDER/loop_id"

echo "------------------------------------------------------------"
echo "Creating DECAN variants..."
./generate_variants.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" "$variants"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi
if [[ "$ACTIVATE_DYNAMIC_GROUPING" != "0" ]]
then
	echo
	echo "Creating dynamic groups..."
	res_generate=$( ./generate_dynamic_groups.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" )
	res=$?
	echo "$res_generate"
	if [[ "$res" != "0" ]]
	then
		echo "Cancelling CLS."
		exit -1
	fi
	add_variants=$( echo "$res_generate" | tail -n 1 | cut -f2 -d':' )
	variants="$variants $add_variants"
fi

echo "------------------------------------------------------------"
echo "Extracting assemblies..."
./assembly_extraction.sh "$codelet_name" "$variants" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" "$loop_id"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi

if [[ "$HOSTNAME" == "massenet" ]]
then
	echo "------------------------------------------------------------"
	echo "Activating recipe..."
	~/recipe.sh 1
fi

#exit 0

echo "------------------------------------------------------------"
echo "Starting experiments..."

for data_size in $data_sizes
do
	echo
	echo
	mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size" &> /dev/null

	echo "Adjusting codelet parametres..."
	./w_adjust.sh "$codelet_folder" "$codelet_name" "$data_size" $MIN_REPETITIONS $CODELET_LENGTH

	echo "Re-counting loop iterations..."
	loop_info=$( ./count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" )
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo "Cancelling CLS."
		exit -1
	fi

	wanted_loop_info=$( echo "$loop_info" | grep "^$loop_id;" )
	most_important_loop=$( echo "$loop_info" | head -n 1 )

	if [[ "$wanted_loop_info" != "$most_important_loop" ]]
	then
		echo "Loop mismatch!"
		tmp_id=$( echo "$wanted_loop_info" | cut -f1 -d';' )
		tmp_loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d';' )
		echo "Wanted loop info: $tmp_id, $tmp_loop_iterations iterations."

		tmp_id=$( echo "$most_important_loop" | cut -f1 -d';' )
		tmp_loop_iterations=$( echo "$most_important_loop" | cut -f2 -d';' )
		echo "Most important loop info: $tmp_id, $tmp_loop_iterations iterations."

		echo "Cancelling CLS."
		exit -1
	fi

	echo "Loop Id;Iterations;" > "$codelet_folder/$CLS_RES_FOLDER/iterations_for_$data_size"
	echo "$loop_info" >> "$codelet_folder/$CLS_RES_FOLDER/iterations_for_$data_size"

	loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d';' )
	echo -e "Iterations \t'$loop_iterations'"

	for memory_load in $memory_loads
	do
		mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load" &> /dev/null
		killall -9 memloader --quiet &> /dev/null
		if [[ "$memory_load" != "0" ]]
		then
			echo "Starting a memloader for '$memory_load' MB/s ($MEMLOAD_ARGS_LIST)"
			$MEMLOADER --target_bw=$memory_load $MEMLOAD_ARGS_LIST > "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/memloader.log" &
			memload_pid=$!
			sleep 5
			kill -0 $memload_pid &> /dev/null
			res=$?
			if [[ "$res" != "0" ]]
			then
				echo "Cancelling CLS."
				exit -1
			else
				disown $memload_pid
			fi
		else
			echo "No memory load."
		fi

		for frequency in $frequencies
		do
			mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency" &> /dev/null
			./set_frequency.sh $frequency
			res=$?
			if [[ "$res" != "0" ]]
			then
				echo "Cancelling run_codelet.sh."
				exit -1
			fi

			for variant in $variants
			do
				mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant" &> /dev/null
				./run_codelet.sh "$codelet_folder" "$codelet_name" $data_size $memory_load $frequency "$variant" "$loop_iterations"
				res=$?
				if [[ "$res" != "0" ]]
				then
					echo "Cancelling CLS."
					exit -1
				fi
			done
		done

		if [[ "$memory_load" != "0" ]]
		then
			killall -9 memloader --quiet &> /dev/null	
		else
			echo "No memory load (=> nothing to kill)."
		fi
	done

	echo "Generating results..."
	./gather_results.sh "$codelet_folder"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo "Cancelling CLS."
		exit -1
	fi
done


echo "------------------------------------------------------------"
echo "Generating results..."
./gather_results.sh "$codelet_folder"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi

echo "------------------------------------------------------------"
echo "Cleaning up..."
./cleanup_codelet_folder.sh "$codelet_folder" "$codelet_name" "$variants"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi


if [[ "$HOSTNAME" == "massenet" ]]
then
	echo "------------------------------------------------------------"
	echo "Deactivating recipe..."
	~/recipe.sh 0
fi

echo "------------------------------------------------------------"


exit 0
