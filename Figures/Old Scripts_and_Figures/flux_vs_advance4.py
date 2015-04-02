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
            if ha[w]=='left':hoffset=0.015
            else:hoffset=-0.015 
            ax.annotate(name2,[x[i]+hoffset,y[i]+voffset],fontsize=fontsize, horizontalalignment=ha[w], verticalalignment=va[w])
    

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True,results=True)
d.fix_terminus()
d.remove_upper_extrap(remove_bottom=False)
d.normalize_elevation()

lm=0.11
bm=0.03
h=0.55
w=0.86
mb = 0.02
#
blue =N.array([45,80,150])/255.
thinning = [N.ma.mean(dz[0:3]) for dz in d.normdz]

fig = plt.figure(figsize=[4,7])
ax = fig.add_axes([lm,bm,w,h])
ax2 = fig.add_axes([lm,bm+h+mb,w,h-0.25])

#ax1 = fig.add_axes([lm+w+mb,bm,w,h])
#ax2 = fig.add_axes([lm+w*2+mb*2,bm,w,h])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

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

ax.scatter(d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float),s=50,c=colorVal)
ax.plot([0,0],[0,4],'-',color='gray',zorder=0,lw=1.3)
ax.set_xlabel("Length Change (km yr"+"$\mathregular{^{-1}})$")
ax.set_ylabel("Calving Flux (Gt yr"+"$\mathregular{^{-1}})$")
ax.yaxis.labelpad = 0
ax.xaxis.labelpad = 0
label_points(ax,d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float),d.name,labelthese = ['Hubbard','Columbia','LeConte','Yahtse'],va=['top','bottom','top','bottom'],ha=['right','left','right','right'],fontsize=12)
cax, kw = clbr.make_axes(ax,location='bottom',pad=0.13)

ax2 = fig.add_axes([lm,bm+h+mb,w,h-0.17])
ax2.scatter(d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float)/d.area*1e3,s=50,c=colorVal)
print N.c_[d.bm_length.astype(float)/(d.interval/365.)>0,d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float)/d.area*1e3]
ax2.plot([0,0],[0,4],'-',color='gray',zorder=0,lw=1.3)
#ax2.set_xlabel("Length Change (km yr"+"$\mathregular{^{-1}})$")
ax2.set_ylabel("Normalized Calving Flux (m w. eq. yr"+"$\mathregular{^{-1}})$")
ax2.yaxis.labelpad = 0
ax2.xaxis.labelpad = 0
label_points(ax2,d.bm_length.astype(float)/(d.interval/365.),d.eb_bm_flx.astype(float)/d.area*1e3,d.name,labelthese = ['Columbia','Yahtse','Northwestern','Sawyer'],va=['top','bottom','top','bottom'],ha=['left','left','right','right'],fontsize=12)



clr = clbr.Colorbar(cax,colorbarim1,orientation='horizontal',ticks=N.arange(-1,1.1,0.5)) 
clr.set_label('Mass Balance (m w. eq. year'+"$\mathregular{^{-1}})$")
#clr.ax.tick_params(labelsize=10)
#clr.ax.xaxis.set_ticks(N.arange(-1,1.1,0.5))

#for label in ax.yaxis.get_ticklabels():label.set_size(10)
#for label in ax.xaxis.get_ticklabels():label.set_size(10)


ax.yaxis.set_ticks(N.arange(0,5))
ax2.yaxis.set_ticks(N.arange(0,4))
ax.yaxis.set_ticklabels(N.arange(0,5))
ax2.yaxis.set_ticklabels(N.arange(0,4))
ax2.xaxis.set_ticklabels([])
ax.set_ylim([0,4])
ax2.set_ylim([0,4])



#ax2.xaxis.set_ticks(N.arange(ax2.get_xlim()[0],ax2.get_xlim()[1],1))


font = matplotlib.font_manager.FontProperties(family='Arial', weight='bold', size=15)
ax.annotate('A',[-0.9,0.2],horizontalalignment='center',verticalalignment='center',fontproperties=font)
ax2.annotate('B',[-0.9,0.2],horizontalalignment='center',verticalalignment='center',fontproperties=font)

w = N.where(d.bm_length.astype(float)/(d.interval/365.)>0)
w2 = N.where(d.bm_length.astype(float)/(d.interval/365.)<0)

advance = d.eb_bm_flx.astype(float)[w]#/d.area[w]*1e3
retreat = d.eb_bm_flx.astype(float)[w2]#/d.area[w2]*1e3
advance2 = d.eb_bm_flx.astype(float)[w]/d.area[w]*1e3
retreat2 = d.eb_bm_flx.astype(float)[w2]/d.area[w2]*1e3

advance = advance[N.where(N.invert(N.isnan(advance)))]
retreat = retreat[N.where(N.invert(N.isnan(retreat)))]
advance2 = advance2[N.where(N.invert(N.isnan(advance2)))]
retreat2 = retreat2[N.where(N.invert(N.isnan(retreat2)))]

t  = scipy.stats.mstats.ttest_ind(advance,retreat)
t2 = scipy.stats.mstats.ttest_ind(advance2,retreat2)
num1 = advance.shape[0]; num2 = retreat.shape[0];
df = ((np.var(advance)/num1 + np.var(retreat)/num2)**(2.0))/(   (np.var(advance)/num1)**(2.0)/(num1-1) +  (np.var(retreat)/num2)**(2.0)/(num2-1) ) 

ax.annotate("t(%3.1f)=%4.2f,p=%5.3f" % (df,t[0],t[1]),[-0.03,3.7], horizontalalignment='right', verticalalignment='center')
num1 = advance2.shape[0]; num2 = retreat2.shape[0];
df = ((np.var(advance)/num1 + np.var(retreat)/num2)**(2.0))/(   (np.var(advance)/num1)**(2.0)/(num1-1) +  (np.var(retreat)/num2)**(2.0)/(num2-1) ) 
ax2.annotate("t(%3.1f)=%4.2f,p=%5.3f" % (df,t2[0],t2[1]),[-0.03,3.7], horizontalalignment='right', verticalalignment='center')

plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/flux_vs_advance2.jpg",dpi=300)



#fig2 = plt.figure(figsize=[4,8])
#ax2 = fig.add_axes([0.1,0.1,0.8,0.8])
#
#ax2.plot(d.smb.astype(float), d.eb_bm_flx.astype(float),'o')
#
#plt.show()