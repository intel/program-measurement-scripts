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
        # ax.axvline(x=xmax/2)

    def set_plot_scale(self, scale, xmax, ymax, xmin, ymin):
        super().set_plot_scale(scale, xmax, ymax, xmin, ymin)
        if not self.ax.yaxis_inverted():
            self.ax.invert_yaxis()


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