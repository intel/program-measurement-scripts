#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "1" ]]
then
	echo "ERROR! Invalid arguments (need the requested frequency, in kHz)."
	exit -1
fi

target_frequency=$1


case "${paths[$HOSTNAME]}" in

"1")
	echo "Setting frequency to '$target_frequency'"
	echo "userspace" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
	echo "$target_frequency" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq > /dev/null
	echo "$target_frequency" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq > /dev/null
	echo "$target_frequency" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed > /dev/null
	actual_frequency=$( cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
	#echo "Actual frequency: '$actual_frequency'"

	if [[ "$target_frequency" != "$actual_frequency" ]]
	then
		echo "ERROR! Frequency change failed!"
		exit -1
	fi
	;;

"2")
	echo "This machine cannot change its CPU's frequency: ignoring frequency change."
	;;

"")
	echo "Could not change the frequency! (setspeed file path unknown)."
	;;

esac


exit 0
