import tkinter as tk
import pandas as pd
from tkinter import ttk
from plot_interaction import PlotInteraction
from utils import Observable, exportCSV, exportXlsx
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab, DataTab
from metric_names import MetricName
import numpy as np
import copy

globals().update(MetricName.__members__)

class AnalyzerData(Observable):
    def __init__(self, loadedData, gui, root, level, name):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.level = level
        self.name = name
        self.gui = gui
        self.root = root
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, update, variants, mappings):
        # mappings
        if not mappings.empty: self.mappings = mappings
        else: self.mappings = loadedData.mappings[self.level]
        # Only show selected variants, default is most frequent variant
        if not variants: self.variants = [loadedData.default_variant]
        else: self.variants = variants
        # Get correct dataframe
        self.df = loadedData.dfs[self.level].copy(deep=True)
    
class AnalyzerTab(tk.Frame):
    def __init__(self, parent, data, title, x_axis, y_axis, extra_metrics):
        super().__init__(parent)
        if data is not None:
            data.add_observers(self)
        self.data = data
        self.level = data.level
        self.name = data.name
        self.title = 'FE_tier1'
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = x_axis
        self.y_axis = self.orig_y_axis = y_axis
        self.variants = []
        self.current_labels = []
        # Each tab has a paned window with the data tables and plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)
        self.extra_metrics = extra_metrics

    def setup(self, metrics):
        # Clear previous plots and meta data tabs TODO: investigate if we can update rather than rebuilding
        for w in self.window.winfo_children():
            w.destroy()
        # Update attributes
        self.df = self.data.df
        self.fig = self.data.fig
        self.mappings = self.data.mappings
        self.variants = self.data.variants
        self.textData = self.data.textData
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, self.df, self.fig, self.textData, self.level, self.data.gui, self.data.root)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Summary Data table
        for missing in set(metrics)-set(self.df.columns):
            self.df[missing] = np.nan
        self.summaryDf = self.df[metrics]
        self.summaryDf = self.summaryDf.sort_values(by=COVERAGE_PCT, ascending=False)
        self.summaryDf.columns = ["{}".format(i) for i in self.summaryDf.columns]

    # Create meta tabs for each plot
    def buildTableTabs(self):
        # Meta tabs
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.dataTab = DataTab(self.tableNote, self.summaryDf)
        self.shortnameTab = ShortNameTab(self.tableNote, self)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.data.loadedData.all_variants, self.variants)
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.dataTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)
        # Summary Export Buttons
        tk.Button(self.dataTab.table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(self.dataTab.summaryTable)).grid(row=0, column=0)
        tk.Button(self.dataTab.table_button_frame, text="Export Summary", command=lambda: exportCSV(self.data.gui.loadedData.summaryDf)).grid(row=0, column=1)
        tk.Button(self.dataTab.table_button_frame, text="Export Summary to Excel", command=lambda: exportXlsx(self.data.gui.loadedData.summaryDf)).grid(row=0, column=2)
        # Initialize meta tabs TODO: do this in the meta tab constructor
        self.shortnameTab.buildLabelTable(self.df, self.shortnameTab)
        if self.level == 'Codelet':
            self.mappingsTab.buildMappingsTab(self.df, self.mappings)


    def get_metrics(self):
        metrics = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        metrics.extend(self.extra_metrics)
        metrics.extend(self.data.gui.loadedData.common_columns_end)
        return metrics
        
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = self.get_metrics()
        self.setup(metrics)
        self.buildTableTabs()