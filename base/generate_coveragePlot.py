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
from capeplot import CapacityPlot
from capeplot import CapacityData
#from generate_QPlot import compute_capacity
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class CoveragePlot(CapacityPlot):
    def __init__(self, data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui=False, 
                 x_axis=None, y_axis=None, mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis=COVERAGE_PCT.value, mappings=mappings, short_names_path=short_names_path)

    def mk_labels(self):
        df = self.df
        try:
            indices = df[SHORT_NAME]
        except:
            indices = df[NAME]
        memlevel = df[MEM_LEVEL]
        mytext = [str('({0}, {1})'.format(indices[i], memlevel[i])) for i in range(len(indices))]
        return mytext

    def mk_label_key(self):
        return "(name, MaxMemLevel[85%])"

    def draw_contours(self, xmax, ymax, color_labels):
        plt.axvline(x=2)
        plt.axvline(x=8)


def coverage_plot(df, outputfile, scale, title, no_plot, chosen_node_set, variants, gui=False, x_axis=None, y_axis=None, mappings=pd.DataFrame(), short_names_path=''):
    # Normalize the column names
    #df, op_metric_name = compute_capacity(df, chosen_node_set)
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    #df, fig, textData = compute_and_plot('ORIG', df, outputfile, scale, title, no_plot, gui, x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    # Return dataframe and figure for GUI

    data = CapacityData(df)
    data.set_chosen_node_set(chosen_node_set)
    data.compute()
    plot = CoveragePlot(data, 'ORIG', outputfile, scale, title, chosen_node_set, no_plot, gui, 
                        x_axis=x_axis, y_axis=y_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)