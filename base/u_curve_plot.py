import matplotlib.pyplot as plt 
from capedata import SummaryData
from collections import OrderedDict
import numpy as np 
import pandas as pd
from metric_names import KEY_METRICS
from metric_names import MetricName as MN
from adjustText import adjust_text

# Set to False to plot S-curve
PLOT_U_CURVE = True
PLOT_U_CURVE = False

# Basic boxplot currently just plotting fixed data but could potentially extend for general usage.
# Creating dataset 
intelFile = "C:/Users/cwong29/Intel Corporation/Cape Project - Documents/Cape GUI Data/data_source/demo-may-2021/intel-la-set.raw.csv"
uiucFile = "C:/Users/cwong29/Intel Corporation/Cape Project - Documents/Cape GUI Data/data_source/demo-may-2021/la-all-full-3-w-matmul-orig.raw.csv"


intelDf = pd.DataFrame(columns = KEY_METRICS)
uiucDf = pd.DataFrame(columns = KEY_METRICS)
SummaryData(intelDf).set_sources([intelFile]).compute('intel-summary-Codelet')
SummaryData(uiucDf).set_sources([uiucFile]).compute('uiuc-summary-Codelet')
combinedDf = pd.merge(left=intelDf, right=uiucDf, on=[MN.NAME], suffixes=('_intel', '_uiuc'))
intelTime = combinedDf[MN.TIME_LOOP_S+'_intel']
uiucTime = combinedDf[MN.TIME_LOOP_S+'_uiuc']
combinedDf['speedup_uiuc_intel'] = intelTime/uiucTime
combinedDf['uspeedup_uiuc_intel'] = combinedDf['speedup_uiuc_intel']
rcpMask=combinedDf['uspeedup_uiuc_intel'] < 1
combinedDf.loc[rcpMask, 'uspeedup_uiuc_intel'] = 1 / combinedDf.loc[rcpMask, 'uspeedup_uiuc_intel'] 
combinedDf = combinedDf.sort_values(by='speedup_uiuc_intel', ascending=True, ignore_index=True)
# Compute rank s.t. speedup of 1 is exactly 0
combinedDf['SRank'] = range(len(combinedDf))
combinedDf['URank'] = combinedDf['SRank']
geMask = combinedDf['speedup_uiuc_intel'] >= 1
idx = combinedDf.loc[geMask, 'speedup_uiuc_intel'].idxmin()
geRank = combinedDf.loc[geMask, 'URank'][idx]

leMask = combinedDf['speedup_uiuc_intel'] <= 1
idx = combinedDf.loc[leMask, 'speedup_uiuc_intel'].idxmax()
leRank = combinedDf.loc[leMask, 'URank'][idx]

unitSpeedupRank = (leRank + geRank)/2
combinedDf['URank'] = combinedDf['URank'] - unitSpeedupRank

combinedDf[MN.NAME]=combinedDf[MN.NAME].str.replace('LinAlg: ','').str.replace('.c_de','').str.replace('-extern-assign-','-').str.replace('I1a','')


#plt.stem(combinedDf['URank'], combinedDf['uspeedup_uiuc_intel'])
if PLOT_U_CURVE:
    xname='URank'
    yname='uspeedup_uiuc_intel'
    title='UCurve (Comparing UIUC runs against Intel runs):\n Speedup of UIUC/Intel (Right) vs. Speedup of Intel/UIUC (Left)'
    ylim=1
else:
    xname='SRank'
    yname='speedup_uiuc_intel'
    title='SCurve (Comparing UIUC runs against Intel runs):\n Speedup of UIUC/Intel in rank order'
    ylim=0

fig = plt.figure(figsize =(10, 7)) 
  
# Creating axes instance 
ax = fig.add_axes([0.1, 0.1, .8, .8]) 

#plt.close('all')
#fig, ax = plt.subplots()
ax.plot(combinedDf[xname], combinedDf[yname], '.-', markersize=15)
texts = [ ax.text(combinedDf.iloc[i][xname], combinedDf.iloc[i][yname], combinedDf.iloc[i][MN.NAME], fontsize=10) \
    for i in range(len(combinedDf))]
#adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black'), force_text=(.2,.5), expand_text=(2,2))

# Only plot the verticle line for U Curve
if PLOT_U_CURVE: ax.axvline(x=0, lw=2, color='red')

median_speedup = combinedDf[yname].median()
ax.axhline(y=median_speedup, lw=2, color='red')
#plt.title(title)
ax.set_title(title)
ax.set_ylim(bottom=ylim)
#adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='black', alpha=0.5), expand_text=(3.8, 5.0))
adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='black', alpha=0.5))
plt.show() 