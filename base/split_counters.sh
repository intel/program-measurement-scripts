#!/bin/bash

source $CLS_FOLDER/const.sh

if [[ "$1" == "" ]]
then
	echo "ERROR! Invalid arguments (need: emon counters list)"
	exit -1
fi

emon_counters="$1"

event_sets=$(emon --dry-run -C"($emon_counters)" | sed 's: :_:g')

event_sets_names=($(echo $event_sets | tr ' ' '\n' | grep Event))
event_sets_idx=($(echo $event_sets | tr ' ' '\n' | nl |  grep Event | sed 's:\s\+\(.*\)\s\+:\1 :' | cut -d' ' -f1))
event_sets_idx=( $(echo ${event_sets_idx[@]}) $(( $(echo $event_sets | tr ' ' '\n' | wc -l) + 1 )) )

#Build the list of all supported core and uncore events
event_set_counters=""
for ((i=0; i<${#event_sets_names[@]}; i++))
do
	begin=$((${event_sets_idx[$i]} + 1))
	end=$((${event_sets_idx[(($i +1))]} - 1 ))

	new_set=$(echo $event_sets | tr ' ' '\n' | sed -n "$begin,$end p" | tr '\n' ',' | sed 's:,$::')
	new_set="${event_sets_names[$i]}:$new_set"
	#	echo $new_set
	event_set_counters=$event_set_counters${DELIM}$new_set
done
event_set_counters=$(echo $event_set_counters | sed 's:^'${DELIM}'::')

#Building the core events list
fuse_core_events=$(echo $event_set_counters | tr ${DELIM} '\n' | egrep "^Event_Set" | tr '\n' ${DELIM})
fuse_core_events=$(echo $fuse_core_events | sed 's:'${DELIM}'$::')
#echo $fuse_core_events

#Building the uncore events list
uncore_events=$(echo $event_set_counters | tr ${DELIM} '\n' | grep "Uncore" | tr '\n' ${DELIM})
uncore_events=$(echo $uncore_events | sed 's:'${DELIM}'$::')
uncore_sets=$(echo $event_set_counters | tr ${DELIM} '\n' | grep "Uncore" |  cut -d':' -f1 | sed 's:.*\(Event_Set_.*\):\1:' | sort -u )
fuse_uncore_events=""
for s in $uncore_sets
do
	myset=$(echo $uncore_events | tr ${DELIM} '\n' | grep $s | cut -d':' -f2 | tr '\n' ',')
	myset=$(echo $myset | sed 's:,$::')
	fuse_uncore_events="$fuse_uncore_events"${DELIM}"Uncore_$s:$myset"
done
fuse_uncore_events=$(echo $fuse_uncore_events | sed 's:^'${DELIM}'::')
#echo $fuse_uncore_events

#Merge the core and uncore event lists and separte using '#'
fuse_counters="$fuse_core_events#$fuse_uncore_events"

echo $fuse_counters
