#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "3" ]]
then
	echo "ERROR! Invalid arguments (need: Memloader's folder, wanted bw, cores to use)."
	exit -1
fi


memloader_path="$1"
bw=$2
cores="$3"

if [[ "$bw" == "0" || "$cores" == "" ]]
then
	echo "Invalid arguments (bw: '$bw', cores: '$cores'"
	exit -1
fi

declare -A clocks

#1662524560 166254600

clocks+=([borodine]=1861946220)		# Detector
clocks+=([britten]=1861946220)		# Detector from Borodine (same proc)
clocks+=([bruckner]=2261000000)		# Cpufreq
clocks+=([buxtehude]=2128014154)	# Detector
clocks+=([campion]=2128014154)		# Detector
clocks+=([carissimi]=1995000000)	# Cpufreq
clocks+=([clerambault]=1995000000)	# Cpufreq
clocks+=([chopin]=3300000000)		# Cpufreq
clocks+=([dandrieu]=3300000000)		# Cpufreq
clocks+=([dubois]=1000000000)		# None
clocks+=([massenet]=2700000000)		# Cpufreq
clocks+=([mauduit]=2660000000)		# Cpufreq

clocks+=([sviridov]=1662546000)		# Detector

reference_clock=${clocks[$HOSTNAME]}

#echo "Reference clock for '$HOSTNAME': $reference_clock"

id=0
rm -f "${memloader_path}"/tmp_res_*

nb_cores=0
for i in $cores
do
	let "nb_cores = $nb_cores + 1"
done

echo -e "Mempinner.sh \tspreading $bw MB/s over $nb_cores cores ($cores)..."

let "bw = $bw / $nb_cores"

rm -f "$memloader_path/"tmp_res_${HOSTNAME}_*
for i in $cores
do
	#echo "Pinning on core #$i [id = $id]"
	numactl -C$i ${memloader_path}/Memloader $bw $reference_clock > "$memloader_path/tmp_res_${HOSTNAME}_${i}_$id" &
	let "id = $id + 1"
done

