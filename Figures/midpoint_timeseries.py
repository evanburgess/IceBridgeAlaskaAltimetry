import psycopg2
import xlrd
import re
import unicodedata
import numpy as N
from time import mktime
from datetime import datetime
from time import mktime
import time as tim
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
from scipy.stats import norm
from scipy.stats.mstats import zscore
import statsmodels.api as sm
from scipy.interpolate import interp1d

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *
# import required modules

#from pylab import plot

def toYearFraction(date):

    def sinceEpoch(date): # returns seconds since epoch
        return tim.mktime(date.timetuple())
    s = sinceEpoch

    year = date.year
    startOfThisYear = dtm.datetime(year=year, month=1, day=1)
    startOfNextYear = dtm.datetime(year=year+1, month=1, day=1)

    yearElapsed = s(date) - s(startOfThisYear)
    yearDuration = s(startOfNextYear) - s(startOfThisYear)
    fraction = yearElapsed/yearDuration

    return date.year + fraction
    
def mk_test(x, alpha = 0.5):
    """
    this perform the MK (Mann-Kendall) test to check if the trend is present in 
    data or not
    
    Input:
        x:   a vector of data
        alpha: significance level
    
    Output:
        h: True (if trend is present) or False (if trend is absence)
        p: p value of the sifnificance test
        
    Examples
    --------
      >>> x = np.random.rand(100)
      >>> h,p = mk_test(x,0.05)  # meteo.dat comma delimited
    """
    n = len(x)
    
    # calculate S 
    s = 0
    for k in xrange(n-1):
        for j in xrange(k+1,n):
            s += N.sign(x[j] - x[k])
    
    # calculate the unique data
    unique_x = N.unique(x)
    g = len(unique_x)
    
    # calculate the var(s)
    if n == g: # there is no tie
        var_s = (n*(n-1)*(2*n+5))/18
    else: # there are some ties in data
        tp = N.zeros(unique_x.shape)
        for i in xrange(len(unique_x)):
            tp[i] = sum(unique_x[i] == x)
        var_s = (n*(n-1)*(2*n+5) + N.sum(tp*(tp-1)*(2*tp+5)))/18
    
    if s>0:
        z = (s - 1)/N.sqrt(var_s)
    elif s == 0:
            z = 0
    elif s<0:
        z = (s + 1)/N.sqrt(var_s)
    
    # calculate the p_value
    p = 2*(1-norm.cdf(abs(z))) # two tail test
    h = abs(z) > norm.ppf(1-alpha/2) 
    
    return h, p

#alpha = 0.05
#x = N.array([2,3,2,3,2,3])
#
#print(mk_test(x,alpha))

def gaussian(x, mu, sig):
    return N.exp(-N.power(x - mu, 2.) / (2 * N.power(sig, 2.)))

def loess_point_smooth(xs1,ys,frac=None):
    xs = date2num(xs1)
    
    xout,yout = sm.nonparametric.lowess(ys,xs,frac=frac).T
    print N.c_[xs,ys,xout,yout]
    xout2 = num2date(xout)
    return xout2,yout
    
def gaussian_point_smooth(xs1,ys):
    xs = date2num(xs1)
    line = N.arange(xs.min(),xs.max()+1)
    mean = N.zeros(line.size)
    
    
    
    for i in xrange(line.size):mean[i] = N.average(ys, weights=gaussian(xs,line[i], 356*2))

    line2 = [num2date(i) for i in line]
    
    return line2,mean

def mk_prep(dates,ys):

    lis=[(i,j) for i,j in zip(dates,ys)]
    b = N.array(lis,dtype=[("date",'S10'),("ys",float)])
    b.sort(order='date')
    return b[:]['ys']

def plot_gulkana(axes):
    timeseries = GetSqlData2("SELECT b_winter,b_summer,max_date,min_date from benchmark;")
    time = N.c_[timeseries['max_date'],timeseries['min_date']].reshape(timeseries['max_date'].size*2)
    baltime = N.cumsum(N.c_[timeseries['b_winter'],timeseries['b_summer']].reshape(timeseries['b_summer'].size*2))
    
    interp = interp1d(time,baltime)
    
    gulkmb = [(interp(toYearFraction(d2))-interp(toYearFraction(d1)))/(interval/365) for d1,d2,interval in zip(N.array(d.date1)[win],N.array(d.date2)[win],N.array(d.interval)[win])]
    #ax.text("sfdgsfd",[datetime.datetime(2002,1,1),-2])
    axes.plot_date(in_gau_x,gulkmb,'ko')
    #axes.plot_date(in_gau_x,gulkmb,'ko')
    
    return in_gau_x,gulkmb
#lowess = sm.nonparametric.lowess
#x = np.random.uniform(low = -2*np.pi, high = 2*np.pi, size=500)+2000
#y = np.sin(x) + np.random.normal(size=len(x))
#z = lowess(y, x)
#w = lowess(y, x, frac=1./3)
#
#print N.c_[x,y,z]
#raise
a = False
if a:
    #userwhere="ergi.name != 'Muldrow Glacier'"
    d = GetLambData(verbose=False,interval_max=30,interval_min=5,by_column=True,as_object=True,get_hypsometry=True,longest_interval=False,removerepeats=True)    
    pickle.dump(d, open( "/Users/igswahwsmcevan/Desktop/temp6.p", "wb" ))
else:
    d = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp6.p", "rb" ))

print 'here'
d.fix_terminus()
d.normalize_elevation()
d.calc_mb()

td = [d2-d1 for d1,d2 in zip(d.date1,d.date2)]
middate = N.array([date+dtm.timedelta(days=dtime.days/2) for dtime,date in zip(td,d.date1)])

regions = d.region[:]
regions = [re.sub("Alaska Range","Interior",region) for region in regions]
regions = [re.sub("Wrangell Mountains","Interior",region) for region in regions]
regions = [re.sub("Chugach Range","South-Central",region) for region in regions]
regions = [re.sub("Kenai Mountains","South-Central",region) for region in regions]
regions = [re.sub("St. Elias Mountains","South-Central",region) for region in regions]
regions = [re.sub("Stikine Icefield","Southeast",region) for region in regions]
regions = [re.sub("Juneau Icefield","Southeast",region) for region in regions]
regions = [re.sub("Fairweather Glacier Bay","Southeast",region) for region in regions]

wse = N.where(N.array(regions)=="Southeast")[0]
wsc = N.where(N.array(regions)=="South-Central")[0]
win = N.where(N.array(regions)=="Interior")[0]

#addressing outliers
notoutliers = abs(zscore(d.mb))<3
wse2 = N.where(N.logical_and(N.array(regions)=="Southeast",notoutliers))[0]
wsc2 = N.where(N.logical_and(N.array(regions)=="South-Central",notoutliers))[0]
win2 = N.where(N.logical_and(N.array(regions)=="Interior",notoutliers))[0]

#GAUSSIAN SMOOTH FUNCTIONS
#se_gau_x,se_gau_y = gaussian_point_smooth(N.array(middate[wse]),N.array(d.mb[wse]))
#sc_gau_x,sc_gau_y = gaussian_point_smooth(N.array(middate[wsc]),N.array(d.mb[wsc]))
#in_gau_x,in_gau_y = gaussian_point_smooth(N.array(middate[win]),N.array(d.mb[win]))
se_gau_x,se_gau_y = loess_point_smooth(N.array(middate[wse]),N.array(d.mb[wse]),frac=0.7)
sc_gau_x,sc_gau_y = loess_point_smooth(N.array(middate[wsc]),N.array(d.mb[wsc]),frac=0.7)
in_gau_x,in_gau_y = loess_point_smooth(N.array(middate[win]),N.array(d.mb[win]),frac=0.7)
#z = lowess(y, x)

#outliers removed
#se_gau_x2,se_gau_y2 = gaussian_point_smooth(N.array(middate[wse2]),N.array(d.mb[wse2]))
#sc_gau_x2,sc_gau_y2 = gaussian_point_smooth(N.array(middate[wsc2]),N.array(d.mb[wsc2]))
#in_gau_x2,in_gau_y2 = gaussian_point_smooth(N.array(middate[win2]),N.array(d.mb[win2]))

#MANN KENDALL TEST


lm=0.15
bm=0.1
w=0.8
h=0.28
mm=0.008

fig = plt.figure(figsize=[4,7])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 11})
ax1 = fig.add_axes([lm,bm,w,h])
ax2 = fig.add_axes([lm,bm+h+mm,w,h])
ax3 = fig.add_axes([lm,bm+h+mm+h+mm,w,h])

years    = mdates.YearLocator(2)   # every year
#months   = mdates.MonthLocator(2)  # every month
yearsFmt = mdates.DateFormatter('%Y')

#PLOTTING POINTS
ax1.plot_date(middate[wse],d.mb[wse],'bo')
ax2.plot_date(middate[wsc],d.mb[wsc],'bo')
ax3.plot_date(middate[win],d.mb[win],'bo')

#PLOTTING GULKANA
middategul,gulbal = plot_gulkana(ax3)
gul_x,gul_y = loess_point_smooth(middategul,gulbal,frac=0.7)

gul = GetSqlData2("SELECT year,b_annual from benchmark;")

gulyears = [dtm.date(dt,8,30) for dt in gul['year']]
ax3.plot_date(gulyears,gul['b_annual'],'r-',lw=2)

#ax1.plot_date(middate[wse2],d.mb[wse2])
#ax2.plot_date(middate[wsc2],d.mb[wsc2])
#ax3.plot_date(middate[win2],d.mb[win2])

#PLOTTING GAUSSIAN SMOOTH FUNCTIONS
ax1.plot_date(se_gau_x,se_gau_y,'b-',lw=2)
ax2.plot_date(sc_gau_x,sc_gau_y,'b-',lw=2)
ax3.plot_date(in_gau_x,in_gau_y,'b-',lw=2)
ax3.plot_date(gul_x,gul_y,'k-',lw=2)

#ax1.plot_date(se_gau_x2,se_gau_y2,'b-')
#ax2.plot_date(sc_gau_x2,sc_gau_y2,'b-')
#ax3.plot_date(in_gau_x2,in_gau_y2,'b-')

#MANN KENDALL TEST
se_mk = mk_prep([i.isoformat() for i in middate[wse]],d.mb[wse])
sc_mk = mk_prep([i.isoformat() for i in middate[wsc]],d.mb[wsc])
in_mk = mk_prep([i.isoformat() for i in middate[win]],d.mb[win])


trendstats =  (mk_test(se_mk, alpha = 0.05),mk_test(sc_mk, alpha = 0.05),mk_test(in_mk, alpha = 0.05))
abc=["C","B","A"]
axes = [ax1,ax2,ax3]
for i,axis in enumerate(axes):
    axis.set_ylim([-4,0.5])
    axis.set_xlim([datetime.datetime(1994,1,1),datetime.datetime(2014,1,1)])
    axis.set_yticks([-4,-3,-2,-1,0])
    axis.xaxis.set_major_locator(years)
    axis.xaxis.set_major_formatter(yearsFmt)
    #axis.xaxis.set_minor_locator(months)
    axis.annotate(abc[i],[datetime.date(1995,1,1),-0.2],fontsize=15, fontweight='bold')
    axis.annotate("Mann-Kendall p=%4.2f" % trendstats[i][1],[datetime.date(1995,1,1),-3.5])

for i,tick in enumerate(ax1.get_xticklabels()):tick.set_rotation(90)

ax2.set_xticklabels('')
ax3.set_xticklabels('')
l = ax3.set_ylabel("Mass Balance (m w. eq. year"+"$\mathregular{^{-1}})$",labelpad=0)
ax1.set_xlabel('Altimetry Interval Mid-point')





fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/midpoint_timeseries.jpg",dpi=300)
plt.show()



