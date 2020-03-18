#!/usr/bin/env python3.6
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime
from capelib import succinctify

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.


BASIC_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'SIMD', 'RAM'}
BUFFER_NODE_SET={'FrontEnd'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FrontEnd'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'SIMD'}
DEFAULT_CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP'}

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

def parse_ip(inputfile,outputfile, norm, title, chosen_node_set):
#	inputfile="/tmp/input.csv"
	df = pd.read_csv(inputfile)
	# Normalize the column names
	df.columns = succinctify(df.columns)
	grouped = df.groupby('variant')
	# Generate SI plot for each variant
	mask = df['variant'] == "ORIG"
	compute_and_plot('XFORM', df[~mask], outputfile, norm, title, chosen_node_set)
	compute_and_plot('ORIG', df[mask], outputfile, norm, title, chosen_node_set)
	#for variant, group in grouped:
	#	compute_and_plot(variant, group, outputfile)

def compute_capacity(df, norm, chosen_node_set):
	print("The node list are as follows :")
	print(chosen_node_set)
	chosen_basic_node_set = BASIC_NODE_SET & chosen_node_set
	for node in chosen_basic_node_set:
		print ("The current node : ", node)
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)
	if norm == 'row':
		print ("<=====Running Row Norm======>")
		df['C_max']=df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1)
	else:
		print ("<=====Running Matrix Norm======>")
		df['C_max']=max(df[list(map(lambda n: "C_{}".format(n), chosen_basic_node_set))].max(axis=1))
	print ("<=====compute_capacity======>")
	print(df['C_max'])
	print ("<=====compute_L1======>")
	print(df['C_L1'])

	for node in BUFFER_NODE_SET & chosen_node_set:
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)



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


def compute_and_plot(variant, df,outputfile_prefix, norm, title, chosen_node_set):
	compute_capacity(df, norm, chosen_node_set)
	compute_saturation(df, chosen_node_set)
	compute_intensity(df, chosen_node_set)
	df[['name', 'variant','Saturation', 'Intensity']].to_csv(variant+'_export_dataframe.csv', index = False, header=True)
	
# 	xs=[]
# 	ys=[]
# 	with open (inputfile, 'rU') as input_csvfile:
# 		csvreader = csv.DictReader(input_csvfile, delimiter=',')
# 		for input_row in csvreader:
# 			# print(input_row['x'], input_row['y'])
# 			xs.append(float(input_row['x']))
# 			ys.append(float(input_row['y']))

# #xs=[1,2,3,4,5,2.5,3,3.5,3.75,3.77]
# #ys=[3,4,1,2,5,2.5,2,2,2,2]

# 		filename=[]
# 		plot_data("Sample plot", filename, xs, ys)




#	headers = ['Index', 'Saturation','Intensity','SI', 'Speedup']

	indices = df['short_name']
	y = df['Saturation']
	z = df['Intensity']
	df['SI']=df['Saturation'] * df['Intensity'] 
	k = df['SI']
	df['Speedup']=1.0  # TODO: should update script to pick a base list as 'before' to compute speedup
	speedups = df['Speedup']
	floprate = df['C_FLOP']
	print (speedups)
	#plot_data("Saturation plot", 'saturation.png', x, y)
	#plot_data("Intensity plot", 'Intensity.png', x, z)
#	outputfile='SI.png'
	today = datetime.date.today()
	outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
	plot_data("{} \n N = {}{}, \nvariant={}, norm={}".format(title, len(chosen_node_set), 
						str(sorted(list(chosen_node_set))), variant, norm),
						outputfile, list(z), list(y),	list(indices), list(speedups), list(floprate))

	#plt.plot(x,y, label='Saturation !')
	#plt.title('Saturation Chart')
	#plt.ylabel ('Y axis')
	#plt.xlabel('X axis')
	#plt.legend()
	#plt.show()

def draw_contours(ax, maxx, ns):
	npoints=40

	ctx=np.linspace(0, maxx, npoints+1)
	ctx=np.delete(ctx, 0) # Drop first element of 0

	lines=[]
	for n in ns:
		cty=n/ctx
		lines.append(ax.plot(ctx, cty, label='n={}'.format(n)))
	return lines

# Set filename to [] for GUI output	
def plot_data(title, filename, xs, ys, indices, speedups, floprates):
	DATA =tuple(zip(xs,ys))
	#     DATA = ((1, 3),
	#             (2, 4),
	#             (3, 1),
	#             (4, 2))
	# dash_style =
	#     direction, length, (text)rotation, dashrotation, push
	# (The parameters are varied to show their effects, not for visual appeal).
	#     dash_style = (
	#         (0, 20, -15, 30, 10),
	#         (1, 30, 0, 15, 10),
	#         (0, 40, 15, 15, 10),
	#         (0, 40, 15, 15, 10),
	#         (0, 40, 15, 15, 10),
	#         (1, 20, 30, 60, 10))
    
	fig, ax = plt.subplots()

	#xmax=max(xs)*2
	xmax=max(xs)*1.2
	ymax=max(ys)*1.2  
	ax.set_xlim((0, xmax))
	ax.set_ylim((0, ymax))
    
	(x, y) = zip(*DATA)
	ax.scatter(x, y, marker='o')

	ns = [1,2,3,4,8]

	ctxs = draw_contours(ax, xmax, ns)

	mytext= [str('({0}, {1:.2f})'.format( indices[i], floprates[i] ))  for i in range(len(DATA))]    

	texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
	#adjust_text(texts)
	adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

	ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
	ax.legend(loc="lower left",title="(name,flops)")

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
	norm = 'matrix'
	title=""
	chosen_node_set = DEFAULT_CHOSEN_NODE_SET
	try:
		opts, args = getopt.getopt(argv, "hi:o:n:l:")
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
		elif opt == '-o':
			outputfile.append(arg)
	if matchobj and len(outputfile) == 0:
		outputfile.append(str(matchobj.group(1))) # Use input file basename as output prefix if user did not provide info
	print ('Inputfile: ', inputfile[0])
	print ('Outputfile: ', outputfile[0])
	print ('Norm: ', norm)
	print ('Node List: ', node_list)
	parse_ip(inputfile[0],outputfile[0], norm, title.upper(), chosen_node_set)

if __name__ == "__main__":
	main(sys.argv[1:])
