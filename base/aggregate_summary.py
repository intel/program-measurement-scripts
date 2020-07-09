#!/usr/bin/python3
import sys
import numpy as np
import pandas as pd
import csv, re
import os
from os.path import expanduser

from argparse import ArgumentParser
from capelib import calculate_energy_derived_metrics
from capelib import vector_ext_str

# Try to extract the data from text
# which is of the format vecType1=x;vecType2=y etc
def parseVecType(text, vecType):
    # Break the strings into three parts following the pattern (<vecType>=)(<value>)(%...)
    # And extract the <value> part.
    expanded = text.str.extract(r"(?P<prefix>{}=)(?P<value>\d*\.?\d*)(?P<suffix>%.*)".format(vecType), expand=True)
    return pd.to_numeric(expanded['value']).fillna(0)/100

def getShortName(df):
    short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'
    if os.path.isfile(short_names_path):
        with open(short_names_path, 'r', encoding='utf-8-sig') as infile:
            rows = list(csv.DictReader(infile, delimiter=','))
            for row in rows:
                if df['Name'][0] == row['name']:
                    df['Short Name'] = row['short_name']

def agg_fn(df):
    app_name, variant, numCores, ds, prefetchers, repetitions, Color, Version = df.name

    out_df = pd.DataFrame({'Name':[app_name], 'Short Name': [app_name], \
        'Variant': [variant], 'Num. Cores': [numCores], 'DataSet/Size': [ds], \
            'prefetchers': [prefetchers], 'Repetitions': [repetitions], 'color': [Color], 'version' : [Version]})

    getShortName(out_df)

    # Calculate potential speedups
    for metric in ['Vec', 'DL1']:
        out_df[metric] = (np.sum(df['AppTime (s)'])) / (np.sum(df['AppTime (s)'] / df[metric]))

    # Calculate sum metrics 
    for metric in ['O=Inst. Count (GI)', '%Coverage', 'AppTime (s)', \
        'Total PKG Energy (J)', 'Total DRAM Energy (J)', 'Total PKG+DRAM Energy (J)']:
        out_df[metric] = np.sum(df[metric])

    # Calculate time weighted metrics like rate metrics
    # Note: for % metrics, they will be approximated by time weight manner although 
    # it will be more preicse, say for %Ops[..], we should use operation count weight
    for metric in ['C=Inst. Rate (GI/s)', 'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)', \
        'L1 Rate (GB/s)', 'L2 Rate (GB/s)',	'L3 Rate (GB/s)', 'RAM Rate (GB/s)', \
            'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
            '%Ops[Vec]', '%Inst[Vec]', '%Ops[FMA]', '%Inst[FMA]', '%Ops[DIV]', '%Inst[DIV]', \
                '%Ops[SQRT]', '%Inst[SQRT]', '%Ops[RSQRT]', '%Inst[RSQRT]', '%Ops[RCP]', '%Inst[RCP]', \
                    'Total PKG Power (W)', 'Total DRAM Power (W)', 'Total PKG+DRAM Power (W)']:
        out_df[metric] = np.dot(df['%Coverage'], df[metric])
    
    # For energy derived, go ahead to compute using aggregated metrics
    num_ops = out_df['O=Inst. Count (GI)']
    ops_per_sec = out_df['C=Inst. Rate (GI/s)'] 
    for kind in ['PKG', 'DRAM', 'PKG+DRAM']:
        energy = out_df['Total {} Energy (J)'.format(kind)]
        calculate_energy_derived_metrics(out_df, kind, energy, num_ops, ops_per_sec)
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
    xmmPercent = np.dot(df['%Coverage'], xmmPercent)
    ymmPercent = np.dot(df['%Coverage'], ymmPercent)
    zmmPercent = np.dot(df['%Coverage'], zmmPercent)
    scPercent = 1 - (xmmPercent + ymmPercent + zmmPercent)

    out_df['VecType[Ops]']=vector_ext_str(zip(['SC', 'XMM', 'YMM', 'ZMM'],[scPercent, xmmPercent, ymmPercent, zmmPercent]))

    return out_df

def aggregate_runs(inputfiles, outputfile):
    print('Inputfiles: ', inputfiles, file=sys.stderr)
    print('Outputfile: ', outputfile, file=sys.stderr)
    
    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        print(inputfile, file=sys.stderr)
        cur_df = pd.read_csv(inputfile, delimiter=',')
        df = df.append(cur_df, ignore_index=True)
    df[['AppName', 'codelet_name']] = df.Name.str.split(pat=": ", expand=True)
    # Need to fix datasize being nan's because groupby does not work
    dsMask = np.isnan(df['DataSet/Size'])
    df.loc[dsMask, 'DataSet/Size'] = 'unknown'
    grouped = df.groupby(['AppName', 'Variant', 'Num. Cores', 'DataSet/Size', 'prefetchers', 'Repetitions', 'Color', 'Version'])
    aggregated = grouped.apply(agg_fn)
    aggregated.to_csv(outputfile, index=False)

if __name__ == '__main__':
    parser = ArgumentParser(description='Aggregate summary sheets into app level.')
    parser.add_argument('-i', nargs='+', help='the input csv file(s)', required=True, dest='in_files')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    args = parser.parse_args()
    aggregate_runs(args.in_files, args.out_file)