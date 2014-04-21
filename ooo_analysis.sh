#!/bin/bash

source ./const.sh

bin="./OoO"
bin_file="$1"
loop_id="$2"

loop_file="$bin_file".snb.ooo

#echo "Trying to generate OoO input file from '$bin_file', loop id = '$loop_id'" 1>&2

"$MAQAO" ./maqao/generator.lua binary="$bin_file" loop_id="$loop_id" uarch="sandy_bridge" > "$loop_file"

echo "OoO_snb_normal;OoO_snb_normal_stalls;OoO_snb_large_resources_gain;OoO_snb_large_resources_stalls;OoO_snb_halved_resources_penalty;OoO_snb_halved_resources_stalls;OoO_long_latency_penalty;OoO_long_latency_stalls"

name=$( basename "$loop_file" | sed 's/_cpi.snb.ooo//g' )

output=$( "$bin" "$loop_file" --verbosity 0 $ooo_args )
res=$( echo "$output" | grep iteration: | cut -f2 -d':' | sed 's/ //g' )
main_culprits=$( echo "$output" | grep "Stalls per iteration" | sed 's/Stalls per iteration \[\([^\]*\)\]/\1/g' )


output=$( "$bin" "$loop_file" --verbosity 0 $ooo_args --rs_size 1000 --rob_size 1000 --prf_int_size 1000 --prf_float_size 1000 --prf_max 1000 --branch_buffer_size 1000 --load_buffer_size 1000 --store_buffer_size 1000 )
res_infinite=$( echo "$output" | grep iteration: | cut -f2 -d':' | sed 's/ //g' )
gain_infinite=$( echo "$res - $res_infinite" | bc )
infinite_culprits=$( echo "$output" | grep "Stalls per iteration" | sed 's/Stalls per iteration \[\([^\]*\)\]/\1/g' )

output=$( "$bin" "$loop_file" --verbosity 0 $ooo_args --rs_size 27 --rob_size 84 --prf_int_size 65 --prf_float_size 55 --prf_max 74 --branch_buffer_size 24 --load_buffer_size 32 --store_buffer_size 18 )
res_halved=$( echo "$output" | grep iteration: | cut -f2 -d':' | sed 's/ //g' )
penalty_halved=$( echo "$res_halved - $res" | bc )
halved_culprits=$( echo "$output" | grep "Stalls per iteration" | sed 's/Stalls per iteration \[\([^\]*\)\]/\1/g' )


output=$( "$bin" "$loop_file" --verbosity 0 $ooo_args --load_latency 40 )
res_long_latency=$( echo "$output" | grep iteration: | cut -f2 -d':' | sed 's/ //g' )
penalty_long_latency=$( echo "$res_long_latency - $res" | bc )
long_latency_culprits=$( echo "$output" | grep "Stalls per iteration" | sed 's/Stalls per iteration \[\([^\]*\)\]/\1/g' )

echo -e "$res;$main_culprits;$gain_infinite;$infinite_culprits;$penalty_halved;$halved_culprits;$penalty_long_latency;$long_latency_culprits"
