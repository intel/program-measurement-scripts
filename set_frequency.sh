#!/bin/bash -l

source ./const.sh

# if [[ "$nb_args" != "1" ]]
# then
#         echo "ERROR! Invalid arguments (need the requested core frequencies, in kHz)."
#         exit -1
# fi

target_frequency=""
min_uncore_frequency=""
max_uncore_frequency=""

while getopts ":c:m:M:" OPTION; do
    case $OPTION in
	c)
	    target_frequency=${OPTARG}
	    ;;
	m)
	    min_uncore_frequency=${OPTARG}
	    ;;
	M)
	    max_uncore_frequency=${OPTARG}
	    ;;
	*)
	    echo "Unexpected argument, usage: $0 -c <core freq> -m <min. uncore freq> -M <max. uncore freq>"
	    exit -1
	    ;;
    esac
done

#target_frequency=$1

if [ ! -z ${target_frequency} ]
then
    
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
else
    echo "Core freq unchanged."
fi

if [[ ! -z ${min_uncore_frequency} && ! -z ${max_uncore_frequency} ]]
then
    ((hi_uncore_bits=min_uncore_frequency/100000))
    ((lo_uncore_bits=max_uncore_frequency/100000))
    ((uncore_bits=hi_uncore_bits<<8|lo_uncore_bits))
    uncore_bits=$(printf "0x%x" ${uncore_bits})
    echo "Setting Uncore Frequency: Min=${min_uncore_frequency}, Max=${max_uncore_frequency} => Uncore bits = ${uncore_bits}"
    if [[ "$UARCH" == "HASWELL" ]]; then
	emon --write-msr 0x620="$uncore_bits"
    else
        echo "Non-HSW system: uncore freq. setting not done"
    fi
elif [[ -z ${min_uncore_frequency} && -z ${max_uncore_frequency} ]]
then
    echo "Uncore freq unchanged."
else
    echo "Uncore freq settings: must specify both min and max freq."
    exit -1
fi

exit 0

