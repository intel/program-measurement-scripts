#!/bin/bash -l

source ./const.sh

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
			echo "Generating '$variant' ($build)..."
			$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "${binary_path}" "$function_name" "$variant_transform" "$UARCH" &> /dev/null
			res=$?
			if [[ "$res" != "0" ]]
			then
				echo "Configuration error. Aborting."
				exit -1
			fi
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
					echo "Keeping '$generated_binary' for '${binary_name}_${variant}_${build}'"
					mv "$generated_binary" "${binary_name}_${variant}_${build}"
					let "keep_one = $keep_one + 1"
				else
					rm "$generated_binary"
				fi
			done
			if [[ "$keep_one" != "1" ]]
			then
				echo "Error! Keep_one should equal 1, not '$keep_one'!"
				exit -1
			fi

#			cp "${binary_name}_${variant}_${build}" "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
			cp "${binary_name}_${variant}_${build}" "${save_binary_path}"

		else
			echo "Error! Variant '$variant' could not be identified!"
			exit -1
		fi
	done
done


exit 0
