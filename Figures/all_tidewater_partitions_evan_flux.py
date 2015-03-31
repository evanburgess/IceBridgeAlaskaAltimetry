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

conn,cur = ConnectDb()


def hyp_med(hyps):
    cum = hyps['area'].cumsum()
    
    idx = N.abs(cum-(cum[-1]/2)).argmin()
    m,b = N.polyfit(hyps['bins'][idx-3:idx+3],(cum-(cum[-1]/2))[idx-3:idx+3],1)
    
    return -b/m

#cur.execute("select ergi.name,area::real as area,glnames.gid*0+1 as surv,eb_best_flx,bm_flux,ergi.glimsid from ergi left join glnames on ergi.glimsid=glnames.glimsid left join tidewater_flux as t on ergi.glimsid=t.glimsid where substring(glactype from 2 for 1) = '1' order by surv,ergi.area;")
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

######################################################
######################################################
######################################################
#PARTITION OF SURVEYED TIDEWATER GLACIERS 
print 'here'

myr = True
#hypsometry for all tidewater glaciers
tempglims = GetSqlData2("SELECT glimsid from ergi WHERE gltype='1'")['glimsid']

hypsoall=[]
for j,gid in enumerate(tempglims):
    #hypsoall.append(GetSqlData2("SELECT bins, SUM(ergibinned.area)/1000000.::real as area,AVG(ergi.area)::real as totalarea from ergibinned inner join ergi on ergibinned.glimsid=ergi.glimsid WHERE ergi.glimsid ='%s' group by bins order by bins;" % gid))
    
    hypsoall.append(GetSqlData2("SELECT bins, SUM(area)/1000000.::real as area from resultsauto WHERE glimsid ='%s' group by bins order by bins;" % gid))

#CALCULATING MEDIAN ELEVATION FOR EACH GLACIER
cur.execute("DROP TABLE IF EXISTS ebt;")
cur.execute("CREATE TABLE ebt (glimsid varchar (40),median real);")
for i,h in enumerate(hypsoall):
    hyp_med(h)
    cur.execute("INSERT INTO ebt (glimsid,median) VALUES ('%s', %s);" % (tempglims[i], hyp_med(h)))
conn.commit()

#INFO AND MEAN ELEVATION FOR TIDEWATER GLACIERS
if myr:orderby = 'e.region,ebt.median'
else:orderby = 'e.area DESC'
temp = GetSqlData2("SELECT e.glimsid,e.name,e.region,ebt.median,e.area::real,e from ergi as e inner join ebt on e.glimsid=ebt.glimsid WHERE e.gltype='1' order by %s;" % orderby)
cur.execute("DROP TABLE ebt;")
conn.commit()
#temp = GetSqlData2("SELECT glimsid,name,region from ergi WHERE ergi.gltype='1' and ergi.name != 'Taku Glacier' order by region,area;")
tideglims = temp['glimsid']
tidenames = list(temp['name'])
tideregion = temp['region']
tidenames = [re.sub(' Glacier','',x) for x in tidenames]   #removing ' glacier'
tidearea = temp['area']
tidemedian = temp['median']

#hypsometry for all tidewater glaciers
hypsoall=[]
for j,gid in enumerate(tideglims):
    hypsoall.append(GetSqlData2("SELECT bins::real, SUM(area)/1000000.::real as area, AVG(glarea)::real as totalarea from resultsauto WHERE glimsid ='%s' group by bins order by bins;" % gid))
    
    
#GETTING AREA ALTITUDE RATIO
aad = [N.sum(N.where(x['bins']>1000,x['area'],0))/x['totalarea'][0] for x in hypsoall]

#DATA FOR SURVEYED GLACIERS
d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True,results=True)
d.fix_terminus()
d.remove_upper_extrap()
d.normalize_elevation()

region=N.array(d.region)
name=N.array(d.name)
flx = d.eb_best_flx

flxerr = d.eb_high_flx.astype(float)-d.eb_low_flx.astype(float)
area = d.area
glimsid = N.array(d.glimsid)
terminvert = N.array([N.ma.mean(dz[0:11]) for dz in d.normdz])
length = d.bm_length.astype(float)


if myr:
    balmodel = d.rlt_totalkgm2
    balerr = N.array(d.rlt_singlerrkgm2).astype(float)
    flx = -d.eb_best_flx.astype(float)*1000./d.area
    flxerr =(d.eb_high_flx.astype(float)-d.eb_low_flx.astype(float))*1000./d.area
else:
    balmodel = d.rlt_totalgt
    balerr = N.array(d.rlt_singlerrkgm2).astype(float)
    flx = -d.eb_best_flx.astype(float)
    flxerr = d.eb_high_flx.astype(float)-d.eb_low_flx.astype(float)

# comverting to std from iqr  altimetry error
#balerr = (bal75diff-bal25diff)/1.394     

#calculating smb and smb error in quadrature
smb = balmodel - flx
smberror = (balerr**2+flxerr**2)**0.5

#matching the glacier bars with hypsometry 
xlocs = []
for glid in glimsid:xlocs.append(N.where(tideglims==glid)[0][0])

#FLUXES FOR ALL! TIDEWATER GLACIERS
flxs = GetSqlData2("SELECT e.name,e.area::real,e.glimsid,flx.eb_best_flx,flx.eb_bm_err,flx.eb_high_flx,flx.eb_best_flx,flx.eb_low_flx,flx.bm_flux,flx.bm_flx_err from ergi as e inner join tidewater_flux as flx on e.glimsid=flx.glimsid WHERE e.gltype='1' and e.name != 'Taku Glacier' AND flx.eb_best_flx != 'nan';")

flxlocs = []
for glid in flxs['glimsid']:
    flxlocs.append(N.where(tideglims==glid)[0][0])

#PLOTTING
fig2 = plt.figure(figsize=[14,8])
ax2 = fig2.add_axes([0.05,0.24,0.87,0.73])

plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

bar1 = ax2.bar(xlocs,balmodel,color='r',width=0.2,yerr=balerr,ecolor='k')
bar3 = ax2.bar(N.array(xlocs)+0.4,smb,color='g',width=0.2,yerr=smberror,ecolor='k')
if myr:bar2 = ax2.bar(N.array(flxlocs)+0.2,-flxs['eb_best_flx']*1000/flxs['area'],color='b',width=0.2,ecolor='k',yerr=-flxs['eb_bm_err']*1000/flxs['area'],zorder=1)
else:bar2 = ax2.bar(N.array(flxlocs)+0.2,-flxs['eb_best_flx'],color='b',width=0.2,ecolor='k',yerr=-flxs['eb_bm_err'],zorder=1)

#GLACIER NAME LABELS
#removing NULL glacier
tidenames = list(N.where(N.array(tidenames)=="NULL","Unnamed",tidenames))

ax2.set_xticks(N.arange(len(tidenames))+0.3)
lbls = ax2.set_xticklabels(tidenames)
for lbl in lbls:lbl.set_rotation(90)

#LINES BETWEEN EACH GLACIER
for i in arange(len(tideglims))-0.2:ax2.plot([i,i],[-10,10],':',color=(0.5,0.5,0.5,1))

#LINES AND NAMES SEPARATING REGIONS
if myr:
    switch = [False]
    switch.extend(list(tideregion[0:-1]!=tideregion[1:]))
    divisions=N.where(N .array(switch))[0]
    for i in divisions-0.2:ax2.plot([i,i],[-10,10],'-k')
    
    regionlist = list(set(tideregion))
    regionlist.sort()
    regionlist = [re.sub(' ','\n',x) for x in regionlist]
    divisions2 = [0]
    divisions2.extend(list(divisions))
    for i in xrange(len(divisions2)): 
        if i == 2:yreg = 4.8
        else:yreg = 5.7
        print regionlist[i] == 'Juneau\nIcefield',regionlist[i],yreg
        ax2.annotate(regionlist[i],[divisions2[i]-0.1,yreg],verticalalignment='top')

#if not myr:
#    cumarea = N.cumsum(tidearea)
#    survcumarea = N.cumsum(tidearea * N.array([i in d.glimsid for i in tideglims]).astype(int))
#    #PLOTTING CUMULATIVE AREA
#    ax3 = ax2.twinx()      
#    ax3.set_ylim([0,100])
#    ax3.set_ylabel('Cumulative Area of Tidewater Glaciers (%)')
#    ax3.plot(N.arange(len(cumarea)),cumarea/cumarea[-1]*100,'k-')
#    ax3.plot(N.arange(len(cumarea)),survcumarea/cumarea[-1]*100,'r-')
#else:
#    ax3 = ax2.twinx()   
#    
#    #PLOTTING TERMINUS DYNAMICS
#    ax3.plot(N.array(xlocs)+0.3,terminvert,'om',label='Terminus Thickness Change (m)')  
#    ax3.plot(N.array(xlocs)+0.3,length*10,'oc',label='Terminus Length Change (km*10)')  
#    ax3.set_ylim([-25,25])
#    ax3.set_ylabel('Terminus Change')
#    ax3.legend(loc='lower center')  
      
#FIGURE SETTINGS 
ax2.set_xlim(ax2.get_xlim()[0]-1,ax2.get_xlim()[1]+1)
ax2.set_ylim([-6,6])
ax2.legend((bar1[0], bar2[0], bar3[0]), ('Mass Balance', 'Calving Flux', 'SMB'),loc='lower right')
if myr:ax2.set_ylabel('m w. eq. year'+"$\mathregular{^{-1}}$")
else:ax2.set_ylabel('Gt')

#select glimsid, SUM(eb.area*eb.bins)/SUM(eb.area) as mnelev group by glimsid;

#PLOTTING THE HYPSOMETRY GIVING ABOVE AND BELOW THE ELA DIFFERENT COLORS AND ABOVE THE ELA GREEN IF THE AAD IS GREATER THAN 0.8 ()
ax3 = ax2.twinx()  
fig2.axes.reverse() # reorder 
for i,h in enumerate(hypsoall):
    whigh = N.where(h['bins']>000)
    wlow = N.where(h['bins']<=000)
    #if aad[i]>0.8:
    #    hbars = ax3.barh(h['bins'][whigh]/600.,h['area'][whigh]/N.max(h['area']),left=i-0.2,color=(0.7,0.7,1,1),height=0.05, edgecolor=(0.7,0.7,1,1),zorder=0)
    #else:
    hbars = ax3.barh(h['bins'][whigh],h['area'][whigh]/N.max(h['area']),left=i-0.2,color=(0.7,0.7,0.7,1),height=30, edgecolor=(0.7,0.7,0.7,1),zorder=0,linewidth=0)
    hbars = ax3.barh(h['bins'][wlow],h['area'][wlow]/N.max(h['area']),left=i-0.2,color=(0.85,0.85,0.85,1),height=30, edgecolor=(0.85,0.85,0.85,1),zorder=0,linewidth=0)


#PLOTTING ASTERISKS BY GLACIERS WITH RECORDS SHORTER THAN 5 YEARS

ax2.plot(N.array([12,13,47,48])+0.2,N.zeros(4)-3,'k*')

ax3.set_ylim(-4000,4000)
ax3.yaxis
plt.text(51,2600,"Elevation (m)", rotation=-90)

for i,m in enumerate(tidemedian):bar = ax3.plot([i-0.2,i+0.8],[m,m],'-k',zorder=0.4)

print fig2.axes

print fig2.axes
#ax2.set_frame_on(False) 
#ax3.set_frame_on(False) 

ax2.plot([-5,60],[-0.921,-0.921],'r-',zorder=0,alpha=0.5)
ax2.plot([-5,60],[0.,0],'k-',zorder=0)
ax3.set_yticks([0,1000,2000,3000,4000])
plt.show()
if myr:outfile = "/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/tidewater2_partition_myr2.jpg"
else:outfile = "/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/tidewater2_partition_gt2.jpg"

fig2.savefig(outfile,dpi=300)
#####################################################################
#####################################################################
#THIS SECTION UPDATES THE tidewater_flux TABLE WITH THE NEW SMB DATA
#####################################################################
cur.execute("ALTER TABLE tidewater_flux DROP COLUMN IF EXISTS smb;")
cur.execute("ALTER TABLE tidewater_flux ADD COLUMN smb real;")
for i in xrange(len(smb)):
    if not N.isnan(smb[i]):cur.execute("UPDATE tidewater_flux SET smb=%s WHERE glimsid='%s';" % (smb[i],glimsid[i]))
conn.commit()
cur.close()
conn.close() 