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

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

def trawl_plot(df, outputfile, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None):
    df.columns = succinctify(df.columns)
    df['C_FLOP [GFlop/s]'] = df['flop_rate_gflop/s']
    fig, texts = compute_and_plot(
        'ORIG', df, outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, source_order=source_order)
    # Return dataframe and figure for GUI
    return (df, fig, texts)

def compute_color_labels(df):
    color_labels = []
    for color in df['color'].unique():
        colorDf = df.loc[df['color'] == color].reset_index()
        codelet = (colorDf['name'][0])
        color_labels.append((codelet.split(':')[0], color))
    return color_labels

def compute_and_plot(variant, df, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None):
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
        ys = df['vec']

    today = datetime.date.today()
    if gui:
        outputfile = None
    else:
        outputfile = '{}-{}-{}-{}.png'.format(outputfile_prefix,
                                          variant, scale, today)
    fig, texts = plot_data("{}\nvariant={}, scale={}".format(title, variant, scale), outputfile, list(
        xs), list(ys), list(indices), scale, df, color_labels=color_labels, y_axis=y_axis, source_order=source_order)
    return fig, texts

# Set filename to [] for GUI output
def plot_data(title, filename, xs, ys, indices, scale, df, color_labels=None, x_axis=None, y_axis=None, source_order=None):
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
    ax.scatter(x, y, marker='o', c=df.color)

    plt.rcParams.update({'font.size': 7})
    mytext = [str('({0})'.format(indices[i]))
              for i in range(len(DATA))]
    texts = [plt.text(xs[i], ys[i], mytext[i]) for i in range(len(DATA))]

    adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
    ax.set(xlabel=x_axis if x_axis else r'OP Rate', ylabel=y_axis if y_axis else r'Potential Speedup: Vectorized')
    ax.set_title(title, pad=40)

    # Arrows between multiple runs
    if source_order:
        df['map_name'] = df['name'].map(lambda x: x.split(' ')[-1].split(',')[-1].split('_')[-1])
        before = df.loc[df['timestamp#'] == source_order[0]]
        after = df.loc[df['timestamp#'] == source_order[1]]
        for index in before.index:
            match = after.loc[after['map_name'] == before['map_name'][index]].reset_index()
            if not match.empty:
                x_axis = x_axis if x_axis else 'C_FLOP [GFlop/s]'
                y_axis = y_axis if y_axis else 'vec'
                xyA = (before[x_axis][index], before[y_axis][index])
                xyB = (match[x_axis][0], match[y_axis][0])
                con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=5, shrinkB=5, mutation_scale=13, fc="w", \
                    connectionstyle='arc3,rad=0.3')
                ax.add_artist(con)

    # Legend
    patches = []
    if color_labels and len(color_labels) >= 2:
        for color_label in color_labels:
            patch = mpatches.Patch(label=color_label[0], color=color_label[1])
            patches.append(patch)

    ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0., 1.02, 1., .102), title="(name)", mode='expand', borderaxespad=0.,
              handles=patches)

    plt.tight_layout()
    if filename:
        plt.savefig(filename)

    return fig, texts
