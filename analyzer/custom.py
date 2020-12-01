import tkinter as tk
from utils import Observable
import pandas as pd
from generate_custom import custom_plot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class CustomData(Observable):
    def __init__(self, loadedData, gui, root):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'Custom'
        self.gui = gui
        self.root = root
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("CustomData Notified from ", loadedData)
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
        # codelet custom plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
            self.df = df
            self.fig = fig
            self.textData = textData
            if level == 'Codelet':
                self.gui.c_customTab.notify(self)

        # source custom plot
        if (level == 'All' or level == 'Source'):
            df = loadedData.srcDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants, mappings=self.src_mapping, short_names_path=self.gui.loadedData.short_names_path)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData
            if level == 'Source':
                self.gui.s_customTab.notify(self)

        # application custom plot
        if (level == 'All' or level == 'Application'):
            df = loadedData.appDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants, mappings=self.app_mapping, short_names_path=self.gui.loadedData.short_names_path)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData
            if level == 'Application':
                self.gui.a_customTab.notify(self)

        if level == 'All':
            self.notify_observers()

class CustomTab(tk.Frame):
    def __init__(self, parent, customData, level):
        tk.Frame.__init__(self, parent)
        if customData is not None:
            customData.add_observers(self)
        self.name = 'Custom'
        self.level = level
        self.customData = self.data = customData
        self.current_variants = []
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = COVERAGE_PCT
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, variants=None, mappings=pd.DataFrame()):
        self.variants = variants
        self.mappings = mappings
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level, self.data.gui, self.data.root)
        # Data table/tabs under plot setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        self.summaryDf = df
        self.summaryDf.columns = ["{}".format(i) for i in self.summaryDf.columns]
        self.summaryDf = self.summaryDf.sort_values(by=COVERAGE_PCT, ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summary_pt)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.data.gui.summaryTab.exportCSV()).grid(row=0, column=1)
        
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if self.level == 'Codelet':
            self.mappingsTab.buildMappingsTab(df, mappings)
    
    # Create tabs for Custom Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote, self)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, customData):
        if self.level == 'Codelet':
            df = customData.df
            fig = customData.fig
            mappings = customData.mappings
            variants = customData.variants
            textData = customData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)

        elif self.level == 'Source':
            df = customData.srcDf
            fig = customData.srcFig
            mappings = customData.src_mapping
            variants = customData.src_variants
            textData = customData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)

        elif self.level == 'Application':
            df = customData.appDf
            fig = customData.appFig
            mappings = customData.app_mapping
            variants = customData.app_variants
            textData = customData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)