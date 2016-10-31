#!/bin/bash -l

#source ./const.sh

# if [[ "$nb_args" != "1" ]]
# then
#         echo "ERROR! Invalid arguments (need the requested core frequencies, in kHz)."
#         exit -1
# fi

declare -A duty2hex

duty2hex[100.00]="0x0"
duty2hex[93.75]="0x1f"
duty2hex[87.50]="0x1e"
duty2hex[81.25]="0x1d"
duty2hex[75.00]="0x1c"
duty2hex[68.75]="0x1b"
duty2hex[62.50]="0x1a"
duty2hex[56.25]="0x19"
duty2hex[50.00]="0x18"
duty2hex[43.75]="0x17"
duty2hex[37.50]="0x16"
duty2hex[31.25]="0x15"
duty2hex[25.00]="0x14"
duty2hex[18.75]="0x13"
duty2hex[12.50]="0x12"
duty2hex[6.25]="0x11"

target_frequency=""
min_uncore_frequency=""
max_uncore_frequency=""
duty_cycle_level=""

while getopts ":c:m:M:D:" OPTION; do
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
	D)
	    duty_cycle_level=${OPTARG}
	    ;;
	*)
	    echo "Unexpected argument, usage: $0 -c <core freq> -m <min. uncore freq> -M <max. uncore freq> -D <duty cycle level>"
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


if [[ ! -z ${duty_cycle_level} ]]
then
	duty_cycle_level=$(printf "%.2f" ${duty_cycle_level})
	duty_bits=${duty2hex[${duty_cycle_level}]}
	if [[ ${duty_bits} != "" ]]
	then
		echo "Setting duty cycle level to ${duty_cycle_level}%"
		emon --write-msr 0x19a=${duty_bits}
	else
		echo "Duty cycle setting: non supported level."
		exit -1
	fi
else
	echo "Duty cycle level unchanged."
fi

exit 0

