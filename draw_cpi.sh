#!/bin/bash

nb_args=$#
if [[ "$nb_args" != "3" ]]
then
	echo "ERROR! Invalid arguments (need: ...)."
	exit -1
fi

cpi_file=$( readlink -f "$1" )
cpi_folder=$( dirname "$cpi_file" )

partial_title="$2"
y_axis="$3"

codelet_name=$( tail -n 1 "$cpi_file" | cut -f1 -d';' )
memload=$( tail -n 1 "$cpi_file" | cut -f3 -d';' )
freq=$( tail -n 1 "$cpi_file" | cut -f4 -d';' )

#echo "Codelet name: '$codelet_name'"
#echo "Memload: '$memload'"
#echo "Freq: '$freq'"

title="$partial_title: $codelet_name, $memload MB/s, $freq kHz"

echo "Drawing '$title'"


plot=$(	awk -F ';' '
		END{
			FS=";";

			#for (i = 0; i < (NF - 5); i++)
			#{
			#	printf "set style line " (i+1) " lt " (i+1) "\n";
			#}

			printf "plot ";
			for (i = 0; i < (NF - 5); i++)
			{
				printf "\"'$cpi_file'\" using " (5 + i) ":xticlabels(2) lw 2 lt "(i + 1)" lc "(i + 1)*2-1" with linespoints";
				if (i != (NF - 6)){ printf ", \\" }
				printf "\n";
			}
		}
		' "$cpi_file" )

#echo "Plot: '$plot'"

t=$( echo -e	"
		#!/usr/bin/gnuplot

		set datafile separator \";\"
		set term postscript eps color size 3,1.8 font 10
		set output \""${cpi_folder}/pic_cpi_${codelet_name}_${memload}_${freq}.eps"\"

		set xlabel \"Data Size\"
		set ylabel \"$y_axis\"

		set pointsize 1

		set title \"$title\"

		set size 1,.8

		set xtics rotate
		set lmargin 31
		set rmargin 1
		set key autotitle columnhead
		set key on outside left top Right title '' box 4


		$plot
		" ) 

echo -e "$t" | gnuplot

exit $?
