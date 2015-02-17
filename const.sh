#!/bin/bash -l

if [[ "$HOSTNAME" == "fxe32lin04.fx.intel.com" ]]
then
	export HOSTNAME="fxe32lin04"
else
	if echo "$HOSTNAME" | grep "fxatom"
	then
		export HOSTNAME="fxsilvermont"
	else
		if echo "$HOSTNAME" | grep "fxilab10"
		then
			export HOSTNAME="fxhaswell-desktop"
		else
			if echo "$HOSTNAME" | grep "fxilab11"
			then
				export HOSTNAME="fxhaswell"
			else
				if [[ "$HOSTNAME" == "fxilab150" || "$HOSTNAME" == "fxilab151" || "$HOSTNAME" == "fxilab152" ]]
				then
					export HOSTNAME="fxhaswell-l4"
				fi
			fi
		fi
	fi
fi

nb_args="$#"

CLS_FOLDER="$PWD"

DECAN_FOLDER="$CLS_FOLDER/sdecan"
DECAN_CONFIGURATOR="$DECAN_FOLDER/prepare_decan_conf.sh"
DECAN_CONFIGURATION="$DECAN_FOLDER/decan.conf"
DECAN="$DECAN_FOLDER/sdecan"
DECAN_LIBLOC="$DECAN_FOLDER/liblocinstru.so"
DECAN_REPORT="decanmodifs.report"
export LD_LIBRARY_PATH="$DECAN_FOLDER:$LD_LIBRARY_PATH"
#source /nfs/fx/proj/openmp/compilers/intel/12.1/Linux/intel64/load.sh &> /dev/null
#export PATH="/opt/intel/Compiler/12.1/bin/:/opt/intel/composer_xe_2011_sp1/bin/:/opt/intel/composer_xe_2011_sp1.9.293/bin/intel64/:/opt/intel/composer_xe_2011_sp1.11.339/bin/intel64/:$PATH:/opt/intel/bin/:/nfs/fx/proj/openmp/compilers/intel/12.1/Linux/install/composer_xe_2011_sp1/bin"
#export PATH="$PATH:/nfs/fx/proj/openmp/compilers/intel/15.0/Linux/pkgs/update0/composer_xe_2015.0.090/bin/intel64/"
if [[ "$HOSTNAME" == "fxtcarilab027" ]]; then
	source /nfs/fx/proj/openmp/compilers/intel/12.1/Linux/intel64/load.sh
else
	source /nfs/fx/proj/openmp/compilers/intel/15.0/Linux/intel64/load0.sh
fi

MAQAO_FOLDER="$CLS_FOLDER/maqao"
MAQAO="$MAQAO_FOLDER/maqao"

CLS_RES_FOLDER="cls_res_${HOSTNAME}"

# For w_adjust.sh use
#CODELET_LENGTH=50
CODELET_LENGTH=200
MIN_REPETITIONS=100

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

# For counter measurements + CQA parameter (?)
some_res=$( echo "$HOSTNAME" | grep "silvermont" )
if [[ "$some_res" == "" ]]
then
	some_res=$( echo "$HOSTNAME" | grep "haswell" )
	if [[ "$some_res" == "" ]]
	then
		UARCH="SANDY_BRIDGE"
		PRETTY_UARCH="Sandy Bridge"
	else
		UARCH="HASWELL"
		PRETTY_UARCH="Haswell"
	fi
else
	UARCH="SILVERMONT"
	PRETTY_UARCH="Silvermont"
fi

if [[ "$HOSTNAME" == "fxilab148" ]]
then
	UARCH="IVY_BRIDGE"
	PRETTY_UARCH="Ivy Bridge"
fi

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
transforms+=([FP_DL]="splitntime_dt4")

transforms+=([NOLS-NOFP]="splitntime_noas-nofpi")
transforms+=([NOLS-NOFP_RAT1B]="splitntime_noas-nofpi_rat1b")
if [[ "$UARCH" == "SILVERMONT" ]]
then
	transforms+=([FES]="splitntime_noas-nofpi_rat1b")
else
	transforms+=([FES]="splitntime_noas-nofpi_ratmb")
fi
transforms+=([REF_NODIV]="reference_nodivision")
transforms+=([REF_NORED]="reference_noreduction")
transforms+=([DEC]="reference_decoupled")
transforms+=([DEC_SAN]="reference_addnopped")

# For run_codelet.sh (2/2)
declare -A XP_CORES
XP_CORES+=([britten]="3")
XP_CORES+=([buxtehude]="7")
XP_CORES+=([chopin]="3")
XP_CORES+=([dandrieu]="3")
XP_CORES+=([massenet]="23")
XP_CORES+=([sviridov]="1")
XP_CORES+=([fxatom001]="1")
XP_CORES+=([fxatom002]="1")
XP_CORES+=([fxatom003]="1")
XP_CORES+=([fxatom004]="1")
XP_CORES+=([fxsilvermont]="1")
XP_CORES+=([fxe12-cwong2901]="11")
XP_CORES+=([fxe12-cwong2901_nopref]="11")
XP_CORES+=([fxe32lin04]="11")
XP_CORES+=([fxhaswell-desktop]="3")
XP_CORES+=([fxhaswell]="3")
XP_CORES+=([fxtcarilab027]="11")
XP_CORES+=([fxhaswell-l4]="3")
XP_CORES+=([fxilab147]="5")
XP_CORES+=([fxilab148]="19")

declare -A XP_CORES
XP_NODES+=([britten]="0")
XP_NODES+=([buxtehude]="1")
XP_NODES+=([chopin]="0")
XP_NODES+=([dandrieu]="0")
XP_NODES+=([massenet]="1")
XP_NODES+=([sviridov]="0")
XP_NODES+=([fxatom001]="0")
XP_NODES+=([fxatom002]="0")
XP_NODES+=([fxatom003]="0")
XP_NODES+=([fxatom004]="0")
XP_NODES+=([fxsilvermont]="0")
XP_NODES+=([fxe12-cwong2901]="1")
XP_NODES+=([fxe12-cwong2901_nopref]="1")
XP_NODES+=([fxe32lin04]="1")
XP_NODES+=([fxhaswell-desktop]="0")
XP_NODES+=([fxhaswell]="0")
XP_NODES+=([fxtcarilab027]="1")
XP_NODES+=([fxhaswell-l4]="0")
XP_NODES+=([fxilab147]="0")
XP_NODES+=([fxilab148]="1")


MEMLOADER="$CLS_FOLDER/memloader"
declare -A MEMLOAD_ARGS
MEMLOAD_ARGS+=([fxe12-cwong2901]="--core=6 --core=7 --core=8 --core=9 --core=10 --self_pin=6 --ref_freq=2500000")
MEMLOAD_ARGS+=([fxtcarilab027]="--core=6 --core=7 --core=8 --core=9 --core=10 --self_pin=6 --ref_freq=2500000")

XP_CORE=${XP_CORES[$HOSTNAME]}
XP_NODE=${XP_NODES[$HOSTNAME]}
MEMLOAD_ARGS_LIST=${MEMLOAD_ARGS[$HOSTNAME]}

# For gather_results.sh
CPIS_FOLDER="cpis"
COUNTERS_FOLDER="counters"

