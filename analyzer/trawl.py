import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_TRAWL import trawl_plot
from generate_TRAWL import TrawlPlot
from capeplot import CapeData
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class TRAWLData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'TRAWL', x_axis=MetricName.CAP_FP_GFLOP_P_S, y_axis=SPEEDUP_VEC)
    
    # def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("TRAWLData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)
    #     # Generate Plot 

    #     # df = self.df.copy(deep=True)
    #     # df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]
    #     # data = CapeData(df)
    #     # # data.compute()
    #     # plot = TrawlPlot(data, 'ORIG', 'test', scale, 'TRAWL', no_plot=False, 
    #     #                  gui=True, x_axis=x_axis, y_axis=y_axis, 
    #     #                  source_order=loadedData.source_order, mappings=self.mappings, 
    #     #                  short_names_path=self.gui.loadedData.short_names_path)
    #     # plot.compute_and_plot()
    #     # self.fig = plot.fig
    #     # self.plotData = plot.plotData

    #     #trawl_df, self.fig, self.plotData = trawl_plot(self.df.copy(deep=True), 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
    #     #        source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
    #     self.notify_observers()

class TrawlTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, TRAWLData, 'TRAWL', [SPEEDUP_VEC, SPEEDUP_DL1])

    # # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        # self.tableNote.add(self.axesTab, text="Axes")
    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return TrawlPlot()
        # return TrawlPlot(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', 'test', self.analyzerData.scale, 'TRAWL', no_plot=False, 
        #                  gui=True, x_axis=self.analyzerData.x_axis, y_axis=self.analyzerData.y_axis, 
        #                  mappings=self.mappings, 
        #                  short_names_path=self.analyzerData.short_names_path)