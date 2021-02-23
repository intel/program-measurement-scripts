import re
import os
import sys
import numpy as np
import pandas as pd
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import copy
import pickle
from metric_names import MetricName
from abc import ABC, abstractmethod
from collections import UserDict
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
    def __init__(self, df):
        self._df = df

    
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

        
    # Subclass could override to read more data
    def try_read_cache(self, filename_prefix):
        cache_file = os.path.join(self.cache_dir, f'{filename_prefix}_dfs.pkl') if self.cache_dir and filename_prefix else None
        if cache_file and os.path.isfile(cache_file):
            with open(cache_file, 'rb') as cache_data:
                data_read = pickle.load(cache_data)
                df = data_read.pop()  # extra the last dataframe which is the df to return
                self.extra_data_to_restore(data_read)
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
            copy_df = self.df[KEY_METRICS + inputs] 
            result_df = self.compute_impl(copy_df)
            result_df = result_df[KEY_METRICS + outputs]
            self.try_write_cache(result_df, cache_filename_prefix)

        #result_df = result_df.astype({MetricName.TIMESTAMP: 'int64'})
        existing_outputs = self.df.columns & outputs
        if len(existing_outputs) > 0:
            # Drop columns if there is existing columns to be overwritten
            warnings.warn("Trying to override existing columns: {}".format(existing_outputs))
            self.df.drop(columns=existing_outputs, inplace=True, errors='ignore')
        self.df.reset_index(drop=True, inplace=True)
        result_df.reset_index(drop=True, inplace=True)
        merged = pd.merge(left=self.df, right=result_df, how='left', on=KEY_METRICS)
        assert self.df[MetricName.NAME].equals(merged[MetricName.NAME])
        assert self.df[MetricName.TIMESTAMP].astype('int64').equals(merged[MetricName.TIMESTAMP].astype('int64'))
        for col in outputs:
            self.df[col] = merged[col]
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
    BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET | REG_NODE_SET
    BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'RS'}
    ALL_NODE_SET = BASIC_NODE_SET | BUFFER_NODE_SET

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
    def __init__(self, data, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
        default_y_axis, default_x_axis = MetricName.CAP_FP_GFLOP_P_S, filtering = False, mappings=pd.DataFrame(), short_names_path=''):
        self.data = data
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
        self.mappings = mappings
        self.short_names_path = short_names_path
        self.colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple', 'cyan', 'lime', 'grey', 'brown', 'salmon', 'gold', 'slateblue']

    # Getter of df, delegate to self.data
    @property
    def df(self):
        return self.data.df
    
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
        mappings = self.mappings
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
                       scale, df, color_labels=color_labels, x_axis=x_axis, y_axis=y_axis, mappings=mappings)
        # self.df = df

    def draw_contours(self, xmax, ymax, color_labels):
        self.ctxs = []  # Do nothing but set the ctxs objects to be empty

    def compute_color_labels(self, df, short_names_path=''):
        color_labels = dict()
        user_colors = [i for i in self.colors if i not in df['Color'].unique()]
        i = 0
        for color in df['Color'].unique():
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

        # Legend
        legend = self.mk_legend(color_labels)

        # Arrows between multiple runs
        name_mapping, mymappings = self.mk_mappings(mappings, df, x_axis, y_axis, xmax, ymax)
        try: plt.tight_layout()
        except: print("plt.tight_layout() failed")
    
        self.fill_plot_data(df, xs, ys, mytexts, ax, legend, title, labels, markers, name_mapping, mymappings)

    def fill_plot_data(self, df, xs, ys, mytexts, ax, legend, title, labels, markers, name_mapping, mymappings):
        names = [name + timestamp for name,timestamp in zip(df[NAME], df[TIMESTAMP].astype(str))]
        self.plotData = {
            'xs' : xs,
            'ys' : ys,
            'mytext' : mytexts,
            'orig_mytext' : copy.deepcopy(mytexts),
            'ax' : ax,
            'legend' : legend,
            'orig_legend' : legend.get_title().get_text(),
            'title' : title,
            'texts' : labels,
            'markers' : markers,
            'names' : names,
            'timestamps' : df[TIMESTAMP].values.tolist(),
            'marker:text' : dict(zip(markers,labels)),
            'marker:name' : dict(zip(markers,names)),
            'name:marker' : dict(zip(names, markers)),
            'name:text' : dict(zip(names, labels)),
            'text:arrow' : {},
            'text:name' : dict(zip(labels, names)),
            'name:mapping' : name_mapping,
            'mappings' : mymappings
        }

        #if filename:
        #plt.savefig(filename)

        #if filename:
        #    pass
            #plt.savefig(filename)
        #else:
        #    plt.show()


    def plot_markers_and_labels(self, df, xs, ys, mytexts, color_labels):
        ax = self.ax
        markers = []
        df.reset_index(drop=True, inplace=True)
        for x, y, color, name, timestamp in zip(xs, ys, df['Color'], df[NAME], df[TIMESTAMP]):
            if color in color_labels: # Check if the color is a user specified name, then get the actual color
                color = color_labels[color]
            markers.extend(ax.plot(x, y, marker='o', color=color, 
                                   label=name+str(timestamp), linestyle='', alpha=1))

        #texts = [plt.text(xs[i], ys[i], mytexts[i], alpha=1) for i in range(len(xs))]
        texts = [plt.text(x, y, mytext, alpha=1) for x, y, mytext in zip(xs, ys, mytexts)]
        return texts, markers

    def mk_legend(self, color_labels):
        ax = self.ax
        patches = []
        if color_labels and len(color_labels) >= 2:
            for color_label in color_labels:
                patch = mpatches.Patch(label=color_label, color=color_labels[color_label])
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
        if not mappings.empty:
            for i in mappings.index:
                name_mapping[mappings['before_name'][i]+str(mappings['before_timestamp#'][i])] = []
                name_mapping[mappings['after_name'][i]+str(mappings['after_timestamp#'][i])] = []
            for index in mappings.index:
                before_row = df.loc[(df[NAME]==mappings['before_name'][index]) & \
                    (df[TIMESTAMP]==mappings['before_timestamp#'][index])].reset_index(drop=True)
                after_row = df.loc[(df[NAME]==mappings['after_name'][index]) & \
                    (df[TIMESTAMP]==mappings['after_timestamp#'][index])].reset_index(drop=True)
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


# Plot with capacity computation
class CapacityPlot(CapePlot):
    def __init__(self, data, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
        default_y_axis, default_x_axis = MetricName.CAP_FP_GFLOP_P_S, filtering = False, mappings=pd.DataFrame(), \
            short_names_path=''):
        super().__init__(data, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, \
            default_y_axis, default_x_axis, filtering, mappings, short_names_path)
        #self.default_x_axis = self.data.op_metric_name

    # Getter of chosen_node_set, delegate to self.data
    @property
    def chosen_node_set(self):
        return self.data.chosen_node_set
