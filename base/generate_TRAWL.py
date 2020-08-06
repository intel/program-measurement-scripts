#!/usr/bin/python3
import pandas as pd
import numpy as np
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from matplotlib import style
from adjustText import adjust_text
from capelib import succinctify
import copy

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

def trawl_plot(df, outputfile, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, variants=['ORIG'], source_order=None, mappings=pd.DataFrame()):
    df.columns = succinctify(df.columns)
    if not mappings.empty:
        mappings.columns = succinctify(mappings.columns)
    df['C_FLOP [GFlop/s]'] = df['flop_rate_gflop/s']
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df['variant'].isin(variants)]
    df, fig, plotData = compute_and_plot(
        'ORIG', df, outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, source_order=source_order, mappings=mappings)
    # Return dataframe and figure for GUI
    return (df, fig, plotData)

def compute_color_labels(df):
    color_labels = []
    for color in df['color'].unique():
        colorDf = df.loc[df['color'] == color].reset_index()
        codelet = (colorDf['name'][0])
        color_labels.append((codelet.split(':')[0], color))
    return color_labels

def compute_and_plot(variant, df, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None, mappings=pd.DataFrame()):
    if df.empty:
        return None, None  # Nothing to do

    # Used to create a legend of file names to color for multiple plots
    color_labels = compute_color_labels(df)
    if no_plot:
        return None, None

    try:
        indices = df['short_name']
    except:
        indices = df['name']

    if x_axis:
        xs = df[x_axis]
    else:
        xs = df['C_FLOP [GFlop/s]']
    if y_axis:
        ys = df[y_axis]
    else:
        ys = df['speedup[vec]']
    today = datetime.date.today()
    if gui:
        outputfile = None
    else:
        outputfile = '{}-{}-{}-{}.png'.format(outputfile_prefix, variant, scale, today)
    fig, plotData = plot_data("{}\nvariant={}, scale={}".format(title, variant, scale), outputfile, list(
        xs), list(ys), list(indices), scale, df, color_labels=color_labels, x_axis=x_axis, y_axis=y_axis, source_order=source_order, mappings=mappings)
    return df, fig, plotData

# Set filename to [] for GUI output
def plot_data(title, filename, xs, ys, indices, scale, df, color_labels=None, x_axis=None, y_axis=None, source_order=None, mappings=pd.DataFrame()):
    DATA = tuple(zip(xs, ys))

    fig, ax = plt.subplots()

    xmax = max(xs)*1.2
    ymax = max(ys)*1.2

    if scale == 'loglog':
        xmin = min(xs)
        ymin = min(ys)
        ax.set_xlim((xmin, xmax))
        ax.set_ylim((ymin, ymax))
        plt.xscale("log")
        plt.yscale("log")
    else:
        ax.set_xlim((0, xmax))
        ax.set_ylim((0, ymax))

    (x, y) = zip(*DATA)

    # Draw contours
    plt.axvline(x=xmax/2)
    plt.axhline(y=ymax/2)

    # Plot data points
    markers = []
    df.reset_index(drop=True, inplace=True)
    for i in range(len(x)):
        markers.extend(ax.plot(x[i], y[i], marker='o', color=df['color'][i][0], label='data'+str(i), linestyle='', alpha=1))

    plt.rcParams.update({'font.size': 7})
    mytext = [str('({0})'.format(indices[i])) for i in range(len(DATA))]
    texts = [plt.text(xs[i], ys[i], mytext[i], alpha=1) for i in range(len(DATA))]
    #adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
    ax.set(xlabel=x_axis if x_axis else r'OP Rate', ylabel=y_axis if y_axis else r'Potential Speedup: Vectorized')
    ax.set_title(title, pad=40)

    # Legend
    patches = []
    if color_labels and len(color_labels) >= 2:
        for color_label in color_labels:
            patch = mpatches.Patch(label=color_label[0], color=color_label[1])
            patches.append(patch)

    legend = ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0., 1.02, 1., .102), title="(name)", mode='expand', borderaxespad=0.,
              handles=patches)

    # Arrows between multiple runs
    if not mappings.empty:
        for index in mappings.index:
            before_row = df.loc[df['name']==mappings['before_name'][index]].reset_index(drop=True)
            after_row = df.loc[df['name']==mappings['after_name'][index]].reset_index(drop=True)
            if not before_row.empty and not after_row.empty:
                x_axis = x_axis if x_axis else 'C_FLOP [GFlop/s]'
                y_axis = y_axis if y_axis else 'speedup[vec]'
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
        'names' : df['name'].values.tolist(),
        'marker:text' : dict(zip(markers,texts)),
        'marker:name' : dict(zip(markers,df['name'].values.tolist())),
        'name:marker' : dict(zip(df['name'].values.tolist(), markers)),
        'text:arrow' : {},
        'text:name' : dict(zip(texts, df['name'].values.tolist()))
    }

    if filename:
        plt.savefig(filename)

    return fig, plotData