#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "5" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's name, variants, codelet's folder, function's name, loop id)."
	exit -1
fi

codelet_name="$1"
variants="$2"
bin_folder=$( readlink -f "$3" )
function_name="$4"
loop_id="$5"

echo "Extracting assemblies from '$bin_folder'..."

echo "Extracting the original assembly..."
echo "-------------------------"	> "$bin_folder/$codelet_name.asm"
echo "$codelet_name"			>> "$bin_folder/$codelet_name.asm"
echo "-------------------------" 	>> "$bin_folder/$codelet_name.asm"
"$MAQAO" "${MAQAO_FOLDER}/assembly_extractor.lua" binary_name="$bin_folder/$codelet_name" funct_name="$function_name" lid="$loop_id" >> "$bin_folder/$codelet_name.asm"
sed -i "s/\t/     \t/g" "$bin_folder/$codelet_name.asm"
#echo "Getting jump address to the most inner loop (address of the first instruction of the extracted loop)"
jump_address=$( head -n 4 "$bin_folder/$codelet_name.asm" | tail -n 1 | cut -f1 -d: )
echo "Original loop/jump address: $jump_address"
if [[ "$jump_address" == "" ]]
then
	echo "Could not find the jump address! Aborting..."
	exit -1
fi

"$MAQAO" module=cqa uarch=SANDY_BRIDGE bin="$bin_folder/$codelet_name" fct=$function_name of=csv -ext
# > "$bin_folder/$codelet_name.stan"
#./convert_stan.sh "$bin_folder/$codelet_name.stan" $loop_id > "$bin_folder/$codelet_name.stan.csv"

head -n 1 $function_name.csv | sed 's/;$//' > "$bin_folder/${codelet_name}.stan_full.csv"
awk -F ';' '{if($5 == '$loop_id'){print;}}' $function_name.csv | sed 's/;$//' >> "$bin_folder/${codelet_name}.stan_full.csv"
group_analysis=$( ./group_analysis.sh "$bin_folder/$codelet_name" "$loop_id" | tail -n 2 )
new_csv=$( echo "$group_analysis" | paste "$bin_folder/${codelet_name}.stan_full.csv" - -d ';' )
echo "$new_csv" > "$bin_folder/${codelet_name}.stan_full.csv"

ooo_analysis=$( ./ooo_analysis.sh "$bin_folder/$codelet_name" "$loop_id" )
new_csv=$( echo "$ooo_analysis" | paste "$bin_folder/${codelet_name}.stan_full.csv" - -d ';' )
echo "$new_csv" > "$bin_folder/${codelet_name}.stan_full.csv"

for variant in $variants
do
	variant_path="$bin_folder/${codelet_name}_${variant}_cpi"
	echo "Extracting assembly from DECANized executable '$variant_path'"
	inner_loop_address=$( objdump -d "$variant_path" | grep "$jump_address:" | egrep -o -e 'jmpq\ \ \ [a-f0-9]+' | tr -s " " | cut -f2 -d' ' )

	if [ ${#inner_loop_address} -eq 0 ]
	then
		#echo "Code was NOT moved by MADRAS"
		inner_loop_address=$jump_address
	#else
		#echo "Code was moved by MADRAS"
	fi

	echo "Inner loop address: '$inner_loop_address'"

	echo "-------------------------"	> "$bin_folder/${codelet_name}_${variant}.asm"
	echo "${codelet_name}_$variant"		>> "$bin_folder/${codelet_name}_${variant}.asm"
	echo "-------------------------" 	>> "$bin_folder/${codelet_name}_${variant}.asm"
	"$MAQAO" "${MAQAO_FOLDER}/assembly_extractor_from_address.lua" binary_name="$variant_path" loop_address="$inner_loop_address" >> "$bin_folder/${codelet_name}_${variant}.asm"
	sed -i "s/\t/     \t/g" "$bin_folder/${codelet_name}_${variant}.asm"
	lid=$( "$MAQAO" "${MAQAO_FOLDER}/loop_id_extractor_from_address.lua" binary_name="$variant_path" loop_address="$inner_loop_address" )

	"$MAQAO" module=cqa uarch=SANDY_BRIDGE bin="$variant_path" fct=$function_name of=csv -ext
	# > "$bin_folder/${codelet_name}_${variant}.stan"
	#./convert_stan.sh "$bin_folder/${codelet_name}_${variant}.stan" $lid > "$bin_folder/${codelet_name}_${variant}.stan.csv"

	head -n 1 $function_name.csv | sed 's/;$//' > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
	awk -F ';' '{if($5 == '$lid'){print;}}' $function_name.csv | sed 's/;$//' >> "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
	new_csv=$( echo "$group_analysis" | paste "$bin_folder/${codelet_name}_${variant}.stan_full.csv" - -d ';' )
	echo "$new_csv" > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"

	ooo_analysis=$( ./ooo_analysis.sh "$bin_folder/${codelet_name}_${variant}_cpi" "$lid" )
	new_csv=$( echo "$ooo_analysis" | paste "$bin_folder/${codelet_name}_${variant}.stan_full.csv" - -d ';' )
	echo "$new_csv" > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
done

rm -f $function_name.csv

echo "Done with assemblies extraction."

exit 0
