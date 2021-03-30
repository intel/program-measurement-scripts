#!/usr/bin/python3
import sys, getopt
import csv
import re
import os
from os.path import expanduser
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from matplotlib import style
import copy
from capeplot import CapacityPlot
from capeplot import CapacityData
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class QPlot(CapacityPlot):
	def __init__(self, data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui=False, x_axis=None, y_axis=None, 
              mappings=pd.DataFrame(), short_names_path=''): 
		super().__init__(data, loadedData, level, variant, outputfile_prefix, scale, title, no_plot, gui, x_axis, y_axis, 
                   default_y_axis=MetricName.CAP_MEMMAX_GB_P_S,  mappings=mappings, short_names_path=short_names_path)

	def mk_labels(self):
		df = self.df
		try:
			indices = df[SHORT_NAME]
		except:
			indices = df[NAME]
		memlevel = df[MEM_LEVEL]
		mytext = [str('({0}, {1})'.format(indices[i], memlevel[i])) for i in range(len(indices))]
		return mytext

	def mk_label_key(self):
		return "(name, MaxMemLevel[85%])"

	def mk_plot_title(self, title, variant, scale):
		chosen_node_set = self.chosen_node_set
		return "{} : N = {}{}, \nvariant={}, scale={}".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))), variant, scale)

	def draw_contours(self, xmax, ymax, color_labels):
		ns = [1,2,4,8,16,32,64]
		ax = self.ax

		npoints=40
		ctx=np.linspace(0, xmax, npoints+1)
		ctxs=[]
		for n in ns:
			cty=n*ctx
			ctxs.append(ax.plot(ctx, cty, label='n={}'.format(n))[0])
		self.ctxs = ctxs

def parse_ip(inputfile,outputfile, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None):
	#	inputfile="/tmp/input.csv"
	input_data_source = sys.stdin if (inputfile == '-') else inputfile
	df = pd.read_csv(input_data_source)
	return parse_ip_df(df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis)

def parse_ip_df(df, outputfile, scale, title, chosen_node_set, no_plot, variants, gui=False, x_axis=None, y_axis=None, mappings=pd.DataFrame(), short_names_path=''):
	# Normalize the column names
		
	df = df.loc[df[VARIANT].isin(variants)].reset_index(drop=True)
	df_XFORM, fig_XFORM, plotData_XFORM = None, None, None
	#df_XFORM, fig_XFORM, plotData_XFORM = compute_and_plot('XFORM', df[~mask], outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, mappings)

	#df_ORIG, fig_ORIG, plotData_ORIG = compute_and_plot('ORIG', df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, mappings, short_names_path)
	## Return dataframe and figure for GUI
	#return (df_XFORM, fig_XFORM, plotData_XFORM, df_ORIG, fig_ORIG, plotData_ORIG)

	#for variant, group in grouped:
	#	compute_and_plot(variant, group, outputfile)

	data = CapacityData(df)
	data.set_chosen_node_set(chosen_node_set) 
	data.compute()
	plot = QPlot(data, 'ORIG', outputfile, scale, title, no_plot, gui, x_axis, y_axis, mappings, short_names_path)
	plot.compute_and_plot()
	return (df_XFORM, fig_XFORM, plotData_XFORM, plot.df, plot.fig, plot.plotData)



def usage(reason):
	error_code = 0
	if reason:
		print ('\nERROR: {}!\n'.format(reason))
		error_code = 2
	print ('Usage:\n  generate_SI.py  -i <inputfile> -o <outputfile prefix> -n norm (row,matrix) -l <nodes> (optionally)>')
	print ('Example:\n  generate_SI.py  -i input.csv -o out.csv -n row -l L1,L2,L3,FLOP,SIMD')
	sys.exit(error_code)
	
def main(argv):
	parser = ArgumentParser(description='Generate QPlot data from summary data.')
	parser.add_argument('-i', help='the input csv file', required=True, dest='in_file')
	parser.add_argument('-s', help='plot scale', required=False, choices=['linear','log','linearlog','loglinear'], 
						default='linear', dest='scale')
	parser.add_argument('-l', help='list of nodes', required=False, 
						default=','.join(sorted(list(DEFAULT_CHOSEN_NODE_SET))), dest='node_list')
	parser.add_argument('-o', help='the output file prefix', required=False, dest='out_file_prefix')
	parser.add_argument('--no-plot', action='store_true', help='Generate data but no plotting')
	args = parser.parse_args()
	print(args)

	# Check input file extension
	print(args.in_file)
	matchobj = re.search(r'(.+?)\.csv', args.in_file)
	if args.in_file == '-':
		title = "STDIN"
	else:
		title = str(matchobj.group(1).upper())
		
	if args.out_file_prefix is None:
		args.out_file_prefix = str(matchobj.group(1))

	# Construct chosen node set from comma-delimited string
	chosen_node_set = set(args.node_list.split(','))

	print ('Inputfile: ', args.in_file)
	print ('Outputfile prefix: ', args.out_file_prefix)
	print ('Scale: ', args.scale)
	print ('Title: ', title)
	print ('Node Set: ', chosen_node_set)
	parse_ip(args.in_file, args.out_file_prefix, args.scale, title, chosen_node_set, args.no_plot)

if __name__ == "__main__":
	main(sys.argv[1:])
