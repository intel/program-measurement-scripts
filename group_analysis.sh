#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need: codelet binary, loop id)."
	exit -1
fi

codelet_binary="$1"
loop_id="$2"

groups=$( "$MAQAO" module=grouping format=pcr bin="$codelet_binary" loop="$loop_id" | sed 's/\t/ /g' | sed 's/ /#/g' )

#echo "Groups = '$groups'" 1>&2

if [[ "$groups" == "" ]]
then
	echo "Problem with group analysis! (bin='$codelet_binary', loop='$loop_id')"
	exit -1
fi

titles=""
values=""

id_group=1
for group in $groups
do
	group=$( echo "$group" | sed 's/#/ /g' )
	#echo "Group: '$group'" 1>&2

	echo -e "Parsing G[$id_group]"

	nb_insns=$( echo "$group" | cut -f1 -d';' )
	echo -e "\tNb insns = '$nb_insns'"
	titles="[G$id_group] Nb insns;$titles"
	values="$nb_insns;$values"

	pattern=$( echo "$group" | cut -f2 -d';' )
	echo -e "\tPattern = $pattern"
	titles="[G$id_group] Pattern;$titles"
	values="$pattern;$values"

	echo -e "\tParsing instructions"
	for insn_id in $( seq $nb_insns )
	do
		let "insn_address_field = 2 + $insn_id"
		insn_address=$( echo "$group" | cut -f$insn_address_field -d';' )
		titles="[G$id_group] [I$insn_id] Address;$titles"
		values="$insn_address;$values"

		let "insn_mnemcode_field = 2 + $nb_insns + $insn_id"
		insn_mnemcode=$( echo "$group" | cut -f$insn_mnemcode_field -d';' )
		titles="[G$id_group] [I$insn_id] Mnem code;$titles"
		values="$insn_mnemcode;$values"

		let "insn_offset_field = 2 + 2 * $nb_insns + $insn_id"
		insn_offset=$( echo "$group" | cut -f$insn_offset_field -d';' )
		titles="[G$id_group] [I$insn_id] Offset;$titles"
		values="$insn_offset;$values"

		let "insn_field = 2 + 3 * $nb_insns + $insn_id"
		insn=$( echo "$group" | cut -f$insn_field -d';' )
		titles="[G$id_group] [I$insn_id] ASM;$titles"
		values="$insn;$values"

		echo -e "\t\t$insn_id [$insn_address] : $insn"
	done

	let "stride_status_field = 2 + 4 * $nb_insns + 3"
	stride_status=$( echo "$group" | cut -f$stride_status_field -d';' )
	echo -e "\tStride status = $stride_status"
	titles="[G$id_group] Stride status;$titles"
	values="$stride_status;$values"

	let "stride_field = 2 + 4 * $nb_insns + 4"
	stride=$( echo "$group" | cut -f$stride_field -d';' )
	echo -e "\tStride = $stride"
	titles="[G$id_group] Stride;$titles"
	values="$stride;$values"

	let "transferred_bytes_field = 2 + 4 * $nb_insns + 6"
	transferred_bytes=$( echo "$group" | cut -f$transferred_bytes_field -d';' )
	echo -e "\tTransferred bytes = $transferred_bytes"
	titles="[G$id_group] Transferred bytes;$titles"
	values="$transferred_bytes;$values"

	let "touched_bytes_field = 2 + 4 * $nb_insns + 7"
	touched_bytes=$( echo "$group" | cut -f$touched_bytes_field -d';' )
	echo -e "\tTouched bytes = $touched_bytes"
	titles="[G$id_group] Touched bytes;$titles"
	values="$touched_bytes;$values"

	let "overlapped_bytes_field = 2 + 4 * $nb_insns + 8"
	overlapped_bytes=$( echo "$group" | cut -f$overlapped_bytes_field -d';' )
	echo -e "\tOverlapped bytes = $overlapped_bytes"
	titles="[G$id_group] Overlapped bytes;$titles"
	values="$overlapped_bytes;$values"

	let "span_field = 2 + 4 * $nb_insns + 9"
	span=$( echo "$group" | cut -f$span_field -d';' )
	echo -e "\tSpan = $span"
	titles="[G$id_group] Span;$titles"
	values="$span;$values"

	let "fresh_bytes_field = 2 + 4 * $nb_insns + 10"
	fresh_bytes=$( echo "$group" | cut -f$fresh_bytes_field -d';' )
	echo -e "\tFresh bytes = $fresh_bytes"
	titles="[G$id_group] Fresh bytes;$titles"
	values="$fresh_bytes;$values"

	# Overlap? No overlap? Register stuff? Are the touch & transferred field addresses OK? What other info can I get?


	let "id_group = $id_group + 1"
done

echo "$titles"
echo "$values"
