import tkinter as tk
from utils import Observable, resource_path
from utils import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_SI import parse_ip_df as parse_ip_siplot_df
import copy
import os
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab
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
        # mappings
        if not mappings.empty: self.mappings = mappings
        else: self.mappings = loadedData.mappings[self.level]
        # Only show selected variants, default is most frequent variant
        if not variants: variants = [loadedData.default_variant]
        # Get correct dataframe
        self.df = loadedData.dfs[self.level].copy(deep=True)
        # Get all unique variants upon first load
        if not update: self.variants = self.df['Variant'].dropna().unique()
        # Generate Plot
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        self.df, self.fig, self.textData = parse_ip_siplot_df\
            (cluster, "FE_tier1", "row", title, chosen_node_set, self.df, variants=variants, filtering=filtering, filter_data=filter_data, \
                mappings=self.mappings, scale=scale, short_names_path=self.gui.loadedData.short_names_path)
        # Add saturation and intensity to shared dataframe for custom tab to use
        loadedData.summaryDf['Saturation'] = self.df['Saturation']
        loadedData.summaryDf['Intensity'] = self.df['Intensity']
        # TODO: Fix analytic variables being dropped in 'def compute_extra' in generate_SI.py
        if not loadedData.analytics.empty:
            self.df.drop(columns=loadedData.analytic_columns, errors='ignore', inplace=True)
            self.df = pd.merge(left=self.df, right=loadedData.summaryDf[loadedData.analytic_columns + [NAME, TIMESTAMP]], on=[NAME, TIMESTAMP], how='left')
        self.notify_observers()

class SIPlotTab(AnalyzerTab):
    def __init__(self, parent, data, level):
        super().__init__(parent)
        if data is not None:
            data.add_observers(self)
        self.name = 'SIPlot'
        self.level = level
        self.data = data
        self.cluster = resource_path(os.path.join('clusters', 'FE_tier1.csv'))
        self.title = 'FE_tier1'
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'Intensity'
        self.y_axis = self.orig_y_axis = 'Saturation'
        self.current_variants = []
        self.current_labels = []
        # SIPlot tab has a paned window with the data tables and sipLot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)
    
    def notify(self, data):
        # Clear previous plots and meta data tabs TODO: investigate if we can update rather than rebuilding
        for w in self.window.winfo_children():
            w.destroy()
        # Update attributes
        self.df = data.df
        self.fig = data.fig
        self.mappings = data.mappings
        self.variants = data.variants
        self.textData = data.textData
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, self.df, self.fig, self.textData, self.level, self.data.gui, self.data.root)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Summary Data table
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend(['Saturation', 'Intensity', 'SI'])
        column_list.extend(self.data.gui.loadedData.common_columns_end)
        self.summaryDf = self.df[column_list]
        self.buildTableTabs() # TODO: see if we can move this to plot/table setup
        self.summaryDf = self.summaryDf.sort_values(by=COVERAGE_PCT, ascending=False)
        self.summaryDf.columns = ["{}".format(i) for i in self.summaryDf.columns]
        summaryTable = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.data.gui.summaryTab.exportCSV()).grid(row=0, column=1)
        
        self.shortnameTab.buildLabelTable(self.df, self.shortnameTab)
        if self.level == 'Codelet':
            self.mappingsTab.buildMappingsTab(self.df, self.mappings)

    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote, self)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.clusterTab = ClusterTab(self.tableNote, self)
        self.filteringTab = FilteringTab(self.tableNote, self)
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.clusterTab, text='Clusters')
        self.tableNote.add(self.filteringTab, text='Filtering')
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)