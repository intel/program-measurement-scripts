#!/bin/bash

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
	echo "Setting core frequency to '$target_frequency'"
	if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then
		(( max_frequency=$(wmic cpu get MaxClockSpeed|sed "s/[^0-9]*//g" |head -2|tail -1|tr -d '\n')*1000 ))
		(( percent=100*target_frequency/max_frequency ))
		powercfg.exe -setacvalueindex SCHEME_MIN SUB_PROCESSOR PROCTHROTTLEMIN $percent
		powercfg.exe -setacvalueindex SCHEME_MIN SUB_PROCESSOR PROCTHROTTLEMAX $percent
		powercfg.exe -SETACTIVE SCHEME_MIN
		(( actual_frequency=$(wmic cpu get CurrentClockSpeed|sed "s/[^0-9]*//g" |head -2|tail -1|tr -d '\n')*1000 ))
	else
		# Adapt to Intel FX
		for ((i=0;i<$(nproc);i++))
		do
			# check if cpufreq-set exists and use it if it does
			which cpufreq-set &> /dev/null
			res=$?

			if [ "${res}" == "0" ]; then
				# cpufreq-set should have SETUID bit set so SUDO is not needed here.
				cpufreq-set -c $i -g userspace
				cpufreq-set -c $i -f $target_frequency
			else
	
				CPUPOWER_VERSION=$(cpupower -v | grep cpupower | sed -e 's/.* \([0-9]*\)\.\([0-9]*\).*/\1.\2/g' )
				if [[ -u $(which cpupower) && $(echo ${CPUPOWER_VERSION} >= 3.19|bc -l) == 1 ]]; then
				  # cpupower having SETUID bit and cpupower 3.19 fixed a bit to use it correctly
					cpupower -c $i frequency-set -g userspace &> /dev/null
					cpupower -c $i frequency-set -f $target_frequency &> /dev/null
				else
				  # cpupower should have SETUID bit but here for the case it is not possible.
					sudo cpupower -c $i frequency-set -g userspace &> /dev/null
					sudo cpupower -c $i frequency-set -f $target_frequency &> /dev/null
				fi
			fi
		done

		#echo "userspace" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
		# Adapt to Intel FX
		#echo "$target_frequency" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed > /dev/null
		# Adapt to Intel FX
		actual_frequency=$( cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
		#actual_frequency=$( sudo cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
		echo "Actual frequency: '$actual_frequency'"

		#Potential fix for Silvermont CPI issues?
	fi
	sleep 1

	if [[ "$target_frequency" != "$actual_frequency" ]]
	then
		echo "ERROR! Frequency change failed!"
		exit -1
	fi
else
	echo "Core freq unchanged."
fi

if [[ ! -z ${min_uncore_frequency} && ! -z ${max_uncore_frequency} ]]
then
	((hi_uncore_bits=min_uncore_frequency/100000))
	((lo_uncore_bits=max_uncore_frequency/100000))
	# Quoted bitshift so Gitlab and code formatting not to get confused
	((uncore_bits="hi_uncore_bits<<8|lo_uncore_bits"))
	uncore_bits=$(printf "0x%x" ${uncore_bits})
	echo "Setting Uncore Frequency: Min=${min_uncore_frequency}, Max=${max_uncore_frequency} => Uncore bits = ${uncore_bits}"
	# Let's assume we can also set uncore for modern processors
	#    if [[ "$UARCH" == "HASWELL" ]]; then
	emon --write-msr 0x620="$uncore_bits"
	#    else
	#        echo "Non-HSW system: uncore freq. setting not done"
	#    fi
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
