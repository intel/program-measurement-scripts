#!/bin/bash

nb_args=$#
if [[ "$nb_args" != "4" ]]
then
	echo "ERROR! Invalid arguments (need: ...)."
	exit -1
fi

counters_file=$( readlink -f "$1" )
counters_folder=$( dirname "$counters_file" )

partial_title="$2"
res_folder="$counters_folder/$partial_title"
mkdir "$counters_folder/$partial_title" &> /dev/null


y_axis="$3"
counters_to_draw="$4"

codelet_name=$( head -n 2 "$counters_file" | tail -n 1 | cut -f1 -d${DELIM} )
memload=$( head -n 2 "$counters_file" | tail -n 1 | cut -f3 -d${DELIM} )
freq=$( head -n 2 "$counters_file" | tail -n 1 | cut -f4 -d${DELIM} )
variant=$( head -n 2 "$counters_file" | tail -n 1 | cut -f5 -d${DELIM} )

available_counters=$( head -n 1 "$counters_file" | cut -f6- -d${DELIM} | tr ${DELIM} " " )

declare -A counter_columns

#echo "Codelet name: '$codelet_name'"
#echo "Memload: '$memload'"
#echo "Freq: '$freq'"
#echo "Freq: '$variant'"

#echo "Available counters: '$available_counters'"

i=6
for counter in $available_counters
do
	counter_columns[$counter]=$i
	let "i = i + 1"
done


#echo "Codelet name: '$codelet_name'"
#echo "Memload: '$memload'"
#echo "Freq: '$freq'"

title="$partial_title: $codelet_name, $variant, $memload MB/s, $freq kHz"

echo "Drawing '$title'"


for counter in $counters_to_draw
do
	last_counter="$counter"
done

plot="plot "
i=0
for counter in $counters_to_draw
do
	let "lt = $i + 1"
	let "lc = (($i + 1) * 2) - 1"
	let "i = $i + 1"

	plot=$( echo -e "$plot \"$counters_file\" using ${counter_columns[$counter]}:xticlabels(2) lw 2 lt $lt lc $lc with linespoints" )
	if [[ "$counter" != "$last_counter" ]]
	then
		plot=$( echo -e "$plot," )
	fi
	plot=$( echo -e "$plot\n" )

done

#echo  "plot: '$plot'"


#plot=$(	awk -F ${DELIM} '
#		END{
#			FS="'${DELIM}'";
#
#			printf "plot ";
#			for (i = 0; i < (NF - 5); i++)
#			{
#				printf "\"'$cpi_file'\" using " (5 + i) ":xticlabels(2) lw 2 lt "(i + 1)" lc "(i + 1)*2-1" with linespoints";
#				if (i != (NF - 6)){ printf ", \\" }
#				printf "\n";
#			}
#		}
#		' "$cpi_file" )

#echo "Plot: '$plot'"

t=$( echo -e	"
		#!/usr/bin/gnuplot

		set datafile separator \""${DELIM}"\"
		set term postscript eps color size 3.8,2.8 font 10
		set output \""${res_folder}/pic_counters_${codelet_name}_${memload}_${freq}_${variant}_${partial_title}.eps"\"

		set xlabel \"Data Size\"
		set ylabel \"$y_axis\"

		set pointsize 1

		set title \"$title\"

		set size 1,.8

		set xtics rotate
		set lmargin 6
		set rmargin 1
		set key autotitle columnhead
		set key on outside bottom center Right title ''


		$plot
" )

echo -e "$t" | gnuplot &> /dev/null

exit $?
