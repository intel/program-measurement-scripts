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
from metric_names import MetricName, NonMetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class SWbiasPlot(CapePlot):
    def __init__(self, data=None, loadedData=None, level=None, variant=None, outputfile_prefix=None, scale=None, title=None, no_plot=None, gui=False, x_axis=None, y_axis=None, 
                 mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis=NonMetricName.SI_TIER_NORMALIZED, mappings=mappings, short_names_path=short_names_path)

    def draw_contours(self, xmax, ymax):
        ax = self.ax
        # ax.axvline(x=0)

    def set_plot_scale(self, scale):
        super().set_plot_scale(scale)
        self.xmin = 0 if self.xmin > 0 else self.xmin
        self.xmax = 0 if self.xmax < 0 else self.xmax
        self.ax.set_xlim((self.xmin, self.xmax))
        self.ax.set_ylim((0, self.ymax))
        # if not self.ax.yaxis_inverted():
        #     self.ax.invert_yaxis()
        self.ax.spines['left'].set_position('zero')
        self.ax.spines['top'].set_color('none')
        self.ax.spines['right'].set_color('none')

def swbias_plot(df, outputfile, scale, title, no_plot, variants, gui=False, x_axis=None, y_axis=None, \
    mappings=pd.DataFrame(), short_names_path=''):
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    data = CapeData(df)
    data.compute()
    plot = SWbiasPlot(data, 
        'ORIG', outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)