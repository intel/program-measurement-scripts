#!/bin/bash -l

source ../base/const.sh
source ../base/vrun_launcher.sh

module load atc/1.5

run() {
  runId=$@
  
  variants="ORG"
  linear_sizes="10000"
  memory_loads="0"
  # TODO make this work somehow; technically saying -t=28 means only 28; more
  # cores without specifying -t is pointless
  num_cores="1"
  prefetchers="0"
  frequencies="2200000"
  
  prefix=$(readlink -f ../..)
  galois_prefix="${prefix}/galois-codelets/build"
  galois_lonestar_prefix="${galois_prefix}/lonestar/codelets"
  #echo ${galois_lonestar_prefix}
  
  # SR runs (including some original)
  declare -gA name2path
  declare -gA name2sizes
  declare -ga run_codelets
  
  fill_codelet_maps "${galois_lonestar_prefix}" "${linear_sizes}"

  # name2sizes must be specified for correctness/backward compatibility purposes
  # (script only executes if something exists in name2sizes)
  name2sizes[pagerank_pull_codelet]="CMDLINE"

  # specify what to pass into command line
  USECMDLINE="-t=28 /net/ohm/export/iss/dist-inputs/transpose/rmat15.tgr"
  # specify the prefix to use when specifying repetitions
  REPPREFIX="-runs="

  CMDLINELABELS="threads graph_name"
  
  run_codelets=( pagerank_pull_codelet )
  
  runLoop "${runId}" "$variants" "$memory_loads" "$frequencies" "$num_cores" \
          "$prefetchers" \
          "RESOURCE=0,SQ=0,SQ_HISTOGRAM=0,LFB_HISTOGRAM=0,TOPDOWN=0,LFB=0,MEM_ROWBUFF=0,MEM_TRAFFIC=0,MEM_HIT=0,TLB=0,LSD=0"

  return
}

launchIt $0 run "$@"
