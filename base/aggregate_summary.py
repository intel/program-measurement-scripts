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
                df.loc[(df['Name']==row['name']) & (df['Timestamp#'].astype(str)==row['timestamp#']), 'Short Name'] = row['short_name']
                #if df['Name'][0] == row['name']:
                #    df['Short Name'] = row['short_name']

def agg_fn(df, short_names_path):
    app_name, variant, numCores, ds, prefetchers, repetitions, timestamp = df.name

    from_name_timestamps = [list(df[['Name','Timestamp#']].itertuples(index=False, name=None))]

    out_df = pd.DataFrame({'Name':[app_name], 'Short Name': [app_name], \
        'Variant': [variant], 'Num. Cores': [numCores], 'DataSet/Size': [ds], \
            'prefetchers': [prefetchers], 'Repetitions': [repetitions], 'Timestamp#': [timestamp], \
            'From Name/Timestamp#': [from_name_timestamps]})
    getShortName(out_df, short_names_path)

    keyMetrics = list(out_df.columns)
    # totalAppTime useful for many computations below
    totalAppTime = np.sum(df['AppTime (s)'])

    # Calculate potential speedups
    speedupMetrics = ['Speedup[Vec]', 'Speedup[DL1]', 'Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]' ] 
    for metric in speedupMetrics:
        try:
            out_df[metric] = totalAppTime / (np.sum(df['AppTime (s)'] / df[metric]))
        except:
            pass

    # Calculate sum metrics 
    sumMetrics = ['O=Inst. Count (GI)', '%Coverage', 'AppTime (s)', 'Total PKG Energy (J)', 
                  'Total DRAM Energy (J)', 'Total PKG+DRAM Energy (J)']
    for metric in sumMetrics:
        try:
            out_df[metric] = np.sum(df[metric])
        except:
            pass

    # Calculate time weighted metrics like rate metrics
    # Note: for % metrics, they will be approximated by time weight manner although 
    # it will be more preicse, say for %Ops[..], we should use operation count weight
    timeWeightedMetrics = ['C=Inst. Rate (GI/s)', 'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)', \
        'L1 Rate (GB/s)', 'L2 Rate (GB/s)',	'L3 Rate (GB/s)', 'RAM Rate (GB/s)', \
            'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
            '%Ops[Vec]', '%Inst[Vec]', '%Ops[FMA]', '%Inst[FMA]', '%Ops[DIV]', '%Inst[DIV]', \
                '%Ops[SQRT]', '%Inst[SQRT]', '%Ops[RSQRT]', '%Inst[RSQRT]', '%Ops[RCP]', '%Inst[RCP]', \
                    'Total PKG Power (W)', 'Total DRAM Power (W)', 'Total PKG+DRAM Power (W)', 'Time (s)']
    for metric in timeWeightedMetrics:
        #out_df[metric] = np.dot(df['%Coverage'], df[metric])
        # FIX: Could just divide above dot product by total %Coverage but use a cleaner formula directly from AppTime
        try:
            out_df[metric] = np.dot(df['AppTime (s)'], df[metric]) / totalAppTime
        except:
            pass
    
    # For energy derived, go ahead to compute using aggregated metrics
    num_ops = out_df['O=Inst. Count (GI)']
    ops_per_sec = out_df['C=Inst. Rate (GI/s)'] 
    for kind in ['PKG', 'DRAM', 'PKG+DRAM']:
        try:
            energy = out_df['Total {} Energy (J)'.format(kind)]
            calculate_energy_derived_metrics(out_df, kind, energy, num_ops, ops_per_sec)
        except:
            pass

    # Finally compute VecType which is the most complicated field to aggregate due to the need to parse strings
    # First reconstruct the sc, xmm, ymm, zmm metrics
    # more precise to just compute scPercent from other vector percentage (see below)
    # scPercent = parseVecType(df['VecType[Ops]'], 'SC')
    xmmPercent = parseVecType(df['VecType[Ops]'], 'XMM')
    ymmPercent = parseVecType(df['VecType[Ops]'], 'YMM')
    zmmPercent = parseVecType(df['VecType[Ops]'], 'ZMM')
    # Aggregate them 
    # Don't bother to compute scPercent because coverage may not sum to 1
    # Just compute aggregated xmm, ymm, zmm percentage and assume the rest as sc
    #scPercent = np.dot(df['%Coverage'], scPercent)
    xmmPercent = np.dot(df['AppTime (s)'], xmmPercent)/totalAppTime
    ymmPercent = np.dot(df['AppTime (s)'], ymmPercent)/totalAppTime
    zmmPercent = np.dot(df['AppTime (s)'], zmmPercent)/totalAppTime
    scPercent = 1 - (xmmPercent + ymmPercent + zmmPercent)

    out_df['VecType[Ops]']=vector_ext_str(zip(['SC', 'XMM', 'YMM', 'ZMM'],[scPercent, xmmPercent, ymmPercent, zmmPercent]))

    excludedMetrics = ['Source Name', 'AppName', 'codelet_name', 'LoopId', 'SrcInfo', 'AppNameWithSrcInfo']
    # Caclulate aggregate memlevel
    node_list = ['L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)']
    metric_to_memlevel = lambda v: re.sub(r" Rate \(.*\)", "", v)
    add_mem_max_level_columns(out_df, node_list, 'MaxMem Rate (GB/s)', metric_to_memlevel)
    # For the rest, compute time weighted average
    remainingMetrics = [x for x in df.columns if x not in list(out_df.columns) + excludedMetrics]
    for metric in remainingMetrics:
        try:
            out_df[metric] = np.dot(df['AppTime (s)'], df[metric]) / totalAppTime
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
        srcNameNullMask = df['Source Name'].isnull()
#        df.loc[srcNameNullMask]['AppNameWithSrcInfo'] = df['AppNameWithSrcInfo'] +': '+df['Source Name']
        df.loc[~srcNameNullMask, 'AppNameWithSrcInfo'] = \
            df.loc[~srcNameNullMask, 'AppNameWithSrcInfo'] + ': ' + df.loc[~srcNameNullMask, 'Source Name']
        newNameColumn = 'AppNameWithSrcInfo'
    # Need to fix datasize being nan's because groupby does not work
    dsMask = pd.isnull(df['DataSet/Size'])
    df.loc[dsMask, 'DataSet/Size'] = 'unknown'
    grouped = df.groupby([newNameColumn, 'Variant', 'Num. Cores', 'DataSet/Size', 'prefetchers', 'Repetitions', 'Timestamp#'])
    aggregated = grouped.apply(agg_fn, short_names_path=name_file)
    # Flatten the Multiindex
    aggregated.reset_index(drop=True, inplace=True)
    aggregated_mapping_df = pd.DataFrame()
    if not mapping_df.empty:
        # Only select mapping with nodes in current summary data
        mapping_df = pd.merge(mapping_df, df[['Name', 'Timestamp#']], left_on=['Before Name', 'Before Timestamp'], right_on=['Name', 'Timestamp#'], how='inner')
        mapping_df = pd.merge(mapping_df, df[['Name', 'Timestamp#']], left_on=['After Name', 'After Timestamp'], right_on=['Name', 'Timestamp#'], how='inner')
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
