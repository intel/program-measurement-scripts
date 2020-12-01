import tkinter as tk
from utils import Observable
from utils import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_coveragePlot import coverage_plot
import copy
from tkinter import ttk
from xlsxgen import XlsxGenerator
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, GuideTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class CoverageData(AnalyzerData):
    def __init__(self, loadedData, gui, root):
        super().__init__(loadedData, gui, root, 'Summary')
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("CoverageData Notified from ", loadedData)
        # use qplot dataframe to generate the coverage plot
        df = loadedData.summaryDf.copy(deep=True)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        # Only show selected variants, default is most frequent variant
        if not variants: variants = [loadedData.default_variant]
        if not update: # Get all unique variants upon first load
            self.variants = df[VARIANT].dropna().unique()
        # mappings
        if mappings.empty:
            self.mappings = loadedData.mapping
        else:
            self.mappings = mappings
        df, fig, texts = coverage_plot(df, "test", scale, "Coverage", False, chosen_node_set, gui=True, x_axis=x_axis, y_axis=y_axis, mappings=self.mappings, \
            variants=variants, short_names_path=self.gui.loadedData.short_names_path)
        self.df = df
        self.fig = fig
        self.textData = texts
        self.notify_observers()

class SummaryTab(AnalyzerTab):
    def __init__(self, parent, coverageData, level):
        super().__init__(parent)
        if coverageData is not None:
           coverageData.add_observers(self)
        self.coverageData = self.data = coverageData
        self.name = 'Summary'
        self.level = level
        self.current_variants = []
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = COVERAGE_PCT
        self.current_labels = []
        self.parent = parent
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                    sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level, self.data.gui, self.data.root)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        column_list.extend(self.data.gui.loadedData.common_columns_end)
        self.summaryDf = df[column_list]
        self.summaryDf = self.summaryDf.sort_values(by=COVERAGE_PCT, ascending=False)
        self.summaryDf.columns = ["{}".format(i) for i in self.summaryDf.columns]
        summary_pt = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summary_pt)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.exportCSV()).grid(row=0, column=1)
        tk.Button(table_button_frame, text="Export Summary to Excel", command=lambda: self.exportXlsx()).grid(row=0, column=2)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        self.mappingsTab.buildMappingsTab(df, mappings)

    def exportCSV(self):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        self.data.gui.loadedData.summaryDf.drop(columns=['Color']).to_csv(export_file_path, index=False, header=True)
    
    def exportXlsx(self):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.xlsx')
        # To be moved to constructor later (after refactoring?)
        xlsxgen = XlsxGenerator()
        xlsxgen.set_header("single")
        xlsxgen.set_scheme("general")
        xlsxgen.from_dataframe("data", self.data.gui.loadedData.summaryDf, export_file_path)

    # Create tabs for data and labels
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote, self)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'Summary')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        #TODO: find better way to display guideTab only when we have the required analytic metrics as now UVSQ has different analytics
        # Not displaying guideTab yet as we still need to define functions
        if False and not self.data.gui.urls and self.data.gui.loadedData.analytic_columns and set(self.data.gui.loadedData.analytic_columns).issubset(self.data.gui.loadedData.summaryDf.columns):
            self.guideTab = GuideTab(self.tableNote, self)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        if False and not self.data.gui.urls and self.data.gui.loadedData.analytic_columns and set(self.data.gui.loadedData.analytic_columns).issubset(self.data.gui.loadedData.summaryDf.columns): 
            self.tableNote.add(self.guideTab, text='Guide')
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    def notify(self, coverageData):
        for w in self.window.winfo_children():
            w.destroy()
        try: self.guideTab.destroy()
        except: pass

        self.update(coverageData.df, coverageData.fig, coverageData.textData, coverageData.mappings, coverageData.variants)