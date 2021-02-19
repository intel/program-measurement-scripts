import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from capeplot import CapacityData
from generate_coveragePlot import coverage_plot
from generate_coveragePlot import CoveragePlot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, GuideTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class CoverageData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'Summary')
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("CoverageData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot
        #chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])

        #df0 = self.df.copy(deep=True)
        #data = CapacityData(df0)
        #data.set_chosen_node_set(chosen_node_set)
        # data.compute()
        #self.merge_metrics(data.df, ['C_L3 [GB/s]', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]', 'C_FLOP [GFlop/s]'])


        # plot = CoveragePlot(self.capacityData, 'ORIG', "test", scale, "Coverage", no_plot=False, gui=True, 
        #                     x_axis=None, y_axis=None, mappings=self.mappings)
        # plot.compute_and_plot()
        # self.fig = plot.fig
        # self.textData = plot.plotData
        
        #coverage_df, self.fig, self.textData = coverage_plot(self.df.copy(deep=True), "test", scale, "Coverage", False, chosen_node_set, gui=True, x_axis=x_axis, y_axis=y_axis, mappings=self.mappings, \
        #    variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class SummaryTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'Summary', 'C_FLOP [GFlop/s]', COVERAGE_PCT, [])

    def notify(self, data):
        # GuideTab currently in development so sometimes a child and sometimes not
        try: self.guideTab.destroy()
        except: pass
        super().notify(data)

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'Summary')
        self.tableNote.add(self.axesTab, text="Axes")
        #TODO: find better way to display guideTab only when we have the required analytic metrics as now UVSQ has different analytics
        # if not self.data.gui.urls and self.data.gui.loadedData.analytic_columns and set(self.data.gui.loadedData.analytic_columns).issubset(self.data.gui.loadedData.summaryDf.columns):
        self.guideTab = GuideTab(self.tableNote, self)
        # if not self.data.gui.urls and self.data.gui.loadedData.analytic_columns and set(self.data.gui.loadedData.analytic_columns).issubset(self.data.gui.loadedData.summaryDf.columns): 
        self.tableNote.add(self.guideTab, text='Guide')

    def mk_plot(self):
        return CoveragePlot(self.data.capacityData, 'ORIG', "test", self.data.scale, "Coverage", no_plot=False, gui=True, 
                            x_axis=None, y_axis=None, mappings=self.mappings)
