import tkinter as tk
import pandas as pd
from tkinter import ttk
from plot_interaction import PlotInteraction
from utils import Observable, exportCSV, exportXlsx
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab, DataTab
from metric_names import MetricName, KEY_METRICS
import numpy as np
import copy
import os
from os.path import expanduser

globals().update(MetricName.__members__)
class PerLevelGuiState:
    def __init__(self, loadedData, level):
        self.level = level
        self.loadedData = loadedData
        # Should have size <= 3
        self.labels = []
        # For data filtering
        # The following variants and filter metric set up a mask to select data point
        self.selectedVariants = []
        self.filterMetric = None
        self.filterMinThreshold = 0
        self.filterMaxThreshold = 0

        # The final mask used to select data points
        self.selectedDataPoints = []

        self.map = pd.DataFrame(columns=KEY_METRICS + [MetricName.VARIANT, 'Color'])
        # A map from color to color name for plotting
        self.colorDict = {}

        # Cape paths
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.short_names_path = os.path.join(self.cape_path, 'short_names.csv')
        self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')

    # Write methods to update the fields and then call 
    # self.loadedData.levelData[level].updated() to notify all observers
    def add_mapping(self, toAdd):
        all_mappings = pd.read_csv(self.mappings_path)
        all_mappings = all_mappings.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)
        all_mappings.to_csv(self.mappings_path, index=False)
        self.loadedData.mapping = self.loadedData.mapping.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)

    def remove_mapping(self, toRemove):
        all_mappings = pd.read_csv(self.mappings_path)
        to_update = [all_mappings, self.loadedData.mapping]
        for mapping in to_update:
            mapping.drop(mapping[(mapping['Before Name']==toRemove['Before Name'].iloc[0]) & \
                        (mapping['Before Timestamp']==toRemove['Before Timestamp'].iloc[0]) & \
                        (mapping['After Name']==toRemove['After Name'].iloc[0]) & \
                        (mapping['After Timestamp']==toRemove['After Timestamp'].iloc[0])].index, inplace=True)
        all_mappings.to_csv(self.mappings_path, index=False)

class AnalyzerData(Observable):
    def __init__(self, loadedData, gui, root, level, name):
        super().__init__()
        self.loadedData = loadedData
    #    self.mappings = pd.DataFrame()
        self.level = level
        self.name = name
        self.gui = gui
        self.root = root
        self.scale = "linear"
        self.x_axis = None
        self.y_axis = None
        # Watch for updates in loaded data
        loadedData.add_observers(self)
        loadedData.levelData[level].add_observers(self)

    # Make df a property that refer to the right dataframe
    @property
    def df(self):
        # Get correct dataframe
        return self.loadedData.get_df(self.level)

    @property
    def mappings(self):
        return self.loadedData.get_mapping(self.level)

    @property
    def capacityData(self):
        return self.loadedData.levelData[self.level].capacityData

    @property
    def siData(self):
        return self.loadedData.levelData[self.level].siData
        
    @property
    def satAnalysisData(self):
        return self.loadedData.levelData[self.level].satAnalysisData

    def notify(self, loadedData, update, variants, mappings):
        # mappings

        #if not mappings.empty: self.mappings = mappings
        #else: self.mappings = loadedData.mappings[self.level]

        # Only show selected variants, default is most frequent variant
        if not variants: self.variants = [self.loadedData.default_variant]
        else: self.variants = variants
        # Get correct dataframe

    def merge_metrics(self, df, metrics):
        self.loadedData.merge_metrics(df, metrics, self.level)
    
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

    @property
    def mappings(self):
        return self.data.mappings

    # TODO: Bring this back
    # TODO: request Elias to move non-tkinter data to Data object for cleaner
    #       MVC design
    #@property
    #def variants(self):
    #    return self.data.variants

    # Subclass needs to override this method
    def mk_plot(self):
        raise Exception("Method needs to be overriden to create plots")
    
    def setup(self, metrics):
        # Clear previous plots and meta data tabs TODO: investigate if we can update rather than rebuilding
        for w in self.window.winfo_children():
            w.destroy()
        # Update attributes
        plot = self.mk_plot()
        plot.compute_and_plot()
        self.fig, self.textData = plot.fig, plot.plotData
        #self.textData = self.data.textData

        self.df = self.data.df
        # self.mappings = self.data.mappings
        self.variants = self.data.variants
        self.metrics = metrics
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, self.df.loc[self.df[VARIANT].isin(self.variants)].reset_index(drop=True), self.fig, self.textData, self.level, self.data.gui, self.data.root)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Format columns for pandastable compatibility
        self.df.columns = ["{}".format(i) for i in self.df.columns]
        self.df.sort_values(by=COVERAGE_PCT, ascending=False, inplace=True)
        for missing in set(metrics)-set(self.df.columns):
            self.df[missing] = np.nan

    # Create meta tabs for each plot
    def buildTableTabs(self):
        # Meta tabs
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.dataTab = DataTab(self.tableNote, self.df, self.metrics, self.variants)
        self.shortnameTab = ShortNameTab(self.tableNote, self, self.df.loc[self.df[VARIANT].isin(self.variants)].reset_index(drop=True))
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
        self.shortnameTab.buildLabelTable()
        if self.level == 'Codelet':
            self.mappingsTab.buildMappingsTab()


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