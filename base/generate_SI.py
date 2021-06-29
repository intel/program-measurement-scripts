#!/usr/bin/env python
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
import copy
from capeplot import StaticPlotData
from capeplot import CapePlot, CapePlotColor 
from capeplot import NodeWithUnitData
from capelib import import_dataframe_columns

import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.patches import Rectangle
import statistics
from matplotlib.legend import Legend
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from metric_names import MetricName
from metric_names import NonMetricName
from metric_names import KEY_METRICS
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class SiData(NodeWithUnitData):
    def __init__(self, df):
        super().__init__(df, NODE_UNIT_DICT)

    # Getter of cur_run_df
    @property
    def cur_run_df(self):
        return self.df
    
    # Setter of cur_run_df (May remove)
    @cur_run_df.setter
    def cur_run_df(self, v):
        self.df = v

    def set_norm(self, norm):
        self.norm = norm
        return self
    
    def set_cluster_df (self, cluster_df):
        self.cluster_df = cluster_df
        return self

    # def compute_capacity(self, df):
    #     chosen_node_set = self.chosen_node_set
    #     norm = self.norm
    #     print("The node list are as follows :")
    #     print(chosen_node_set)
    #     chosen_basic_node_set = BASIC_NODE_SET & chosen_node_set
    #     chosen_buffer_node_set = BUFFER_NODE_SET & chosen_node_set
    #     chosen_scalar_node_set = SCALAR_NODE_SET & chosen_node_set
    #     # for node in chosen_basic_node_set:
    #     #     print ("The current node : ", node)
    #     #     formula=capacity_formula[node]
    #     #     df['C_{}'.format(node)]=formula(df)

    #     # Dropped C_max calculation as we did that in capacity phase that metric was C_allmax [G*/s]
    #     #self.compute_norm(norm, df, chosen_basic_node_set, MetricName.CAP_MEMMAX_GB_P_S)
    #     #print ("<=====compute_capacity======>")
    #     self.compute_norm(norm, df, chosen_scalar_node_set, 'C_scalar')
    #     print ("<=====compute_cu_scalar======>")

    #     for node in chosen_buffer_node_set:
    #         formula=capacity_formula[node]
    #         df['C_{}'.format(node)]=formula(df)
    #     # # Compute memory level 
    #     # chosen_mem_node_set = MEM_NODE_SET & chosen_node_set
    #     # # Below will get the C_* name with max value
    #     # df[MEM_LEVEL]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
    #     # # Remove the first two characters which is 'C_'
    #     # df[MEM_LEVEL] = df[MEM_LEVEL].apply((lambda v: v[2:]))
    #     # # Drop the unit
    #     # df[MEM_LEVEL] = df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)


    def compute_norm(self, norm, df, node_set, lhs):
        # First go ahead to compute the row norm
        # Get the right column names for the sat node by prepending C_ to node names.  Store the results in 'SatCaps' column
        df['SatCaps']=df[NonMetricName.SI_SAT_NODES].apply(lambda ns: self.capacities(set(ns) & BASIC_NODE_SET))
        # Get the max of the columns specified in 'SatCaps' column
        df[lhs] = df.apply(lambda x: x[x['SatCaps']].max(), axis=1)
        if norm == 'matrix':
           # Just take the max across all row norms and make it the matrix norm
            df[lhs] = df[lhs].max()
            
        #if norm == 'row':
        #    print ("<=====Running Row Norm======>")
        #    df[lhs]=df[list(map(lambda n: "C_{}".format(n), node_set))].max(axis=1)
        #else:
        #    print ("<=====Running Matrix Norm======>")
        #    df[lhs]=max(df[list(map(lambda n: "C_{}".format(n), node_set))].max(axis=1))
        df.drop('SatCaps', axis=1, inplace=True)

    def concat_ordered_columns(self, frames):
        columns_ordered = []
        for frame in frames:
            columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
        final_df = pd.concat(frames, ignore_index=True)
        # final_df[TIMESTAMP] = final_df[TIMESTAMP].fillna(0).astype(int)
        return final_df[columns_ordered]

    # Return (expected inputs, expected outputs)
    def input_output_args(self):
        # input_args = [NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES, MetricName.CAP_ALLMAX_GW_P_S] + \
        #     self.capacities(self.chosen_node_set)+self.stallPcts(self.chosen_node_set & REAL_BUFFER_NODE_SET)
        input_args = [NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES ] + \
            self.capacities(self.chosen_node_set)+self.stallPcts(self.chosen_node_set & REAL_BUFFER_NODE_SET)
        output_args = ['Saturation', 'Intensity', 'SI']
        return input_args, output_args

    def compute_impl(self, df):
        cluster_df = self.cluster_df
        cluster_df['is_cluster'] = True
        cur_run_df = df
        cur_run_df['is_cluster'] = False
        #self.compute_CSI(cluster_df)
        #cluster_df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup

        cluster_df[TIMESTAMP]=0
        cluster_df[TIME_APP_S]=0.0
        cluster_df[COVERAGE_PCT]=0.0
        cluster_df['Color'] = ""

        cluster_and_cur_run_df = self.concat_ordered_columns([cluster_df,cur_run_df])

        # Compute Capacity, Saturation and intensity again for all the runs (cluster + current runs).
        self.compute_CSI(cluster_and_cur_run_df)
        import_dataframe_columns(cluster_df, cluster_and_cur_run_df, sorted(set(cluster_and_cur_run_df.columns)-set(cluster_df.columns)))

        self.cluster_and_cur_run_df = cluster_and_cur_run_df
        # Select the rows corresponding to cur_run_df for plotting
        df = cluster_and_cur_run_df[cluster_and_cur_run_df['is_cluster'] == False]

        #cluster_and_cur_run_df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup    
        self.Ns = len(self.chosen_node_set)
        return df 
    
    # Subclass override to set the fields give more data
    def extra_data_to_restore(self, more_data):
        assert len(more_data) == 3
        self.cluster_df, self.cluster_and_cur_run_df, self.Ns = more_data
        assert len(self.cluster_and_cur_run_df) >= len(self.cluster_df) 
        
    # Subclass override to provide more data to be written
    def extra_data_to_save(self):
        return [self.cluster_df, self.cluster_and_cur_run_df, self.Ns]

    def compute_CSI(self, df_to_update):
        if len(df_to_update) == 0:
            df_to_update[['Saturation', 'Intensity', 'SI']] = np.nan
            return  # Nothing to do for empty data
        # If SiSatNodes columns not exist.  Fill in default values here
        if not NonMetricName.SI_SAT_NODES in df_to_update.columns: 
            df_to_update[NonMetricName.SI_SAT_NODES]=[DEFAULT_CHOSEN_NODE_SET]*len(df_to_update)
        if not NonMetricName.SI_CLUSTER_NAME in df_to_update.columns: 
            df_to_update[NonMetricName.SI_CLUSTER_NAME]=''
        # Union of all sets of SI_SAT_NODES
        #self.chosen_node_set = set().union(*df_to_update[NonMetricName.SI_SAT_NODES].tolist())    
        #chosen_node_set = self.chosen_node_set
        chosen_node_set = set().union(*df_to_update[NonMetricName.SI_SAT_NODES].tolist())    

        # Fill the NA entries with ''
        df_to_update.fillna({NonMetricName.SI_CLUSTER_NAME:''}, inplace=True)
        #self.compute_capacity(df_to_update)
        self.compute_saturation(df_to_update, chosen_node_set)
        self.compute_intensity(df_to_update, chosen_node_set)
        df_to_update['SI'] = df_to_update['Saturation'] * df_to_update['Intensity'] 

    @classmethod
    def capacities(cls, nodesWithUnit):
        return list(map(lambda n: cls.capacity(n), nodesWithUnit))
        
    @classmethod
    def capacity(cls, nodeWithUnit):
        # Remove brackets and then use the splitted node + unit to get the enum
        return MetricName.cap(*nodeWithUnit.replace("[", "").replace("]", "").split(" "))

    @classmethod
    def stallPcts(cls, nodesWithUnit):
        return list(map(lambda n: cls.stallPct(n), nodesWithUnit))

    @classmethod
    def stallPct(cls, nodeWithUnit):
        # Remove brackets and then use the splitted node + unit to get the enum
        return MetricName.stallPct(INV_NODE_UNIT_DICT[nodeWithUnit])


    def compute_saturation_old(self, df, chosen_node_set):
        listOfCapacityColumns = self.capacities(chosen_node_set)
        #nodeMax=df[listOfCapacityColumns].max(axis=0)
        # Below will compute the groupped capacity max based on SI_CLUSTER_NAME
        # The transform() will send the max values back to the original dataframe
        newNodeMax = df[listOfCapacityColumns+[NonMetricName.SI_CLUSTER_NAME]].groupby(by=[NonMetricName.SI_CLUSTER_NAME]).transform(max)
        #nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
        newNodeMax = newNodeMax.applymap(lambda x: x if x > 1.00 else 100.00)
        print ("<=====compute_saturation======>")
        for node in chosen_node_set - REAL_BUFFER_NODE_SET:
            #df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
            df['RelSat_{}'.format(node)]=df[self.capacity(node)] / newNodeMax[self.capacity(node)]
        # For control unit node, use raw % stalls as rel_sat 
        for node in chosen_node_set & REAL_BUFFER_NODE_SET:
            #df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
            df['RelSat_{}'.format(node)]=df[self.stallPct(node)] / df[self.stallPct(node)].max() 
        df['SatSats']=df[NonMetricName.SI_SAT_NODES].apply(lambda ns: list(map(lambda n: "RelSat_{}".format(n), ns)))
        df['Saturation'] = df.apply(lambda x: x[x['SatSats']].sum(), axis=1)
        #df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)
        # Per defined by Dave, codelets with no cluster will have Saturation being undefined, so set them to nan
        df.loc[df[NonMetricName.SI_CLUSTER_NAME] == '', 'Saturation']=np.nan
        df.drop('SatSats', axis=1, inplace=True)

    def compute_saturation(self, df, chosen_node_set):
        listOfCapacityColumns = self.capacities(chosen_node_set - REAL_BUFFER_NODE_SET)
        listOfPctColumns = self.stallPcts(chosen_node_set & REAL_BUFFER_NODE_SET)
        listOfColumns = listOfCapacityColumns+listOfPctColumns
        def max_clusters_only(x):
            return x[x['is_cluster'] == True].max()
        #nodeMax=df[listOfCapacityColumns].max(axis=0)
        # Below will compute the groupped capacity max based on SI_CLUSTER_NAME
        # The transform() will send the max values back to the original dataframe
        cluster_mask = df['is_cluster']==True
        newNodeMax = df[listOfColumns+[NonMetricName.SI_CLUSTER_NAME, 'is_cluster']] \
            .groupby(by=[NonMetricName.SI_CLUSTER_NAME]).apply(lambda x: max_clusters_only(x[['is_cluster']+listOfColumns]))
        #nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
        #newNodeMax[listOfCapacityColumns] = newNodeMax[listOfCapacityColumns].applymap(lambda x: x if x > 0.01 else 1.00)
        newNodeMax[listOfCapacityColumns] = newNodeMax[listOfCapacityColumns].applymap(lambda x: x if x > 1 else 100)
        newNodeMax[listOfPctColumns] = newNodeMax[listOfPctColumns].applymap(lambda x: x if x > 0.01 else 1)
        working=pd.merge(left=df, right=newNodeMax, on=[NonMetricName.SI_CLUSTER_NAME], suffixes=('','_max'))
        print ("<=====compute_saturation======>")
        #for node in chosen_node_set - REAL_BUFFER_NODE_SET:
        for node in chosen_node_set:
            metric_name = self.stallPct(node) if node in REAL_BUFFER_NODE_SET else self.capacity(node)
            working[f'RelSat_{node}']=(working[metric_name] / working[f'{metric_name}_max']).clip(upper=1.0)
        # # For control unit node, use raw % stalls as rel_sat 
        # for node in chosen_node_set & REAL_BUFFER_NODE_SET:
        #     #df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
        #     df['RelSat_{}'.format(node)]=df[self.stallPct(node)] / df[self.stallPct(node)].max() 
        import_dataframe_columns(df, working, [f'RelSat_{n}' for n in chosen_node_set])

        # Make SatSats tuples so it can be used for groupby
        df['SatSats'] = df[NonMetricName.SI_SAT_NODES].apply(lambda ns: tuple(map(lambda n: "RelSat_{}".format(n), ns)))
        df['Saturation'] = df.groupby('SatSats').apply(lambda x: x[list(x.name)].sum(axis=1).to_frame('Saturation'))
        #df['Saturation'] = df.apply(lambda x: x[x['SatSats']].sum(), axis=1)
        #df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)
        # Per defined by Dave, codelets with no cluster will have Saturation being undefined, so set them to nan
        df.loc[df[NonMetricName.SI_CLUSTER_NAME] == '', 'Saturation']=np.nan
        df.drop('SatSats', axis=1, inplace=True)


    def compute_intensity(self, df, chosen_node_set):
        df['SatCaps']=df[NonMetricName.SI_SAT_NODES].apply(lambda ns: tuple(self.capacities(ns)))
        node_cnt=df[NonMetricName.SI_SAT_NODES].apply(lambda ns: len(ns))
        group_by_satcaps = df.groupby('SatCaps')
        csum = group_by_satcaps.apply(lambda x: x[list(x.name)].sum(axis=1).to_frame('csum')).squeeze()
        cmax = group_by_satcaps.apply(lambda x: x[list(x.name)].max(axis=1).to_frame('cmax')).squeeze()
        #csum = df.apply(lambda x: x[x['SatCaps']].sum(), axis=1)
        #cmax = df.apply(lambda x: x[x['SatCaps']].max(), axis=1)
        #df['Intensity']=node_cnt*df[MetricName.CAP_ALLMAX_GW_P_S] / csum
        df['Intensity']=node_cnt*cmax / csum

        #node_cnt = len(chosen_node_set)
        #csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
        #df['Intensity']=node_cnt*df[MetricName.CAP_MEMMAX_GB_P_S] / csum
        df.drop('SatCaps', axis=1, inplace=True)

MEM_NODE_SET={'L1 [GW/s]', 'L2 [GW/s]', 'L3 [GW/s]', 'RAM [GW/s]'}
REG_NODE_SET={'VR [GW/s]'}
OP_NODE_SET={'FLOP [GFlop/s]'}
BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET | REG_NODE_SET
SCALAR_NODE_SET={'L1 [GW/s]', 'L2 [GW/s]', 'L3 [GW/s]', 'RAM [GW/s]'}
REAL_BUFFER_NODE_SET={'FE [GW/s]', 'SB [GW/s]', 'LM [GW/s]', 'RS [GW/s]', 'LB [GW/s]'}
BUFFER_NODE_SET=REAL_BUFFER_NODE_SET | {'CU [GW/s]'}
ALL_NODE_SET = BASIC_NODE_SET | BUFFER_NODE_SET
# Dictionary to lookup node name to its unit to use
NODE_UNIT_DICT = dict(node_unit.split(" ") for node_unit in ALL_NODE_SET)
INV_NODE_UNIT_DICT = dict([node_unit, node_unit.split(" ")[0]] for node_unit in ALL_NODE_SET) 
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FE'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR'}
DEFAULT_CHOSEN_NODE_SET=BASIC_NODE_SET

# # For node using derived metrics (e.g. FE), make sure the depended metrics are computed
# capacity_formula= {
#     }

# class SiPlot(CapacityPlot):
#     def __init__(self, data, variant, outputfile_prefix, norm, title, 
class SiPlot(CapePlot):
    def __init__(self, data=None, loadedData=None, level=None, variant=None, outputfile_prefix=None, norm=None, title=None, 
                 filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
        super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot=False, gui=True, x_axis=None, y_axis=None, 
                         default_y_axis = 'Saturation', default_x_axis = 'Intensity', filtering = filtering, mappings=mappings, 
                         short_names_path=short_names_path)
        # cur_run_df already set when self.data is created
        #self.data.set_chosen_node_set (chosen_node_set)
        #self.data.set_norm(norm)
        #self.data.set_cluster_df(cluster_df)
        #self.norm = norm
        #self.cur_run_df = cur_run_df
        #self.cluster_df = cluster_df
        self.filter_data = filter_data

    def setAttrs(self, data, loadedData, level, variant, outputfile_prefix, norm, title, 
                 filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
        self._setAttrs(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot=False, gui=True, x_axis=None, y_axis=None, 
                         default_y_axis = 'Saturation', default_x_axis = 'Intensity', filtering = filtering, mappings=mappings, 
                         short_names_path=short_names_path)


    # df here is the cur_run_df
    # def mk_data(self, df):
    #     self.data = SiData(df)

    # Getter of cluster_and_cur_run_df, delegate to self.data
    @property
    def cluster_and_cur_run_df(self):
        cluster_df = self.cluster_df
        cur_run_df = self.df
        return pd.concat([cluster_df, cur_run_df], ignore_index=True)
        #return self.data.cluster_and_cur_run_df
        
    @property
    def cur_run_df(self):
        return self.df

    # @property
    # def Ns(self):
    #     return max([data.Ns for data in self.data], default=0)
    
    # Getter of cluster_df, delegate to self.data
    @property
    def cluster_df(self):
        # In case need to use drop_duplicates(uture.  We can use the following trick
        # df = pd.concat([data.cluster_df for data in self.data])
        # return df.loc[df.astype(str).drop_duplicates().index]
        return pd.concat([data.cluster_df for data in self.data], ignore_index=True)

        #return self.data.cluster_df

    # Getter of norm, delegate to self.data
    @property
    def norm(self):
        return self.data.norm

    def mk_labels(self):
        l_df = self.df
        #orig_codelet_index = l_df[SHORT_NAME]
        # orig_codelet_variant = l_df[VARIANT]
        # orig_codelet_memlevel = l_df[MEM_LEVEL]
        #mytext= [str('({0})'.format( orig_codelet_index[i] ))  for i in range(len(orig_codelet_index))]
        mytext = l_df[SHORT_NAME].map('({0})'.format).tolist()
        return mytext


    # Update the data frame containing plot data.
    def filter_data_points(self, l_df):
        filter_data = self.filter_data
        l_df = l_df.loc[(l_df[filter_data[0]] >= filter_data[1]) & (l_df[filter_data[0]] <= filter_data[2])]
        return l_df

    def mk_plot_title(self, title, variant, scale):
        # chosen_node_set = self.chosen_node_set
        chosen_node_list = sorted(set().union(*self.df['SiSatNodes'].to_list()))
        # If chosen_node_set is too long then we need to add more new lines as matplotlib doesn't handle this automatically
        # 80 chars is the max that will fit on a line
        title = "" if title is None else f"{title} : "
        title = f"{title}n = {len(chosen_node_list)}\n"
        title = title + ", ".join(chosen_node_list)
        # nodes = sorted(list(chosen_node_set))
        # chars = 0
        # for i, node in enumerate(nodes):
        #     chars += len(node)
        #     if chars > 80:
        #         title += "\n"
        #         chars = 0
        #     title += node
        #     if i != len(nodes) - 1:
        #         title += ", "
        return title
        # return "{} \n n = {}{} \n".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))))

    def set_plot_scale(self, scale):
        ax = self.ax
        cluster_and_cur_run_ys = self.cluster_and_cur_run_df['Saturation']
        cluster_and_cur_run_xs = self.cluster_and_cur_run_df['Intensity']
        min_xs, max_xs, min_ys, max_ys = self.get_min_max(cluster_and_cur_run_xs, cluster_and_cur_run_ys)
        self.xmax=max(max_xs, self.xmax)
        self.ymax=max(max_ys, self.ymax)
        self.xmin=min(min_xs, self.xmin)
        self.ymin=min(min_ys, self.ymin)

        # Set specified axis scales
        if scale == 'linear' or scale == 'linearlinear':
            pass
        elif scale == 'log' or scale == 'loglog':
            ax.set_xscale("log")
            ax.set_yscale("log")
        elif scale == 'loglinear':
            ax.set_xscale("log")
        elif scale == 'linearlog':
            ax.set_yscale("log")

        print("Entering plot_data_orig_point")

        ax.set_xlim((0, self.xmax))
        ax.set_ylim((0, self.ymax))

    def mk_label_key(self):
        return "I$_C$$_G$ = 1.59, " + "S$_C$$_G$ = 4.06, " + "k$_C$$_G$ = 6.48, Label = (name)"

    def draw_contours(self, maxx, maxy):
        cluster_and_cur_run_ys = self.cluster_and_cur_run_df['Saturation']
        cluster_and_cur_run_xs = self.cluster_and_cur_run_df['Intensity']
        min_xs, max_xs, min_ys, max_ys = self.get_min_max(cluster_and_cur_run_xs, cluster_and_cur_run_ys)
        maxx=max(max_xs, maxx)
        maxy=max(max_ys, maxy)

        #Ns = self.Ns
        ax = self.ax
        #ns = [1,2,(Ns-1), Ns, (Ns+1),(Ns+2)]
        ns = range(2, 12, 2)
        npoints=40

        ctx=np.linspace(0, maxx, npoints+1)
        ctx=np.delete(ctx, 0) # Drop first element of 0

        lines=[]
        for n in ns:
            cty=n/ctx
            lines.append(ax.plot(ctx, cty, label='k={}'.format(n))[0])
        self.ctxs = lines

        # Create a Rectangle patch
        # (but not saved in self.ctxs)
        self.cluster_rects = {}
        for i, cluster in enumerate(self.df[NonMetricName.SI_CLUSTER_NAME].unique()):
            if cluster:
                if cluster in self.color_map['Label'].tolist(): color = self.color_map.loc[self.color_map['Label']==cluster]['Color'].iloc[0]
                else: 
                    try: color = self.COLOR_ORDER[i]
                    except: color = CapePlotColor.DEFAULT_COLOR
                target_df = self.cluster_df.loc[self.cluster_df[NonMetricName.SI_CLUSTER_NAME] == cluster]
                print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
                rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])), 
                                (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor=color,facecolor='none')
                self.cluster_rects[cluster] = rect
                ax.add_patch(rect)
        self.set_rect_visibility()

    def is_cluster_hidden(self, cluster):
        hidden_mask = self.guiState.get_hidden_mask(self.df)
        return cluster not in self.df[~hidden_mask][NonMetricName.SI_CLUSTER_NAME].tolist()
    
    def set_rect_visibility(self):
        for cluster in self.cluster_rects:
            if self.is_cluster_hidden(cluster):
                self.cluster_rects[cluster].set_alpha(0)
            else:
                self.cluster_rects[cluster].set_alpha(1)

    def update_contours(self):
        for cluster in self.cluster_rects:
            if cluster in self.color_map['Label'].tolist(): 
                rect_color = self.color_map.loc[self.color_map['Label']==cluster]['Color'].iloc[0]
                self.cluster_rects[cluster].set_edgecolor(rect_color)
        self.set_rect_visibility()

# For node using derived metrics (e.g. FE), make sure the depended metrics are computed


# TODO: more refactoring to generalize for other plots
class StaticSiPlot(SiPlot):
    def __init__(self, sidata, source_title, outfile):
        self.sidata = sidata
        super().__init__(None)
        self.source_title = source_title
        self.outfile = outfile
        self._color_map = self.df[KEY_METRICS].copy()
        self._color_map['Label'] = ''
        self._color_map['Color'] = [CapePlotColor.DEFAULT_COLOR] *len(self._color_map)


    def init_plotData(self):
        self.plotData = StaticPlotData(df=self.df, xs=None, ys=None, mytexts=None, ax=None, title=None, 
                                 labels=None, markers=None, name_mapping=None, mymappings=None, guiState=None, plot=self, 
                                 xmax=None, ymax=None, xmin=None, ymin=None, variant=None, names=None)

    @property
    def df(self):
        return self.sidata.df
    @property
    def cluster_df(self):
        return self.sidata.cluster_df

    def hide_labels(self):
        self.plotData.hide_labels()

    def set_labels(self, labels):
        self.plotData.set_labels(labels)

    def skip_adjustText(self):
        self.plotData.skip_adjustText()

    @property
    def color_map(self):
        return self._color_map

    def is_cluster_hidden(self, cluster):
        return False

    def get_visible_df(self):
        return self.df

    @property
    def mapping(self): 
        return pd.DataFrame()

    def get_source_title(self):
        return self.source_title

    def get_encoded_names(self, df):
        return df[MetricName.NAME] + df[MetricName.TIMESTAMP].astype(str)

    def finish_plot(self, df, xs, ys, mytexts, ax, title, labels, markers, name_mapping, mymappings, scale):
        super().finish_plot(df, xs, ys, mytexts, ax, title, labels, markers, name_mapping, mymappings, scale)
        self.adjustText()
        self.fig.tight_layout()
        self.fig.savefig(self.outfile)


def parse_ip_df(cluster_df, outputfile, norm, title, chosen_node_set, cur_run_df, variants, filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
    # Computation to get SI in the cluster df and then combine with the summary df

    # Only show selected variants, default is 'ORIG'
    cur_run_df = cur_run_df.loc[cur_run_df[VARIANT].isin(variants)].reset_index(drop=True)

    #return compute_and_plot('ORIG', full_df, 'SIPLOT', norm, title, chosen_node_set, target_df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale, short_names_path=short_names_path)
    siData = mk_data(cluster_df, norm, cur_run_df, chosen_node_set)
    siData.compute()
    plot = SiPlot (siData, 'ORIG', 'SIPLOT', norm, title, chosen_node_set, cluster_df, variants=variants, \
        filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)
    

def mk_data(cluster_df, norm, cur_run_df, chosen_node_set = DEFAULT_CHOSEN_NODE_SET):
    siData = SiData(cur_run_df)
    siData.set_chosen_node_set_with_unit(chosen_node_set)
    siData.set_norm(norm)
    siData.set_cluster_df(cluster_df)
    return siData

def compute_only(cluster_df, norm, cur_run_df, chosen_node_set = DEFAULT_CHOSEN_NODE_SET):
    siData = mk_data(cluster_df, norm, cur_run_df, chosen_node_set)
    siData.compute()
    return siData.cluster_df, siData.cluster_and_cur_run_df, siData.df

def parse_ip(inputfile,outputfile, norm, title, chosen_node_set, rfile):
#    inputfile="/tmp/input.csv"
    cur_run_df = pd.read_csv(rfile)
    parse_ip_df(inputfile, outputfile, norm, title, chosen_node_set, cur_run_df)


def usage(reason):
    error_code = 0
    if reason:
        print ('\nERROR: {}!\n'.format(reason))
        error_code = 2
    print ('Usage:\n  generate_SI.py  -i <inputfile> -o <outputfile prefix> -n norm (row,matrix) -l <nodes> (optionally)>')
    print ('Example:\n  generate_SI.py  -i input.csv -o out.csv -n row -l L1,L2,L3,FLOP,VR')
    sys.exit(error_code)
    
def main(argv):
    #if len(argv) != 8 and len(argv) != 6 and len(argv) != 4 and len(argv) != 2 and len(argv) != 1:
    #    usage('Wrong number of arguments')
    inputfile = []
    rfile = []
    outputfile = []
    node_list = []
    norm = 'row'
    title=""
    chosen_node_set = DEFAULT_CHOSEN_NODE_SET
    try:
        opts, args = getopt.getopt(argv, "hi:o:n:l:r:")
        print (opts)
        print (args)
    except getopt.GetoptError:
        usage('Wrong argument opts(s)')
    if len(args) != 0:
        usage('Wrong argument(s)')
    for opt, arg in opts:
        if opt == '-h':
            usage([])
        elif opt == '-n':
            normobj = arg
            print (normobj)
            if normobj != 'matrix' and normobj != 'row':
                print ('norm has to be either matrix or row')
            else:
                norm = normobj
        elif opt == '-l':
            node_list = arg.split(',')
            print (node_list)
            chosen_node_set = set(node_list)
            print (chosen_node_set)
        elif opt == '-i':
            inputfile.append(arg)
            matchobj = re.search(r'(.+?)\.csv', arg)
            title = str(matchobj.group(1))
            if not matchobj:
                print ('inputfile should be a *.csv file')
                sys.exit()
        elif opt == '-r':
            rfile.append(arg)
            r_matchobj = re.search(r'(.+?)\.csv', arg)
            if not r_matchobj:
                print ('rfile should be a *.csv file')
                sys.exit()
        elif opt == '-o':
            outputfile.append(arg)
    if matchobj and len(outputfile) == 0:
        outputfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
        rfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
    print ('Inputfile: ', inputfile[0])
    #print ('Rfile: ', rfile[0])
    print ('Outputfile: ', outputfile[0])
    print ('Norm: ', norm)
    print ('Node List: ', node_list)
    parse_ip(inputfile[0],outputfile[0], norm, title.upper(), chosen_node_set, rfile[0])

if __name__ == "__main__":
    main(sys.argv[1:])