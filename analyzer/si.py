import tkinter as tk
from utils import Observable, resource_path
from analyzer_base import PlotTab, AnalyzerData
import pandas as pd
from generate_SI import parse_ip_df as parse_ip_siplot_df
from generate_SI import SiData
from generate_SI import SiPlot
import copy
import os
import pickle
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab, FilteringTab, DataTab
from metric_names import MetricName
from metric_names import NonMetricName
from sat_analysis import do_sat_analysis as find_si_clusters
globals().update(MetricName.__members__)

class SIPlotData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'SIPlot')
        self.run_cluster = True

    # def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, cluster=resource_path(os.path.join('clusters', 'FE_tier1.csv')), title="FE_tier1", \
    #     filtering=False, filter_data=None, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("SIPlotData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)

    #     # plot = SiPlot (self.siData, 'ORIG', 'SIPLOT', "row", title, 
    #     #                filtering=filtering, filter_data=filter_data, mappings=self.mappings, scale=self.scale, 
    #     #                short_names_path=self.gui.loadedData.short_names_path) 
    #     # plot.compute_and_plot()
    #     # self.fig = plot.fig
    #     # self.plotData = plot.plotData

    #     #siplot_df, self.fig, self.plotData = parse_ip_siplot_df\
    #     #    (self.cluster_df, "FE_tier1", "row", title, chosen_node_set, self.df.copy(deep=True), variants=self.variants, filtering=filtering, filter_data=filter_data, \
    #     #        mappings=self.mappings, scale=scale, short_names_path=self.gui.loadedData.short_names_path)
    #     # Add new metrics to shared dataframe
    #     self.notify_observers()

    def resetRunCluster(self):
        self.run_cluster = True

class SIPlotTab(PlotTab):
    def __init__(self, parent):
        super().__init__(parent, SIPlotData, 'FE_tier1', 'Intensity', 'Saturation',
                         ['Saturation', 'Intensity', 'SI', NonMetricName.SI_CLUSTER_NAME])
        self.cluster = resource_path(os.path.join('clusters', 'FE_tier1.csv'))
    
    # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.clusterTab = ClusterTab(self.tableNote, self)
        # self.filteringTab = FilteringTab(self.tableNote, self)
        # self.tableNote.add(self.clusterTab, text='Clusters')
        # self.tableNote.add(self.filteringTab, text='Filtering')
    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.siDataItems)

    def mk_plot(self):
        # TODO: Work with Elias to use cherry pick rather than passing in filter data
        return SiPlot (self.analyzerData.siDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', 'SIPLOT', "row", 'SIPlot', 
                       filtering=False, filter_data=None, mappings=self.mappings, 
                       scale=self.analyzerData.scale, 
                       short_names_path=self.analyzerData.short_names_path) 

    def resetTablValues(self):
        self.analyzerData.resetRunCluster()