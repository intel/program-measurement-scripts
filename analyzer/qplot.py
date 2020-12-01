import tkinter as tk
from utils import Observable
import pandas as pd
from generate_QPlot import parse_ip_df as parse_ip_qplot_df
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class QPlotData(Observable):
    def __init__(self, loadedData, gui, root):
        super().__init__()
        # Watch for updates in loaded data
        loadedData.add_observers(self)
        self.loadedData = loadedData
        self.df = None
        self.fig = None
        self.ax = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None
        self.mappings = pd.DataFrame()
        self.name = 'QPlot'
        self.gui = gui
        self.root = root

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("QPlotData Notified from ", loadedData)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
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
        # Codelet plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            # TODO: Need to settle how to deal with multiple plots/dataframes
            # May want to let user to select multiple plots to look at within this tab
            # Currently just save the ORIG data
            self.df = df_ORIG if df_ORIG is not None else df_XFORM
            self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Codelet':
                self.gui.c_qplotTab.notify(self)
        
        # source qplot
        if (level == 'All' or level == 'Source'):
            df = loadedData.srcDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.src_mapping, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            self.srcDf = df_ORIG if df_ORIG is not None else df_XFORM
            self.srcFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.srcTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Source':
                self.gui.s_qplotTab.notify(self)

        # application qplot
        if (level == 'All' or level == 'Application'):
            df = loadedData.appDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.app_mapping, variants=variants, short_names_path=self.gui.loadedData.short_names_path)
            self.appDf = df_ORIG if df_ORIG is not None else df_XFORM
            self.appFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.appTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Application':
                self.gui.a_qplotTab.notify(self)

        if level == 'All':
            self.notify_observers()

class QPlotTab(tk.Frame):
    def __init__(self, parent, qplotData, level):
        tk.Frame.__init__(self, parent)
        if qplotData is not None:
           qplotData.add_observers(self)
        self.name = 'QPlot'
        self.level = level
        self.qplotData = self.data = qplotData
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = 'C_max [GB/s]'
        self.current_variants = []
        self.current_labels = []
        # QPlot tab has a paned window with the data tables and qplot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level, self.data.gui, self.data.root)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        # Summary Data Table
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]'])
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

    # plot data to be updated
    def notify(self, qplotData):
        if self.level == 'Codelet':
            df = qplotData.df
            fig = qplotData.fig
            mappings = qplotData.mappings
            variants = qplotData.variants
            textData = qplotData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Source':
            df = qplotData.srcDf
            fig = qplotData.srcFig
            mappings = qplotData.src_mapping
            variants = qplotData.src_variants
            textData = qplotData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Application':
            df = qplotData.appDf
            fig = qplotData.appFig
            mappings = qplotData.app_mapping
            variants = qplotData.app_variants
            textData = qplotData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)