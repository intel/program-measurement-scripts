import tkinter as tk
import graphviz
import pandas as pd
import os
import copy
import operator
from os.path import expanduser
from tkinter import messagebox
from pandastable import Table
from transitions.extensions import GraphMachine as Machine
from transitions import State
from utils import center, Observable, resource_path, exportCSV, exportXlsx
from analyzer_base import AnalyzerTab, AnalyzerData 
# from plot_interaction import ChecklistBox
from metric_names import MetricName
from metric_names import NonMetricName, KEY_METRICS
globals().update(MetricName.__members__)

class AxesTab(tk.Frame):
    @staticmethod
    def custom_axes(parent, var, gui):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        # TRAWL
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='TRAWL', menu=menu)
        for metric in [SPEEDUP_VEC, SPEEDUP_DL1, MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S, VARIANT]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # QPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='QPlot', menu=menu)
        for metric in [MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_L3_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S, MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # SIPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='SIPlot', menu=menu)
        for metric in ['Saturation', 'Intensity']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Speedups (If mappings):
        # if not parent.tab.mappings.empty:
        #     menu = tk.Menu(main_menu, tearoff=False)
        #     main_menu.add_cascade(label='Speedups', menu=menu)
        #     for metric in [SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']:
        #         menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Diagnostic Variables
        # if gui.loadedData.analytic_columns and set(gui.loadedData.analytic_columns).issubset(gui.loadedData.summaryDf.columns):
        #     menu = tk.Menu(main_menu, tearoff=False)
        #     main_menu.add_cascade(label='Diagnostics', menu=menu)
        #     for metric in gui.loadedData.analytic_columns:
        #         menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='Summary', menu=summary_menu)
        metrics = [[COVERAGE_PCT, TIME_APP_S, TIME_LOOP_S],
                    [NUM_CORES, DATA_SET, PREFETCHERS, REPETITIONS],
                    [E_PKG_J, E_DRAM_J, E_PKGDRAM_J], 
                    [P_PKG_W, P_DRAM_W, P_PKGDRAM_W],
                    [COUNT_INSTS_GI, RATE_INST_GI_P_S],
                    [RATE_L1_GB_P_S, RATE_L2_GB_P_S, RATE_L3_GB_P_S, RATE_RAM_GB_P_S, RATE_FP_GFLOP_P_S, RATE_INST_GI_P_S, RATE_REG_ADDR_GB_P_S, RATE_REG_DATA_GB_P_S, RATE_REG_SIMD_GB_P_S, RATE_REG_GB_P_S],
                    [COUNT_OPS_VEC_PCT, COUNT_OPS_FMA_PCT, COUNT_OPS_DIV_PCT, COUNT_OPS_SQRT_PCT, COUNT_OPS_RSQRT_PCT, COUNT_OPS_RCP_PCT],
                    [COUNT_INSTS_VEC_PCT, COUNT_INSTS_FMA_PCT, COUNT_INSTS_DIV_PCT, COUNT_INSTS_SQRT_PCT, COUNT_INSTS_RSQRT_PCT, COUNT_INSTS_RCP_PCT],
                    gui.loadedData.summaryDf.columns.tolist()]
        # TODO: Get all other metrics not in a pre-defined category and put in Misc instead of All
        categories = ['Time/Coverage', 'Experiment Settings', 'Energy', 'Power', 'Instructions', 'Rates', r'%ops', r'%inst', 'All']
        for index, category in enumerate(categories):
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics[index]:
                if metric in gui.loadedData.summaryDf.columns:
                    menu.add_radiobutton(value=metric, label=metric, variable=var)
        return menubutton

    def __init__(self, parent, tab, plotType):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.plotType = plotType
        # Axes metric options
        metric_label = tk.Label(self, text='Metrics:')
        self.y_selected = tk.StringVar(value='Choose Y Axis Metric')
        self.x_selected = tk.StringVar(value='Choose X Axis Metric')
        x_options = ['Choose X Axis Metric', MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S]
        if self.plotType == 'Custom' or self.plotType == 'Scurve':
            x_menu = AxesTab.custom_axes(self, self.x_selected, self.tab.data.gui)
            y_menu = AxesTab.custom_axes(self, self.y_selected, self.tab.data.gui)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['Choose Y Axis Metric', MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_L3_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S]
            elif self.plotType == 'TRAWL':
                y_options = ['Choose Y Axis Metric', SPEEDUP_VEC, SPEEDUP_DL1]
            elif self.plotType == 'Summary':
                x_options.append(RECIP_TIME_LOOP_MHZ)
                y_options = ['Choose Y Axis Metric', COVERAGE_PCT, TIME_LOOP_S, TIME_APP_S, RECIP_TIME_LOOP_MHZ]
            y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
            x_menu = tk.OptionMenu(self, self.x_selected, *x_options)
            y_menu['menu'].insert_separator(1)
            x_menu['menu'].insert_separator(1)
        # Axes scale options
        scale_label = tk.Label(self, text='Scales:')
        self.yscale_selected = tk.StringVar(value='Choose Y Axis Scale')
        self.xscale_selected = tk.StringVar(value='Choose X Axis Scale')
        yscale_options = ['Choose Y Axis Scale', 'Linear', 'Log']
        xscale_options = ['Choose X Axis Scale', 'Linear', 'Log']
        yscale_menu = tk.OptionMenu(self, self.yscale_selected, *yscale_options)
        xscale_menu = tk.OptionMenu(self, self.xscale_selected, *xscale_options)
        yscale_menu['menu'].insert_separator(1)
        xscale_menu['menu'].insert_separator(1)
        # Update button to replot
        update = tk.Button(self, text='Update', command=self.update_axes)
        # Tab grid
        metric_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        scale_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        x_menu.grid(row=1, column=0, padx=5, sticky=tk.W)
        y_menu.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        xscale_menu.grid(row=1, column=1, padx=5, sticky=tk.W)
        yscale_menu.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        update.grid(row=3, column=0, padx=5, sticky=tk.NW)
    
    def update_axes(self):
        # Get user selected metrics
        if self.x_selected.get() != 'Choose X Axis Metric':
            self.tab.x_axis = self.x_selected.get()
        if self.y_selected.get() != 'Choose Y Axis Metric':
            self.tab.y_axis = self.y_selected.get()
        # Get user selected scales
        if self.xscale_selected.get() != 'Choose X Axis Scale':
            self.tab.x_scale = self.xscale_selected.get().lower()
        if self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.y_scale = self.yscale_selected.get().lower()
        # Save current plot states
        self.tab.plotInteraction.save_plot_state()
        # Set user selected metrics/scales if they have changed at least one
        if self.x_selected.get() != 'Choose X Axis Metric' or self.y_selected.get() != 'Choose Y Axis Metric' or self.xscale_selected.get() != 'Choose X Axis Scale' or self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.data.scale = self.tab.x_scale + self.tab.y_scale
            self.tab.data.y_axis = "{}".format(self.tab.y_axis)
            self.tab.data.x_axis = "{}".format(self.tab.x_axis)
            self.tab.data.notify(self.tab.data.gui.loadedData)

class ShortNameData(AnalyzerData):
    def __init__(self, data, gui, root, level):
        super().__init__(data, gui, root, level, "ShortNameTabData")

    def notify(self, data):
        self.notify_observers()

class ShortNameTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        # Build Short Name Table
        self.table = Table(self, dataframe=pd.DataFrame(), showtoolbar=False, showstatusbar=True)
        table_button_frame = tk.Frame(self)
        table_button_frame.grid(row=4, column=1)
        self.update_button = tk.Button(table_button_frame, text="Update", command=lambda: self.updateLabels(self.table.model.df))
        self.export_button = tk.Button(table_button_frame, text="Export", command=lambda: self.exportCSV(self.table))
        self.find_replace_button = tk.Button(table_button_frame, text="Find & Replace ShortName", command=lambda: self.findAndReplace())

    def notify(self, data):
        self.table.model.df = self.data.df[[NAME, SHORT_NAME, TIMESTAMP, 'Color', VARIANT]]
        self.table.show()
        self.table.redraw()
        self.update_button.grid(row=0, column=0)
        self.export_button.grid(row=0, column=1)
        self.find_replace_button.grid(row=0, column=2)

    def findAndReplace(self):
        find=tk.simpledialog.askstring("Find", "Find what:")
        replace=tk.simpledialog.askstring("Replace", "Replace with:")
        self.table.model.df['ShortName']=self.table.model.df['ShortName'].str.replace(find, replace)
        self.table.redraw()

    # Merge user input labels with current mappings and replot
    def updateLabels(self, table_df):
        # Update short names in each of the main dfs
        self.data.loadedData.update_short_names(table_df)

    def exportCSV(self, table):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        table.model.df.to_csv(export_file_path, index=False, header=True)
        
    # @property
    # def df(self):
    #     return self.loadedData.get_df(self.level)[[NAME, SHORT_NAME, TIMESTAMP, 'Color', VARIANT]].loc[self.loadedData.get_df(self.level)[VARIANT].isin(self.tab.variants)].reset_index(drop=True)

class MappingsData(AnalyzerData):
    def __init__(self, data, gui, root, level):
        super().__init__(data, gui, root, level, "Mappings")

    def notify(self, data):
        self.notify_observers()

class MappingsTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        self.table = Table(self, dataframe=self.mappings, showtoolbar=False, showstatusbar=True)
        self.setupCustomOptions()
        # TODO: Fix showing/hiding intermediate mappings
        #if gui.loadedData.removedIntermediates: tk.Button(self, text="Show Intermediates", command=self.showIntermediates).grid(row=3, column=1)
        #else: tk.Button(self, text="Remove Intermediates", command=self.removeIntermediates).grid(row=3, column=1)

    def notify(self, data):
        self.placeholderCheck()
        self.table.show()
        self.table.redraw()
        self.edit_button.grid(row=10, column=0)
        self.update_button.grid(row=10, column=1, sticky=tk.W)
    
    def updateTable(self):
        self.table.redraw()
        self.win.destroy()

    def addMapping(self):
        # extract timestamp,name,short_name from selected before and after to add to mappings
        toAdd = pd.DataFrame()
        toAdd['Before Timestamp'] = [int(self.before_selected.get().rsplit('[')[2][:-1])]
        toAdd['Before Name'] = [self.before_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['After Timestamp'] = [int(self.after_selected.get().rsplit('[')[2][:-1])]
        toAdd['After Name'] = [self.after_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['Difference'] = self.data.df.loc[(self.data.df[NAME] == toAdd['After Name'][0]) & (self.data.df[TIMESTAMP] == toAdd['After Timestamp'][0])][VARIANT].iloc[0]
        self.data.loadedData.add_mapping(self.data.level, toAdd)
        self.table.model.df = self.mappings
        self.updateTable()
    
    def removeMapping(self):
        toRemove = pd.DataFrame()
        toRemove['Before Name'] = [self.before_selected.get().split(']')[1].split('[')[0][1:-1]]
        toRemove['Before Timestamp'] = [int(self.before_selected.get().rsplit('[')[2][:-1])]
        toRemove['After Name'] = [self.after_selected.get().split(']')[1].split('[')[0][1:-1]]
        toRemove['After Timestamp'] = [int(self.after_selected.get().rsplit('[')[2][:-1])]
        # Update loadedData and database mappings
        self.data.loadedData.remove_mapping(self.data.level, toRemove)
        self.placeholderCheck()
        self.updateTable()

    def placeholderCheck(self):
        # Add placeholder row if current mappings table is now empty for proper GUI display
        if self.mappings.empty:
            self.table.model.df = pd.DataFrame(columns=['Before Name', 'Before Timestamp', 'After Name', 'After Timestamp', SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference', 'DataSource', 'Before Variant', 'After Variant'])
            self.table.model.df = self.table.model.df.append(pd.Series(name='temp'))
        else: self.table.model.df = self.mappings

    def updateMapping(self):
        # Update observers with the new mappings
        self.data.loadedData.update_mapping(self.data.level)

    def setupCustomOptions(self):
        self.edit_button = tk.Button(self, text="Edit", command=self.editMappings)
        self.update_button = tk.Button(self, text="Update", command=self.updateMapping)

    def editMappings(self):
        options = "[" + self.data.df[SHORT_NAME] + "] " + self.data.df[NAME] + " [" + self.data.df[TIMESTAMP].map(str) + "]"
        self.win = tk.Toplevel()
        center(self.win)
        self.win.title('Edit Mappings')
        message = 'Select a before and after codelet to create a new\nmapping or remove an existing one.'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        self.before_selected = tk.StringVar(value='Choose Before Codelet')
        self.after_selected = tk.StringVar(value='Choose After Codelet')
        before_menu = tk.OptionMenu(self.win, self.before_selected, *options)
        after_menu = tk.OptionMenu(self.win, self.after_selected, *options)
        before_menu.grid(row=1, column=0, padx=10, pady=10)
        after_menu.grid(row=1, column=2, padx=10, pady=10)
        tk.Button(self.win, text="Add", command=self.addMapping).grid(row=2, column=1, padx=10, pady=10)
        tk.Button(self.win, text="Remove", command=self.removeMapping).grid(row=3, column=1, padx=10, pady=10)
    
    def cancelAction(self):
        self.choice = 'cancel'
        self.win.destroy()

    def selectAction(self, metric):
        self.choice = metric
        self.win.destroy()

    # def showIntermediates(self):
    #     self.tab.data.gui.loadedData.mapping = self.tab.data.gui.loadedData.orig_mapping.copy(deep=True)
    #     self.tab.data.gui.loadedData.add_speedup(self.tab.data.gui.loadedData.mapping, self.tab.data.gui.loadedData.summaryDf)
    #     self.tab.data.gui.loadedData.removedIntermediates = False
    #     data_tab_pairs = [(self.tab.data.gui.qplotData, self.tab.data.gui.c_qplotTab), (self.tab.data.gui.trawlData, self.tab.data.gui.c_trawlTab), \
    #         (self.tab.data.gui.siplotData, self.tab.data.gui.c_siPlotTab), (self.tab.data.gui.customData, self.tab.data.gui.c_customTab), \
    #         (self.tab.data.gui.coverageData, self.tab.data.gui.c_summaryTab)]
    #     for data, tab in data_tab_pairs:
    #         data.notify(self.tab.data.gui.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.variants, scale=tab.x_scale+tab.y_scale)
    
    # def removeIntermediates(self):
    #     # Ask the user which speedup metric they'd like to use for end2end transitions
    #     self.win = tk.Toplevel()
    #     center(self.win)
    #     self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
    #     self.win.title('Select Speedup')
    #     message = 'Select the speedup to maximize for\nend-to-end transitions.'
    #     tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
    #     for index, metric in enumerate([SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S]):
    #         b = tk.Button(self.win, text=metric)
    #         b['command'] = lambda metric=metric : self.selectAction(metric) 
    #         b.grid(row=index+1, column=1, padx=20, pady=10)
    #     root.wait_window(self.win)
    #     if self.choice == 'cancel': return
    #     self.loadedData.levelData[self.level].mapping = self.loadedData.get_end2end(self.loadedData.get_mapping(self.level), self.choice)
    #     self.loadedData.levelData[self.level].mapping = self.loadedData.get_speedups(self.level, self.loadedData.get_mapping(self.level))
    #     self.loadedData.add_speedup(self.loadedData.get_mapping(self.level), self.loadedData.get_df(self.level))
    #     self.loadedData.removedIntermediates = True
    #     data_tab_pairs = [(self.tab.data.gui.qplotData, self.tab.data.gui.c_qplotTab), (self.tab.data.gui.trawlData, self.tab.data.gui.c_trawlTab), (self.tab.data.gui.siplotData, self.tab.data.gui.c_siPlotTab), (self.tab.data.gui.customData, self.tab.data.gui.c_customTab), (self.tab.data.gui.coverageData, self.tab.data.gui.c_summaryTab)]
    #     for data, tab in data_tab_pairs:
    #         data.notify(self.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.variants, scale=tab.x_scale+tab.y_scale)

    # @staticmethod
    # def restoreCustom(df, all_mappings):
    #     # for each row in all_mappings
    #     # if before and after are in df -> add to mappings
    #     # Auto change user's saved mapping file with the latest naming convention
    #     mappings_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'mappings.csv')
    #     all_mappings.rename(columns={'before_name':'Before Name', 'before_timestamp#':'Before Timestamp', \
    #     'after_name':'After Name', 'after_timestamp#':'After Timestamp'}, inplace=True)
    #     all_mappings.to_csv(mappings_path, index=False)
    #     before = pd.merge(left=df[[NAME, TIMESTAMP]], right=all_mappings, left_on=[NAME, TIMESTAMP], right_on=['Before Name', 'Before Timestamp'], how='inner').drop(columns=[NAME, TIMESTAMP])
    #     mappings = pd.merge(left=df[[NAME, TIMESTAMP]], right=before, left_on=[NAME, TIMESTAMP], right_on=['After Name', 'After Timestamp'], how='inner').drop(columns=[NAME, TIMESTAMP])
    #     return mappings

class ClusterTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.cluster_path = resource_path('clusters')
        self.cluster_selected = tk.StringVar(value='Choose Cluster')
        cluster_options = ['Choose Cluster']
        for cluster in os.listdir(self.cluster_path):
            cluster_options.append(cluster[:-4])
        self.cluster_menu = tk.OptionMenu(self, self.cluster_selected, *cluster_options)
        self.cluster_menu['menu'].insert_separator(1)
        update = tk.Button(self, text='Update', command=self.update)
        colors = tk.Button(self, text='Color by Cluster', command=self.updateColors)
        self.cluster_menu.pack(side=tk.LEFT, anchor=tk.NW)
        update.pack(side=tk.LEFT, anchor=tk.NW)
        colors.pack(side=tk.LEFT, anchor=tk.NW, padx=10)

    def updateColors(self):
        table_df = self.tab.shortnameTab.table.model.df
        table_df = pd.merge(left=table_df, right=self.tab.df[KEY_METRICS + [NonMetricName.SI_CLUSTER_NAME]], how='left', on=KEY_METRICS)
        table_df['Color'] = table_df[NonMetricName.SI_CLUSTER_NAME]
        table_df.drop(columns=[NonMetricName.SI_CLUSTER_NAME], inplace=True, errors='ignore')
        self.tab.shortnameTab.updateLabels(table_df)
    
    def update(self):
        if self.cluster_selected.get() != 'Choose Cluster':
            path = os.path.join(self.cluster_path, self.cluster_selected.get() + '.csv')
            self.tab.cluster = path
            self.tab.title = self.cluster_selected.get()
            self.tab.siplotData.notify(self.tab.data.gui.loadedData, variants=self.tab.variants, update=True, cluster=path, title=self.cluster_selected.get())

class VariantTab(tk.Frame):
    def __init__(self, parent, tab, all_variants, variants):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.checkListBox = ChecklistBox(self, all_variants, variants, self.tab, bd=1, relief="sunken", background="white")
        update = tk.Button(self, text='Update', command=self.checkListBox.updateVariants)
        select_all = tk.Button(self, text='Select All', command= lambda val=1 : self.checkListBox.set_all(val))
        deselect_all = tk.Button(self, text='Deselect All', command= lambda val=0 : self.checkListBox.set_all(val))
        self.checkListBox.pack(side=tk.LEFT)
        update.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)
        select_all.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)
        deselect_all.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)

class DataTabData(AnalyzerData):
    def __init__(self, data, gui, root, level):
        super().__init__(data, gui, root, level, "DataTabData")

    def notify(self, data):
        self.notify_observers()

class DataTab(AnalyzerTab):
    def __init__(self, parent, data, metrics=[], variants=[]):
        super().__init__(parent, data)
        # self.summaryTable = Table(self, dataframe=df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)[metrics], showtoolbar=False, showstatusbar=True)
        self.summaryTable = Table(self, dataframe=pd.DataFrame(), showtoolbar=False, showstatusbar=True)
        self.table_button_frame = tk.Frame(self)
        self.table_button_frame.grid(row=4, column=1)
        self.export_summary_button = tk.Button(self.table_button_frame, text="Export Summary Sheet", command=lambda: exportCSV(self.data.df))
        self.export_colored_summary_button = tk.Button(self.table_button_frame, text="Export Colored Summary", command=lambda: exportXlsx(self.data.df))

    def notify(self, data):
        # Update table with latest loadedData df
        self.summaryTable.model.df = self.data.df
        self.summaryTable.show()
        self.summaryTable.redraw()
        self.export_summary_button.grid(row=0, column=0)
        self.export_colored_summary_button.grid(row=0, column=1)

class LabelTab(tk.Frame):
    def __init__(self, parent, tab, level):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.loadedData = self.tab.data.gui.loadedData
        self.metric1 = tk.StringVar(value='Metric 1')
        self.metric2 = tk.StringVar(value='Metric 2')
        self.metric3 = tk.StringVar(value='Metric 3')
        self.menu1 = AxesTab.custom_axes(self, self.metric1, self.tab.data.gui)
        self.menu2 = AxesTab.custom_axes(self, self.metric2, self.tab.data.gui)
        self.menu3 = AxesTab.custom_axes(self, self.metric3, self.tab.data.gui)
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)
        # Grid layout 
        self.menu1.grid(row=0, column=0, padx = 10, pady=10, sticky=tk.NW)
        self.menu2.grid(row=0, column=1, pady=10, sticky=tk.NW)
        self.menu3.grid(row=0, column=2, padx = 10, pady=10, sticky=tk.NW)
        self.updateButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
        self.resetButton.grid(row=1, column=1, sticky=tk.NW)

    def resetMetrics(self):
        self.metric1.set('Metric 1')
        self.metric2.set('Metric 2')
        self.metric3.set('Metric 3')
        # self.loadedData.levelData[level].reset_labels()

    def reset(self):
        self.resetMetrics()
        for tab in self.tab.plotInteraction.tabs:
            if tab.name != 'Scurve':
                textData = tab.plotInteraction.textData
                tab.current_labels = []
                for i, text in enumerate(textData['texts']):
                    text.set_text(textData['orig_mytext'][i])
                    textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                    textData['legend'].get_title().set_text(textData['orig_legend'])
                tab.plotInteraction.canvas.draw()
                # Adjust labels if already adjusted
                if tab.plotInteraction.adjusted:
                    tab.plotInteraction.adjustText()

    def updateLabels(self):
        current_metrics = []
        if self.metric1.get() != 'Metric 1': current_metrics.append(self.metric1.get())
        if self.metric2.get() != 'Metric 2': current_metrics.append(self.metric2.get())
        if self.metric3.get() != 'Metric 3': current_metrics.append(self.metric3.get())
        current_metrics = [metric for metric in current_metrics if metric in self.tab.plotInteraction.df.columns.tolist()]
        if not current_metrics: return # User hasn't selected any label metrics
        for tab in self.tab.plotInteraction.tabs:
            if tab.name != 'Scurve':
                tab.current_labels = current_metrics
                textData = tab.plotInteraction.textData

                # TODO: Update the rest of the plots at the same level with the new checked variants
                # for tab in self.parent.tab.plotInteraction.tabs:
                #     for i, cb in enumerate(self.cbs):
                #         tab.labelTab.checkListBox.vars[i].set(self.vars[i].get())
                #     tab.current_labels = self.parent.tab.current_labels

                # If nothing selected, revert labels and legend back to original
                if not tab.current_labels:
                    for i, text in enumerate(textData['texts']):
                        text.set_text(textData['orig_mytext'][i])
                        textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                        textData['legend'].get_title().set_text(textData['orig_legend'])
                else: 
                    # Update existing plot texts by adding user specified metrics
                    df = tab.plotInteraction.df
                    for i, text in enumerate(textData['texts']):
                        toAdd = textData['orig_mytext'][i][:-1]
                        for choice in tab.current_labels:
                            codeletName = textData['names'][i]
                            # TODO: Clean this up so it's on the edges and not the data points
                            if choice in [SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']:
                                tempDf = pd.DataFrame()
                                if not tab.mappings.empty: # Mapping
                                    tempDf = tab.mappings.loc[(tab.mappings['Before Name']+tab.mappings['Before Timestamp'].astype(str))==codeletName]
                                if tempDf.empty: 
                                    if choice == 'Difference': 
                                        tempDf = tab.mappings.loc[(tab.mappings['After Name']+tab.mappings['After Timestamp'].astype(str))==codeletName]
                                        if tempDf.empty:
                                            value = 'Same'
                                    else: value = 1
                                else: value = tempDf[choice].iloc[0]
                            else:
                                value = df.loc[(df[NAME]+df[TIMESTAMP].astype(str))==codeletName][choice].iloc[0]
                            if isinstance(value, int) or isinstance(value, float):
                                toAdd += ', ' + str(round(value, 2))
                            else:
                                toAdd += ', ' + str(value)
                        toAdd += ')'
                        text.set_text(toAdd)
                        textData['mytext'][i] = toAdd
                    # Update legend for user to see order of metrics in the label
                    newTitle = textData['orig_legend'][:-1]
                    for choice in tab.current_labels:
                        newTitle += ', ' + choice
                    newTitle += ')'
                    textData['legend'].get_title().set_text(newTitle)
                tab.plotInteraction.canvas.draw()
                # Adjust labels if already adjusted
                if tab.plotInteraction.adjusted:
                    tab.plotInteraction.adjustText()

class FilteringData(AnalyzerData):
    def __init__(self, data, gui, root, level):
        super().__init__(data, gui, root, level, "FilteringData")

    def notify(self, data):
        self.notify_observers()

class FilteringTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data)
        self.setupThreshold()

    def notify(self, data):
        self.setOptions()
        self.buildPointSelector()
        # Grid setup
        self.threshold_frame.grid(row=0, column=1, sticky=tk.NW)
        self.metric_menu.grid(row=0, column=1, sticky=tk.N)
        self.min_label.grid(row=1, column=1, sticky=tk.NW)
        self.min_entry.grid(row=1, column=2, sticky=tk.NW)
        self.max_label.grid(row=2, column=1, sticky=tk.NW)
        self.max_entry.grid(row=2, column=2, sticky=tk.NW)
        self.update_threshold_button.grid(row=0, column=2, sticky=tk.N)
        self.pointSelector.grid(row=0, column=0)

    def buildPointSelector(self):
        options=[]
        # TODO do this without iterating over the indices
        for i in range(len(self.data.df[SHORT_NAME])):
            options.append('[' + self.data.df[SHORT_NAME][i] + '] ' + self.data.df[NAME][i] + ' [' + str(self.data.df[TIMESTAMP][i]) + ']')
        self.pointSelector = ChecklistBox(self, options, self.data.loadedData.levelData[self.level].guiState.hidden, self, short_names=self.data.df[SHORT_NAME].tolist(), names=self.data.df[NAME].tolist(), timestamps=self.data.df[TIMESTAMP].tolist(), bd=1, relief="sunken", background="white")
        # self.selector_update_button = tk.Button(self, text='Update Points', command=self.pointSelector.updatePlot)
        # self.pointSelector.restoreState(self.stateDictionary)

    def setOptions(self):
        self.metric_menu = AxesTab.custom_axes(self.threshold_frame, self.metric_selected, self.data.gui)
        # metric_options = [metric for metric in self.data.df.columns.tolist()]
        # metric_options.insert(0, 'Choose Metric')
        # self.metric_menu = tk.OptionMenu(self, self.metric_selected, *metric_options)
        # self.metric_menu['menu'].insert_separator(1)

    def setupThreshold(self):
        self.threshold_frame = tk.Frame(self)
        # Metric Selector
        self.metric_selected = tk.StringVar(value='Choose Metric')
        # Min threshold option
        self.min_label = tk.Label(self.threshold_frame, text='Min Threshold: ')
        self.min_num = tk.DoubleVar()
        self.min_entry = tk.Entry(self.threshold_frame, textvariable=self.min_num)
        # Max threshold option
        self.max_label = tk.Label(self.threshold_frame, text='Max Threshold: ')
        self.max_num = tk.DoubleVar()
        self.max_entry = tk.Entry(self.threshold_frame, textvariable=self.max_num)
        self.update_threshold_button = tk.Button(self, text='Update', command=self.updateFilter)

    def updateFilter(self):
        names = self.pointSelector.updatePlot()
        metric = self.metric_selected.get()
        if metric == 'Choose Metric': metric = ''
        self.data.loadedData.setFilter(self.level, metric, self.min_num.get(), self.max_num.get(), names)

class GuideTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        # State GUI
        self.canvas = tk.Canvas(self, width=500, height=250)
        self.canvas.pack(side=tk.LEFT)
        self.fsm = FSM(self)
        self.fsm.add_observers(self)
        self.img = tk.PhotoImage(file=self.fsm.file)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)

        bottomframe = tk.Frame(self)
        bottomframe.pack(side=tk.BOTTOM)

        proceedButton = tk.Button(self, text="Proceed", command=self.fsm.proceed)
        proceedButton.pack(side=tk.TOP)
        detailsButton = tk.Button(self, text="Details", command=self.fsm.details)
        detailsButton.pack(side=tk.TOP)
        prevButton = tk.Button(self, text="Previous", command=self.fsm.previous)
        prevButton.pack(side=tk.TOP)

    def notify(self, observable):
        self.fsm.save_graph()
        self.img = tk.PhotoImage(file=self.fsm.file)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)

class FSM(Observable):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.tab = self.parent.tab
        self.title = self.tab.plotInteraction.textData['title']
        self.file = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'my_state_diagram.png')
        # Temporary hardcoded points for each state
        # self.a2_points = ['livermore_default: lloops.c_kernels_line1340_01587402719', 'NPB_2.3-OpenACC-C: sp.c_compute_rhs_line1452_01587402719']
        # self.a3_points = ['TSVC_default: tsc.c_vbor_line5367_01587481116', 'NPB_2.3-OpenACC-C: cg.c_conj_grad_line549_01587481116', 'NPB_2.3-OpenACC-C: lu.c_pintgr_line2019_01587481116']
        transitions = [{'trigger':'proceed', 'source':'INIT', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'details', 'source':'AStart', 'dest':'A1', 'after':'A1'},
                {'trigger':'details', 'source':'A1', 'dest':'A11', 'after':'A11'},
                {'trigger':'proceed', 'source':'A1', 'dest':'A2', 'after':'A2'},
                {'trigger':'proceed', 'source':'A2', 'dest':'A3', 'after':'A3'},
                {'trigger':'proceed', 'source':'A3', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'proceed', 'source':'AStart', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'proceed', 'source':'AEnd', 'dest':'B1', 'after':'B1'},
                {'trigger':'proceed', 'source':'B1', 'dest':'B2', 'after':'B2'},
                {'trigger':'proceed', 'source':'B2', 'dest':'BEnd', 'after':'BEnd'},
                {'trigger':'proceed', 'source':'BEnd', 'dest':'End', 'after':'End'},
                {'trigger':'previous', 'source':'End', 'dest':'BEnd', 'after':'BEnd'},
                {'trigger':'previous', 'source':'BEnd', 'dest':'B2', 'after':'B2'},
                {'trigger':'previous', 'source':'B2', 'dest':'B1', 'after':'B1'},
                {'trigger':'previous', 'source':'B1', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'previous', 'source':'AEnd', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'previous', 'source':'AStart', 'dest':'INIT', 'after':'INIT'},
                {'trigger':'previous', 'source':'A3', 'dest':'A2', 'after':'A2'},
                {'trigger':'previous', 'source':'A2', 'dest':'A1', 'after':'A1'},
                {'trigger':'previous', 'source':'A1', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'previous', 'source':'A11', 'dest':'A1', 'after':'A1'}]
        states = ['INIT', 'AStart', State('A1', ignore_invalid_triggers=True), State('A11', ignore_invalid_triggers=True), 'A2', 'A3', 'AEnd', 'B1', 'B2', 'BEnd', 'End']

        if self.tab.data.gui.loadedData.transitions == 'showing':
            self.machine = Machine(model=self, states=states, initial='A11', transitions=transitions)
        elif self.tab.data.gui.loadedData.transitions == 'hiding':
            self.tab.data.gui.loadedData.transitions = 'disabled'
            self.machine = Machine(model=self, states=states, initial='A1', transitions=transitions)
        else:
            self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)
        self.save_graph()
        # Get points that we want to save for each state
        self.a1_highlighted = self.tab.plotInteraction.A_filter(relate=operator.gt, metric=SPEEDUP_TIME_LOOP_S, threshold=1, getNames=True) # Highlight SIDO codelets
        self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, getNames=True) # Highlight RHS codelets
        self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, getNames=True) # Highlight FMA codelets

    def INIT(self):
        print("In INIT")
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'INIT', pad=40)
        self.notify_observers()
    
    def AStart(self):
        print("In AStart")
        self.tab.plotInteraction.showMarkers()
        self.tab.plotInteraction.unhighlightPoints()
        self.tab.labelTab.reset()
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A-Start', pad=40)
        self.notify_observers()

    def A1(self):
        print("In A1")
        if self.tab.data.gui.loadedData.transitions == 'showing':
            print("going back to orig variants")
            self.tab.data.gui.loadedData.transitions = 'hiding'
            self.tab.plotInteraction.showMarkers()
            self.tab.variantTab.checkListBox.showOrig()
        else:
            print("A1 state after orig variants")
            self.tab.plotInteraction.showMarkers()
            self.tab.plotInteraction.unhighlightPoints()
            self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A1 (SIDO>1)', pad=40)
            self.a1_highlighted = self.tab.plotInteraction.A_filter(relate=operator.gt, metric=SPEEDUP_TIME_LOOP_S, threshold=1, show=True, highlight=True) # Highlight SIDO codelets
            self.updateLabels(SPEEDUP_TIME_LOOP_S)
            self.notify_observers()

    def A11(self):
        print("In A11")
        if self.tab.data.gui.loadedData.transitions != 'showing':
            self.tab.data.gui.loadedData.transitions = 'showing'
            for name in self.tab.plotInteraction.textData['names']:
                if name not in self.a1_highlighted:
                    self.tab.plotInteraction.togglePoint(self.tab.plotInteraction.textData['name:marker'][name], visible=False)
            self.tab.variantTab.checkListBox.showAllVariants()

    def A2(self):
        print("In A2")
        self.tab.plotInteraction.unhighlightPoints()
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A2 (RHS=1)', pad=40)
        self.tab.plotInteraction.A_filter(relate=operator.gt, metric=SPEEDUP_TIME_LOOP_S, threshold=1, highlight=False, remove=True) # Remove SIDO codelets
        self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, highlight=True, show=True) # Highlight RHS codelets
        self.updateLabels(COUNT_OPS_RHS_OP)
        self.notify_observers()

    def A3(self):
        print("In A3")
        self.tab.plotInteraction.unhighlightPoints()
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A3 (FMA)', pad=40)
        self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, highlight=False, remove=True) # Remove RHS codelets
        self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True) # Highlight FMA codelets
        self.updateLabels(COUNT_OPS_FMA_PCT)
        self.notify_observers()

    def AEnd(self):
        print("In AEnd")
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A-End', pad=40)
        self.all_highlighted = self.a1_highlighted + self.a2_highlighted + self.a3_highlighted
        self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True, points=self.all_highlighted) # Highlight all previously highlighted codelets
        self.updateLabels('advice')
        self.notify_observers()

    def B1(self):
        print("In B1")
        self.notify_observers()

    def B2(self):
        print("In B2")
        self.notify_observers()

    def BEnd(self):
        print("In BEnd")
        self.notify_observers()

    def End(self):
        print("In End")
        self.notify_observers()

    def save_graph(self):
        self.machine.get_graph(show_roi=True).draw(self.file, prog='dot')
    
    def updateLabels(self, metric):
        self.tab.labelTab.resetMetrics()
        self.tab.labelTab.metric1.set(metric)
        self.tab.labelTab.updateLabels()

class ChecklistBox(tk.Frame):
    def __init__(self, parent, choices, hidden, tab, short_names=[], names=[], timestamps=[], **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent=parent
        self.tab=tab
        scrollbar = tk.Scrollbar(self)
        scrollbar_x = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        checklist = tk.Text(self, width=40)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        checklist.pack(fill=tk.Y, expand=True)
        self.vars = []
        self.names = []
        self.cbs = []
        bg = self.cget("background")
        for index, choice in enumerate(choices):
            var = tk.IntVar(value=1)
            self.vars.append(var)
            if short_names and names and timestamps:
                name = names[index] + str(timestamps[index])
                self.names.append(name)
                if name in hidden:
                    var.set(0)
            cb = tk.Checkbutton(self, var=var, text=choice,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            checklist.window_create("end", window=cb)
            checklist.insert("end", "\n")
        checklist.config(yscrollcommand=scrollbar.set)
        checklist.config(xscrollcommand=scrollbar_x.set)
        scrollbar.config(command=checklist.yview)
        scrollbar_x.config(command=checklist.xview)
        checklist.configure(state="disabled")

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
            try: 
                index = self.names.index(name)
                self.vars[index].set(0)
            except: pass

    def updatePlot(self):
        hidden_names = []
        for index, var in enumerate(self.vars):
            # selected = var.get()
            # selected_value = 1 if selected else 0
            if not var.get(): hidden_names.append(self.names[index])
            # marker = tab.plotInteraction.textData['name:marker'][name]
            # marker.set_alpha(selected_value)
            # text = tab.plotInteraction.textData['marker:text'][marker]
            # text.set_alpha(selected_value) 
            # if text in tab.plotInteraction.textData['text:arrow']: tab.plotInteraction.textData['text:arrow'][text].set_visible(selected)
            # try: 
            #     for mapping in tab.plotInteraction.textData['name:mapping'][name]:
            #         mapping.set_alpha(selected_value)
            # except: pass
        return hidden_names
        # tab.plotInteraction.canvas.draw()

    def updatePlot1(self):
        for tab in self.tab.tabs:
            for index, var in enumerate(self.vars):
                selected = var.get()
                selected_value = 1 if selected else 0
                name = self.names[index]
                tab.plotInteraction.pointSelector.vars[index].set(selected_value)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(selected_value)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(selected_value) 
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(selected)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(selected_value)
                except: pass
            tab.plotInteraction.canvas.draw()

    def getCheckedItems(self):
        values = []
        for i, cb in enumerate(self.cbs):
            value =  self.vars[i].get()
            if value:
                values.append(cb['text'])
        return values

    def showAllVariants(self):
        for i, cb in enumerate(self.cbs):
            self.vars[i].set(1)
        self.updateVariants()
    
    def showOrig(self):
        for i, cb in enumerate(self.cbs):
            if cb['text'] == self.tab.data.gui.loadedData.default_variant: self.vars[i].set(1)
            else: self.vars[i].set(0)
        self.updateVariants()

    def updateVariants(self):
        self.parent.tab.variants = self.getCheckedItems()
        # Update the rest of the plots at the same level with the new checked variants
        for tab in self.parent.tab.plotInteraction.tabs:
            for i, cb in enumerate(self.cbs):
                tab.variantTab.checkListBox.vars[i].set(self.vars[i].get())
            tab.variants = self.parent.tab.variants
        self.parent.tab.plotInteraction.save_plot_state()
        # Get new mappings from database to update plots
        self.all_mappings = pd.read_csv(self.tab.data.gui.loadedData.mappings_path)
        # self.mapping = MappingsTab.restoreCustom(self.tab.data.gui.loadedData.summaryDf.loc[self.tab.data.gui.loadedData.summaryDf[VARIANT].isin(self.parent.tab.variants)], self.all_mappings)
        for tab in self.parent.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title, mappings=self.mapping)
            else: tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, level=tab.level, mappings=self.mapping)

    def set_all(self, val):
        for var in self.vars: var.set(val)