#!/bin/bash -l

#export HOSTNAME="fxe12-cwong2901_nopref"

nb_args="$#"

CLS_FOLDER="$PWD"

DECAN_FOLDER="$CLS_FOLDER/sdecan"
DECAN_CONFIGURATOR="$DECAN_FOLDER/prepare_decan_conf.sh"
DECAN_CONFIGURATION="$DECAN_FOLDER/decan.conf"
DECAN="$DECAN_FOLDER/sdecan"
DECAN_LIBLOC="$DECAN_FOLDER/liblocinstru.so"
DECAN_REPORT="decanmodifs.report"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$DECAN_FOLDER"
export LD_LIBRARY_PATH="/localdisk/vincent_libraries:$LD_LIBRARY_PATH"
export PATH="/opt/intel/Compiler/12.1/bin/:$PATH:/opt/intel/bin"

MAQAO_FOLDER="$CLS_FOLDER/maqao"
MAQAO="$MAQAO_FOLDER/maqao"

CLS_RES_FOLDER="cls_res_${HOSTNAME}"

# For w_adjust.sh use
CODELET_LENGTH=100
MIN_REPETITIONS=250

# For run_codelet.sh (1/2)
META_REPETITIONS=11
ACTIVATE_COUNTERS=1
ACTIVATE_ADVANCED_COUNTERS=0

# For cls.sh
ACTIVATE_DYNAMIC_GROUPING=0
COMBINATORICS="$CLS_FOLDER/dynamic_grouping/combinatorics/combinatorics"
COMBINATORICS_SH="$CLS_FOLDER/dynamic_grouping/combinatorics/combinatorics.sh"

# Modules
#module load compilers/intel/12.1.3
#module load tools/likwid/2.3.0
#module load tools/numactl/2.0.7

# For generate_original.sh
BINARIES_FOLDER="binaries"
export LANG=en_US.utf8
export LC_ALL=en_US.utf8


# For generate_variants.sh
declare -A transforms
transforms+=([REF]="time_reference_div_on_stack")
transforms+=([REF_PREF]="time_reference_pref")
transforms+=([REF_SAN]="time_reference")

transforms+=([DL1]="splitntime_dt1_rat_dos")
transforms+=([DL1_SAN]="splitntime_dt1_rat")
transforms+=([DL1_dos]="splitntime_dt1_rat_dos")
transforms+=([DL2_rat]="splitntime_dt2_rat")
transforms+=([DL3_rat]="splitntime_dt3_rat")

transforms+=([LS]="splitntime_mem_AS")
transforms+=([LS_PREF]="splitntime_mem_AS_pref")
transforms+=([LS_RAT1B]="splitntime_mem_AS_rat1b")
transforms+=([LS_FES]="splitntime_mem_AS_ratmb")

transforms+=([FP]="splitntime_fp_div_on_stack")
transforms+=([FP_RAT1B]="splitntime_fp_rat1b")
transforms+=([FP_FES]="splitntime_fp_div_on_stack_ratmb")
transforms+=([FP_SAN]="splitntime_fp")

transforms+=([NOLS-NOFP]="splitntime_noas-nofpi")
transforms+=([NOLS-NOFP_RAT1B]="splitntime_noas-nofpi_rat1b")
transforms+=([FES]="splitntime_noas-nofpi_ratmb")

transforms+=([REF_NODIV]="reference_nodivision")
transforms+=([REF_NORED]="reference_noreduction")

# For run_codelet.sh (2/2)
declare -A XP_CORES
XP_CORES+=([britten]="3")
XP_CORES+=([buxtehude]="7")
XP_CORES+=([chopin]="3")
XP_CORES+=([dandrieu]="3")
XP_CORES+=([massenet]="23")
XP_CORES+=([sviridov]="1")
XP_CORES+=([fxe12-cwong2901]="11")
XP_CORES+=([fxe12-cwong2901_nopref]="11")
XP_CORES+=([fxtcarilab027]="11")

MEMLOADER="$CLS_FOLDER/memloader"
declare -A MEMLOAD_ARGS
MEMLOAD_ARGS+=([fxe12-cwong2901]="--core=6 --core=7 --core=8 --core=9 --core=10 --self_pin=6 --ref_freq=2500000")
MEMLOAD_ARGS+=([fxtcarilab027]="--core=6 --core=7 --core=8 --core=9 --core=10 --self_pin=6 --ref_freq=2500000")

XP_CORE=${XP_CORES[$HOSTNAME]}
MEMLOAD_ARGS_LIST=${MEMLOAD_ARGS[$HOSTNAME]}

# For gather_results.sh
CPIS_FOLDER="cpis"
COUNTERS_FOLDER="counters"

