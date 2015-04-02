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
import datetime as dtm
import matplotlib.dates as mdates
import ConfigParser
from glob import glob

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

def datebtw(date, daterange):return date>daterange[0] and date<daterange[1]

def hyp_med(bins,count):
    cum = count.cumsum()
    
    idx = N.abs(cum-(cum[-1]/2)).argmin()
    m,b = N.polyfit(bins[idx-3:idx+3],(cum-(cum[-1]/2))[idx-3:idx+3],1)
    
    return -b/m
d = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True)


td = [d2-d1 for d1,d2 in zip(d.date1,d.date2)]
middate = [date+dtm.timedelta(days=dtime.days/2) for dtime,date in zip(td,d.date1)]

year = N.array([md.year for md in middate])
biyear = N.where(year%2==0,year-1,year)

#year = biyear
freq = N.bincount(year)
x = N.where(freq!=0)[0]
datex = [datetime.date(yr,1,1) for yr in x]




#FINDING DISTRIBUTION OF SAMPLES THROUGH TIME
data = GetLambData(longest_interval=True,as_object=True, orderby="ergi.region,ergi.name",interval_min=5)
timeline = [datetime.date(t,1,1) for t in N.arange(1993,2015)]
count = N.zeros(len(timeline))

for j,t in enumerate(timeline):
    for i in xrange(len(data.date2)):
        if datebtw(t,[data.date1[i],data.date2[i]]):count[j]+=1
ordtime = [i.toordinal() for i in timeline]        
print datetime.date.fromordinal(hyp_med(ordtime,count).astype(int))













fig = plt.figure(figsize=[3.5,3.5])
ax = fig.add_subplot(111)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

fig.subplots_adjust(left=0.20,bottom=0.2, right=0.95, top=0.95,wspace=0.35)

bar = ax.bar(datex,freq[x],width=356,color='0.5')
ax.plot_date(timeline,count,'-',color='k',lw=2,zorder=0.1)
#ax.xaxis_date()
years    = YearLocator(2)   # every year
ax.xaxis.set_major_locator(years)

for lbl in ax.xaxis.get_ticklabels():lbl.set_rotation(45)
ax.set_xlabel('Time (yr)')
ax.set_ylabel('Count')

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/sampling_distribution_temporal.jpg",dpi=300)
plt.show()



fig2 = plt.figure(figsize=[3.5,3.5])
ax2 = fig2.add_subplot(111)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

fig2.subplots_adjust(left=0.20,bottom=0.2, right=0.93, top=0.95,wspace=0.35)



surv = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE surveyed = 't' GROUP BY bins ORDER BY bins;")
unsu = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto GROUP BY bins ORDER BY bins;")

ax2.bar(unsu['bins'],unsu['area'],width=30,color=[0.6,0.6,1],zorder=0,linewidth=0,label="Alaska Region")
ax2.bar(surv['bins'],surv['area'],width=30,color='b',linewidth=0,label="Surveyed Glaciers")
ax2.set_ylabel('Area (km'+"$\mathregular{^{2})}$")
ax2.set_xlabel("Elevation (m)")
ax2.set_xticks(N.arange(0,6001,2000))
ax2.set_yticks(N.arange(0,1800,500))
ax2.set_xlim([0,6000])
ax2.legend(fontsize=10)

#ax.annotate("A",xy=[0,1],xycoords='axes fraction',xytext = [8,-8],textcoords='offset points',weight='bold',size=13,va='top',ha='left')
#ax2.annotate("B",xy=[0,1],xycoords='axes fraction',xytext = [8,-8],textcoords='offset points',weight='bold',size=13,va='top',ha='left')

fig2.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/sampling_distribution_spatial.jpg",dpi=300)
plt.show()