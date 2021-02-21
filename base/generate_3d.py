#!/usr/bin/python3
import pandas as pd
import numpy as np
import warnings
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from matplotlib import style
from mpl_toolkits.mplot3d import Axes3D
from adjustText import adjust_text
import copy
from capeplot import CapacityPlot
from capeplot import CapacityData
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class Plot3d(CapacityPlot):
    def __init__(self, data, variant, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, z_axis=None, mappings=pd.DataFrame(), short_names_path=''):
        super().__init__(data, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                         default_y_axis=COVERAGE_PCT.value, mappings=mappings, short_names_path=short_names_path)
        self.z_axis = z_axis
        self.default_z_axis = 'C_FLOP [GFlop/s]'

    def compute_and_plot(self):
        variant = self.variant
        outputfile_prefix = self.outputfile_prefix
        scale = self.scale
        title = self.title
        no_plot = self.no_plot
        gui = self.gui
        x_axis = self.x_axis
        y_axis = self.y_axis
        z_axis = self.z_axis
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
        if z_axis:
            zs = df[z_axis]
        else: 
            zs = df[self.default_z_axis]
    
        today = datetime.date.today()
        if gui:
            outputfile = None
        else:
            outputfile = '{}-{}-{}-{}.png'.format (outputfile_prefix, variant, scale, today)

        self.plot_data(self.mk_plot_title(title, variant, scale), outputfile, xs, ys, zs, mytext, 
                       scale, df, color_labels=color_labels, x_axis=x_axis, y_axis=y_axis, z_axis=z_axis, mappings=mappings)
        #self.df = df

    def plot_data(self, title, filename, xs, ys, zs, mytexts, scale, df, color_labels=None, \
        x_axis=None, y_axis=None, z_axis=None, mappings=pd.DataFrame()):
        # DATA = tuple(zip(xs, ys))

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')

        xmax=max(xs)*1.2
        ymax=max(ys)*1.2  
        zmax=max(zs)*1.2  
        xmin=min(xs)
        ymin=min(ys)
        zmin=min(zs)

        # Set specified axis scales
        self.set_plot_scale(scale, xmax, ymax, zmax, xmin, ymin, zmin)

        # Plot data points
        labels, markers = self.plot_markers_and_labels(df, xs, ys, zs, mytexts)

        xlabel=x_axis if x_axis else self.default_x_axis
        ylabel=y_axis if y_axis else self.default_y_axis
        zlabel=z_axis if z_axis else self.default_z_axis
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_zlabel(zlabel)
        self.ax.set_title(title, pad=40)

        # Legend
        legend = self.mk_legend(color_labels)

        # Arrows between multiple runs
        # name_mapping, mymappings = self.mk_mappings(mappings, df, x_axis, y_axis, xmax, ymax)
        name_mapping = []
        mymappings = []
        plt.tight_layout()
    
        self.fill_plot_data(df, xs, ys, zs, mytexts, self.ax, legend, title, labels, markers, name_mapping, mymappings)

    def plot_markers_and_labels(self, df, xs, ys, zs, mytexts):
        ax = self.ax
        markers = []
        df.reset_index(drop=True, inplace=True)
        ax.scatter(xs, ys, zs, marker='o')
        # for x, y, z, color, name, timestamp in zip(xs, ys, zs, df['Color'], df[NAME], df[TIMESTAMP]):
        #     markers.extend(ax.plot(x, y, z, marker='o', color=color[0], 
        #                            label=name+str(timestamp), linestyle='', alpha=1))

        #texts = [plt.text(xs[i], ys[i], mytexts[i], alpha=1) for i in range(len(xs))]
        # texts = [plt.text(x, y, z, mytext, alpha=1) for x, y, z, mytext in zip(xs, ys, zs, mytexts)]
        texts = []
        return texts, markers

    def set_plot_scale(self, scale, xmax, ymax, zmax, xmin, ymin, zmin):
        ax = self.ax
        if scale == 'logloglog' or scale == 'log':
            plt.xscale("log")
            plt.yscale("log")
            #plt.zscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((ymin, ymax))
            ax.set_zlim((zmin, zmax))
        elif scale == 'logloglinear':
            plt.xscale("log")
            plt.yscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((ymin, ymax))
            ax.set_zlim((0, zmax))
        elif scale == 'loglinearlog':
            plt.xscale("log")
            #plt.zscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_zlim((zmin, zmax))
            ax.set_ylim((0, ymax))
        elif scale == 'loglinearlinear':
            plt.xscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((0, ymax))
            ax.set_zlim((0, zmax))
        elif scale == 'linearlinearlinear' or scale == 'linearlinear':
            ax.set_xlim((0, xmax))
            ax.set_ylim((0, ymax))
            ax.set_zlim((0, zmax))
        elif scale == 'linearlinearlog':
            #plt.zscale("log")
            ax.set_xlim((xmin, xmax))
            ax.set_ylim((ymin, ymax))
            ax.set_zlim((0, zmax))
        elif scale == 'linearloglinear':
            plt.yscale("log")
            ax.set_ylim((ymin, ymax))
            ax.set_xlim((0, xmax))
            ax.set_zlim((0, zmax))
        elif scale == 'linearloglog':
            plt.yscale("log")
            #plt.zscale("log")
            ax.set_ylim((ymin, ymax))
            ax.set_zlim((zmin, zmax))
            ax.set_xlim((0, xmax))

    def fill_plot_data(self, df, xs, ys, zs, mytexts, ax, legend, title, labels, markers, name_mapping, mymappings):
        names = [name + timestamp for name,timestamp in zip(df[NAME], df[TIMESTAMP].astype(str))]
        self.plotData = {
            'xs' : xs,
            'ys' : ys,
            'zs' : zs,
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

def plot_3d(df, outputfile, scale, title, no_plot, variants, gui=False, x_axis=None, y_axis=None, z_axis=None, \
    mappings=pd.DataFrame(), short_names_path=''):
    chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
    if not mappings.empty:
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
        'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
    df['C_FLOP [GFlop/s]'] = df[RATE_FP_GFLOP_P_S]
    # Only show selected variants, default is 'ORIG'
    df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
    data = CapacityData(df)
    data.set_chosen_node_set(chosen_node_set)
    data.compute()
    plot = Plot3d(data, 
        'ORIG', outputfile, scale, title, chosen_node_set, no_plot, gui=gui, x_axis=x_axis, y_axis=y_axis, z_axis=z_axis, mappings=mappings, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)


