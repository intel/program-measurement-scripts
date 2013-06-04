#!/bin/bash

decan_path=$1
binary_path=$2
function_name=$3
macro=$4
groups="$5"

treated=0

echo "Preparing DECAN conf"
echo "Decan path: $decan_path"
echo "Binary path: $binary_path"
echo "Function name: $function_name"
echo "Macro: $macro"
echo "Groups: '$groups'"


# ----------- Basic transformations
if [[ "$macro" == "time_reference"* ]]
then
	transformation="none"
	option1=""
	option2=""
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "time_reference_div_on_stack"* ]]
then
	transformation="none"
	option1=""
	option2=""
	timers="basic"
	counters=""

	elementary="divonstack"
	divider_value="3.14"
	divided_value="7.89"

	treated=1
fi

if [[ "$macro" == "splitncount"* ]]
then
	transformation="none"
	option1=""
	option2=""
	timers=""
	counters="basic"
	treated=1
fi


# ----------- DT transformations
if [[ "$macro" == "splitntime_dt1"* ]]
then
	transformation="stream"
	option1="dt"
	option2="dt_sub_0"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_dt1_rat"* ]]
then
	transformation="stream"
	option1="dt"
	option2="dt_sub_1"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "special_grouping"* ]]
then
	transformation="stream"
	option1="mem"
	option2="delete"
	grouping="delete"
	group_option="delete"

	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_dt2_rat"* ]]
then
	transformation="stream"
	option1="dt"
	option2="dt_sub_2"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_dt3_rat"* ]]
then
	transformation="stream"
	option1="dt"
	option2="dt_sub_3"
	timers="basic"
	counters=""
	treated=1
fi


# ----------- Mem transformations
if [[ "$macro" == "splitntime_mem_AS"* ]]
then
	transformation="stream"
	option1="mem"
	option2="delete"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_mem_AS_rat1b"* ]]
then
	transformation="stream"
	option1="mem"
	option2="one-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_mem_AS_ratmb"* ]]
then
	transformation="stream"
	option1="mem"
	option2="n-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi


# ----------- FP transformations
if [[ "$macro" == "splitntime_fp"* ]]
then
	transformation="stream"
	option1="fp"
	option2="delete"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_fp_rat1b"* ]]
then
	transformation="stream"
	option1="fp"
	option2="one-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_fp_ratmb"* ]]
then
	transformation="stream"
	option1="fp"
	option2="n-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_fp_div_on_stack"* ]]
then
	transformation="stream"
	option1="fp"
	option2="delete"
	timers="basic"
	counters=""

	elementary="divonstack"
	divider_value="3.14"
	divided_value="7.89"

	treated=1
fi


# ----------- Control transformations
if [[ "$macro" == "splitntime_noas-nofpi"* ]]
then
	transformation="stream"
	option1="ctrl"
	option2="delete"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_noas-nofpi_rat1b"* ]]
then
	transformation="stream"
	option1="ctrl"
	option2="one-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "splitntime_noas-nofpi_ratmb"* ]]
then
	transformation="stream"
	option1="ctrl"
	option2="n-byte-nop"
	timers="basic"
	counters=""
	treated=1
fi


# ----------- Special transformations
if [[ "$macro" == "reference_nodivision"* ]]
then
	transformation="atomic"
	option1=""
	option2="no_division"
	timers="basic"
	counters=""
	treated=1
fi

if [[ "$macro" == "reference_noreduction"* ]]
then
	transformation="atomic"
	option1=""
	option2="no_reduction"
	timers="basic"
	counters=""
	treated=1
fi


if [[ "$macro" == *"_hwc" ]]
then
	timers=""
	counters=""
	hardware_counters=""
fi


if [ $treated -eq 0 ]
then
	rm -f "$decan_path/decan.conf"
	echo "Macro was not recognized. Aborting."
	exit -1
fi


echo "---1------------------------------"	>  $decan_path/decan.conf
echo "binary= $binary_path"			>> $decan_path/decan.conf
echo "functions= $function_name"		>> $decan_path/decan.conf
echo "loop_id= $loop_id"			>> $decan_path/decan.conf

echo "---2------------------------------"	>> $decan_path/decan.conf
echo "transformation= $transformation"		>> $decan_path/decan.conf
echo "option1= $option1"			>> $decan_path/decan.conf
echo "option2= $option2"			>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "global_variable_value=0"			>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "parallel= "				>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "instance_mode= "				>> $decan_path/decan.conf

echo "---4------------------------------"	>> $decan_path/decan.conf
echo "timers= $timers"				>> $decan_path/decan.conf
echo "timing_system= refined"			>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "counters= $counters"			>> $decan_path/decan.conf
echo "hardware_counters= $hardware_counters"	>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "groups= $grouping"			>> $decan_path/decan.conf
echo "group_option= $group_option"		>> $decan_path/decan.conf
echo "dynamic_groups= $groups"			>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "blacklist= " 				>> $decan_path/decan.conf

echo "----------------------------------"	>> $decan_path/decan.conf
echo "elementary=$elementary"			>> $decan_path/decan.conf
echo "divider_value= $divider_value"		>> $decan_path/decan.conf
echo "divided_value= $divided_value"		>> $decan_path/decan.conf


echo "DECAN conf was prepared successfully!"

exit 0
