#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "3" ]]
then
	echo "ERROR! Invalid arguments (need the binary's path and the function's name)."
	exit -1
fi

binary_path=$( readlink -f "$1" )
binary_folder=$( dirname "$binary_path" )
binary_name=$( basename "$binary_path" )
function_name="$2"
loop_id="$3"

different_builds="cpi"
if [[ "$ACTIVATE_COUNTERS" != "0" ]]
then
	echo "Activating DECAN region generation!"
	different_builds="$different_builds hwc"
fi

echo "Generating DECAN dynamic group variants..."
echo

#echo "Finding the number of groups..."
nb_groups=$( ${MAQAO} module=grouping bin=$binary_path fct=${function_name} with_sse=1 loop=$loop_id --cm | wc -l )
echo "Number of static groups: '$nb_groups'"

echo "Generating combinatorics..."
combinatorics=$( $COMBINATORICS_SH $nb_groups ) 
#echo "Combinatorics: '$combinatorics'"


cd "$binary_folder"

first_iteration_keep_list=""
for build in $different_builds
do
	$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "${binary_path}" "$function_name" "special_grouping_$build" "$combinatorics" &> /dev/null
	$DECAN "$DECAN_CONFIGURATION" &>/dev/null

	generated_binaries=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
	if [[ "$generated_binaries" == "" ]]
	then
		echo "ERROR! No binary was generated!"
		exit -1
	fi

	#echo "'$generated_binaries'"

	keep_one=0
	keep_list=""
	for generated_binary in $generated_binaries
	do

		tmp_loop_id=$( echo "$generated_binary" | sed -e "s/.*_L\([[:digit:]][[:digit:]]*\).*/\1/g" )
		if [[ "$tmp_loop_id" == "$loop_id" ]]
		then
			dynamic_group=$( echo "$generated_binary" | sed -e "s/.*_\(G.*\)_.*/\1/g" )
			output_name="delgroup_${dynamic_group}_${build}"
			echo "Keeping '$generated_binary' for '$output_name'"

			mv "$generated_binary" "${binary_name}_$output_name"
			keep_list="$keep_list delgroup_${dynamic_group}"
		else
			rm "$generated_binary"
		fi
	done
	if [[ "$keep_list" == "" ]]
	then
		echo "Error! Keep_one should be strictly positive!"
		exit -1
	fi

	cp ${binary_name}_delgroup_* "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"

	rm -f $PWD/$DECAN_REPORT

	if [[ "$first_iteration_keep_list" == "" ]]
	then
		first_iteration_keep_list="$keep_list"
	fi
done

echo "Adding variants: $first_iteration_keep_list"

exit 0





