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
import matplotlib.colors as colors
import matplotlib.cm as cmx

import ConfigParser
from glob import glob

def label_points(ax,x,y,text,miny=3,fontsize=9,labelthese = None,va=None,ha=None):
    for i,name in enumerate(text):
        if re.sub(" Glacier", "",name) in labelthese:
            name2 = re.sub(" Glacier", "",name)
            
            w=N.where(N.array(labelthese)==re.sub(" Glacier", "",name))[0]
            if va[w]=='top':voffset=-0.05
            else:voffset=0.05 
            if ha[w]=='left':hoffset=0.05
            else:hoffset=-0.05 
            ax.annotate(name2,[x[i]+hoffset,y[i]+voffset],fontsize=fontsize, horizontalalignment=ha[w], verticalalignment=va[w])
    

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True,results=True)
d.fix_terminus()
d.remove_upper_extrap(remove_bottom=False)
d.normalize_elevation()

lm=0.05
bm=0.03
h=0.95
w=0.45
mb = 0.02






blue =N.array([45,80,150])/255.
thinning = [N.ma.mean(dz[0:3]) for dz in d.normdz]

fig = plt.figure(figsize=[7,4])
ax = fig.add_axes([lm,bm,w,h])
ax1 = fig.add_axes([lm+w+mb,bm,w,h])
#ax2 = fig.add_axes([lm+w*2+mb*2,bm,w,h])

#ax = fig.add_axes([lm,bm+h*2+mb*2,w,h])
#ax1 = fig.add_axes([lm,bm+h+mb,w,h])
#ax2 = fig.add_axes([lm,bm,w,h])
colorbar = 'RdBu'
jet = cm = plt.get_cmap(colorbar) 
cNorm  = colors.Normalize(vmin=-1, vmax=1)
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
cNorm1  = colors.Normalize(vmin=-25, vmax=20)
scalarMap1 = cmx.ScalarMappable(norm=cNorm1, cmap=jet)

colorVal = scalarMap.to_rgba(d.rlt_totalkgm2)
colorVal1 = scalarMap1.to_rgba(thinning)

#CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
#fig = plt.figure(figsize=[15,10])
#ax = fig.add_axes(position)
colorbarim1 = ax.imshow([d.rlt_totalkgm2],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=-1,vmax=1)
colorbarim2 = ax.imshow([thinning],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=-20,vmax=20)
plt.clf()

ax = fig.add_axes([lm,bm,w,h])
ax.scatter(d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float),s=20,c=colorVal)
ax.set_xlabel("Length Change (km yr"+"$^{-1}$"+")",fontsize=10)
ax.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=10)
ax.yaxis.labelpad = 0
label_points(ax,d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float),d.name,labelthese = ['Hubbard','Columbia','LeConte','Yahtse'],va=['top','bottom','top','bottom'],ha=['right','left','right','right'])
cax, kw = clbr.make_axes(ax,location='bottom',pad=0.2)

clr = clbr.Colorbar(cax,colorbarim1,orientation='horizontal') 
clr.set_label('Mass Balance (m w. eq. year'+"$^{-1}$"+')',size = 10)
clr.ax.tick_params(labelsize=10)

ax1 = fig.add_axes([lm+w+mb,bm,w,h])
ax1.scatter(d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float),s=20,c=colorVal1)
#ax1.scatter(thinning,d.eb_bm_flx.astype(float),,color=blue)
ax1.set_xlabel("Terminus Elevation Change\n(m yr"+"$^{-1}$"+")",fontsize=10)
#ax1.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=10)
label_points(ax1,thinning,d.eb_bm_flx.astype(float),d.name,labelthese = ['Hubbard','Columbia','LeConte','Yahtse'],va=['top','bottom','top','bottom'],ha=['right','left','right','right'])

cax1, kw1 = clbr.make_axes(ax1,location='bottom',pad=0.2)

clr1 = clbr.Colorbar(cax1,colorbarim1,orientation='horizontal') 
clr1.set_label('Mass Balance (m w. eq. year'+"$^{-1}$"+')',size = 10)
clr1.ax.tick_params(labelsize=10)

plt.show()
raise

#ax2.plot(d.rlt_totalkgm2,d.eb_bm_flx.astype(float),'o',color=blue)
#ax2.set_xlabel("Mass Balance \n(m w. eq. yr"+"$^{-1}$"+")",fontsize=10)
##ax2.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=10)
#label_points(ax2,d.rlt_totalkgm2,d.eb_bm_flx.astype(float),d.name,labelthese = ['Hubbard','Columbia','LeConte','Yahtse'],va=['top','bottom','top','bottom'],ha=['right','left','right','right'])
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
    
ax.text(0.05, 0.04, "A.", transform=ax.transAxes,fontsize=13, fontweight='bold', va='bottom')
ax1.text(0.05, 0.04, "B.", transform=ax1.transAxes,fontsize=13, fontweight='bold', va='bottom')
#ax2.text(0.05, 0.04, "C.", transform=ax2.transAxes,fontsize=13, fontweight='bold', va='bottom')


ax1.yaxis.set_tick_params(labelleft='off')
#ax2.yaxis.set_tick_params(labelright='on')
#ax2.yaxis.set_tick_params(labelleft='off')

for label in ax.yaxis.get_ticklabels():label.set_size(10)
#for label in ax1.yaxis.get_ticklabels():label.set_size(10)
#for label in ax2.yaxis.get_ticklabels():label.set_size(10)

for label in ax.xaxis.get_ticklabels():label.set_size(10)
for label in ax1.xaxis.get_ticklabels():label.set_size(10)
#for label in ax2.xaxis.get_ticklabels():label.set_size(10)

ax.yaxis.set_ticks(N.arange(0,5))
ax1.yaxis.set_ticks(N.arange(0,5))
ax.yaxis.set_ticklabels(N.arange(0,5))
ax.set_ylim([0,4])
ax1.set_ylim([0,4])


#ax2.xaxis.set_ticks(N.arange(ax2.get_xlim()[0],ax2.get_xlim()[1],1))

plt.show()

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/flux_vs_advance.jpg",dpi=300)


#fig2 = plt.figure(figsize=[4,8])
#ax2 = fig.add_axes([0.1,0.1,0.8,0.8])
#
#ax2.plot(d.smb.astype(float), d.eb_bm_flx.astype(float),'o')
#
#plt.show()