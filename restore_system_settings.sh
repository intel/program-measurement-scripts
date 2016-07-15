#!/bin/bash
# Restore the system settings previously saved by save_system_settings.sh
# following usage can be done:
# saved_settings=$(save_system_settings.sh ...)
# .. do something
# restore_system_settings.sh ${saved_settings}
# System settings restored.


source $(dirname $0)/const.sh

if [[ "$nb_args" != "4" ]]
then
        echo "ERROR! Invalid arguments (need prefetcher bits, thp setting, freq, uncore bit)."
        exit -1
fi

old_prefetcher_bits="$1"
old_thp_setting="$2"
old_frequency="$3"
old_uncore_bits="$4"


# Restore prefetcher settings.
echo "Writing ${old_prefetcher_bits} to MSR 0x1a4 to restore prefetcher settings."
#emon --write-msr 0x1a4=${old_prefetcher_bits}
set_prefetcher_bits ${old_prefetcher_bits}
# restore thp setting
set_thp ${old_thp_setting}

if [[ "$UARCH" == "HASWELL" ]]; then
	emon --write-msr 0x620="$old_uncore_bits"
fi

$(dirname $0)/set_frequency.sh ${old_frequency}
