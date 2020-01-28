#!/usr/bin/env python3.6
import sys
import csv
import warnings
import numpy as np

import matplotlib.pyplot as plt
from adjustText import adjust_text

warnings.simplefilter("ignore")  # Ignore deprecation of withdash.



def draw_contours(ax, maxx, ns):
    npoints=40

    ctx=np.linspace(0, maxx, npoints+1)
    ctx=np.delete(ctx, 0) # Drop first element of 0

    lines=[]
    for n in ns:
        cty=n/ctx
        lines.append(ax.plot(ctx, cty, label='n={}'.format(n)))
    return lines
    
def plot_data(title, filename, xs, ys):
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

    xmax=max(xs)*2
    ymax=max(ys)*2  
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
    texts = [plt.text(xs[i], ys[i], text_strs[i], ha='center', va='center') for i in range(len(DATA))]
    #adjust_text(texts)
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))

    ax.set(title=title, xlabel=r'$I$', ylabel=r'$S$')
    ax.legend(loc="upper right")

    if filename:
        plt.savefig(filename)
    else:
        plt.show()

inputfile="/tmp/input.csv"
xs=[]
ys=[]
with open (inputfile, 'rU') as input_csvfile:
    csvreader = csv.DictReader(input_csvfile, delimiter=',')
    for input_row in csvreader:
        # print(input_row['x'], input_row['y'])
        xs.append(float(input_row['x']))
        ys.append(float(input_row['y']))
#xs=[1,2,3,4,5,2.5,3,3.5,3.75,3.77]
#ys=[3,4,1,2,5,2.5,2,2,2,2]

filename='/tmp/myfig.png' # Set to [] for GUI output
filename=[]
plot_data("Sample plot", filename, xs, ys)

