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
from capelib import succinctify
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
from matplotlib import style
from adjustText import adjust_text
import copy

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.

MEM_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]'}
OP_NODE_SET={'FLOP [GFlop/s]', 'SIMD [GB/s]'}
BASIC_NODE_SET=MEM_NODE_SET | OP_NODE_SET

BUFFER_NODE_SET={'FrontEnd'}
DEFAULT_CHOSEN_NODE_SET={'L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'RAM [GB/s]', 'FLOP [GFlop/s]'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
	'L1 [GB/s]': (lambda df : df['l1_rate_gb/s']),
	'L2 [GB/s]': (lambda df : df['l2_rate_gb/s']),
	'L3 [GB/s]': (lambda df : df['l3_rate_gb/s']),
	'FLOP [GFlop/s]': (lambda df : df['flop_rate_gflop/s']),
	'SIMD [GB/s]': (lambda df : df['register_simd_rate_gb/s']),
	'RAM [GB/s]': (lambda df : df['ram_rate_gb/s']),
	'FrontEnd [GB/s]': (lambda df : df['%frontend']*df['C_max'])	
	}

def parse_ip(inputfile,outputfile, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None):
	#	inputfile="/tmp/input.csv"
	input_data_source = sys.stdin if (inputfile == '-') else inputfile
	df = pd.read_csv(input_data_source)
	return parse_ip_df(df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis)

def parse_ip_df(df, outputfile, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None, variants=['ORIG'], source_order=None, mappings=pd.DataFrame()):
	# Normalize the column names
	df.columns = succinctify(df.columns)
	if not mappings.empty:
		mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
		'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)

	grouped = df.groupby('variant')
	# Only show selected variants, default is 'ORIG'
	df = df.loc[df['variant'].isin(variants)]
	df_XFORM, fig_XFORM, textData_XFORM = None, None, None
	#df_XFORM, fig_XFORM, textData_XFORM = compute_and_plot('XFORM', df[~mask], outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, source_order, mappings)
	df_ORIG, fig_ORIG, textData_ORIG = compute_and_plot('ORIG', df, outputfile, scale, title, chosen_node_set, no_plot, gui, x_axis, y_axis, source_order, mappings)
	# Return dataframe and figure for GUI
	return (df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG)
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

	df['C_max [GB/s]']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].max(axis=1)
	df = df[df['C_max [GB/s]'].notna()]
	df['memlevel']=df[list(map(lambda n: "C_{}".format(n), chosen_mem_node_set))].idxmax(axis=1)
	# Remove the first two characters which is 'C_'
	df['memlevel'] = df['memlevel'].apply((lambda v: v[2:]))
	# Drop the unit
	df['memlevel'] = df['memlevel'].str.replace(" \[.*\]","", regex=True)
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
	op_metric_name = 'C_{}'.format(op_node)
	formula=capacity_formula[op_node]
	df[op_metric_name]=formula(df)
	return df, op_metric_name



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
	df['Intensity']=node_cnt*df['C_max [GB/s]'] / csum
	print(df['Intensity'])

def compute_color_labels(df):
	color_labels = []
	for color in df['color'].unique():
		colorDf = df.loc[df['color']==color].reset_index()
		codelet = (colorDf['name'][0])
		color_labels.append((codelet.split(':')[0], color))
	return color_labels

def compute_and_plot(variant, df,outputfile_prefix, scale, title, chosen_node_set, no_plot, gui=False, x_axis=None, y_axis=None, source_order=None, mappings=pd.DataFrame()):
	if df.empty:
		return None, None, None # Nothing to do
	df, op_node_name = compute_capacity(df, chosen_node_set)
	#	compute_saturation(df, chosen_node_set)
	#	compute_intensity(df, chosen_node_set)
	output_data_source = sys.stdout if (outputfile_prefix == '-') else outputfile_prefix+variant+'_export_dataframe.csv'
	#print('Saving to '+output_data_source)
	#df[['name', 'variant','C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel', op_node_name]].to_csv(output_data_source, index = False, header=True)
	
	# Used to create a legend of file names to color for multiple plots
	color_labels = compute_color_labels(df)

	if no_plot:
		return df, None, None

	try:
		indices = df['short_name']
	except:
		indices = df['name']


	if x_axis:
		xs = df[x_axis]
	else:
		xs = df[op_node_name]
	if y_axis:
		ys = df[y_axis]
	else:
		ys = df['C_max [GB/s]']
		
	mem_level=df['memlevel']
	today = datetime.date.today()
	if gui:
		outputfile=None
	else:
		outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, scale, today)	
	fig, textData = plot_data("{} : N = {}{}, \nvariant={}, scale={}".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))), variant, scale),
						outputfile, list(xs), list(ys),	list(indices), list(mem_level), scale, df, op_node_name, x_axis=x_axis, y_axis=y_axis, color_labels=color_labels, source_order=source_order, mappings=mappings)
	return df, fig, textData


def draw_contours(ax, maxx, ns):
	npoints=40

	ctx=np.linspace(0, maxx, npoints+1)
#	ctx=np.delete(ctx, 0) # Drop first element of 0

	lines=[]
	for n in ns:
		cty=n*ctx
		lines.append(ax.plot(ctx, cty, label='n={}'.format(n))[0])
	return lines

# Set filename to [] for GUI output	
def plot_data(title, filename, xs, ys, indices, memlevel, scale, df, op_node_name, x_axis=None, y_axis=None, color_labels=None, source_order=None, mappings=pd.DataFrame()):
	DATA =tuple(zip(xs,ys))
    
	fig, ax = plt.subplots()

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
	#ax.scatter(x, y, marker='o', c=df.color)
	# Draw contour lines
	ns = [1,2,4,8,16,32]
	ctxs = []
	ctxs = draw_contours(ax, xmax, ns)
	# Plot markers
	markers = []
	df.reset_index(drop=True, inplace=True)
	for i in range(len(x)):
		markers.extend(ax.plot(x[i], y[i], marker='o', color=df['color'][i][0], label=df['name'][i], linestyle='', alpha=1))
	
	# Point Labels
	plt.rcParams.update({'font.size': 7})
	mytext= [str('({0}, {1})'.format( indices[i], memlevel[i] ))  for i in range(len(DATA))]  
	texts = [plt.text(xs[i], ys[i], mytext[i], alpha=1) for i in range(len(DATA))]
	#adjust_text(texts, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
	ax.set(xlabel=x_axis if x_axis else 'C_FLOP [GFlop/s]', ylabel=y_axis if y_axis else 'C_max [GB/s]')
	ax.set_title(title, pad=40)
				
	# Legend
	patches = []
	if color_labels and len(color_labels) >= 2:
		for color_label in color_labels:
			patch = mpatches.Patch(label=color_label[0], color=color_label[1])
			patches.append(patch)
	patches.extend(ctxs)
	legend = ax.legend(loc="lower left", ncol=6, bbox_to_anchor=(0.,1.02,1.,.102),title="Label = (name, memlevel)", mode='expand', borderaxespad=0., \
		handles=patches)

	# Arrows between multiple runs
	name_mapping = dict()
	mymappings = []
	if not mappings.empty:
		for i in mappings.index:
			name_mapping[mappings['before_name'][i]] = []
			name_mapping[mappings['after_name'][i]] = []
		for index in mappings.index:
			before_row = df.loc[df['name']==mappings['before_name'][index]].reset_index(drop=True)
			after_row = df.loc[df['name']==mappings['after_name'][index]].reset_index(drop=True)
			if not before_row.empty and not after_row.empty:
				x_axis = x_axis if x_axis else op_node_name
				y_axis = y_axis if y_axis else 'C_max [GB/s]'
				xyA = (before_row[x_axis][0], before_row[y_axis][0])
				xyB = (after_row[x_axis][0], after_row[y_axis][0])
				# Check which way to curve the arrow to avoid going out of the axes
				if (xmax - xyB[0] > xyB[0] and xmax - xyA[0] > xyA[0] and xyA[1] < xyB[1]) or \
					(ymax - xyB[1] > xyB[1] and ymax - xyA[1] > xyA[1] and xyA[0] > xyB[0]) or \
					(ymax - xyB[1] < xyB[1] and ymax - xyA[1] < xyA[1] and xyA[0] < xyB[0]) or \
					(xmax - xyB[0] < xyB[0] and xmax - xyA[0] < xyA[0] and xyA[1] > xyB[1]):
					con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
						connectionstyle='arc3,rad=0.3', alpha=1)
				else:
					con = ConnectionPatch(xyA, xyB, 'data', 'data', arrowstyle="-|>", shrinkA=2.5, shrinkB=2.5, mutation_scale=13, fc="w", \
						connectionstyle='arc3,rad=-0.3', alpha=1)
				ax.add_artist(con)
				name_mapping[before_row['name'][0]].append(con)
				name_mapping[after_row['name'][0]].append(con)
				mymappings.append(con)
	plt.tight_layout()

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
		'names' : df['name'].values.tolist(),
		'marker:text' : dict(zip(markers,texts)),
		'marker:name' : dict(zip(markers,df['name'].values.tolist())),
		'name:marker' : dict(zip(df['name'].values.tolist(), markers)),
		'name:text' : dict(zip(df['name'].values.tolist(), texts)),
		'text:arrow' : {},
		'text:name' : dict(zip(texts, df['name'].values.tolist())),
		'name:mapping' : name_mapping,
		'mappings' : mymappings
	}

	#if filename:
		#plt.savefig(filename)

	return fig, plotData

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
