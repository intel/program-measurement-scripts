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
old_uncore_bits=($(emon --read-msr 0x620 | grep MSR | cut -f2 -d=|uniq ))

# save orignal THP setting first
old_thp_setting=$( cat /sys/kernel/mm/transparent_hugepage/enabled | sed -n 's/.*\[\(.*\)\].*/\1/p;' )

old_frequency=$( cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_setspeed | head -n 1 )


echo $old_prefetcher_bits  $old_thp_setting $old_frequency $old_uncore_bits

exit 0

