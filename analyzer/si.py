import tkinter as tk
from utils import Observable, resource_path
import pandas as pd
from generate_SI import parse_ip_df as parse_ip_siplot_df
import copy
import os
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class SIPlotData(Observable):
    def __init__(self, loadedData, gui, root):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'SIPlot'
        self.gui = gui
        self.root = root
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, cluster=resource_path(os.path.join('clusters', 'FE_tier1.csv')), title="FE_tier1", \
        filtering=False, filter_data=None, scale='linear', level='All', mappings=pd.DataFrame()):
        print("SIPlotData Notified from ", loadedData)
        df = loadedData.summaryDf.copy(deep=True)
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        # mappings
        if mappings.empty:
            self.mappings = loadedData.mapping
            self.src_mapping = loadedData.src_mapping
            self.app_mapping = loadedData.app_mapping
        else:
            self.mappings = mappings
            self.src_mapping = mappings
            self.app_mapping = mappings
        # Only show selected variants, default is most frequent variant
        if not variants: variants = [loadedData.default_variant]
        # Plot only at Codelet level for now
        if not update: self.variants = df['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()

        df_ORIG, fig_ORIG, textData_ORIG = parse_ip_siplot_df\
            (cluster, "FE_tier1", "row", title, chosen_node_set, df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=self.mappings, scale=scale, short_names_path=self.gui.loadedData.short_names_path)
        self.df = df_ORIG
        loadedData.summaryDf = pd.merge(left=loadedData.summaryDf, right=self.df[[NAME, TIMESTAMP, 'Saturation', 'Intensity']], on=[NAME, TIMESTAMP], how='left')
        self.fig = fig_ORIG
        self.textData = textData_ORIG

        # TODO: Fix analytic variables being dropped in 'def compute_extra' in generate_SI.py
        if not loadedData.analytics.empty:
            self.df.drop(columns=loadedData.analytic_columns, errors='ignore', inplace=True)
            self.df = pd.merge(left=self.df, right=loadedData.summaryDf[loadedData.analytic_columns + [NAME, TIMESTAMP]], on=[NAME, TIMESTAMP], how='left')

        self.notify_observers()

class SIPlotTab(tk.Frame):
    def __init__(self, parent, siplotData, level):
        tk.Frame.__init__(self, parent)
        if siplotData is not None:
            siplotData.add_observers(self)
        self.name = 'SIPlot'
        self.level = level
        self.siplotData = self.data = siplotData
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
    
    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot/Table Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level, self.data.gui, self.data.root)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Summary Data table
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend(['Saturation', 'Intensity', 'SI'])
        # column_list.extend(['Saturation', 'Intensity', 'SI', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
        #       'C_RAM [GB/s]', 'C_max [GB/s]'])
        column_list.extend(self.data.gui.loadedData.common_columns_end)
        self.summaryDf = df[column_list]
        self.buildTableTabs()
        self.summaryDf = self.summaryDf.sort_values(by=COVERAGE_PCT, ascending=False)
        self.summaryDf.columns = ["{}".format(i) for i in self.summaryDf.columns]
        summaryTable = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.data.gui.summaryTab.exportCSV()).grid(row=0, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if self.level == 'Codelet':
            self.mappingsTab.buildMappingsTab(df, mappings)

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

    # plot data to be updated
    def notify(self, siplotData):
        for w in self.window.winfo_children():
            w.destroy()
        self.update(siplotData.df, siplotData.fig, textData=siplotData.textData, mappings=siplotData.mappings, variants=siplotData.variants)