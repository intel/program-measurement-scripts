#!/bin/bash

source ./const.sh

#echo "                                                                        Transforming STAN output"

if [ $# -ne 2 ]
then
	echo "$0 <file> <loop id>"
	exit -1
fi

file=$1
loop_id=$2


#echo "*******************************************************" && awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g"  | tail -n +7 | awk '/General loop properties/,0'

#echo "                                                                        Extracting Cycles summary"
echo "*******************************************************"
echo "                   Cycles summary                      "
awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g" | sed "s/\t//g" | tail -n +7 | awk ' /Cycles summary/ {flag=1;next} /Vectorization ratios/{flag=0} flag { print }'

#echo "                                                                        Extracting Back-end table"

#echo "*******************************************************"
echo "                       Back-end"
echo "*******************************************************"

awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g" | tail -n +7 | awk '/General loop properties/,0' | grep P0 -A 2 | sed s/\\tP0/spaceholder\\tP0/g > tabz

cols=`head -n 1 tabz | wc -w`
for (( i=1; i <= $cols; i++))
do
	awk '{printf ("%s%s", tab, $'$i'); tab="\t"} END {print ""}' tabz
	#done | sed "s/spaceholder//g" | sed "s/\tuops/        uops/g" | sed "s/\t/    /g" | sed "s/ cycles/cycles/g"
done | sed "s/spaceholder//g" | sed "s/\t/"${DELIM}"/g"
echo

rm -f tabz

awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g" | tail -n +7 | awk '/General loop properties/,0' | grep "Cycles executing div" -A2

#echo "                                                                        Extracting General Loop Properties"
echo "*******************************************************"
echo "                General Loop Properties                "
awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g"  | tail -n +7 | awk ' /General loop properties/ {flag=1;next} /Back-end/{flag=0} flag { print }' | head -n -2
echo

#echo "                                                                        Extracting Vectorization ratios"
echo "*******************************************************"
echo "                Vectorization ratios                "
awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g" | sed "s/=/"${DELIM}"/g"  | tail -n +7 | awk ' /Vectorization ratios/ {flag=1;next} /End/{flag=0} flag { print }'
echo

#echo "                                                                        Extracting Assembly code"
echo "*******************************************************"
echo "                    Assembly code                      "
awk ' /Processing loop '$loop_id'/ {flag=1;next} /End/{flag=0} flag { print }' $file | sed "s/:/"${DELIM}"/g" | sed "s/\t/"${DELIM}"/g" | tail -n +7 | awk ' /Assembly code/ {flag=1;next} /General loop properties/{flag=0} flag { print }'
echo


exit 0
