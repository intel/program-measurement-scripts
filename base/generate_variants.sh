#!/bin/bash -l

source $CLS_FOLDER/const.sh

if [[ "$nb_args" != "5" ]]
then
	echo "ERROR! Invalid arguments (need the binary's path and the function's name)."
	exit -1
fi

binary_path=$( readlink -f "$1" )
binary_folder=$( dirname "$binary_path" )
binary_name=$( basename "$binary_path" )
function_name="$2"
loop_id="$3"
variants="$4"
save_binary_path=$( readlink -f "$5" )

different_builds="cpi"
# Always generate *_hwc
#if [[ "$ACTIVATE_COUNTERS" != "0" ]]
#then
echo "Activating DECAN region generation!"
different_builds="$different_builds hwc"
#fi

echo "Generating DECAN variants..."
echo

mkdir "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

cd "$binary_folder"
for variant in $variants
do
	if [[ "${variant}" == "ORG" ]]
	then
		# Just to be safe to generate REF for ORG runs
		variant="REF"
	fi

	for build in $different_builds
	do
		variant_transform=${transforms[$variant]}_${build}
		echo "Current variant: '$variant' [$variant_transform]"
		if [[ "$variant_transform" != "" ]]
		then
			echo -n "Generating '$variant' ($build)..."
			output_variant_binary=${binary_name}_${variant}_${build}
			if [[ "${build}" == "hwc" && -e ${binary_path}_emon_api ]]
			then
				echo "using EMON API binary..."
				# use emon api binary for hwc measurement and create a basic config file for cpi runs.
				cat <<EOF > emon_api_config_file
<EMON_CONFIG>
EVENTS = "INST_RETIRED.ANY,CPU_CLK_UNHALTED.REF_TSC,CPU_CLK_UNHALTED.THREAD"
DURATION=99999999999
OUTPUT_FILE=emon_api.out
</EMON_CONFIG>
EOF
				$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "${binary_path}_emon_api" "$function_name" "$variant_transform" "$UARCH" &> /dev/null
			else
				echo "using non-EMON API binary..."
				$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "${binary_path}" "$function_name" "$variant_transform" "$UARCH"
				echo $DECAN_CONFIGURATOR "$DECAN_FOLDER/" "${binary_path}" "$function_name" "$variant_transform" "$UARCH"
			fi
			res=$?
			if [[ "$res" != "0" ]]
			then
				echo "Configuration error. Aborting."
				exit -1
			fi
			echo Executing binary generating CMD: $DECAN "$DECAN_CONFIGURATION"
			$DECAN "$DECAN_CONFIGURATION" &> /dev/null


			generated_binaries=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
			if [[ "$generated_binaries" == "" ]]
			then
				echo "ERROR! No binary was generated!"
				exit -1
			fi
			rm -f $PWD/$DECAN_REPORT

			keep_one=0
			for generated_binary in $generated_binaries
			do

				tmp_loop_id=$( echo "$generated_binary" | sed -e "s/.*_L\([[:digit:]][[:digit:]]*\).*/\1/g" )
				if [[ "$tmp_loop_id" == "$loop_id" ]]
				then
					echo "Keeping '$generated_binary' for '${output_variant_binary}'"
					mv "$generated_binary" "${output_variant_binary}"
					let "keep_one = $keep_one + 1"
				else
					rm "$generated_binary"
				fi
			done
			if [[ "$keep_one" != "1" && ${variant} != "REF" ]]
			then
				echo "Error! Keep_one should equal 1, not '$keep_one'!"
				exit -1
			fi

			#			cp "${binary_name}_${variant}_${build}" "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
			cp "${output_variant_binary}" "${save_binary_path}"

		else
			echo "Error! Variant '$variant' could not be identified!"
			exit -1
		fi
	done
done


exit 0
