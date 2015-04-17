import numpy as N
import datetime as dtm
import matplotlib as plt
from Altimetry.Altimetry import *

#DETERMINES IF A DATE IS WITHIN AN INTERVAL
def datebtw(date, daterange):return date>daterange[0] and date<daterange[1]

#QUERYING DATABASE
d = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True) #ZZZ

#GETTING MIDDATE OF INTERVALS
td = [d2-d1 for d1,d2 in zip(d.date1,d.date2)]
middate = [date+dtm.timedelta(days=dtime.days/2) for dtime,date in zip(td,d.date1)]

#MIDDATE YEARS
year = N.array([md.year for md in middate])

#GROUPING THEM INTO EVEN NUMBERED YEARS
biyear = N.where(year%2==0,year-1,year)

#BUILDING A HISTOGRAM
freq = N.bincount(year)
x = N.where(freq!=0)[0]
datex = [dtm.date(yr,1,1) for yr in x]

#FINDING DISTRIBUTION OF SAMPLES THROUGH TIME
data = GetLambData(longest_interval=True,as_object=True,interval_min=5)
timeline = [dtm.date(t,1,1) for t in N.arange(1993,2015)]
count = N.zeros(len(timeline))

for j,t in enumerate(timeline):
    for i in xrange(len(data.date2)):
        if datebtw(t,[data.date1[i],data.date2[i]]):count[j]+=1
ordtime = [i.toordinal() for i in timeline]        

#FIGURE S2 SETUP
fig = plt.figure(figsize=[3.5,3.5])
ax = fig.add_subplot(111)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
fig.subplots_adjust(left=0.20,bottom=0.2, right=0.95, top=0.95,wspace=0.35)

#PLOTTING 
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

#########################################################################################################
#FIGURE S6 SETUP
fig2 = plt.figure(figsize=[3.5,3.5])
ax2 = fig2.add_subplot(111)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
fig2.subplots_adjust(left=0.20,bottom=0.2, right=0.93, top=0.95,wspace=0.35)

#QUERYING DATABASE FOR HYPOSMETRY
surv = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM altimetryextrapolation WHERE surveyed = 't' GROUP BY bins ORDER BY bins;")#zzz
unsu = GetSqlData2("SELECT bins::real,SUM(area)::real/1000000. as area FROM altimetryextrapolation GROUP BY bins ORDER BY bins;")#zzz

#PLOTTING
ax2.bar(unsu['bins'],unsu['area'],width=30,color=[0.6,0.6,1],zorder=0,linewidth=0,label="Alaska Region")
ax2.bar(surv['bins'],surv['area'],width=30,color='b',linewidth=0,label="Surveyed Glaciers")

#AXES LABEL,LIMITS, TICKS
ax2.set_ylabel('Area (km'+"$\mathregular{^{2})}$")
ax2.set_xlabel("Elevation (m)")
ax2.set_xticks(N.arange(0,6001,2000))
ax2.set_yticks(N.arange(0,1800,500))
ax2.set_xlim([0,6000])
ax2.legend(fontsize=10)

fig2.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/sampling_distribution_spatial.jpg",dpi=300)
plt.show()