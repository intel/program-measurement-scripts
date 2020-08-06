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

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text
from matplotlib.patches import Rectangle
import statistics
from matplotlib.legend import Legend
from capelib import succinctify
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.


BASIC_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]', 'VR [GB/s]', 'RAM [GB/s]'}
#SCALAR_NODE_SET={'l1_rate_gb/s', 'l2_rate_gb/s', 'l3_rate_gb/s', 'ram_rate_gb/s'}
MEM_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
SCALAR_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'RS'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FrontEnd'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR'}
DEFAULT_CHOSEN_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
    'L1 [GB/s]': (lambda df : df['l1_rate_gb/s']/8),
    'L2 [GB/s]': (lambda df : df['l2_rate_gb/s']/8),
    'L3 [GB/s]': (lambda df : df['l3_rate_gb/s']/8),
    'FLOP [GFlop/s]': (lambda df : df['flop_rate_gflop/s']),
    'VR [GB/s]': (lambda df : df['register_simd_rate_gb/s']/24),
    'RAM [GB/s]': (lambda df : df['ram_rate_gb/s']/8),
    'FE': (lambda df : df['%frontend']*(df['C_max [GB/s]'])),
    'SB': (lambda df : df['%sb']*(df['C_max [GB/s]'])),
    'LM': (lambda df : df['%lm']*(df['C_max [GB/s]'])),
    'RS': (lambda df : df['%rs']*(df['C_max [GB/s]'])),
    'CU': (lambda df : (df['%frontend']*df['C_scalar'] + df['%lb']*df['C_scalar'] + df['%sb']*df['C_scalar'] + df['%lm']*df['C_scalar']))
    }

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed

def concat_ordered_columns(frames):
    columns_ordered = []
    for frame in frames:
        columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
    final_df = pd.concat(frames)
    return final_df[columns_ordered]

def parse_ip_df(inputfile, outputfile, norm, title, chosen_node_set, rdf, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame()):
    df = pd.read_csv(inputfile)
    grouped = df.groupby('variant')
    # Generate SI plot for each variant
    mask = df['variant'] == "ORIGG"
    #if not df.empty
    short_name=''
    target_df = pd.DataFrame()
    compute_and_plot('XFORM', df[~mask], outputfile, norm, title, chosen_node_set, target_df)
    rdf.columns = succinctify(rdf.columns)
    if not mappings.empty:
        mappings.columns = succinctify(mappings.columns)
    # Only show selected variants, default is 'ORIG'
    rdf = rdf.loc[rdf['variant'].isin(variants)]
    l_df = df
    column_list = df.columns.tolist()
    column_list.extend(['apptime_s', 'timestamp#', r'%coverage', 'color'])
    data = pd.DataFrame(columns=column_list)
    short_name = rdf['short_name']
    data = data.append(rdf, ignore_index=False)[column_list]
    #data = data.append(rdf, ignore_index=False)[df.columns.tolist()]
    dfs = [l_df,data]
    full_df = concat_ordered_columns(dfs)

    return compute_and_plot_orig('ORIG', full_df, 'SIPLOT', norm, title, chosen_node_set, target_df, short_name, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings)

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

    #print(df)
    if norm == 'row':
        print ("<=====Running Row Norm======>")
        df['C_max [GB/s]']=df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1)
    else:
        print ("<=====Running Matrix Norm======>")
        df['C_max [GB/s]']=max(df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1))
    print ("<=====compute_capacity======>")
    #print(df['C_max [GB/s]'])

    if norm == 'row':
        print ("<=====Running Row Norm======>")
        df['C_scalar']=df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1)
    else:
        print ("<=====Running Matrix Norm======>")
        df['C_scalar']=max(df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1))
    print ("<=====compute_cu_scalar======>")
    #print(df['C_scalar'])
    out_df['C_scalar'] = df['C_scalar']
    for node in chosen_buffer_node_set:
        formula=capacity_formula[node]
        df['C_{}'.format(node)]=formula(df)
    # Compute memory level 
    chosen_mem_node_set = MEM_NODE_SET & chosen_node_set
    # Below will get the C_* name with max value
    df['memlevel']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
    # Remove the first two characters which is 'C_'
    df['memlevel'] = df['memlevel'].apply((lambda v: v[2:]))
    # Drop the unit
    df['memlevel'] = df['memlevel'].str.replace(" \[.*\]","", regex=True)

def compute_saturation(df, chosen_node_set, out_df):
    nodeMax=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].max(axis=0)
    #max_list = np.array(nodeMax.values.tolist())
    #print(nodeMax)
    nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
    print ("<=====compute_saturation======>")
    #print(nodeMax)
    for node in chosen_node_set:
        df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
    df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)
    #print(df['Saturation'])
    out_df['Saturation'] = df['Saturation']


def compute_intensity(df, chosen_node_set, out_df):
    node_cnt = len(chosen_node_set)
    csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
    df['Intensity']=node_cnt*df['C_max [GB/s]'] / csum
    #print(df['Intensity'])
    out_df['Intensity'] = df['Intensity']

def compute_color_labels(df):
    color_labels = []
    for color in df['color'].unique():
        colorDf = df.loc[df['color']==color].reset_index()
        codelet = (colorDf['name'][0])
        color_labels.append((codelet.split(':')[0], color))
    return color_labels

def compute_and_plot_orig(variant, df,outputfile_prefix, norm, title, chosen_node_set, tdf, orig_name, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame()):
    out_csv = variant+ '_' + outputfile_prefix +'_export_dataframe.csv'
    #print (out_csv)
    out_df = pd.DataFrame()
    out_df[['name', 'short_name', 'variant']] = df[['name', 'short_name', 'variant']]
    compute_capacity(df, norm, chosen_node_set, out_df)
    compute_saturation(df, chosen_node_set, out_df)
    compute_intensity(df, chosen_node_set, out_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        out_df['C_{}'.format(node)]=formula(df)
    out_df['k'] = df['Saturation'] * df['Intensity']
    out_df['speedup'] = df['speedup']
    out_df.to_csv(out_csv, index = False, header=True)
    indices = df['short_name']
    y = df['Saturation']
    z = df['Intensity']
    df['SI']=df['Saturation'] * df['Intensity'] 
    k = df['SI']
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
    k_avg = k.mean()
    speedups = df['Speedup']
    floprate = df['C_FLOP [GFlop/s]']
    codelet_variant = df['variant']
    #plot_data("Saturation plot", 'saturation.png', x, y)
    #plot_data("Intensity plot", 'Intensity.png', x, z)
#    outputfile='SI.png'
    today = datetime.date.today()
    outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    f_outputfile='Final_{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    tdf.to_csv('target_debug.csv', index = False, header=True)

    plot_data_orig("{} \n n = {}{} \n".format(title, len(chosen_node_set), 
                        str(sorted(list(chosen_node_set)))),
                        outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set), tdf, k_avg)
    fig = None
    l_df = None
    # Used to create a legend of file names to color for multiple plots
    if not orig_name.empty:
        l_df = df.dropna(subset=['color']) # User selected data will have color column while FE_tier1.csv will not
        #l_df = df.loc[df['short_name'].isin(orig_name)]
        color_labels = compute_color_labels(l_df)
        fig, textData = plot_data_point("{} \n n = {}{} \n".format(title, len(chosen_node_set), 
                            str(sorted(list(chosen_node_set)))),
                            f_outputfile, l_df, orig_name, list(z), list(y), len(chosen_node_set), tdf, k_avg, color_labels, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings)
    return l_df, fig, textData
    #print ("Plotting Magnified Data")
    #outputfile='Magnified - {}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    #plot_magnified_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
    #                    str(sorted(list(chosen_node_set))), variant, norm),
    #                    outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set), list(codelet_variant))

def compute_and_plot(variant, df,outputfile_prefix, norm, title, chosen_node_set, out_df):
    out_csv = variant+ '_' + outputfile_prefix +'_export_dataframe.csv'
    out_df[['name', 'short_name', 'variant']] = df[['name', 'short_name', 'variant']]

    compute_capacity(df, norm, chosen_node_set, out_df)
    compute_saturation(df, chosen_node_set, out_df)
    compute_intensity(df, chosen_node_set, out_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        out_df['C_{}'.format(node)]=formula(df)
    out_df['k'] = df['Saturation'] * df['Intensity']
    out_df['speedup'] = df['speedup']
    out_df.to_csv(out_csv, index = False, header=True)
    indices = df['short_name']
    y = df['Saturation']
    z = df['Intensity']
    df['SI']=df['Saturation'] * df['Intensity'] 
    k = df['SI']
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
    speedups = df['Speedup']
    floprate = df['C_FLOP [GFlop/s]']
    codelet_variant = df['variant']
    #plot_data("Saturation plot", 'saturation.png', x, y)
    #plot_data("Intensity plot", 'Intensity.png', x, z)
#    outputfile='SI.png'
    today = datetime.date.today()
    outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    plot_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
                        str(sorted(list(chosen_node_set))), variant, norm),
                        outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set))
    print ("Plotting Magnified Data")
    outputfile='Magnified - {}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    #plot_magnified_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
    #                    str(sorted(list(chosen_node_set))), variant, norm),
    #                    outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set), list(codelet_variant))

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
def plot_magnified_data(title, filename, xs, ys, indices, speedups, floprates, Ns, codelet_variant):
    DATA =tuple(zip(xs,ys))
    #     DATA = ((1, 3),
    #             (2, 4),
    #             (3, 1),
    #             (4, 2))
    # dash_style =
    #     direction, length, (text)rotation, dashrotation, push
    # (The parameters are varied to show their effects, not for visual appeal).
    #     dash_style = (
    #         (0, 20, -15, 30, 10),
    #         (1, 30, 0, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (1, 20, 30, 60, 10))
    
    fig, ax = plt.subplots()

    #xmax=max(xs)*2
    xmax=max(xs) + 0.2*max(xs)
    ymax=max(ys) + 0.2*max(xs)
    xmin=min(xs) - 0.2*min(xs)
    ymin=min(ys) - 0.2*min(ys)

    ax.set_xlim((xmin, xmax))
    ax.set_ylim((xmin, ymax))

    (x, y) = zip(*DATA)
    ax.scatter(x, y, marker='o')

    ns = [1,2,(Ns-1), Ns, (Ns+1),8]

    ctxs = draw_contours(ax, xmax, ns)

    plt.rcParams.update({'font.size': 7})
    mytext= [str('({0}, {1})'.format( indices[i], codelet_variant[i] ))  for i in range(len(DATA))]    
    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    #ax.legend(loc="lower left",title="(name,flops)")

    if filename:
        plt.savefig(filename)
    else:
        plt.show()

# Set filename to [] for GUI output    
def plot_data(title, filename, xs, ys, indices, speedups, floprates, Ns):
    DATA =tuple(zip(xs,ys))
    #     DATA = ((1, 3),
    #             (2, 4),
    #             (3, 1),
    #             (4, 2))
    # dash_style =
    #     direction, length, (text)rotation, dashrotation, push
    # (The parameters are varied to show their effects, not for visual appeal).
    #     dash_style = (
    #         (0, 20, -15, 30, 10),
    #         (1, 30, 0, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (1, 20, 30, 60, 10))
    
    fig, ax = plt.subplots()

    #xmax=max(xs)*2
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2  
    ax.set_xlim((0, xmax))
    ax.set_ylim((0, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)
    ax.scatter(x, y, marker='o')

    ns = [1,2,(Ns-1), Ns, (Ns+1),8]

    ctxs = draw_contours(ax, xmax, ns)

    plt.rcParams.update({'font.size': 7})
    mytext= [str('({0}, {1:.2f})'.format( indices[i], floprates[i] ))  for i in range(len(DATA))]    
    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]

    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    #ax.legend(loc="lower left",title="(name,flops)")
# Create the second legend and add the artist manually.
    ax.legend(loc="lower left",title="CG:(" + str(round(x_mean, 2)) + " , " + str(round(y_mean, 2)) + ")\n"
                                + "SD:(" + str(round(x_stdev, 2)) + " , " + str(round(y_stdev, 2)) + ")")
    if filename:
        plt.savefig(filename)
    else:
        plt.show()

# Set filename to [] for GUI output    
def plot_data_point(title, filename, orig_df, orig_name, xs, ys, Ns, target_df, k_average, color_labels=None, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame()):
    #     DATA = ((1, 3),
    #             (2, 4),
    #             (3, 1),
    #             (4, 2))
    # dash_style =
    #     direction, length, (text)rotation, dashrotation, push
    # (The parameters are varied to show their effects, not for visual appeal).
    #     dash_style = (
    #         (0, 20, -15, 30, 10),
    #         (1, 30, 0, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (1, 20, 30, 60, 10))
    if filtering:
        orig_df = orig_df.loc[(orig_df[filter_data[0]] >= filter_data[1]) & (orig_df[filter_data[0]] <= filter_data[2])]

    fig, ax = plt.subplots()
    print("Entering plot_data_orig_point")

    orig_codelet_sat = orig_df['Saturation'].values.tolist()
    orig_codelet_int = orig_df['Intensity'].values.tolist()
    DATA = tuple(zip(orig_codelet_int,orig_codelet_sat))

    orig_codelet_index = orig_df['short_name'].values.tolist()
    orig_codelet_names = orig_df['name'].values.tolist()
    orig_codelet_speedup = orig_df['speedup'].values.tolist()
    orig_codelet_variant = orig_df['variant'].values.tolist()
    orig_codelet_memlevel = orig_df['memlevel'].values.tolist()
    #xmax=max(xs)*2
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2  
    ax.set_xlim((0, xmax))
    ax.set_ylim((0, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)
    print('Data length: ', len(DATA))

    # Draw contours
    ns = [1,2,(Ns-1), Ns, (Ns+1),(Ns+2)]
    ctxs = draw_contours(ax, xmax, ns)

    # Plot data points
    markers = []
    orig_df.reset_index(drop=True, inplace=True)
    for i in range(len(DATA)):
        markers.extend(ax.plot(x[i], y[i], marker='o', color=orig_df['color'][i][0], label='data'+str(i), linestyle='', alpha=1))

    plt.rcParams.update({'font.size': 7})
    #mytext= [str('({0}, {1}, {2})'.format( orig_codelet_index[i], orig_codelet_variant[i], orig_codelet_speedup[i] ))  for i in range(len(DATA))]
    mytext= [str('({0}, {1}, {2})'.format( orig_codelet_index[i], orig_codelet_variant[i], orig_codelet_memlevel[i]))  for i in range(len(DATA))]
    texts = [plt.text(x[i], y[i], mytext[i], alpha=1) for i in range(len(DATA))]

    # Create a Rectangle patch
    print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
    rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])),
            (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
    ax.add_patch(rect)
    ax.set(xlabel=r'$I$', ylabel=r'$S$')
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
    if not mappings.empty:
        for index in mappings.index:
            before_row = orig_df.loc[orig_df['name']==mappings['before_name'][index]].reset_index(drop=True)
            after_row = orig_df.loc[orig_df['name']==mappings['after_name'][index]].reset_index(drop=True)
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
                        connectionstyle='arc3,rad=0.3')
                else:
                    con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                        connectionstyle='arc3,rad=-0.3')
                ax.add_artist(con)
    
    plt.tight_layout()
    #ax.add_artist(leg);

    plotData = {
        'xs' : x,
        'ys' : y,
        'mytext' : mytext,
        'orig_mytext' : copy.deepcopy(mytext),
        'ax' : ax,
        'legend' : legend,
        'orig_legend' : legend.get_title().get_text(),
        'title' : title,
        'texts' : texts,
        'markers' : markers,
        'names' : orig_df['name'].values.tolist(),
        'marker:text' : dict(zip(markers,texts)),
        'marker:name' : dict(zip(markers,orig_df['name'].values.tolist())),
        'name:marker' : dict(zip(orig_df['name'].values.tolist(), markers)),
        'text:arrow' : {},
        'text:name' : dict(zip(texts, orig_df['name'].values.tolist()))
    }

    if filename:
        plt.savefig(filename)
    else:
        plt.show()

    return fig, plotData

# Set filename to [] for GUI output    
def plot_data_orig(title, filename, xs, ys, indices, speedups, floprates, Ns, target_df, k_average):
    DATA =tuple(zip(xs,ys))
    #     DATA = ((1, 3),
    #             (2, 4),
    #             (3, 1),
    #             (4, 2))
    # dash_style =
    #     direction, length, (text)rotation, dashrotation, push
    # (The parameters are varied to show their effects, not for visual appeal).
    #     dash_style = (
    #         (0, 20, -15, 30, 10),
    #         (1, 30, 0, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (0, 40, 15, 15, 10),
    #         (1, 20, 30, 60, 10))
    
    fig, ax = plt.subplots()

    #xmax=max(xs)*2
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2  
    ax.set_xlim((0, xmax))
    ax.set_ylim((0, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)


    ax.scatter(x, y, marker='o')

    ns = [1,2,(Ns-1), Ns, (Ns+1),(Ns+2)]

    ctxs = draw_contours(ax, xmax, ns)

    plt.rcParams.update({'font.size': 7})

    mytext= [str('({0}, {1:.2f})'.format( indices[i], floprates[i] ))  for i in range(len(DATA))]
    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts)
    #adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))
    # Create a dot
    plt.plot(x_mean, y_mean, 'ro')
    #plt.annotate("C$_C$$_G$", (x_mean, y_mean), arrowprops=dict(facecolor='red', shrink=0.05))
    # Create a Rectangle patch
    print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
    rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])),
            (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
    ax.add_patch(rect)
    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    #ax.legend(loc="lower left",title="(name,flops)")
# Create the second legend and add the artist manually.
    ax.legend(loc="lower left",title="I$_C$$_G$ = " + str(round(x_mean, 2)) + "\nS$_C$$_G$ = " + str(round(y_mean, 2)) 
    + "\nk$_C$$_G$ = " + str(round(k_average, 2)))
    #ax.add_artist(leg);

    if filename:
        plt.savefig(filename)
    else:
        plt.show()

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
