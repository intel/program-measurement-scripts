#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need: the requested frequency in kHz, target core)."
	exit -1
fi

target_frequency=$1
target_core=$2


declare -A min_freq
min_freq+=([borodine]="")
min_freq+=([britten]="")
min_freq+=([bruckner]="")
min_freq+=([buxtehude]="")
min_freq+=([campion]="")
min_freq+=([carissimi]="")
min_freq+=([clerambault]="")
min_freq+=([chopin]="1600000")
min_freq+=([dandrieu]="1600000")
min_freq+=([dubois]="")
min_freq+=([massenet]="1200000")
min_freq+=([mauduit]="")
min_freq+=([sviridov]="")

declare -A max_freq
max_freq+=([borodine]="")
max_freq+=([britten]="")
max_freq+=([bruckner]="")
max_freq+=([buxtehude]="")
max_freq+=([campion]="")
max_freq+=([carissimi]="")
max_freq+=([clerambault]="")
max_freq+=([chopin]="3300000")
max_freq+=([dandrieu]="3300000")
max_freq+=([dubois]="")
max_freq+=([massenet]="2700000")
max_freq+=([mauduit]="")
max_freq+=([sviridov]="")

if [[ "$target_frequency" == "min" ]]
then
	target_frequency=${min_freq[$HOSTNAME]};
fi

if [[ "$target_frequency" == "max" ]]
then
	target_frequency=${max_freq[$HOSTNAME]};
fi


case "$HOSTNAME" in

"britten")	;&
"chopin")	;&
"dandrieu")	;&
"massenet") ;&
"regular_cpufreq_change")

	echo "Setting frequency to '$target_frequency'"
	echo "userspace" | tee /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_governor > /dev/null

	echo "${min_freq[$HOSTNAME]}" | tee /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_min_freq &> /dev/null
	echo "${max_freq[$HOSTNAME]}" | tee /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_max_freq > /dev/null
	echo "${min_freq[$HOSTNAME]}" | tee /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_min_freq > /dev/null # A second time in case min freq was > max freq

	echo "$target_frequency" | tee /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_setspeed > /dev/null

	actual_frequency=$( cat /sys/devices/system/cpu/cpu$target_core/cpufreq/scaling_cur_freq | head -n 1 )
	if [[ "$target_frequency" != "$actual_frequency" ]]
	then
		echo "ERROR! Frequency change failed!"
		exit -1
	fi
	;;

"buxtehude")	;&
"sviridov")		;&
"no_cpufreq_available")

	echo "This machine cannot change its CPU's frequency: ignoring frequency change."
	;;

*)
	echo "Could not change the frequency! (setspeed file path unknown)."
	exit -1
	;;

esac


exit 0
