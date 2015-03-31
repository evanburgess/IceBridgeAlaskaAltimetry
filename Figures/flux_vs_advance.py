import psycopg2
import xlrd
import re
import unicodedata
import numpy as N
from time import mktime
from datetime import datetime
from time import mktime
import time
import os
import glob
import simplekml as kml
import subprocess
import datetime as dtm
from types import *
import sys
import ppygis
import StringIO
import shapefile
from osgeo import osr
from pylab import *
import matplotlib as plt

import ConfigParser
from glob import glob

def label_points(ax,x,y,text,miny=3,fontsize=9):
    for i,name in enumerate(text):
        if y[i]>miny:
            name2 = re.sub(" Glacier", "",name)
            
            if (x[i]-ax.get_xlim()[0])/(ax.get_xlim()[1]-ax.get_xlim()[0])<0.1:align='left'
            else:align='right'
            
            print name,(y[i]-ax.get_ylim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])
            if (y[i]-ax.get_ylim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])>0.95:align2='top'
            else:align2='bottom'
            
            ax.annotate(name2,[x[i],y[i]],fontsize=fontsize, horizontalalignment=align, verticalalignment=align2)
    

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True,results=True)
d.fix_terminus()
d.remove_upper_extrap(remove_bottom=False)
d.normalize_elevation()

lm=0.17
bm=0.07
h=0.24
w=0.8
mb = 0.09

blue =N.array([45,80,150])/255.
fig = plt.figure(figsize=[4,8])
ax = fig.add_axes([lm,bm+h*2+mb*2,w,h])
ax1 = fig.add_axes([lm,bm+h+mb,w,h])
ax2 = fig.add_axes([lm,bm,w,h])


ax.plot(d.bm_length.astype(float),d.eb_bm_flx.astype(float),'o',color=blue)
ax.set_xlabel("Length Change (km)",fontsize=11)
ax.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
label_points(ax,d.bm_length.astype(float),d.eb_bm_flx.astype(float),d.name,miny=0.8)

thinning = [N.ma.mean(dz[0:3]) for dz in d.normdz]
ax1.plot(thinning,d.eb_bm_flx.astype(float),'o',color=blue)
ax1.set_xlabel("Terminus Elevation Change (m yr"+"$^{-1}$"+")",fontsize=11)
ax1.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
label_points(ax1,thinning,d.eb_bm_flx.astype(float),d.name,miny=0.8)

ax2.plot(d.rlt_totalkgm2,d.eb_bm_flx.astype(float),'o',color=blue)
ax2.set_xlabel("Mass Balance (m w. eq. yr"+"$^{-1}$"+")",fontsize=11)
ax2.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
label_points(ax2,d.rlt_totalkgm2,d.eb_bm_flx.astype(float),d.name,miny=0.8)
    #for i,name in enumerate(d.name):
    #if d.eb_bm_flx.astype(float)[i]>0.8:
    #    name2 = re.sub(" Glacier", "",name)
    #    if d.rlt_totalkgm2[i]<-3:align='left'
    #    else:align='right'
    #    
    #    if d.eb_bm_flx.astype(float)[i]>3:align2='bottom'
    #    else:align2='top'
    #    
    #    ax2.annotate(name2,[d.rlt_totalkgm2[i],d.eb_bm_flx.astype(float)[i]],fontsize=8, horizontalalignment=align, verticalalignment=align2)
    
ax.text(0.05, 0.05, "A.", transform=ax.transAxes,fontsize=13, fontweight='bold', va='bottom')
ax1.text(0.05, 0.05, "B.", transform=ax1.transAxes,fontsize=13, fontweight='bold', va='bottom')
ax2.text(0.05, 0.05, "C.", transform=ax2.transAxes,fontsize=13, fontweight='bold', va='bottom')

ax2.xaxis.set_ticks(N.arange(ax2.get_xlim()[0],ax2.get_xlim()[1],1))

plt.show()

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/flux_vs_advance.jpg",dpi=300)


#fig2 = plt.figure(figsize=[4,8])
#ax2 = fig.add_axes([0.1,0.1,0.8,0.8])
#
#ax2.plot(d.smb.astype(float), d.eb_bm_flx.astype(float),'o')
#
#plt.show()