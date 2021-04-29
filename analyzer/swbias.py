import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_sw_bias import swbias_plot
from generate_sw_bias import SWbiasPlot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class SWbiasData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'SWbias', x_axis=MetricName.CAP_FP_GFLOP_P_S, y_axis=SPEEDUP_VEC)

class SWbiasTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, SWbiasData, 'SWbias', [SPEEDUP_VEC, SPEEDUP_DL1])

    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return SWbiasPlot()