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
from utils import center, Observable, resource_path
from metric_names import MetricName
from metric_names import NonMetricName
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
        for metric in [SPEEDUP_VEC, SPEEDUP_DL1, 'C_FLOP [GFlop/s]', RATE_INST_GI_P_S, VARIANT]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # QPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='QPlot', menu=menu)
        for metric in ['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]', 'C_FLOP [GFlop/s]', RATE_INST_GI_P_S]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # SIPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='SIPlot', menu=menu)
        for metric in ['Saturation', 'Intensity']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Speedups (If mappings):
        if not parent.tab.mappings.empty:
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Speedups', menu=menu)
            for metric in [SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Diagnostic Variables
        if gui.loadedData.analytic_columns and set(gui.loadedData.analytic_columns).issubset(gui.loadedData.summaryDf.columns):
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Diagnostics', menu=menu)
            for metric in gui.loadedData.analytic_columns:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
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
        x_options = ['Choose X Axis Metric', 'C_FLOP [GFlop/s]', RATE_INST_GI_P_S]
        if self.plotType == 'Custom' or self.plotType == 'Scurve':
            x_menu = AxesTab.custom_axes(self, self.x_selected, self.tab.data.gui)
            y_menu = AxesTab.custom_axes(self, self.y_selected, self.tab.data.gui)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['Choose Y Axis Metric', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]']
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
            self.tab.data.notify(self.tab.data.gui.loadedData, x_axis="{}".format(self.tab.x_axis), y_axis="{}".format(self.tab.y_axis), variants=self.tab.variants, scale=self.tab.x_scale+self.tab.y_scale, level=self.tab.level)

class ShortNameTab(tk.Frame):
    @staticmethod
    def addShortNames(namesDf):
        short_names_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'short_names.csv')
        if 'Color' not in namesDf.columns: namesDf['Color'] = pd.Series()
        if os.path.getsize(short_names_path) > 0:
            existing_shorts = pd.read_csv(short_names_path)
            merged = pd.concat([existing_shorts, namesDf[[NAME, SHORT_NAME, TIMESTAMP, 'Color']]]).drop_duplicates([NAME, TIMESTAMP], keep='last').reset_index(drop=True)
        else: 
            merged = namesDf[[NAME, SHORT_NAME, TIMESTAMP, 'Color']]
        merged.to_csv(short_names_path, index=False)

    def __init__(self, parent, tab, level=None):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.level = level
        self.tab = tab
        self.cape_path = self.tab.data.gui.loadedData.cape_path
        self.short_names_path = self.tab.data.gui.loadedData.short_names_path
        self.mappings_path = self.tab.data.gui.loadedData.mappings_path

    # Create table for Labels tab and update button
    def buildLabelTable(self, df, tab):
        short_name_table = df[[NAME, TIMESTAMP, 'Color']]
        short_name_table[SHORT_NAME] = short_name_table[NAME]
        merged = self.getShortNames(short_name_table)
        merged = pd.merge(left=merged, right=df[[NAME, TIMESTAMP, COVERAGE_PCT]], on=[NAME, TIMESTAMP], how='right')
        # sort label table by coverage to keep consistent with data table
        merged.sort_values(by=COVERAGE_PCT, ascending=False, inplace=True)
        merged = merged[[NAME, SHORT_NAME, TIMESTAMP, 'Color']]
        merged.columns = ["{}".format(i) for i in merged.columns]
        self.table = Table(tab, dataframe=merged, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        table_button_frame = tk.Frame(tab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Update", command=lambda: self.updateLabels(self.table.model.df)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export", command=lambda: self.exportCSV(self.table)).grid(row=0, column=1)
        tk.Button(table_button_frame, text="Find & Replace ShortName", command=lambda: self.findAndReplace()).grid(row=0, column=2)
        return self.table

    def findAndReplace(self):
        find=tk.simpledialog.askstring("Find", "Find what:")
        replace=tk.simpledialog.askstring("Replace", "Replace with:")
        self.table.model.df['ShortName']=self.table.model.df['ShortName'].str.replace(find, replace)
        self.table.redraw()
    
    # Merge user input labels with current mappings and replot
    def updateLabels(self, table_df, clusters=False):
        if self.checkForDuplicates(table_df):
            return
        else:
            # Add to local database 
            if not clusters: ShortNameTab.addShortNames(table_df)
            # Change the short name in each of the main dfs
            for level in self.tab.data.loadedData.dfs:
                df = self.tab.data.loadedData.dfs[level]
                df = pd.merge(left=df, right=table_df[[NAME, SHORT_NAME, TIMESTAMP, 'Color']], on=[NAME, TIMESTAMP], how='left')
                df[SHORT_NAME] = df[SHORT_NAME + "_y"].fillna(df[SHORT_NAME + "_x"])
                df['Color'] = df["Color_y"].fillna(df["Color_x"])
                df.drop(columns=[SHORT_NAME + "_y", SHORT_NAME + "_x", 'Color_x', 'Color_y'], inplace=True, errors='ignore')
                df = self.tab.data.gui.loadedData.compute_colors(df, clusters)
                self.tab.data.loadedData.dfs[level] = df.copy(deep=True)
        for tab in self.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title, mappings=tab.mappings)
            else: tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, level=tab.level, mappings=tab.mappings)
    
    def getShortNames(self, df):
        if os.path.getsize(self.short_names_path) > 0:
            existing_shorts = pd.read_csv(self.short_names_path)
            current_shorts = df[[NAME, SHORT_NAME, TIMESTAMP, 'Color']]
            merged = pd.concat([current_shorts, existing_shorts]).drop_duplicates([NAME, TIMESTAMP], keep='last').reset_index(drop=True)
        else: 
            merged = df[[NAME, SHORT_NAME, TIMESTAMP, 'Color']]
        return merged

    def checkForDuplicates(self, df):
        # Check if there are duplicates short names with the same timestamp
        pass
        # df.reset_index(drop=True, inplace=True)
        # duplicate_rows = df.duplicated(subset=[SHORT_NAME, TIMESTAMP], keep=False)
        # if duplicate_rows.any():
        #     message = str()
        #     for index, row in df[duplicate_rows].iterrows():
        #         message = message + 'row: ' + str(index + 1) + ', ShortName: ' + row[SHORT_NAME] + '\n'
        #     messagebox.showerror("Duplicate Short Names", "You currently have two or more duplicate short names from the same file. Please change them to continue. \n\n" \
        #         + message)
        #     return True
        # return False

    def exportCSV(self, table):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        table.model.df.to_csv(export_file_path, index=False, header=True)

class MappingsTab(tk.Frame):
    def __init__(self, parent, tab, level):
        super().__init__(parent)
        self.parent = parent
        self.tab = tab
        self.level = level
        self.mappings_path = self.tab.data.gui.loadedData.mappings_path
        self.short_names_path = self.tab.data.gui.loadedData.short_names_path

    def editMappings(self, options):
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

    def addMapping(self):
        # extract timestamp,name,short_name from selected before and after to add to mappings
        toAdd = pd.DataFrame()
        toAdd['Before Timestamp'] = [int(self.before_selected.get().rsplit('[')[2][:-1])]
        toAdd['Before Name'] = [self.before_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['After Timestamp'] = [int(self.after_selected.get().rsplit('[')[2][:-1])]
        toAdd['After Name'] = [self.after_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['Difference'] = self.tab.data.gui.loadedData.summaryDf.loc[(self.tab.data.gui.loadedData.summaryDf[NAME] == toAdd['After Name'][0]) & \
                                                            (self.tab.data.gui.loadedData.summaryDf[TIMESTAMP] == toAdd['After Timestamp'][0])][VARIANT].iloc[0]
        # Update mapping database and remove duplicates
        self.all_mappings = self.all_mappings.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)
        self.all_mappings.to_csv(self.mappings_path, index=False)
        # Check if this is the first time adding -> need to remove NaN placeholder row
        if self.mappings.iloc[0].name == 'temp':
            self.mappings.drop('temp', inplace=True)
        self.mappings = self.mappings.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)
        self.updateTable()
    
    def removeMapping(self):
        before_name = self.before_selected.get().split(']')[1].split('[')[0][1:-1]
        before_timestamp = int(self.before_selected.get().rsplit('[')[2][:-1])
        after_name = self.after_selected.get().split(']')[1].split('[')[0][1:-1]
        after_timestamp = int(self.after_selected.get().rsplit('[')[2][:-1])
        # Update mapping table/database
        to_update = [self.all_mappings, self.mappings]
        for mapping in to_update:
            mapping.drop(mapping[(mapping['Before Name']==before_name) & \
                (mapping['Before Timestamp']==before_timestamp) & \
                (mapping['After Name']==after_name) & \
                (mapping['After Timestamp']==after_timestamp)].index, inplace=True)
        # Update the mappings for this level
        self.tab.data.gui.loadedData.mappings[self.level] = self.mappings
        # Add placeholder row if current mappings table is now empty
        if self.mappings.empty:
            self.mappings = pd.DataFrame(columns=['Before Timestamp', 'Before Name', 'After Timestamp', 'After Name', \
                'Difference'])
            self.mappings = self.mappings.append(pd.Series(name='temp'))
        # Save updated mappings and update the GUI table
        self.all_mappings.to_csv(self.mappings_path, index=False)
        self.updateTable()
    
    def updateTable(self):
        self.table.destroy()
        self.table = Table(self, dataframe=self.mappings, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        self.win.destroy()

    def updateMappings(self):
        # Replace any previous mappings for the current files with the current mappings in the table
        # self.all_mappings = self.all_mappings.loc[(self.all_mappings['Before Timestamp']!=self.source_order[0]) & \
        #                         (self.all_mappings['After Timestamp']!=self.source_order[1])].reset_index(drop=True)
        # self.all_mappings = self.all_mappings.append(self.mappings, ignore_index=True)
        # self.all_mappings.to_csv(self.mappings_path, index=False)
        # Check if there are actually mappings to update
        if self.mappings.iloc[0].name == 'temp': mappings = pd.DataFrame()
        else: mappings = self.mappings
        for tab in self.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title, mappings=mappings)
            else: tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, level=tab.level, mappings=mappings)

    def buildMappingsTab(self, df, mappings):
        self.df = df
        # Check if we already have custom mappings for the file(s)
        self.all_mappings = pd.read_csv(self.mappings_path)
        self.mappings = MappingsTab.restoreCustom(self.df, self.all_mappings)
        if self.mappings.empty:
            # Create empty mappings dataframe for user to add to
            self.mappings = pd.DataFrame(columns=['Before Timestamp', 'Before Name', 'After Timestamp', 'After Name', \
                'Difference'])
            self.mappings = self.mappings.append(pd.Series(name='temp'))
        self.table = Table(self, dataframe=self.mappings, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        self.addCustomOptions(df)
        #if gui.loadedData.removedIntermediates: tk.Button(self, text="Show Intermediates", command=self.showIntermediates).grid(row=3, column=1)
        #else: tk.Button(self, text="Remove Intermediates", command=self.removeIntermediates).grid(row=3, column=1)
        # Add options for custom mapppings if multiple files loaded

        # Edit button allows the user to add/delete mappings
        # Options will be "Short_Name [TIMESTAMP]"

    @staticmethod
    def restoreCustom(df, all_mappings):
        # for each row in all_mappings
        # if before and after are in df -> add to mappings
        # Auto change user's saved mapping file with the latest naming convention
        mappings_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'mappings.csv')
        all_mappings.rename(columns={'before_name':'Before Name', 'before_timestamp#':'Before Timestamp', \
        'after_name':'After Name', 'after_timestamp#':'After Timestamp'}, inplace=True)
        all_mappings.to_csv(mappings_path, index=False)
        before = pd.merge(left=df[[NAME, TIMESTAMP]], right=all_mappings, left_on=[NAME, TIMESTAMP], right_on=['Before Name', 'Before Timestamp'], how='inner').drop(columns=[NAME, TIMESTAMP])
        mappings = pd.merge(left=df[[NAME, TIMESTAMP]], right=before, left_on=[NAME, TIMESTAMP], right_on=['After Name', 'After Timestamp'], how='inner').drop(columns=[NAME, TIMESTAMP])
        return mappings

    def addCustomOptions(self, df):
        #df = gui.loadedData.summaryDf
        options = "[" + df[SHORT_NAME] + "] " + df[NAME] + " [" + df[TIMESTAMP].map(str) + "]"
        tk.Button(self, text="Edit", command=lambda options=list(options): self.editMappings(options)).grid(row=10, column=0)
        tk.Button(self, text="Update", command=self.updateMappings).grid(row=10, column=1, sticky=tk.W)

    def addCustomOptions1(self, df):
        before = df.loc[df[TIMESTAMP] == self.source_order[0]]
        after = df.loc[df[TIMESTAMP] == self.source_order[1]]
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            for index in before.index:
                short_name = short_names.loc[(short_names[NAME]==before[NAME][index]) & (short_names[TIMESTAMP]==self.source_order[0])].reset_index(drop=True)
                if not short_name.empty: # Add short name to end of full codelet name in brackets
                    before[NAME][index] += '[' + short_name[SHORT_NAME][0] + ']'
            for index in after.index:
                short_name = short_names.loc[(short_names[NAME]==after[NAME][index]) & (short_names[TIMESTAMP]==self.source_order[1])].reset_index(drop=True)
                if not short_name.empty: after[NAME][index] = after[NAME][index] + '[' + \
                    short_name[SHORT_NAME][0] + ']'
        tk.Button(self, text="Edit", command=lambda before=list(before[NAME]), after=list(after[NAME]) : \
            self.editMappings(before, after)).grid(row=10, column=0)
        tk.Button(self, text="Update", command=self.updateMappings).grid(row=10, column=1, sticky=tk.W)

    def showIntermediates(self):
        self.tab.data.gui.loadedData.mapping = self.tab.data.gui.loadedData.orig_mapping.copy(deep=True)
        self.tab.data.gui.loadedData.add_speedup(self.tab.data.gui.loadedData.mapping, self.tab.data.gui.loadedData.summaryDf)
        self.tab.data.gui.loadedData.removedIntermediates = False
        data_tab_pairs = [(self.tab.data.gui.qplotData, self.tab.data.gui.c_qplotTab), (self.tab.data.gui.trawlData, self.tab.data.gui.c_trawlTab), \
            (self.tab.data.gui.siplotData, self.tab.data.gui.c_siPlotTab), (self.tab.data.gui.customData, self.tab.data.gui.c_customTab), \
            (self.tab.data.gui.coverageData, self.tab.data.gui.summaryTab)]
        for data, tab in data_tab_pairs:
            data.notify(self.tab.data.gui.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.variants, scale=tab.x_scale+tab.y_scale)
    
    def cancelAction(self):
        self.choice = 'cancel'
        self.win.destroy()

    def selectAction(self, metric):
        self.choice = metric
        self.win.destroy()
    
    def removeIntermediates(self):
        # Ask the user which speedup metric they'd like to use for end2end transitions
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        self.win.title('Select Speedup')
        message = 'Select the speedup to maximize for\nend-to-end transitions.'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        for index, metric in enumerate([SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S]):
            b = tk.Button(self.win, text=metric)
            b['command'] = lambda metric=metric : self.selectAction(metric) 
            b.grid(row=index+1, column=1, padx=20, pady=10)
        root.wait_window(self.win)
        if self.choice == 'cancel': return
        self.tab.data.gui.loadedData.mapping = self.tab.data.gui.loadedData.get_end2end(self.tab.data.gui.loadedData.mapping, self.choice)
        self.tab.data.gui.loadedData.mapping = self.tab.data.gui.loadedData.get_speedups(self.tab.data.gui.loadedData.mapping)
        self.tab.data.gui.loadedData.add_speedup(self.tab.data.gui.loadedData.mapping, self.tab.data.gui.loadedData.summaryDf)
        self.tab.data.gui.loadedData.removedIntermediates = True
        data_tab_pairs = [(self.tab.data.gui.qplotData, self.tab.data.gui.c_qplotTab), (self.tab.data.gui.trawlData, self.tab.data.gui.c_trawlTab), (self.tab.data.gui.siplotData, self.tab.data.gui.c_siPlotTab), (self.tab.data.gui.customData, self.tab.data.gui.c_customTab), (self.tab.data.gui.coverageData, self.tab.data.gui.summaryTab)]
        for data, tab in data_tab_pairs:
            data.notify(self.tab.data.gui.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.variants, scale=tab.x_scale+tab.y_scale)

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
        table_df = pd.merge(left=table_df, right=self.tab.df[[NAME, TIMESTAMP, NonMetricName.SI_CLUSTER_NAME]], how='left', on=[NAME, TIMESTAMP])
        table_df['Color'] = table_df[NonMetricName.SI_CLUSTER_NAME]
        table_df.drop(columns=[NonMetricName.SI_CLUSTER_NAME], inplace=True, errors='ignore')
        self.tab.shortnameTab.updateLabels(table_df, True)
    
    def update(self):
        if self.cluster_selected.get() != 'Choose Cluster':
            path = os.path.join(self.cluster_path, self.cluster_selected.get() + '.csv')
            self.tab.cluster = path
            self.tab.title = self.cluster_selected.get()
            self.tab.siplotData.notify(self.tab.data.gui.loadedData, variants=self.tab.variants, update=True, cluster=path, title=self.cluster_selected.get())

class ChecklistBox(tk.Frame):
    def __init__(self, parent, choices, current_choices, tab, listType='', **kwargs):
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
            if choice not in current_choices:
                var.set(0)
            self.vars.append(var)
            self.names.append(choice.split(' ', 1)[-1].rsplit(' ', 1)[0] + choice.rsplit(' ', 1)[-1][1:-1])
            cb = tk.Checkbutton(self, var=var, text=choice,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            if listType == 'pointSelector':
                cb['command'] = lambda name=self.names[index], index=index : self.updatePlot(name, index)
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

    def updatePlot(self, name, index):
        selected = self.vars[index].get()
        if selected:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(1)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(1)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(1)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(True)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(1)
                except: pass
                tab.plotInteraction.canvas.draw()
        else:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(0)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(0)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(0)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(False)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(0)
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
        self.mapping = MappingsTab.restoreCustom(self.tab.data.gui.loadedData.summaryDf.loc[self.tab.data.gui.loadedData.summaryDf[VARIANT].isin(self.parent.tab.variants)], self.all_mappings)
        for tab in self.parent.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title, mappings=self.mapping)
            else: tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, level=tab.level, mappings=self.mapping)

    def set_all(self, val):
        for var in self.vars: var.set(val)

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

class DataTab(tk.Frame):
    def __init__(self, parent, df):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.summaryTable = Table(self, dataframe=df, showtoolbar=False, showstatusbar=True)
        self.summaryTable.show()
        self.summaryTable.redraw()
        self.table_button_frame = tk.Frame(self)
        self.table_button_frame.grid(row=3, column=1)

class LabelTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
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

class FilteringTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        # Metric drop down menu
        self.metric_selected = tk.StringVar(value='Choose Metric')
        to_remove = [NAME, SHORT_NAME, VARIANT, TIMESTAMP, 'Color']
        metric_options = [metric for metric in tab.summaryDf.columns.tolist() if metric not in to_remove]
        metric_options.insert(0, 'Choose Metric')
        self.metric_menu = tk.OptionMenu(self, self.metric_selected, *metric_options)
        self.metric_menu['menu'].insert_separator(1)
        # Min threshold option
        min_label = tk.Label(self, text='Min Threshold: ')
        self.min_num = tk.IntVar()
        self.min_entry = tk.Entry(self, textvariable=self.min_num)
        # Max threshold option
        max_label = tk.Label(self, text='Max Threshold: ')
        self.max_num = tk.IntVar()
        self.max_entry = tk.Entry(self, textvariable=self.max_num)
        # Grid setup
        update = tk.Button(self, text='Update', command=self.update)
        self.metric_menu.grid(row=0, column=0)
        min_label.grid(row=1, column=0)
        self.min_entry.grid(row=1, column=1)
        max_label.grid(row=2, column=0)
        self.max_entry.grid(row=2, column=1)
        update.grid(row=3, column=0)

    def update(self):
        if self.metric_selected.get() == 'Choose Metric': pass
        else:
            filter_data = (self.metric_selected.get(), self.min_num.get(), self.max_num.get())
            self.tab.data.gui.siplotData.notify(self.tab.data.gui.loadedData, variants=self.tab.variants, update=True, cluster=self.tab.cluster, title=self.tab.title, \
                filtering=True, filter_data=filter_data)

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
        self.a2_points = ['livermore_default: lloops.c_kernels_line1340_01587402719', 'NPB_2.3-OpenACC-C: sp.c_compute_rhs_line1452_01587402719']
        self.a3_points = ['TSVC_default: tsc.c_vbor_line5367_01587481116', 'NPB_2.3-OpenACC-C: cg.c_conj_grad_line549_01587481116', 'NPB_2.3-OpenACC-C: lu.c_pintgr_line2019_01587481116']
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
        self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, points=self.a2_points, getNames=True) # Highlight RHS codelets
        self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, points=self.a3_points, getNames=True) # Highlight FMA codelets

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
        self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, highlight=True, show=True, points=self.a2_points) # Highlight RHS codelets
        self.updateLabels(COUNT_OPS_RHS_OP)
        self.notify_observers()

    def A3(self):
        print("In A3")
        self.tab.plotInteraction.unhighlightPoints()
        self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + 'A3 (FMA)', pad=40)
        self.tab.plotInteraction.A_filter(relate=operator.eq, metric=COUNT_OPS_RHS_OP, threshold=1, highlight=False, remove=True, points=self.a2_points) # Remove RHS codelets
        self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True, points=self.a3_points) # Highlight FMA codelets
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