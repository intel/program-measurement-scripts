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
from capeplot import CapacityPlot

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text
from matplotlib.patches import Rectangle
import statistics
from matplotlib.legend import Legend
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.



BASIC_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]', 'VR [GB/s]', 'RAM [GB/s]'}
MEM_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
SCALAR_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
BUFFER_NODE_SET={'FE', 'CU', 'SB', 'LM', 'RS'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FE'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'VR'}
DEFAULT_CHOSEN_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]'}

# For node using derived metrics (e.g. FE), make sure the depended metrics are computed
capacity_formula= {
    'L1 [GB/s]': (lambda df : df[RATE_L1_GB_P_S]/8),
    'L2 [GB/s]': (lambda df : df[RATE_L2_GB_P_S]/8),
    'L3 [GB/s]': (lambda df : df[RATE_L3_GB_P_S]/8),
    'FLOP [GFlop/s]': (lambda df : df[RATE_FP_GFLOP_P_S]),
    'VR [GB/s]': (lambda df : df[RATE_REG_SIMD_GB_P_S]/24),
    'RAM [GB/s]': (lambda df : df[RATE_RAM_GB_P_S]/8),
    'FE': (lambda df : df[STALL_FE_PCT]*(df['C_max [GB/s]'])),
    'SB': (lambda df : df[STALL_SB_PCT]*(df['C_max [GB/s]'])),
    'LM': (lambda df : df[STALL_LM_PCT]*(df['C_max [GB/s]'])),
    'RS': (lambda df : df[STALL_RS_PCT]*(df['C_max [GB/s]'])),
    'CU': (lambda df : (df[STALL_FE_PCT]*df['C_scalar'] + df[STALL_LB_PCT]*df['C_scalar'] + df[STALL_SB_PCT]*df['C_scalar'] + df[STALL_LM_PCT]*df['C_scalar']))
    }

class SiPlot(CapacityPlot):
    def __init__(self, variant, outputfile_prefix, norm, title, chosen_node_set, cluster_df, cur_run_df, variants=['ORIG'], 
                 filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
        super().__init__(chosen_node_set, variant, cur_run_df, outputfile_prefix, scale, title, no_plot=False, gui=True, x_axis=None, y_axis=None, 
                         default_y_axis = 'Saturation', default_x_axis = 'Intensity', filtering = filtering, mappings=mappings, short_names_path=short_names_path)
        self.norm = norm
        self.cur_run_df = cur_run_df
        self.variants = variants
        self.filter_data = filter_data
        self.cluster_df = cluster_df
        
    def compute_capacity(self, df):
        chosen_node_set = self.chosen_node_set
        norm = self.norm
        print("The node list are as follows :")
        print(chosen_node_set)
        chosen_basic_node_set = BASIC_NODE_SET & chosen_node_set
        chosen_buffer_node_set = BUFFER_NODE_SET & chosen_node_set
        for node in chosen_basic_node_set:
            print ("The current node : ", node)
            formula=capacity_formula[node]
            df['C_{}'.format(node)]=formula(df)

        if norm == 'row':
            print ("<=====Running Row Norm======>")
            df['C_max [GB/s]']=df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1)
        else:
            print ("<=====Running Matrix Norm======>")
            df['C_max [GB/s]']=max(df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1))
        print ("<=====compute_capacity======>")

        if norm == 'row':
            print ("<=====Running Row Norm======>")
            df['C_scalar']=df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1)
        else:
            print ("<=====Running Matrix Norm======>")
            df['C_scalar']=max(df[list(map(lambda n: "C_{}".format(n), SCALAR_NODE_SET))].max(axis=1))
        print ("<=====compute_cu_scalar======>")
        for node in chosen_buffer_node_set:
            formula=capacity_formula[node]
            df['C_{}'.format(node)]=formula(df)
        # Compute memory level 
        chosen_mem_node_set = MEM_NODE_SET & chosen_node_set
        # Below will get the C_* name with max value
        df[MEM_LEVEL]=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
        # Remove the first two characters which is 'C_'
        df[MEM_LEVEL] = df[MEM_LEVEL].apply((lambda v: v[2:]))
        # Drop the unit
        df[MEM_LEVEL] = df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)

    def compute_extra(self):
        cluster_df = self.cluster_df
        cur_run_df = self.cur_run_df
        self.compute_CSI(cluster_df)
        # Capcacity already computed in compute_capacity() method so commented below
        # for node in sorted(chosen_node_set):
        #     formula=capacity_formula[node]
        #     cluster_df['C_{}'.format(node)]=formula(cluster_df)
        # cluster_df['SI']=cluster_df['Saturation'] * cluster_df['Intensity'] 
        # Use the 1.0 speedup for now.  If cluster file has speedup metric, make sure it 
        # is using "Speedup" name starting with capital "S"
        #target_df['speedup'] = cluster_df['speedup']
        cluster_df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup

        #column_list = cluster_df.columns.tolist()
        #column_list.extend([TIME_APP_S, TIMESTAMP, COVERAGE_PCT, 'Color'])
        cluster_df[TIMESTAMP]=0
        cluster_df[TIME_APP_S]=0.0
        cluster_df[COVERAGE_PCT]=0.0
        cluster_df['Color'] = ""
        column_list = cluster_df.columns

        #cur_run_data_df = pd.DataFrame(columns=column_list)
        #cur_run_data_df = cur_run_data_df.append(cur_run_df, ignore_index=False)[column_list]

        #cluster_and_cur_run_df = concat_ordered_columns([cluster_df,cur_run_data_df])
        cluster_and_cur_run_df = self.concat_ordered_columns([cluster_df,cur_run_df])[column_list]
        #self.cluster_df = cluster_df

        # Compute Capacity, Saturation and intensity again for all the runs (cluster + current runs).
        self.compute_CSI(cluster_and_cur_run_df)
        cluster_and_cur_run_df['SI']=cluster_and_cur_run_df['Saturation'] * cluster_and_cur_run_df['Intensity'] 

        self.cluster_and_cur_run_df = cluster_and_cur_run_df
        # Select the rows corresponding to cur_run_df for plotting
        self.df = cluster_and_cur_run_df.tail(len(cur_run_df))

        # out_df looks unused so groupped together and commented out below
        # out_df = pd.DataFrame()
        # out_df[[NAME, SHORT_NAME, VARIANT]] = cluster_and_cur_run_df[[NAME, SHORT_NAME, VARIANT]]
        # for node in sorted(chosen_node_set):
        #     formula=capacity_formula[node]
        #     out_df['C_{}'.format(node)]=formula(cluster_and_cur_run_df)
        # # out_df['C_scalar'] = cluster_and_cur_run_df['C_scalar']
        # out_df['Saturation'] = cluster_and_cur_run_df['Saturation']
        # out_df['Intensity'] = cluster_and_cur_run_df['Intensity']
        # out_df['k'] = cluster_and_cur_run_df['Saturation'] * cluster_and_cur_run_df['Intensity']
        # out_df['speedup'] = cluster_and_cur_run_df['speedup']

        # below also looked unused so commented out
        # indices = cluster_and_cur_run_df[SHORT_NAME]
        # k = cluster_and_cur_run_df['SI']
        # k_avg = k.mean()

        cluster_and_cur_run_df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup    
        self.Ns = len(self.chosen_node_set)

    def compute_CSI(self, df_to_update):
        chosen_node_set = self.chosen_node_set
        self.compute_capacity(df_to_update)
        self.compute_saturation(df_to_update, chosen_node_set)
        self.compute_intensity(df_to_update, chosen_node_set)

    def mk_labels(self):
        l_df = self.df
        orig_codelet_index = l_df[SHORT_NAME]
        orig_codelet_variant = l_df[VARIANT]
        orig_codelet_memlevel = l_df[MEM_LEVEL]
        mytext= [str('({0}, {1}, {2})'.format( orig_codelet_index[i], orig_codelet_variant[i], orig_codelet_memlevel[i]))  for i in range(len(orig_codelet_index))]
        return mytext


    # Update the data frame containing plot data.
    def filter_data_points(self, l_df):
        filter_data = self.filter_data
        l_df = l_df.loc[(l_df[filter_data[0]] >= filter_data[1]) & (l_df[filter_data[0]] <= filter_data[2])]
        return l_df

    def mk_plot_title(self, title, variant, scale):
        chosen_node_set = self.chosen_node_set
        return "{} \n n = {}{} \n".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))))

    def set_plot_scale(self, scale, xmax, ymax, xmin, ymin):
        ax = self.ax
        cluster_and_cur_run_ys = self.cluster_and_cur_run_df['Saturation']
        cluster_and_cur_run_xs = self.cluster_and_cur_run_df['Intensity']
        xmax=max(max(cluster_and_cur_run_xs)*1.2, xmax)
        ymax=max(max(cluster_and_cur_run_ys)*1.2, ymax)
        xmin=min(min(cluster_and_cur_run_xs), xmin)
        ymin=min(min(cluster_and_cur_run_ys), ymin)

        # Set specified axis scales
        if scale == 'linear' or scale == 'linearlinear':
            pass
        elif scale == 'log' or scale == 'loglog':
            plt.xscale("log")
            plt.yscale("log")
        elif scale == 'loglinear':
            plt.xscale("log")
        elif scale == 'linearlog':
            plt.yscale("log")

        print("Entering plot_data_orig_point")

        ax.set_xlim((0, xmax))
        ax.set_ylim((0, ymax))

    def mk_label_key(self):
        return "I$_C$$_G$ = 1.59, " + "S$_C$$_G$ = 4.06, " + "k$_C$$_G$ = 6.48, Label = (name, variant, memlevel)"

    def draw_contours(self, maxx, maxy):
        cluster_and_cur_run_ys = self.cluster_and_cur_run_df['Saturation']
        cluster_and_cur_run_xs = self.cluster_and_cur_run_df['Intensity']
        maxx=max(max(cluster_and_cur_run_xs)*1.2, maxx)
        maxy=max(max(cluster_and_cur_run_ys)*1.2, maxy)

        Ns = self.Ns
        ax = self.ax
        ns = [1,2,(Ns-1), Ns, (Ns+1),(Ns+2)]
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
        target_df = self.cluster_df
        print ("intensity anchor points :" , min(target_df['Intensity']) , " , " , min(target_df['Saturation']))
        rect = Rectangle((min(target_df['Intensity']),min(target_df['Saturation'])),(max(target_df['Intensity'])- min(target_df['Intensity'])), 
                         (max(target_df['Saturation']) - min(target_df['Saturation'])),linewidth=1,edgecolor='r',facecolor='none')
        ax.add_patch(rect)

    def compute_saturation(self, df, chosen_node_set):
        nodeMax=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].max(axis=0)
        nodeMax =  nodeMax.apply(lambda x: x if x >= 1.00 else 100.00 )
        print ("<=====compute_saturation======>")
        for node in chosen_node_set:
            df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
        df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)


    def compute_intensity(self, df, chosen_node_set):
        node_cnt = len(chosen_node_set)
        csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
        df['Intensity']=node_cnt*df['C_max [GB/s]'] / csum


# For node using derived metrics (e.g. FE), make sure the depended metrics are computed

    def concat_ordered_columns(self, frames):
        columns_ordered = []
        for frame in frames:
            columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
        final_df = pd.concat(frames)
        # final_df[TIMESTAMP] = final_df[TIMESTAMP].fillna(0).astype(int)
        return final_df[columns_ordered]

def parse_ip_df(cluster_inputfile, outputfile, norm, title, chosen_node_set, cur_run_df, variants=['ORIG'], filtering=False, filter_data=None, mappings=pd.DataFrame(), scale='linear', short_names_path=''):
    if not mappings.empty:
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
        'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
    # Computation to get SI in the cluster df and then combine with the summary df
    cluster_df = pd.read_csv(cluster_inputfile)

    # Only show selected variants, default is 'ORIG'
    cur_run_df = cur_run_df.loc[cur_run_df[VARIANT].isin(variants)]

    #return compute_and_plot('ORIG', full_df, 'SIPLOT', norm, title, chosen_node_set, target_df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale, short_names_path=short_names_path)
    plot = SiPlot ('ORIG', 'SIPLOT', norm, title, chosen_node_set, cluster_df, cur_run_df, variants=variants, \
        filtering=filtering, filter_data=filter_data, mappings=mappings, scale=scale, short_names_path=short_names_path)
    plot.compute_and_plot()
    return (plot.df, plot.fig, plot.plotData)
    

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