#!/usr/bin/env python3.6
import sys, getopt
import csv
import re
import traceback
import pandas as pd
import numpy as np
import warnings

import matplotlib.pyplot as plt
from matplotlib import style
from adjustText import adjust_text

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.


BASIC_NODE_SET={'L1', 'L2', 'L3', 'FLOP'}
BUFFER_NODE_SET={'FrontEnd'}
CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP', 'FrontEnd'}
# For L1, L2, L3, FLOP 4 node runs
CHOSEN_NODE_SET={'L1', 'L2', 'L3', 'FLOP'}

# For node using derived metrics (e.g. FrontEnd), make sure the depended metrics are computed
capacity_formula= {
	'L1': (lambda df : df['l1_rate']),
	'L2': (lambda df : df['l2_rate']),
	'L3': (lambda df : df['l3_rate']),
	'FLOP': (lambda df : df['gflops']),
	'FrontEnd': (lambda df : df['%frontend']*df['C_max'])	
	}

def parse_ip(inputfile,outputfile):
#	inputfile="/tmp/input.csv"
	df = pd.read_csv(inputfile)
	grouped = df.groupby('variant')
	# Generate SI plot for each variant
	for variant, group in grouped:
		compute_and_plot(variant, group, outputfile)

def compute_capacity(df):
	for node in BASIC_NODE_SET & CHOSEN_NODE_SET:
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)
	df['C_max']=df[list(map(lambda n: "C_{}".format(n), BASIC_NODE_SET))].max(axis=1)

	for node in BUFFER_NODE_SET & CHOSEN_NODE_SET:
		formula=capacity_formula[node]
		df['C_{}'.format(node)]=formula(df)



def compute_saturation(df):
	nodeMax=df[list(map(lambda n: "C_{}".format(n), CHOSEN_NODE_SET))].max(axis=0)
	print(nodeMax)
	for node in CHOSEN_NODE_SET:
		df['RelSat_{}'.format(node)]=df['C_{}'.format(node)] / nodeMax['C_{}'.format(node)]
	df['Saturation']=df[list(map(lambda n: "RelSat_{}".format(n), CHOSEN_NODE_SET))].sum(axis=1)		


def compute_intensity(df):
	node_cnt = len(CHOSEN_NODE_SET)
	csum=df[list(map(lambda n: "C_{}".format(n), CHOSEN_NODE_SET))].sum(axis=1)
	df['Intensity']=node_cnt*df['C_max'] / csum


def compute_and_plot(variant, df,outputfile_prefix):
	print(df[['name', 'variant']])
	compute_capacity(df)
	compute_saturation(df)
	compute_intensity(df)
	
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
	#plot_data("Saturation plot", 'saturation.png', x, y)
	#plot_data("Intensity plot", 'Intensity.png', x, z)
#	outputfile='SI.png'
	outputfile='{}-{}.png'.format(outputfile_prefix, variant)
	plot_data("Interchange Transformed - Node Count = 4, variant={}".format(variant),
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

	ns = [1,2,4,8]

	ctxs = draw_contours(ax, xmax, ns)
	#     ctxLabels=list(map(lambda x: "n={}".format(x), ns))
	#     print(ctxLabels)
	text_strs=[str(DATA[i]) for i in range(len(DATA))]
	# print(text_strs)
	mytext= [str('{0}'.format( indices[i] ))  for i in range(len(DATA))]    
	#     for i in range(len(DATA)):
	#         (x, y) = DATA[i]
	#         (dd, dl, r, dr, dp) = dash_style[i]
	#         t = ax.text(x, y, str((x, y)), withdash=True,
	#                     dashdirection=dd,
	#                     dashlength=dl,
	#                     rotation=r,
	#                     dashrotation=dr,
	#                     dashpush=dp,
	#                     )
	texts = [plt.text(xs[i], ys[i], mytext[i], ha='center', va='center') for i in range(len(DATA))]
	#adjust_text(texts)
	adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

	ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
	ax.legend(loc="upper right")

	if filename:
		plt.savefig(filename)
	else:
		plt.show()


def usage(reason):
	error_code = 0
	if reason:
		print ('\nERROR: {}!\n'.format(reason))
		error_code = 2
	print ('Usage:\n  report_summary.py  -i <inputfile> (optionally) -o <outputfile prefix>')
	sys.exit(error_code)
	
def main(argv):
	if len(argv) != 4 and len(argv) != 2 and len(argv) != 1:
		usage('Wrong number of arguments')
	inputfile = []
	outputfile = []
	try:
		opts, args = getopt.getopt(argv, "hi:o:")
	except getopt.GetoptError:
		usage('Wrong argument(s)')
	if len(args) != 0:
		usage('Wrong argument(s)')		
	for opt, arg in opts:
		if opt == '-h':
			usage([])
		elif opt == '-i':
			inputfile.append(arg)
			matchobj = re.search(r'(.+?)\.csv', arg)
			if not matchobj:
				print ('inputfile should be a *.csv file')
				sys.exit()
			if matchobj and len(argv) == 2:
				outputfile.append(str(matchobj.group(1)) + '_summary.csv')
		elif opt == '-o':
			outputfile.append(arg)
	print ('Inputfile: ', inputfile[0])
	print ('Outputfile: ', outputfile[0])
	parse_ip(inputfile[0],outputfile[0])

if __name__ == "__main__":
	main(sys.argv[1:])
