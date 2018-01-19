#!/bin/bash -l

source $CLS_FOLDER/const.sh

if [[ "$nb_args" != "4" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's name, variants, codelet's folder, loop id)."
	exit -1
fi

codelet_name="$1"
variants="$2"
bin_folder=$( readlink -f "$3" )
loop_id="$4"

local_uarch="SANDY_BRIDGE"
if [[ "$UARCH" == "HASWELL" ]]
then
	local_uarch="$UARCH"
elif [[ "$UARCH" == "skylake_server" ]]; then
	local_uarch="SKYLAKE"
fi

echo "Extracting assemblies from '$bin_folder'..."

echo "Extracting the original assembly..."
echo "-------------------------"	> "$bin_folder/$codelet_name.asm"
echo "$codelet_name"			>> "$bin_folder/$codelet_name.asm"
echo "-------------------------" 	>> "$bin_folder/$codelet_name.asm"
"$MAQAO" "${MAQAO_FOLDER}/assembly_extractor.lua" binary_name="$bin_folder/$codelet_name" lid="$loop_id" >> "$bin_folder/$codelet_name.asm"
sed -i "s/\t/     \t/g" "$bin_folder/$codelet_name.asm"
#echo "Getting jump address to the most inner loop (address of the first instruction of the extracted loop)"
jump_address=$( head -n 4 "$bin_folder/$codelet_name.asm" | tail -n 1 | cut -f1 -d: )
echo "Original loop/jump address: $jump_address"
if [[ "$jump_address" == "" ]]
then
	echo "Could not find the jump address! Aborting..."
	exit -1
fi

#"$MAQAO" module=cqa uarch="$local_uarch" bin="$bin_folder/$codelet_name" loop=$loop_id of=csv -ext
${GENERATE_CQA_CSV_SH} "$local_uarch" "$bin_folder/$codelet_name" $loop_id 
cat loops.csv | sed 's/'${DELIM}'$//g' > "$bin_folder/${codelet_name}.stan_full.csv"

rm loops.csv

#group_analysis=$( ./group_analysis.sh "$bin_folder/$codelet_name" "$loop_id" | tail -n 2 )
#new_csv=$( echo "$group_analysis" | paste "$bin_folder/${codelet_name}.stan_full.csv" - -d ${DELIM} )
#echo "$new_csv" > "$bin_folder/${codelet_name}.stan_full.csv"

ooo_analysis=$( $CLS_FOLDER/ooo_analysis.sh "$bin_folder/$codelet_name" "$loop_id" )
new_csv=$( echo "$ooo_analysis" | paste "$bin_folder/${codelet_name}.stan_full.csv" - -d ${DELIM} )
echo "$new_csv" > "$bin_folder/${codelet_name}.stan_full.csv"

#vect_analysis=$( ./cqa_vectorization.sh "$bin_folder/$codelet_name" "$loop_id" )
#new_csv=$( echo "$vect_analysis" | paste "$bin_folder/${codelet_name}.stan_full.csv" - -d ${DELIM} )
#echo "$new_csv" > "$bin_folder/${codelet_name}.stan_full.csv"


"$MAQAO" "${MAQAO_FOLDER}/loop_id_in_object.lua" binary_name="$bin_folder/$codelet_name" loop_id="$loop_id" object_name="$bin_folder/../codelet.o" > "$bin_folder/../loop_id_in_obj"


for variant in $variants
do
  if [[ "${variant}" == "ORG" ]]
      then
#      variant_path="$bin_folder/${codelet_name}_REF_cpi"
      # Info is already in ${codelet_name}.stan_full.csv, copy to ${codelet_name}_ORG.stan_full.csv
      cp "$bin_folder/${codelet_name}.asm" "$bin_folder/${codelet_name}_ORG.asm"
      cp "$bin_folder/${codelet_name}.stan_full.csv" "$bin_folder/${codelet_name}_ORG.stan_full.csv"
  else
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
      
      #"$MAQAO" module=cqa uarch="$local_uarch" bin="$variant_path" loop=$lid of=csv -ext
      ${GENERATE_CQA_CSV_SH} "$local_uarch" "$variant_path" $lid 

      cat loops.csv | sed 's/'${DELIM}'$//g' > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
      rm loops.csv
      new_csv=$( echo "$group_analysis" | paste "$bin_folder/${codelet_name}_${variant}.stan_full.csv" - -d ${DELIM} )
      echo "$new_csv" > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
#	ooo_analysis=$( ./ooo_analysis.sh "$bin_folder/${codelet_name}_${variant}_cpi" "$lid" )
      ooo_analysis=$( $CLS_FOLDER/ooo_analysis.sh "${variant_path}" "$lid" )
      new_csv=$( echo "$ooo_analysis" | paste "$bin_folder/${codelet_name}_${variant}.stan_full.csv" - -d ${DELIM} )
      echo "$new_csv" > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
#	vect_analysis=$( ./cqa_vectorization.sh "$bin_folder/${codelet_name}_${variant}_cpi" "$lid" )
      vect_analysis=$( $CLS_FOLDER/cqa_vectorization.sh "${variant_path}" "$lid" )
      new_csv=$( echo "$vect_analysis" | paste "$bin_folder/${codelet_name}_${variant}.stan_full.csv" - -d ${DELIM} )
      echo "$new_csv" > "$bin_folder/${codelet_name}_${variant}.stan_full.csv"
  fi
done

rm -f loops.csv

echo "Done with assemblies extraction."

exit 0
