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

d = GetSqlData2("select name, region, gltype, surge, t.* from ergi inner join (select SUM(mean*area)/1e9*0.85 as gt, SUM(mean*area)/SUM(area)*0.85 mwe,glimsid from resultsauto2 where surveyed = 't' group by glimsid) as t on ergi.glimsid=t.glimsid left join gltype on ergi.glimsid=gltype.glimsid order by region,name;")

for  i in zip (d['name'],d['gt'],d['mwe'],d['gltype'],d['surge'],d['region']):
    print "%s,%4.2f,%4.2f,%i,%s,%s" % i
#fig = plt.figure(figsize=[7,9])
#
#ax = plt.gca()
#ax.xaxis.set_visible(False)
#ax.yaxis.set_visible(False)
#
#plt.rc("font", **{"sans-serif": ["Arial"],"size": 9})
#
#x = 50
#gt = ["%4.2f" % i for i in d['gt'][0:x]]
#mwe = ["%4.2f" % i for i in d['mwe'][0:x]]
#name = d['name'][0:x]
##t = ax.table(cellText=N.c_[d['name'][0:x],gt,mwe],loc='center')
#
#b = 20
#hs = 10
#col1 = 5
#
#h=b
#for n in name[0:50]:
#    ax.annotate(n,[col1,h],xycoords='figure points')
#    h+=hs
#
#colLabels=['Glacier Name', "Mass Balance\n(Gt yr"+"$\mathregular{^{-1}}$)", "Mass Balance\n(m w. eq. yr"+"$\mathregular{^{-1}}$)"]

#ax.annotate(d['name'][0],[20,10])
plt.show()