import tkinter as tk
from utils import Observable
from utils import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_TRAWL import trawl_plot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class TRAWLData(AnalyzerData):
    def __init__(self, loadedData, gui, root):
        super().__init__(loadedData, gui, root, 'TRAWL')
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("TRAWLData Notified from ", loadedData)
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
        # Get all unique variants upon first load
        if not update: self.variants = loadedData.summaryDf['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()
        # Codelet trawl plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            self.df = df
            self.fig = fig
            self.textData = textData
            if level == 'Codelet':
                self.gui.c_trawlTab.notify(self)

        # source trawl plot
        if level == 'All' or level == 'Source':
            df = loadedData.srcDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.src_mapping, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData
            if level == 'Source':
                self.gui.s_trawlTab.notify(self)

        # application trawl plot
        if level == 'All' or level == 'Application':
            df = loadedData.appDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.app_mapping, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData
            if level == 'Application':
                self.gui.a_trawlTab.notify(self)

        if level == 'All':
            self.notify_observers()

class TrawlTab(AnalyzerTab):
    def __init__(self, parent, trawlData, level):
        super().__init__(parent)
        if trawlData is not None:
           trawlData.add_observers(self)
        self.name = 'TRAWL'
        self.level = level
        self.trawlData = self.data = trawlData
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = SPEEDUP_VEC
        self.current_variants = []
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level, self.data.gui, self.data.root)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend([SPEEDUP_VEC, SPEEDUP_DL1])
        column_list.extend(self.data.gui.loadedData.common_columns_end)
        self.summaryDf = df[column_list]
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

    # Create tabs for TRAWL Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote, self)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, trawlData):
        if self.level == 'Codelet':
            df = trawlData.df
            fig = trawlData.fig
            mappings = trawlData.mappings
            variants = trawlData.variants
            textData = trawlData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

        elif self.level == 'Source':
            df = trawlData.srcDf
            fig = trawlData.srcFig
            mappings = trawlData.src_mapping
            variants = trawlData.src_variants
            textData = trawlData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

        elif self.level == 'Application':
            df = trawlData.appDf
            fig = trawlData.appFig
            mappings = trawlData.app_mapping
            variants = trawlData.app_variants
            textData = trawlData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)