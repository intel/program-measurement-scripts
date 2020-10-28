#!/usr/bin/python3
import sys
import numpy as np
import pandas as pd
import csv, re
import os

from argparse import ArgumentParser
from capelib import calculate_energy_derived_metrics
from capelib import vector_ext_str
from capelib import add_mem_max_level_columns
from capelib import compute_speedup
from compute_transitions import aggregate_transitions
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

# Try to extract the data from text
# which is of the format vecType1=x;vecType2=y etc
def parseVecType(text, vecType):
    # Break the strings into three parts following the pattern (<vecType>=)(<value>)(%...)
    # And extract the <value> part.
    expanded = text.str.extract(r"(?P<prefix>{}=)(?P<value>\d*\.?\d*)(?P<suffix>%.*)".format(vecType), expand=True)
    return pd.to_numeric(expanded['value']).fillna(0)/100

def getShortName(df, short_names_path):
    if short_names_path is not None and os.path.isfile(short_names_path):
        with open(short_names_path, 'r', encoding='utf-8-sig') as infile:
            rows = list(csv.DictReader(infile, delimiter=','))
            for row in rows:
                df.loc[(df[NAME]==row[NAME]) & (df[TIMESTAMP].astype(str)==row[TIMESTAMP]), SHORT_NAME] = row[SHORT_NAME]
                #if df[NAME][0] == row[NAME]:
                #    df[SHORT_NAME] = row['short_name']

def agg_fn(df, short_names_path):
    app_name, variant, numCores, ds, prefetchers, timestamp = df.name

    from_name_timestamps = [list(df[[NAME,TIMESTAMP]].itertuples(index=False, name=None))]

    out_df = pd.DataFrame({NAME:[app_name], SHORT_NAME: [app_name], \
        VARIANT: [variant], NUM_CORES: [numCores], DATA_SET: [ds], \
            PREFETCHERS: [prefetchers], TIMESTAMP: [timestamp], \
            'From Name/Timestamp#': [from_name_timestamps]})
    getShortName(out_df, short_names_path)

    keyMetrics = list(out_df.columns)
    # totalAppTime useful for many computations below
    totalAppTime = np.sum(df[TIME_APP_S])

    # Calculate potential speedups
    speedupMetrics = [SPEEDUP_VEC, SPEEDUP_DL1, SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S ] 
    for metric in speedupMetrics:
        try:
            out_df[metric] = totalAppTime / (np.sum(df[TIME_APP_S] / df[metric]))
        except:
            pass

    # Calculate sum metrics 
    sumMetrics = [COUNT_INSTS_GI, COVERAGE_PCT, TIME_APP_S, E_PKG_J, 
                  E_DRAM_J, E_PKGDRAM_J]
    for metric in sumMetrics:
        try:
            out_df[metric] = np.sum(df[metric])
        except:
            pass

    # Calculate time weighted metrics like rate metrics
    # Note: for % metrics, they will be approximated by time weight manner although 
    # it will be more preicse, say for %Ops[..], we should use operation count weight
    timeWeightedMetrics = [RATE_INST_GI_P_S, RATE_FP_GFLOP_P_S, RATE_INT_GIOP_P_S, \
        RATE_L1_GB_P_S, RATE_L2_GB_P_S,	RATE_L3_GB_P_S, RATE_RAM_GB_P_S, \
            RATE_REG_ADDR_GB_P_S, RATE_REG_DATA_GB_P_S, RATE_REG_SIMD_GB_P_S, RATE_REG_GB_P_S,
            COUNT_OPS_VEC_PCT, COUNT_INSTS_VEC_PCT, COUNT_OPS_FMA_PCT, COUNT_INSTS_FMA_PCT, COUNT_OPS_DIV_PCT, COUNT_INSTS_DIV_PCT, \
                COUNT_OPS_SQRT_PCT, COUNT_INSTS_SQRT_PCT, COUNT_OPS_RSQRT_PCT, COUNT_INSTS_RSQRT_PCT, COUNT_OPS_RCP_PCT, COUNT_INSTS_RCP_PCT, \
                    P_PKG_W, P_DRAM_W, P_PKGDRAM_W, TIME_LOOP_S, ARRAY_EFFICIENCY_PCT]
    for metric in timeWeightedMetrics:
        #out_df[metric] = np.dot(df[COVERAGE_PCT], df[metric])
        # FIX: Could just divide above dot product by total %Coverage but use a cleaner formula directly from AppTime
        try:
            out_df[metric] = np.dot(df[TIME_APP_S], df[metric]) / totalAppTime
        except:
            pass
    
    # For energy derived, go ahead to compute using aggregated metrics
    num_ops = out_df[COUNT_INSTS_GI]
    ops_per_sec = out_df[RATE_INST_GI_P_S] 
    for kind in ['PKG', 'DRAM', 'PKG+DRAM']:
        try:
            energy = out_df['Total {} Energy (J)'.format(kind)]
            calculate_energy_derived_metrics(out_df, kind, energy, num_ops, ops_per_sec)
        except:
            pass

    # Finally compute VecType which is the most complicated field to aggregate due to the need to parse strings
    # First reconstruct the sc, xmm, ymm, zmm metrics
    # more precise to just compute scPercent from other vector percentage (see below)
    # scPercent = parseVecType(df[COUNT_VEC_TYPE_OPS_PCT], 'SC')
    xmmPercent = parseVecType(df[COUNT_VEC_TYPE_OPS_PCT], 'XMM')
    ymmPercent = parseVecType(df[COUNT_VEC_TYPE_OPS_PCT], 'YMM')
    zmmPercent = parseVecType(df[COUNT_VEC_TYPE_OPS_PCT], 'ZMM')
    # Aggregate them 
    # Don't bother to compute scPercent because coverage may not sum to 1
    # Just compute aggregated xmm, ymm, zmm percentage and assume the rest as sc
    #scPercent = np.dot(df[COVERAGE_PCT], scPercent)
    xmmPercent = np.dot(df[TIME_APP_S], xmmPercent)/totalAppTime
    ymmPercent = np.dot(df[TIME_APP_S], ymmPercent)/totalAppTime
    zmmPercent = np.dot(df[TIME_APP_S], zmmPercent)/totalAppTime
    scPercent = 1 - (xmmPercent + ymmPercent + zmmPercent)

    out_df[COUNT_VEC_TYPE_OPS_PCT]=vector_ext_str(zip(['SC', 'XMM', 'YMM', 'ZMM'],[scPercent, xmmPercent, ymmPercent, zmmPercent]))

    excludedMetrics = [SRC_NAME, 'AppName', 'codelet_name', 'LoopId', 'SrcInfo', 'AppNameWithSrcInfo']
    # Caclulate aggregate MEM_LEVEL
    node_list = [RATE_L1_GB_P_S, RATE_L2_GB_P_S, RATE_L3_GB_P_S, RATE_RAM_GB_P_S]
    metric_to_memlevel = lambda v: re.sub(r" Rate \(.*\)", "", v)
    add_mem_max_level_columns(out_df, node_list, RATE_MAXMEM_GB_P_S, metric_to_memlevel)
    # For the rest, compute time weighted average
    remainingMetrics = [x for x in df.columns if x not in list(out_df.columns) + excludedMetrics]
    for metric in remainingMetrics:
        try:
            out_df[metric] = np.dot(df[TIME_APP_S], df[metric]) / totalAppTime
        except:
            pass

    return out_df

def aggregate_runs_df(df, level="app", name_file=None, mapping_df = pd.DataFrame()):
    df[['AppName', 'codelet_name']] = df.Name.str.split(pat=": ", expand=True)
    if level == "app":
        newNameColumn='AppName'
    else:
        # First group is optional (so names generated by CapeScripts will just get into src_info, leaving loop_id None)
        splitInfo = df['codelet_name'].str.extract(r'((?P<LoopId>\d+)_)?(?P<SrcInfo>.+)', expand=True)
        # Need to store output into splitInfo first because optional group introduced an extra column
        df[['LoopId', 'SrcInfo']] = splitInfo[['LoopId', 'SrcInfo']]
        df['AppNameWithSrcInfo'] = df['AppName']+': ' + df['SrcInfo']
        srcNameNullMask = df[SRC_NAME].isnull()
#        df.loc[srcNameNullMask]['AppNameWithSrcInfo'] = df['AppNameWithSrcInfo'] +': '+df[SRC_NAME]
        df.loc[~srcNameNullMask, 'AppNameWithSrcInfo'] = \
            df.loc[~srcNameNullMask, 'AppNameWithSrcInfo'] + ': ' + df.loc[~srcNameNullMask, SRC_NAME]
        newNameColumn = 'AppNameWithSrcInfo'
    # Need to fix datasize being nan's because groupby does not work
    dsMask = pd.isnull(df[DATA_SET])
    df.loc[dsMask, DATA_SET] = 'unknown'
    grouped = df.groupby([newNameColumn, VARIANT, NUM_CORES, DATA_SET, PREFETCHERS, TIMESTAMP])
    aggregated = grouped.apply(agg_fn, short_names_path=name_file)
    # Flatten the Multiindex
    aggregated.reset_index(drop=True, inplace=True)
    aggregated_mapping_df = pd.DataFrame()
    if not mapping_df.empty:
        # Only select mapping with nodes in current summary data
        mapping_df = pd.merge(mapping_df, df[[NAME, TIMESTAMP]], left_on=['Before Name', 'Before Timestamp'], right_on=[NAME, TIMESTAMP], how='inner')
        mapping_df = pd.merge(mapping_df, df[[NAME, TIMESTAMP]], left_on=['After Name', 'After Timestamp'], right_on=[NAME, TIMESTAMP], how='inner')
        aggregated_mapping_df = aggregate_transitions(mapping_df, aggregated) 
        aggregated_mapping_df = compute_speedup(aggregated, aggregated_mapping_df)
    return aggregated, aggregated_mapping_df

def aggregate_runs(inputfiles, outputfile, level="app", name_file=None, mapping_file=None):
    print('Inputfiles: ', inputfiles, file=sys.stderr)
    print('Outputfile: ', outputfile, file=sys.stderr)
    print('Short name file: ', name_file, file=sys.stderr)
    print('Mapping file: ', mapping_file, file=sys.stderr)

    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        print(inputfile, file=sys.stderr)
        cur_df = pd.read_csv(inputfile, delimiter=',')
        df = df.append(cur_df, ignore_index=True)

    mapping_df = pd.read_csv(mapping_file, delimiter=',') if mapping_file is not None else pd.DataFrame()

    aggregated, aggregated_mapping = aggregate_runs_df(df, level=level, name_file=name_file, mapping_df = mapping_df)
    aggregated.to_csv(outputfile, index=False)

    if not aggregated_mapping.empty:
        root, ext = os.path.splitext(outputfile)
        dirname = os.path.dirname(root)
        basename = os.path.basename(root)
        aggregated_mapping.to_csv(os.path.join(dirname, basename+'.mapping'+ext), index=False)


if __name__ == '__main__':
    parser = ArgumentParser(description='Aggregate summary sheets into source or app level.')
    parser.add_argument('-i', nargs='+', help='the input csv file(s)', required=True, dest='in_files')
    parser.add_argument('-l', nargs='?', default='app', help='aggregation level (default app can change to src)', \
        choices=['app', 'src'], dest='level')
    parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    parser.add_argument('-m', nargs='?', help='the input mapping csv file', dest='mapping_file')
    args = parser.parse_args()
    aggregate_runs(args.in_files, args.out_file, args.level, args.name_file, args.mapping_file )
