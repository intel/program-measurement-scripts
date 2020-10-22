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
from adjustText import adjust_text
import copy
from capeplot import CapacityPlot
from metric_names import MetricName
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

class QPlot(CapacityPlot):
	def __init__(self, variant, df, outputfile_prefix, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None, mappings=pd.DataFrame(), short_names_path=''): 
		super().__init__('C_max [GB/s]', chosen_node_set)
		self.variant = variant
		self.df = df 
		self.outputfile_prefix = outputfile_prefix 
		self.scale = scale
		self.title = title
		self.no_plot = no_plot
		self.gui = gui
		self.x_axis = x_axis
		self.y_axis = y_axis
		self.source_order = source_order
		self.mappings = mappings
		self.short_names_path = short_names_path

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
		return "(name, memlevel)"

	def mk_plot_title(self, title, variant, scale):
		chosen_node_set = self.chosen_node_set
		return "{} : N = {}{}, \nvariant={}, scale={}".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))), variant, scale)

	def draw_contours(self, xmax, ymax):
		ns = [1,2,4,8,16,32]
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

def parse_ip_df(df, outputfile, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None, variants=['ORIG'], source_order=None, mappings=pd.DataFrame(), short_names_path=''):
	# Normalize the column names
	if not mappings.empty:
		mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
		'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)

	grouped = df.groupby(VARIANT)
	# Only show selected variants, default is 'ORIG'
	df = df.loc[df[VARIANT].isin(variants)]
	df_XFORM, fig_XFORM, textData_XFORM = None, None, None
	#df_XFORM, fig_XFORM, textData_XFORM = compute_and_plot('XFORM', df[~mask], outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, mappings)

	#df_ORIG, fig_ORIG, textData_ORIG = compute_and_plot('ORIG', df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, mappings, short_names_path)
	## Return dataframe and figure for GUI
	#return (df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG)

	#for variant, group in grouped:
	#	compute_and_plot(variant, group, outputfile)

	plot = QPlot('ORIG', df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, source_order, mappings, short_names_path)
	plot.compute_and_plot()
	return (df_XFORM, fig_XFORM, textData_XFORM, plot.df, plot.fig, plot.plotData)



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
