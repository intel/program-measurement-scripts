#!/bin/bash

prefix="/nfs/fx/home/cwong29/working/NR-scripts"
nr_prefix="${prefix}/nr-codelets/numerical_recipes"
saeed_prefix="${prefix}/intel_codelets"
tmpfile=$(mktemp)

shopt -s extglob

for codelet_dir in ${nr_prefix}/*/*/*_+([[:digit:]])_?e ${saeed_prefix}/*/*/*+([[:digit:]])_?e ; do
	for cls_dir in $codelet_dir/cls_res_*_*; do
		if [ -d ${cls_dir} ]; then
			if [ ! -f ${cls_dir}/counters/*_metrics.cape.csv ]; then
				echo "Generate cape format csv at ${cls_dir}"
				./format2cape.sh ${cls_dir} $(hostname)
			fi
			# cape file exists
			capefile="${cls_dir}/counters/*_metrics.cape.csv"
			head -1 ${capefile} >> ${tmpfile}
		fi
	done
done

echo ${tmpfile}
