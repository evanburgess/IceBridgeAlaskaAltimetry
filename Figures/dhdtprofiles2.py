# -*- coding: utf-8 -*-
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
color = N.array([[0,0,0],[163,100,57],[45,80,150],[75,150,38]])/255.
min_intervals=N.array([0,3,5,10,3,5])
intervalsmax=N.array([3,5,10,30,30,30])
labels = ['<=3yr intervals','3-5 yrs','5-10yrs','>=10yrs','>=3yrs','>=5yrs','Before 2003','After 2002']
shpfiles = ['intervals_less3yr','intervals_3_5yrs','intervals5_10yrs','intervals_more10yrs','intervals_more3yrs','intervals_more5yrs','Before2003','After2002']
div1 = '2000-01-01'
i=0

startfromscratch=True


if startfromscratch:    

    surveyeddata = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True)  # 
    #surveyeddata.fix_terminus()
    #surveyeddata.remove_upper_extrap()
    surveyeddata.normalize_elevation()
    surveyeddata.calc_dz_stats()
    #surveyeddata.extend_upper_extrap()

    land = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'") 
    land.fix_terminus()
    land.remove_upper_extrap(remove_bottom=False)
    land.normalize_elevation()
    land.calc_dz_stats(too_few=4)
    land.extend_upper_extrap()
    
    tide = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'",results=True) 
    tide.fix_terminus()
    tide.remove_upper_extrap(remove_bottom=False)
    tide.normalize_elevation()
    tide.calc_dz_stats(too_few=4)
    tide.extend_upper_extrap()

    lake = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest' AND gltype.surge='f'") 
    lake.fix_terminus()
    lake.remove_upper_extrap(remove_bottom=False)
    lake.normalize_elevation()
    lake.calc_dz_stats(too_few=4)
    lake.extend_upper_extrap()


    #ext = extrapolate2([land,tide,lake],insert_surveyed_data=surveyeddata,keep_postgres_tbls=True,export_shp='/Users/igswahwsmcevan/Altimetry/results/intervals_more5yrs_no_yak.shp')
#raise    

#    pickle.dump(ext, open( "/Users/igswahwsmcevan/Papers/AK_altimetry/finalresults.p", "wb" ))
#else:ext = pickle.load(open( "/Users/igswahwsmcevan/Papers/AK_altimetry/finalresults.p", "rb" ))


columbia = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Columbia'") 
columbia.fix_terminus()
columbia.remove_upper_extrap(remove_bottom=False)
columbia.normalize_elevation()

hubbard = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Hubbard'") 
hubbard.fix_terminus()
hubbard.remove_upper_extrap(remove_bottom=False)
hubbard.normalize_elevation()

wolverine = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Wolverine'") 
wolverine.fix_terminus()
wolverine.remove_upper_extrap(remove_bottom=False)
wolverine.normalize_elevation()

gulkana = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Gulkana'") 
gulkana.fix_terminus()
gulkana.remove_upper_extrap(remove_bottom=False)
gulkana.normalize_elevation()

#GLACIERS THAT ARE THICKENING AT THE TERMINUS AND THINNING UP HIGH
switch = N.logical_and(N.array([N.mean(dz[:20]) for dz in tide.normdz])>0,N.array([N.mean(dz[40:80]) for dz in tide.normdz])<0)


samples_lim=None
err_lim=None
title=None
alphafill = 0.2

fig = plt.figure(figsize=[4,6])
ax = fig.add_axes([0.15,0.545,0.8,0.43])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 13})
#ax.set_title('Surface Elevation Change: %s Glaciers' % outroot[i])

ax.set_ylabel("Elevation Change (m yr"+"$\mathregular{^{-1})}$", fontsize=11,labelpad=3)
#ax.set_xlabel('Normalized Elevation', fontsize=11)
ax.set_ylim([-6,1])
ax.set_xlim([0,1])
for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(10) 

ax.plot(land.norme,land.dzs_mean,'-',color=N.array([163,100,57])/255.,linewidth=2.5,label='Mean')
ax.plot(land.norme,land.dzs_mean-land.dzs_sem,'-',land.norme,land.dzs_mean+land.dzs_sem,'-',color=N.array([163,100,57])/255.,linewidth=1)
ax.fill_between(land.norme,land.dzs_mean+land.dzs_std,land.dzs_mean-land.dzs_std,alpha=alphafill,color= N.array([163,100,57])/255.,lw=0)

ax.plot(lake.norme,lake.dzs_mean,'-',color='green',linewidth=2.5,label='Mean')
ax.plot(lake.norme,lake.dzs_mean-lake.dzs_sem,'-',lake.norme,lake.dzs_mean+lake.dzs_sem,'-',color='green',linewidth=1)
ax.fill_between(lake.norme,lake.dzs_mean+lake.dzs_std,lake.dzs_mean-lake.dzs_std,alpha=alphafill,color= 'green',lw=0)

font = matplotlib.font_manager.FontProperties(family='Arial', weight='bold', size=15)
ax.annotate('A',[0.07,0.5],horizontalalignment='center',verticalalignment='center',fontproperties=font)

for dz in land.normdz:ax.plot(land.norme,dz,'-k',linewidth=0.4,alpha=0.2)
for dz in lake.normdz:ax.plot(lake.norme,dz,'-k',linewidth=0.4,alpha=0.2)

ax2 = fig.add_axes([0.15,0.07,0.8,0.43])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 13})

ax2.set_ylabel("Elevation Change (m yr"+"$\mathregular{^{-1})}$", fontsize=11,labelpad=-2)
ax2.set_xlabel('Normalized Elevation', fontsize=11)
ax2.set_ylim([-10,12])
ax2.set_xlim([0,1])
for tick in ax2.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
for tick in ax2.yaxis.get_major_ticks():tick.label.set_fontsize(10) 

ax2.plot(tide.norme,tide.dzs_mean,'-',color='blue',linewidth=2,label='Mean')
ax2.plot(tide.norme,tide.dzs_mean-tide.dzs_sem,'-',tide.norme,tide.dzs_mean+tide.dzs_sem,'-',color='blue',linewidth=0.7)
ax2.fill_between(tide.norme,tide.dzs_mean+tide.dzs_std,tide.dzs_mean-tide.dzs_std,alpha=alphafill,color= 'blue',lw=0)

for j,dz in enumerate(tide.normdz):
    if switch[j]: ax2.plot(tide.norme,dz,'-k',linewidth=0.5,alpha=0.3)   # can make these a separate color
    else: ax2.plot(tide.norme,dz,'-k',linewidth=0.5,alpha=0.3)
    
ax2.plot(columbia.norme,columbia.normdz[0],'--k',linewidth=1.,alpha=0.6)
ax2.plot(hubbard.norme,hubbard.normdz[0],'-.k',linewidth=1.,alpha=0.6)

ax.plot(gulkana.norme,gulkana.normdz[0],'--k',linewidth=1.,alpha=0.6)
ax.plot(wolverine.norme,wolverine.normdz[0],'-.k',linewidth=1.,alpha=0.6)

ax2.annotate('B',[0.07,10],horizontalalignment='center',verticalalignment='center',fontproperties=font)

#ax3 = ax2.twiny()
#ax3.set_xlim([0,15])
#plt.text(0.1,14,"Calving Flux (Gt a"+"$^{-1}$"+")", fontsize=11)
#ax3.set_xticks([1, 2, 3,4,5])
#for tick in ax3.xaxis.get_major_ticks():tick.label2.set_fontsize(10) 
#
#
##PLOTTING FLUXES AS CIRCLES
#termidz = [dz.compressed()[0] for dz in tide.normdz]
#
#for i,flx in enumerate(tide.eb_bm_flx.astype(float)):
#    circle1=plt.Circle([0,termidz[i]],flx,color='r',zorder=-1)
#    ell = mpatches.Ellipse(xy=[0,termidz[i]], width=flx*2, height=0.3, angle=0)
#    ax3.add_artist(ell)
#    ell.set_alpha(0.7)
#    ell.set_color('r')
plt.show()

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/dhdtprofiles2t.jpg",dpi=500)

