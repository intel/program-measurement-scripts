import tkinter as tk
from utils import Observable
from utils import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_QPlot import parse_ip_df as parse_ip_qplot_df
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class QPlotData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'QPlot')
        # TODO: Try removing all of these attributes
        self.df = None
        self.fig = None
        self.ax = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("QPlotData Notified from ", loadedData)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
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
        df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (self.df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
        self.df = df_ORIG if df_ORIG is not None else df_XFORM
        self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
        self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM
        self.notify_observers()

class QPlotTab(AnalyzerTab):
    def __init__(self, parent, data, level):
        super().__init__(parent)
        if data is not None:
           data.add_observers(self)
        self.name = 'QPlot'
        self.data = data
        self.level = level
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = 'C_max [GB/s]'
        self.current_variants = []
        self.current_labels = []
        # QPlot tab has a paned window with the data tables and qplot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
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
        self.buildTableTabs()
        # Summary Data Table
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]'])
        column_list.extend(self.data.gui.loadedData.common_columns_end)
        self.summaryDf = self.df[column_list]
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
        self.axesTab = AxesTab(self.tableNote, self, 'QPlot')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)