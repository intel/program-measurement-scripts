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
from capeplot import CapeData
from metric_names import MetricName
from statistics import median
import math
import numpy as np
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class ScurvePlot(CapePlot):
    def __init__(self, variant, df, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, 
                 source_order=None, mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(variant, df, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis='C_FLOP [GFlop/s]', mappings=mappings, short_names_path=short_names_path)
    
    def plot_data(self, title, filename, xs, ys, mytexts, scale, df, color_labels, \
        x_axis=None, y_axis=None, mappings=pd.DataFrame()):
        # Scurve doesn't support mappings and x_axis is always 'Rank'
        x_axis = 'Rank'
        mappings = pd.DataFrame()
        # Get scurve points and labels to plot
        self.scurve = Scurve(ys.tolist())
        xs = self.scurve.x_vals
        ys = self.scurve.y_vals
        mytexts = self.scurve.labels
        super().plot_data(title, filename, xs, ys, mytexts, scale, df, color_labels, \
            x_axis, y_axis, mappings)

    def plot_markers_and_labels(self, df, xs, ys, mytexts, color_labels):
        ax = self.ax
        markers = []
        df.reset_index(drop=True, inplace=True)
        for x, y, label in zip(xs, ys, mytexts):
            markers.extend(ax.plot(x, y, marker='o', color='blue', 
                                   label=label, linestyle='', alpha=1))

        texts = [plt.text(x, y, mytext, alpha=1) for x, y, mytext in zip(xs, ys, mytexts)]
        return texts, markers

def scurve_plot(df, outputfile, scale, title, no_plot, variants, gui=False, x_axis=None, y_axis=None, \
    source_order=None, mappings=pd.DataFrame(), short_names_path=''):
    df['C_FLOP [GFlop/s]'] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    plot = ScurvePlot('ORIG', df, outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, source_order=source_order, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)

class Scurve:
    @staticmethod
    def get_bin(value, bin_width, fn=round):
        return fn(value / bin_width) * bin_width
 
    def __init__(self, data, bin_width=0.5):
        min_, max_, median_ = min(data), max(data), median(data)
        head = Scurve.get_bin(min_, bin_width, math.floor)
        last = Scurve.get_bin(max_, bin_width, math.ceil)
        self.y_min = head / median_
        self.y_max = last / median_
        self.n_bins = round((last - head) / bin_width) + 1
        self.bins = [ Scurve.get_bin(x * bin_width + head, bin_width) for x in range(self.n_bins) ]
        self.counts = [ 0 ] * self.n_bins
        for value in data:
            bin = Scurve.get_bin(value, bin_width, math.floor)
            self.counts[min(round(bin / bin_width), self.n_bins - 1)] += 1
        nz_counts = list(filter(lambda t: bool(t[1]), enumerate(self.counts)))
        self.x_vals = list(range(len(nz_counts)))
        self.y_vals = [ self.bins[t[0]] / median_ for t in nz_counts ]
        self.labels = [ t[1] for t in nz_counts ]
        assert(len(self.x_vals) == len(self.y_vals) and len(self.y_vals) == len(self.labels))
        assert(sum(self.labels) == len(data))