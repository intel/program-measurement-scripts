#!/usr/bin/python3
import pandas as pd
import numpy as np
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from matplotlib import style
import copy
from capeplot import CapePlot
from capedata import CapeData
from metric_names import MetricName
from statistics import median
import math
import numpy as np
from metric_names import KEY_METRICS
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class ScurveAllPlot(CapePlot):
    def __init__(self, data=None, loadedData=None, level=None, variant=None, outputfile_prefix=None, scale=None, title=None, no_plot=None, gui=False, x_axis=None, y_axis=None, 
                 mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis=MetricName.CAP_FP_GFLOP_P_S, mappings=mappings, short_names_path=short_names_path)
    
    def plot_data(self, title, filename, xs, ys, mytexts, scale, df, \
        x_axis=None, y_axis=None, mappings=pd.DataFrame()):
        # Scurve doesn't support mappings
        mappings = pd.DataFrame()
        # Get median value of data
        self.median = median(ys.tolist())
        mytext = self.mk_labels()
        # Created a rank order by sorting the values and using their new index as the x-axis
        temp_df = pd.DataFrame()
        temp_df['y-metric'] = ys
        temp_df['label'] = mytext
        # Need to add the key metrics so we can label/color the sorted points
        temp_df[NAME] = self.df[NAME]
        temp_df[TIMESTAMP] = self.df[TIMESTAMP]
        temp_df = temp_df.sort_values(by=['y-metric'])
        temp_df['x-metric'] = [i for i in range(len(ys))]
        self.ordered_key_metrics = temp_df[[NAME, TIMESTAMP]]
        x_axis = x_axis if x_axis else self.default_x_axis
        x_axis = 'Rank Order (' + x_axis + ')'
        #nonNullMask=~temp_df['y-metric'].isnull()
        super().plot_data(title, filename, temp_df['x-metric'], temp_df['y-metric'], 
                          temp_df['label'], scale, df, x_axis, y_axis, mappings)

    def get_names(self):
        return self.guiState.get_encoded_names(self.df.sort_values(by=[self.x_axis])).tolist()

    def get_min_max(self, xs, ys):
        x_largestNonNull = xs[~ys.isnull()].max()
        xmin, xmax, ymin, ymax = super().get_min_max(xs, ys)
        return xmin, min(xmax, x_largestNonNull), ymin, ymax

    def mk_mappings(self, mappings, df, x_axis, y_axis, xmax, ymax):
        # Mappings implementation not ready yet for s-curve
        return dict(), []

    def plot_markers_and_labels(self, df, xs, ys, mytexts):
        ax = self.ax
        markers = []
        self.ordered_key_metrics.drop(columns=['Color'], inplace=True, errors='ignore')
        sorted_color_map = pd.merge(left=self.ordered_key_metrics, right=self.color_map[KEY_METRICS + ['Color']], on=KEY_METRICS, how='left')
        for x, y, color, name, timestamp in zip(xs, ys, sorted_color_map['Color'], sorted_color_map[NAME], sorted_color_map[TIMESTAMP]):
            markers.extend(ax.plot(x, y, marker='o', color=color, 
                                   label=name+str(timestamp), linestyle='', alpha=1))

        texts = [self.ax.text(x, y, mytext, alpha=1) for x, y, mytext in zip(xs, ys, mytexts)]
        return texts, markers

    def draw_contours(self, xmax, ymax):
        ax = self.ax
        ax.axhline(y=self.median)

def scurve_all_plot(df, outputfile, scale, title, no_plot, variants, gui=False, x_axis=None, y_axis=None, \
    mappings=pd.DataFrame(), short_names_path=''):
    df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    data = CapeData(df)
    data.compute()
    plot = ScurveAllPlot(data, 'ORIG', outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)