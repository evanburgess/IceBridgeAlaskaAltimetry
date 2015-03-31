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
import pickle

import ConfigParser
from glob import glob

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

def plot_brace(ax,left,right,y,height,up=True,color='k',annotate=None,fontsize=12,rotation=0):
    if up:hgt = height/2.
    else: hgt = -height/2.
    
    mid = (left+right)/2.
    
    brace,tip = ax.plot([left,left,right,right],[y-hgt,y,y,y-hgt],'-%s' % color,[mid,mid],[y,y+hgt],'-%s' % color)
    if type(annotate)!=NoneType:
        if up:vert='bottom'
        else:vert='top'
        txt = ax.annotate(annotate,[mid,y+hgt*1.2],horizontalalignment='center',verticalalignment=vert,fontsize=fontsize,rotation=rotation)
        return brace,tip,txt
    else:
        return brace,tip
 
   
#PLOTTING FULL PARTITIONING
a = False
if a:
    lamb = GetLambData(longest_interval=True,userwhere="ergi.gltype='1' and ergi.name != 'Taku Glacier'", as_object=True, orderby='glimsid',results=True)
    
    pickle.dump(lamb, open( "/Users/igswahwsmcevan/Desktop/temp3.p", "wb" ))
else:
    lamb = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp3.p", "rb" ))
width = 0.4

#########################################################################
#FLUXES WITH ALL GLACIERS
#WHICH OF THE LAMB SURVEYED TIDEWATERS DO WE HAVE FLUX ESTIMATES?
w = N.where(N.isnan(lamb.eb_bm_flx.astype(float))==False)[0]
print len(w)
#of those get the total flux and flux error
flx=-N.sum(lamb.eb_bm_flx.astype(float)[w])
flxerr=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5

#NOW NEED THE ALTIMETRY NET MASS BUDGET FOR EACH OF THESE GLACIERS
##################
t = GetSqlData2("SELECT glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))
vol=N.sum(t['net'][w])
volerr=N.sum(t['neterror'][w])
print ['vol',vol]  
#################
#NOW CLIMATIC BALANCE OR SMB
smb = N.sum(vol - flx)
smberr = (volerr**2+flxerr**2)**0.5

#print smb, N.sum(t['net'][w],lamb.eb_bm_flx.astype(float)[w],t['net'][w]+lamb.eb_bm_flx.astype(float)[w])

#########################
#NOW BEGINNING PLOTTING
fig = plt.figure(figsize=[2.3,2.3])
colors = [[1,0.8,0.8],[1,0,0],[0.8,0.8,1],[0,0,1],[0.8,1,0.8],[0,1,0]]
axwidth=0.23

#ax = fig.add_axes([0.43,0.1,axwidth*2.35,0.8],frameon=False)
ax = fig.add_axes([0.28,0.05,0.7,0.9],frameon=True)

plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

barlocs = [0,1,4,5,2,3]

b1,b2,b3 = ax.bar(N.array([3.2,4.2,5.2])+width,[vol,smb,flx],yerr=[volerr,smberr,flxerr],width=width,color=[0.5,0.5,0.5],ecolor='k') # 

#print 'all'
#temp =  N.c_[lamb.name[w],t['net'][w],lamb.eb_bm_flx.astype(float)[w]]
#for li in temp:print "%s,%s,%s" % (li[0],li[1],li[2])
#print smb,flx,vol
#print smberr,flxerr,volerr
#########################################################################
#FLUXES WITH ALL GLACIERS EXCLUDING COLUMBIA
#WHICH OF THE LAMB SURVEYED TIDEWATERS DO WE HAVE FLUX ESTIMATES?
w = N.where(N.logical_and(N.isnan(lamb.eb_bm_flx.astype(float))==False,N.array([x!='Columbia Glacier' for x in lamb.name])))[0]

#of those get the total flux and flux error
flx=-N.sum(lamb.eb_bm_flx.astype(float)[w])
flxerr=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5

#flx=-N.mean((lamb.eb_bm_flx.astype(float)/lamb.area*1000.)[w])                     #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
#flxerr=N.sum(((lamb.eb_bm_err.astype(float)/lamb.area*1000.)[w])**2)**0.5/len(w)         #REROR this isn't right!!THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT

#NOW NEED THE ALTIMETRY NET MASS BUDGET FOR EACH OF THESE GLACIERS
##################
t = GetSqlData2("SELECT glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))
#t = GetSqlData2("SELECT glimsid, SUM(mean*area)/SUM(area)*0.85::real as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/SUM(area)*0.85)^2+(0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))   #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT

vol=N.sum(t['net'][w]) 
print ['vol',vol]      
volerr=N.sum(t['neterror'][w])   


#vol=N.mean(t['net'][w])                            #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
#volerr=(N.sum(t['neterror'][w]**2))**0.5/len(w)    #ERROR this isn't right!!THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
#################
#NOW CLIMATIC BALANCE OR SMB
smb = N.sum(vol - flx)
smberr = (volerr**2+flxerr**2)**0.5
w2 = N.where(lamb.name!='Columbia Glacier')

b1,b2,b3 = ax.bar(N.array([3.2,4.2,5.2]),[vol,smb,flx],yerr=[volerr,smberr,flxerr],width=width,color=[0.8,0.8,0.8],ecolor='k') # 
#print smb, N.sum(t['net'][w],lamb.eb_bm_flx.astype(float)[w],t['net'][w]+lamb.eb_bm_flx.astype(float)[w])
#print 'no col'
#temp =  N.c_[lamb.name[w],t['net'][w],lamb.eb_bm_flx.astype(float)[w]]
#for li in temp:print "%s,%s,%s" % (li[0],li[1],li[2])
#print smb,flx,vol
#print smberr,flxerr,volerr
##########################################################################
#UNPARTITIONED MASS LOSS



#list of glimsids of glaciers that have partitioned mass balances
partitionedglims = lamb.glimsid[N.where(N.isnan(lamb.eb_bm_flx.astype(float))==False)[0]]
t = GetSqlData2("SELECT name, glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid NOT IN ('%s') AND gltype = '1' GROUP BY glimsid,name;" %  "','".join(partitionedglims))
unpart_vol=N.sum(t['net'][w])
unpart_volerr=N.sum(t['neterror'][w])

b1 = ax.bar([6.5],[unpart_vol],yerr=[unpart_volerr],width=width,color=[0.5,0.5,0.5],ecolor='k') # 
ax.plot(ax.get_xlim(),[0,0],'-k',lw=1.5)

#ax.annotate('Mass Balance',[3+width*1.5,-4],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Calving',[4+width*1.5,-16],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Net',[5+width*1.5,-11],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Unpartitioned',[6.5+width/2,-4],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
font = matplotlib.font_manager.FontProperties(family='Arial', weight='bold', size=15)
plot_brace(ax,3.2,3.2+width*2,-8,2,up=False,color='k',annotate='Net',fontsize=10)#('B',[0.5,-49],horizontalalignment='center',verticalalignment='center',fontproperties=font)
plot_brace(ax,4.2,4.2+width*2,-2,2,up=False,color='k',annotate='SMB',fontsize=10)
plot_brace(ax,5.2,5.2+width*2,2,2,up=True,color='k',annotate='Calving',fontsize=10,rotation=90)
plot_brace(ax,6.5,6.5+width,-2,2,up=False,color='k',annotate='Unpartitioned',fontsize=10,rotation=90)
ax.annotate('C',[3.4,-49],horizontalalignment='center',verticalalignment='center',fontproperties=font)
ax.set_ylabel("Gt year"+"$\mathregular{^{-1}}$",labelpad=0)
ax.axes.get_xaxis().set_visible(False)
ax.get_yaxis().tick_left()

plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/tidewater_partition.jpg",dpi=300)