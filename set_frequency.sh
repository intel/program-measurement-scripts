#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "1" ]]
then
        echo "ERROR! Invalid arguments (need the requested core frequencies, in kHz)."
        exit -1
fi

target_frequency=$1

 
case "${paths[$HOSTNAME]}" in

*)
        echo "Setting core frequency to '$target_frequency'"
# Adapt to Intel FX
        for ((i=0;i<$(nproc);i++))
        do
                cpufreq-set -c $i -g userspace
                cpufreq-set -c $i -f $target_frequency
        done    
#       echo "userspace" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
# Adapt to Intel FX
#       echo "$target_frequency" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed > /dev/null
# Adapt to Intel FX
        actual_frequency=$( cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
#       actual_frequency=$( sudo cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
        #echo "Actual frequency: '$actual_frequency'"

	#Potential fix for Silvermont CPI issues?
	sleep 1

        if [[ "$target_frequency" != "$actual_frequency" ]]
        then
                echo "ERROR! Frequency change failed!"
                exit -1
        fi
        ;;

"")
        echo "Could not change the frequency! (setspeed file path unknown)."
        ;;

esac

 
exit 0

