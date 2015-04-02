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
import datetime as dtm
from scipy.stats.mstats import kruskalwallis
import ConfigParser

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *
    

def make_interval_length_plot(axes,interval_list,colorlist):

    plt.rc("font", **{"sans-serif": ["Arial"],"size": 10})
    box = axes.boxplot(interval_list,vert=False,patch_artist=True,widths=0.5)
    print 'hi'
    for i,uzip in enumerate(zip(box['boxes'],box['medians'])):
        bx,median = uzip
        print 'bx',bx
        print 'med',median
        bx.set_facecolor(colorlist[i])
        bx.set_edgecolor(colorlist[i])
        median.set_color(color='k')
        median.set_lw(3)

    for i,uzip in enumerate(zip(box['caps'],box['whiskers'])):
        cap,whisk = uzip
        cap.set_lw(0)
        whisk.set_color(color=N.repeat(colorlist,2,axis=0)[i])
        whisk.set_ls('-')
        whisk.set_lw(3)
        
    axes.set_xticks([5,10,15,20])
    axes.set_xlabel("Interval Length\n(years)")
    axes.axes.get_yaxis().set_visible(False)
    axes.get_xaxis().tick_bottom()
    
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

    #surveyeddata = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True)  # 
    ##surveyeddata.fix_terminus()
    ##surveyeddata.remove_upper_extrap()
    #surveyeddata.normalize_elevation()
    #surveyeddata.calc_dz_stats()
    #surveyeddata.extend_upper_extrap()
 #Chugach Range
 #Fairweather Glacier Bay
 #
 #Juneau Icefield
 #Stikine Icefield
 #Aluetian Range
 #Coast Range BC
 #Kenai Mountains
 #Wrangell Mountains
 #St. Elias Mountains
 #Brooks Range
 #
    interiorz = " ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"
    scz = " ergi.region IN ('Chugach Range','St. Elias Mountains','Kenai Mountains','Aluetian Range')"
    sez = " ergi.region IN ('Juneau Icefield','Stikine Icefield','Fairweather Glacier Bay','Coast Range BC')"

    interior = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=2 AND gltype.surge='f' AND%s" % interiorz) 
    #interior.fix_terminus()
    interior.remove_upper_extrap(remove_bottom=True)
    interior.normalize_elevation()
    interior.calc_dz_stats(too_few=4)
    interior.extend_upper_extrap()
    
    sc = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f' AND%s" % scz) 
    print sc
    sc.fix_terminus()
    sc.remove_upper_extrap(remove_bottom=True)
    sc.normalize_elevation()
    sc.calc_dz_stats(too_few=4)
    sc.extend_upper_extrap()

    se = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f' AND%s" % sez) 
    #se.fix_terminus()
    se.remove_upper_extrap(remove_bottom=True)
    se.normalize_elevation()
    se.calc_dz_stats(too_few=4)
    se.extend_upper_extrap()

    #land = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f' AND%s" % sez) 
    ##se.fix_terminus()
    #land.remove_upper_extrap(remove_bottom=True)
    #land.normalize_elevation()
    #land.calc_dz_stats(too_few=4)
    #land.extend_upper_extrap()    

    #columbia = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Columbia'") 
    #columbia.fix_terminus()
    #columbia.remove_upper_extrap(remove_bottom=False)
    #columbia.normalize_elevation()
    #
    #hubbard = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Hubbard'") 
    #hubbard.fix_terminus()
    #hubbard.remove_upper_extrap(remove_bottom=False)
    #hubbard.normalize_elevation()
    #
    #wolverine = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Wolverine'") 
    #wolverine.fix_terminus()
    #wolverine.remove_upper_extrap(remove_bottom=False)
    #wolverine.normalize_elevation()
    #
    #gulkana = GetLambData(verbose=False,longest_interval=True,interval_min=5,by_column=True,as_object=True, userwhere="glnames.name='Gulkana'") 
    #gulkana.fix_terminus()
    #gulkana.remove_upper_extrap(remove_bottom=False)
    #gulkana.normalize_elevation()
    
#    pickle.dump([surveyeddata,land,tide,lake,columbia,hubbard,wolverine,gulkana], open( "/Users/igswahwsmcevan/Desktop/tempreg.p", "wb" ))
#else:
#    surveyeddata,land,tide,lake,columbia,hubbard,wolverine,gulkana = pickle.load(open( "/Users/igswahwsmcevan/Desktop/tempreg.p", "rb" ))

#GLACIERS THAT ARE THICKENING AT THE TERMINUS AND THINNING UP HIGH
#switch = N.logical_and(N.array([N.mean(dz[:20]) for dz in tide.normdz])>0,N.array([N.mean(dz[40:80]) for dz in tide.normdz])<0)


samples_lim=None
err_lim=None
title=None
alphafill = 0.2

fig = plt.figure(figsize=[4,6])
ax = fig.add_axes([0.15,0.545,0.7,0.43])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 13})
#ax.set_title('Surface Elevation Change: %s Glaciers' % outroot[i])

ax.set_ylabel("Elevation Change (m yr"+"$\mathregular{^{-1})}$", fontsize=11,labelpad=3)
#ax.set_xlabel('Normalized Elevation', fontsize=11)
ax.set_ylim([-6,1])
ax.set_xlim([0,1])
for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(10) 

#ax.plot(land.norme,land.dzs_mean,'-',color=N.array([163,100,57])/255.,linewidth=2.5,label='Mean')
#ax.plot(land.norme,land.dzs_mean-land.dzs_sem,'-',land.norme,land.dzs_mean+land.dzs_sem,'-',color=N.array([163,100,57])/255.,linewidth=1)
#ax.fill_between(land.norme,land.dzs_mean+land.dzs_std,land.dzs_mean-land.dzs_std,alpha=alphafill,color= N.array([163,100,57])/255.,lw=0)

l1, = ax.plot(interior.norme,interior.dzs_mean,'-',color='green',linewidth=2.5,label='Interior')
ax.plot(interior.norme,interior.dzs_mean-interior.dzs_sem,'-',interior.norme,interior.dzs_mean+interior.dzs_sem,'-',color='green',linewidth=1)
ax.fill_between(interior.norme,interior.dzs_mean-interior.dzs_std,interior.dzs_mean+interior.dzs_std,facecolor= 'green',alpha=alphafill,lw=0.01)

l2, = ax.plot(sc.norme,sc.dzs_mean,'-',color='b',linewidth=2.5,label='South Central')
ax.plot(sc.norme,sc.dzs_mean-sc.dzs_sem,'-',sc.norme,sc.dzs_mean+sc.dzs_sem,'-',color='b',linewidth=1)
ax.fill_between(sc.norme,sc.dzs_mean-sc.dzs_std,sc.dzs_mean+sc.dzs_std,facecolor= 'b',alpha=alphafill,lw=0.01)

l3, = ax.plot(se.norme,se.dzs_mean,'-',color='r',linewidth=2.5,label='Southeast')
ax.plot(se.norme,se.dzs_mean-se.dzs_sem,'-',se.norme,se.dzs_mean+se.dzs_sem,'-',color='r',linewidth=1)
ax.fill_between(se.norme,se.dzs_mean-se.dzs_std,se.dzs_mean+se.dzs_std,facecolor= 'r',alpha=alphafill,lw=0.01)

intarr = N.concatenate(tuple([dz for dz in interior.normdz]),axis=2).reshape(len(interior.normdz),100)
scarr = N.concatenate(tuple([dz for dz in sc.normdz]),axis=2).reshape(len(sc.normdz),100)
searr = N.concatenate(tuple([dz for dz in se.normdz]),axis=2).reshape(len(se.normdz),100)
sarr = N.vstack((scarr,searr))

kw = []
for i in xrange(100):kw.append(kruskalwallis(intarr[:,i],sarr[:,i])[1])
    

#ax.plot(interior.norme,inarr[0,:],'--k')

plt.legend([l1,l2,l3],['Interior N=%s'% str(len(interior.name)),'South Central N=%s'% str(len(sc.name)),'Southeast N=%s'% str(len(se.name))],loc='lower left',fontsize=9)


font = matplotlib.font_manager.FontProperties(family='Arial', weight='bold', size=15)
#ax.annotate('A',[0.07,0.5],horizontalalignment='center',verticalalignment='center',fontproperties=font)

for dz in interior.normdz:ax.plot(interior.norme,dz,'-k',linewidth=0.4,alpha=0.4)
#for dz in lake.normdz:ax.plot(lake.norme,dz,'-k',linewidth=0.4,alpha=0.2)

ax2 = fig.add_axes([0.15,0.07,0.7,0.43])

ax2.plot(interior.norme,interior.dzs_n,'g',label='n Samples')
ax2.plot(sc.norme,sc.dzs_n,'b',label='n Samples')
ax2.plot(se.norme,se.dzs_n,'r',label='n Samples')
ax2.set_ylabel('N')
ax3 = ax2.twinx()
ax3.plot(se.norme,kw,'k',label='n Samples')
ax3.plot([0,1],[0.05,0.05],'k--')
ax3.set_ylabel('p-value')

#ax2.plot()
#plt.rc("font", **{"sans-serif": ["Arial"],"size": 13})
#
#ax2.set_ylabel("Elevation Change (m yr"+"$\mathregular{^{-1})}$", fontsize=11,labelpad=-2)
#ax2.set_xlabel('Normalized Elevation', fontsize=11)
#ax2.set_ylim([-10,12])
#ax2.set_xlim([0,1])
#for tick in ax2.xaxis.get_major_ticks():tick.label.set_fontsize(10) 
#for tick in ax2.yaxis.get_major_ticks():tick.label.set_fontsize(10) 
#
#ax2.plot(tide.norme,tide.dzs_mean,'-',color='blue',linewidth=2,label='Mean')
#ax2.plot(tide.norme,tide.dzs_mean-tide.dzs_sem,'-',tide.norme,tide.dzs_mean+tide.dzs_sem,'-',color='blue',linewidth=0.7)
#ax2.fill_between(tide.norme,tide.dzs_mean+tide.dzs_std,tide.dzs_mean-tide.dzs_std,alpha=alphafill,color= 'blue',lw=0)
#ax2.fill_between(ax.get_xlim(),N.repeat(N.array(ax.get_ylim()[0]),2),N.repeat(N.array(ax.get_ylim()[1]),2),alpha=0.1,color= 'black',lw=0,zorder=0)
#
#for j,dz in enumerate(tide.normdz):
#    if switch[j]: ax2.plot(tide.norme,dz,'-k',linewidth=0.5,alpha=0.3)   # can make these a separate color
#    else: ax2.plot(tide.norme,dz,'-k',linewidth=0.5,alpha=0.3)
#    
#ax2.plot(columbia.norme,columbia.normdz[0],'--k',linewidth=1.,alpha=0.6)
#ax2.plot(hubbard.norme,hubbard.normdz[0],'-.k',linewidth=1.,alpha=0.6)
#
#ax.plot(gulkana.norme,gulkana.normdz[0],'--k',linewidth=1.,alpha=0.6)
#ax.plot(wolverine.norme,wolverine.normdz[0],'-.k',linewidth=1.,alpha=0.6)
#
#ax2.annotate('B',[0.07,10],horizontalalignment='center',verticalalignment='center',fontproperties=font)



ax3 = fig.add_axes([0.60,0.65,0.2,0.1])
make_interval_length_plot(ax3,[interior.interval/365.,sc.interval/365.,se.interval/365.],['g','b','r'])

#ax4 = fig.add_axes([0.60,0.43,0.3,0.05])
#make_interval_length_plot(ax4,[tide.interval/365.],['blue'])


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

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/dhdtprofiles_by_zone.jpg",dpi=500)

