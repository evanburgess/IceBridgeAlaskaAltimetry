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
    z = np.polyfit(N.log(x), y, 1)
    f = np.poly1d(z)
    
    if type(extend)==NoneType:
        x_new = np.linspace(N.log(N.min(x)),N.log(N.max(x)), 50)
        print [N.log(N.min(x)),N.log(N.max(x))]
    else:
        x_new = np.linspace(N.log(extend[0]),N.log(extend[1]), 50)
        print 'extend',[N.log(extend[0]),N.log(extend[1])]
    y_new = f(x_new)
    
    return z,x_new,y_new,corr
    
conn,cur = ConnectDb()

#cur.execute("select ergi.glimsid,ergi.area,ergi.albersgeom,rlt.bal,rlt.surveyed,rlt.gltype,ergi.name into temp1 from ergi inner join (SELECT glimsid, SUM(mean*area)/SUM(area)*0.85 as bal, every(surveyed) as surveyed, AVG(gltype::real) as gltype from resultsauto group by glimsid) as rlt on ergi.glimsid=rlt.glimsid;")
#cur.commit()

lm=0.17
bm=0.07
h=0.28
w=0.7
mb = 0.02

fig = plt.figure(figsize=[4,8])
ax2 = fig.add_axes([lm,bm,w,h])
ax1 = fig.add_axes([lm,bm+h+mb,w,h])
ax = fig.add_axes([lm,bm+h*2+mb*2,w,h])

ax.set_xscale('log')
ax1.set_xscale('log')
ax2.set_xscale('log')
####################################
#NOT SURVEYED
####################################
markersz = 5
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=1;")
ax.plot(d['area'],d['bal'],'.b',markersize=markersz,alpha=0.3)
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k')


d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=0;")
ax1.plot(d['area'],d['bal'],'.r',markersize=markersz,alpha=0.1)
z_u1,x_new_u1,y_new_u1,corr_u1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new_u1), y_new_u1,'k')

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='f' AND gltype=2;")
ax2.plot(d['area'],d['bal'],'.g',markersize=markersz,alpha=0.3)
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k')


####################################
#SURVEYED
####################################
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=1 AND name != 'Columbia Glacier';")
ax.plot(d['area'],d['bal'],'ob')
z,x_new,y_new,corr0 = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k',linewidth=2)

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=1;")
tax=ax.twinx()
tax.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/N.sum(d['area'])*100,'k')



d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=0 AND bal<-1.8;;")
ax1.plot(d['area'],d['bal'],'ok')
d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=0 and bal>-1.8;")
ax1.plot(d['area'],d['bal'],'or')
z1,x_new1,y_new1,corr1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new1), y_new1,'k',linewidth=2)

ax1.fill_between(N.exp(x_new1),y_new1,y_new_u1,zorder=4,alpha=0.3,color='k')


d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=0;")
tax1=ax1.twinx()
tax1.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/N.sum(d['area'])*100,'k')




d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE surveyed='t' AND gltype=2;")
ax2.plot(d['area'],d['bal'],'og')
z,x_new,y_new,corr2 = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k',linewidth=2)

d = GetSqlData2("SELECT area::real,bal,surveyed,gltype,name FROM temp1 WHERE gltype=2;")
tax2=ax2.twinx()
tax2.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/N.sum(d['area'])*100,'k')

#plt.show()

ax2.set_xlabel("Glacier Area (km"+"$^2$"+")",fontsize=10)
ax.set_ylabel("Mass Balance (m eq yr"+r"$^{-1}$"+")",fontsize=10)
tax.set_ylabel("Cumulative Glacier Area (%)",fontsize=10)

ax.set_xlim([10e-2,10e3])
ax1.set_xlim([10e-2,10e3])
ax2.set_xlim([10e-2,10e3])

tax.set_ylim([0,100])
#tax1.set_ylim([0,100])
tax2.set_ylim([0,100])

#print [i.get_position() for i in ax.yaxis.get_ticklabels()]
ax1.annotate("r=%1.2f,sig=%1.2f"%(corr1[0],corr1[1]),[0.2,-2.5],fontsize=10)
ax2.annotate("r=%1.2f,sig=%1.2f"%(corr2[0],corr2[1]),[0.2,-3.5],fontsize=10)
ax.annotate("r=%1.2f,sig=%1.2f"%(corr0[0],corr0[1]),[0.2,-0.8],fontsize=10)
#print [0.2,ax.yaxis.get_ticklabels()[1].get_position()[1]]
#print ax.yaxis.get_ticklabels()[1].get_position()
ax2.annotate("C.",[0.2,0],fontsize=13, fontweight='bold')
ax1.annotate("B.",[0.2,-0.4],fontsize=13, fontweight='bold')
ax.annotate("A.",[0.2,0.2],fontsize=13, fontweight='bold')

for label in ax.yaxis.get_ticklabels():label.set_size(10)
for label in ax1.yaxis.get_ticklabels():label.set_size(10)
for label in ax2.yaxis.get_ticklabels():label.set_size(10)

for label in tax.yaxis.get_ticklabels():label.set_size(10)
for label in tax1.yaxis.get_ticklabels():label.set_size(10)
for label in tax2.yaxis.get_ticklabels():label.set_size(10)

ax.xaxis.set_tick_params(labeltop='on')
ax.xaxis.set_tick_params(labelbottom='off')
ax1.xaxis.set_tick_params(labelbottom='off')

for label in ax.xaxis.get_ticklabels():label.set_size(10)
for label in ax2.xaxis.get_ticklabels():label.set_size(10)





plt.show()