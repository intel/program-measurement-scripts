import matplotlib.pyplot as plt 
from collections import OrderedDict
import numpy as np 
  
  
# Basic boxplot currently just plotting fixed data but could potentially extend for general usage.
# Creating dataset 
np.random.seed(10) 
#dataset=['SOA', 'SOAFU', 'SOAFUSPLIT', 'SOAFUSPLITFUME']
 
data_dict = OrderedDict([('SOA', np.array([24.85, 23.74, 24.36, 24.27, 24.56, 24.12, 24.15, 24.37, 24.15, 24.62])),
             ('SOAFU', np.array([23.17, 22.81, 23.32, 23.54, 22.81, 23.06, 23.04, 22.99, 23.16, 23.31])),
             ('SOAFUFUME', np.array([22.44, 22.44, 22.76, 22.87, 23.08, 22.91, 22.99, 22.99, 22.72, 22.65])),
             ('SOAFUSPLIT', np.array([23.35, 23.37, 23.69, 23.43, 23.45, 23.4, 23.17, 23.07, 23.17, 23.36])),
             ('SOAFUSPLITFUME', np.array([22.92, 23.1, 22.89, 23.01, 22.93, 22.95, 22.89, 22.83, 23.14, 22.86]))])
dataset = list(data_dict.keys())
data = [ data_dict[ds] for ds in dataset ]
  
fig = plt.figure(figsize =(10, 7)) 
  
# Creating axes instance 
ax = fig.add_axes([0.1, 0.1, .8, .8]) 

ax.set_xticklabels(dataset)

  
# Creating plot 
bp = ax.boxplot(data) 
plt.title('QMCPACK Profile time boxplot')
  
# show plot 
plt.show() 