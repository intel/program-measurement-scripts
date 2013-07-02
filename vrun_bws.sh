#!/bin/bash -l


if [[ $# -lt 1 ]]
then
	echo "Need codelet folders as parametre!"
	exit -1
fi

codelets_path=$@
#"/home/users/vpalomares/nfs/codelets/NR_format/NRs/bws/bws_deadweights/8/stores*movaps*swp_none"

for codelet in "$codelets_path"
do
	codelet_paths="$codelet_paths $codelet"
done


sbatch -w dandrieu -p special ./slurm_launcher.sh "$codelet_paths"


#	echo "Launching CLS on '$codelet'..."

#	sbatch -w sviridov -p regular ./cls.sh "$codelet" "$variants" "$sizes" "$memory_loads" "$frequencies"


#	&> "$codelet/cls.log"
#	res=$?
#	if [[ "$res" != "0" ]]
#	then
#		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
#	fi
#done
