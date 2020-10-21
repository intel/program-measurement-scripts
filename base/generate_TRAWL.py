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
import copy
from capeplot import CapePlot
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class TrawlPlot(CapePlot):
    def __init__(self):
        pass
    pass

def trawl_plot(df, outputfile, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, variants=['ORIG'], source_order=None, mappings=pd.DataFrame(), short_names_path=''):
    if not mappings.empty:
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
        'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
    df['C_FLOP [GFlop/s]'] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)]
    df, fig, plotData = compute_and_plot(
        'ORIG', df, outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, source_order=source_order, mappings=mappings, short_names_path=short_names_path)
    # Return dataframe and figure for GUI
    #plot = TrawlPlot('ORIG', df, outputfile, scale, title, no_plot, gui=gui, \
    #    x_axis=x_axis, y_axis=y_axis, source_order=source_order, mappings=mappings, short_names_path=short_names_path)
    #plot.compute_and_plot()
    # return (plot.df, plot.fig, plot.plotData)

    return (df, fig, plotData)

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

def compute_and_plot(variant, df, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None, mappings=pd.DataFrame(), short_names_path=''):
    if df.empty:
        return None, None  # Nothing to do

    # Used to create a legend of file names to color for multiple plots
    color_labels = compute_color_labels(df, short_names_path)
    if no_plot:
        return None, None

    try:
        indices = df[SHORT_NAME]
    except:
        indices = df[NAME]

    if x_axis: xs = df[x_axis]
    else: xs = df['C_FLOP [GFlop/s]']
    if y_axis: ys = df[y_axis]
    else: ys = df[SPEEDUP_DL1]
    
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

    (x, y) = zip(*DATA)

    # Draw contours
    plt.axvline(x=xmax/2)
    plt.axhline(y=ymax/2)

    # Plot data points
    markers = []
    df.reset_index(drop=True, inplace=True)
    for i in range(len(x)):
        markers.extend(ax.plot(x[i], y[i], marker='o', color=df['Color'][i][0], label=df[NAME][i]+str(df[TIMESTAMP][i]), linestyle='', alpha=1))

    plt.rcParams.update({'font.size': 7})
    mytext = [str('({0})'.format(indices[i])) for i in range(len(DATA))]
    texts = [plt.text(xs[i], ys[i], mytext[i], alpha=1) for i in range(len(DATA))]
    #adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
    ax.set(xlabel=x_axis if x_axis else 'C_FLOP [GFlop/s]', ylabel=y_axis if y_axis else SPEEDUP_VEC)
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
    name_mapping = dict()
    mymappings = []
    if not mappings.empty:
        for i in mappings.index:
            name_mapping[mappings['before_name'][i]+str(mappings['before_timestamp#'][i])] = []
            name_mapping[mappings['after_name'][i]+str(mappings['after_timestamp#'][i])] = []
        for index in mappings.index:
            before_row = df.loc[(df[NAME]==mappings['before_name'][index]) & (df[TIMESTAMP]==mappings['before_timestamp#'][index])].reset_index(drop=True)
            after_row = df.loc[(df[NAME]==mappings['after_name'][index]) & (df[TIMESTAMP]==mappings['after_timestamp#'][index])].reset_index(drop=True)
            if not before_row.empty and not after_row.empty:
                x_axis = x_axis if x_axis else 'C_FLOP [GFlop/s]'
                y_axis = y_axis if y_axis else SPEEDUP_VEC
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
    
    names = [name + timestamp for name,timestamp in zip(df[NAME], df[TIMESTAMP].astype(str))]
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
        'timestamps' : df[TIMESTAMP].values.tolist(),
        'marker:text' : dict(zip(markers,texts)),
        'marker:name' : dict(zip(markers,names)),
        'name:marker' : dict(zip(names, markers)),
        'name:text' : dict(zip(names, texts)),
        'text:arrow' : {},
        'text:name' : dict(zip(texts, names)),
        'name:mapping' : name_mapping,
        'mappings' : mymappings
    }

    #if filename:
        #plt.savefig(filename)

    return fig, plotData
