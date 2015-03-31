# -*- coding: utf-8 -*-
#import xlrd
import re
import unicodedata
import numpy as np
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
# from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from osgeo.gdalnumeric import *
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.mlab as mlab
import scipy.misc
import matplotlib
import matplotlib.colors as colors
import matplotlib.cm as cmx
import scipy.stats as stats
import scipy.stats.mstats as mstats
from numpy.ma import MaskedArray, masked, nomask
import numpy.ma as ma
import pickle

import ConfigParser

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

def plotthis(data):
    fig = plt.figure(figsize=[10,8])
    ax = fig.add_axes([0.11,0.31,0.74,0.6])
    for line in data.normdz:pl1 = ax.plot(data.norme, line,'r-',alpha=0.2)
    pl1 = ax.plot(data.norme, data.dzs_mean,'k-')
    pl2 = ax.plot(data.norme, data.dzs_mean-data.dzs_sem,'k--',data.norme, data.dzs_mean+data.dzs_sem,'k--')    
    plt.show()

    
plot_hist=False

user_where=["FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'","FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'","FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest' AND gltype.surge='f'","gltype.surge='f'"]
#user_where=["FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'","FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'","FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatWest' AND glnames.name!='YakutatEast' AND gltype.surge='f'"]
outroot = ["Tidewater","Lake","Land","All"]
color = ['k','g','r','r']
min_interval=5
intervalsmax=30
labels = ['<=3yr intervals','3-5 yrs','5-10yrs','>=10yrs','>=3yrs','>=5yrs','Before 2003','After 2002']
shpfiles = ['intervals_less3yr','intervals_3_5yrs','intervals5_10yrs','intervals_more10yrs','intervals_more3yrs','intervals_more5yrs','Before2003','After2002']
div1 = '2000-01-01'
i=0

surveyeddata = GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True)
surveyeddata.fix_terminus()
#surveyeddata.remove_upper_extrap()
surveyeddata.normalize_elevation()
surveyeddata.calc_dz_stats()
#surveyeddata.extend_upper_extrap()

types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]

regs = ["('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","('Alaska Range','Wrangell Mountains','Brooks Range')"]
 
lamb = [] 
userwheres=[]
for typ in types:
    for reg in regs:
        if not (reg=="('Alaska Range','Wrangell Mountains','Brooks Range')" and typ=="ergi.gltype=1"):

            userwheres.append("%s AND region IN %s" % (typ,reg))
            lamb.append(GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, results=True, userwhere="%s AND ergi.region IN %s" % (typ,reg)))
            lamb[-1].fix_terminus()
            lamb[-1].remove_upper_extrap()
            lamb[-1].normalize_elevation()
            lamb[-1].calc_dz_stats()
            lamb[-1].extend_upper_extrap()

fig = plt.figure(figsize=[3,6])
ax = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)

userwheres

clrs = N.array([[102,194,165],[252,141,98],[141,160,203]])/255.

labels = ['Southeast','South-Central','Interior']
handles=[]
for clr,lb in zip(clrs,lamb[0:3]):
    handles.append(ax.plot(lb.norme,lb.dzs_mean,color=clr,lw=1.5))
    ax.fill_between(lb.norme,lb.dzs_mean+lb.dzs_std,lb.dzs_mean-lb.dzs_std,color=clr,alpha=0.3,lw=0.01,label=labels[i])
    
for clr,lb in zip(clrs,lamb[5:]):
    ax2.plot(lb.norme,lb.dzs_mean,color=clr,lw=1.5)
    ax2.fill_between(lb.norme,lb.dzs_mean+lb.dzs_std,lb.dzs_mean-lb.dzs_std,color=clr,alpha=0.3,lw=0.01)


for clr,lb in zip(clrs[0:2],lamb[3:5]):
    ax3.plot(lb.norme,lb.dzs_mean,color=clr,lw=1.5)
    ax3.fill_between(lb.norme,lb.dzs_mean+lb.dzs_std,lb.dzs_mean-lb.dzs_std,color=clr,alpha=0.3,lw=0.01)

plt.rc("font", **{"sans-serif": ["Arial"],"size": 13})

axes = [ax,ax2,ax3]

for aborc,axi in zip(['A','B','C'],axes):
    for tick in axi.yaxis.get_major_ticks():tick.label.set_fontsize(10) 
    axi.annotate(aborc,xy=[0,1],xytext=[5,-5],xycoords='axes fraction',fontsize=13,ha='left',va='top',textcoords='offset points',fontweight='bold')
for tick in ax3.yaxis.get_major_ticks():tick.label.set_fontsize(10)
for tick in ax3.xaxis.get_major_ticks():tick.label.set_fontsize(10)
ax.get_xaxis().set_ticklabels([])
ax.get_yaxis().set_ticks([-6,-4,-2,0])
ax2.get_yaxis().set_ticks([-6,-4,-2,0])

ax2.get_xaxis().set_ticklabels([])
ax.set_ylim([-7,1.5])
ax2.set_ylim([-7,1.5])
ax3.set_ylim([-12,12])
ax.set_ylabel("Elevation Change (m yr"+"$\mathregular{^{-1})}$", fontsize=11,labelpad=-2)
ax3.set_xlabel('Normalized Elevation', fontsize=11)

N.repeat(N.array(ax.get_ylim()),2)
ax3.fill_between([0,1],N.repeat(N.array(ax.get_ylim()),2)[:2],N.repeat(N.array(ax.get_ylim()),2)[2:],color='0.5',alpha=0.15,lw=0.01,zorder=0)
handles = [h[0] for h in handles]
    
ax.legend(handles,labels,fontsize=10,loc=4)
#ext = extrapolate3(lamb,userwheres,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True)#,export_shp='/Users/igswahwsmcevan/Altimetry/results/%s_no_yak.shp' % shpfiles[5])

plt.subplots_adjust(left=0.16, bottom=0.085, right=0.95, top=0.98, wspace=None, hspace=0.02)
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/dhdtprofiles_regional.jpg",dpi=500)
