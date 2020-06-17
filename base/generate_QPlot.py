#!/usr/bin/python3
import sys, getopt
import csv
import re
import os
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
from capelib import succinctify
from argparse import ArgumentParser

import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from adjustText import adjust_text
import tkinter as tk
from tkinter import ttk
from pandastable import Table

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

MEM_NODE_SET={'L1', 'L2', 'L3', 'RAM'}
OP_NODE_SET={'FLOP', 'SIMD'}
BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET

BUFFER_NODE_SET={'FrontEnd'}
DEFAULT_CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'RAM', 'FLOP'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
	'L1': (lambda df : df['l1_rate_gb/s']/8),
	'L2': (lambda df : df['l2_rate_gb/s']/8),
	'L3': (lambda df : df['l3_rate_gb/s']/8),
	'FLOP': (lambda df : df['flop_rate_gflop/s']),
	'SIMD': (lambda df : df['register_simd_rate_gb/s']/8),
	'RAM': (lambda df : df['ram_rate_gb/s']/8),
	'FrontEnd': (lambda df : df['%frontend']*df['C_max'])	
	}

def parse_ip(inputfile,outputfile, scale, title, chosen_node_set, no_plot, gui=False, analyzer_gui=None):
	#	inputfile="/tmp/input.csv"
	input_data_source = sys.stdin if (inputfile == '-') else inputfile
	df = pd.read_csv(input_data_source)
	# Normalize the column names
	df.columns = succinctify(df.columns)


	grouped = df.groupby('variant')
	# Destroy old Summary/QPlot if any
	for w in analyzer_gui.c_qplot_window.winfo_children():
		w.destroy()
	# Generate SI plot for each variant
	mask = df['variant'] == "ORIG"
	compute_and_plot('XFORM', df[~mask], outputfile, scale, title, chosen_node_set, no_plot, gui, analyzer_gui)
	compute_and_plot('ORIG', df[mask], outputfile, scale, title, chosen_node_set, no_plot, gui, analyzer_gui)
	#for variant, group in grouped:
	#	compute_and_plot(variant, group, outputfile)

def compute_capacity(df, chosen_node_set):
	print("The node list are as follows :")
	print(chosen_node_set)
	chosen_mem_node_set = MEM_NODE_SET & chosen_node_set
	for node in chosen_mem_node_set:
		print ("The current node : ", node)
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)

	df['C_max']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].max(axis=1)
	df = df[df['C_max'].notna()]
	df['memlevel']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
	# Remove the first two characters which is 'C_'
	df['memlevel'] = df['memlevel'].apply((lambda v: v[2:]))
	print ("<=====compute_capacity======>")
#	print(df['C_max'])

	chosen_op_node_set = OP_NODE_SET & chosen_node_set
	if len(chosen_op_node_set) > 1:
		print("Too many op node selected: {}".format(chosen_op_node_set))
		sys.exit(-1)
	elif len(chosen_op_node_set) < 1:
		print("No op node selected")
		sys.exit(-1)
	# Exactly 1 op node selected below
	op_node = chosen_op_node_set.pop()
	formula=capacity_formula[op_node]
	df['C_op']=formula(df)
	return df



def compute_saturation(df, chosen_node_set):
	nodeMax=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].max(axis=0)
	print ("<=====compute_saturation======>")
	print(nodeMax)
	for node in chosen_node_set:
		df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
	df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), chosen_node_set))].sum(axis=1)		
	#df['Saturation'].to_csv('export_dataframe.csv', index = False, header=True)
	#df.to_csv(export_dataframe.csv', index=False)
	print(df['Saturation'])


def compute_intensity(df, chosen_node_set):
	node_cnt = len(chosen_node_set)
	csum=df[list(map(lambda n: "C_{}".format(n), chosen_node_set))].sum(axis=1)
	df['Intensity']=node_cnt*df['C_max'] / csum
	print(df['Intensity'])


def compute_and_plot(variant, df,outputfile_prefix, scale, title, chosen_node_set, no_plot, gui=False, analyzer_gui=None):
	if df.empty:
		return # Nothing to do
	df = compute_capacity(df, chosen_node_set)
	#	compute_saturation(df, chosen_node_set)
	#	compute_intensity(df, chosen_node_set)
	output_data_source = sys.stdout if (outputfile_prefix == '-') else outputfile_prefix+variant+'_export_dataframe.csv'
	print('Saving to '+output_data_source)
	df[['name', 'variant','C_L1', 'C_L2', 'C_L3', 'C_RAM', 'C_max', 'memlevel', 'C_op']].to_csv(output_data_source, index = False, header=True)

	if no_plot:
		return

	try:
		indices = df['short_name']
	except:
		indices = df['name']
	xs = df['C_op']
	ys = df['C_max']
	mem_level=df['memlevel']
	today = datetime.date.today()
	if gui:
		outputfile=None
	else:
		outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, scale, today)	
	plot_data("{} : N = {}{}, \nvariant={}, scale={}".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))), variant, scale),
						outputfile, list(xs), list(ys),	list(indices), list(mem_level), scale, analyzer_gui)
	
	# Add summary dataframe to QPlot tab
	summary_frame = tk.Frame(analyzer_gui.c_qplot_window)
	summary_frame.pack()
	analyzer_gui.c_qplot_window.add(summary_frame, stretch='always')
	pt = Table(summary_frame, dataframe=df[['name', 'variant','C_L1', 'C_L2', 'C_L3', 'C_RAM', 'C_max', 'memlevel', 'C_op']],
				showtoolbar=True, showstatusbar=True)
	pt.show()
	pt.redraw()


def draw_contours(ax, maxx, ns):
	npoints=40

	ctx=np.linspace(0, maxx, npoints+1)
#	ctx=np.delete(ctx, 0) # Drop first element of 0

	lines=[]
	for n in ns:
		cty=n*ctx
		lines.append(ax.plot(ctx, cty, label='n={}'.format(n)))
	return lines

# Set filename to [] for GUI output	
def plot_data(title, filename, xs, ys, indices, memlevel, scale, analyzer_gui=None):
	DATA =tuple(zip(xs,ys))
    
	fig, ax = plt.subplots()

	#xmax=max(xs)*2
	xmax=max(xs)*1.2
	ymax=max(ys)*1.2  

	if scale == 'loglog':
		xmin=min(xs)
		ymin=min(ys)
		ax.set_xlim((xmin, xmax))
		ax.set_ylim((ymin, ymax))
		plt.xscale("log")
		plt.yscale("log")
	else:
		ax.set_xlim((0, xmax))
		ax.set_ylim((0, ymax))
    
	(x, y) = zip(*DATA)
	ax.scatter(x, y, marker='o')

	ns = [1,2,4,8,16,32]

	ctxs = draw_contours(ax, xmax, ns)
	mytext= [str('({0}, {1})'.format( indices[i], memlevel[i] ))  for i in range(len(DATA))]    
	texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
	#adjust_text(texts)
	adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

	ax.set(xlabel=r'OP Rate', ylabel=r'Memory Rate')
	ax.set_title(title, pad=40)

#	chartBox = ax.get_position()
#	ax.set_position([chartBox.x0,chartBox.y0,chartBox.width,chartBox.height*0.65])
#	ax.legend(loc="center left", bbox_to_anchor=(1,0.5),title="(name,memlevel)", mode='expand')
	ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0.,1.02,1.,.102),title="(name,memlevel)", mode='expand', borderaxespad=0.)
	plt.tight_layout()
	if filename:
		plt.savefig(filename)
	else:
		# Display QPlot from QPlot tab
		qplot_frame = tk.Frame(analyzer_gui.c_qplot_window)
		qplot_frame.pack()
		qplot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		analyzer_gui.c_qplot_window.add(qplot_frame, stretch='always')
		canvas = FigureCanvasTkAgg(fig, qplot_frame)
		toolbar = NavigationToolbar2Tk(canvas, qplot_frame)
		toolbar.update()
		canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		canvas.draw()
		canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

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
	parser.add_argument('-s', help='plot scale', required=False, choices=['scalar','loglog'], 
						default='scalar', dest='scale')
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
