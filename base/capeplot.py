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
import pickle
from metric_names import MetricName
from abc import ABC, abstractmethod
from collections import UserDict
import networkx as nx
from adjustText import adjust_text
import matplotlib
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)
from capelib import add_mem_max_level_columns
from metric_names import KEY_METRICS

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.
plt.rcParams.update({'font.size': 7}) # Set consistent font size for all plots

# Base class for plot data without GUI specific data
# Subclass should override for plot specific data processing.
class CapeData(ABC):
    AllCapeDataItems = []
    DepGraph = nx.DiGraph()

    def __init__(self, df):
        self._df = df
        self.cache_file = None
        CapeData.AllCapeDataItems.append(self)

    
    # Getter of df
    @property
    def df(self):
        return self._df
    
    # # Setter of df (remove so cannot change it)
    # @df.setter
    # def df(self, v):
    #     self._df = v

    cache_dir = None
    # Class variable to remember path to cache data file
    # Set to None to reset
    @classmethod
    def set_cache_dir(cls, data_dir):
        cls.cache_dir = data_dir

    @classmethod
    def clear_dependency_info(cls, self):
        cls.AllCapeDataItems.clear()
        cls.DepGraph = nx.DiGraph()

    def record_dependency(self):
        inSet = set(self.input_args())
        outSet = set(self.output_args())
        for node in self.AllCapeDataItems:
            if node == self:
                continue
            if node.df is not self.df:
                continue
            nodeToItemMetrics = set(node.output_args()) & inSet
            if nodeToItemMetrics and not self.DepGraph.has_edge(node, self):
                self.DepGraph.add_edge(node, self, metrics=nodeToItemMetrics)
            itemToNodeMetrics = set(node.input_args()) & outSet
            if itemToNodeMetrics and not self.DepGraph.has_edge(self, node):
                self.DepGraph.add_edge(self, node, metrics=itemToNodeMetrics)
                
            


    @classmethod
    def invalidate_metrics(cls, metrics, itemPool=None):
        itemPool = cls.AllCapeDataItems if itemPool is None else itemPool
        metricSet = set(metrics)
        invalidateItems = set([item for item in itemPool if set(item.input_args()) & metricSet])
        invalidateItems = invalidateItems | set().union(*[nx.descendants(cls.DepGraph, item) for item in invalidateItems])

        # while updated:
        #     invalidateItems = [item for item in cls.AllCapeDataItems if set(item.input_args()) & metricSet]
        #     newMetricSet = set().union(*[item.output_args() for item in invalidateItems]) | metricSet
        #     updated = not newMetricSet.equals(metricSet)
        #     metricSet = newMetricSet
        # Now we have collected all teams to be invalidated
        for item in invalidateItems:
            # only invalidate cache for now
            # TODO: may want to recompute data in topoligical order
            item.invalidate_cache()
        
        
    def invalidate_cache(self):
        cache_file = self.cache_file 
        if cache_file and os.path.isfile(cache_file):
            os.remove(cache_file)
            self.cache_file = None

    # Subclass could override to read more data
    def try_read_cache(self, filename_prefix):
        cache_file = os.path.join(self.cache_dir, f'{filename_prefix}_dfs.pkl') if self.cache_dir and filename_prefix else None
        if cache_file and os.path.isfile(cache_file):
            with open(cache_file, 'rb') as cache_data:
                data_read = pickle.load(cache_data)
                df = data_read.pop()  # extra the last dataframe which is the df to return
                self.extra_data_to_restore(data_read)
                self.cache_file = cache_file
                return df
        return None

    # Subclass could override to save more data
    def try_write_cache(self, df, filename_prefix):
        cache_file = os.path.join(self.cache_dir, f'{filename_prefix}_dfs.pkl') if self.cache_dir and filename_prefix else None
        if cache_file:
            with open(cache_file, 'wb') as cache_data:
                more_data_to_write = self.extra_data_to_save()
                # df insert at the end so it can be popped by the read call
                pickle.dump(more_data_to_write + [df], cache_data)
                self.cache_file = cache_file
             
    # Subclass override to set the fields give more data
    def extra_data_to_restore(self, more_data):
        pass
    
    # Subclass override to provide more data to be written
    def extra_data_to_save(self):
        return []

    # Should check merge_metrics() in LoadedData class (they should be doing the same thing)
    def compute(self, cache_filename_prefix=None):
        # Copy-in copy-out
        inputs, outputs = self.input_output_args()
        inputs = sorted(inputs)
        outputs = sorted(outputs)

        result_df = self.try_read_cache(cache_filename_prefix)
        if result_df is None:
            copy_df = self.df[KEY_METRICS + [n for n in inputs if n not in KEY_METRICS]] 
            result_df = self.compute_impl(copy_df)
            result_df = result_df[KEY_METRICS + [n for n in outputs if n not in KEY_METRICS]]
            self.try_write_cache(result_df, cache_filename_prefix)

        #result_df = result_df.astype({MetricName.TIMESTAMP: 'int64'})
        # Exclude key metrics not to be overwritten - except when self.df is empty which will be checked below
        existing_outputs = (set(self.df.columns) & set(outputs)) - set(KEY_METRICS)
        if len(existing_outputs) > 0:
            # Drop columns if there is existing columns to be overwritten
            warnings.warn("Trying to override existing columns: {}".format(existing_outputs))
            self.df.drop(columns=existing_outputs, inplace=True, errors='ignore')
        self.df.reset_index(drop=True, inplace=True)
        result_df.reset_index(drop=True, inplace=True)
        if len(self.df) > 0:
            # Not empty self.df case
            merged = pd.merge(left=self.df, right=result_df, how='left', on=KEY_METRICS)
            # Make sure join order is consistent with original self.df order
            assert self.df[MetricName.NAME].equals(merged[MetricName.NAME])

            self.df[MetricName.TIMESTAMP].astype('int64')
            merged[MetricName.TIMESTAMP].astype('int64')
            assert self.df[MetricName.TIMESTAMP].astype('int64').equals(merged[MetricName.TIMESTAMP].astype('int64'))
        else:
            # Empty self.df case, result_df must have all the KEY_METRICS
            assert set(result_df.columns) & set(KEY_METRICS) == set(KEY_METRICS) 
            merged = result_df
        updatedCols = set()
        for col in outputs:
            if col in self.df.columns and self.df[col].equals(merged[col]):
                continue # Update not needed
            self.df[col] = merged[col]
            updatedCols.add(col)
        self.record_dependency()
        # Invalidate item if they work on the same df using updatedCols metrics
        self.invalidate_metrics(updatedCols, [item for item in self.AllCapeDataItems if item.df is self.df])
        return self

    @abstractmethod
    # Process data.  Input from df and return results
    # The data processing outside will supply expected columns specified by input_output_args() method
    # On return, only the expected ouptut columns specified by input_output_args() method will be incorporated
    def compute_impl(self, df):
        return df
    
    @abstractmethod
    # Return (expected inputs, expected outputs)
    # This is a contract of the data computation
    # SEE ALSO: compute_impl()
    def input_output_args(self):
        return None, None

    def output_args(self):
        input_args, output_args = self.input_output_args()
        return output_args

    def input_args(self):
        input_args, output_args = self.input_output_args()
        return input_args

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
    

# Base class for all plots
class CapePlot:
    def __init__(self, data, levelData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
        default_y_axis, default_x_axis = MetricName.CAP_FP_GFLOP_P_S, filtering = False, mappings=pd.DataFrame(), short_names_path=''):
        # Data is a list of data
        self.data = data
        self.levelData = levelData
        self.level = level
        self.guiState = levelData.guiState
        self.default_y_axis = default_y_axis
        self.default_x_axis = default_x_axis
        self.ctxs = []
        self.filtering = filtering
        self.variant = variant
        self.outputfile_prefix = outputfile_prefix
        self.scale = scale
        self.title = title
        self.no_plot = no_plot
        self.gui = gui
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.short_names_path = short_names_path
        self.colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple', 'cyan', 'lime', 'grey', 'brown', 'salmon', 'gold', 'slateblue']
        self.fig = None
        self.plotData = None

    # Getter of df, delegate to self.data
    @property
    def df(self):
        if len(self.data) == 0:
            return pd.DataFrame()
        df = pd.concat([data.df for data in self.data], ignore_index=True)
        return df

    @property
    def mapping(self):
        return self.levelData.mapping

    @property
    def color_map(self):
        return self.levelData.color_map

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
        return "{}\nvariant={}, scale={}".format(title, variant, scale)
        
    # Override to update the data frame containing plot data.
    def filter_data_points(self, in_df):
        return in_df
        
    def compute_and_plot(self):
        variant = self.variant
        outputfile_prefix = self.outputfile_prefix
        scale = self.scale
        title = self.title
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

        # Used to create a legend of file names to color for multiple plots
        color_labels = self.compute_color_labels(df, short_names_path)
        if no_plot:
            return 

        mytext = self.mk_labels()
        if x_axis:
            xs = df[x_axis]
        else:
            xs = df[self.default_x_axis]
        if y_axis: 
            ys = df[y_axis]
        else: 
            ys = df[self.default_y_axis]
    
        today = datetime.date.today()
        if gui:
            outputfile = None
        else:
            outputfile = '{}-{}-{}-{}.png'.format (outputfile_prefix, variant, scale, today)

        self.plot_data(self.mk_plot_title(title, variant, scale), outputfile, xs, ys, mytext, 
                       scale, df, color_labels=color_labels, x_axis=x_axis, y_axis=y_axis)

    def draw_contours(self, xmax, ymax, color_labels):
        self.ctxs = []  # Do nothing but set the ctxs objects to be empty

    def compute_color_labels(self, df, short_names_path=''):
        color_labels = dict()
        user_colors = [i for i in self.colors if i not in df['Color'].unique()]
        i = 0
        for color in sorted(df['Color'].unique()):
            if color not in self.colors: # If it is user-specified then we want to display that in the legend
                color_labels[color] = user_colors[i]
                i += 1
            else: # Otherwise we just use the app name in the legend
                colorDf = df.loc[df['Color']==color].reset_index()
                codelet = colorDf[NAME][0]
                timestamp = colorDf[TIMESTAMP][0]
                app_name = codelet.split(':')[0]
                if short_names_path:
                    short_names = pd.read_csv(short_names_path)
                    row = short_names.loc[(short_names[NAME]==app_name) & \
                        (short_names[TIMESTAMP]==timestamp)].reset_index(drop=True)
                    if not row.empty: app_name = row[SHORT_NAME][0]
                color_labels[app_name] = color
        return color_labels

    @classmethod
    def get_min_max(cls, xs, ys):
        finiteXs = xs[np.isfinite(xs)]
        finiteYs = ys[np.isfinite(ys)]
        xmax=max(finiteXs, default=1)*1.2
        ymax=max(finiteYs, default=1)*1.2  
        xmin=min(finiteXs, default=0)
        ymin=min(finiteYs, default=0)
        return xmin, xmax, ymin, ymax
        
    # Set filename to [] for GUI output
    def plot_data(self, title, filename, xs, ys, mytexts, scale, df, color_labels, \
        x_axis=None, y_axis=None, mappings=pd.DataFrame()):
        # DATA = tuple(zip(xs, ys))

        self.fig, ax = plt.subplots()
        self.ax = ax

        xmin, xmax, ymin, ymax = self.get_min_max(xs, ys)

        # Set specified axis scales
        self.set_plot_scale(scale, xmax, ymax, xmin, ymin)

        # (x, y) = zip(*DATA)

        # Draw contours
        self.draw_contours(xmax, ymax, color_labels)

        # Plot data points
        labels, markers = self.plot_markers_and_labels(df, xs, ys, mytexts, color_labels)

        #adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        ax.set(xlabel=x_axis if x_axis else self.default_x_axis, \
            ylabel=y_axis if y_axis else self.default_y_axis)
        ax.set_title(title, pad=40)

        # Add footnote with datafile and timestamp
        plt.figtext(0, 0.005, self.levelData.source_title, horizontalalignment='left')

        # Legend
        legend = self.mk_legend(color_labels)

        # Arrows between multiple runs
        name_mapping, mymappings = self.mk_mappings(mappings, df, x_axis, y_axis, xmax, ymax)
        try: plt.tight_layout()
        except: print("plt.tight_layout() failed")
    
        self.plotData = PlotData(df, xs, ys, mytexts, ax, legend, title, labels, markers, name_mapping, mymappings, self.guiState, self)

    def plot_markers_and_labels(self, df, xs, ys, mytexts, color_labels):
        ax = self.ax
        markers = []
        for x, y, color, name, timestamp in zip(xs, ys, self.color_map['Color'], self.color_map[NAME], self.color_map[TIMESTAMP]):
            markers.extend(ax.plot(x, y, marker='o', color=color, 
                                   label=name+str(timestamp), linestyle='', alpha=1))
        #texts = [plt.text(xs[i], ys[i], mytexts[i], alpha=1) for i in range(len(xs))]
        texts = [plt.text(x, y, mytext, alpha=1) for x, y, mytext in zip(xs, ys, mytexts)]
        return texts, markers

    def mk_legend(self, color_labels):
        ax = self.ax
        patches = []
        for label in self.color_map['Label'].unique():
            if label:
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
            for i in mappings.index:
                name_mapping[mappings['Before Name'][i]+str(mappings['Before Timestamp'][i])] = []
                name_mapping[mappings['After Name'][i]+str(mappings['After Timestamp'][i])] = []
            for index in mappings.index:
                before_row = self.df.loc[(self.df[NAME]==mappings['Before Name'][index]) & \
                    (self.df[TIMESTAMP]==mappings['Before Timestamp'][index])].reset_index(drop=True)
                after_row = self.df.loc[(self.df[NAME]==mappings['After Name'][index]) & \
                    (self.df[TIMESTAMP]==mappings['After Timestamp'][index])].reset_index(drop=True)
                if not before_row.empty and not after_row.empty:
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
                            connectionstyle='arc3,rad=0.3', alpha=1)
                    else:
                        con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", \
                            shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
                            connectionstyle='arc3,rad=-0.3', alpha=1)
                    ax.add_artist(con)
                    name_mapping[before_row[NAME][0] + str(before_row[TIMESTAMP][0])].append(con)
                    name_mapping[after_row[NAME][0] + str(after_row[TIMESTAMP][0])].append(con)
                    mymappings.append(con)
        return name_mapping, mymappings

    def set_plot_scale(self, scale, xmax, ymax, xmin, ymin):
        ax = self.ax
        if scale == 'linear' or scale == 'linearlinear':
            ax.set_xlim((0, xmax))
            ax.set_ylim((0, ymax))
        elif scale == 'log' or scale == 'loglog':
            plt.xscale("log")
            plt.yscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((ymin, ymax))
        elif scale == 'loglinear':
            plt.xscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((0, ymax))
        elif scale == 'linearlog':
            plt.yscale("log")
            ax.set_xlim((0, xmax))
            ax.set_ylim((ymin, ymax))

    def setupFrames(self, canvasFrame, chartButtonFrame):
        # NavigationToolbar2Tk can only be created if there isn't anything in the grid
        self.plotData.setupFrames(self.fig, canvasFrame, chartButtonFrame)

class PlotData():
    def __init__(self, df, xs, ys, mytexts, ax, legend, title, labels, markers, name_mapping, mymappings, guiState, plot):
        names = guiState.get_encoded_names(df).tolist()
        self.xs = xs
        self.ys = ys
        self.mytext = mytexts
        self.orig_mytext = copy.deepcopy(mytexts)
        self.ax = ax
        self.legend = legend
        self.orig_legend = legend.get_title().get_text()
        self.title = title
        self.texts = labels
        self.markers = markers
        self.names = names
        self.timestamps = df[TIMESTAMP].values.tolist()
        self.marker_text = dict(zip(markers,labels))
        self.marker_name = dict(zip(markers,names))
        self.name_marker = dict(zip(names, markers))
        self.name_text = dict(zip(names, labels))
        self.text_arrow = {}
        self.text_name = dict(zip(labels, names))
        self.name_mapping = name_mapping
        self.mappings = mymappings
        self.canvas = None
        self.guiState = guiState
        self.plot = plot
        self.guiState.add_observers(self)
        self.adjusted = False
        self.adjusting = False

    def notify(self, data):
        self.updateMarkers()
        self.updateLabels()

    def updateMarkers(self):
        # Hide/Show the markers, labels, and arrows
        for name in self.names:
            alpha = 1
            if self.guiState.isHidden(name): alpha = 0
            self.name_marker[name].set_alpha(alpha)
            self.name_text[name].set_alpha(self.guiState.labelVisbility(name))
            # Unhighlight/highlight points
            if name in self.guiState.highlighted: self.highlight(self.name_marker[name])
            else: self.unhighlight(self.name_marker[name])
            # Need to first set all mappings to visible, then remove hidden ones to avoid hiding then showing
            if name in self.name_mapping: self.name_mapping[name].set_alpha(1)
        for name in self.name_mapping:
            if self.guiState.isHidden(name): self.name_mapping[name].set_alpha(0)
        self.canvas.draw()

    def updateLabels(self):
        # Update labels on plot
        current_metrics = self.guiState.labels
        for i, text in enumerate(self.texts):
            label = self.orig_mytext[i][:-1]
            codeletName = self.names[i]
            for metric in current_metrics:
                # Update label menu with currently selected metric
                # self.tab.labelTab.metrics[metric_index].set(metric)
                # Append to end of label
                encoded_names = self.guiState.get_encoded_names(self.guiState.levelData.df)
                value = self.guiState.levelData.df.loc[encoded_names==codeletName][metric].iloc[0]
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
        self.canvas.draw()

    def toggleLabel(self, marker):
        label = self.marker_text[marker]
        label.set_alpha(not label.get_alpha())
        if label in self.text_arrow: self.text_arrow[label].set_visible(label.get_alpha())
        self.canvas.draw()
    
    def toggleLabels(self, alpha, adjusted):
        for marker in self.marker_text:
            if marker.get_alpha(): 
                self.marker_text[marker].set_alpha(alpha) 
                if adjusted: 
                    # possibly called adjustText after a zoom and no arrow is mapped to this label outside of the current axes
                    # TODO: Create "marker:arrow" to simplify this statement
                    if self.marker_text[marker] in self.text_arrow: self.text_arrow[self.marker_text[marker]].set_visible(alpha)
        self.canvas.draw()

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
            # Create new texts that maintain the current visibility
            self.texts = [plt.text(self.xs[i], self.ys[i], self.mytext[i], alpha=1 if i not in hiddenTexts else 0, color='k' if i not in highlightedTexts else 'r') for i in range(len(self.mytext))]
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
        self.canvas.get_tk_widget().after(0, self.canvas.draw)
        self.adjusted = True
        self.adjusting = False
        print('Done Adjust text')

    def adjustText(self):
        if not self.adjusting: 
            self.adjusting = True
            if sys.platform == 'darwin':
                self.thread_adjustText()
            else: 
                # Do this in mainthread
                plt_sca(self.ax)
                threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()

    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.ax.get_xlim() or self.cur_ylim != self.ax.get_ylim()) and \
            (self.home_xlim != self.ax.get_xlim() or self.home_ylim != self.ax.get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.cur_xlim = self.ax.get_xlim()
            self.cur_ylim = self.ax.get_ylim()
            self.adjustText()

    def setLims(self):
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
        if action == 'Select Point':
            selected = self.getSelected(event)
            self.guiState.selectPoints(selected)
            return
        if action == 'Choose Action': return
        for marker in self.markers:
            contains, points = marker.contains(event)
            if contains and marker.get_alpha():
                name = self.marker_name[marker]
                if action == 'Highlight Point': 
                    if marker.get_marker() == 'o': self.guiState.highlightPoints([name])
                    else: self.guiState.unhighlightPoints([name])
                elif action == 'Remove Point':
                    self.guiState.removePoints([name]) 
                elif action == 'Toggle Label': 
                    alpha = not self.name_text[name].get_alpha()
                    self.guiState.toggleLabel(name, alpha)

    def setupFrames(self, fig, canvasFrame, chartButtonFrame):
        # NavigationToolbar2Tk can only be created if there isn't anything in the grid
        for slave in chartButtonFrame.grid_slaves():
            slave.grid_forget()
        # Refresh the canvas
        for slave in canvasFrame.pack_slaves():
            slave.destroy()
        # Store initial xlim and ylim for adjustText 
        self.setLims()
        # Create canvas and toolbar for plot
        self.canvas = FigureCanvasTkAgg(fig, canvasFrame)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('draw_event', self.onDraw)
        self.toolbar = NavigationToolbar2Tk(self.canvas, chartButtonFrame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, anchor=tk.N, padx=10)
        self.canvas.draw()
        self.toolbar.grid(column=7, row=0, sticky=tk.S)
        self.toolbar.update()
    

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