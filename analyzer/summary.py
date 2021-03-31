import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, AnalyzerData
import pandas as pd
from capeplot import CapacityData
from generate_coveragePlot import coverage_plot
from generate_coveragePlot import CoveragePlot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab, GuideTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class CoverageData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Summary')
    
    # def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("CoverageData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)
    #     # Generate Plot
    #     #chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])

    #     #df0 = self.df.copy(deep=True)
    #     #data = CapacityData(df0)
    #     #data.set_chosen_node_set(chosen_node_set)
    #     # data.compute()
    #     #self.merge_metrics(data.df, [MetricName.CAP_L3_GB_P_S, MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S, MetricName.CAP_FP_GFLOP_P_S])


    #     # plot = CoveragePlot(self.capacityData, 'ORIG', "test", scale, "Coverage", no_plot=False, gui=True, 
    #     #                     x_axis=None, y_axis=None, mappings=self.mappings)
    #     # plot.compute_and_plot()
    #     # self.fig = plot.fig
    #     # self.plotData = plot.plotData
        
    #     #coverage_df, self.fig, self.plotData = coverage_plot(self.df.copy(deep=True), "test", scale, "Coverage", False, chosen_node_set, gui=True, x_axis=x_axis, y_axis=y_axis, mappings=self.mappings, \
    #     #    variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
    #     self.notify_observers()

class SummaryTab(PlotTab):
    def __init__(self, parent):
        super().__init__(parent, CoverageData, 'Summary', MetricName.CAP_FP_GFLOP_P_S, COVERAGE_PCT, [])

    def notify(self, data):
        super().notify(data)

    # # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
    #     # self.axesTab = AxesTab(self.tableNote, self, 'Summary')
        # self.tableNote.add(self.axesTab, text="Axes")
        #TODO: find better way to display guideTab only when we have the required analytic metrics as now UVSQ has different analytics
        # self.guideTab = GuideTab(self.tableNote, self)
        # self.tableNote.add(self.guideTab, text='Guide')
    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return CoveragePlot(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', "test", self.analyzerData.scale, "Coverage", no_plot=False, gui=True, 
                            x_axis=self.analyzerData.x_axis, y_axis=self.analyzerData.y_axis, mappings=self.mappings)
