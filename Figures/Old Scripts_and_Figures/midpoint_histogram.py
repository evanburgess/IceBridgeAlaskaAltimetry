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



d = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True)


td = [d2-d1 for d1,d2 in zip(d.date1,d.date2)]
middate = [date+dtm.timedelta(days=dtime.days/2) for dtime,date in zip(td,d.date1)]

year = N.array([md.year for md in middate])
biyear = N.where(year%2==0,year-1,year)

#year = biyear
freq = N.bincount(year)
x = N.where(freq!=0)[0]
datex = [datetime.date(yr,1,1) for yr in x]

fig = plt.figure(figsize=[7,3.5])
ax = fig.add_subplot(121)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})



bar = ax.bar(datex,freq[x],width=356)

ax.xaxis_date()
for lbl in ax.xaxis.get_ticklabels():lbl.set_rotation(90)
ax.set_xlabel('Year')
ax.set_ylabel('Number of Interval Midpoints')

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/midpoint_histogram_double_even.jpg",dpi=300)


surv = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE surveyed = 't' GROUP BY bins ORDER BY bins;")
unsu = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE surveyed = 'f' GROUP BY bins ORDER BY bins;")

plt.show()