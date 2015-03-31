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

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

mn = 1
user_where=["FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'","FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'","FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest'","gltype.surge='f'"]

land = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere=user_where[0]) 
land.fix_terminus()
land.remove_upper_extrap()
land.normalize_elevation()
land.calc_dz_stats()
land.extend_upper_extrap()
        
tide = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere=user_where[1]) 
tide.fix_terminus()
tide.remove_upper_extrap(remove_bottom=False)
tide.normalize_elevation()
tide.calc_dz_stats()
tide.extend_upper_extrap()

columbia = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere="glnames.name='Columbia'") 
columbia.fix_terminus()
columbia.remove_upper_extrap(remove_bottom=False)
columbia.normalize_elevation()

hubbard = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere="glnames.name='Hubbard'") 
hubbard.fix_terminus()
hubbard.remove_upper_extrap(remove_bottom=False)
hubbard.normalize_elevation()


lake = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere=user_where[2]) 
lake.fix_terminus()
lake.remove_upper_extrap()
lake.normalize_elevation()
lake.calc_dz_stats()
lake.extend_upper_extrap()

lake2 = GetLambData(verbose=False,removerepeats=True,interval_min=mn,interval_max=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest' AND gltype.surge='f'") 
lake2.fix_terminus()
lake2.remove_upper_extrap()
lake2.normalize_elevation()
lake2.calc_dz_stats()
lake2.extend_upper_extrap()

#GLACIERS THAT ARE THICKENING AT THE TERMINUS AND THINNING UP HIGH
switch = N.logical_and(N.array([N.mean(dz[:20]) for dz in tide.normdz])>0,N.array([N.mean(dz[40:80]) for dz in tide.normdz])<0)


samples_lim=None
err_lim=None
title=None
alphafill = 0.2

fig = plt.figure(figsize=[4,6])
ax = fig.add_axes([0.15,0.55,0.8,0.4])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
#ax.set_title('Surface Elevation Change: %s Glaciers' % outroot[i])

ax.set_ylabel('dh/dt (m a'+"$\mathregular{^{-1})}$", fontsize=11,labelpad=0)
#ax.set_xlabel('Normalized Elevation', fontsize=11)
ax.set_ylim([-6,1])
ax.set_xlim([0,1])
for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(10) 

ax.plot(land.norme,land.dzs_mean,'-',color='brown',linewidth=2.5,label='Mean')
ax.plot(land.norme,land.dzs_mean-land.dzs_sem,'-',land.norme,land.dzs_mean+land.dzs_sem,'-',color='brown',linewidth=1)
ax.fill_between(land.norme,land.dzs_mean+land.dzs_std,land.dzs_mean-land.dzs_std,alpha=alphafill,color= 'brown',lw=0)

ax.plot(lake.norme,lake.dzs_mean,'-',color='green',linewidth=2.5,label='Mean')
ax.plot(lake.norme,lake.dzs_mean-lake.dzs_sem,'-',lake.norme,lake.dzs_mean+lake.dzs_sem,'-',color='green',linewidth=1)
ax.fill_between(lake.norme,lake.dzs_mean+lake.dzs_std,lake.dzs_mean-lake.dzs_std,alpha=alphafill,color= 'green',lw=0)

for dz in land.normdz:ax.plot(land.norme,dz,'-k',linewidth=0.4,alpha=0.2)
for dz in lake.normdz:ax.plot(lake.norme,dz,'-k',linewidth=0.4,alpha=0.2)

ax2 = fig.add_axes([0.15,0.1,0.8,0.4])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

ax2.set_ylabel('dh/dt (m a'+"$\mathregular{^{-1})}$", fontsize=11,labelpad=0)
ax2.set_xlabel('Normalized Elevation', fontsize=11)
ax2.set_ylim([-10,12])
ax2.set_xlim([0,1])
for tick in ax2.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
for tick in ax2.yaxis.get_major_ticks():tick.label.set_fontsize(10) 

ax2.plot(tide.norme,tide.dzs_mean,'-',color='blue',linewidth=2,label='Mean')
ax2.plot(tide.norme,tide.dzs_mean-tide.dzs_sem,'-',tide.norme,tide.dzs_mean+tide.dzs_sem,'-',color='blue',linewidth=0.7)
ax2.fill_between(tide.norme,tide.dzs_mean+tide.dzs_std,tide.dzs_mean-tide.dzs_std,alpha=alphafill,color= 'blue',lw=0)
for j,dz in enumerate(tide.normdz):
    if switch[j]: 
        ax2.plot(tide.norme,dz,'-r',linewidth=0.5,alpha=0.3)
        print tide.name[j]
    else: ax2.plot(tide.norme,dz,'-k',linewidth=0.5,alpha=0.3)
ax2.plot(columbia.norme,columbia.normdz[0],'--k',linewidth=1.,alpha=0.6)
ax2.plot(hubbard.norme,hubbard.normdz[0],'-.k',linewidth=1.,alpha=0.6)

#PLOTTING FLUXES AS CIRCLES
termidz = [dz[0] for dz in tide.normdz]

for i,flx in enumerate(tide.eb_bm_flx.astype(float)):
    circle1=plt.Circle([0,termidz[i]],flx**0.5/10,color='r',zorder=-1)
    pth = ax2.add_patch(circle1)
plt.show()

#fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/dhdtprofiles.jpg",dpi=500)
















#plt.legend(loc=4,fontsize=11)

#sort = N.argsort([dz[2] for dz in data.normdz])

#print data.name[sort[0]],data.name[sort[1]],data.name[sort[2]],data.name[sort[0]],data.name[sort[-2]],data.name[sort[-1]]
#print data.name[sort[0]], data.norme[25], data.normdz[sort[0]][25]
#ax.annotate(data.name[sort[0]], xy=(data.norme[25], data.normdz[sort[0]][25]), xytext=(0.4, -8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
#ax.annotate(data.name[sort[1]], xy=(data.norme[20], data.normdz[sort[1]][20]), xytext=(0.4, -6),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
#ax.annotate(data.name[sort[2]], xy=(data.norme[15], data.normdz[sort[2]][15]), xytext=(0.4, -9.),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
#ax.annotate(data.name[sort[3]], xy=(data.norme[10], data.normdz[sort[3]][10]), xytext=(0.4, -7),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
#ax.annotate(data.name[sort[-2]], xy=(data.norme[10], data.normdz[sort[-1]][10]), xytext=(0.4, 2.3),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
#ax.annotate(data.name[sort[-1]], xy=(data.norme[15], data.normdz[sort[-2]][15]), xytext=(0.4, 1.8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))

#ax2 = fig.add_axes([0.11,0.35,0.8,0.18])
#ax2.plot(data.norme,N.zeros(data.norme.size),'-',color='grey')
#ax2.plot(data.norme,N.array(data.kurtosis)-3,'g-',label='Excess Kurtosis')     
#ax2.plot(data.norme,N.array(data.skew),'r-',label='Skewness')
#ax2.set_ylim([-6,6])
#ax2.set_ylabel('Test Statistic')
#plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=True, shadow=True,fontsize=11)
#ax3 = ax2.twinx()
#ax3.plot(data.norme,N.zeros(data.norme.size)+0.05,'-',color='grey')
#ax3.plot(data.norme,N.sqrt(N.array(data.normalp)),'k-',label='Shapiro-Wilk')
##ax3.plot(data.norme,N.array(normal2),'k-',label='DiAgostino')
#ax3.set_xlabel('Normalized Elevation')
#ax3.set_ylabel('p-values')
#ax3.set_ylim([0,1.1])
#plt.legend(loc='upper center', bbox_to_anchor=(0.78, -0.1),ncol=2, fancybox=True, shadow=True,fontsize=11) 
#
#ax4 = fig.add_axes([0.11,0.11,0.8,0.15])      
##print data.dzs_n
#ax4.plot(data.norme,data.dzs_n,'k',label='n Samples')
#ax4.set_xlabel('Normalized Elevation')
#ax4.set_ylabel('N Samples')
#ax4.set_ylim([0,N.max(data.dzs_n)*1.1])
#plt.legend(loc='upper center',bbox_to_anchor=(0.24, -0.3),ncol=1, fancybox=True, shadow=True,fontsize=11) 
#ax5 = ax4.twinx()
#ax5.plot(data.norme,data.quadsum,'r-',label='Surveyed Err.')
#ax5.plot(data.norme,data.dzs_sem,'b-',label='Unsurveyed Err.')
#ax5.set_ylim(err_lim)
#ax4.set_ylim(samples_lim)
#ax.set_title(title)
#plt.legend(loc='upper center',bbox_to_anchor=(0.78, -0.3),ncol=1, fancybox=True, shadow=True,fontsize=11) 
#plt.show()

#return ax,ax2,ax3,ax4,ax5

