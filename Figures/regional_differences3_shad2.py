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

def plot_brace(ax,left,right,y,height,up=True,color='k',annotate=None,fontsize=12,bbox=None,zorder=4):
    if up:hgt = height/2.
    else: hgt = -height/2.
    
    mid = (left+right)/2.
    if type(bbox) != NoneType: bbox = dict(fc="white", lw=0)
    
    brace,tip = ax.plot([left,left,right,right],[y-hgt,y,y,y-hgt],'-%s' % color,[mid,mid],[y,y+hgt],'-%s' % color)
    if type(annotate)!=NoneType:
        if up:vert='bottom'
        else:vert='top'
        txt = ax.annotate(annotate,[mid,y+hgt*1.2],horizontalalignment='center',verticalalignment=vert,fontsize=fontsize,bbox=bbox,zorder=zorder)
        return brace,tip,txt
    else:
        return brace,tip
 
 
#a = False
#if a:
#    data_un = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
#    regions = GetSqlData2("SELECT DISTINCT region::text FROM ergi;")['region'].astype('a30')
#    
#    
#    pickle.dump([data,regions], open( "/Users/igswahwsmcevan/Desktop/temp.p", "wb" ))
#else:
#    data,regions = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp.p", "rb" ))



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
#ylim = [-4.,0.55]
#
#fig2 = plt.figure(figsize=[8,5])
#ax2 = fig2.add_axes([0.08,0.2,0.9,0.78])
#plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
#boxdata2 = []
#xs=[]
#xi=0
#for reg in regions:
#    for gl in gltype:
#        boxdata2.append(data['bal'][N.where(N.logical_and(data['region']==reg,data['gltype']==gl))])
#        xs.append(xi)
#        xi+=1
#    xi+=2
#
#labels = N.c_[N.zeros(regions.size,dtype='a30'),regions,N.zeros(regions.size,dtype='a30')]
#labels=labels.reshape(labels.size)
#labels=[re.sub(' ','\n',label) for label in labels]
#
#box = ax2.boxplot(boxdata2,positions=xs,widths=1,sym='o')
#lbls = ax2.set_xticklabels(labels,horizontalalignment='center',size=12,rotation=90)
##for lbl in lbls:lbl.set_rotation(90)
#
#    
##colrs = N.tile(['brown','blue','green'],regions.size)
#colorlist = N.tile(['brown','blue','green'],regions.size)[N.where(N.array([b.size for b in boxdata2])!=0)]
#colorlist2 = N.tile(N.repeat(['brown','blue','green'],2),regions.size)
#
#wt = N.where(N.array([b.size for b in boxdata2])!=0)[0]*2
#colorlist2=colorlist2[N.sort(N.append(wt,wt+1))]
#
#for i in N.arange(3.5,regions.size*5,5):ax2.plot([i,i],ylim,'--',c='0.5')
#
#for i,bx in enumerate(box['boxes']):bx.set_color(color=colorlist[i])
#for i,bx in enumerate(box['medians']):bx.set_color(color=colorlist[i])
#for i,bx in enumerate(box['caps']):bx.set_color(color=colorlist2[i])
#for i,bx in enumerate(box['whiskers']):bx.set_color(color=colorlist2[i])
#for i,bx in enumerate(box['fliers']):
#    bx.set_markerfacecolor(colorlist2[i])
#    bx.set_markeredgewidth(0)
#    bx.set_markersize(5)
#    bx.set_alpha(0.3)
#
#ns = N.array([bd.size for bd in boxdata2])
#
#nsw = N.where(ns!=0)
#ns = ns[nsw]
#xs = N.array(xs)[nsw]
#
#for i,n in enumerate(ns):
#    if colorlist[i]=='blue':y=0.37
#    else:y=0.25
#    ax2.annotate(n,[xs[i],y],horizontalalignment='center',size=9)
#    
#ax2.plot(ax2.get_xlim(),[0,0],'-k')
#ax2.set_ylim(ylim)
#ax2.set_xlim([ax2.get_xlim()[0]-0.7,ax2.get_xlim()[1]])
#ax2.set_ylabel("Mass Balance (m w. eq. a"+"$\mathregular{^{-1})}$")
#ax2.set_yticks(N.arange(ylim[0],ylim[1],1).astype(int))
#
#
##data = GetSqlData2("SELECT SUM(mean*resultsauto.area)/8.5 FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
#
#plt.show()
#fig2.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/NewSuppfig_all_glaciers.jpg",dpi=300)

#################################################################################
#################################################################################
#################################################################################
a = False
if a:
    survdata = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto WHERE surveyed='t' GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
    regions = GetSqlData2("SELECT DISTINCT region::text FROM ergi;")['region'].astype('a30')  
    alldata = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
    d = GetSqlData2("SELECT gltype,surveyed,SUM(mean*area)/SUM(area)*0.85 as myr,SUM(mean*area)/1e9*0.85 as gt,(((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/SUM(area)*0.85)^2+(0)^2)^0.5::real as myrerr,(((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as gterr,sum(area)/1e6::real as area from resultsauto group by gltype,surveyed order by gltype,surveyed;")  
    lamb = GetLambData(longest_interval=True,userwhere="ergi.gltype='1' and ergi.name != 'Taku Glacier'", as_object=True, orderby='glimsid',results=True)
    pickle.dump([survdata,regions,d,alldata,lamb], open( "/Users/igswahwsmcevan/Desktop/temp.p", "wb" ))
else:
    survdata,regions,d,alldata,lamb = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp.p", "rb" ))

survdata['region']=N.where([i in ("East Yakutat Glacier","West Yakutat Glacier","Battle Glacier") for i in survdata['name']],"Fairweather Glacier Bay",survdata['region'])


  
gltype=[0,2,1]
regions = regions[N.where(regions!='None')]
regions = regions[[7,8,0,9,6,1,2,3]]
regionlabels= [re.sub(' ','\n',region) for region in regions]
ylim = [-4.,0.55]

#alldata['gltype'] = N.where(alldata['gltype']==2,0,alldata['gltype'])
#LABELS FOR X AXIS
regionslab=N.array(['Alaska\nRange','Wrangell','Chugach','St. Elias','Kenai','Fairwthr.\nGl. Bay','Juneau','Stikine'])
labels = N.c_[N.zeros(regions.size,dtype='a30'),regionslab,N.zeros(regions.size,dtype='a30')]
labels=labels.reshape(labels.size)
#labels=[re.sub(' ','\n',label) for label in labels]


#FORMATTING DATA FOR BOXPLOT
boxdata = []
pointdata= []
xs=[]
xi=0
for reg in regions:
    for gl in gltype:
        boxdata.append(alldata['bal'][N.where(N.logical_and(alldata['region']==reg,alldata['gltype']==gl))])
        pointdata.append(survdata['bal'][N.where(N.logical_and(survdata['region']==reg,survdata['gltype']==gl))])
        xs.append(xi)
        xi+=1
    xi+=2
xs = N.array(xs)
    
picks=[]
ns = N.array([bd.size for bd in pointdata])

for i,n in enumerate(ns):
    if n!=0:picks.append(i)
        


#COLORS 
colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.
colors = N.array([[240,201,175],[163,100,57],[179,203,252],[45,80,150],[189,237,166],[75,150,38]])/255.
#colorlist = N.tile(['brown','blue','green'],regions.size)#[N.where(N.array([b.size for b in boxdata2])!=0)]
#colorlist2 = N.tile(N.repeat(['brown','blue','green'],2),regions.size)
#colorlist3 = N.tile(['brown','blue','green'],regions.size)

colorlist = N.array([[0,0,0]])
for i in xrange(len(boxdata)):colorlist = N.append(colorlist,colors[[0,4,2],:],axis=0)
colorlist = N.delete(colorlist,0,0)
colorlist=colorlist[picks]

colorlistdark = N.array([[0,0,0]])
for i in xrange(len(boxdata)):colorlistdark = N.append(colorlistdark,colors[[1,5,3],:],axis=0)
colorlistdark = N.delete(colorlistdark,0,0)
colorlistdark=colorlistdark#[picks]


#FIGURE 
fig3 = plt.figure(figsize=[8,3.5])
ax3 = fig3.add_axes([0.07,0.02,0.7,0.94],frameon=True)
ax = fig3.add_axes([0.88,0.02,0.11,0.94],frameon=True)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 11})

#box = ax3.boxplot(boxdata,positions=xs,widths=1,sym='',patch_artist=True)

lbls = ax3.set_xticklabels(labels,horizontalalignment='center',size=12)


pointdata= N.array(pointdata)
pointxs = []
for i,line in enumerate(pointdata):pointxs.append(N.zeros_like(line)+xs[i])
#pointdata = pointdata[[N.where(N.array([i.size for i in boxdata])!=0)[0]]]
#pointxs = N.array(pointxs)[[N.where(N.array([i.size for i in boxdata])!=0)[0]]]


box = ax3.boxplot(pointdata,positions=N.array(xs),widths=1,sym='',patch_artist=True)
        

big = [1,4]
for i,k in enumerate(N.arange(3.5,regions.size*5,5)):
    if i in big: lw,lcolor = 3,'0.5'
    else: lw,lcolor = 0.5,'0.2'
    ax3.plot([k,k],ylim,color=lcolor,lw=lw)

##for i,bx in enumerate(box['boxes']):bx.set_color(color=colorlist[i])
for i,bx in enumerate(box['boxes']):
    bx.set_facecolor(colorlistdark[i])
    bx.set_edgecolor(colorlistdark[i])
for i,bx in enumerate(box['medians']):
    bx.set_color(color='k')
    bx.set_lw(2)
for i,bx in enumerate(box['caps']):
    #bx.set_color(color=N.repeat(colorlist,2,axis=0)[i])
    bx.set_lw(0)
for i,bx in enumerate(box['whiskers']):
    bx.set_color(color=N.repeat(colorlistdark,2,axis=0)[i])
    bx.set_ls('-')
    bx.set_lw(2)
box['fliers'] = []
#for i,bx in enumerate(box['fliers']):
#    bx.set_markerfacecolor(colorlist3[i])
#    bx.set_markeredgewidth(0)
#    bx.set_markersize(5)
#    bx.set_alpha(0.3)
#    

    #sca.set_lw(0)
#    N.where(N.array([i.size for i in boxdata])!=0)


#nsw = N.where(ns!=0)
#ns = ns[picks]
#xs2 = N.array(xs)[nsw]

for n,x in zip(ns[picks],xs[picks]):
    #if colorlist[i]=='blue':y=0.37
    #else:
    y=0.3
    ax3.annotate(n,[x,y],horizontalalignment='center',size=10)
    

ax3.set_ylim(ylim)
ax3.set_xlim([ax3.get_xlim()[0]-0.7,ax3.get_xlim()[1]+1])
ax3.set_ylabel("Mass Balance (m w. eq. a"+"$\mathregular{^{-1})}$")
ax3.set_yticks(N.arange(ylim[0],ylim[1],1).astype(int))
ax3.axes.get_xaxis().set_visible(False)
ax3.get_yaxis().tick_left()

braceys=[-2,-2,-2,-2.5,-2.5,-2,-2,-2]
begs=N.arange(0,37,5)-0.5
ends = N.arange(0,37,5)+2.5
for by,beg,end,reg in zip(braceys,begs,ends,regionslab):plot_brace(ax3,beg,end,by,0.2,up=False,annotate=reg,fontsize=10,bbox='white')
braceys=[-3.2,-3,-2.8]
begs = begs[[0,2,5]]
ends = ends[[1,4,7]]
zones = ['Interior','South-Central','Southeast']
stop = [1,4,7]

for by,beg,end,reg in zip(braceys,begs,ends,zones):plot_brace(ax3,beg,end,by,0.2,up=False,annotate=reg,fontsize=10,bbox='white')

xlim =ax3.get_xlim()
ax3.plot(xlim,[0,0],'-k')#ax3.set_xlim(xlim)


########################################################################
#MASS BALANCE BY GTS 
density=0.85
density_err=0.06
acrossgl_err=0.000
width = 0.8



#colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.


barlocs = [0,2,1]


#PLOTTING Mass Balance(m w. eq.)

#ADDING ERROR FOR SMALL GLACIER BIAS from output from balance_by_area2.py
uneven_error = [list(d['gterr']),list(d['gterr'])]
uneven_error[0][0]+=2.605

#PLOTTING

pl1 = ax.bar(N.array(barlocs), d['gt'][[1,3,5]], color=colors[[1,3,5]], width=width,yerr=N.array(uneven_error)[:,[1,3,5]],error_kw=dict(ecolor='k'))
pl2 = ax.bar(N.array(barlocs), d['gt'][[0,2,4]], color=colors[[0,2,4]], width=width,yerr=N.array(uneven_error)[:,[0,2,4]],error_kw=dict(ecolor='k'),bottom=d['gt'][[1,3,5]])
#ax.bar(barlocs, d['gt'], color=colors, width=width,yerr=uneven_error,error_kw=dict(ecolor='k'))

##########################################################################
##########################################################################
##########################################################################
##PLOTTING FULL PARTITIONING
#
#
#width = 0.4
##ax4 = fig.add_axes([axwidth*2+0.15,0.1,axwidth,0.8])
#
#
#
#
##FLUXES WITH ALL GLACIERS
##WHICH OF THE LAMB SURVEYED TIDEWATERS DO WE HAVE FLUX ESTIMATES?
#w = N.where(N.isnan(lamb.eb_bm_flx.astype(float))==False)[0]
#print len(w)
##of those get the total flux and flux error
#flx=-N.sum(lamb.eb_bm_flx.astype(float)[w])
#flxerr=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5
#
##NOW NEED THE ALTIMETRY NET MASS BUDGET FOR EACH OF THESE GLACIERS
###################
#t = GetSqlData2("SELECT glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))
#vol=N.sum(t['net'][w])
#volerr=N.sum(t['neterror'][w])
#
##################
##NOW CLIMATIC BALANCE OR SMB
#smb = N.sum(vol - flx)
#smberr = (volerr**2+flxerr**2)**0.5
#b1,b2,b3 = ax.bar([3.,4.,5.],[smb,flx,vol],yerr=[smberr,flxerr,volerr],width=width,color=[0.5,0.5,0.5],ecolor='k') # 
##data = GetSqlData2("SELECT SUM(mean*resultsauto.area)/8.5 FROM resultsauto GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")
##########################################################################
##########################################################################
##########################################################################
##FLUXES WITH ALL GLACIERS EXCLUDING COLUMBIA
##WHICH OF THE LAMB SURVEYED TIDEWATERS DO WE HAVE FLUX ESTIMATES?
#w = N.where(N.logical_and(N.isnan(lamb.eb_bm_flx.astype(float))==False,N.array([x!='Columbia Glacier' for x in lamb.name])))[0]
#
##of those get the total flux and flux error
#flx=-N.sum(lamb.eb_bm_flx.astype(float)[w])
#flxerr=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5
#
##flx=-N.mean((lamb.eb_bm_flx.astype(float)/lamb.area*1000.)[w])                     #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
##flxerr=N.sum(((lamb.eb_bm_err.astype(float)/lamb.area*1000.)[w])**2)**0.5/len(w)         #REROR this isn't right!!THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
#
##NOW NEED THE ALTIMETRY NET MASS BUDGET FOR EACH OF THESE GLACIERS
###################
#t = GetSqlData2("SELECT glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))
##t = GetSqlData2("SELECT glimsid, SUM(mean*area)/SUM(area)*0.85::real as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/SUM(area)*0.85)^2+(0)^2)^0.5::real as neterror from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(lamb.glimsid))   #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
#
#vol=N.sum(t['net'][w])       
#volerr=N.sum(t['neterror'][w])   
#
#
##vol=N.mean(t['net'][w])                            #THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
##volerr=(N.sum(t['neterror'][w]**2))**0.5/len(w)    #ERROR this isn't right!!THIS CALCULATES NUMBERS FOR PAPER OR THE SAME NUMBERS BUT IN M/W EQ RATHER THAN GT
##################
##NOW CLIMATIC BALANCE OR SMB
#smb = N.sum(vol - flx)
#smberr = (volerr**2+flxerr**2)**0.5
#w2 = N.where(lamb.name!='Columbia Glacier')
#
#b1,b2,b3 = ax.bar(N.array([3.,4.,5.])+width,[smb,flx,vol],yerr=[smberr,flxerr,volerr],width=width,color=[0.8,0.8,0.8],ecolor='k') # 
#
#########################################################################
#########################################################################
#########################################################################
##UNPARTITIONED MASS LOSS
#
#
#
##list of glimsids of glaciers that have partitioned mass balances
#partitionedglims = lamb.glimsid[N.where(N.isnan(lamb.eb_bm_flx.astype(float))==False)[0]]
#t = GetSqlData2("SELECT name, glimsid, SUM(mean*area)/1e9*0.85 as net, (((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as neterror from resultsauto WHERE glimsid NOT IN ('%s') AND gltype = '1' GROUP BY glimsid,name;" %  "','".join(partitionedglims))
#unpart_vol=N.sum(t['net'][w])
#unpart_volerr=N.sum(t['neterror'][w])
#
#b1 = ax.bar([6.5],[unpart_vol],yerr=[unpart_volerr],width=width,color=[0.5,0.5,0.5],ecolor='k') # 
#
#ax.annotate('SMB',[3+width*1.5,-4],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Calving',[4+width*1.5,-16],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Net',[5+width*1.5,-11],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
#ax.annotate('Unpartitioned Tidewater Mass Balance',[6.5+width/2,-4],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
font = matplotlib.font_manager.FontProperties(family='Arial', weight='bold', size=15)
ax3.annotate('A',[0.5,-3.8],horizontalalignment='center',verticalalignment='center',fontproperties=font)
ax.annotate('B',[-1.2,-74],horizontalalignment='center',verticalalignment='center',fontproperties=font, annotation_clip=False)
ax3.annotate("N =",[-2.7,0.3],horizontalalignment='center',annotation_clip=False, weight='bold', size=12)


#PLOT settings
ax.annotate('Land',[0+width/2,-65],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
ax.annotate('Lake',[1+width/2,-25],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
ax.annotate('Tide',[2+width/2,-10],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
ax.axes.get_xaxis().set_visible(False)
ax.get_yaxis().tick_left()
ax.set_ylim([-77,0])
#plot_brace(ax,3.2,5.8,-32,5,up=False,annotate='Tidewater\nPartitioning',fontsize=10)

for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(11) 
xmin, xmax = ax.get_xaxis().get_view_interval()
ymin, ymax = ax.get_yaxis().get_view_interval()
ax.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=1.5))
ax.add_artist(Line2D((xmin, xmax), (0, 0), color='black', linewidth=1.))
ax.plot([xmin, xmax],[-74,-74],'--k')
ax.set_ylabel("Mass Balance (Gt a"+"$\mathregular{^{-1}}$)",fontsize=11,labelpad=0)

plt.show()
fig3.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/NewSuppfig1_to_map_shad2.jpg",dpi=300)