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


tide = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE gltype = '1' GROUP BY bins ORDER BY bins;")
lake = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE gltype = '2' GROUP BY bins ORDER BY bins;")
land = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM resultsauto WHERE gltype = '0' GROUP BY bins ORDER BY bins;")

fig = plt.figure(figsize=[14,8])
ax = fig.add_axes([0.10,0.05,0.3,0.73])
ax2 = fig.add_axes([0.4,0.05,0.3,0.73])
ax3 = fig.add_axes([0.7,0.05,0.3,0.73])

ax.plot(land['bins'],N.cumsum(land['area'])/N.sum(land['area']),'r')
ax.plot(lake['bins'],N.cumsum(lake['area'])/N.sum(lake['area']),'g')
ax.plot(tide['bins'],N.cumsum(tide['area'])/N.sum(tide['area']),'b')

plt.show()