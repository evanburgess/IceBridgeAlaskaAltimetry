import numpy as N
import time as tim
import matplotlib as plt
import pickle
import datetime as dtm
import matplotlib.dates as mdates
from scipy.stats import norm
import statsmodels.api as sm
from scipy.interpolate import interp1d
from matplotlib.dates import date2num,num2date
from Altimetry.Altimetry import *

#CONVERTS A DATETIME OBJECT INTO A FRACTIONAL YEAR
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



#GAUSSIAN FUNCTION
def gaussian(x, mu, sig):
    """GAUSSIAN FUNCTION"""
    return N.exp(-N.power(x - mu, 2.) / (2 * N.power(sig, 2.)))

#LOWESS POINT SMOOTH
def loess_point_smooth(xs1,ys,frac=None):
    xs = date2num(xs1)
    xout,yout = sm.nonparametric.lowess(ys,xs,frac=frac).T
    xout2 = num2date(xout)
    
    return xout2,yout

#THIS FITS A LINEAR LEAST SQUARE MODEL TO A LOWESS FILTER OF POINT DATA
def loess_linearfit(xs1,ys,frac=None):
    xs = date2num(xs1)
    
    xout,yout = sm.nonparametric.lowess(ys,xs,frac=frac).T
    
    m,b = N.polyfit(xout, ys, 1)
    yout2 = m*xout+b
    xout2 = num2date(xout)
    return xout2,yout2
    
#A GAUSSIAN SMOOTH OF POINT DATA
def gaussian_point_smooth(xs1,ys):
    xs = date2num(xs1)
    line = N.arange(xs.min(),xs.max()+1)
    mean = N.zeros(line.size)
    
    for i in xrange(line.size):mean[i] = N.average(ys, weights=gaussian(xs,line[i], 356*2))

    line2 = [num2date(i) for i in line]
    
    return line2,mean
    
#PREPARES THE DATA FOR A MANN-KENDALL TREND TEST BY ORDERING THE DATA
def mk_prep(dates,ys):

    lis=[(i,j) for i,j in zip(dates,ys)]
    b = N.array(lis,dtype=[("date",'S10'),("ys",float)])
    b.sort(order='date')
    return b[:]['ys']

#ROBUST LINEAR MODEL BUT FOR WHEN THE X IS A DATETIME OBJECT    
def rlm_date(x,y):
    from statsmodels.robust.robust_linear_model import RLM
    x2 = sm.add_constant(date2num(x))
    rlmmodel = RLM(y,x2)
    rlmresults = rlmmodel.fit()

    return x,rlmresults.fittedvalues,N.array(rlmresults.pvalues).mean()

#THIS FUNCTION PLOTS A BENCHMARK GLACIER TIMESERIES GIVEN THE GLACIER NAME, AND INTERVALS.  
def plot_benchmark(glaciername=None,datesandintervals=None,timeseries=True,cumulative=False):
    if type(datesandintervals)==list and timeseries==False:

        timeseries = GetSqlData2("SELECT b_winter,b_summer,max_date,min_date from benchmark WHERE name='%s';" % glaciername)  #zzz
        time = N.c_[timeseries['max_date'],timeseries['min_date']].reshape(timeseries['max_date'].size*2)               # cumulative mass balance timeseries
        baltime = N.cumsum(N.c_[timeseries['b_winter'],timeseries['b_summer']].reshape(timeseries['b_summer'].size*2))  # cumulative mass balance timeseries
        
        interp = interp1d(time,baltime)
        date1,date2,intervals = datesandintervals
        mb = [(interp(toYearFraction(d2))-interp(toYearFraction(d1)))/(interval/365) for d1,d2,interval in zip(N.array(date1),N.array(date2),N.array(intervals))]

        middate = N.array([d1+dtm.timedelta(days=inv/2) for d1,inv in zip(date1,intervals)])
        return middate,mb

    elif type(datesandintervals)==NoneType and timeseries==True:
        d = GetSqlData2("SELECT year,b_annual from benchmark WHERE name='%s';" % glaciername)#zzz
        
        years = [dtm.date(dt,8,30) for dt in d['year']]
        
        if cumulative==False: return years,d['b_annual']
        elif cumulative==True: return years,N.cumsum(d['b_annual'])
    else: raise "ERROR: Need to specify only a timeseries or midpoint set"

#LINEAR REGRESSION WITH X AS A DATETIME OBJECT
def date_regress(x,y):
    dx = date2num(x)
    slope, intercept, r_value, p_value, std_err = stats.linregress(dx,y)
    return slope*dx+intercept,p_value
    
#QUERYING DATABASE
a = True
if a:
    d = GetLambData(verbose=False,interval_max=30,interval_min=5,by_column=True,as_object=True,get_hypsometry=True,longest_interval=True,removerepeats=True)   #zzz   
    pickle.dump(d, open( "/Users/igswahwsmcevan/Desktop/temp6.p", "wb" ))
else:
    d = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp6.p", "rb" ))

#CALCULATING GLACIER MASS BALANCE.
d.fix_terminus()
d.normalize_elevation()
d.calc_mb()

#CALCULATING MIDPOINT DATES
td = [d2-d1 for d1,d2 in zip(d.date1,d.date2)]
middate = N.array([date+dtm.timedelta(days=dtime.days/2) for dtime,date in zip(td,d.date1)])

#CLASSIFYING THE GLACIERS BY ZONE INSTEAD OF MOUNTAIN RANGE
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

#RETRIEVING BENCHMARK GLACIER DATA
midgulx,midguly=plot_benchmark(glaciername="Gulkana Glacier",datesandintervals=[N.array(d.date1)[win],N.array(d.date2)[win],N.array(d.interval)[win]],timeseries=False,cumulative=False)
midwolx,midwoly=plot_benchmark(glaciername="Wolverine Glacier",datesandintervals=[N.array(d.date1)[win],N.array(d.date2)[win],N.array(d.interval)[win]],timeseries=False,cumulative=False)
gulx,guly=plot_benchmark(glaciername="Gulkana Glacier",timeseries=True,cumulative=False)
wolx,woly=plot_benchmark(glaciername="Wolverine Glacier",timeseries=True,cumulative=False)


#WE TRIED MANY DIFFERENT MIDPOINT SMOOTHING FUNCTIONS AND REJECTED ALL OF THEM HERE ARE THE OPTIONS IF SOMEONE CHANGES THEIR MIND
#se_gau_x,se_gau_y = gaussian_point_smooth(N.array(middate[wse]),N.array(d.mb[wse]))
#sc_gau_x,sc_gau_y = gaussian_point_smooth(N.array(middate[wsc]),N.array(d.mb[wsc]))
#in_gau_x,in_gau_y = gaussian_point_smooth(N.array(middate[win]),N.array(d.mb[win]))

#se_gau_x,se_gau_y = loess_linearfit(N.array(middate[wse]),N.array(d.mb[wse]),frac=0.7)
#sc_gau_x,sc_gau_y = loess_linearfit(N.array(middate[wsc]),N.array(d.mb[wsc]),frac=0.7)
#in_gau_x,in_gau_y = loess_linearfit(N.array(middate[win]),N.array(d.mb[win]),frac=0.7)

#se_gau_x,se_gau_y,se_p = rlm_date(N.array(middate[wse]),N.array(d.mb[wse]))#loess_point_smooth(N.array(middate[wse]),N.array(d.mb[wse]),frac=0.7)
#sc_gau_x,sc_gau_y,sc_p = rlm_date(N.array(middate[wsc]),N.array(d.mb[wsc]))#loess_point_smooth(N.array(middate[wsc]),N.array(d.mb[wsc]),frac=0.7)
#in_gau_x,in_gau_y,in_p = rlm_date(N.array(middate[win]),N.array(d.mb[win]))#loess_point_smooth(N.array(middate[win]),N.array(d.mb[win]),frac=0.7)

#MANN KENDALL TEST
se_mk = mk_prep([i.isoformat() for i in middate[wse]],d.mb[wse])
sc_mk = mk_prep([i.isoformat() for i in middate[wsc]],d.mb[wsc])
in_mk = mk_prep([i.isoformat() for i in middate[win]],d.mb[win])
gul_mk = mk_prep([i.isoformat() for i in midgulx],midguly)
wol_mk = mk_prep([i.isoformat() for i in midwolx],midwoly)

wgul1993 = N.where(N.array([g.year for g in gulx])>1993)[0]
wwol1993 = N.where(N.array([g.year for g in wolx])>1993)[0]

gul_time_mk = mk_prep([i.isoformat() for i in N.array(gulx)[wgul1993]],N.array(guly)[wgul1993])  # cutting the timeseries down to 1994-2014
wol_time_mk = mk_prep([i.isoformat() for i in N.array(wolx)[wwol1993]],N.array(woly)[wwol1993])  # cutting the timeseries down to 1994-2014

trendstats =  (mk_test(se_mk, alpha = 0.05),mk_test(sc_mk, alpha = 0.05),mk_test(in_mk, alpha = 0.05),mk_test(gul_time_mk, alpha = 0.05),mk_test(gul_time_mk, alpha = 0.05),mk_test(wol_time_mk, alpha = 0.05))


#FIGURE SETUP
fig = plt.figure(figsize=[4,7])
ax1 = plt.subplot2grid((8,1), (6, 0), rowspan=2)
ax2 = plt.subplot2grid((8,1), (4, 0), rowspan=2)
ax3 = plt.subplot2grid((8,1), (2, 0), rowspan=2)
ax4 = plt.subplot2grid((8,1), (0, 0), rowspan=2)
fig.subplots_adjust(hspace=0.04,bottom=0.1,left=0.14,top=0.98,right=0.98)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 11})

#DATE FORMATTER
years    = mdates.YearLocator(2)   # every year
yearsFmt = mdates.DateFormatter('%Y')

#PLOTTING POINTS
ax1.plot_date(middate[wse],d.mb[wse],'ko',alpha = 0.5,markersize=4,zorder=5)
ax2.plot_date(middate[wsc],d.mb[wsc],'ko',alpha = 0.5,markersize=4,zorder=5)
ax3.plot_date(middate[win],d.mb[win],'ko',alpha = 0.5,markersize=4,zorder=5)
ax1.plot_date([N.array(d.date1)[wse],N.array(d.date2)[wse]],[d.mb[wse],d.mb[wse]],'-k',alpha = 0.2)
ax2.plot_date([N.array(d.date1)[wsc],N.array(d.date2)[wsc]],[d.mb[wsc],d.mb[wsc]],'-k',alpha = 0.2)
ax3.plot_date([N.array(d.date1)[win],N.array(d.date2)[win]],[d.mb[win],d.mb[win]],'-k',alpha = 0.2)

#PLOTTING GAUSSIAN SMOOTH FUNCTIONS WE DON'T HAVE A SMOOTHER PLOTING NOW
#ax1.plot_date(se_gau_x,se_gau_y,'k-',lw=3,zorder=4)
#ax2.plot_date(sc_gau_x,sc_gau_y,'k-',lw=3,zorder=4)
#ax3.plot_date(in_gau_x,in_gau_y,'k-',lw=3,zorder=4)
#ax4.plot_date(gul_gau_x,gul_gau_y,'r-',lw=2,zorder=4)

#PLOTTING BENCHMARK DATA
ax4.plot_date(gulx,guly,'r-',lw=0.5,label='Gulkana')
ax4.plot_date(wolx,woly,'b-',lw=0.5,label='Wolverine')
mysgul,pgul=date_regress(gulx[28:],guly[28:])
myswol,pwol=date_regress(wolx[28:],woly[28:])
ax4.plot_date(gulx[28:],mysgul,'r-',lw=2)
ax4.plot_date(wolx[28:],myswol,'b-',lw=2)

ax4.legend(fontsize=9,loc='lower right')#, bbox_to_anchor=(0.956, 0.47))

slope, intercept, r_value, p_value, std_err = stats.linregress(date2num(wolx),woly)
#ax4.plot_date(midgulx,midguly,'ro',alpha = 0.5,zorder=3)
#ax4.plot_date(midwolx,midwoly,'bo',alpha = 0.5)


#SETTING AXES PARAMETERS, TICKS,LIMITS,LABELS,ETC
abc=["D","C","B","A"]
axes = [ax1,ax2,ax3,ax4]

for i,axis in enumerate(axes):
    if i<4:axis.set_yticks([-4,-3,-2,-1,0,1])
    else:axis.set_yticks([-1,-0.7])
    axis.xaxis.set_major_locator(years)
    axis.xaxis.set_major_formatter(yearsFmt)
    axis.annotate(abc[i],xy=(.025, .975),xycoords='axes fraction',fontsize=15, fontweight='bold',va='top',ha='left')
    if i < 3:axis.annotate("p=%4.2f" % trendstats[i][1],[dtm.date(1995,1,1),-3.7],fontsize=9)
 
    elif i==3:axis.annotate("Gulkana p=%4.2f\nWolverine p=%4.2f" % (trendstats[i][1],trendstats[i+2][1]),[dtm.date(1994,8,1),-3.9],fontsize=9)
    if i>0:axis.set_xticklabels('')
    if not i==4:axis.set_ylim([-4,1.5])
    else:axis.set_ylim([-1.05,-0.65])
    axis.set_xlim([dtm.datetime(1994,1,1),dtm.datetime(2014,1,1)])

for i,tick in enumerate(ax1.get_xticklabels()):tick.set_rotation(90)

l = ax4.annotate("Mass Balance (m w. eq. yr"+"$\mathregular{^{-1}})$",[dtm.date(1991,3,1),-10],rotation=90, annotation_clip=False,va='center')
ax1.set_xlabel('Time (yr)')

fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/midpoint_timeseries_longest_interval_RLM.jpg",dpi=300)
plt.show()



