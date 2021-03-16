import tkinter as tk
import pandas as pd
from tkinter import ttk
from plot_interaction import PlotInteraction
from utils import Observable, exportCSV, exportXlsx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab, DataTab
from metric_names import MetricName as MN
from metric_names import KEY_METRICS, ALL_METRICS, CATEGORIZED_METRICS
import numpy as np
import copy
import os
from os.path import expanduser

# globals().update(MetricName.__members__)
class PerLevelGuiState(Observable):
    def __init__(self, loadedData, level):
        super().__init__()
        self.level = level
        self.loadedData = loadedData
        # Should have size <= 3
        self.labels = []
        self.hidden = []
        self.highlighted = []
        # For data filtering
        # The following variants and filter metric set up a mask to select data point
        self.selectedVariants = []
        self.filterMetric = None
        self.filterMinThreshold = 0
        self.filterMaxThreshold = 0

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

    def moveColumnFirst(self, column):
        if column in self.columnOrder:
            self.nonKeyColumnOrder = [column]+[m for m in self.nonKeyColumnOrder if m != column]
            self.updated()
        
    @property
    def columnOrder(self):
        return KEY_METRICS + self.nonKeyColumnOrder

    def set_color_map(self, color_map_df):
        if 'Label' not in color_map_df: color_map_df['Label'] = ''
        color_map_df.fillna({'Color':'blue'}, inplace=True)
        self.color_map = color_map_df

    def get_color_map(self):
        return self.color_map
    
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

    def reset_labels(self):
        self.labels = []
        self.updated()

    def setFilter(self, metric, minimum, maximum, names, variants):
        self.filterMetric = metric
        self.filterMinThreshold = minimum
        self.filterMaxThreshold = maximum
        self.selectedVariants = variants
        self.hidden = names
        # Add codelet names outside of filtered range to hidden names
        if metric:
            df = self.loadedData.df.loc[(self.loadedData.df[metric] < minimum) | (self.loadedData.df[metric] > maximum)]
            self.hidden.extend((df[MN.NAME]+df[MN.TIMESTAMP].astype(str)).tolist())
        self.updated()

    def removePoints(self, names):
        self.hidden.extend(names)
        self.hidden = list(dict.fromkeys(self.hidden))
        self.updated()

    def showPoints(self, names):
        self.hidden = [name for name in self.hidden if name not in names]
        self.updated()

    def highlightPoints(self, names):
        self.highlighted.extend(names)
        self.highlighted = list(dict.fromkeys(self.highlighted))
        self.updated()

    def unhighlightPoints(self, names):
        self.highlighted = [name for name in self.highlighted if name not in names]
        self.updated()

    def setLabels(self, metrics):
        self.labels = metrics
        self.updated()

    def reset_state(self):
        self.hidden = []
        self.highlighted = []

    # Plot interaction objects for each plot at this level will be notified to avoid a complete redraw
    def updated(self):
        self.notify_observers()

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
    def variants(self):
        return self.loadedData.levelData[self.level].guiState.selectedVariants

    @property
    def columnOrder(self):
        return self.loadedData.levelData[self.level].guiState.columnOrder

    # Move need to move this to controller class (Plot interaction?)
    def moveColumnFirst(self, column):
        self.loadedData.levelData[self.level].guiState.moveColumnFirst(column)

    @property
    def capacityDataItems(self):
        return self.loadedData.levelData[self.level].capacityDataItems

    @property
    def siDataItems(self):
        return self.loadedData.levelData[self.level].siDataItems
        
    @property
    def satAnalysisDataItems(self):
        return self.loadedData.levelData[self.level].satAnalysisDataItems

    def notify(self, loadedData, update, variants, mappings):
        pass

    def merge_metrics(self, df, metrics):
        self.loadedData.merge_metrics(df, metrics, self.level)
    
class AnalyzerTab(tk.Frame):
    def __init__(self, parent, data, title='', x_axis='', y_axis='', extra_metrics=[], name='', ):
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
        self.extra_metrics = extra_metrics
        self.mappings_path = self.data.loadedData.mappings_path
        self.short_names_path = self.data.loadedData.short_names_path
        self.window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        self.window.pack(fill=tk.BOTH, expand=True)
        self.plotInteraction = PlotInteraction(self)
        # Setup Plot Frames
        self.plotFrame = tk.Frame(self.window)
        self.plotFrame2 = tk.Frame(self.plotFrame)
        self.plotFrame3 = tk.Frame(self.plotFrame)
        self.plotFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.plotFrame3.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.plotFrame2.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Plot interacting buttons
        # self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.plotInteraction.saveState)
        self.adjust_button = tk.Button(self.plotFrame3, text='Adjust Text', command=self.plotInteraction.adjustText)
        self.toggle_labels_button = tk.Button(self.plotFrame3, text='Hide Labels', command=self.plotInteraction.toggleLabels)
        self.show_markers_button = tk.Button(self.plotFrame3, text='Show Points')
        self.unhighlight_button = tk.Button(self.plotFrame3, text='Unhighlight')
        self.action_selected = tk.StringVar(value='Choose Action')
        action_options = ['Choose Action', 'Highlight Point', 'Remove Point', 'Toggle Label']
        self.action_menu = tk.OptionMenu(self.plotFrame3, self.action_selected, *action_options)
        self.action_menu['menu'].insert_separator(1)
        # Notebook of plot specific tabs
        self.tab_note = ttk.Notebook(self.window)
        self.axesTab = AxesTab(self.tab_note, self, self.name)
        self.tab_note.add(self.axesTab, text='Axes')
        self.labelTab = LabelTab(self.tab_note, self, self.level)
        self.tab_note.add(self.labelTab, text='Labels')

    @property
    def mappings(self):
        return self.data.mappings

    # Subclass needs to override this method
    def mk_plot(self):
        raise Exception("Method needs to be overriden to create plots")
    
    def setup(self, metrics):
        # Update attributes
        plot = self.mk_plot()
        plot.compute_and_plot()
        self.fig, self.textData = plot.fig, plot.plotData

        self.df = self.data.df
        self.variants = self.data.variants
        self.metrics = metrics
        # Update names for plot buttons
        self.show_markers_button['command'] = lambda names=self.textData['names'] : self.plotInteraction.showPoints(names)
        self.unhighlight_button['command'] = lambda names=self.textData['names'] : self.plotInteraction.unhighlightPoints(names)
        # NavigationToolbar2Tk can only be created if there isn't anything in the grid
        for slave in self.plotFrame3.grid_slaves():
            slave.grid_forget()
        # Refresh the canvas
        for slave in self.plotFrame2.pack_slaves():
            slave.destroy()
        # Store initial xlim and ylim for adjustText 
        self.plotInteraction.setLims()
        # Create canvas and toolbar for plot
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame2)
        self.canvas.mpl_connect('button_press_event', self.plotInteraction.onClick)
        self.canvas.mpl_connect('draw_event', self.plotInteraction.onDraw)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame3)
        # Grid Layout
        self.axesTab.render()
        self.labelTab.render()
        self.tab_note.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.toolbar.grid(column=7, row=0, sticky=tk.S)
        self.action_menu.grid(column=5, row=0, sticky=tk.S)
        self.unhighlight_button.grid(column=4, row=0, sticky=tk.S, pady=2)
        self.show_markers_button.grid(column=3, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.plotFrame3.grid_rowconfigure(0, weight=1)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, anchor=tk.N, padx=10)
        self.toolbar.update()
        self.canvas.draw()
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tab_note, stretch='never')

        # Format columns for pandastable compatibility
        self.df.columns = ["{}".format(i) for i in self.df.columns]
        self.df.sort_values(by=MN.COVERAGE_PCT, ascending=False, inplace=True)
        for missing in set(metrics)-set(self.df.columns):
            self.df[missing] = np.nan

    def get_metrics(self):
        metrics = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        metrics.extend(self.extra_metrics)
        metrics.extend(self.data.gui.loadedData.common_columns_end)
        return metrics
        
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = self.get_metrics()
        self.setup(metrics)

class LevelTab(tk.Frame):
    def __init__(self, parent, data):
        super().__init__(parent)
        if data is not None:
            data.add_observers(self)
            data.loadedData.levelData[data.level].guiState.add_observers(self)
        self.data = data
        self.level = data.level
        self.name = data.name

    @property
    def mappings(self):
        return self.data.mappings

class AxesTab(tk.Frame):
    @staticmethod
    def all_metric_menu(parent, var):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        main_menu.add_radiobutton(value=var.get(), label=var.get(), variable=var)
        main_menu.insert_separator(1)
        # TRAWL
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='TRAWL', menu=menu)
        for metric in [MN.SPEEDUP_VEC, MN.SPEEDUP_DL1, MN.CAP_FP_GFLOP_P_S, MN.RATE_INST_GI_P_S, MN.VARIANT]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # QPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='QPlot', menu=menu)
        for metric in [MN.CAP_L1_GB_P_S, MN.CAP_L2_GB_P_S, MN.CAP_L3_GB_P_S, MN.CAP_RAM_GB_P_S, MN.CAP_MEMMAX_GB_P_S, MN.CAP_FP_GFLOP_P_S, MN.RATE_INST_GI_P_S]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # SIPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='SIPlot', menu=menu)
        for metric in ['Saturation', 'Intensity']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='All', menu=summary_menu)
        # metrics = [[MN.COVERAGE_PCT, MN.TIME_APP_S, MN.TIME_LOOP_S],
        #             [MN.NUM_CORES, MN.DATA_SET, MN.PREFETCHERS, MN.REPETITIONS],
        #             [MN.E_PKG_J, MN.E_DRAM_J, MN.E_PKGDRAM_J], 
        #             [MN.P_PKG_W, MN.P_DRAM_W, MN.P_PKGDRAM_W],
        #             [MN.COUNT_INSTS_GI, MN.RATE_INST_GI_P_S],
        #             [MN.RATE_L1_GB_P_S, MN.RATE_L2_GB_P_S, MN.RATE_L3_GB_P_S, MN.RATE_RAM_GB_P_S, MN.RATE_FP_GFLOP_P_S, 
        #              MN.RATE_INST_GI_P_S, MN.RATE_REG_ADDR_GB_P_S, MN.RATE_REG_DATA_GB_P_S, MN.RATE_REG_SIMD_GB_P_S, MN.RATE_REG_GB_P_S],
        #             [MN.COUNT_OPS_VEC_PCT, MN.COUNT_OPS_FMA_PCT, MN.COUNT_OPS_DIV_PCT, MN.COUNT_OPS_SQRT_PCT, MN.COUNT_OPS_RSQRT_PCT, MN.COUNT_OPS_RCP_PCT],
        #             [MN.COUNT_INSTS_VEC_PCT, MN.COUNT_INSTS_FMA_PCT, MN.COUNT_INSTS_DIV_PCT, MN.COUNT_INSTS_SQRT_PCT, MN.COUNT_INSTS_RSQRT_PCT, MN.COUNT_INSTS_RCP_PCT],
        #             ALL_METRICS]
        # categories = ['Time/Coverage', 'Experiment Settings', 'Energy', 'Power', 'Instructions', 'Rates', r'%ops', r'%inst', 'All']
        for category, metrics in CATEGORIZED_METRICS.items():
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics:
                menu.add_radiobutton(value=metric, label=metric, variable=var)

        # for index, category in enumerate(categories):
        #     menu = tk.Menu(summary_menu, tearoff=False)
        #     summary_menu.add_cascade(label=category, menu=menu)
        #     for metric in metrics[index]:
        #         menu.add_radiobutton(value=metric, label=metric, variable=var)
        return menubutton

    def __init__(self, parent, tab, plotType):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.plotType = plotType
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
            self.tab.data.scale = self.tab.x_scale + self.tab.y_scale
            self.tab.data.y_axis = "{}".format(self.tab.y_axis)
            self.tab.data.x_axis = "{}".format(self.tab.x_axis)
            self.tab.data.notify(self.tab.data.gui.loadedData)

class LabelTab(tk.Frame):
    def __init__(self, parent, tab, level):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.level = level
        self.loadedData = self.tab.data.loadedData
        self.metric1 = tk.StringVar(value='Metric 1')
        self.metric2 = tk.StringVar(value='Metric 2')
        self.metric3 = tk.StringVar(value='Metric 3')
        self.metrics = [self.metric1, self.metric2, self.metric3]
        self.menu1 = AxesTab.all_metric_menu(self, self.metric1)
        self.menu2 = AxesTab.all_metric_menu(self, self.metric2)
        self.menu3 = AxesTab.all_metric_menu(self, self.metric3)
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)

    @property
    def df(self):
        return self.loadedData.levelData[self.level].df

    @property
    def mappings(self):
        return self.loadedData.levelData[self.level].mapping

    @property
    def textData(self):
        return self.tab.plotInteraction.textData

    def render(self):
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
        self.loadedData.updateLabels([], self.level)

    def updateLabels(self):
        current_metrics = []
        if self.metric1.get() != 'Metric 1': current_metrics.append(self.metric1.get())
        if self.metric2.get() != 'Metric 2': current_metrics.append(self.metric2.get())
        if self.metric3.get() != 'Metric 3': current_metrics.append(self.metric3.get())
        # TODO: merge mapping speedups into master dataframe to avoid this check
        current_metrics = [metric for metric in current_metrics if metric in self.df.columns.tolist()]
        if not current_metrics: return # User hasn't selected any label metrics
        self.loadedData.updateLabels(current_metrics, self.level)