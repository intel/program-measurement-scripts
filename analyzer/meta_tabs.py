import tkinter as tk
from PIL import ImageTk, Image
import pandas as pd
import os
import copy
from os.path import expanduser
from tkinter import messagebox
from pandastable import Table, config
from utils import center, Observable, resource_path, exportCSV, exportXlsx
from analyzer_model import AnalyzerData 
from analyzer_base import PlotTab, AnalyzerTab, AxesTab
# from plot_interaction import AxesTab
from metric_names import MetricName as MN
from metric_names import NonMetricName, KEY_METRICS, CATEGORIZED_METRICS, PLOT_METRICS, SHORT_NAME_METRICS
from capeplot import CapePlot, CapePlotColor
from fsm import FSM
globals().update(MN.__members__)

class ShortNameData(AnalyzerData):
    def __init__(self, data, level):
        super().__init__(data, level, "ShortNameTabData")
        self.shortNameTable = pd.DataFrame(columns=KEY_METRICS+[MN.SHORT_NAME, MN.VARIANT, 'Label'])

    def exportCSV(self, export_file_path):
        self.shortNameTable.to_csv(export_file_path, index=False, header=True)

class ShortNameTab(AnalyzerTab):
    def __init__(self, parent):
        super().__init__(parent, ShortNameData)
        # Build Short Name Table
        self.table = Table(self, dataframe=pd.DataFrame(), showtoolbar=False, showstatusbar=True)
        table_button_frame = tk.Frame(self)
        table_button_frame.grid(row=4, column=1)
        self.update_button = tk.Button(table_button_frame, text="Update", command=lambda: self.updateLabels())
        self.cluster_color_button = tk.Button(table_button_frame, text="Color by Cluster", command=lambda: self.colorClusters())
        self.export_button = tk.Button(table_button_frame, text="Export", command=lambda: self.exportCSV(self.table))
        self.find_replace_button = tk.Button(table_button_frame, text="Find & Replace ShortName", command=lambda: self.findAndReplace())
        self.table.show()
        self.update_button.grid(row=0, column=0)
        self.cluster_color_button.grid(row=0, column=1)
        self.export_button.grid(row=0, column=2)
        self.find_replace_button.grid(row=0, column=3)

    def notify(self, data):
        columns = [NAME, SHORT_NAME, TIMESTAMP, VARIANT]
        df = self.analyzerData.df[columns] if not self.analyzerData.df.empty else pd.DataFrame(columns=columns)
        color_map = self.analyzerData.levelData.guiState.get_color_map()
        self.table.model.df = pd.merge(left=df, right=color_map[KEY_METRICS + ['Label']], on=KEY_METRICS, how='left')
        self.table.redraw()

    def assignColors(self, df):
        labels = df['Label'].unique()
        colors = CapePlotColor.hashColors(labels)
        labelToColor = pd.DataFrame({'Label': labels, 'Color': colors})
        dfCols = [col for col in df.columns if col != 'Color']
        return pd.merge(left=df[dfCols], right=labelToColor, on=['Label'], how='left')
        
    def colorClusters(self):
        # Update the GUI state color map with colors for each codelet and the label for the legend
        df = self.analyzerData.df[KEY_METRICS + [NonMetricName.SI_CLUSTER_NAME]]
        df[NonMetricName.SI_CLUSTER_NAME].replace({'':'No Cluster'}, inplace=True)
        df['Label'] = df[NonMetricName.SI_CLUSTER_NAME]
        df = self.assignColors(df)
        ncMask = df['Label']=='No Cluster'
        self.update_colors(ncMask, df)

    def colorCustomLabels(self):
        # Update the GUI state color map with colors for unique user inputted Labels
        df = self.table.model.df[KEY_METRICS + ['Label']]
        df['Label'].replace({'':'No Label'}, inplace=True)
        df = self.assignColors(df)
        ncMask = df['Label']=='No Label'
        self.update_colors(ncMask, df)

    def update_colors(self, ncMask, df):
        # needed .value possibly due to a Pandas bug
        # See:https://stackoverflow.com/questions/24188729/pandas-adding-a-series-to-a-dataframe-causes-nan-values-to-appear
        df.loc[ncMask, 'Color'] = pd.Series([CapePlotColor.DEFAULT_COLOR]*len(df[ncMask])).values
        # Update shortname table "Label" column
        self.table.model.df.drop(columns=['Label'], inplace=True)
        self.table.model.df = pd.merge(left=self.table.model.df, right=df[KEY_METRICS + ['Label']], on=KEY_METRICS, how='left')
        self.table.redraw()
        self.analyzerData.levelData.update_colors(df)

    def findAndReplace(self):
        find=tk.simpledialog.askstring("Find", "Find what:")
        replace=tk.simpledialog.askstring("Replace", "Replace with:")
        if find is None or replace is None:
            return
        self.table.model.df['ShortName']=self.table.model.df['ShortName'].str.replace(find, replace)
        self.table.redraw()

    # Merge user input labels with current mappings and replot
    def updateLabels(self):
        df = self.table.model.df.copy(deep=True)
        # Update the color map according to the user specified labels
        self.colorCustomLabels()
        # Fill in the Color column based on unique user inputted labels
        # df = self.assignColors(df)
        # Update short names in each of the main dfs
        self.analyzerData.levelData.loadedData.update_short_names(df[KEY_METRICS+SHORT_NAME_METRICS], self.level)

    def exportCSV(self, table):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        table.model.df.to_csv(export_file_path, index=False, header=True)

class MappingsData(AnalyzerData):
    def __init__(self, data, level):
        super().__init__(data, level, "Mappings")

class MappingsTab(AnalyzerTab):
    def __init__(self, parent):
        super().__init__(parent, MappingsData)
        self.table = Table(self, dataframe=pd.DataFrame(), showtoolbar=False, showstatusbar=True)
        self.edit_button = tk.Button(self, text="Edit", command=self.editMappings)
        # self.update_button = tk.Button(self, text="Update", command=self.updateMapping)
        self.table.show()
        self.edit_button.grid(row=10, column=0)
        # self.update_button.grid(row=10, column=1, sticky=tk.W)
        # TODO: Fix showing/hiding intermediate mappings
        #if gui.loadedData.removedIntermediates: tk.Button(self, text="Show Intermediates", command=self.showIntermediates).grid(row=3, column=1)
        #else: tk.Button(self, text="Remove Intermediates", command=self.removeIntermediates).grid(row=3, column=1)

    def notify(self, data):
        self.table.model.df = self.analyzerData.levelData.mapping_df
        self.table.redraw()

    def addMapping(self):
        # extract timestamp,name,short_name from selected before and after to add to mappings
        toAdd = pd.DataFrame()
        toAdd['Before Timestamp'] = [int(self.before_selected.get().rsplit('[')[2][:-1])]
        toAdd['Before Name'] = [self.before_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['After Timestamp'] = [int(self.after_selected.get().rsplit('[')[2][:-1])]
        toAdd['After Name'] = [self.after_selected.get().split(']')[1].split('[')[0][1:-1]]
        toAdd['Difference'] = self.analyzerData.df.loc[(self.analyzerData.df[NAME] == toAdd['After Name'][0]) & (self.analyzerData.df[TIMESTAMP] == toAdd['After Timestamp'][0])][VARIANT].iloc[0]
        self.analyzerData.levelData.loadedData.add_mapping(self.analyzerData.level, toAdd)
    
    def removeMapping(self):
        toRemove = pd.DataFrame()
        toRemove['Before Name'] = [self.before_selected.get().split(']')[1].split('[')[0][1:-1]]
        toRemove['Before Timestamp'] = [int(self.before_selected.get().rsplit('[')[2][:-1])]
        toRemove['After Name'] = [self.after_selected.get().split(']')[1].split('[')[0][1:-1]]
        toRemove['After Timestamp'] = [int(self.after_selected.get().rsplit('[')[2][:-1])]
        self.analyzerData.levelData.loadedData.remove_mapping(self.analyzerData.level, toRemove)

    # def placeholderCheck(self):
    #     # Add placeholder row if current mappings table is now empty for proper GUI display
    #     if self.mappings.empty:
    #         self.table.model.df = pd.DataFrame(columns=['Before Name', 'Before Timestamp', 'After Name', 'After Timestamp', SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference', 'DataSource', 'Before Variant', 'After Variant'])
    #         self.table.model.df = self.table.model.df.append(pd.Series(name='temp'))
    #     else: self.table.model.df = self.mappings

    def updateMapping(self):
        # Update observers with the new mappings
        self.analyzerData.loadedData.update_mapping(self.analyzerData.level)

    def editMappings(self):
        options = "[" + self.analyzerData.df[SHORT_NAME] + "] " + self.analyzerData.df[NAME] + " [" + self.analyzerData.df[TIMESTAMP].map(str) + "]"
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

    # def selectAction(self, metric):
    #     self.choice = metric
    #     self.win.destroy()

    # def showIntermediates(self):
    #     self.tab.data.loadedData.mapping = self.tab.data.loadedData.orig_mapping.copy(deep=True)
    #     self.tab.data.loadedData.add_speedup(self.tab.data.loadedData.mapping, self.tab.data.loadedData.summaryDf)
    #     self.tab.data.loadedData.removedIntermediates = False
    #     data_tab_pairs = [(self.tab.data.gui.qplotData, self.tab.data.gui.c_qplotTab), (self.tab.data.gui.trawlData, self.tab.data.gui.c_trawlTab), \
    #         (self.tab.data.gui.siplotData, self.tab.data.gui.c_siPlotTab), (self.tab.data.gui.customData, self.tab.data.gui.c_customTab), \
    #         (self.tab.data.gui.coverageData, self.tab.data.gui.c_summaryTab)]
    #     for data, tab in data_tab_pairs:
    #         data.notify(self.tab.data.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.variants, scale=tab.x_scale+tab.y_scale)
    
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

class DataTabData(AnalyzerData):
    class ColumnFilter:
        def __init__(self, column):
            self.column = column
            self.string = ''
            self.fn = None

        def set_string(self, string):
            self.string = string

        def set_fn(self, fn):
            self.fn = fn
        
        def apply(self, df):
            mask = [self.fn(entry, self.string) for entry in df[self.column].astype(str)]
            return mask

    def __init__(self, data, level):
        super().__init__(data, level, "DataTabData")
        self.columnFilters = {}

    def filterMask(self, df):
        mask = pd.Series([True] * len(df))
        for col, filter in self.columnFilters.items():
            mask = mask & filter.apply(df)
        return mask

    def removeFilter(self, column):
        if column in self.columnFilters:
            self.columnFilters.pop(column)
            self.updateFilter()

    def removeAllFilters(self):
        if self.columnFilters:
            self.columnFilters = {}
            self.updateFilter()

    def findOrCreateFilter(self, column):
        return copy.deepcopy(self.columnFilters[column]) if column in self.columnFilters else DataTabData.ColumnFilter(column)

    def setFilter(self, filter):
        self.columnFilters[filter.column] = filter
        self.updateFilter()
    
    def updateFilter(self):
        mask = self.filterMask(self.df)
        # Currently mask contains everything that should be shown (starts with) so send in the ~mask
        self.levelData.guiState.setFilterMask(~mask)

    # def notify(self, data):
    #     self.notify_observers()

class DataTab(AnalyzerTab):

    #Override table class for customized behavior.  SEE: https://readthedocs.org/projects/pandastable/downloads/pdf/latest/ 
    class DataTable(Table):
        def __init__(self, parent):
            super().__init__(parent, dataframe=pd.DataFrame(columns=KEY_METRICS), showtoolbar=False, showstatusbar=True)
            self.parent = parent
            options = {'align': 'w', 'cellbackgr': '#F4F4F3', 'cellwidth': 80, 'colheadercolor': '#535b71', 'floatprecision': 2, 
                       'font': 'Arial', 'fontsize': 10, 'fontstyle': '', 'grid_color': '#ABB1AD', 
                       'linewidth': 1, 'rowheight': 22, 'rowselectedcolor': '#E4DED4', 'textcolor': 'black'}
            config.apply_options(options, self)
            self.doneSetWrap = False
            #self.show()
            #self.setWrap()
            
        def handle_left_click(self, event):
            #rowclicked = self.get_row_clicked(event)
            #colclicked = self.get_col_clicked(event)
            #print(f'leftclicked: ({rowclicked}, {colclicked})')
            # TODO: add selection
            super().handle_left_click(event)

        def show(self):
            super().show()
            # NOTE: Has to do setWrap() after finishing show() so override and call it
            self.setWrap()

        # Note this will replace the original menu.  
        # In progress checking with developers to add the items instead of replacement..
        def popupMenu(self, event, rows=None, cols=None, outside=None):
            #popupmenu1 = super().popupMenu(event, rows, cols, outside)
            popupmenu = tk.Menu(self, tearoff = 0)
            def popupFocusOut(event):
                popupmenu.unpost() 
                #mymenu = tk.Menu(popupmenu, tearoff = 0)
                #popupmenu.add_cascade(label='Cape', menu=mymenu)
            popupmenu.add_command(label='Highlight Point', command=lambda: self.highlight(event, rows, cols, outside))
            popupmenu.add_command(label='Unhighlight Point', command=lambda: self.unhighlight(event, rows, cols, outside))
            popupmenu.add_command(label='Remove Point', command=lambda: self.remove(event, rows, cols, outside))
            popupmenu.add_command(label='Toggle Label', command=lambda: self.toggleLabel(event, rows, cols, outside))
            popupmenu.add_command(label='Filter Column', command=lambda: self.filterColumn(event, rows, cols, outside), 
                                  state=tk.NORMAL if len(cols) == 1 else tk.DISABLED)
            popupmenu.add_command(label='Remove Filter', command=lambda: self.removeFilter(event, rows, cols, outside), 
                                  state=tk.NORMAL if len(cols) == 1 else tk.DISABLED)
            popupmenu.add_command(label='Remove All Filters', command=lambda: self.removeAllFilters(event, rows, cols, outside), 
                                  state=tk.NORMAL if len(cols) == 1 else tk.DISABLED)
            popupmenu.add_command(label='Stable Sort', command=lambda: self.stableSort(event, rows, cols, outside))
            popupmenu.add_command(label='Sort Numerically', command=lambda: self.sortNumerically(event, rows, cols, outside),
                                  state=tk.NORMAL if len(cols) == 1 else tk.DISABLED)

            popupmenu.bind("<FocusOut>", popupFocusOut)
            popupmenu.focus_set()
            popupmenu.post(event.x_root, event.y_root)
            return popupmenu

        def remove(self, event, rows, cols, outside):
            #rowclicked = self.get_row_clicked(event)
            #colclicked = self.get_col_clicked(event)
            #print(f'remove: ({rowclicked}, {colclicked})')
            self.parentframe.removeData(self.model.df.iloc[rows][KEY_METRICS])

        def highlight(self, event, rows, cols, outside):
            self.parentframe.highlightData(self.model.df.iloc[rows][KEY_METRICS])

        def unhighlight(self, event, rows, cols, outside):
            self.parentframe.unhighlightData(self.model.df.iloc[rows][KEY_METRICS])

        def toggleLabel(self, event, rows, cols, outside):
            self.parentframe.toggleLabelData(self.model.df.iloc[rows][KEY_METRICS])

        def filterColumn(self, event, rows, cols, outside):
            assert len(cols) == 1
            DataTab.FilterDialog(self.parentframe, self.model.df.columns[cols[0]])

        def removeFilter(self, event, rows, cols, outside):
            assert len(cols) == 1
            self.parentframe.removeFilter(self.model.df.columns[cols[0]])

        def removeAllFilters(self, event, rows, cols, outside):
            self.parentframe.removeAllFilters()

        def stableSort(self, event, rows, cols, outside):
            colnames = self.model.df.columns[cols]
            self.model.df.sort_values(by=list(colnames), ascending=True, inplace=True, ignore_index=True, kind='mergesort')
            self.redraw()

        def sortNumerically(self, event, rows, cols, outside):
            assert len(cols) == 1
            colname = self.model.df.columns[cols[0]]
            try:
                self.model.df['_SortKey'] = self.model.df[colname].astype(float)
            except:
                tk.messagebox.showerror("Numerical Sort Error", 
                                        f"Error attempting to convert column '{colname}' to float.") 
                return
            self.model.df.sort_values(by=['_SortKey'], ascending=True, inplace=True, ignore_index=True, kind='mergesort')
            self.model.df.drop(columns=['_SortKey'], inplace=True)
            self.redraw()

        # _highlighted column expected in out_df
        # will be used but not displayed in table
        def update_preserve_order(self, out_df):
            cnt_df = self.model.df
            #cnt_df['_highlighted'] = None
            if not cnt_df.empty:
                merged = pd.merge(cnt_df, out_df[KEY_METRICS+['_highlighted']], on=KEY_METRICS, how='outer', indicator='Exist')
                bothMask= (merged.Exist == 'both')
                addedMask= (merged.Exist == 'right_only')
                # 'left_only' are row to be dropped so ignored
                merged.drop(columns=['Exist'], inplace=True)
                result_df = merged[bothMask]
                if (addedMask.any()):
                    merged_in = pd.merge(out_df, merged[addedMask][KEY_METRICS], on=KEY_METRICS, how='inner')
                    result_df= result_df.append(merged_in, ignore_index=True)
                # Take the out_df order and append rest of cnt_df columns
                combined_column_order = list(out_df.columns) + [c for c in cnt_df.columns if c not in out_df.columns]
                result_df = result_df[combined_column_order]
            else:
                result_df = out_df
                
            result_df = result_df.reset_index(drop=True)
            result_df = self.parentframe.filter(result_df)
            highlightedMask = result_df['_highlighted']
            self.model.df = result_df.drop(columns=['_highlighted'])
            self.resetColors()
            self.setRowColors(rows=result_df.index[highlightedMask].to_list(), clr='red', cols='all')
            self.redraw()
            
    class FilterDialog(tk.simpledialog.Dialog):
        def __init__(self, parent, column):
            self.filter = parent.findOrCreateFilter(column)
            super().__init__(parent, title="Filter")

        def body(self, master):
            # Add stuff to master frame
            self.filter_selected = tk.StringVar(value='Starts with')
            self.filter_options = {'Starts with':str.startswith, 'Contains':str.__contains__, 'Equals':str.__eq__}
            self.filter_menu = tk.OptionMenu(master, self.filter_selected, *self.filter_options)

            self.entry_text = tk.StringVar()
            entry = tk.Entry(master, textvariable=self.entry_text)
            self.filter_menu.grid(row=0, column=0, padx=10, pady=10)
            entry.grid(row=0, column=1, padx=10, pady=10)

            # GUI component Will work on the self.filter object

        def buttonbox(self):
            box = tk.Frame(self)
            apply_button = tk.Button(box, text="Apply", command=self.apply)
            apply_button.pack(pady=10)
            box.pack()

        def apply(self):
            self.filter.set_string(self.entry_text.get())
            self.filter.set_fn(self.filter_options[self.filter_selected.get()])
            # Done so set filter back 
            self.parent.setFilter(self.filter)
            self.destroy()
    
    def __init__(self, parent, metrics=[], variants=[]):
        super().__init__(parent, DataTabData)
        # self.summaryTable = Table(self, dataframe=df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)[metrics], showtoolbar=False, showstatusbar=True)
        self.summaryTable = DataTab.DataTable(self)
        self.table_button_frame = tk.Frame(self)
        self.table_button_frame.grid(row=4, column=1)
        self.export_summary_button = tk.Button(self.table_button_frame, text="Export Summary Sheet", command=lambda: exportCSV(self.analyzerData.df))
        self.export_colored_summary_button = tk.Button(self.table_button_frame, text="Export Colored Summary", command=lambda: exportXlsx(self.analyzerData.df))
        #self.export_rawcsv_button = tk.Button(self.table_button_frame, text="Export Shown Points as Raw CSV", command=self.exportShownDataRawCSV)
        self.move_column_first_button = tk.Button(self.table_button_frame, text="Move Column(s) First", command=self.moveColumnsFirst)
        self.summaryTable.show()
        self.export_summary_button.grid(row=0, column=0)
        self.export_colored_summary_button.grid(row=0, column=1)
        #self.export_rawcsv_button.grid(row=0, column=2)
        self.move_column_first_button.grid(row=0, column=2)
    
    # def exportShownDataRawCSV(self):
    #     self.analyzerData.loadedData.exportShownDataRawCSV(tk.filedialog.asksaveasfilename(defaultextension=".raw.csv", filetypes=[("Cape Raw Data", "*.raw.csv")]))

    def setupGuiState(self, guiState):
        guiState.add_observer(self)

    def removeData(self, nameTimestampDf):
        self.guiState.removeData(nameTimestampDf)

    def highlightData(self, nameTimestampDf):
        self.guiState.highlightData(nameTimestampDf)

    def unhighlightData(self, nameTimestampDf):
        self.guiState.unhighlightData(nameTimestampDf)

    def toggleLabelData(self, nameTimestampDf):
        self.guiState.toggleLabelData(nameTimestampDf)

    def setupAnalyzerData(self, analyzerData):
        analyzerData.add_observer(self)

    def findOrCreateFilter(self, column):
        return self.analyzerData.findOrCreateFilter(column)

    def setFilter(self, filter):
        self.analyzerData.setFilter(filter)

    def removeFilter(self, column):
        self.analyzerData.removeFilter(column)

    def removeAllFilters(self):
        self.analyzerData.removeAllFilters()

    def filter(self, df): 
        return df[self.analyzerData.filterMask(df)]

    class ChooseColumnDialog(tk.simpledialog.Dialog):
        def body(self, master):
            self.metric = tk.StringVar(value='Metric')
            self.menu = AxesTab.all_metric_menu(master, self.metric, group=True)
            self.menu.grid(row=0, column=0)
            return self.menu

        def apply(self):
            self.result = self.metric.get()
            if self.result == 'Metric': self.result = None
            elif self.result in PLOT_METRICS: self.result = PLOT_METRICS[self.result]
            elif self.result in CATEGORIZED_METRICS: self.result = CATEGORIZED_METRICS[self.result]
            else: self.result = [self.result]
        
    def moveColumnsFirst(self):
        columns = DataTab.ChooseColumnDialog(self).result
        if columns:
            self.analyzerData.moveColumnsFirst(columns)
    
    def notify(self, data):
        # Update table with latest loadedData df
        out_df = self.analyzerData.df[[m for m in self.analyzerData.columnOrder if m in self.analyzerData.df.columns]]
        selectedMask = self.guiState.get_selected_mask(self.analyzerData.df)
        out_df['_highlighted'] = self.guiState.get_highlighted_mask(self.analyzerData.df)
        if selectedMask.any(): 
            out_df = out_df[selectedMask]
        if not self.guiState.showHiddenPointInTable: 
            hiddenMask = self.guiState.get_hidden_mask(self.analyzerData.df)
            out_df = out_df[~hiddenMask]
        out_df.sort_values(by=MN.COVERAGE_PCT, ascending=False, inplace=True)
        self.summaryTable.update_preserve_order(out_df)

class FilteringData(AnalyzerData):
    def __init__(self, data, level):
        super().__init__(data, level, "FilteringData")

class FilteringTab(AnalyzerTab):
    def __init__(self, parent):
        super().__init__(parent, FilteringData)
        self.setupThreshold()
        self.setOptions()
        self.buildActionSelector()
        # Grid setup
        self.threshold_frame.grid(row=0, column=2, sticky=tk.NW)
        self.metric_menu.grid(row=0, column=1, sticky=tk.N)
        self.min_label.grid(row=1, column=1, sticky=tk.NW)
        self.min_entry.grid(row=1, column=2, sticky=tk.NW)
        self.max_label.grid(row=2, column=1, sticky=tk.NW)
        self.max_entry.grid(row=2, column=2, sticky=tk.NW)
        self.action_menu.grid(row=3, column=1, pady=10, sticky=tk.NW)
        self.update_button.grid(row=0, column=3, sticky=tk.N)
        self.selectPointCb.grid(row=4, column=1, sticky=tk.N)
        self.showHiddenCb.grid(row=4, column=2, sticky=tk.N)

    def notify(self, data):
        if self.analyzerData.df.empty:
            return
        self.buildPointSelector()
        self.buildVariantSelector()
        self.pointSelector.grid(row=0, column=0)
        self.variantSelector.grid(row=0, column=1)

    def buildActionSelector(self):
        self.action_selected = tk.StringVar(value='Choose Action')
        self.action_selected.trace('w', self.action_selected_callback)
        action_options = ['Choose Action', 'Select Point', 'Highlight Point', 'Remove Point', 'Toggle Label']
        self.action_menu = tk.OptionMenu(self.threshold_frame, self.action_selected, *action_options)
        self.action_menu['menu'].insert_separator(1)

    def action_selected_callback(self, *args):
        self.analyzerData.guiState.action_selected = self.action_selected.get()

    def buildVariantSelector(self):
        all_variants = self.analyzerData.df[VARIANT].unique()
        selected_variants = self.analyzerData.variants
        self.variantSelector = VariantSelector(self, all_variants, selected_variants)
        # select_all = tk.Button(self, text='Select All', command= lambda val=1 : self.variantSelector.set_all(val))
        # deselect_all = tk.Button(self, text='Deselect All', command= lambda val=0 : self.variantSelector.set_all(val))
        # select_all.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)
        # deselect_all.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)

    def buildPointSelector(self):
        options = ('[' + self.analyzerData.df[SHORT_NAME] + '] ' + self.analyzerData.df[NAME] + ' [' + self.analyzerData.df[TIMESTAMP].astype(str) + ']').tolist()
        self.names = (self.analyzerData.df[NAME] + self.analyzerData.df[TIMESTAMP].astype(str)).tolist()
        self.pointSelector = PointSelector(self, options, self.analyzerData.guiState.hidden, self.names)
        # self.pointSelector.restoreState(self.stateDictionary)

    def setOptions(self):
        self.metric_menu = AxesTab.all_metric_menu(self.threshold_frame, self.metric_selected)
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
        # Update GUI State with selected filters
        self.update_button = tk.Button(self, text='Update', command=self.updateFilter)
        selectPointVar = tk.IntVar(value=1)  
        self.selectPointCb = tk.Checkbutton(self.threshold_frame, var=selectPointVar, text='Select Point', onvalue=1, offvalue=0, 
                                            command=lambda: self.guiState.setSelectPoint(selectPointVar.get()==1))
        showHiddenInTableVar = tk.IntVar(value=0)  
        self.showHiddenCb = tk.Checkbutton(self.threshold_frame, var=showHiddenInTableVar, text='Show Hidden Point in Table', onvalue=1, offvalue=0, 
                                            command=lambda: self.guiState.setShowHiddenInTable(showHiddenInTableVar.get()==1))
    
    def updateFilter(self):
        names = self.pointSelector.getUncheckedNames()
        variants = self.variantSelector.getCheckedVariants()
        metric = self.metric_selected.get()
        if metric == 'Choose Metric': metric = ''
        self.analyzerData.setFilter(metric, self.min_num.get(), self.max_num.get(), names, variants)
        # Update the point selector to reflect the metric/variant filtering
        self.pointSelector.restoreState(self.analyzerData.guiState.hidden)

class GuideTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        # self.tab = tab
        # State GUI
        self.canvas = tk.Canvas(self, width=1200, height=380)
        self.canvas.pack(side=tk.LEFT, anchor=tk.NW)
        self.fsm = FSM()
        self.fsm.add_observer(self)

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_fsm_buttons()
        self.refresh()

        #self.proceed_button.grid(column=0, row=0, sticky=tk.NW, pady=2)

        # detailsButton = tk.Button(self.buttonFrame, text="Details", command=self.fsm.details)
        # detailsButton.grid(column=0, row=1, sticky=tk.NW, pady=2)
        # prevButton = tk.Button(self.buttonFrame, text="Previous", command=self.fsm.previous)
        # prevButton.grid(column=0, row=2, sticky=tk.NW, pady=2)

    class FsmResetter:
        def __init__(self, fsm):
            self.fsm = fsm

        def notify(self, observable):
            # not to reset state (for demo or is right behavior in general - to explore)
            return
            self.fsm.reset_state()
            
            
    def setLoadedData(self, loadedData):
        loadedData.add_observer(GuideTab.FsmResetter(self.fsm))
     
    def create_fsm_buttons(self):
        self.button_map = dict()
        # get_all_transitions() return two arrays transition and transition name
        for transition, transition_name in zip(*self.fsm.get_all_transitions()):
            self.button_map[transition] = tk.Button(self.buttonFrame, text=transition_name, command=getattr(self.fsm, transition))
        # self.proceed_button = self.mk_button(text='Proceed', command=self.fsm.proceed)
        # self.previous_button = self.mk_button(text='Previous', command=self.fsm.previous)
        # self.abeg_1a_button = self.mk_button(text='Application Coverage (CoverageSummary)', command=self.fsm.appCoverage)
        # self.abeg_1b_button = self.mk_button(text='Library Time (TimeSummary)', command=self.fsm.libTime)
        # self.abeg_2a_button = self.mk_button(text='Show Rank Order (showRankOrder)', command=self.fsm.showRankOrder)
        # self.abeg_2b_button = self.mk_button(text='Show U-Curve (showUCurve)', command=self.fsm.showUCurve)
        # self.abeg_3_button = self.mk_button(text='Show Arithmetic Intensity (showArithIntensity)', command=self.fsm.showArithIntensity)
        # self.sido_analysis_button = self.mk_button(text='SIDO Analysis (sidoAnalysis)', command=self.fsm.sidoAnalysis)
        # self.swbias_reco_button = self.mk_button(text='SWBias Recommendations (swbiasReco)', command=self.fsm.swbiasReco)
        # self.show_oneview_button = self.mk_button(text='Show Oneview (showOneview)', command=self.fsm.showOneview)

    def reset_buttons(self):
        for button in self.button_map.values():
            button.grid_remove()
        row = 0
        for transition in self.fsm.get_next_transitions():
            self.button_map[transition].grid(column=0, row=row, sticky=tk.NW, pady=2)
            row = row + 1
    
    def refresh(self):
        self.reset_buttons()
        self.fsm.save_graph()
        self.update_canvas()

    def notify(self, observable):
        self.refresh()

    def update_canvas(self):
        image = Image.open(self.fsm.file)
        cwidth = self.canvas.winfo_reqwidth()
        cheight = self.canvas.winfo_reqheight()
        fitted_width = min(image.width, cwidth)
        fitted_height = min(image.height, cheight)
        scaling = min(fitted_width/image.width, fitted_height/image.height)
        image = image.resize((int(scaling*image.width), int(scaling*image.height)), Image.ANTIALIAS)

        self.img = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)
        self.canvas.update()
        

class Checklist(tk.Frame):
    def __init__(self, parent, options):
        tk.Frame.__init__(self, parent, bd=1, relief="sunken", background="white")
        self.parent=parent
        self.options = options
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar_x = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.checklist = tk.Text(self, width=40)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.checklist.pack(fill=tk.Y, expand=True)
        self.vars = []
        self.cbs = []
        self.buildChecklist()

    def buildChecklist(self):
        bg = self.cget("background")
        for option in self.options:
            var = tk.IntVar(value=1)
            self.vars.append(var)
            cb = tk.Checkbutton(self, var=var, text=option,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            self.checklist.window_create("end", window=cb)
            self.checklist.insert("end", "\n")
        self.configure()

    def configure(self):
        self.checklist.config(yscrollcommand=self.scrollbar.set)
        self.checklist.config(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar.config(command=self.checklist.yview)
        self.scrollbar_x.config(command=self.checklist.xview)
        self.checklist.configure(state="disabled")

    def set_all(self, val):
        for var in self.vars: var.set(val)

class VariantSelector(Checklist):
    def __init__(self, parent, options, selected):
        super().__init__(parent, options)
        self.selected = selected
        self.restoreState()
    
    def restoreState(self):
        for i, cb in enumerate(self.cbs):
            variant = cb['text']
            if variant not in self.selected: self.vars[i].set(0)
            else: self.vars[i].set(1)

    def getCheckedVariants(self):
        variants = []
        for i, cb in enumerate(self.cbs):
            value =  self.vars[i].get()
            if value:
                variants.append(cb['text'])
        return variants

class PointSelector(Checklist):
    def __init__(self, parent, options, hidden, names):
        super().__init__(parent, options)
        self.names = names
        self.restoreState(hidden)

    def restoreState(self, hidden):
        for i, var in enumerate(self.vars):
            name = self.names[i]
            if name in hidden: var.set(0)
            else: var.set(1)
            
    def getUncheckedNames(self):
        unchecked = []
        for index, var in enumerate(self.vars):
            if not var.get(): unchecked.append(self.names[index])
        return unchecked