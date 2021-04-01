import tkinter as tk
import pandas as pd
from tkinter import ttk
from plot_interaction import PlotInteraction
from utils import Observable, exportCSV, exportXlsx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from metric_names import MetricName as MN
from metric_names import KEY_METRICS, ALL_METRICS, CATEGORIZED_METRICS, PLOT_METRICS
import numpy as np
import copy
import os
from os.path import expanduser

# globals().update(MetricName.__members__)
class PerLevelGuiState(Observable):
    def __init__(self, levelData, level):
        super().__init__()
        self.level = level
        self.levelData = levelData
        # Should have size <= 3
        self.labels = []
        self.hidden = []
        self.highlighted = []
        self.selected = []
        self.label_visibility = {}
        # For data filtering
        # The following variants and filter metric set up a mask to select data point
        self.selectedVariants = []
        self.filterMetric = None
        self.filterMinThreshold = 0
        self.filterMaxThreshold = 0

        # Currently selected plot interaction action
        self.action_selected = 'Choose Action'

        # The final mask used to select data points
        self.selectedDataPoints = []

        # A map from color to color name for plotting
        self.color_map = pd.DataFrame(columns=KEY_METRICS + ['Label', 'Color'])

        # Cape paths
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.short_names_path = os.path.join(self.cape_path, 'short_names.csv')
        self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')
        # Column order for data table display.  All except KEY_METRICS.
        self.nonKeyColumnOrder = [m for m in ALL_METRICS if m not in KEY_METRICS] 
        self.guiDataDict = {}

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't save observers as they are GUI components
        del state['observers']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore observers to []
        self.observers = []

    def findOrCreateGuiData(self, guiDataClass):
        if guiDataClass not in self.guiDataDict:
            self.guiDataDict[guiDataClass] = guiDataClass(self.levelData, self.level)
        return self.guiDataDict[guiDataClass]
    
    def moveColumnFirst(self, column):
        if column in self.columnOrder:
            self.nonKeyColumnOrder = [column]+[m for m in self.nonKeyColumnOrder if m != column]
            self.updated_notify_observers()
        
    @property
    def columnOrder(self):
        return KEY_METRICS + self.nonKeyColumnOrder

    def toggleLabels(self, names, alpha):
        for name in names:
            self.label_visibility[name] = alpha
        self.updated_notify_observers()

    def toggleLabel(self, name, alpha):
        self.label_visibility[name] = alpha
        self.updated_notify_observers()

    def set_color_map(self, color_map_df):
        if 'Label' not in color_map_df: color_map_df['Label'] = ''
        color_map_df.fillna({'Color':'blue'}, inplace=True)
        self.color_map = color_map_df
        self.updated_notify_observers()

    def get_color_map(self):
        return self.color_map
    
    # Write methods to update the fields and then call 
    # self.loadedData.levelData[level].updated() to notify all observers
    def add_mapping(self, toAdd):
        all_mappings = pd.read_csv(self.mappings_path)
        all_mappings = all_mappings.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)
        all_mappings.to_csv(self.mappings_path, index=False)
        self.levelData.mapping = self.levelData.mapping.append(toAdd, ignore_index=True).drop_duplicates().reset_index(drop=True)

    def remove_mapping(self, toRemove):
        all_mappings = pd.read_csv(self.mappings_path)
        to_update = [all_mappings, self.levelData.mapping]
        for mapping in to_update:
            mapping.drop(mapping[(mapping['Before Name']==toRemove['Before Name'].iloc[0]) & \
                        (mapping['Before Timestamp']==toRemove['Before Timestamp'].iloc[0]) & \
                        (mapping['After Name']==toRemove['After Name'].iloc[0]) & \
                        (mapping['After Timestamp']==toRemove['After Timestamp'].iloc[0])].index, inplace=True)
        all_mappings.to_csv(self.mappings_path, index=False)

    def reset_labels(self):
        self.labels = []
        self.updated_notify_observers()

    def setFilter(self, metric, minimum, maximum, names, variants):
        self.filterMetric = metric
        self.filterMinThreshold = minimum
        self.filterMaxThreshold = maximum
        self.selectedVariants = variants
        self.hidden = names
        # Add codelet names outside of filtered range to hidden names
        if metric:
            df = self.levelData.df.loc[(self.levelData.df[metric] < minimum) | (self.levelData.df[metric] > maximum)]
            self.hidden.extend((df[MN.NAME]+df[MN.TIMESTAMP].astype(str)).tolist())
        self.hidden = list(dict.fromkeys(self.hidden))
        self.showLabels()
        self.hideLabels(self.hidden)
        self.updated_notify_observers()

    def removePoints(self, names):
        self.hidden.extend(names)
        self.hidden = list(dict.fromkeys(self.hidden))
        for name in names:
            self.label_visibility[name] = 0
        self.updated_notify_observers()

    def selectPoints(self, names):
        self.selected = names
        self.updated_notify_observers()

    def showPoints(self, names):
        self.hidden = [name for name in self.hidden if name not in names]
        for name in names:
            self.label_visibility[name] = 1
        self.updated_notify_observers()

    def isHidden(self, name):
        return name in self.hidden

    def hideLabels(self, names):
        for name in names:
            self.label_visibility[name] = 0

    def showLabels(self):
        for name in self.label_visibility:
            self.label_visibility[name] = 1
    
    def labelVisbility(self, name):
        alpha = 1
        if name in self.label_visibility:
            alpha = self.label_visibility[name]
        return alpha

    def highlightPoints(self, names):
        self.highlighted.extend(names)
        self.highlighted = list(dict.fromkeys(self.highlighted))
        self.updated_notify_observers()

    def unhighlightPoints(self, names):
        self.highlighted = [name for name in self.highlighted if name not in names]
        self.updated_notify_observers()

    def setLabels(self, metrics):
        self.labels = metrics
        self.updated_notify_observers()

    def reset_state(self):
        self.hidden = []
        self.highlighted = []

    def get_encoded_names(self, df):
        return df[MN.NAME] + df[MN.TIMESTAMP].astype(str)

    def get_hidden_mask(self, df):
        return self.get_encoded_names(df).isin(self.hidden)

    def get_highlighted_mask(self, df):
        return self.get_encoded_names(df).isin(self.highlighted)

    def get_selected_mask(self, df):
        return self.get_encoded_names(df).isin(self.selected)
        

    # Plot interaction objects for each plot at this level will be notified to avoid a complete redraw

class AnalyzerData(Observable):
    def __init__(self, levelData, level, name):
        super().__init__()
        self.levelData = levelData
    #    self.mappings = pd.DataFrame()
        self.level = level
        self.name = name
        #self.gui = gui
        #self.root = root
        self.scale = "linear"
        self.x_axis = None
        self.y_axis = None
        # Watch for updates in loaded data
        #levelData.loadedData.add_observer(self)
        #levelData.add_observer(self)

    # Make df a property that refer to the right dataframe
    @property
    def df(self):
        # Get correct dataframe
        return self.levelData.df

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't save observers as they are GUI components
        del state['observers']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore observers to []
        self.observers = []

    # @property
    # def guiState(self):
    #     return self.loadedData.levelData[self.level].guiState

    @property
    def mappings(self):
        return self.levelData.mapping

    @property
    def variants(self):
        return self.levelData.guiState.selectedVariants

    @property
    def common_columns_start(self):
        return self.levelData.common_columns_start

    @property
    def common_columns_end(self):
        return self.levelData.common_columns_end

    @property
    def short_names_path(self):
        return self.levelData.short_names_path

    @property
    def guiState(self):
        return self.levelData.guiState

    @property
    def columnOrder(self):
        return self.levelData.guiState.columnOrder

    # Move need to move this to controller class (Plot interaction?)
    def moveColumnFirst(self, column):
        self.levelData.guiState.moveColumnFirst(column)

    def setFilter(self, metric, minimum, maximum, names, variants):
        self.levelData.guiState.setFilter(metric, minimum, maximum, names, variants)

    @property
    def capacityDataItems(self):
        return self.levelData.capacityDataItems

    @property
    def siDataItems(self):
        return self.levelData.siDataItems
        
    @property
    def satAnalysisDataItems(self):
        return self.levelData.satAnalysisDataItems

    def notify(self, loadedData):
        print(f"{self.name} Notified from ", loadedData)
        self.updated_notify_observers()

    def update_axes(self, scale, x_axis, y_axis):
        self.scale = scale
        self.y_axis = "{}".format(y_axis)
        self.x_axis = "{}".format(x_axis)
        self.updated_notify_observers()
        
    def merge_metrics(self, df, metrics):
        self.levelData.merge_metrics(df, metrics)

class GuiBaseTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.analyzerData = None

    def setAnalyzerData(self, analyzerData):
        assert (analyzerData is not None)
        self.analyzerData = analyzerData
        self.setupAnalyzerData(analyzerData)
        #analyzerData.add_observer(self)

    def setupAnalyzerData(self, analyzerData):
        pass

    @property
    def level(self):
        return self.analyzerData.level
        
    @property
    def mappings(self):
        return self.analyzerData.mappings
        
    @property
    def levelData(self):
        return self.analyzerData.levelData

    @property
    def guiState(self):
        return self.levelData.guiState

class AnalyzerTab(GuiBaseTab):
    def __init__(self, parent, analyzerDataClass):
        super().__init__(parent)
        self.analyzerDataClass = analyzerDataClass

    # Do nothing.  Sublcass override to set up notify()
    def setupGuiState(self, guiState):
        pass

    def setupLevelData(self, levelData):
        # GUI tabs listen to levelData
        levelData.add_observer(self)

    def setLevelData(self, levelData):
        guiState = levelData.guiState
        self.setupGuiState(guiState)
        self.setupLevelData(levelData)
        self.setAnalyzerData(guiState.findOrCreateGuiData(self.analyzerDataClass))
        
    # def setAnalyzerData(self, analyzerData):
    #     super().setAnalyzerData(analyzerData)
    #     #self.level = analyzerData.level
    #     #self.name = analyzerData.name
    #     #self.mappings_path = self.data.loadedData.mappings_path
    #     #self.short_names_path = self.data.short_names_path
    #     return self

    
class PlotTab(AnalyzerTab):
    class PlotUpdater:
        def __init__(self, plotTab):
            self.plotTab = plotTab

        def notify(self, data):
            self.plotTab.try_adjust_plot()
    
    def __init__(self, parent, analyzerDataClass, title='', x_axis='', y_axis='', extra_metrics=[], name=''):
        super().__init__(parent, analyzerDataClass)
        self.title = 'FE_tier1'
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = x_axis
        self.y_axis = self.orig_y_axis = y_axis
        self.variants = []
        self.current_labels = []
        self.extra_metrics = extra_metrics
        self.window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        self.window.pack(fill=tk.BOTH, expand=True)
        # Setup Plot Frames
        self.plotFrame = tk.Frame(self.window)
        self.canvasFrame = tk.Frame(self.plotFrame)
        self.chartButtonFrame = tk.Frame(self.plotFrame)
        self.plotFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chartButtonFrame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvasFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Plot interacting buttons
        self.plotInteraction = PlotInteraction()
        # self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.plotInteraction.saveState)
        self.adjust_button = tk.Button(self.chartButtonFrame, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.chartButtonFrame, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.chartButtonFrame, text='Show Points')
        self.unhighlight_button = tk.Button(self.chartButtonFrame, text='Unhighlight')
        # Notebook of plot specific tabs
        self.tab_note = ttk.Notebook(self.window)
        self.axesTab = AxesTab(self.tab_note, self)
        self.tab_note.add(self.axesTab, text='Axes')
        self.labelTab = LabelTab(self.tab_note, self)
        self.tab_note.add(self.labelTab, text='Labels')
        self.plotData = None
        # Update names for plot buttons
        self.show_markers_button['command'] = self.showPoints
        self.unhighlight_button['command'] = self.unhighlightPoints
        # Grid Layout
        self.axesTab.render()
        self.labelTab.render()
        # Grid Layout
        self.tab_note.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.unhighlight_button.grid(column=4, row=0, sticky=tk.S, pady=2)
        self.show_markers_button.grid(column=3, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.chartButtonFrame.grid_rowconfigure(0, weight=1)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tab_note, stretch='never')
        self.plot = None
        self.plotUpdater = PlotTab.PlotUpdater(self)

    def adjustText(self):
        self.plotData.adjustText()
    
    def toggleLabels(self):
        alpha = 1
        if self.toggle_labels_button['text'] == 'Hide Labels':
            self.toggle_labels_button['text'] = 'Show Labels'
            alpha = 0
        else:
            self.toggle_labels_button['text'] = 'Hide Labels'
        self.analyzerData.guiState.toggleLabels(self.plotData.names, alpha)
        self.plotData.checkAdjusted()

    def showPoints(self):
        self.analyzerData.guiState.showPoints(self.plotData.names)
    
    def unhighlightPoints(self):
        self.analyzerData.guiState.unhighlightPoints(self.plotData.names)


    def setupGuiState(self, guiState):
        super().setupGuiState(guiState)
        guiState.add_observer(self.plotUpdater)
    
    def setupAnalyzerData(self, analyzerData):
        super().setupAnalyzerData(analyzerData)
        analyzerData.add_observer(self.plotUpdater)
        #self.labelTab.setAnalyzerData(data)
        #self.plotInteraction.setAnalyzerData(data)

    def setLevelData(self, levelData):
        super().setLevelData(levelData)
        self.labelTab.setLevelData(levelData)

    # Subclass needs to override this method
    def mk_plot(self):
        raise Exception("Method needs to be overriden to create plots")

    # Subclass needs to override this method. Return self.plot to ease chaining
    def update_plot(self):
        assert self.plot is not None
        return self.plot.setLevelData(self.analyzerData.levelData).setLevel(self.analyzerData.level) \
            .setScale(self.analyzerData.scale).setXaxis(self.analyzerData.x_axis).setYaxis(self.analyzerData.y_axis)\
                .setMapping(self.analyzerData.mappings).setShortNamesPath(self.analyzerData.short_names_path)
    
    # Try to adjust current plot without replotting
    def try_adjust_plot(self):
        if not self.plot: return
        if self.analyzerData.x_axis == self.plot.x_axis and self.analyzerData.y_axis == self.plot.y_axis:
            # Can reuse plot if x- and y- axes are not changed
            self.plot.adjust_plot(self.analyzerData.scale)
        else:
            self.full_plot()
    
    # full fledge plotting of data
    def full_plot(self):
        # Update attributes
        self.df = self.analyzerData.df
        if self.df.empty:
            return

        if not self.plot:
            self.plot = self.mk_plot()
            self.plot.setupFrames(self.canvasFrame, self.chartButtonFrame)
        else:
            self.update_plot()

        self.plot.compute_and_plot()
        #self.fig, self.plotData = self.plot.fig, self.plot.plotData
        #self.plotInteraction.setPlotData(self.plotData)

        #self.variants = self.analyzerData.variants
        #self.metrics = metrics

        # Format columns for pandastable compatibility
        # self.df.columns = ["{}".format(i) for i in self.df.columns]
        # self.df.sort_values(by=MN.COVERAGE_PCT, ascending=False, inplace=True)
        # for missing in set(metrics)-set(self.df.columns):
        #     self.df[missing] = np.nan

    def get_metrics(self):
        metrics = copy.deepcopy(self.analyzerData.common_columns_start)
        metrics.extend(self.extra_metrics)
        metrics.extend(self.analyzerData.common_columns_end)
        return metrics
        
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        #metrics = self.get_metrics()
        self.full_plot()

    def resetTabValues(self):
        self.x_scale = self.orig_x_scale
        self.y_scale = self.orig_y_scale
        self.x_axis = self.orig_x_axis
        self.y_axis = self.orig_y_axis
        #self.variants = [self.data.loadedData.default_variant] #TODO: edit this out
        self.variants = []
        self.current_labels = []


class AxesTab(tk.Frame):
    @staticmethod
    def all_metric_menu(parent, var):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        main_menu.add_radiobutton(value=var.get(), label=var.get(), variable=var)
        main_menu.insert_separator(1)
        # TRAWL/QPlot/SIPlot metrics
        for category, metrics in PLOT_METRICS.items():
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label=category, menu=menu)
            for metric in metrics:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='All', menu=summary_menu)
        for category, metrics in CATEGORIZED_METRICS.items():
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        return menubutton

    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        #self.plotType = plotType
        # Axes metric options TODO: Should we limit the metrics allowed depending on the current plot?
        self.metric_label = tk.Label(self, text='Metrics:')
        self.y_selected = tk.StringVar(value='Choose Y Axis Metric')
        self.x_selected = tk.StringVar(value='Choose X Axis Metric')
        self.x_menu = AxesTab.all_metric_menu(self, self.x_selected)
        self.y_menu = AxesTab.all_metric_menu(self, self.y_selected)
        # Axes scale options
        self.scale_label = tk.Label(self, text='Scales:')
        self.yscale_selected = tk.StringVar(value='Choose Y Axis Scale')
        self.xscale_selected = tk.StringVar(value='Choose X Axis Scale')
        yscale_options = ['Choose Y Axis Scale', 'Linear', 'Log']
        xscale_options = ['Choose X Axis Scale', 'Linear', 'Log']
        self.yscale_menu = tk.OptionMenu(self, self.yscale_selected, *yscale_options)
        self.xscale_menu = tk.OptionMenu(self, self.xscale_selected, *xscale_options)
        self.yscale_menu['menu'].insert_separator(1)
        self.xscale_menu['menu'].insert_separator(1)
        # Update button to replot
        self.update = tk.Button(self, text='Update', command=self.update_axes)

        # x_options = ['Choose X Axis Metric', MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S, RECIP_TIME_LOOP_MHZ]
        # if self.plotType == 'Custom' or self.plotType == 'Scurve':
        #     x_menu = AxesTab.all_metric_menu(self, self.x_selected, self.tab.data.gui)
        #     y_menu = AxesTab.all_metric_menu(self, self.y_selected, self.tab.data.gui)
        # else:  
        #     if self.plotType == 'QPlot':
        #         y_options = ['Choose Y Axis Metric', MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_L3_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S]
        #     elif self.plotType == 'TRAWL':
        #         y_options = ['Choose Y Axis Metric', SPEEDUP_VEC, SPEEDUP_DL1]
        #     elif self.plotType == 'Summary':
        #         x_options.append(RECIP_TIME_LOOP_MHZ)
        #         y_options = ['Choose Y Axis Metric', COVERAGE_PCT, TIME_LOOP_S, TIME_APP_S, RECIP_TIME_LOOP_MHZ]
        #     else:
        #         x_options = ['Choose X Axis Metric']
        #         y_options = ['Choose Y Axis Metric']
        #     y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
        #     x_menu = tk.OptionMenu(self, self.x_selected, *x_options)
        #     y_menu['menu'].insert_separator(1)
        #     x_menu['menu'].insert_separator(1)

    def render(self):
        # Tab grid
        self.metric_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scale_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.x_menu.grid(row=1, column=0, padx=5, sticky=tk.W)
        self.y_menu.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.xscale_menu.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.yscale_menu.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.update.grid(row=3, column=0, padx=5, sticky=tk.NW)

    def hide(self):
        self.metric_label.grid_remove()
        self.scale_label.grid_remove()
        self.x_menu.grid_remove()
        self.y_menu.grid_remove()
        self.xscale_menu.grid_remove()
        self.yscale_menu.grid_remove()
        self.update.grid_remove()
    
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
        # Set user selected metrics/scales if they have changed at least one
        if self.x_selected.get() != 'Choose X Axis Metric' or self.y_selected.get() != 'Choose Y Axis Metric' or self.xscale_selected.get() != 'Choose X Axis Scale' or self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.analyzerData.update_axes(self.tab.x_scale + self.tab.y_scale, self.tab.x_axis, self.tab.y_axis)

class LabelTabData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Label')
        self.metrics = LabelTab.DUMMY_METRICS.copy()

    def setMetric(self, idx, value):
        self.metrics[idx] = value

    def getMetrics(self):
        return self.metrics
       

class LabelTab(AnalyzerTab):
    DUMMY_METRICS = ['Metric 1', 'Metric 2', 'Metric 3']
    def __init__(self, parent, tab):
        super().__init__(parent, LabelTabData)
        #self.parent = parent
        #self.tab = tab
        self.metrics = [self.mkStringVar(i) for i in range(3)]
        self.menus = [AxesTab.all_metric_menu(self, m) for m in self.metrics]
        #self.metric1 = tk.StringVar(value='Metric 1')
        #self.metric2 = tk.StringVar(value='Metric 2')
        #self.metric3 = tk.StringVar(value='Metric 3')
        #self.metrics = [self.metric1, self.metric2, self.metric3]
        # self.menu1 = AxesTab.all_metric_menu(self, self.metric[0])
        # self.menu2 = AxesTab.all_metric_menu(self, self.metric[1])
        # self.menu3 = AxesTab.all_metric_menu(self, self.metric[2])
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)

    # @property
    # def level(self):
    #     return self.data.level
    def mkStringVar(self, idx):
        metric = tk.StringVar(value=LabelTab.DUMMY_METRICS[idx])
        metric.trace('w', lambda *args: self.varChanged(idx))
        return metric

    def varChanged(self, idx):
        self.analyzerData.setMetric(idx, self.metrics[idx].get())
        


    @property
    def df(self):
        return self.levelData.df

    @property
    def current_metrics(self):
        return [metric.get() for metric in self.metrics if metric.get() not in LabelTab.DUMMY_METRICS]

    # @property
    # def mappings(self):
    #     return self.levelData.mapping

    # @property
    # def plotData(self):
    #     return self.tab.plotInteraction.plotData
    # Override so not to monitor levelData
    def setupLevelData(self, levelData):
        pass        
    # Monitor gui state changes instead
    def setupGuiState(self, guiState):
        guiState.add_observer(self)

    def setupAnalyzerData(self, analyzerData):
        self.setMetrics(analyzerData.getMetrics())

    def notify(self, data):
        if self.current_metrics != self.guiState.labels:
            self.resetMetrics()
            if self.guiState.labels: self.setMetrics(self.guiState.labels)

    def setMetrics(self, metrics):
        for i, metric in enumerate(metrics):
            self.metrics[i].set(metric)

    def render(self):
        self.menus[0].grid(row=0, column=0, padx = 10, pady=10, sticky=tk.NW)
        self.menus[1].grid(row=0, column=1, pady=10, sticky=tk.NW)
        self.menus[2].grid(row=0, column=2, padx = 10, pady=10, sticky=tk.NW)
        self.updateButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
        self.resetButton.grid(row=1, column=1, sticky=tk.NW)

    def resetMetrics(self):
        for metric, label in zip(self.metrics, LabelTab.DUMMY_METRICS):
            m.set(label)
        # self.metric1.set('Metric 1')
        # self.metric2.set('Metric 2')
        # self.metric3.set('Metric 3')

    def reset(self):
        self.guiState.reset_labels()

    def updateLabels(self):
        # TODO: merge mapping speedups into master dataframe to avoid this check
        new_metrics = [metric for metric in self.current_metrics if metric in self.df.columns.tolist()]
        if not new_metrics: return # User hasn't selected any label metrics
        self.guiState.setLabels(new_metrics)