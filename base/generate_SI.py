#!/usr/bin/env python
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings
import datetime

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.


BASIC_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'SIMD', 'RAM'}
BUFFER_NODE_SET={'FrontEnd'}
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FrontEnd'}
# For L1, L2, L3, FLOP 4 node runs
#CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'SIMD'}
CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
	'L1': (lambda df : df['l1_rate']/8),
	'L2': (lambda df : df['l2_rate']/8),
	'L3': (lambda df : df['l3_rate']/8),
	'FLOP': (lambda df : df['gflops']),
	'SIMD': (lambda df : df['reg_simd_rate']/8),
	'RAM': (lambda df : df['ram_rate']/8),
	'FrontEnd': (lambda df : df['%frontend']*df['C_max'])	
	}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
b_capacity_formula= {
	'L1': (lambda df : df['l1_rate']/8),
	'L2': (lambda df : df['l2_rate']/8),
	'L3': (lambda df : df['l3_rate']/8),
	'FLOP': (lambda df : df['gflops']),
	'SIMD': (lambda df : df['reg_simd_rate']/8),
	'FrontEnd': (lambda df : df['%frontend']*df['C_max'])	
	}

def parse_ip(inputfile,outputfile, norm):
#	inputfile="/tmp/input.csv"
	df = pd.read_csv(inputfile)
	grouped = df.groupby('variant')
	# Generate SI plot for each variant
	mask = df['variant'] == "ORIG"
	compute_and_plot('XFORM', df[~mask], outputfile, norm)
	compute_and_plot('ORIG', df[mask], outputfile, norm)
	#for variant, group in grouped:
	#	compute_and_plot(variant, group, outputfile)

def compute_capacity(df, norm):
	print("The node list are as follows :")
	print(CHOSEN_NODE_SET)
	for node in BASIC_NODE_SET & CHOSEN_NODE_SET:
		print ("The current node : ", node)
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)
	if norm == 'row':
		print ("<=====Running Row Norm======>")
		df['C_max']=df[list(map(lambda n: "C_{}".format(n), BASIC_NODE_SET & CHOSEN_NODE_SET))].max(axis=1)
	else:
		print ("<=====Running Matrix Norm======>")
		df['C_max']=max(df[list(map(lambda n: "C_{}".format(n), BASIC_NODE_SET & CHOSEN_NODE_SET))].max(axis=1))
	print ("<=====compute_capacity======>")
	print(df['C_max'])
	print ("<=====compute_L1======>")
	print(df['C_L1'])

	for node in BUFFER_NODE_SET & CHOSEN_NODE_SET:
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)



def compute_saturation(df):
	nodeMax=df[list(map(lambda n: "C_{}".format(n), CHOSEN_NODE_SET))].max(axis=0)
	print ("<=====compute_saturation======>")
	print(nodeMax)
	for node in CHOSEN_NODE_SET:
		df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
	df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), CHOSEN_NODE_SET))].sum(axis=1)
	#df['Saturation'].to_csv('export_dataframe.csv', index = False, header=True)
	#df.to_csv(export_dataframe.csv', index=False)
	print(df['Saturation'])



def compute_intensity(df):
	node_cnt = len(CHOSEN_NODE_SET)
	csum=df[list(map(lambda n: "C_{}".format(n), CHOSEN_NODE_SET))].sum(axis=1)
	df['Intensity']=node_cnt*df['C_max'] / csum
	print(df['Intensity'])


def compute_and_plot(variant, df,outputfile_prefix, norm):
	compute_capacity(df, norm)
	compute_saturation(df)
	compute_intensity(df)
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
	speedups = df['C_FLOP'].round(decimals=2) # Currently set to the flop rate
	print (speedups)
	#plot_data("Saturation plot", 'saturation.png', x, y)
	#plot_data("Intensity plot", 'Intensity.png', x, z)
#	outputfile='SI.png'
	today = datetime.date.today()
	outputfile='{}-{}-{}-{}.png'.format(outputfile_prefix, variant, norm, today)
	plot_data("{} \n N = {}{}, \nvariant={}, norm={}".format(TITLE.upper(), len(CHOSEN_NODE_SET), str(CHOSEN_NODE_SET), variant, norm),
						outputfile, list(z), list(y),	list(indices), list(speedups))

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
def plot_data(title, filename, xs, ys, indices, speedups):
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

	mytext= [str('({0}, {1})'.format( indices[i], speedups[i] ))  for i in range(len(DATA))]    

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
	print ('Usage:\n  generate_SI.py  -i <inputfile> -o <outputfile prefix> -n norm (row,matrix)-l <nodes> (optionally)>')
	print ('Example:\n  generate_SI.py  -i input.csv -o out.csv -n row -l L1,L2,L3,FLOP,SIMD')
	sys.exit(error_code)
	
def main(argv):
	#if len(argv) != 6 and len(argv) != 4 and len(argv) != 2 and len(argv) != 1:
	#	usage('Wrong number of arguments')
	inputfile = []
	outputfile = []
	node_list = []
	norm = 'matrix'
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
			global CHOSEN_NODE_SET
			CHOSEN_NODE_SET = {node_list[i] for i in range(0, len(node_list))}
			print ({node_list[i] for i in range(0, len(node_list))})
			#CHOSEN_NODE_SET = node_list.split(',')
		elif opt == '-i':
			inputfile.append(arg)
			matchobj = re.search(r'(.+?)\.csv', arg)
			outputfile.append(str(matchobj.group(1)) + '_summary.csv')
			titleobj = str(matchobj.group(1))
			global TITLE
			TITLE = titleobj
			if not matchobj:
				print ('inputfile should be a *.csv file')
				sys.exit()
		elif opt == '-o':
			outputfile.append(arg)
	print ('Inputfile: ', inputfile[0])
	print ('Outputfile: ', outputfile[0])
	print ('Norm: ', norm)
	print ('Node List: ', node_list)
	parse_ip(inputfile[0],outputfile[0], norm)

if __name__ == "__main__":
	main(sys.argv[1:])
