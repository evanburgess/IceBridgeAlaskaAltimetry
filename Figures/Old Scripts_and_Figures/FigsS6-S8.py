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

def full_plot_extrapolation_curves(data,samples_lim=None,err_lim=None,title=None,hypsometry=None,color=None):
    alphafill = 0.1
    fig = plt.figure(figsize=[6,10])
    ax = fig.add_axes([0.11,0.59,0.79,0.4])
    
    if type(color)==NoneType: color='k'

    plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
    
    ax.set_ylabel("Elevation Change (m w. eq. yr"+"$\mathregular{^{-1})}$")
    ax.set_ylim([-10,3])
    ax.set_xlim([0,1])
    
    
    for dz in data.normdz:ax.plot(data.norme,dz,'-',color=color,linewidth=0.5,alpha=0.5)
    ax.plot(data.norme,data.dzs_mean,'-k',linewidth=2,label='Mean')
    ax.plot(data.norme,data.dzs_median,'--k',linewidth=2,label='Median')
    #ax.plot(data.norme,data.dzs_median-data.dzs_madn,'--k')
    #ax.plot(data.norme,data.dzs_median+data.dzs_madn,'--k')
    ax.plot(data.norme,data.dzs_mean+data.dzs_sem,'-r',linewidth=0.7,label= "Unsurveyed Error Estimate")
    ax.plot(data.norme,data.dzs_mean-data.dzs_sem,'-r',linewidth=0.7)
    ax.fill_between(data.norme,data.dzs_mean+data.dzs_std,data.dzs_mean-data.dzs_std,alpha=alphafill,color= 'black',lw=0.01)
    plt.legend(loc=4,fontsize=11)
    ax.set_ylim([-10,12])
    sort = N.argsort([dz[2] for dz in data.normdz])
    
    #ax1 = ax.twinx()
    #ax1.bar(hypsometry['normbins'],hypsometry['area'],width=0.01,color='0.2')
    
    #print data.name[sort[0]],data.name[sort[1]],data.name[sort[2]],data.name[sort[0]],data.name[sort[-2]],data.name[sort[-1]]
    #print data.name[sort[0]], data.norme[25], data.normdz[sort[0]][25]
    #ax.annotate(data.name[sort[0]], xy=(data.norme[25], data.normdz[sort[0]][25]), xytext=(0.4, -8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    #ax.annotate(data.name[sort[1]], xy=(data.norme[20], data.normdz[sort[1]][20]), xytext=(0.4, -6),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    #ax.annotate(data.name[sort[2]], xy=(data.norme[15], data.normdz[sort[2]][15]), xytext=(0.4, -9.),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    #ax.annotate(data.name[sort[3]], xy=(data.norme[10], data.normdz[sort[3]][10]), xytext=(0.4, -7),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    #ax.annotate(data.name[sort[-2]], xy=(data.norme[10], data.normdz[sort[-1]][10]), xytext=(0.4, 2.3),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    #ax.annotate(data.name[sort[-1]], xy=(data.norme[15], data.normdz[sort[-2]][15]), xytext=(0.4, 1.8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    
    ax2 = fig.add_axes([0.11,0.13,0.79,0.15])
    ax2.plot(data.norme,N.zeros(data.norme.size),'-',color='grey')
    ax2.plot(data.norme,N.array(data.kurtosis)-3,'k--',label='Excess Kurtosis',lw=1.5)     
    ax2.plot(data.norme,N.array(data.skew),'k-',label='Skewness',lw=1.2)
    ax2.set_ylim([-6,6])
    ax2.set_ylabel('Test Statistic',color='k')
    ax2.set_xlabel('Normalized Elevation')
    
    
    plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.3),ncol=1, fancybox=False, shadow=False,fontsize=11)
    ax3 = ax2.twinx()
    ax3.plot(data.norme,N.zeros(data.norme.size)+0.05,'-',color='grey')
    ax3.plot(data.norme,N.sqrt(N.array(data.normalp)),'r-',label='Shapiro-Wilk')
    #ax3.plot(data.norme,N.array(normal2),'k-',label='DiAgostino')
    for t in ax3.get_yticklabels():t.set_color('r')
    ax3.set_ylabel('p-values',color='r')
    ax3.set_ylim([0,1.1])
    plt.legend(loc='upper center', bbox_to_anchor=(0.78, -0.3),ncol=2, fancybox=False, shadow=False,fontsize=11) 
    
          
    #print data.dzs_n
    ax4 = fig.add_axes([0.11,0.38,0.79,0.18])
    ax4.plot(data.norme,data.dzs_n,'k',label='n Samples')
    #ax4.set_xlabel('Normalized Elevation')
    ax4.set_ylabel('N Samples')
    ax4.set_ylim([0,N.max(data.dzs_n)*1.1])
    plt.legend(loc='upper center',bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=False, shadow=False,fontsize=11) 
    ax5 = ax4.twinx()
    ax5.plot(data.norme,data.quadsum,'b-',label='Surveyed Error Estimate')
    ax5.plot(data.norme,data.dzs_sem,'r-',label='Unsurveyed Error Estimate')
    ax5.set_ylim(err_lim)
    ax5.set_ylabel("Uncertainty (m w. eq. yr"+"$\mathregular{^{-1})}$")
    ax4.set_ylim(samples_lim)

    
    plt.legend(loc='upper center',bbox_to_anchor=(0.78, -0.1),ncol=1, fancybox=False, shadow=False,fontsize=11) 
    
    ax.text(0.03,0.94,"A",fontsize=15, fontweight='bold',transform=ax.transAxes)
    ax4.text(0.03,0.83,"B",fontsize=15, fontweight='bold',transform=ax4.transAxes)
    ax2.text(0.03,0.83,"C",fontsize=15, fontweight='bold',transform=ax2.transAxes)
    

    #plt.show()

    return fig

colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.  
tidehyps = GetSqlData2("SELECT normbins::real,SUM(ergibins3.area)/1e6::real as area from ergibins3 left join ergi on ergibins3.glimsid=ergi.glimsid WHERE gltype=1 group by normbins order by normbins;")
landhyps = GetSqlData2("SELECT normbins::real,SUM(ergibins3.area)/1e6::real as area from ergibins3 left join ergi on ergibins3.glimsid=ergi.glimsid WHERE gltype=0 group by normbins order by normbins;")
lakehyps = GetSqlData2("SELECT normbins::real,SUM(ergibins3.area)/1e6::real as area from ergibins3 left join ergi on ergibins3.glimsid=ergi.glimsid WHERE gltype=2 group by normbins order by normbins;")
    

land = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'") 
land.convert085()
land.fix_terminus()
land.remove_upper_extrap(remove_bottom=False)
land.normalize_elevation()
land.calc_dz_stats(too_few=4)
land.extend_upper_extrap()
fig = full_plot_extrapolation_curves(land,hypsometry=landhyps,color=colors[0])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS6_land_stats.jpg",dpi=300)
fig=None


tide = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'",results=True) 
tide.convert085()
tide.fix_terminus()
tide.remove_upper_extrap(remove_bottom=False)
tide.normalize_elevation()
tide.calc_dz_stats(too_few=4)
tide.extend_upper_extrap()
fig = full_plot_extrapolation_curves(tide,samples_lim=None,err_lim=None,title=None,color=colors[2])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS7_tide_stats.jpg",dpi=300)
fig=None


lake = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest' AND gltype.surge='f'") 
lake.convert085()
lake.fix_terminus()
lake.remove_upper_extrap(remove_bottom=False)
lake.normalize_elevation()
lake.calc_dz_stats(too_few=4)
lake.extend_upper_extrap()
fig = full_plot_extrapolation_curves(lake,samples_lim=None,err_lim=None,title=None,color=colors[4])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS8_lake_stats.jpg",dpi=300)
fig=None
plt.show()