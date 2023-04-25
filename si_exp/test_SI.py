#!/usr/bin/env python
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text
from matplotlib.patches import Rectangle
import statistics
from matplotlib.legend import Legend
from metric_names import MetricName
warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

DO_DEBUG_LOGS = True


BASIC_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR', 'RAM'}
SCALAR_NODE_SET={'L1', 'L2', 'L3', 'RAM'}
BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'LB', 'RS'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FrontEnd'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR'}
DEFAULT_CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
    'L1': (lambda df : df[MetricName.RATE_L1_GB_P_S]/8),
    'L2': (lambda df : df[MetricName.RATE_L2_GB_P_S]/8),
    'L3': (lambda df : df[MetricName.RATE_L3_GB_P_S]/8),
    'FLOP': (lambda df : df[MetricName.RATE_FP_GFLOP_P_S]),
    'VR': (lambda df : df[MetricName.RATE_REG_SIMD_GB_P_S]/24),
    'RAM': (lambda df : df[MetricName.RATE_RAM_GB_P_S]/8),
    'FE': (lambda df : df[MetricName.STALL_FE_PCT]*(df['C_max'])/100),
    'SB': (lambda df : df[MetricName.STALL_SB_PCT]*(df['C_max'])/100),
    'LM': (lambda df : df[MetricName.STALL_LM_PCT]*(df['C_max'])/100),
    'LB': (lambda df : df[MetricName.STALL_LB_PCT]*(df['C_max'])/100),
    'RS': (lambda df : df[MetricName.STALL_RS_PCT]*(df['C_max'])/100),
    'CU': (lambda df : (df['%frontend']*df['C_scalar']/100 + df['%lb']*df['C_scalar']/100 + df['%sb']*df['C_scalar']/100 + df['%lm']*df['C_scalar'])/100)
    }

CU_NODE_DICT = {
    'FE': MetricName.STALL_FE_PCT,
    'SB': MetricName.STALL_SB_PCT,
    'LM': MetricName.STALL_LM_PCT,
    'LB': MetricName.STALL_LB_PCT,
    'RS': MetricName.STALL_RS_PCT,
}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed

def concat_ordered_columns(frames):
    columns_ordered = []
    for frame in frames:
        columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
    final_df = pd.concat(frames)
    return final_df[columns_ordered]

def parse_ip(inputfile,outputfile, norm, title, chosen_node_set, rflie):
#    inputfile="/tmp/input.csv"
    df = pd.read_csv(inputfile)
    grouped = df.groupby(MetricName.VARIANT)
    # Generate SI plot for each variant
    mask = df[MetricName.VARIANT] == "ORIG"
    #if not df.empty
    short_name=''
    target_df = pd.DataFrame()
    compute_and_plot('XFORM', df[~mask], outputfile, norm, title, chosen_node_set, target_df)
    rdf = pd.read_csv(rflie)
    compute_and_plot_orig('ORIG', df[~mask], outputfile, norm, title, chosen_node_set, target_df, short_name)
    for i, row in rdf.iterrows():
        l_df = df
        data = pd.DataFrame(columns=df.columns.tolist())
        data = data.append(row, ignore_index=False)[df.columns.tolist()]
        short_name = row[MetricName.SHORT_NAME]
        print(short_name)
        #df_row_merged = pd.concat([l_df, row], ignore_index=False)[l_df.columns.tolist()]
        dfs = [l_df,data]
        full_df = concat_ordered_columns(dfs)
        #full_df.to_csv(short_name + '_debug.csv', index = False, header=True)
        outputfile_prfx = short_name + outputfile
        compute_and_plot_orig('ORIG', full_df, outputfile_prfx, norm, title, chosen_node_set, target_df, short_name)
    #compute_and_plot_orig('ORIG', rdf, outputfile_prfx, norm, title, chosen_node_set, target_df, short_name)
    # if not df.empty
    # compute_and_plot('ORIG', df[mask], outputfile, norm, title, chosen_node_set)
    # for variant, group in grouped:
        # compute_and_plot(variant, group, outputfile)

def compute_capacity(df, norm, chosen_node_set, out_df):
    #print("The node list are as follows :")
    #print(chosen_node_set)
    chosen_basic_node_set = BASIC_NODE_SET & chosen_node_set
    chosen_buffer_node_set = BUFFER_NODE_SET & chosen_node_set
    for node in chosen_basic_node_set:
        #print ("The current node : ", node)
        formula=capacity_formula[node]
        df['C_{}'.format(node)]=formula(df)

    #print(df)
    if norm == 'row':
        #print ("<=====Running Row Norm======>")
        df['C_max']=df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1)
    else:
        #print ("<=====Running Matrix Norm======>")
        df['C_max']=max(df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1))
    #print ("<=====compute_capacity======>")
    #print(df['C_max'])

    if norm == 'row':
        #print ("<=====Running Row Norm======>")
        df['C_scalar']=df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1)
    else:
        #print ("<=====Running Matrix Norm======>")
        df['C_scalar']=max(df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1))
    #print ("<=====compute_cu_scalar======>")
    #print(df['C_scalar'])
    out_df['C_scalar'] = df['C_scalar']
    for node in chosen_buffer_node_set:
        formula=capacity_formula[node]
        df['C_{}'.format(node)]=formula(df)

def compute_saturation(df, chosen_node_set, out_df):
    nodeMax=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].max(axis=0)
    #max_list = np.array(nodeMax.values.tolist())
    #print(nodeMax)
    nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
    #print ("<=====compute_saturation======>")
    #print(nodeMax)
    for node in chosen_node_set - BUFFER_NODE_SET:
        df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
    for node in chosen_node_set & BUFFER_NODE_SET:
        df['RelSat_{}'.format(node)] = df[CU_NODE_DICT[node]] / df[CU_NODE_DICT[node]].max(axis=0) 
    df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)
    #print(df['Saturation'])
    out_df['Saturation'] = df['Saturation']


def compute_intensity(df, chosen_node_set, out_df):
    node_cnt = len(chosen_node_set)
    csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
    df['Intensity']=node_cnt*df['C_max'] / csum
    #print(df['Intensity'])
    out_df['Intensity'] = df['Intensity']

def test_and_plot_orig(variant, df,outputfile_prefix, norm, title, chosen_node_set, tdf, orig_name):
    out_csv = variant+ '_' + outputfile_prefix +'_export_dataframe.csv'
    #print (out_csv)
    out_df = pd.DataFrame()
    out_df[[MetricName.NAME, MetricName.SHORT_NAME, MetricName.VARIANT]] = df[[MetricName.NAME, MetricName.SHORT_NAME, MetricName.VARIANT]]
    compute_capacity(df, norm, chosen_node_set, out_df)
    compute_saturation(df, chosen_node_set, out_df)
    compute_intensity(df, chosen_node_set, out_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        out_df['C_{}'.format(node)]=formula(df)
    out_df['k'] = df['Saturation'] * df['Intensity']

    #out_df.to_csv(out_csv, index = False, header=True)
    indices = df[MetricName.SHORT_NAME]
    y = df['Saturation']
    z = df['Intensity']
    df['SI']=df['Saturation'] * df['Intensity'] 
    k = df['SI']
    k_avg = k.mean()
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
    speedups = df['Net_SW_Bias']
    floprate = df['C_FLOP']
    codelet_variant = df[MetricName.VARIANT]
    #plot_data("Saturation plot", 'saturation.png', x, y)
    #plot_data("Intensity plot", 'Intensity.png', x, z)
#    outputfile='SI.png'
    today = datetime.date.today()
    outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    f_outputfile='Final_{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    #tdf.to_csv('target_debug.csv', index = False, header=True)
    if DO_DEBUG_LOGS:
        plot_data_orig("{} \n n = {}{} \n".format(title, len(chosen_node_set), 
                        str(sorted(list(chosen_node_set)))),
                        outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set), tdf, k_avg)
    if orig_name:
        l_df = df.loc[df[MetricName.SHORT_NAME].isin([orig_name])]
        #print(l_df)
        result = test_data_point("{} \n n = {}{} \n".format(title, len(chosen_node_set), 
                            str(sorted(list(chosen_node_set)))),
                            f_outputfile, l_df, orig_name, list(z), list(y), len(chosen_node_set), tdf, k_avg)
    return result
    #print ("Plotting Magnified Data")
    #outputfile='Magnified - {}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    #plot_magnified_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
    #                    str(sorted(list(chosen_node_set))), variant, norm),
    #                    outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set), list(codelet_variant))

def compute_and_plot(variant, df,outputfile_prefix, norm, title, chosen_node_set, out_df):
    out_csv = variant+ '_' + outputfile_prefix +'_export_dataframe.csv'
    #print (out_csv)
    out_df[[MetricName.NAME, MetricName.SHORT_NAME, MetricName.VARIANT]] = df[[MetricName.NAME, MetricName.SHORT_NAME, MetricName.VARIANT]]

    compute_capacity(df, norm, chosen_node_set, out_df)
    compute_saturation(df, chosen_node_set, out_df)
    compute_intensity(df, chosen_node_set, out_df)
    for node in sorted(chosen_node_set):
        formula=capacity_formula[node]
        out_df['C_{}'.format(node)]=formula(df)
    out_df['k'] = df['Saturation'] * df['Intensity']
    #out_df.to_csv(out_csv, index = False, header=True)
    indices = df[MetricName.SHORT_NAME]
    y = df['Saturation']
    z = df['Intensity']
    df['SI']=df['Saturation'] * df['Intensity'] 
    k = df['SI']
    k_avg = df['Saturation'].mean() * df['Intensity'].mean()
    df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
    speedups = df['Speedup']
    floprate = df['C_FLOP']
    codelet_variant = df[MetricName.VARIANT]
    #plot_data("Saturation plot", 'saturation.png', x, y)
    #plot_data("Intensity plot", 'Intensity.png', x, z)
#    outputfile='SI.png'
    today = datetime.date.today()
    outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
    #plot_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
    #                    str(sorted(list(chosen_node_set))), variant, norm),
    #                    outputfile, list(z), list(y),    list(indices), list(speedups), list(floprate), len(chosen_node_set))
    #print ("Plotting Magnified Data")
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
        #lines.append(ax.plot(ctx, cty, label='k={}'.format(n)))
        lines.append(ax.plot(ctx, cty))
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

    mytext= [str('({0}, {1})'.format( indices[i], codelet_variant[i] ))  for i in range(len(DATA))]    

    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

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

    mytext= [str('({0}, {1:.2f})'.format( indices[i], floprates[i] ))  for i in range(len(DATA))]    

    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

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
def test_data_point(title, filename, orig_df, orig_name, xs, ys, Ns, target_df, k_average):
    fig, ax = plt.subplots()
    #print("Entering test_data_orig_point")
    #print (orig_df)

    orig_codelet_sat = orig_df['Saturation'].values.tolist()
    orig_codelet_int = orig_df['Intensity'].values.tolist()

    orig_codelet_sat_val = orig_df['Saturation'].values[0]
    orig_codelet_int_val = orig_df['Intensity'].values[0]

    #print ("Sat value = ", orig_codelet_sat)
    #print ("Int value = ", orig_codelet_int)
    DATA = tuple(zip(orig_codelet_int,orig_codelet_sat))

    orig_codelet_index = orig_df[MetricName.SHORT_NAME].values.tolist()
    orig_codelet_variant = orig_df[MetricName.VARIANT].values.tolist()
    #xmax=max(xs)*2
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2
    xmin=min(xs) - 0.5
    ymin=min(ys) - 0.5
    ax.set_xlim((0, xmax))
    ax.set_ylim((0, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)


    ax.scatter(x, y, marker='o')
    #plt.plot(orig_codelet_int, orig_codelet_sat,'ro') 

    ns = [(Ns-1), Ns, (Ns+1),(Ns+2)]

    ctxs = draw_contours(ax, xmax, ns)
    #print('Data length: ', len(DATA))
    mytext= [str('({0}, {1})'.format( orig_codelet_index[i], orig_codelet_variant[i]))  for i in range(len(DATA))]
    #mytext = [str('({0})'.format( orig_codelet_index ))]

    texts = [plt.text(orig_codelet_int[i], orig_codelet_sat[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #texts = [plt.text(orig_codelet_int, orig_codelet_int, mytext, ha='center', va='center')]
    adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))
    # Create a dot
    #plt.plot(x_mean, y_mean, 'bo')
    # Create a Rectangle patch
    #print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
    rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])),
            (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
    ax.add_patch(rect)
    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    centerx = min(target_df['Intensity'])
    centery = min(target_df['Saturation'])
    if ((orig_codelet_sat_val >= min(target_df['Saturation'])) and (orig_codelet_sat_val <= max(target_df['Saturation'])) and
        (orig_codelet_int_val >= min(target_df['Intensity'])) and (orig_codelet_int_val <= max(target_df['Intensity']))) :
        return False
    else :
        return True

# Set filename to [] for GUI output    
def plot_data_point(title, filename, orig_df, orig_name, xs, ys, Ns, target_df, k_average):
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
    print("Entering plot_data_orig_point")

    orig_codelet_sat = orig_df['Saturation'].values.tolist()
    orig_codelet_int = orig_df['Intensity'].values.tolist()
    DATA = tuple(zip(orig_codelet_int,orig_codelet_sat))

    orig_codelet_index = orig_df[MetricName.SHORT_NAME].values.tolist()
    orig_codelet_variant = orig_df[MetricName.VARIANT].values.tolist()
    #xmax=max(xs)*2
    xmax=max(xs)*1.2
    ymax=max(ys)*1.2
    xmin=min(xs) - 0.5
    ymin=min(ys) - 0.5
    ax.set_xlim((1, xmax))
    ax.set_ylim((3, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)


    ax.scatter(x, y, marker='o')
    #plt.plot(orig_codelet_int, orig_codelet_sat,'ro') 

    ns = [(Ns-1), Ns, (Ns+1),(Ns+2)]

    ctxs = draw_contours(ax, xmax, ns)
    print('Data length: ', len(DATA))
    mytext= [str('({0}, {1}, {2})'.format( orig_codelet_index[i], orig_codelet_variant[i]))  for i in range(len(DATA))]
    #mytext = [str('({0})'.format( orig_codelet_index ))]

    texts = [plt.text(orig_codelet_int[i], orig_codelet_sat[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #texts = [plt.text(orig_codelet_int, orig_codelet_int, mytext, ha='center', va='center')]
    adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))
    # Create a dot
    #plt.plot(x_mean, y_mean, 'bo')
    # Create a Rectangle patch
    print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
    rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])),
            (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
    ax.add_patch(rect)
    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    centerx = min(target_df['Intensity'])
    centery = min(target_df['Saturation'])
    #ax.legend(loc="lower left",title="(name,flops)")
# Create the second legend and add the artist manually.
    ax.legend(loc="lower left",title="I$_C$$_G$ = 2.42" + "\nS$_C$$_G$ = 2.84" + "\nk$_C$$_G$ = 6.81")
    #ax.add_artist(leg);

    if filename:
        plt.savefig(filename)
    else:
        plt.show()

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

    xmin=min(xs) - 0.5
    ymin=min(ys) - 0.5
    ax.set_xlim((xmin, xmax))
    ax.set_ylim((ymin, ymax))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys) 
    x_stdev = statistics.stdev(xs)
    y_stdev = statistics.stdev(ys) 

    (x, y) = zip(*DATA)


    ax.scatter(x, y, marker='o')

    ns = [(Ns-1), Ns, (Ns+1),(Ns+2)]

    ctxs = draw_contours(ax, xmax, ns)

    mytext= [str('({0}, {1:.2f}, {2:.2f})'.format( indices[i], floprates[i], speedups[i] ))  for i in range(len(DATA))]

    texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))
    # Create a dot
    plt.plot(x_mean, y_mean, 'ro')
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
