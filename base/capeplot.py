import re
import pandas as pd
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import copy
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)
from capelib import add_mem_max_level_columns

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.
plt.rcParams.update({'font.size': 7}) # Set consistent font size for all plots

# Base class for all plots
class CapePlot:
    def __init__(self, default_y_axis):
        self.default_y_axis = default_y_axis
        self.default_x_axis = 'C_FLOP [GFlop/s]'
        self.ctxs = []

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
        

    # Override to compute more metrics
    def compute_extra(self):
        pass
        
    def compute_and_plot(self):
        variant = self.variant
        df = self.df
        outputfile_prefix = self.outputfile_prefix
        scale = self.scale
        title = self.title
        no_plot = self.no_plot
        gui = self.gui
        x_axis = self.x_axis
        y_axis = self.y_axis
        mappings = self.mappings
        short_names_path = self.short_names_path

        self.compute_extra()
        
        if df.empty:
            return # Nothing to do

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
            outputfile = '{}-{}-{}-{}.png'.format \
                (outputfile_prefix, variant, scale, today)
        self.fig, self.plotData = self.plot_data(self.mk_plot_title(title, variant, scale), outputfile, list(
            xs), list(ys), list(mytext), scale, df, color_labels=color_labels, x_axis=x_axis, y_axis=y_axis, mappings=mappings)
        self.df = df

    def draw_contours(self, xmax, ymax):
        self.ctxs = []  # Do nothing but set the ctxs objects to be empty

    def compute_color_labels(self, df, short_names_path=''):
        color_labels = []
        for color in df['Color'].unique():
            colorDf = df.loc[df['Color']==color].reset_index()
            codelet = colorDf[NAME][0]
            timestamp = colorDf[TIMESTAMP][0]
            app_name = codelet.split(':')[0]
            if short_names_path:
                short_names = pd.read_csv(short_names_path)
                row = short_names.loc[(short_names[NAME]==app_name) & \
                    (short_names[TIMESTAMP]==timestamp)].reset_index(drop=True)
                if not row.empty: app_name = row[SHORT_NAME][0]
            color_labels.append((app_name, color))
        return color_labels

    # Set filename to [] for GUI output
    def plot_data(self, title, filename, xs, ys, mytext, scale, df, color_labels=None, \
        x_axis=None, y_axis=None, mappings=pd.DataFrame()):
        DATA = tuple(zip(xs, ys))

        fig, ax = plt.subplots()
        self.ax = ax

        xmax=max(xs)*1.2
        ymax=max(ys)*1.2  
        xmin=min(xs)
        ymin=min(ys)

        # Set specified axis scales
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

        (x, y) = zip(*DATA)

        # Draw contours
        self.draw_contours(xmax, ymax)

        # Plot data points
        markers = []
        df.reset_index(drop=True, inplace=True)
        for i in range(len(x)):
            markers.extend(ax.plot(x[i], y[i], marker='o', color=df['Color'][i][0], \
                label=df[NAME][i]+str(df[TIMESTAMP][i]), linestyle='', alpha=1))

        texts = [plt.text(xs[i], ys[i], mytext[i], alpha=1) for i in range(len(DATA))]

        #adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        ax.set(xlabel=x_axis if x_axis else self.default_x_axis, \
            ylabel=y_axis if y_axis else self.default_y_axis)
        ax.set_title(title, pad=40)

        # Legend
        patches = []
        if color_labels and len(color_labels) >= 2:
            for color_label in color_labels:
                patch = mpatches.Patch(label=color_label[0], color=color_label[1])
                patches.append(patch)

        if self.ctxs:  
            patches.extend(self.ctxs)

        legend = ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0., 1.02, 1., .102), \
            title=self.mk_label_key(), mode='expand', borderaxespad=0., handles=patches)

        # Arrows between multiple runs
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
        plt.tight_layout()
    
        names = [name + timestamp for name,timestamp in zip(df[NAME], df[TIMESTAMP].astype(str))]
        plotData = {
            'xs' : xs,
            'ys' : ys,
            'mytext' : mytext,
            'orig_mytext' : copy.deepcopy(mytext),
            'ax' : ax,
            'legend' : legend,
            'orig_legend' : legend.get_title().get_text(),
            'title' : title,
            'texts' : texts,
            'markers' : markers,
            'names' : names,
            'timestamps' : df[TIMESTAMP].values.tolist(),
            'marker:text' : dict(zip(markers,texts)),
            'marker:name' : dict(zip(markers,names)),
            'name:marker' : dict(zip(names, markers)),
            'name:text' : dict(zip(names, texts)),
            'text:arrow' : {},
            'text:name' : dict(zip(texts, names)),
            'name:mapping' : name_mapping,
            'mappings' : mymappings
        }

        #if filename:
        #plt.savefig(filename)

        return fig, plotData


# Plot with capacity computation
class CapacityPlot(CapePlot):
    MEM_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
    OP_NODE_SET={'FLOP [GFlop/s]', 'SIMD [GB/s]'}
    BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET

    BUFFER_NODE_SET={'FE'}
    DEFAULT_CHOSEN_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]', 'FLOP [GFlop/s]'}

    # For node using derived metrics (e.g. FE), make sure the depended metrics are computed
    capacity_formula= {
	    'L1 [GB/s]': (lambda df : df[RATE_L1_GB_P_S]),
	    'L2 [GB/s]': (lambda df : df[RATE_L2_GB_P_S]),
	    'L3 [GB/s]': (lambda df : df[RATE_L3_GB_P_S]),
	    'FLOP [GFlop/s]': (lambda df : df[RATE_FP_GFLOP_P_S]),
	    'SIMD [GB/s]': (lambda df : df[RATE_REG_SIMD_GB_P_S]),
	    'RAM [GB/s]': (lambda df : df[RATE_RAM_GB_P_S]),
	    'FE [GB/s]': (lambda df : df[STALL_FE_PCT]*df['C_max'])	
    }
        
    def __init__(self, default_y_axis, chosen_node_set):
        super().__init__(default_y_axis)
        self.chosen_node_set = chosen_node_set

	# Override to compute capacity
    def compute_extra(self):
        self.compute_capacity()
        
    def compute_capacity(self):
        df = self.df
        chosen_node_set = self.chosen_node_set
        print("The node list are as follows :")
        print(chosen_node_set)
        chosen_mem_node_set = CapacityPlot.MEM_NODE_SET & chosen_node_set
        for node in chosen_mem_node_set:
            print ("The current node : ", node)
            formula=CapacityPlot.capacity_formula[node]
            df['C_{}'.format(node)]=formula(df)

        node_list = list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))
        metric_to_memlevel = lambda v: re.sub(r" \[.*\]", "", v[2:])
        add_mem_max_level_columns(df, node_list, 'C_max [GB/s]', metric_to_memlevel)
		# df['C_max [GB/s]']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].max(axis=1)
		# df = df[df['C_max [GB/s]'].notna()]
		# df[MEM_LEVEL]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
		# # Remove the first two characters which is 'C_'
		# df[MEM_LEVEL] = df[MEM_LEVEL].apply((lambda v: v[2:]))
		# # Drop the unit
		# df[MEM_LEVEL] = df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)
        print ("<=====compute_capacity======>")
	#	print(df['C_max'])

        chosen_op_node_set = CapacityPlot.OP_NODE_SET & chosen_node_set
        if len(chosen_op_node_set) > 1:
            print("Too many op node selected: {}".format(chosen_op_node_set))
            sys.exit(-1)
        elif len(chosen_op_node_set) < 1:
            print("No op node selected")
            sys.exit(-1)
		# Exactly 1 op node selected below
        op_node = chosen_op_node_set.pop()
        op_metric_name = 'C_{}'.format(op_node)
        formula=CapacityPlot.capacity_formula[op_node]
        df[op_metric_name]=formula(df)
        self.df = df
        self.default_x_axis = op_metric_name