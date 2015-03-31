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

def loglin(x,y,extend=None):
    corr = scipy.stats.pearsonr(N.log(x), y)
    z = N.polyfit(N.log(x), y, 1)
    f = N.poly1d(z)
    
    if type(extend)==NoneType:
        x_new = N.linspace(N.log(N.min(x)),N.log(N.max(x)), 50)
        #print [N.log(N.min(x)),N.log(N.max(x))]
    else:
        x_new = N.linspace(N.log(extend[0]),N.log(extend[1]), 50)
        #print 'extend',[N.log(extend[0]),N.log(extend[1])]
    y_new = f(x_new)
    
    return z,x_new,y_new,corr
    
conn,cur = ConnectDb()

totalarea = GetSqlData2("SELECT SUM(area)::real as totalarea FROM temp1;")['totalarea']

#cur.execute("select ergi.glimsid,ergi.area,ergi.albersgeom,rlt.bal,rlt.surveyed,rlt.gltype,ergi.name into temp1 from ergi inner join (SELECT glimsid, SUM(mean*area)/SUM(area)*0.85 as bal, every(surveyed) as surveyed, AVG(gltype::real) as gltype from resultsauto group by glimsid) as rlt on ergi.glimsid=rlt.glimsid;")
#cur.commit()

lm=0.17
bm=0.07
h=0.28
w=0.7
mb = 0.02

colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.

fig = plt.figure(figsize=[4,8])
ax = fig.add_axes([lm,bm,w,h])
ax2 = fig.add_axes([lm,bm+h+mb,w,h])
ax1 = fig.add_axes([lm,bm+h*2+mb*2,w,h])

ax.set_xscale('log')
ax1.set_xscale('log')
ax2.set_xscale('log')

plt.rc("font", **{"sans-serif": ["Arial"],"size": 10})


####################################
#NOT SURVEYED
####################################
markersz = 5
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=1;")
ax.plot(d['area'],d['bal'],'.b',markersize=markersz,alpha=0.7,markeredgewidth=0.01,color=colors[2])#b)
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k')

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=0;")
ax1.plot(d['area'],d['bal'],'.r',markersize=markersz,alpha=0.1,markeredgewidth=0.01,color=colors[1])#r
z_u1,x_new_u1,y_new_u1,corr_u1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new_u1), y_new_u1,'k')

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=2;")
ax2.plot(d['area'],d['bal'],'.g',markersize=markersz,alpha=0.7,markeredgewidth=0.01,color=colors[4])#g
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k')


####################################
#SURVEYED
####################################
dcol = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=1 AND name = 'Columbia Glacier';")#
ax.plot(dcol['area'],dcol['bal'],'ok')
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=1 AND name != 'Columbia Glacier';")
ax.plot(d['area'],d['bal'],'ob',color=colors[3])
z,x_new,y_new,corr0 = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k',linewidth=2)

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=1;")
tax=ax.twinx()
tax.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')



d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=0 AND bal<-1.8;;")
ax1.plot(d['area'],d['bal'],'ok')
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=0 and bal>-1.8;")
ax1.plot(d['area'],d['bal'],'or',color=colors[1])
z1,x_new1,y_new1,corr1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new1), y_new1,'k',linewidth=2)

ax1.fill_between(N.exp(x_new1),y_new1,y_new_u1,zorder=4,alpha=0.3,color='k')

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=0;")
tax1=ax1.twinx()
tax1.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')


#SELECT ergi.glimsid,ergi.name,ergi.area,bal,surveyed::bool,gltype,ergi.area as totalarea into temp1 from (SELECT glimsid, SUM(mean*area)/SUM(area)*0.85 as bal,MAX(surveyed::int) as surveyed from resultsauto group by glimsid) as temp inner join ergi on temp.glimsid=ergi.glimsid;

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=2 AND name = 'East Yakutat Glacier';")
ax2.plot(d['area'],d['bal'],'ok')
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=2 AND name != 'East Yakutat Glacier';")
ax2.plot(d['area'],d['bal'],'og',color=colors[5])
z,x_new,y_new,corr2 = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k',linewidth=2)

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=2;")
tax2=ax2.twinx()
tax2.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')

#plt.show()

ax.set_xlabel("Glacier Area (km"+"$\mathregular{^2)}$", labelpad=0)
ax1.set_ylabel("Mass Balance (m w eq yr"+"$\mathregular{^{-1})}$", labelpad=0)
tax1.set_ylabel("Cumulative Glacier Area (%)", labelpad=0)

ax.set_xlim([10e-2,10e3])
ax1.set_xlim([10e-2,10e3])
ax2.set_xlim([10e-2,10e3])

ax.set_ylim([-4,0.4])
ax1.set_ylim([-4,0.4])
ax2.set_ylim([-4,0.4])


tax.set_ylim([0,100])
tax1.set_ylim([0,100])
tax2.set_ylim([0,100])

#print [i.get_position() for i in ax.yaxis.get_ticklabels()]
tax1.annotate("b=%1.4fln(area)+%1.4f\nr=%1.2f,sig=%1.2f"%(z[0],z[1],corr1[0],corr1[1]),[0.2,5],fontsize=10,zorder=4)
ax2.annotate("r=%1.2f,sig=%1.2f"%(corr2[0],corr2[1]),[0.2,-3.5],fontsize=10)
ax.annotate("r=%1.2f,sig=%1.2f"%(corr0[0],corr0[1]),[0.2,-3.5],fontsize=10)
#print [0.2,ax.yaxis.get_ticklabels()[1].get_position()[1]]
#print ax.yaxis.get_ticklabels()[1].get_position()
ax2.annotate("B",[0.2,-0.1],fontsize=13, fontweight='bold')
ax1.annotate("A",[0.2,-0.1],fontsize=13, fontweight='bold')
ax.annotate("C",[0.2,-0.1],fontsize=13, fontweight='bold')

#for label in ax.yaxis.get_ticklabels():label.set_size(10)
#for label in ax1.yaxis.get_ticklabels():label.set_size(10)
#for label in ax2.yaxis.get_ticklabels():label.set_size(10)
#
#for label in tax.yaxis.get_ticklabels():label.set_size(10)
#for label in tax1.yaxis.get_ticklabels():label.set_size(10)
#for label in tax2.yaxis.get_ticklabels():label.set_size(10)

ax1.xaxis.set_tick_params(labeltop='on')
ax1.xaxis.set_tick_params(labelbottom='off')
ax.xaxis.set_tick_params(labelbottom='on')
ax2.xaxis.set_tick_params(labelbottom='off')

#for label in ax.xaxis.get_ticklabels():label.set_size(10)
#for label in ax2.xaxis.get_ticklabels():label.set_size(10)

print 'Conversion Function'
print "Balance = %1.5fln(area)+%1.5f-(%1.5fln(area)+%1.5f)"%(z1[0],z1[1],z_u1[0],z_u1[1])

cur.execute("ALTER TABLE temp1 DROP COLUMN IF EXISTS area_corr;")
cur.execute("ALTER TABLE temp1 ADD COLUMN area_corr real;")
cur.execute("UPDATE temp1 SET area_corr=%1.5f*ln(area)+%1.5f-(%1.5f*ln(area)+%1.5f) WHERE gltype=0 and surveyed='f';"%(z1[0],z1[1],z_u1[0],z_u1[1]))

conn.commit()
print "Small Glacier Correction in Gts yr -1: %s" % GetSqlData2("SELECT SUM(area*1000000*area_corr)/1e9 as correction FROM temp1;")['correction']
print "Small Glacier Correction in m w eq yr -1: %s" % GetSqlData2("SELECT SUM(area*area_corr)/SUM(area) as correction FROM temp1 WHERE gltype=0 and surveyed='f';")['correction']
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS3_area_correction3.jpg",dpi=300)