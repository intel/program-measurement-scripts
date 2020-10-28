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
#from generate_QPlot import compute_capacity
import copy
from capeplot import CapacityPlot
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class CustomPlot(CapacityPlot):
    def __init__(self, variant, df, outputfile_prefix, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None, mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(COVERAGE_PCT.value, chosen_node_set)
        self.variant = variant
        self.df = df 
        self.outputfile_prefix = outputfile_prefix 
        self.scale = scale
        self.title = title
        self.no_plot = no_plot
        self.gui = gui
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.mappings = mappings
        self.short_names_path = short_names_path

def custom_plot(df, outputfile, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, \
    variants=['ORIG'], mappings=pd.DataFrame(), short_names_path=''):
    chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
    #df, op_metric_name = compute_capacity(df, chosen_node_set)
    if not mappings.empty:
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
        'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
    df['C_FLOP [GFlop/s]'] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)]
    # df, fig, plotData = compute_and_plot(
    #     'ORIG', df, outputfile, scale, title, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    # Return dataframe and figure for GUI
    plot = CustomPlot(
        'ORIG', df, outputfile, scale, title, chosen_node_set, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)


