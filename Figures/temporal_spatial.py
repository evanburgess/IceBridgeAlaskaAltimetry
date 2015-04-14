# -*- coding: utf-8 -*-
import pickle
from scipy.interpolate import interp1d
import time as tim
import scipy
from Altimetry.Interface import *

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
    
def partition_dataset(*args,**kwargs):

    for k in kwargs:
        if k not in ['interval_min','interval_max','applytoall']:raise "ERROR: Unidentified keyword present"
    lamb = [] 
    userwheres=[]
    userwheres2=[]
    notused = []
    notused2 = []
    zones=[]
    if 'interval_max' in kwargs.keys():intervalsmax = kwargs['interval_max']
    else:intervalsmax=30
    
    if 'interval_min' in kwargs.keys():min_interval = kwargs['interval_min']
    else:min_interval=5
    
    from itertools import product
    for items in product(*list(args)):
        userwhere =  " AND ".join(items)

        if kwargs:
            if not type(kwargs['applytoall'])==list:kwargs['applytoall']=[kwargs['applytoall']]
            userwhere2 = userwhere+" AND "+" AND ".join(kwargs['applytoall'])
            
        out = GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, userwhere=userwhere2,get_hypsometry=True)
        if type(out)!=NoneType:
            userwheres2.append(userwhere2)
            userwheres.append(userwhere)
            lamb.append(out)
            lamb[-1].fix_terminus()
            lamb[-1].remove_upper_extrap()
            lamb[-1].normalize_elevation()
            lamb[-1].calc_dz_stats()
            lamb[-1].extend_upper_extrap()
            lamb[-1].calc_mb()
        else:
            notused.append(userwhere)
            notused2.append(userwhere2)
    return lamb,userwheres2,notused2,userwheres,notused

def plot_benchmark(glaciername=None,datesandintervals=None,timeseries=True,cumulative=False):
    if type(datesandintervals)==list and timeseries==False:
        #print timeseries,"SELECT b_winter,b_summer,max_date,min_date from benchmark WHERE name='%s';" % glaciername
        timeseries = GetSqlData2("SELECT b_winter,b_summer,max_date,min_date from benchmark WHERE name='%s';" % glaciername)
        time = N.c_[timeseries['max_date'],timeseries['min_date']].reshape(timeseries['max_date'].size*2)               # cumulative mass balance timeseries
        baltime = N.cumsum(N.c_[timeseries['b_winter'],timeseries['b_summer']].reshape(timeseries['b_summer'].size*2))  # cumulative mass balance timeseries
        
        interp = interp1d(time,baltime)
        date1,date2,intervals = datesandintervals
        mb = [(interp(toYearFraction(d2))-interp(toYearFraction(d1)))/(interval/365) for d1,d2,interval in zip(N.array(date1),N.array(date2),N.array(intervals))]

        middate = N.array([d1+dtm.timedelta(days=inv/2) for d1,inv in zip(date1,intervals)])
        return middate,mb
    elif type(datesandintervals)==NoneType and timeseries==True:
        d = GetSqlData2("SELECT year,b_annual from benchmark WHERE name='%s';" % glaciername)
        
        years = [dtm.date(dt,8,30) for dt in d['year']]
        
        if cumulative==False: return years,d['b_annual']
        elif cumulative==True: return years,N.cumsum(d['b_annual'])
    else: raise "ERROR: Need to specify only a timeseries or midpoint set"

def stdintervaldep(timeseries, consecutive=False):
    yrs = N.arange(1,16)
    std = N.array([])
    if consecutive:


        
        for n in yrs:
            s = N.array([])
            start = 0 
            end=1
            while end!=timeseries.size:
                end = start+n
                print start,end
                s=N.append(s,N.array(timeseries[start:end]).mean())
                start += 1
            std = N.append(std,s.std())
        return yrs,std
            
    else:    

        for n in yrs:
            s = N.array([])
        
            for i in xrange(1000):
                s = N.append(s,N.mean(N.array([random.choice(timeseries) for i in range(n)])))
            std = N.append(std,s.std())
        return yrs,std

#CALCULATES THE STANDARD DEVIATION IN MASS BALANCE OVER A SERIES OF INTERVAL LENGTHS SPECIFIED BY STARTS AND ENDS RETURNS THE STD AND NUMBER OF SAMPLES        
def altimetryintervalstd(starts,ends,onlyone=False):
    std = N.array([])
    n = N.array([])

    starts = [1,2,3,4,5,6,8]
    ends = [1,2,3,4,5,7,30]
    
    for mn,mx in zip(starts,ends):
        t = GetLambData(verbose=False,interval_max=mx,interval_min=mn,by_column=True,as_object=True,results=True)
        
        if onlyone:
            ws=[]
            names = sort(list(set(t.name)))
            for gl in names:
                ws.append(random.choice(N.where(N.array(t.name)==gl)[0]))
            
            std = N.append(std, t.rlt_totalkgm2[ws].std())
            n = N.append(n, t.rlt_totalkgm2[ws].size)  
        else:       
            std = N.append(std, t.rlt_totalkgm2.std())
            n = N.append(n, t.rlt_totalkgm2.size) 
            
        if t.rlt_totalkgm2.size<8:raise "Only 8 in this interval set"

    return std,n
            
plot_hist=False

user_where=["FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'","FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'","FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatEast' AND glnames.name!='YakutatWest' AND gltype.surge='f'","gltype.surge='f'"]
#user_where=["FLOOR((ergi.glactype::real-9000)/100)=0 AND gltype.surge='f'","FLOOR((ergi.glactype::real-9000)/100)=1 AND glnames.name!='Columbia'","FLOOR((ergi.glactype::real-9000)/100)=2 AND glnames.name!='Bering' AND glnames.name!='YakutatWest' AND glnames.name!='YakutatEast' AND gltype.surge='f'"]
outroot = ["Tidewater","Lake","Land","All"]
color = ['k','g','r','r']
min_interval=5
intervalsmax=30
labels = ['<=3yr intervals','3-5 yrs','5-10yrs','>=10yrs','>=3yrs','>=5yrs','Before 2003','After 2002']
shpfiles = ['intervals_less3yr','intervals_3_5yrs','intervals5_10yrs','intervals_more10yrs','intervals_more3yrs','intervals_more5yrs','Before2003','After2002']
div1 = '2000-01-01'
i=0

runall=True


if runall:    
    ##Separating Tidewater and Lakes
    #################################################################################
    #types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    #lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["ergi.gltype=0","gltype.surge='f'","ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    starts = [1,2,3,4,5,6,8]
    ends = [1,2,3,4,5,8,30]
    altstd,altn = altimetryintervalstd(starts,ends,onlyone=False)

    pickle.dump([altstd,starts,ends,altn], open("/Users/igswahwsmcevan/Altimetry/results/spatialtemporal.p", "wb" ))
else:
    altstd,starts,ends,altn = pickle.load(open("/Users/igswahwsmcevan/Altimetry/results/spatialtemporal.p", "rb" ))

#BENCHMARK GLACIER DATA
#midgulx,midguly=plot_benchmark(glaciername="Gulkana Glacier",datesandintervals=[N.array(lamb[2].date1),N.array(lamb[2].date2),N.array(lamb[2].interval)],timeseries=False,cumulative=False)
#midwolx,midwoly=plot_benchmark(glaciername="Wolverine Glacier",datesandintervals=[N.array(lamb[1].date1),N.array(lamb[1].date2),N.array(lamb[1].interval)],timeseries=False,cumulative=False)
gulx,guly=plot_benchmark(glaciername="Gulkana Glacier",timeseries=True,cumulative=False)
wolx,woly=plot_benchmark(glaciername="Wolverine Glacier",timeseries=True,cumulative=False)

gulx = gulx[28:]
wolx = wolx[28:]
guly = guly[28:]
woly = woly[28:]



#gulyrs,gulstd = stdintervaldep(guly)
#wolyrs,wolstd = stdintervaldep(woly)

gulyrs_csc,gulstd_csc = stdintervaldep(guly, consecutive=True)
wolyrs_csc,wolstd_csc = stdintervaldep(woly, consecutive=True)


fig = plt.figure(figsize=[5,4.5])
ax = fig.add_subplot(1,1,1)
ax.grid(which='major',color='0.8',linestyle='-',lw=0.3,zorder=1)
ax.set_axisbelow(True)

fly='o'


 

#ydata = f(xdata, *params) + eps

def expdecay(x,n,tau):return n*N.exp(-x/tau)

poptgul,pcov = scipy.optimize.curve_fit(expdecay, gulyrs_csc, gulstd_csc)
poptwol,pcov = scipy.optimize.curve_fit(expdecay, wolyrs_csc, wolstd_csc)

ymodelg = expdecay(gulyrs_csc,poptgul[0],poptgul[1])
ymodelw = expdecay(wolyrs_csc,poptwol[0],poptwol[1])

#ax.plot(gulyrs_csc,gulstd_csc,'r-',wolyrs_csc,wolstd_csc,'b-',lw=2)
#ax.plot(gulyrs_csc,ymodelg,'k-',wolyrs_csc,ymodelw,'k-')


plt1=ax.step(gulyrs_csc,gulstd_csc,'r-',lw=2,where='mid', label='Gulkana',zorder=2) 
plt2=ax.step(wolyrs_csc,wolstd_csc,'b-',lw=2,where='mid', label='Wolverine',zorder=2)   




#ax.plot((N.array(starts)+N.array(ends))/2,altstd,'k',lw=2)

ends[-1]=16
starts.append(16)
ends.append(50)
altstd = N.append(altstd,altstd[-1])


starts= N.array(starts)-0.5
starts[-2]=8

plt3=ax.step(N.array(starts),altstd,'k',lw=2,where='post', label='Altimetry',zorder=2)
offset = N.zeros(len(starts))-10

poptalt,pcov = scipy.optimize.curve_fit(expdecay, N.array(starts), altstd)

ymodela = expdecay(N.array(starts),poptalt[0],poptalt[1])

#ax.plot(gulyrs_csc,gulstd_csc,'r-',wolyrs_csc,wolstd_csc,'b-',lw=2)
#ax.plot(N.array(starts),ymodela,'k-',wolyrs_csc,ymodelw,'k-')


#offset[0]=25
for o,sa,na,s,e in zip(offset,altstd,N.append(altn,altn[-1]),N.array(starts)+0.5,ends):

    ax.annotate("%i" % na,[(N.array(s)+N.array(e))/2.,sa],xytext=[0,o],textcoords='offset points',fontsize=11,ha='center',zorder=2)    


plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
#errs = ax.errorbar(x[0], gts[0], yerr=[err[0], err[0]],fmt='o',color='k')
#errs = ax.errorbar(x[1:], gts[1:], yerr=[err[1:], err[1:]],fmt='o',color='0.7')
#ax.plot([0,15],[gts[0],gts[0]],'k-')
#ax.set_xlim([-0.5,7])
#ax.set_ylim([-100,-40])
#ax.set_xlabel("Partitioning Method")
#ax.set_ylabel("Mass Balance\n(Gt yr"+"$\mathregular{^{-1})}$")
#ax.set_xticks(N.arange(0,11))
#ax.set_xticklabels(titles,rotation=90,fontsize=11,verticalalignment='top')
ax.set_ylabel("Std. Dev. of Mass Balance\n(m w. eq. yr"+"$\mathregular{^{-1})}$")
ax.set_xlabel("Interval Length (yr)")
ax.set_xlim(0,15)

#ax.grid(which='major',color='k',linestyle='-',lw=0.8)
ax.legend(fontsize=11)
plt.subplots_adjust(left=0.22,right=0.98,bottom=0.14,top=0.95)
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/temporal_spatial_step.jpg",dpi=500)

