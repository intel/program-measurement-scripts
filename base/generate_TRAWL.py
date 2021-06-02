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
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class TrawlPlot(CapePlot):
    def __init__(self, data=None, loadedData=None, level=None, variant=None, outputfile_prefix=None, scale=None, title=None, no_plot=None, gui=False, x_axis=None, y_axis=None, 
                 mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis=SPEEDUP_DL1.value, mappings=mappings, short_names_path=short_names_path)

    def draw_contours(self, xmax, ymax):
        ax = self.ax
        ax.axvline(x=xmax/2)
        ax.axhline(y=ymax/2)


def trawl_plot(df, outputfile, scale, title, no_plot, variants, gui=False, x_axis=None, y_axis=None, \
    mappings=pd.DataFrame(), short_names_path=''):
    df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    data = CapeData(df)
    data.compute()
    plot = TrawlPlot(data, 
        'ORIG', outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)



