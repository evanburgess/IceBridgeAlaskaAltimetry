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

def plot_brace(ax,left,right,y,height,up=True,color='k',annotate=None):
    if up:hgt = height/2.
    else: hgt = -height/2.
    
    mid = (left+right)/2.
    
    brace,tip = ax.plot([left,left,right,right],[y-hgt,y,y,y-hgt],'-%s' % color,[mid,mid],[y,y+hgt],'-%s' % color)
    if type(annotate)!=NoneType:
        if up:vert='bottom'
        else:vert='top'
        txt = ax.annotate(annotate,[mid,y+hgt*1.2],horizontalalignment='center',verticalalignment=vert)
        return brace,tip,txt
    else:
        return brace,tip
    

d = GetSqlData2("SELECT gltype,surveyed,SUM(mean*area)/SUM(area)*0.85 as myr,SUM(mean*area)/1000000000.*0.85 as gt,((SUM(sem*area)/SUM(area))^2+0.06^2)^0.5 as myrerr,((SUM(sem*area)/1000000000.)^2+0.06^2)^0.5 as gterr,sum(area)/1000000.::real as area from resultsauto group by gltype,surveyed order by gltype,surveyed;")

lamb = GetLambData(longest_interval=True,userwhere="ergi.gltype='1' and ergi.name != 'Taku Glacier'", as_object=True, orderby='glimsid')

totaltide = GetSqlData2("SELECT SUM(mean*area)/1000000000.::real*0.85 as gt,((SUM(sem*area)/1000000000.::real)^2+0.06^2)^0.5 as gterr from resultsauto where gltype='1'")

#PARTITIONING TIDEWATERS
#getting total mass balance for these glaciers
tidewatergts = GetSqlData2("SELECT SUM(mean*area)/1e9*0.85 as gt from resultsauto where glimsid in ('%s') group by glimsid;" % "','".join(lamb.glimsid))['gt']
smb = tidewatergts + lamb.eb_bm_flx.astype(float)

volerr = (lamb.vol75diff-lamb.vol25diff)/1.394     # comverting to std from iqr
smberror = (volerr**2+lamb.eb_bm_err.astype(float)**2)**0.5



fig = plt.figure(figsize=[8,3])

colors = [[1,0.8,0.8],[1,0,0],[0.8,0.8,1],[0,0,1],[0.8,1,0.8],[0,1,0]]
#classes = ['Land/NotSurv','Land/Surv','Tide/NotSurv','Tide/Surv','Lake/NotSurv','Lake/Surv']
#offset = 0
#for i,result in enumerate(results):
#    #trash,trash,val,err = zip(*sorted(zip(result['results']['bytype_survey']['gltype'],result['results']['bytype_survey']['surveyed'],result['results']['bytype_survey']['totalgt'],result['results']['bytype_survey']['errgt'])))
#    
barlocs = [0,1,4,5,2,3]
axwidth=0.23
#PLOTTING Mass Balance(m w. eq.)
ax = fig.add_axes([0.09,0.1,axwidth,0.8],frameon=False)
pl1 = ax.bar(barlocs, d['myr'], color=colors, width=1,yerr=d['myrerr'],error_kw=dict(ecolor='k'))
print barlocs, d['myr']

ax.axes.get_xaxis().set_visible(False)
ax.get_yaxis().tick_left()
ax.set_ylim([-1.6,0.2])
ax.set_xlim([-0.4,6.4])
ax.set_ylabel("Mass Balance (m w. eq. a"+"$^{-1}$"+")",fontsize=11)
for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(11) 
xmin, xmax = ax.get_xaxis().get_view_interval()
ymin, ymax = ax.get_yaxis().get_view_interval()
ax.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=2))

#PLOTTING Mass Balance(Gt)
ax2 = fig.add_axes([axwidth+0.2,0.1,0.54,0.8],frameon=False)
pl1 = ax2.bar(barlocs, d['gt'], color=colors, width=1,yerr=d['gterr'],error_kw=dict(ecolor='k'))
ax2.axes.get_xaxis().set_visible(False)
#ax2.get_yaxis().tick_left()
ax2.set_ylim([-60,10])
ax2.set_xlim([0,13])
ax2.set_ylabel("Mass Balance (Gt a"+"$^{-1}$"+")",fontsize=11)
for tick in ax2.yaxis.get_major_ticks():tick.label.set_fontsize(11) 
xmin, xmax = ax2.get_xaxis().get_view_interval()
ymin, ymax = ax2.get_yaxis().get_view_interval()
ax2.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=2))
ax2.add_artist(Line2D((xmax, xmax), (ymin, ymax), color='black', linewidth=2))
ax2.add_artist(Line2D((xmin, xmax), (ymax, ymax), color='black', linewidth=2))
##PLOTTING Partitioning
#ax3 = fig.add_axes([0.10,0.10,0.9,0.5])
#
#bar1 = ax3.bar(N.arange(len(lamb.name)),lamb.volmodel,color='r',width=0.2,yerr=volerr,ecolor='k')
#bar2 = ax3.bar(N.arange(len(lamb.name))+0.2,-lamb.eb_bm_flx.astype(float),color='b',width=0.2,yerr=lamb.eb_bm_err.astype(float),ecolor='k')
#bar3 = ax3.bar(N.arange(len(lamb.name))+0.4,smb,color='g',width=0.2,yerr=smberror,ecolor='k')
#ax3.set_xticks(N.arange(len(lamb.name))+0.3)
#ax3.set_ylabel("Gt a"+"$^{-1}$")
#name = [re.sub(' Glacier','',x) for x in lamb.name]
#lbls = ax3.set_xticklabels(name)
#for lbl in lbls:lbl.set_rotation(90)
#ax3.set_xlim([0,22])
##
#PLOTTING FULL PARTITIONING
width = 0.6
#ax4 = fig.add_axes([axwidth*2+0.15,0.1,axwidth,0.8])
#ax4.set_xlim([0.7,4.9])


w = N.where(N.isnan(lamb.eb_bm_flx.astype(float))==False)[0]

bothflx=-N.sum(lamb.eb_bm_flx.astype(float)[w])
bothflxerr=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5
bothvol=N.sum(lamb.volmodel[w])
bothvolerr=N.sum(volerr[w]**2)**0.5
bothsmberr = N.sum(smberror[w]**2)**0.5
bothsmb=N.sum(smb[w])

bothname=[lamb.name[i] for i in w]

b1,b2,b3 = ax2.bar([7,8.5,10],[bothsmb,bothflx,bothvol],yerr=[bothsmberr,bothflxerr,bothvolerr],width=width,ecolor='k') # 

ax2.annotate('SMB',[7+width,-4],rotation=90,horizontalalignment='center',verticalalignment='top')
ax2.annotate('Calving',[8.5+width,-16],rotation=90,horizontalalignment='center',verticalalignment='top')
ax2.annotate('Net',[10+width,-11],rotation=90,horizontalalignment='center',verticalalignment='top')
ax2.annotate('Unpartitioned',[11.3+width,-4],rotation=90,horizontalalignment='center',verticalalignment='top')

#
w = N.where(N.logical_and(N.isnan(lamb.eb_bm_flx.astype(float))==False,N.array([x!='Columbia Glacier' for x in lamb.name])))[0]

bothflx2=-N.sum(lamb.eb_bm_flx.astype(float)[w])
bothflxerr2=N.sum((lamb.eb_bm_err.astype(float)[w])**2)**0.5
bothsmb2=N.sum(smb[w])
bothvolerr2=N.sum(volerr[w]**2)**0.5
bothsmberr2 = N.sum(smberror[w]**2)**0.5
bothvol2=N.sum(lamb.volmodel[w])
bothname2=[lamb.name[i] for i in w]
b1,b2,b3 = ax2.bar(N.array([7,8.5,10])+width,[bothsmb2,bothflx2,bothvol2],color=[0.7,0.7,1],yerr=[bothsmberr2,bothflxerr2,bothvolerr2],width=width,ecolor='k') # yerr=volerr,

b4 = ax2.bar(11.5,totaltide['gt']-bothvol,color=[0,0,1],width=width,ecolor='k') # yerr=volerr,

p1 = ax2.plot([0,13],[0,0],'-k')
plot_brace(ax2,7,12.1,-50,5,up=False,annotate='Tidewater\nPartitioning')
#ax4.axes.get_xaxis().set_visible(False)
#ax4.get_yaxis().tick_left()
#ax4.set_ylim([-60,10])
#ax4.set_ylabel("Gt a"+"$^{-1}$")
#
#
#ax4.set_xticks(N.array([7,8,9,10])+width)
#lbls = ax4.set_xticklabels(['SMB','Calving','Net','Unpartitioned'])
#for lbl in lbls:lbl.set_rotation(90)


#xmin, xmax = ax4.get_xaxis().get_view_interval()
#ymin, ymax = ax4.get_yaxis().get_view_interval()
#ax4.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=2))


fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/partition.jpg",dpi=300)


plt.show()





#conn,cur = ConnectDb()



#
#cur.execute("select ergi.name,area::real as area,glnames.gid*0+1 as surv,eb_bm_flx,bm_flux,ergi.glimsid from ergi left join glnames on ergi.glimsid=glnames.glimsid left join tidewater_flux as t on ergi.glimsid=t.glimsid where substring(glactype from 2 for 1) = '1' order by surv,ergi.area;")
#name,area,surv,ebbm,bm,glimsid = zip(*cur.fetchall())
#
#surv2 = N.array(surv,dtype=bool)
#name = [re.sub(' Glacier','',x) for x in name]
#
#glimslist = "'%s'" % "','".join(N.array(glimsid)[N.where(N.array(surv)==1)])
#
#p = GetLambData(longest_interval=True,userwhere= "ergi.glimsid IN (%s)" % glimslist,as_object=True)
#
#
#
#balmodel = N.zeros(len(glimsid))
#date1 = []
#date2 = []
#color_vals = [-2, 0, 2]
#for i,x in enumerate(glimsid):
#    print x
#    w = N.where(N.array(p.glimsid)==x)[0]
#    if len(w) == 1: balmodel[i]=p.balmodel[w]
#    if len(w) == 1: date1.append(p.date1[w]) 
#    else: date1.append(None)
#    if len(w) == 1: date2.append(p.date2[w]) 
#    else: date2.append(None)
#    
#
#    
#    
#norm = matplotlib.colors.Normalize(-2,2) # maps your data to the range [0, 1]
#cmap = matplotlib.cm.get_cmap('RdBu') # can pick your color map
#
#color=N.array(cmap(norm(balmodel)))
#wclr = N.where(balmodel==0)
#color[wclr] = [0.4,0.4,0.4,1]

########################################################
##PIE CHART OF SURV/UNSURV GLACIERS AND FLUXES
#fig = plt.figure(figsize=[8,8])
#ax1 = fig.add_axes([0.05,0.17,0.65,0.65])
#
#pie = ax1.pie(area,labels=name,explode=abs(surv2.astype(float)-1)/9., colors=color,labeldistance=1.01)
#labelpostions = [x.get_position() for x in pie[1]]
#
#plt.clf()
#ax1 = fig.add_axes([0.05,0.17,0.65,0.65])
#pie = ax1.pie(area,labels=name,explode=abs(surv2.astype(float)-1)/9., colors=color,labeldistance=1.2)
#for i,circ in enumerate(labelpostions):
#    if ebbm[i]!=None:
#        circle1=plt.Circle(circ,ebbm[i]**0.5/10,color='r',zorder=-1)
#        pth = ax1.add_patch(circle1)
#for j,x in enumerate(pie[1]): 
#    if area[j]<50:
#        x.set_fontsize(5)
#        x.set_rotation(-55)
#    else:
#        x.set_fontsize(10)
#        
#ax1.set_title("Surveyed/Unsurveyed Tidewater Glaciers by Area")
#
#ax_cb = fig.add_axes([.9,.25,.03,.5])
#cb = mpl.colorbar.ColorbarBase(ax_cb, cmap=cmap, norm=norm, ticks=color_vals)
#cb.set_label('Lamb Balance (m/yr)')    
#fig.savefig("/Users/igswahwsmcevan/Altimetry/results/tidewatersurvey.jpg",dpi=300)
#    
#
#plt.show()
#
#
##FOR BOBO
#for i in xrange(len(name)):print "%s,%s,%s" % (name[i],date1[i],date2[i])
#
######################################################
##PARTITION OF SURVEYED TIDEWATER GLACIERS 
#
#
#d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1' and ergi.name != 'Taku Glacier'", as_object=True)
#
#for i,x in enumerate(d.eb_bm_flx):
#    if x==None: d.eb_bm_flx[i]=N.nan
#d.eb_bm_flx =-d.eb_bm_flx.astype(float)
#
#z = zip(d.region,d.name,d.volmodel,d.vol25diff,d.vol75diff,d.eb_bm_flx,d.eb_bm_err,d.area,d.glimsid)
#z.sort()
#region,name,volmodel,vol25diff,vol75diff,flx,flxerr,area,glimsid = zip(*z)
#
#area=N.array(area)
#flx=N.array(flx)
#volmodel=N.array(volmodel)
#region=N.array(region)
#name=N.array(name)
#vol25diff=N.array(vol25diff)
#vol75diff=N.array(vol75diff)
#flxerr=N.array(flxerr)
#glimsid=N.array(glimsid)
#
#
#volerr = (vol75diff-vol25diff)/1.394     # comverting to std from iqr
#
##calculating smb and smb error in quadrature
#smb = volmodel - flx
#smberror = (volerr**2+flxerr**2)**0.5
#
##removing ' glacier'
#name = [re.sub(' Glacier','',x) for x in name]
#
##PLOTTING
#fig2 = plt.figure(figsize=[14,8])
#ax2 = fig2.add_axes([0.1,0.17,0.85,0.75])
#
#
#bar1 = ax2.bar(N.arange(len(name)),volmodel,color='r',width=0.2,yerr=volerr,ecolor='k')
#bar2 = ax2.bar(N.arange(len(name))+0.2,flx,color='b',width=0.2,yerr=flxerr,ecolor='k')
#bar3 = ax2.bar(N.arange(len(name))+0.4,smb,color='g',width=0.2,yerr=smberror,ecolor='k')
#
#ax2.set_xticks(N.arange(len(name))+0.3)
#
##LINES BETWEEN EACH GLACIER
#for i in arange(len(name))-0.2:ax2.plot([i,i],[-10,10],':',color=(0.5,0.5,0.5,1))
#
##LINES AND NAMES SEPARATING REGIONS
#switch = [False]
#switch.extend(list(region[0:-1]!=region[1:]))
#divisions=N.where(N.array(switch))[0]
#for i in divisions-0.2:ax2.plot([i,i],[-10,10],'-k')
#
#regionlist = list(set(region))
#regionlist.sort()
#regionlist = [re.sub(' ','\n',x) for x in regionlist]
#divisions2 = [0]
#divisions2.extend(list(divisions))
#for i in xrange(len(divisions2)): ax2.annotate(regionlist[i],[divisions2[i]-0.1,5.5],verticalalignment='top')
#
##FIGURE SETTINGS 
#ax2.set_xlim(ax2.get_xlim()[0]-1,ax2.get_xlim()[1]+1)
#ax2.set_ylim([-6,6])
#
#ax2.legend((bar1[0], bar2[0], bar3[0]), ('Altimetry', 'Flux', 'SMB'))
#ax2.set_ylabel('Gt/yr')
#
#lbls = ax2.set_xticklabels(name)
#for lbl in lbls:lbl.set_rotation(90)
#
#hypso=[]
#for j,gid in enumerate(glimsid):
#    hypso.append(GetSqlData2("SELECT bin, SUM(area)/1000000. as area from ergibinned WHERE glimsid IN ('%s') group by bin order by bin;" % gid))
#
#
#for i,h in enumerate(hypso):hbars = ax2.barh(h['bin']/600.,h['area']/N.max(h['area']),left=i-0.2,color=(0.9,0.9,0.9,1),height=0.05, edgecolor=(0.9,0.9,0.9,1),zorder=0)
#
#
#for i,h in enumerate(hypso):
#    meanelev = N.sum(h['bin']*h['area'])/N.sum(h['area'])/600.
#    bar = ax2.plot([i-0.2,i+0.8],[meanelev,meanelev],'-k',zorder=0.4)
#
#
#plt.show()
#fig2.savefig("/Users/igswahwsmcevan/Altimetry/results/tidewater_partition_gt.jpg",dpi=300)
##
#
#######################################################
##PARTITION OF SURVEYED TIDEWATER GLACIERS 
#d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1' and ergi.name != 'Taku Glacier'", as_object=True)
#
#for i,x in enumerate(d.eb_bm_flx):
#    if x==None: d.eb_bm_flx[i]=N.nan
#d.eb_bm_flx =-d.eb_bm_flx.astype(float)
#
#z = zip(d.region,d.name,d.balmodel,d.bal25diff,d.bal75diff,d.eb_bm_flx,d.eb_bm_err,d.area,d.glimsid)
#z.sort()
#region,name,balmodel,bal25diff,bal75diff,flx,flxerr,area,glimsid = zip(*z)
#
#area=N.array(area)
#flx=N.array(flx)*1000000000./area
#balmodel=N.array(balmodel)
#region=N.array(region)
#name=N.array(name)
#bal25diff=N.array(bal25diff)
#bal75diff=N.array(bal75diff)
#flxerr=N.array(flxerr)
#glimsid=N.array(glimsid)
#
#
#balerr = (bal75diff-bal25diff)/1.394     # comverting to std from iqr
#
##calculating smb and smb error in quadrature
#smb = balmodel - flx
#smberror = (balerr**2+flxerr**2)**0.5
#
##removing ' glacier'
#name = [re.sub(' Glacier','',x) for x in name]
#
#
##PLOTTING
#fig2 = plt.figure(figsize=[14,8])
#ax2 = fig2.add_axes([0.1,0.17,0.85,0.75])
#
#
#bar1 = ax2.bar(N.arange(len(name)),balmodel,color='r',width=0.2,yerr=balerr,ecolor='k')
#bar2 = ax2.bar(N.arange(len(name))+0.2,flx,color='b',width=0.2,yerr=flxerr,ecolor='k')
#bar3 = ax2.bar(N.arange(len(name))+0.4,smb,color='g',width=0.2,yerr=smberror,ecolor='k')
#
#ax2.set_xticks(N.arange(len(name))+0.3)
#
##LINES BETWEEN EACH GLACIER
#for i in arange(len(name))-0.2:ax2.plot([i,i],[-10,10],':',color=(0.5,0.5,0.5,1))
#
##LINES AND NAMES SEPARATING REGIONS
#switch = [False]
#switch.extend(list(region[0:-1]!=region[1:]))
#divisions=N.where(N .array(switch))[0]
#for i in divisions-0.2:ax2.plot([i,i],[-10,10],'-k')
#
#regionlist = list(set(region))
#regionlist.sort()
#regionlist = [re.sub(' ','\n',x) for x in regionlist]
#divisions2 = [0]
#divisions2.extend(list(divisions))
#for i in xrange(len(divisions2)): ax2.annotate(regionlist[i],[divisions2[i]-0.1,5.5],verticalalignment='top')
#
##FIGURE SETTINGS 
#ax2.set_xlim(ax2.get_xlim()[0]-1,ax2.get_xlim()[1]+1)
#ax2.set_ylim([-6,6])
#
#ax2.legend((bar1[0], bar2[0], bar3[0]), ('Altimetry', 'Flux', 'SMB'))
#ax2.set_ylabel('m/yr')
#
#lbls = ax2.set_xticklabels(name)
#for lbl in lbls:lbl.set_rotation(90)
#
#hypso=[]
#for j,gid in enumerate(glimsid):
#    hypso.append(GetSqlData2("SELECT bin, SUM(ergibinned.area)/1000000. as area,AVG(ergi.area)::real as totalarea from ergibinned inner join ergi on ergibinned.glimsid=ergi.glimsid WHERE ergibinned.glimsid ='%s' group by bin order by bin;" % gid))
#
#
#for i,h in enumerate(hypso):hbars = ax2.barh(h['bin']/600.,h['area']/N.max(h['area']),left=i-0.2,color=(0.9,0.9,0.9,1),height=0.05, edgecolor=(0.9,0.9,0.9,1),zorder=0)
#
#
#for i,h in enumerate(hypso):
#    meanelev = N.sum(h['bin']*h['area'])/N.sum(h['area'])/600.
#    bar = ax2.plot([i-0.2,i+0.8],[meanelev,meanelev],'-k',zorder=0.4)
#
#
#plt.show()
#fig2.savefig("/Users/igswahwsmcevan/Altimetry/results/tidewater_partition_m.jpg",dpi=300)

######################################################
##PARTITION OF SURVEYED TIDEWATER GLACIERS 
#
#myr = True
##data for surveyed glaciers
#d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True)
#
#for i,x in enumerate(d.eb_bm_flx):
#    if x==None: d.eb_bm_flx[i]=N.nan
#d.eb_bm_flx =-d.eb_bm_flx.astype(float)
#if myr:
#    z = zip(d.region,d.name,d.balmodel,d.bal25diff,d.bal75diff,d.eb_bm_flx,d.eb_bm_err.astype(float),d.area,d.glimsid)
#
#else:
#    z = zip(d.region,d.name,d.volmodel,d.vol25diff,d.vol75diff,d.eb_bm_flx,d.eb_bm_err.astype(float),d.area,d.glimsid)
#    
#z.sort()
#region,name,balmodel,bal25diff,bal75diff,flx,flxerr,area,glimsid = zip(*z)
#
#area=N.array(area)
#if myr:
#    flx=N.array(flx)*1000./area
#    flxerr=N.array(flxerr)*1000./area
#else:
#    flx=N.array(flx)
#    flxerr=N.array(flxerr)
#    
#balmodel=N.array(balmodel)
#region=N.array(region)
#name=N.array(name)
#bal25diff=N.array(bal25diff)
#bal75diff=N.array(bal75diff)
#
#glimsid=N.array(glimsid)
#
#balerr = (bal75diff-bal25diff)/1.394     # comverting to std from iqr
#
##calculating smb and smb error in quadrature
#smb = balmodel - flx
#smberror = (balerr**2+flxerr**2)**0.5
#
#
##hypsometry for all tidewater glaciers
#if myr:orderby = 'e.region,ebt.mnelev'
#else:orderby = 'e.area DESC'
#temp = GetSqlData2("SELECT e.glimsid,e.name,e.region,ebt.mnelev,e.area::real,e from ergi as e inner join (select glimsid, SUM(eb.area*eb.bins)/SUM(eb.area) as mnelev from ergibinned as eb group by glimsid) as ebt on e.glimsid=ebt.glimsid WHERE e.gltype='1' order by %s;" % orderby)
##temp = GetSqlData2("SELECT glimsid,name,region from ergi WHERE ergi.gltype='1' and ergi.name != 'Taku Glacier' order by region,area;")
#tideglims = temp['glimsid']
#tidenames = list(temp['name'])
#tideregion = temp['region']
#tidenames = [re.sub(' Glacier','',x) for x in tidenames]   #removing ' glacier'
#tidearea = temp['area']
#
#
#hypsoall=[]
#for j,gid in enumerate(tideglims):
#    hypsoall.append(GetSqlData2("SELECT bins, SUM(ergibinned.area)/1000000.::real as area,AVG(ergi.area)::real as totalarea from ergibinned inner join ergi on ergibinned.glimsid=ergi.glimsid WHERE ergibinned.glimsid ='%s' group by bins order by bins;" % gid))
#
##GETTING AREA ALTITUDE RATIO
#aad = [N.sum(N.where(x['bins']>1000,x['area'],0))/x['totalarea'][0] for x in hypsoall]
#
#
##matching hypsometry with the glacier bars
#xlocs = []
#for glid in glimsid:
#    xlocs.append(N.where(tideglims==glid)[0][0])
#
##FLUXES FOR ALL! TIDEWATER GLACIERS
#flxs = GetSqlData2("SELECT e.name,e.area::real,e.glimsid,flx.eb_bm_flx,flx.eb_bm_err,flx.eb_high_flx,flx.eb_best_flx,flx.eb_low_flx,flx.bm_flux,flx.bm_flx_err from ergi as e inner join tidewater_flux as flx on e.glimsid=flx.glimsid WHERE e.gltype='1' and e.name != 'Taku Glacier' AND flx.eb_bm_flx != 'nan';")
#
#flxlocs = []
#for glid in flxs['glimsid']:
#    flxlocs.append(N.where(tideglims==glid)[0][0])
#    
##PLOTTING
#fig2 = plt.figure(figsize=[14,8])
#ax2 = fig2.add_axes([0.1,0.17,0.85,0.75])
#
#
#bar1 = ax2.bar(xlocs,balmodel,color='r',width=0.2,yerr=balerr,ecolor='k')
##bar2 = ax2.bar(N.array(xlocs)+0.2,flx,color='b',width=0.2,yerr=flxerr,ecolor='k')
#bar3 = ax2.bar(N.array(xlocs)+0.4,smb,color='g',width=0.2,yerr=smberror,ecolor='k')
#if myr:
#    bar2 = ax2.bar(N.array(flxlocs)+0.2,-flxs['eb_bm_flx']*1000/flxs['area'],color='b',width=0.2,ecolor='k',yerr=-flxs['eb_bm_err']*1000/flxs['area'])
#else:
#    bar2 = ax2.bar(N.array(flxlocs)+0.2,-flxs['eb_bm_flx'],color='b',width=0.2,ecolor='k',yerr=-flxs['eb_bm_err'])
#
##GLACIER NAME LABELS
#ax2.set_xticks(N.arange(len(tidenames))+0.3)
#lbls = ax2.set_xticklabels(tidenames)
#for lbl in lbls:lbl.set_rotation(90)
#
##LINES BETWEEN EACH GLACIER
#for i in arange(len(tideglims))-0.2:ax2.plot([i,i],[-10,10],':',color=(0.5,0.5,0.5,1))
#
##LINES AND NAMES SEPARATING REGIONS
#if myr:
#    switch = [False]
#    switch.extend(list(tideregion[0:-1]!=tideregion[1:]))
#    divisions=N.where(N .array(switch))[0]
#    for i in divisions-0.2:ax2.plot([i,i],[-10,10],'-k')
#    
#    regionlist = list(set(tideregion))
#    regionlist.sort()
#    regionlist = [re.sub(' ','\n',x) for x in regionlist]
#    divisions2 = [0]
#    divisions2.extend(list(divisions))
#    for i in xrange(len(divisions2)): ax2.annotate(regionlist[i],[divisions2[i]-0.1,5.5],verticalalignment='top')
#
#if not myr:
#    cumarea = N.cumsum(tidearea)
#    survcumarea = N.cumsum(tidearea * N.array([i in d.glimsid for i in tideglims]).astype(int))
#
#    ax3 = ax2.twinx()      
#    ax3.set_ylim([0,100])
#    ax3.set_ylabel('Cumulative Area of Tidewater Glaciers (%)')
#    ax3.plot(N.arange(len(cumarea)),cumarea/cumarea[-1]*100,'k-')
#    ax3.plot(N.arange(len(cumarea)),survcumarea/cumarea[-1]*100,'r-')
#
##FIGURE SETTINGS 
#ax2.set_xlim(ax2.get_xlim()[0]-1,ax2.get_xlim()[1]+1)
#ax2.set_ylim([-6,6])
#
#ax2.legend((bar1[0], bar2[0], bar3[0]), ('Altimetry', 'Flux', 'SMB'),loc='lower right')
#if myr:ax2.set_ylabel('m/yr')
#else:ax2.set_ylabel('Gt')
#
##select glimsid, SUM(eb.area*eb.bins)/SUM(eb.area) as mnelev group by glimsid;
#
##PLOTTING THE HYPSOMETRY GIVING ABOVE AND BELOW THE ELA DIFFERENT COLORS AND ABOVE THE ELA GREEN IF THE AAD IS GREATER THAN 0.8 ()
#for i,h in enumerate(hypsoall):
#    whigh = N.where(h['bins']>1000)
#    wlow = N.where(h['bins']<=1000)
#    if aad[i]>0.8:
#        hbars = ax2.barh(h['bins'][whigh]/600.,h['area'][whigh]/N.max(h['area']),left=i-0.2,color=(0.7,0.7,1,1),height=0.05, edgecolor=(0.7,0.7,1,1),zorder=0)
#    else:
#        hbars = ax2.barh(h['bins'][whigh]/600.,h['area'][whigh]/N.max(h['area']),left=i-0.2,color=(0.7,0.7,0.7,1),height=0.05, edgecolor=(0.7,0.7,0.7,1),zorder=0)
#
#    hbars = ax2.barh(h['bins'][wlow]/600.,h['area'][wlow]/N.max(h['area']),left=i-0.2,color=(0.85,0.85,0.85,1),height=0.05, edgecolor=(0.85,0.85,0.85,1),zorder=0)
#
#for i,h in enumerate(hypsoall):
#    meanelev = N.sum(h['bins']*h['area'])/N.sum(h['area'])/600.
#    bar = ax2.plot([i-0.2,i+0.8],[meanelev,meanelev],'-k',zorder=0.4)
#
#
#plt.show()
#if myr:outfile = "/Users/igswahwsmcevan/Altimetry/results/tidewater2_partition_myr.jpg"
#else:outfile = "/Users/igswahwsmcevan/Altimetry/results/tidewater2_partition_gt.jpg"
#    
#fig2.savefig(outfile,dpi=300)
