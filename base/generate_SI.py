#!/usr/bin/env python
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
import copy
from capeplot import CapePlot

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text
from matplotlib.patches import Rectangle
import statistics
from matplotlib.legend import Legend
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class SiPlot(CapePlot):
    pass


BASIC_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]', 'VR [GB/s]', 'RAM [GB/s]'}
MEM_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
SCALAR_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'RS'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FE'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR'}
DEFAULT_CHOSEN_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]'}

# For node using derived metrics (e.g. FE), make sure the depended metrics are computed
capacity_formula= {
    'L1 [GB/s]': (lambda df : df[RATE_L1_GB_P_S]/8),
    'L2 [GB/s]': (lambda df : df[RATE_L2_GB_P_S]/8),
    'L3 [GB/s]': (lambda df : df[RATE_L3_GB_P_S]/8),
    'FLOP [GFlop/s]': (lambda df : df[RATE_FP_GFLOP_P_S]),
    'VR [GB/s]': (lambda df : df[RATE_REG_SIMD_GB_P_S]/24),
    'RAM [GB/s]': (lambda df : df[RATE_RAM_GB_P_S]/8),
    'FE': (lambda df : df[STALL_FE_PCT]*(df['C_max [GB/s]'])),
    'SB': (lambda df : df[STALL_SB_PCT]*(df['C_max [GB/s]'])),
    'LM': (lambda df : df[STALL_LM_PCT]*(df['C_max [GB/s]'])),
    'RS': (lambda df : df[STALL_RS_PCT]*(df['C_max [GB/s]'])),
    'CU': (lambda df : (df[STALL_FE_PCT]*df['C_scalar'] + df[STALL_LB_PCT]*df['C_scalar'] + df[STALL_SB_PCT]*df['C_scalar'] + df[STALL_LM_PCT]*df['C_scalar']))
    }

# For node using derived metrics (e.g. FE), make sure the depended metrics are computed

def concat_ordered_columns(frames):
    columns_ordered = []
    for frame in frames:
        columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
    final_df = pd.concat(frames)
    return final_df[columns_ordered]

def parse_ip_df(inputfile, outputfile, norm, title, chosen_node_set, rdf, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
    if not mappings.empty:
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
        'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
    # Computation to get SI in the cluster df and then combine with the summary df
    df = pd.read_csv(inputfile)
    target_df = pd.DataFrame()
    target_df[[NAME, SHORT_NAME, VARIANT]] = df[[NAME, SHORT_NAME, VARIANT]]
    compute_capacity(df, norm, chosen_node_set, target_df)
    compute_saturation(df, chosen_node_set, target_df)
    compute_intensity(df, chosen_node_set, target_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        target_df['C_{}'.format(node)]=formula(df)
    target_df['k'] = df['Saturation'] * df['Intensity']
    target_df['speedup'] = df['speedup']
    df['SI']=df['Saturation'] * df['Intensity'] 
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
    # Only show selected variants, default is 'ORIG'
    rdf = rdf.loc[rdf[VARIANT].isin(variants)]
    l_df = df
    column_list = df.columns.tolist()
    column_list.extend([TIME_APP_S, TIMESTAMP, COVERAGE_PCT, 'Color'])
    data = pd.DataFrame(columns=column_list)
    data = data.append(rdf, ignore_index=False)[column_list]
    dfs = [l_df,data]
    full_df = concat_ordered_columns(dfs)

    return compute_and_plot('ORIG', full_df, 'SIPLOT', norm, title, chosen_node_set, target_df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale, short_names_path=short_names_path)

def parse_ip(inputfile,outputfile, norm, title, chosen_node_set, rfile):
#    inputfile="/tmp/input.csv"
    rdf = pd.read_csv(rfile)
    parse_ip_df(inputfile, outputfile, norm, title, chosen_node_set, rdf)

def compute_capacity(df, norm, chosen_node_set, out_df):
    print("The node list are as follows :")
    print(chosen_node_set)
    chosen_basic_node_set = BASIC_NODE_SET & chosen_node_set
    chosen_buffer_node_set = BUFFER_NODE_SET & chosen_node_set
    for node in chosen_basic_node_set:
        print ("The current node : ", node)
        formula=capacity_formula[node]
        df['C_{}'.format(node)]=formula(df)

    if norm == 'row':
        print ("<=====Running Row Norm======>")
        df['C_max [GB/s]']=df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1)
    else:
        print ("<=====Running Matrix Norm======>")
        df['C_max [GB/s]']=max(df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1))
    print ("<=====compute_capacity======>")

    if norm == 'row':
        print ("<=====Running Row Norm======>")
        df['C_scalar']=df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1)
    else:
        print ("<=====Running Matrix Norm======>")
        df['C_scalar']=max(df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1))
    print ("<=====compute_cu_scalar======>")
    out_df['C_scalar'] = df['C_scalar']
    for node in chosen_buffer_node_set:
        formula=capacity_formula[node]
        df['C_{}'.format(node)]=formula(df)
    # Compute memory level 
    chosen_mem_node_set = MEM_NODE_SET & chosen_node_set
    # Below will get the C_* name with max value
    df[MEM_LEVEL]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
    # Remove the first two characters which is 'C_'
    df[MEM_LEVEL] = df[MEM_LEVEL].apply((lambda v: v[2:]))
    # Drop the unit
    df[MEM_LEVEL] = df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)

def compute_saturation(df, chosen_node_set, out_df):
    nodeMax=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].max(axis=0)
    nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
    print ("<=====compute_saturation======>")
    for node in chosen_node_set:
        df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
    df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)
    out_df['Saturation'] = df['Saturation']


def compute_intensity(df, chosen_node_set, out_df):
    node_cnt = len(chosen_node_set)
    csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
    df['Intensity']=node_cnt*df['C_max [GB/s]'] / csum
    out_df['Intensity'] = df['Intensity']

def compute_color_labels(df, short_names_path=''):
    color_labels = []
    for color in df['Color'].unique():
        colorDf = df.loc[df['Color']==color].reset_index()
        codelet = colorDf[NAME][0]
        timestamp = colorDf[TIMESTAMP][0]
        app_name = codelet.split(':')[0]
        if short_names_path:
            short_names = pd.read_csv(short_names_path)
            row = short_names.loc[(short_names[NAME]==app_name) & (short_names[TIMESTAMP]==timestamp)].reset_index(drop=True)
            if not row.empty: app_name = row[SHORT_NAME][0]
        color_labels.append((app_name, color))
    return color_labels

def compute_and_plot(variant, df, outputfile_prefix, norm, title, chosen_node_set, tdf, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
    out_df = pd.DataFrame()
    out_df[[NAME, SHORT_NAME, VARIANT]] = df[[NAME, SHORT_NAME, VARIANT]]
    compute_capacity(df, norm, chosen_node_set, out_df)
    compute_saturation(df, chosen_node_set, out_df)
    compute_intensity(df, chosen_node_set, out_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        out_df['C_{}'.format(node)]=formula(df)
    out_df['k'] = df['Saturation'] * df['Intensity']
    out_df['speedup'] = df['speedup']
    indices = df[SHORT_NAME]
    y = df['Saturation']
    z = df['Intensity']
    df['SI']=df['Saturation'] * df['Intensity'] 
    k = df['SI']
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup    
    k_avg = k.mean()
    today = datetime.date.today()
    f_outputfile='Final_{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    fig = None
    l_df = None
    # Used to create a legend of file names to color for multiple plots
    l_df = df.dropna(subset=['Color']) # User selected data will have color column while FE_tier1.csv will not
    color_labels = compute_color_labels(l_df, short_names_path)
    fig, textData = plot_data("{} \n n = {}{} \n".format(title, len(chosen_node_set), 
                        str(sorted(list(chosen_node_set)))),
                        f_outputfile, l_df, list(z), list(y), len(chosen_node_set), tdf, k_avg, color_labels, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale)
    return l_df, fig, textData

def draw_contours(ax, maxx, ns):
    npoints=40

    ctx=np.linspace(0, maxx, npoints+1)
    ctx=np.delete(ctx, 0) # Drop first element of 0

    lines=[]
    for n in ns:
        cty=n/ctx
        lines.append(ax.plot(ctx, cty, label='k={}'.format(n))[0])
    return lines

# Set filename to [] for GUI output    
def plot_data(title, filename, orig_df, xs, ys, Ns, target_df, k_average, color_labels=None, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear'):
    if filtering:
        orig_df = orig_df.loc[(orig_df[filter_data[0]] >= filter_data[1]) & (orig_df[filter_data[0]] <= filter_data[2])]

    fig, ax = plt.subplots()

    xmax=max(xs)*1.2
    ymax=max(ys)*1.2  
    xmin=min(xs)
    ymin=min(ys)

    # Set specified axis scales
    if scale == 'linear' or scale == 'linearlinear':
        ax.set_xlim((0, xmax))
        ax.set_ylim((0, ymax))
    elif scale == 'log' or scale == 'loglog':
        plt.xscale("log")
        plt.yscale("log")
        ax.set_xlim((xmin, xmax))
        ax.set_ylim((ymin, ymax))
    elif scale == 'loglinear':
        plt.xscale("log")
        ax.set_xlim((xmin, xmax))
        ax.set_ylim((0, ymax))
    elif scale == 'linearlog':
        plt.yscale("log")
        ax.set_xlim((0, xmax))
        ax.set_ylim((ymin, ymax))

    print("Entering plot_data_orig_point")

    orig_codelet_sat = orig_df['Saturation'].values.tolist()
    orig_codelet_int = orig_df['Intensity'].values.tolist()
    DATA = tuple(zip(orig_codelet_int,orig_codelet_sat))

    orig_codelet_index = orig_df[SHORT_NAME].values.tolist()
    orig_codelet_variant = orig_df[VARIANT].values.tolist()
    orig_codelet_memlevel = orig_df[MEM_LEVEL].values.tolist()
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2  
    ax.set_xlim((0, xmax))
    ax.set_ylim((0, ymax))

    (x, y) = zip(*DATA)
    print('Data length: ', len(DATA))

    # Draw contours
    ns = [1,2,(Ns-1), Ns, (Ns+1),(Ns+2)]
    ctxs = draw_contours(ax, xmax, ns)

    # Plot data points
    markers = []
    orig_df.reset_index(drop=True, inplace=True)
    for i in range(len(DATA)):
        markers.extend(ax.plot(x[i], y[i], marker='o', color=orig_df['Color'][i][0], label=orig_df[NAME][i]+str(orig_df[TIMESTAMP][i]), linestyle='', alpha=1))

    plt.rcParams.update({'font.size': 7})
    mytext= [str('({0}, {1}, {2})'.format( orig_codelet_index[i], orig_codelet_variant[i], orig_codelet_memlevel[i]))  for i in range(len(DATA))]
    texts = [plt.text(x[i], y[i], mytext[i], alpha=1) for i in range(len(DATA))]

    # Create a Rectangle patch
    print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
    rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])),
            (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
    ax.add_patch(rect)
    ax.set(xlabel="Intensity", ylabel="Saturation")
    ax.set_title(title, pad=40)
    centerx = min(target_df['Intensity'])
    centery = min(target_df['Saturation'])
    # Legend
    patches = []
    if color_labels and len(color_labels) >= 2:
        for color_label in color_labels:
            patch = mpatches.Patch(label=color_label[0], color=color_label[1])
            patches.append(patch)
    patches.extend(ctxs)
    legend = ax.legend(loc="lower left",ncol=6, bbox_to_anchor=(0.,1.02,1.,.102),title="I$_C$$_G$ = 1.59, " + "S$_C$$_G$ = 4.06, " + "k$_C$$_G$ = 6.48, Label = (name, variant, memlevel)", \
        mode='expand', borderaxespad=0., handles=patches)
    
    # Arrows between multiple runs
    name_mapping = dict()
    mymappings = []
    if not mappings.empty:
        for i in mappings.index:
            name_mapping[mappings['before_name'][i]+str(mappings['before_timestamp#'][i])] = []
            name_mapping[mappings['after_name'][i]+str(mappings['after_timestamp#'][i])] = []
        for index in mappings.index:
            before_row = orig_df.loc[(orig_df[NAME]==mappings['before_name'][index]) & (orig_df[TIMESTAMP]==mappings['before_timestamp#'][index])].reset_index(drop=True)
            after_row = orig_df.loc[(orig_df[NAME]==mappings['after_name'][index]) & (orig_df[TIMESTAMP]==mappings['after_timestamp#'][index])].reset_index(drop=True)
            if not before_row.empty and not after_row.empty:
                x_axis = 'Intensity'
                y_axis = 'Saturation'
                xyA = (before_row[x_axis][0], before_row[y_axis][0])
                xyB = (after_row[x_axis][0], after_row[y_axis][0])
                # Check which way to curve the arrow to avoid going out of the axes
                if (xmax - xyB[0] > xyB[0] and xmax - xyA[0] > xyA[0] and xyA[1] < xyB[1]) or \
                    (ymax - xyB[1] > xyB[1] and ymax - xyA[1] > xyA[1] and xyA[0] > xyB[0]) or \
                    (ymax - xyB[1] < xyB[1] and ymax - xyA[1] < xyA[1] and xyA[0] < xyB[0]) or \
                    (xmax - xyB[0] < xyB[0] and xmax - xyA[0] < xyA[0] and xyA[1] > xyB[1]):
                    con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                        connectionstyle='arc3,rad=0.3', alpha=1)
                else:
                    con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                        connectionstyle='arc3,rad=-0.3', alpha=1)
                ax.add_artist(con)
                name_mapping[before_row[NAME][0] + str(before_row[TIMESTAMP][0])].append(con)
                name_mapping[after_row[NAME][0] + str(after_row[TIMESTAMP][0])].append(con)
                mymappings.append(con)
    plt.tight_layout()

    names = [name + timestamp for name,timestamp in zip(orig_df[NAME], orig_df[TIMESTAMP].astype(str))]
    plotData = {
        'xs' : xs,
        'ys' : ys,
        'mytext' : mytext,
        'orig_mytext' : copy.deepcopy(mytext),
        'ax' : ax,
        'legend' : legend,
        'orig_legend' : legend.get_title().get_text(),
        'title' : title,
        'texts' : texts,
        'markers' : markers,
        'names' : names,
        'timestamps' : orig_df[TIMESTAMP].values.tolist(),
        'marker:text' : dict(zip(markers,texts)),
        'marker:name' : dict(zip(markers,names)),
        'name:marker' : dict(zip(names, markers)),
        'name:text' : dict(zip(names, texts)),
        'text:arrow' : {},
        'text:name' : dict(zip(texts, names)),
        'name:mapping' : name_mapping,
        'mappings' : mymappings
    }

    if filename:
        pass
        #plt.savefig(filename)
    else:
        plt.show()

    return fig, plotData

def usage(reason):
    error_code = 0
    if reason:
        print ('\nERROR: {}!\n'.format(reason))
        error_code = 2
    print ('Usage:\n  generate_SI.py  -i <inputfile> -o <outputfile prefix> -n norm (row,matrix) -l <nodes> (optionally)>')
    print ('Example:\n  generate_SI.py  -i input.csv -o out.csv -n row -l L1,L2,L3,FLOP,VR')
    sys.exit(error_code)
    
def main(argv):
    #if len(argv) != 8 and len(argv) != 6 and len(argv) != 4 and len(argv) != 2 and len(argv) != 1:
    #    usage('Wrong number of arguments')
    inputfile = []
    rfile = []
    outputfile = []
    node_list = []
    norm = 'row'
    title=""
    chosen_node_set = DEFAULT_CHOSEN_NODE_SET
    try:
        opts, args = getopt.getopt(argv, "hi:o:n:l:r:")
        print (opts)
        print (args)
    except getopt.GetoptError:
        usage('Wrong argument opts(s)')
    if len(args) != 0:
        usage('Wrong argument(s)')
    for opt, arg in opts:
        if opt == '-h':
            usage([])
        elif opt == '-n':
            normobj = arg
            print (normobj)
            if normobj != 'matrix' and normobj != 'row':
                print ('norm has to be either matrix or row')
            else:
                norm = normobj
        elif opt == '-l':
            node_list = arg.split(',')
            print (node_list)
            chosen_node_set = set(node_list)
            print (chosen_node_set)
        elif opt == '-i':
            inputfile.append(arg)
            matchobj = re.search(r'(.+?)\.csv', arg)
            title = str(matchobj.group(1))
            if not matchobj:
                print ('inputfile should be a *.csv file')
                sys.exit()
        elif opt == '-r':
            rfile.append(arg)
            r_matchobj = re.search(r'(.+?)\.csv', arg)
            if not r_matchobj:
                print ('rfile should be a *.csv file')
                sys.exit()
        elif opt == '-o':
            outputfile.append(arg)
    if matchobj and len(outputfile) == 0:
        outputfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
        rfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
    print ('Inputfile: ', inputfile[0])
    #print ('Rfile: ', rfile[0])
    print ('Outputfile: ', outputfile[0])
    print ('Norm: ', norm)
    print ('Node List: ', node_list)
    parse_ip(inputfile[0],outputfile[0], norm, title.upper(), chosen_node_set, rfile[0])

if __name__ == "__main__":
    main(sys.argv[1:])