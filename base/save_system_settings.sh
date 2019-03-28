#!/bin/bash
# Save the system settings
# Output original settings for later resume purpose.
# Note: should make sure the output of this script can be used as input so that
# following usage can be done:
# saved_settings=$(save_system_settings.sh ...)
# .. do something
# restore_system_settings.sh ${saved_settings}
# System settings restored.


source $(dirname $0)/const.sh

#Saving old prefetcher settings
old_prefetcher_bits=($(emon --read-msr 0x1a4 | grep MSR | cut -f2 -d=|uniq ))
if [[ "${#old_prefetcher_bits[@]}" -gt "1" ]]
then
	# Different settings among processor - not supported.
	echo "Processors with different original prefetcher settings.  Cancelling CLS." >& 2
	exit -1
fi

#Saving old uncore settings
old_uncore_bits=($(emon --read-msr 0x620 | grep MSR | cut -f2 -d=|uniq|tr -d "\r" ))

((hi_bits=old_uncore_bits>>8))
((lo_bits=old_uncore_bits&0xff))
# In same units as Core freq.
((min_uncore_freq=hi_bits*100000))
((max_uncore_freq=lo_bits*100000))


# save orignal THP setting first
if [[ "$(uname)" == "CYGWIN_NT-6.2" ]]; then
	old_thp_setting="NA"
	(( old_frequency=$(wmic cpu get CurrentClockSpeed|sed "s/[^0-9]*//g" |head -2|tail -1|tr -d '\n')*1000 ))
else
	old_thp_setting=$( cat /sys/kernel/mm/transparent_hugepage/enabled | sed -n 's/.*\[\(.*\)\].*/\1/p;' )
	old_frequency=$( cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )
fi

#echo $old_prefetcher_bits  $old_thp_setting $old_frequency $old_uncore_bits
echo $old_prefetcher_bits  $old_thp_setting $old_frequency $min_uncore_freq $max_uncore_freq

exit 0

