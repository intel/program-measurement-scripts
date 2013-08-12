#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need: codelet binary, loop id)."
	exit -1
fi

codelet_binary="$1"
loop_id="$2"

groups=$( ~/nfs/CLS/maqao/maqao module=grouping format=pcr bin="$codelet_binary" loop="$loop_id" )

#echo "Groups = '$groups'"

if [[ "$groups" == "" ]]
then
	echo "Problem with group analysis! (bin='$codelet_binary', loop='$loop_id')"
	exit -1
fi

id_group=1
for group in $groups
do
	echo -e "Parsing G[$id_group]"

	nb_insns=$( echo "$group" | cut -f1 -d';' )
	echo -e "\tNb insns = $nb_insns"

	pattern=$( echo "$group" | cut -f2 -d';' )
	echo -e "\tPattern = $pattern"

	echo -e "\tParsing instructions"
	for insn_id in $( seq $nb_insns )
	do
		let "insn_address_field = 2 + $insn_id"
		insn_address=$( echo "$group" | cut -f$insn_address_field -d';' )

		let "insn_memncode_field = 2 + $nb_insns + $insn_id"
		insn_memncode=$( echo "$group" | cut -f$insn_memncode_field -d';' )

		let "insn_offset_field = 2 + 2 * $nb_insns + $insn_id"
		insn_offset=$( echo "$group" | cut -f$insn_offset_field -d';' )

		echo -e "\t\t$insn_id [$insn_address] : $insn_memncode $insn_offset(whatever_something)"
	done

	let "stride_status_field = 2 + 3 * $nb_insns + 3"
	stride_status=$( echo "$group" | cut -f$stride_status_field -d';' )
	echo -e "\tStride status = $stride_status"

	let "stride_field = 2 + 3 * $nb_insns + 4"
	stride=$( echo "$group" | cut -f$stride_field -d';' )
	echo -e "\tStride = $stride"

	let "transferred_bytes_field = 2 + 3 * $nb_insns + 6"
	transferred_bytes=$( echo "$group" | cut -f$transferred_bytes_field -d';' )
	echo -e "\tTransferred bytes = $transferred_bytes"

	let "touched_bytes_field = 2 + 3 * $nb_insns + 7"
	touched_bytes=$( echo "$group" | cut -f$touched_bytes_field -d';' )
	echo -e "\tTouched bytes = $touched_bytes"

	let "overlapped_bytes_field = 2 + 3 * $nb_insns + 8"
	overlapped_bytes=$( echo "$group" | cut -f$overlapped_bytes_field -d';' )
	echo -e "\tOverlapped bytes = $overlapped_bytes"

	let "span_field = 2 + 3 * $nb_insns + 9"
	span=$( echo "$group" | cut -f$span_field -d';' )
	echo -e "\tSpan = $span"

	let "fresh_bytes_field = 2 + 3 * $nb_insns + 10"
	fresh_bytes=$( echo "$group" | cut -f$fresh_bytes_field -d';' )
	echo -e "\tFresh bytes = $fresh_bytes"

	# Overlap? No overlap? Register stuff? Are the touch & transferred field addresses OK? What other info can I get?


	let "id_group = $id_group + 1"
done
