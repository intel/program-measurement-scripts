#!/usr/bin/python3
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
from capelib import succinctify
from argparse import ArgumentParser

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text

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

def parse_ip(inputfile,outputfile, scale, title, chosen_node_set):
#	inputfile="/tmp/input.csv"
	df = pd.read_csv(inputfile)
	# Normalize the column names
	df.columns = succinctify(df.columns)


	grouped = df.groupby('variant')
	# Generate SI plot for each variant
	mask = df['variant'] == "ORIG"
	compute_and_plot('XFORM', df[~mask], outputfile, scale, title, chosen_node_set)
	compute_and_plot('ORIG', df[mask], outputfile, scale, title, chosen_node_set)
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
#	print(df['C_op'])



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


def compute_and_plot(variant, df,outputfile_prefix, scale, title, chosen_node_set):
	compute_capacity(df, chosen_node_set)
#	compute_saturation(df, chosen_node_set)
#	compute_intensity(df, chosen_node_set)
	df[['name', 'variant','C_L1', 'C_L2', 'C_L3', 'C_RAM', 'C_max', 'memlevel', 'C_op']].to_csv(variant+'_export_dataframe.csv', 
                                                                                                      index = False, header=True)
	

	indices = df['short_name']
	xs = df['C_op']
	ys = df['C_max']
	mem_level=df['memlevel']
	today = datetime.date.today()
	outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, scale, today)
	plot_data("{} : N = {}{}, \nvariant={}, scale={}".format(title, len(chosen_node_set), str(sorted(list(chosen_node_set))), variant, scale),
						outputfile, list(xs), list(ys),	list(indices), list(mem_level), scale)


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
def plot_data(title, filename, xs, ys, indices, memlevel, scale):
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
		plt.show()


def usage(reason):
	error_code = 0
	if reason:
		print ('\nERROR: {}!\n'.format(reason))
		error_code = 2
	print ('Usage:\n  generate_SI.py  -i <inputfile> -o <outputfile prefix> -n norm (row,matrix) -l <nodes> (optionally)>')
	print ('Example:\n  generate_SI.py  -i input.csv -o out.csv -n row -l L1,L2,L3,FLOP,SIMD')
	sys.exit(error_code)
	
def main(argv):
	if len(argv) != 8 and len(argv) != 6 and len(argv) != 4 and len(argv) != 2 and len(argv) != 1:
		usage('Wrong number of arguments')
	inputfile = []
	outputfile = []
	node_list = []
	scale = 'scalar'
	title=""
	chosen_node_set = DEFAULT_CHOSEN_NODE_SET
	try:
		opts, args = getopt.getopt(argv, "hi:o:s:l:")
		print (opts)
		print (args)
	except getopt.GetoptError:
		usage('Wrong argument opts(s)')
	if len(args) != 0:
		usage('Wrong argument(s)')		
	for opt, arg in opts:
		if opt == '-h':
			usage([])
		elif opt == '-s':
			normobj = arg
			print (normobj)
			if normobj != 'scalar' and normobj != 'loglog':
				print ('norm has to be either scalar or loglog')
			else:
				scale = normobj
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
		elif opt == '-o':
			outputfile.append(arg)
	if matchobj and len(outputfile) == 0:
		outputfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
	
	print ('Inputfile: ', inputfile[0])
	print ('Outputfile: ', outputfile[0])
	print ('Scale: ', scale)
	print ('Node List: ', node_list)
	parse_ip(inputfile[0],outputfile[0], scale, title.upper(), chosen_node_set)

if __name__ == "__main__":
	main(sys.argv[1:])