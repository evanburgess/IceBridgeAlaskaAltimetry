import xlrd
import re
import unicodedata
import numpy as N
import datetime as dtm
import os
import glob
import simplekml as kml
import subprocess
import matplotlib.pyplot as plt
from osgeo import gdal
from types import *
import sys
import time
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from osgeo.gdalnumeric import *
sys.path.append('/Users/igswahwsmcevan/Altimetry/code/')
#from Altimetry import timeout
from Altimetry.Interface import *
from Altimetry.Analytics import *
from Altimetry.UpdateDb import * 
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import scipy.misc
import matplotlib
import matplotlib.colors as colors
import matplotlib.cm as cmx
import types

 

names=["Baird Glacier","Field Glacier","Gillam Glacier","Kaskawulsh Glacier"]
year1s=[2001,2007,2000,1995]
year2s=[2010,2011,2010,2000]
letter=["A","B","C","D"]
#Field Glacier.2007.2011
#Gillam Glacier.2000.2010
#Kaskawulsh Glacier.1995.2000

lm=0.15
bm=0.07
h=0.213
w=0.79
mb = 0.02

fig = plt.figure(figsize=[4,8])
ax4 = fig.add_axes([lm,bm,w,h])
ax3 = fig.add_axes([lm,bm+h+mb,w,h])
ax2 = fig.add_axes([lm,bm+h*2+mb*2,w,h])
ax1 = fig.add_axes([lm,bm+h*3+mb*3,w,h])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

axes=[ax1,ax2,ax3,ax4]
for i,ax in enumerate(axes):
   
    data = GetLambData(removerepeats=False,verbose=True,by_column=False,as_object=True,userwhere="ergi.name='%s' AND extract(year from date1)=%s AND extract(year from date2)=%s" % (names[i],year1s[i],year2s[i]))[0]
    
    data.convert085()
    data.remove_upper_extrap(remove_bottom=True)
    data.normalize_elevation()
    
    nm = re.findall("^(.*) Glacier",data.name)[0]
    zdzfile =  "/Users/igswahwsmcevan/Altimetry/zdzfiles/%s.%s.%s.raw.zdz.txt" % (nm,data.date1.year,data.date2.year)
    #title = "%s  %s -- %s" % (nm,data.date1.isoformat(),data.date2.isoformat())

    try:
        x,y = N.loadtxt(zdzfile,skiprows=1,unpack=True)
        skip=False
    except:
        print 'failed'
        skip=True
    
    y*=0.85
    if not skip:ax.plot((x - data.min)/(data.max-data.min),y,'o',alpha=0.04,color=[0.7,0.7,0.7])    #PLOTTING POINTS 
    ax.plot(data.norme,data.normdz,'r',linewidth=1.5,zorder=3) #PLOTTING LINES

    deriv = data.fix_terminus()
    data.remove_upper_extrap()
    data.normalize_elevation()

    #ax.plot(data.norme,data.norm25,'b-',data.norme,data.norm75,'b-')
    ax.plot(data.norme,data.normdz,color=[0,1,51/255.],linewidth=1.5,zorder=2)
    #ax.plot([0,1],[0,0],'k')
    ax.set_xlim([0,0.5])
    ax.set_ylim([-7,2])

    if i==3:ax.set_xlabel("Normalized Elevation (m)")
    if i!=3:ax.xaxis.set_tick_params(labelbottom='off')
    ax.annotate(letter[i],[0.02,1],fontsize=12, fontweight='bold')


plt.figtext(0.01,0.52,"Elevation Change (m w. eq. yr"+"$\mathregular{^{-1})}$",rotation='vertical',verticalalignment='center',horizontalalignment='left')
plt.show()


fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/terminus_fix.jpg",dpi=300)


    