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

a = True
if a:
    data = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
    regions = GetSqlData2("SELECT DISTINCT region::text FROM ergi;")['region'].astype('a30')
    
    
    pickle.dump([data,regions], open( "/Users/igswahwsmcevan/Desktop/temp.p", "wb" ))
else:
    data,regions = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp.p", "rb" ))

gltype=[0,1,2]
regions = regions[N.where(regions!='None')]
regions = regions[[10,7,8,0,9,6,1,2,3,4,5]]
regionlabels= [re.sub(' ','\n',region) for region in regions]

################################################################################
################################################################################
################################################################################
#Regions only
#boxdata = []
#for reg in regions:boxdata.append(data['bal'][N.where(data['region']==reg)])
#
#fig = plt.figure(figsize=[8,5])
#ax = fig.add_axes([0.1,0.3,0.8,0.65])
#
#ax.boxplot(boxdata)
#lbls = ax.set_xticklabels(regions)
#for lbl in lbls:
#    lbl.set_rotation(65)
#    lbl.set_size(9)
#
#ax.set_ylim(-4,0.5)
################################################################################
################################################################################
################################################################################
ylim = [-4.,0.55]

fig2 = plt.figure(figsize=[8,5])
ax2 = fig2.add_axes([0.08,0.2,0.9,0.78])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
boxdata2 = []
xs=[]
xi=0
for reg in regions:
    for gl in gltype:
        boxdata2.append(data['bal'][N.where(N.logical_and(data['region']==reg,data['gltype']==gl))])
        xs.append(xi)
        xi+=1
    xi+=2

labels = N.c_[N.zeros(regions.size,dtype='a30'),regions,N.zeros(regions.size,dtype='a30')]
labels=labels.reshape(labels.size)
labels=[re.sub(' ','\n',label) for label in labels]

box = ax2.boxplot(boxdata2,positions=xs,widths=1,sym='o')
lbls = ax2.set_xticklabels(labels,horizontalalignment='center',size=12,rotation=90)
#for lbl in lbls:lbl.set_rotation(90)

    
#colrs = N.tile(['brown','blue','green'],regions.size)
colorlist = N.tile(['brown','blue','green'],regions.size)[N.where(N.array([b.size for b in boxdata2])!=0)]
colorlist2 = N.tile(N.repeat(['brown','blue','green'],2),regions.size)

wt = N.where(N.array([b.size for b in boxdata2])!=0)[0]*2
colorlist2=colorlist2[N.sort(N.append(wt,wt+1))]

for i in N.arange(3.5,regions.size*5,5):ax2.plot([i,i],ylim,'--',c='0.5')

for i,bx in enumerate(box['boxes']):bx.set_color(color=colorlist[i])
for i,bx in enumerate(box['medians']):bx.set_color(color=colorlist[i])
for i,bx in enumerate(box['caps']):bx.set_color(color=colorlist2[i])
for i,bx in enumerate(box['whiskers']):bx.set_color(color=colorlist2[i])
for i,bx in enumerate(box['fliers']):
    bx.set_markerfacecolor(colorlist2[i])
    bx.set_markeredgewidth(0)
    bx.set_markersize(5)
    bx.set_alpha(0.3)

ns = N.array([bd.size for bd in boxdata2])

nsw = N.where(ns!=0)
ns = ns[nsw]
xs = N.array(xs)[nsw]

for i,n in enumerate(ns):
    if colorlist[i]=='blue':y=0.37
    else:y=0.25
    ax2.annotate(n,[xs[i],y],horizontalalignment='center',size=9)
    
ax2.plot(ax2.get_xlim(),[0,0],'-k')
ax2.set_ylim(ylim)
ax2.set_xlim([ax2.get_xlim()[0]-0.7,ax2.get_xlim()[1]])
ax2.set_ylabel("Mass Balance (m w. eq. a"+"$\mathregular{^{-1})}$")
ax2.set_yticks(N.arange(ylim[0],ylim[1],1).astype(int))


#data = GetSqlData2("SELECT SUM(mean*resultsauto.area)/8.5 FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")

plt.show()
fig2.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/NewSuppfig_all_glaciers.jpg",dpi=300)

#################################################################################
#################################################################################
#################################################################################
a = True
if a:
    data = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto WHERE surveyed='t' GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
    regions = GetSqlData2("SELECT DISTINCT region::text FROM ergi;")['region'].astype('a30')
    
    
    pickle.dump([data,regions], open( "/Users/igswahwsmcevan/Desktop/temp.p", "wb" ))
else:
    data,regions = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp.p", "rb" ))

gltype=[0,1,2]
regions = regions[N.where(regions!='None')]
regions = regions[[7,8,0,9,6,1,2,3]]
regionlabels= [re.sub(' ','\n',region) for region in regions]

ylim = [-4.,0.55]

fig3 = plt.figure(figsize=[8,5])
ax3 = fig3.add_axes([0.08,0.2,0.9,0.78])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
boxdata2 = []
xs=[]
xi=0
for reg in regions:
    for gl in gltype:
        boxdata2.append(data['bal'][N.where(N.logical_and(data['region']==reg,data['gltype']==gl))])
        xs.append(xi)
        xi+=1
    xi+=2

labels = N.c_[N.zeros(regions.size,dtype='a30'),regions,N.zeros(regions.size,dtype='a30')]
labels=labels.reshape(labels.size)
labels=[re.sub(' ','\n',label) for label in labels]

box = ax3.boxplot(boxdata2,positions=xs,widths=1,sym='o')
lbls = ax3.set_xticklabels(labels,horizontalalignment='center',size=12,rotation=90)
#for lbl in lbls:lbl.set_rotation(90)

    
#colrs = N.tile(['brown','blue','green'],regions.size)
colorlist = N.tile(['brown','blue','green'],regions.size)[N.where(N.array([b.size for b in boxdata2])!=0)]
colorlist2 = N.tile(N.repeat(['brown','blue','green'],2),regions.size)

wt = N.where(N.array([b.size for b in boxdata2])!=0)[0]*2
colorlist2=colorlist2[N.sort(N.append(wt,wt+1))]

for i in N.arange(3.5,regions.size*5,5):ax3.plot([i,i],ylim,'--',c='0.5')

for i,bx in enumerate(box['boxes']):bx.set_color(color=colorlist[i])
for i,bx in enumerate(box['medians']):bx.set_color(color=colorlist[i])
for i,bx in enumerate(box['caps']):bx.set_color(color=colorlist2[i])
for i,bx in enumerate(box['whiskers']):bx.set_color(color=colorlist2[i])
for i,bx in enumerate(box['fliers']):
    bx.set_markerfacecolor(colorlist2[i])
    bx.set_markeredgewidth(0)
    bx.set_markersize(5)
    bx.set_alpha(0.3)

ns = N.array([bd.size for bd in boxdata2])
nsw = N.where(ns!=0)
ns = ns[nsw]
xs = N.array(xs)[nsw]

for i,n in enumerate(ns):
    if colorlist[i]=='blue':y=0.37
    else:y=0.25
    ax3.annotate(n,[xs[i],y],horizontalalignment='center',size=9)
    
ax3.plot(ax3.get_xlim(),[0,0],'-k')
ax3.set_ylim(ylim)
ax3.set_xlim([ax3.get_xlim()[0]-0.7,ax3.get_xlim()[1]])
ax3.set_ylabel("Mass Balance (m w. eq. a"+"$\mathregular{^{-1})}$")
ax3.set_yticks(N.arange(ylim[0],ylim[1],1).astype(int))


#data = GetSqlData2("SELECT SUM(mean*resultsauto.area)/8.5 FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")

plt.show()
fig3.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/NewSuppfig1_surveyedglaciers.jpg",dpi=300)