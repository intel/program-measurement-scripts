import re
import tkinter as tk
import threading
import os
import sys
import numpy as np
import pandas as pd
import warnings
import datetime
import copy
from metric_names import MetricName
from collections import UserDict
from adjustText import adjust_text
import matplotlib
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from capedata import CapeData
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)
from capelib import add_mem_max_level_columns
from metric_names import KEY_METRICS
from abc import ABC, abstractmethod
import hashlib

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.
plt.rcParams.update({'font.size': 8.5}) # Set consistent font size for all plots


class NodeCentricData(CapeData):
    def __init__(self, df):
        super().__init__(df)
        self.chosen_node_set = set()

    def set_chosen_node_set(self, chosen_node_set):
        self.chosen_node_set = chosen_node_set
        return self

class NodeWithUnitData(NodeCentricData):
    def __init__(self, df, node_dict):
        super().__init__(df)
        self.chosen_node_set = set()
        self.node_dict = node_dict 

    # Override this because for node with units
    # Expect the chosen_node_set has not units and to be computed
    def set_chosen_node_set(self, chosen_node_set):
        self.chosen_node_set = {"{} {}".format(n, self.node_dict[n]) for n in chosen_node_set}
        return self

    def set_chosen_node_set_with_unit(self, chosen_node_set_with_unit):
        self.chosen_node_set = chosen_node_set_with_unit
        return self

class CapacityData(NodeCentricData):
    MEM_NODE_SET={'L1', 'L2', 'L3', 'RAM'}
    REG_NODE_SET={'VR'}
    OP_NODE_SET={'FLOP'}
    BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET 
    BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'RS', 'LB'}
    ALL_NODE_SET = BASIC_NODE_SET | BUFFER_NODE_SET | REG_NODE_SET

    BUFFER_NODE_SET={'FE'}
    DEFAULT_CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'RAM', 'FLOP'}

    # For node using derived metrics (e.g. FE), make sure the depended metrics are computed
    capacity_formula= [
	    # 'L1 [GB/s]': (lambda df : df[RATE_L1_GB_P_S]),
	    # 'L2 [GB/s]': (lambda df : df[RATE_L2_GB_P_S]),
	    # 'L3 [GB/s]': (lambda df : df[RATE_L3_GB_P_S]),
	    # 'FLOP [GFlop/s]': (lambda df : df[RATE_FP_GFLOP_P_S]),
	    # 'SIMD [GB/s]': (lambda df : df[RATE_REG_SIMD_GB_P_S]),
	    # 'RAM [GB/s]': (lambda df : df[RATE_RAM_GB_P_S]),
	    # 'FE [GB/s]': (lambda df : df[STALL_FE_PCT]*df['C_max'])	

        (MetricName.CAP_FP_GB_P_S, (lambda df,nodes : df[RATE_FP_GFLOP_P_S]*8 if "FLOP" in nodes else None)),
        (MetricName.CAP_L1_GB_P_S, (lambda df,nodes : df[RATE_L1_GB_P_S] if "L1" in nodes else None)),
        (MetricName.CAP_L2_GB_P_S, (lambda df,nodes : df[RATE_L2_GB_P_S] if "L2" in nodes else None)),
        (MetricName.CAP_L3_GB_P_S, (lambda df,nodes : df[RATE_L3_GB_P_S] if "L3" in nodes else None)),
        (MetricName.CAP_RAM_GB_P_S, (lambda df,nodes : df[RATE_RAM_GB_P_S] if "RAM" in nodes else None)),
        # NOTE: C_VR has 1/3 factor built in for SI use
        (MetricName.CAP_VR_GB_P_S, (lambda df,nodes : df[RATE_REG_SIMD_GB_P_S]/3 if "VR" in nodes else None)), 

        (MetricName.CAP_FP_GFLOP_P_S, (lambda df,nodes : df[RATE_FP_GFLOP_P_S] if "FLOP" in nodes else None)),
        (MetricName.CAP_L1_GW_P_S, (lambda df,nodes : df[RATE_L1_GB_P_S]/8 if "L1" in nodes else None)),
        (MetricName.CAP_L2_GW_P_S, (lambda df,nodes : df[RATE_L2_GB_P_S]/8 if "L2" in nodes else None)), 
        (MetricName.CAP_L3_GW_P_S, (lambda df,nodes : df[RATE_L3_GB_P_S]/8 if "L3" in nodes else None)), 
        (MetricName.CAP_RAM_GW_P_S, (lambda df,nodes : df[RATE_RAM_GB_P_S]/8 if "RAM" in nodes else None)), 
        # NOTE: C_VR has 1/3 factor built in for SI use
        (MetricName.CAP_VR_GW_P_S, (lambda df,nodes : df[RATE_REG_SIMD_GB_P_S]/8/3 if "VR" in nodes else None)), 

        (MetricName.CAP_MEMMAX_GB_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGB_s([n for n in nodes if n in CapacityData.MEM_NODE_SET])]).max(axis=1))), 
        (MetricName.CAP_MEMMAX_GW_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGW_s([n for n in nodes if n in CapacityData.MEM_NODE_SET])]).max(axis=1))), 

        (MetricName.CAP_ALLMAX_GB_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGB_s([n for n in nodes if n in CapacityData.BASIC_NODE_SET])]).max(axis=1))), 
        (MetricName.CAP_ALLMAX_GW_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGW_s([n for n in nodes if n in CapacityData.BASIC_NODE_SET])]).max(axis=1))), 
        
        # Same formula as C_max [*] (for now) (used for SI)
        (MetricName.CAP_SCALAR_GB_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGB_s([n for n in nodes if n in CapacityData.MEM_NODE_SET])]).max(axis=1))), 
        (MetricName.CAP_SCALAR_GW_P_S, (lambda df,nodes : 
            (df[CapacityData.nodesToCapsGW_s([n for n in nodes if n in CapacityData.MEM_NODE_SET])]).max(axis=1))), 

        (MetricName.CAP_FE_GB_P_S, (lambda df,nodes : (df[STALL_FE_PCT]/100)*df[MetricName.CAP_ALLMAX_GB_P_S])), 
        (MetricName.CAP_FE_GW_P_S, (lambda df,nodes : (df[STALL_FE_PCT]/100)*(df[MetricName.CAP_ALLMAX_GW_P_S]))), 
        (MetricName.CAP_SB_GB_P_S, (lambda df,nodes : (df[STALL_SB_PCT]/100)*(df[MetricName.CAP_ALLMAX_GB_P_S]))), 
        (MetricName.CAP_SB_GW_P_S, (lambda df,nodes : (df[STALL_SB_PCT]/100)*(df[MetricName.CAP_ALLMAX_GW_P_S]))), 
        (MetricName.CAP_LM_GB_P_S, (lambda df,nodes : (df[STALL_LM_PCT]/100)*(df[MetricName.CAP_ALLMAX_GB_P_S]))), 
        (MetricName.CAP_LM_GW_P_S, (lambda df,nodes : (df[STALL_LM_PCT]/100)*(df[MetricName.CAP_ALLMAX_GW_P_S]))), 
        (MetricName.CAP_RS_GB_P_S, (lambda df,nodes : (df[STALL_RS_PCT]/100)*(df[MetricName.CAP_ALLMAX_GB_P_S]))), 
        (MetricName.CAP_RS_GW_P_S, (lambda df,nodes : (df[STALL_RS_PCT]/100)*(df[MetricName.CAP_ALLMAX_GW_P_S]))),
        (MetricName.CAP_LB_GB_P_S, (lambda df,nodes : (df[STALL_LB_PCT]/100)*(df[MetricName.CAP_ALLMAX_GB_P_S]))),
        (MetricName.CAP_LB_GW_P_S, (lambda df,nodes : (df[STALL_LB_PCT]/100)*(df[MetricName.CAP_ALLMAX_GW_P_S]))),

        # used for SI
        (MetricName.CAP_CU_GW_P_S, (lambda df,nodes : ((df[STALL_FE_PCT]/100 + df[STALL_LB_PCT]/100 + 
                                             df[STALL_SB_PCT]/100 + df[STALL_LM_PCT]/100)*df[MetricName.CAP_SCALAR_GW_P_S]))),
        (MetricName.CAP_CU_GB_P_S, (lambda df,nodes : ((df[STALL_FE_PCT]/100 + df[STALL_LB_PCT]/100 + 
                                             df[STALL_SB_PCT]/100 + df[STALL_LM_PCT]/100)*df[MetricName.CAP_SCALAR_GB_P_S])))
    ]



    def __init__(self, df):
        super().__init__(df)
    # A dictionary/dataframe like object passed to go through formula to 
    # record input and output variables.
    class RecordDict(UserDict):
        def __init__(self):
            super().__init__()
            self.input_keys = set() 
            self.output_keys = set() 
            self.drop_keys = set() 
            
            
        def seenKey(self, key, keys):
            if type(key) is list:
                newkeys = key
            else:
                newkeys = {key}
            keys.update(newkeys)
            return newkeys

        def __getitem__(self, key):
            keys = self.seenKey(key, self.input_keys)
            # Return a dummy dataframe to get it going
            return pd.DataFrame([{k:0 for k in keys}])
        
        def __setitem__(self, key, value):
            self.seenKey(key, self.output_keys)

        def drop(self, columns, inplace):
            self.drop_keys = self.drop_keys.union(columns)
            
    @classmethod
    def nodesToCaps(cls, nodes):
        # Simply returns all capacity variable names starting with C_n where n in nodes
        return [caps for (caps,f) in cls.capacity_formula if caps.startswith(tuple(["C_{}".format(n) for n in nodes]))]

    @classmethod
    def nodesToCapsGB_s(cls, nodes):
        return [caps for caps in cls.nodesToCaps(nodes) if caps.endswith('[GB/s]')]

    @classmethod
    def nodesToCapsGW_s(cls, nodes):
        # NOTE here we choose *not* to check GW/s explicitly because unit for FLOP is GFlop/s
        return [caps for caps in cls.nodesToCaps(nodes) if not caps.endswith('[GB/s]')]

    def input_output_args(self):
        dict_record = CapacityData.RecordDict()
        self.apply_formula(dict_record)
        output_args = dict_record.output_keys
        input_args = dict_record.input_keys.difference(output_args)
        output_args = output_args.difference(dict_record.drop_keys)
        return input_args, output_args

        
    def compute_impl(self, df):
        return self.compute_capacity(df)


    def apply_formula(self, df):
        chosen_node_set = self.chosen_node_set
        # Including C_max needed to compute control unit capacities
        maxCaps = self.nodesToCaps({'allmax'})
        allCaps = set(self.nodesToCaps(chosen_node_set.union({'max', 'scalar'}))).union(set(maxCaps))

        for lhs,formula in self.capacity_formula:
            if lhs in allCaps: df[lhs] = formula(df, chosen_node_set)

        # Drop the C_max capacities as QPlot use the name for other use.
        #df.drop(columns=maxCaps, inplace=True)
        

    def compute_capacity(self, df):
        # df = self.df
        self.apply_formula(df)

        # chosen_mem_node_set = CapacityData.MEM_NODE_SET & chosen_node_set
        # for node in chosen_mem_node_set:
        #     print ("The current node : ", node)
        #     formula=CapacityData.capacity_formula[node]
        #     df['C_{}'.format(node)]=formula(df)

        # node_list = list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))
        #metric_to_memlevel = lambda v: re.sub(r" \[.*\]", "", v[2:])
        # add_mem_max_level_columns(df, node_list, MetricName.CAP_MEMMAX_GB_P_S, metric_to_memlevel)
		# df[MetricName.CAP_MEMMAX_GB_P_S]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].max(axis=1)
		# df = df[df[MetricName.CAP_MEMMAX_GB_P_S].notna()]
		# df[MEM_LEVEL]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
		# # Remove the first two characters which is 'C_'
		# df[MEM_LEVEL] = df[MEM_LEVEL].apply((lambda v: v[2:]))
		# # Drop the unit
		# df[MEM_LEVEL] = df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)
        print ("<=====compute_capacity======>")
	#	print(df['C_max'])

        chosen_op_node_set = CapacityData.OP_NODE_SET & self.chosen_node_set
        if len(chosen_op_node_set) > 1:
            print("Too many op node selected: {}".format(chosen_op_node_set))
            sys.exit(-1)
        elif len(chosen_op_node_set) < 1:
            print("No op node selected")
            sys.exit(-1)
		# Exactly 1 op node selected below
        # op_node = chosen_op_node_set.pop()
        # op_metric_name = 'C_{}'.format(op_node)
        # formula=CapacityData.capacity_formula[op_node]
        # df[op_metric_name]=formula(df)
        #self.df = df
        return df
        #self.op_metric_name = op_metric_name
    
class CapePlotColor:
    #COLOR_MAP = matplotlib.cm.get_cmap('hsv')
    COLOR_MAP = matplotlib.cm.get_cmap('tab20')
    NUM_COLORS = 20
    COLOR_ORDER1 = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple', 'cyan', 'lime', 'grey', 'brown', 'salmon', 'gold', 'slateblue']
    COLOR_ORDER = [None] * NUM_COLORS
    for i in range(NUM_COLORS):
        COLOR_ORDER[i] = COLOR_MAP(i/NUM_COLORS) 
    DEFAULT_COLOR = COLOR_ORDER[0]

    @classmethod
    def hash(cls, name):
        # Hash excluding the default color
        return int(hashlib.sha256(name.encode('utf-8')).hexdigest(), 16) % (len(cls.COLOR_ORDER) - 1) + 1

    @classmethod
    def hashColors(cls, names):
        # Map from names to index to index space of COLOR_ORDER with potential collisons
        hashs = np.array([cls.hash(name) for name in names])
        # Follow determine indices of hashs successful hashs without collison (first occurrences)
        successfulHashs, successfulIndices = np.unique(hashs, return_index=True)
        # This array record, given the hashed location, which original index of names array it is from 
        hashToNameIndices=np.array([-1]*len(cls.COLOR_ORDER))
        hashToNameIndices[successfulHashs] = successfulIndices
        # Use a linear probing scheme to fill collided hashs.  Basically look for next open slots for each collision
        # The order of assignment will pick smallest hashs first and so on.
        remainingIndices = sorted([idx for idx in range(len(hashs)) if idx not in successfulIndices])
        remainingHashs = [hashs[idx] for idx in remainingIndices]
        # Get remaining slot 
        openSlots = np.where(hashToNameIndices == -1)[0]
        openSlots = openSlots[openSlots>0] # Excluding the default color slot (which will be used when run out of colors)
        for indexToAssign, collidedHash in zip(remainingIndices, remainingHashs):
            if openSlots.size == 0: 
                # Assign remaining hashs to default
                hashs[indexToAssign] = 0
                continue
            biggerMask = openSlots>collidedHash
            # Find next slot just bigger than collidedHash if not, get the earliest slot.  This simulate a round robin scheduling
            slot = openSlots[np.amin(np.where(biggerMask))] if np.any(biggerMask) else np.amin(openSlots)
            hashToNameIndices[slot] = indexToAssign
            openSlots = openSlots[openSlots != slot]
            hashs[indexToAssign] = slot

        return [cls.COLOR_ORDER[idx] for idx in hashs]
        

# Base class for all plots
class CapePlot:
    def __init__(self, data=None, levelData=None, level=None, variant=None, outputfile_prefix=None, scale=None, title=None, no_plot=None, gui=None, x_axis=None, y_axis=None, \
        default_y_axis=None, default_x_axis = MetricName.CAP_FP_GFLOP_P_S, filtering = False, mappings=pd.DataFrame(), short_names_path=''):
        self.ctxs = []
        #self.colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple', 'cyan', 'lime', 'grey', 'brown', 'salmon', 'gold', 'slateblue']
        self.container = None
        self.fig, self.ax = plt.subplots()
        self.ax.clear()
        self.footnoteText = None
        self.init_plotData()
        self._setAttrs(data, levelData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
            default_y_axis, default_x_axis, filtering, mappings, short_names_path)

    def init_plotData(self):
        self.plotData = DynamicPlotData(df=None, xs=None, ys=None, mytexts=None, ax=None, title=None, 
                                 labels=None, markers=None, name_mapping=None, mymappings=None, guiState=None, plot=self,
                                 xmax=None, ymax=None, xmin=None, ymin=None, variant=None, names=None)
    
    def _setAttrs(self, data, levelData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
        default_y_axis, default_x_axis, filtering, mappings, short_names_path):
        # Data is a list of data
        self.data = data
        self.levelData = levelData
        self.level = level
        self.variant = variant
        self.outputfile_prefix = outputfile_prefix
        self.scale = scale
        self.title = title
        self.no_plot = no_plot
        self.gui = gui
        self._x_axis = x_axis
        self._y_axis = y_axis
        self.default_y_axis = default_y_axis
        self.default_x_axis = default_x_axis
        self.filtering = filtering
        self.short_names_path = short_names_path
        #self.guiState = levelData.guiState
        self.plotData.setAttrs (df=self.df, xs=None, ys=None, mytexts=None, ax=self.ax, title=title, 
                                labels=None, markers=None, name_mapping=None, mymappings=None, guiState=self.guiState, plot=self, 
                                xmax=None, ymax=None, xmin=None, ymin=None, variant=variant, names=None)


    def setData(self, data):
        self.data = data
        return self
        
        
    def setLevelData(self, levelData):
        self.levelData = levelData
        return self

    def setLevel(self, level):
        self.level = level
        return self

    def setScale(self, scale):
        self.scale = scale
        return self

    def setXaxis(self, x_axis):
        self._x_axis = x_axis
        return self

    def setYaxis(self, y_axis):
        self._y_axis = y_axis
        return self

    def setMapping(self, mapping):
        # Unused
        return self

    def setShortNamesPath(self, path):
        self.short_names_path = path
        return self
        
    # Getter of df, delegate to self.data
    @property
    def df(self):
        # if len(self.data) == 0:
        #     return pd.DataFrame()
        # df = pd.concat([data.df for data in self.data], ignore_index=True)
        # return df
        return None if self.levelData is None else self.levelData.df

    @property
    def mapping(self):
        return self.levelData.mapping_df

    @property
    def color_map(self):
        return self.levelData.color_map

    @property
    def guiState(self):
        return None if self.levelData is None else self.levelData.guiState
    # # Setter of df (May remove), delegate to self.data
    # @df.setter
    # def df(self, v):
    #     self.data.df = v

    def mk_labels(self):
        df = self.df
        try:
            indices = df[SHORT_NAME]
        except:
            indices = df[NAME]
        mytext = [str('({0})'.format(indices[i])) for i in range(len(indices))]
        return mytext

    def mk_label_key(self):
        return "(name)"

    def mk_plot_title(self, title, variant, scale):
        new_title = ""
        if title: new_title += "{}\n".format(title)
        if variant: new_title += "variant={}, ".format(variant)
        if scale: new_title += "scale={}".format(scale)
        return new_title
        
    # Override to update the data frame containing plot data.
    def filter_data_points(self, in_df):
        return in_df
        
    @property
    def x_axis(self):
        return self._x_axis if self._x_axis else self.default_x_axis

    @property
    def y_axis(self):
        return self._y_axis if self._y_axis else self.default_y_axis

    def compute_and_plot(self):
        variant = self.variant
        outputfile_prefix = self.outputfile_prefix
        scale = self.scale
        #title = self.title
        no_plot = self.no_plot
        gui = self.gui
        x_axis = self.x_axis
        y_axis = self.y_axis
        short_names_path = self.short_names_path

        
        if self.df.empty:
            return # Nothing to do

        if self.filtering:
            self.df = self.filter_data_points(self.df)

        df = self.df

        if no_plot:
            return 

        mytext = self.mk_labels()
        xs = df[x_axis]
        ys = df[y_axis]
    
        today = datetime.date.today()
        if gui:
            outputfile = None
        else:
            outputfile = '{}-{}-{}-{}.png'.format (outputfile_prefix, variant, scale, today)

        self.plot_data(self.extend_plot_title(variant, scale), outputfile, xs, ys, mytext, 
                       scale, df, x_axis=x_axis, y_axis=y_axis)

    def extend_plot_title(self, variant, scale):
        return self.mk_plot_title(self.title, variant, scale)

    def draw_contours(self, xmax, ymax):
        self.ctxs = []  # Do nothing but set the ctxs objects to be empty

    # Subclass override to update their specific contours
    def update_contours(self):
        pass

    def get_min_max(self, xs, ys):
        finiteXs = xs[np.isfinite(xs)]
        finiteYs = ys[np.isfinite(ys)]
        xmax=max(finiteXs, default=1)*1.2
        ymax=max(finiteYs, default=1)*1.2  
        xmin=min(finiteXs, default=0)
        ymin=min(finiteYs, default=0)
        return xmin, xmax, ymin, ymax
        
    # Try to adjust the plot without replotting it.
    def adjust_plot(self, scale):
        print("Updater plot")
        # Will call back to self.plot_rest() with some info saved in plotData
        # TODO: Need to update to handle color legend update
        self.plot_adjustable(scale)

    def get_encoded_names(self, df):
        return self.guiState.get_encoded_names(df)

    def get_names(self):
        # This is subclassed by Rank Order to return the ordered encoded names
        return self.get_encoded_names(self.df).tolist()

        
    def get_source_title(self):
        return self.levelData.source_title
        
    # Set filename to [] for GUI output
    def plot_data(self, title, filename, xs, ys, mytexts, scale, df, x_axis, y_axis, mappings=pd.DataFrame()):
        # DATA = tuple(zip(xs, ys))

        # if not self.fig:
        #     self.fig, ax = plt.subplots()
        #     self.ax = ax
        # else:
        self.ax.clear()
        ax = self.ax

        self.xmin, self.xmax, self.ymin, self.ymax = self.get_min_max(xs, ys)

        # Draw contours
        self.draw_contours(self.xmax, self.ymax)

        # Plot data points
        labels, markers = self.plot_markers_and_labels(df, xs, ys, mytexts)
        # self.set_font_size(labels, 8.5)

        # Arrows between multiple runs
        name_mapping, mymappings = self.mk_mappings(mappings, df, x_axis, y_axis, self.xmax, self.ymax)

        # Add footnote with datafile and timestamp
        #plt.figtext(0, 0.005, self.levelData.source_title, horizontalalignment='left')
        if self.footnoteText: self.footnoteText.remove()
        self.footnoteText = self.fig.text(0, 0.005, self.get_source_title(), horizontalalignment='left')

        ax.set(xlabel=x_axis, ylabel=y_axis)
        self.finish_plot(df, xs, ys, mytexts, ax, title, labels, markers, name_mapping, mymappings, scale)




        # try: 
        #     self.fig.tight_layout()
        #     self.fig.set_tight_layout(True)
        # #    self.fig.canvas.draw()
        # except: print("self.fig.tight_layout() failed")

    
    # More basic updates to plot
    def finish_plot(self, df, xs, ys, mytexts, ax, title, labels, markers, name_mapping, mymappings, scale):
        names = self.get_names()
        #self.fig.set_tight_layout(True)
        self.plotData.setAttrs(df, xs, ys, mytexts, ax, title, labels, markers, 
            name_mapping, mymappings, self.guiState, self, self.xmax, self.ymax, self.xmin, self.ymin, 
            self.variant, names)
        # Plot rest of the plot (which can be adjusted later)
        self.plot_adjustable(scale)

    def plot_adjustable(self, scale):
        # Set specified axis scales
        ax = self.ax
        self.set_plot_scale(scale)
        # Store axis limits to prevent adjustText from adjusting twice
        self.plotData.setLims()
        # Update legend
        legend = self.mk_legend()
        self.plotData.legend = legend
        self.plotData.orig_legend = legend.get_title().get_text()
        # Update color of points
        for color, name, timestamp in zip(self.color_map['Color'], self.color_map[NAME], self.color_map[TIMESTAMP]):
            name = name+str(timestamp)
            if name in self.plotData.name_marker: self.plotData.name_marker[name].set_color(color)

        # Update contours
        self.update_contours()

        # labels, markers = self.plot_markers_and_labels(self.df, xs, ys, mytexts)
        # (x, y) = zip(*DATA)

        #adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        ax.set_title(self.extend_plot_title(self.plotData.variant, scale), pad=40)
        self.plotData.updateMarkers()
        self.plotData.updateLabels()
        self.plotData.thread_safe_canvas_draw()

    def plot_markers_and_labels(self, df, xs, ys, mytexts):
        ax = self.ax
        markers = []
        for x, y, color, name, timestamp in zip(xs, ys, self.color_map['Color'], self.color_map[NAME], self.color_map[TIMESTAMP]):
            markers.extend(ax.plot(x, y, marker='o', color=color, 
                                   label=name+str(timestamp), linestyle='', alpha=1))
        #texts = [plt.text(xs[i], ys[i], mytexts[i], alpha=1) for i in range(len(xs))]
        texts = [self.ax.text(x, y, mytext, alpha=1) for x, y, mytext in zip(xs, ys, mytexts)]
        return texts, markers

    def get_visible_df(self):
        hidden_mask = self.guiState.get_hidden_mask(self.df)
        return self.df[~hidden_mask]

    def mk_legend(self):
        ax = self.ax
        patches = []
        visible_df = self.get_visible_df()
        visible_df['encoded_name'] = self.get_encoded_names(visible_df)
        for label in self.color_map['Label'].unique():
            if label:
                mask = self.color_map['Label'] == label
                masked_df = self.color_map[mask]
                masked_df['encoded_name'] = self.get_encoded_names(masked_df)
                exists = masked_df['encoded_name'].isin(visible_df['encoded_name'])
                if sum(exists):
                    patch = mpatches.Patch(label=label, color=self.color_map.loc[self.color_map['Label']==label]['Color'].iloc[0])
                    patches.append(patch)

        if self.ctxs:  
            patches.extend(self.ctxs)

        legend = ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0., 1.02, 1., .102), \
            title=self.mk_label_key(), mode='expand', borderaxespad=0., handles=patches)
        return legend

    def mk_mappings(self, mappings, df, x_axis, y_axis, xmax, ymax):
        ax = self.ax
        name_mapping = dict()
        mymappings = []
        mappings = self.mapping
        if not mappings.empty:
            # Each codelet tracks their mapping arrow objects in 'name_mapping' for future showing/hiding
            for index in mappings.index:
                # Extract the row corresponding to the mapping entry from the full data frame 
                before_row = self.df.loc[(self.df[NAME] == mappings['Before Name'][index]) & (self.df[TIMESTAMP] == mappings['Before Timestamp'][index])].reset_index(drop=True)
                after_row = self.df.loc[(self.df[NAME] == mappings['After Name'][index]) & (self.df[TIMESTAMP] == mappings['After Timestamp'][index])].reset_index(drop=True)
                # Only add mappings if the row exists and if there isn't a NAN value in this plot's metrics
                if not before_row.empty and not after_row.empty and not pd.isnull(before_row[self.x_axis].iloc[0]) and not pd.isnull(before_row[self.y_axis].iloc[0]) and not pd.isnull(after_row[self.x_axis].iloc[0]) and not pd.isnull(after_row[self.y_axis].iloc[0]):
                    # Create new list if not already in the name_mapping dictionary
                    before_key = mappings['Before Name'][index]+str(mappings['Before Timestamp'][index])
                    after_key = mappings['After Name'][index]+str(mappings['After Timestamp'][index])
                    if before_key not in name_mapping: name_mapping[before_key] = []
                    if after_key not in name_mapping: name_mapping[after_key] = []
                    # Get source and destination points for each arrow
                    x_axis = x_axis if x_axis else self.default_x_axis
                    y_axis = y_axis if y_axis else self.default_y_axis
                    xyA = (before_row[x_axis][0], before_row[y_axis][0])
                    xyB = (after_row[x_axis][0], after_row[y_axis][0])
                    # Check which way to curve the arrow to avoid going out of the axes
                    if (xmax - xyB[0] > xyB[0] and xmax - xyA[0] > xyA[0] and xyA[1] < xyB[1]) or \
                        (ymax - xyB[1] > xyB[1] and ymax - xyA[1] > xyA[1] and xyA[0] > xyB[0]) or \
                        (ymax - xyB[1] < xyB[1] and ymax - xyA[1] < xyA[1] and xyA[0] < xyB[0]) or \
                        (xmax - xyB[0] < xyB[0] and xmax - xyA[0] < xyA[0] and xyA[1] > xyB[1]):
                        con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", \
                            shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                            connectionstyle='arc3,rad=0.1', alpha=1)
                    else:
                        con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", \
                            shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                            connectionstyle='arc3,rad=-0.1', alpha=1)
                    ax.add_artist(con)
                    # Add this arrow to the list of arrows coming from this source
                    name_mapping[before_row[NAME][0] + str(before_row[TIMESTAMP][0])].append(con)
                    name_mapping[after_row[NAME][0] + str(after_row[TIMESTAMP][0])].append(con)
                    mymappings.append(con)
        return name_mapping, mymappings

    def set_plot_scale(self, scale):
        ax = self.ax
        if scale == 'linear' or scale == 'linearlinear':
            ax.set_xscale("linear")
            ax.set_yscale("linear")
            ax.set_xlim((0, self.xmax))
            ax.set_ylim((0, self.ymax))
        elif scale == 'log' or scale == 'loglog':
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlim((self.xmin, self.xmax))
            ax.set_ylim((self.ymin, self.ymax))
        elif scale == 'loglinear':
            ax.set_xscale("log")
            ax.set_yscale("linear")
            ax.set_xlim((self.xmin, self.xmax))
            ax.set_ylim((0, self.ymax))
        elif scale == 'linearlog':
            ax.set_xscale("linear")
            ax.set_yscale("log")
            ax.set_xlim((0, self.xmax))
            ax.set_ylim((self.ymin, self.ymax))

    @property
    def control(self):
        return self.container.control
    
    def setupFrames(self, canvasFrame, chartButtonFrame, container):
        # NavigationToolbar2Tk can only be created if there isn't anything in the grid
        self.plotData.setupFrames(self.fig, canvasFrame, chartButtonFrame)
        self.container = container

    def tidy_plot(self):
        self.plotData.tidy_plot()
    
    def adjustText(self):
        self.plotData.set_font_size(8.5)
        self.plotData.adjustText()
        #self.plotData.thread_safe_canvas_draw()

    def setLabelAlphas(self, alpha):
        self.plotData.setLabelAlphas(alpha)

    def showPoints(self):
        self.plotData.showPoints()

    def unhighlightPoints(self):
        self.plotData.unhighlightPoints()
        
class BasePlotData(ABC):
    def __init__(self, df, xs, ys, mytexts, ax, title, labels, markers, 
                 name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names):
        self.setAttrs(df, xs, ys, mytexts, ax, title, labels, markers, 
                      name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names)

    def setAttrs(self, df, xs, ys, mytexts, ax, title, labels, markers, 
                 name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names):
        self.xs = xs
        self.ys = ys
        self.mytext = mytexts
        self.orig_mytext = copy.deepcopy(mytexts)
        self.ax = ax
        self.title = title
        self.texts = labels
        self.markers = markers
        self.text_arrow = {}
        self.name_mapping = name_mapping
        self.mappings = mymappings
        self.plot = plot
        self.xmax = xmax
        self.ymax = ymax
        self.xmin = xmin
        self.ymin = ymin
        self.variant = variant
        if df is None:
            return
        self.names = names
        self.timestamps = df[TIMESTAMP].values.tolist()
        self.marker_text = dict(zip(markers,labels)) if markers else None
        self.marker_name = dict(zip(markers,names)) if markers else None
        self.name_marker = dict(zip(names, markers)) if markers else None
        self.name_text = dict(zip(names, labels)) if labels else None
        self.text_name = dict(zip(labels, names)) if labels else None
        if hasattr(self, 'guiState') and self.guiState is not None:
            self.guiState.rm_observer(self)
        self.guiState = guiState
        #self.guiState.add_observer(self)
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.thread_safe_canvas_draw()

    @abstractmethod
    def is_marker_hidden(self, name):
        return NotImplemented

    def updateMarkers(self):
        # Hide/Show the markers, labels, and arrows
        for name in self.names:
            alpha = 1
            if self.is_marker_hidden(name): alpha = 0
            self.name_marker[name].set_alpha(alpha)
            self.name_text[name].set_alpha(self.get_label_alpha(name))
            # Unhighlight/highlight and select points
            self.unhighlight(self.name_marker[name])
            if self.is_selected(name): self.select(self.name_marker[name])
            if self.is_highlighted(name): self.highlight(self.name_marker[name])
            # Need to first set all mappings to visible, then remove hidden ones to avoid hiding then showing
            if name in self.name_mapping: 
                for arrow in self.name_mapping[name]: arrow.set_alpha(1)
        for name in self.name_mapping:
            if self.is_marker_hidden(name): 
                for arrow in self.name_mapping[name]: arrow.set_alpha(0)

    def updateLabels(self):
        # Update labels on plot
        current_metrics = self.get_labels()
        cur_df = self.get_df()
        encoded_names = self.plot.get_encoded_names(cur_df)
        for i, text in enumerate(self.texts):
            label = self.orig_mytext[i][:-1]
            codeletName = self.names[i]
            for metric in current_metrics:
                # Update label menu with currently selected metric
                # self.tab.labelTab.metrics[metric_index].set(metric)
                # Append to end of label
                value = cur_df.loc[encoded_names==codeletName][metric].iloc[0]
                if isinstance(value, int) or isinstance(value, float):
                    label += ', ' + str(round(value, 2))
                else:
                    label += ', ' + str(value)
            label += ')'
            text.set_text(label)
            self.mytext[i] = label
        # Update legend for user to see order of metrics in the label
        newTitle = self.orig_legend[:-1]
        for metric in current_metrics:
            newTitle += ', ' + metric
        newTitle += ')'
        self.legend.get_title().set_text(newTitle)

    def tidy_plot(self):
        # Could have done this outside as well
        # TODO: may merge PlotData with CapePlot
        self.canvas.figure.tight_layout()
        self.thread_safe_canvas_draw()

    @abstractmethod
    def thread_safe_canvas_draw(self):
        pass

    @abstractmethod
    def get_df(self):
        return NotImplemented

    def setLims(self):
        self.cur_xlim = self.ax.get_xlim()
        self.cur_ylim = self.ax.get_ylim()

    def highlight(self, marker):
        text = self.marker_text[marker]
        marker.set_marker('*')
        marker.set_markeredgecolor('k')
        marker.set_markeredgewidth(0.5)
        marker.set_markersize(11)
        text.set_color('r')

    def unhighlight(self, marker):
        text = self.marker_text[marker]
        marker.set_marker('o')
        marker.set_markeredgecolor(marker.get_markerfacecolor())
        marker.set_markersize(6.0)
        text.set_color('k')

    def select(self, marker):
        marker.set_marker('^')
        marker.set_markeredgecolor('k')
        marker.set_markeredgewidth(0.5)
        marker.set_markersize(7.0)

    def set_font_size(self, size):
        labels = self.texts
        for label in labels:
            label.set_fontsize(size)

    def getTimestamp(self, marker):
        return self.marker_timestamps[marker]

class DynamicPlotData(BasePlotData):
    def __init__(self, df, xs, ys, mytexts, ax, title, labels, markers, 
                 name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names):
        super().__init__(df, xs, ys, mytexts, ax, title, labels, markers, 
                         name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names)
        self.canvas = None
        self.adjusted = False
        self.adjusting = False

    def setAttrs(self, df, xs, ys, mytexts, ax, title, labels, markers, 
                 name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names):
        super().setAttrs(df, xs, ys, mytexts, ax, title, labels, markers, 
                      name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names)
        if hasattr(self, 'guiState') and self.guiState is not None:
            self.guiState.rm_observer(self)
        self.guiState = guiState
        #self.guiState.add_observer(self)
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.thread_safe_canvas_draw()

    @property
    def control(self):
        return None if self.plot is None else self.plot.control

    def is_marker_hidden(self, name):
        return self.guiState.isHidden(name)

    def get_label_alpha(self, name):
        return self.guiState.labelVisbility(name)

    def is_selected(self, name):
        return name in self.guiState.selected
        
    def is_highlighted(self, name):
        return name in self.guiState.highlighted
         

    def get_labels(self):
        return self.guiState.labels
        
    def get_df(self):
        return self.guiState.levelData.df


    def setLabelAlphas(self, alpha):
        self.guiState.setLabelAlphas(self.names, alpha)
        self.checkAdjusted()

    def showPoints(self):
        self.guiState.showPoints(self.names)

    def unhighlightPoints(self):
        self.guiState.unhighlightPoints(self.names)


    # Return encoded names of data points selected by the event
    def getSelected(self, event):
        return [self.marker_name[m] for m in self.markers if m.contains(event)[0]]
        
    def thread_adjustText(self):
        print('Adjusting text...')
        if self.adjusted: # Remove old adjusted texts/arrows and create new texts before calling adjust_text again
            # Store index of hidden texts to update the new texts
            hiddenTexts = []
            highlightedTexts = []
            for i in range(len(self.texts)):
                if not self.texts[i].get_alpha(): hiddenTexts.append(i)
                if self.texts[i].get_color() == 'r': highlightedTexts.append(i)
            # Remove all old texts and arrows
            for child in self.ax.get_children():
                if isinstance(child, matplotlib.text.Annotation) or (isinstance(child, matplotlib.text.Text) and child.get_text() not in [self.title, '', self.ax.get_title()]):
                    child.remove()
            # Create new texts that maintain the current visibilty
            self.texts = [self.ax.text(self.xs[i], self.ys[i], self.mytext[i], alpha=1 if i not in hiddenTexts else 0, color='k' if i not in highlightedTexts else 'r') for i in range(len(self.mytext))]
            # Update marker to text mappings with the new texts
            self.marker_text = dict(zip(self.markers,self.texts))
            self.name_text = dict(zip(self.names,self.texts))
        # Only adjust texts that are in the current axes (in case of a zoom)
        to_adjust = []
        for i in range(len(self.texts)):
            if self.texts[i].get_alpha() and \
                self.xs[i] >= self.ax.get_xlim()[0] and self.xs[i] <= self.ax.get_xlim()[1] and \
                self.ys[i] >= self.ax.get_ylim()[0] and self.ys[i] <= self.ax.get_ylim()[1]:
                to_adjust.append(self.texts[i])
        adjust_text(to_adjust, ax=self.ax, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        # Map each text to the corresponding arrow
        index = 0
        for child in self.ax.get_children():
            if isinstance(child, matplotlib.text.Annotation):
                self.text_arrow[to_adjust[index]] = child # Mapping
                if not to_adjust[index].get_alpha(): child.set_visible(False) # Hide arrows with hidden texts
                index += 1
        #self.root.after(0, self.canvas.draw)
        # TODO: WARNING global variable used here. May want to get it from GUI componenet.
        self.thread_safe_canvas_draw()
        self.adjusted = True
        self.adjusting = False
        print('Done Adjust text')

    # See: https://github.com/matplotlib/matplotlib/issues/13293
    # matplotlib not threadsafe so use the workaround to schedule draw in GUI thread.
    def thread_safe_canvas_draw(self):
        self.canvas.get_tk_widget().after(0, self.canvas.draw)

    # control is the controller object in Analyzer_controller which provides the method to run long running job displaying status
    def adjustText(self):
        if not self.adjusting: 
            self.adjusting = True
            if sys.platform == 'darwin':
                self.thread_adjustText()
            else: 
                # Do this in mainthread
                plt_sca(self.ax)
                if self.control:
                    self.control.display_work('Adjusting text...', self.thread_adjustText)
                else: 
                    threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()


    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.ax.get_xlim() or self.cur_ylim != self.ax.get_ylim()) and \
            (self.home_xlim != self.ax.get_xlim() or self.home_ylim != self.ax.get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            self.cur_xlim = self.ax.get_xlim()
            self.cur_ylim = self.ax.get_ylim()
            print("Ondraw adjusting")
            self.adjustText()



    def setHomeLims(self):
        self.home_xlim = self.cur_xlim = self.ax.get_xlim()
        self.home_ylim = self.cur_ylim = self.ax.get_ylim()

    def checkAdjusted(self):
        if self.adjusted:
            self.adjustText()

    def onClick(self, event):
        #print("(%f, %f)", event.xdata, event.ydata)
        # for child in self.plotData.ax.get_children():
        #     print(child)
        action = self.guiState.action_selected
        if self.guiState.selectPoint:
            selected = self.getSelected(event)
            self.guiState.selectPoints(selected)

        if action == 'Choose Action': return
        for marker in self.markers:
            contains, points = marker.contains(event)
            if contains and marker.get_alpha():
                name = self.marker_name[marker]
                if action == 'Highlight Point':
                    if marker.get_marker() != '*': self.guiState.highlightPoints([name])
                    else: self.guiState.unhighlightPoints([name])
                elif action == 'Remove Point':
                    self.guiState.removePoints([name])
                    #TODO: Quick fix to remove adjust text arrows after removing a point, instead should remove just that specific arrow
                    self.checkAdjusted() 
                elif action == 'Toggle Label': 
                    alpha = not self.name_text[name].get_alpha()
                    self.guiState.setLabelAlpha(name, alpha)

    def setupFrames(self, fig, canvasFrame, chartButtonFrame):
        # # NavigationToolbar2Tk can only be created if there isn't anything in the grid
        # for slave in chartButtonFrame.grid_slaves():
        #     slave.grid_forget()
        # # Refresh the canvas
        # for slave in canvasFrame.pack_slaves():
        #     slave.destroy()
        # Store initial xlim and ylim for adjustText
        self.setHomeLims()
        # Create canvas and toolbar for plot
        self.canvas = FigureCanvasTkAgg(fig, canvasFrame)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('draw_event', self.onDraw)
        # Create a frame just for the NavigationToolbar2Tk as it requires pack layout,
        # which may not be the case for chartButtonFrame
        toolbarFrame = tk.Frame(chartButtonFrame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
        #self.canvas.draw()
        # NOTE: Need to add just after buttons
        toolbarFrame.grid(column=6, row=0, sticky=tk.S)
        self.toolbar.update()
    


class StaticPlotData(BasePlotData):
    def __init__(self, df, xs, ys, mytexts, ax, title, labels, markers, 
                 name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names):
        super().__init__(df, xs, ys, mytexts, ax, title, labels, markers, 
                         name_mapping, mymappings, guiState, plot, xmax, ymax, xmin, ymin, variant, names)
        self.show_label = True
        self.do_adjustText = True
        self.df = df
        self.labels = [MetricName.RATE_FP_GFLOP_P_S]

    def get_df(self):
        return self.df

    def hide_labels(self):
        self.show_label = False

    def set_labels(self, labels):
        self.labels = labels

    def skip_adjustText(self):
        self.do_adjustText = False

    def get_labels(self):
        return self.labels

    # Do nothing for basic plots
    def thread_safe_canvas_draw(self):
        pass
    
    def is_marker_hidden(self, name):
        return False

    def get_label_alpha(self, name):
        return 1 if self.show_label else 0

    def is_selected(self, name):
        return False
        
    def is_highlighted(self, name):
        return False

    def adjustText(self):
        if self.do_adjustText:
            self.thread_adjustText()
# Plot with capacity computation
class CapacityPlot(CapePlot):
    def __init__(self, data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
        default_y_axis, default_x_axis = MetricName.CAP_FP_GFLOP_P_S, filtering = False, mappings=pd.DataFrame(), \
            short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
            default_y_axis, default_x_axis, filtering, mappings, short_names_path)
        #self.default_x_axis = self.data.op_metric_name

    # Getter of chosen_node_set, delegate to self.data
   # @property
   # def chosen_node_set(self):
   #     return self.data.chosen_node_set

    @property
    def chosen_node_set(self):
        return set().union(*[data.chosen_node_set for data in self.data])    


# Extracted from sca(ax) from 3.2.2
def plt_sca(ax):
    """ 
    Set the current Axes instance to *ax*.

    The current Figure is updated to the parent of *ax*.
    """
    managers = plt._pylab_helpers.Gcf.get_all_fig_managers()
    for m in managers:
        if ax in m.canvas.figure.axes:
            plt._pylab_helpers.Gcf.set_active(m)
            m.canvas.figure.sca(ax)
            return
    raise ValueError("Axes instance argument was not found in a figure")
