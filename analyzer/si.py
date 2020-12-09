import tkinter as tk
from utils import Observable, resource_path
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_SI import parse_ip_df as parse_ip_siplot_df
import copy
import os
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab, DataTab
from metric_names import MetricName
from sat_analysis import find_clusters as find_si_clusters
globals().update(MetricName.__members__)


# Sample dummy call to SI script to show how it would work
#df = pd.DataFrame([[1, 2], [3, 4]], columns=list('AB'))
#clusters = find_si_clusters(df)

class SIPlotData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'SIPlot')

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, cluster=resource_path(os.path.join('clusters', 'FE_tier1.csv')), title="FE_tier1", \
        filtering=False, filter_data=None, scale='linear', level='All', mappings=pd.DataFrame()):
        print("SIPlotData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        #cluster_df = find_clusters(self.df)
        cluster_df = pd.read_csv(cluster)
        self.df, self.fig, self.textData = parse_ip_siplot_df\
            (cluster_df, "FE_tier1", "row", title, chosen_node_set, self.df, variants=self.variants, filtering=filtering, filter_data=filter_data, \
                mappings=self.mappings, scale=scale, short_names_path=self.gui.loadedData.short_names_path)
        # Add new metrics to shared dataframe
        self.loadedData.dfs[self.level].drop(columns=['Saturation', 'Intensity'], inplace=True, errors='ignore')
        self.loadedData.dfs[self.level] = pd.merge(self.loadedData.dfs[self.level], self.df[[NAME, TIMESTAMP, 'Saturation', 'Intensity']], on=[NAME, TIMESTAMP], how='left')
        # TODO: Fix analytic variables being dropped in 'def compute_extra' in generate_SI.py
        if not loadedData.analytics.empty:
            self.df.drop(columns=loadedData.analytic_columns, errors='ignore', inplace=True)
            self.df = pd.merge(left=self.df, right=loadedData.summaryDf[loadedData.analytic_columns + [NAME, TIMESTAMP]], on=[NAME, TIMESTAMP], how='left')
        self.notify_observers()

class SIPlotTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'FE_tier1', 'Intensity', 'Saturation')
        self.cluster = resource_path(os.path.join('clusters', 'FE_tier1.csv'))
    
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        metrics.extend(['Saturation', 'Intensity', 'SI'])
        metrics.extend(self.data.gui.loadedData.common_columns_end)
        super().setup(metrics)
        self.buildTableTabs()

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.clusterTab = ClusterTab(self.tableNote, self)
        self.filteringTab = FilteringTab(self.tableNote, self)
        self.tableNote.add(self.clusterTab, text='Clusters')
        self.tableNote.add(self.filteringTab, text='Filtering')
        