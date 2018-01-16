#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "1" ]]
then
	echo "ERROR! Invalid arguments (need: number_of_groups)."
	exit -1
fi

number_of_groups="$1"

res=$( $COMBINATORICS "$1" | tr "\n" "|" | sed "s/ |/|/g" )

res=${res%?}

echo "$res"
