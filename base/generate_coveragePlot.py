#!/usr/bin/python3
import pandas as pd
import numpy as np
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import style
from adjustText import adjust_text

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.


def coverage_plot(df, inputfile, outputfile, scale, title, no_plot, gui=False):
    fig, texts = compute_and_plot(
        'ORIG', df, outputfile, scale, title, no_plot, gui)
    # Return dataframe and figure for GUI
    return (fig, texts)

def compute_color_labels(df):
    color_labels = []
    for color in df['color'].unique():
        colorDf = df.loc[df['color'] == color].reset_index()
        codelet = (colorDf['name'][0])
        color_labels.append((codelet.split(':')[0], color))
    return color_labels

def compute_and_plot(variant, df, outputfile_prefix, scale, title, no_plot, gui=False):
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

    xs = df['C_FLOP [GFlop/s]']
    ys = df[r'%coverage']

    mem_level = df['memlevel']
    today = datetime.date.today()
    if gui:
        outputfile = None
    else:
        outputfile = '{}-{}-{}-{}.png'.format(outputfile_prefix,
                                          variant, scale, today)
    fig, texts = plot_data("{}\nvariant={}, scale={}".format(title, variant, scale), outputfile, list(
        xs), list(ys), list(indices), list(mem_level), scale, df, color_labels)
    return fig, texts

# Set filename to [] for GUI output
def plot_data(title, filename, xs, ys, indices, memlevel, scale, df=None, color_labels=None):
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
    mytext = [str('({0}, {1})'.format(indices[i], memlevel[i]))
              for i in range(len(DATA))]
    texts = [plt.text(xs[i], ys[i], mytext[i]) for i in range(len(DATA))]

    adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
    ax.set(xlabel=r'OP Rate', ylabel=r'% Coverage')
    ax.set_title(title, pad=40)

    patches = []
    if color_labels and len(color_labels) >= 2:
        for color_label in color_labels:
            patch = mpatches.Patch(label=color_label[0], color=color_label[1])
            patches.append(patch)

    ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0., 1.02, 1., .102), title="(name,memlevel)", mode='expand', borderaxespad=0.,
              handles=patches)

    plt.tight_layout()
    if filename:
        plt.savefig(filename)

    return fig, texts
