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
import matplotlib.colors as mcolors

import ConfigParser
from glob import glob

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

def hyp_med(bins,count):
    cum = count.cumsum()
    
    idx = N.abs(cum-(cum[-1]/2)).argmin()
    m,b = N.polyfit(bins[idx-3:idx+3],(cum-(cum[-1]/2))[idx-3:idx+3],1)
    
    return -b/m
    
def datebtw(date, daterange):return date>daterange[0] and date<daterange[1]

def make_divergent(pos,negs,maxval,minval): 
    normzero = N.abs(minval)/(maxval-minval)
    
    pos = N.where(pos<=1,pos*(1-normzero)+normzero,pos/255.)
    negs = N.where(negs<=1,negs*normzero,negs/255.)
    
    x,r,g,b = N.append(negs,pos,axis=0).T
    
    print N.c_[x,r,g,b]
    
    cdict = {'red':[],'green':[],'blue':[]}
    lastx=-1
    for i,x1 in enumerate(x):
        if lastx != x1:cdict['red'].append([x1,r[i],r[i]])
        else:
            cdict['red'].pop(-1)
            cdict['red'].append([x[i-1],r[i-1],r[i]])
        lastx=x1
    
    lastx=-1
    for i,x1 in enumerate(x):
        if lastx != x1:cdict['green'].append([x1,g[i],g[i]])
        else:
            cdict['green'].pop(-1)
            cdict['green'].append([x[i-1],g[i-1],g[i]])
        lastx=x1
        
    lastx=-1
    for i,x1 in enumerate(x):
        if lastx != x1:cdict['blue'].append([x1,b[i],b[i]])
        else:
            cdict['blue'].pop(-1)
            cdict['blue'].append([x[i-1],b[i-1],b[i]])
        lastx=x1
    print cdict
    return cdict, mcolors.LinearSegmentedColormap('CustomMap', cdict)
    
    
    
    
    
data = GetLambData(longest_interval=True,as_object=True, orderby="ergi.region,ergi.name",interval_min=5)
net = GetSqlData2("SELECT glimsid,SUM(mean*area)/SUM(area)*0.85 as net from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(data.glimsid))

#print N.c_[data.glimsid, net['glimsid'],net['net']]
net2 = []
for ele in data.glimsid:
    net2.append(net['net'][N.where(net['glimsid']==ele)[0]][0])
    



                   


net = N.array(net2)
outputfile="/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/Longest_Interval_All_Glaciers_intervals3.jpg"
#outputfile=None
show=True
annotate=True
colorby=net
colorbar = matplotlib.cm.RdYlBu
colorrng = None
ticklabelsize=10
#categorysize=15

"""====================================================================================================
Altimetry.Analytics.PlotIntervals

Evan Burgess 2013-10-18
====================================================================================================
Purpose:
    Plotting intervals retreived from Lamboutput data.
    
Usage:PlotIntervals(data,outputfile=None,show=True)

    data        Output from GetLambData.  Keywords bycolumn = True and ,orderby = 'glnames.region,glnames.name,lamb.date1,lamb.date2'
        
    outputfile  Full path
    
    show        Set to False to not display figure
====================================================================================================        
        """

#FINDING DISTRIBUTION OF SAMPLES THROUGH TIME
timeline = [datetime.date(t,1,1) for t in N.arange(1993,2015)]
count = N.zeros(len(timeline))

for j,t in enumerate(timeline):
    for i in xrange(len(data.date2)):
        if datebtw(t,[data.date1[i],data.date2[i]]):count[j]+=1
ordtime = [i.toordinal() for i in timeline]        
print datetime.date.fromordinal(hyp_med(ordtime,count).astype(int))


#COLOR TABLE
pos=N.flipud(N.array([[1,166,189,219],
[0.5,208,209,230],
[0,236,231,242]]))

negs = N.flipud(N.array([[1,255,255,200],#,255,237,160],
[0.9,255,255,0],
[0.8,254,178,76],
[0.7,253,141,60],
[0.6,227,26,28],
[0.5,128,0,38],
[0.,0,0,0]]))

maxval,minval = colorby.max(),colorby.min()


dic, colorbar = make_divergent(pos,negs,maxval,minval)
print type(colorbar)
#regions = sorted(list(set(s.region)))
#names = (list(set(s.name)))




years    = YearLocator()   # every year
months   = MonthLocator()  # every month
yearsFmt = DateFormatter('%Y')

fig = plt.figure(figsize=[7,9])
ax = fig.add_axes([0.08,0.06,0.93,0.92])



#CREATING COLOR BARS
cm = plt.get_cmap(colorbar) 
if type(colorrng) == NoneType:colorrng = [colorby.min(),colorby.max()]
cNorm  = colors.Normalize(vmin=colorrng[0], vmax=colorrng[1])
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

#CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
#fig = plt.figure(figsize=[15,10])
#ax = fig.add_axes(position)
colorbarim = ax.imshow([colorby],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=colorrng[0], vmax=colorrng[1])
plt.clf()
ax = fig.add_axes([0.08,0.06,0.93,0.92])


plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
#PLOTTING TIME HISTOGRAM
#ax2=ax.twinx()


y = 0.1
lastregion = data.region[0]
lastgl = ''
lastrgbottom = 0.1
lastx=datetime.date(1900,1,1) 
lasty=1000


adjust={"Donjek":-280,"Susitna":200,"Tanaina":200,"TlikakilaNorthFork":300,"Fairweather":-700,"Lamplugh":250,"Exit":-700,"McCarty":700,"Valerie":100,'Skilak':700,"Triumph":400,"LeConte":200}
for i in xrange(len(data.name)): 
    if lastregion != data.region[i]:
        
        regi = data.region[i-1] # re.sub(' ','\n',data.region[i-1])
        if "Kenai" in regi:ax.annotate(regi,xy=[min(data.date1)+dtm.timedelta(days=70),y+0.05],annotation_clip=False,ha='left',fontsize=10)
        else:ax.annotate(regi,xy=[min(data.date1)+dtm.timedelta(days=70),y],annotation_clip=False,ha='left',fontsize=10)
        pt = ax.plot_date([datetime.datetime(1980,2,1),datetime.datetime(2020,2,1)], [y+0.3,y+0.3], ':',color=[0.5,0.5,0.5],lw=1.5)
        lastrgbottom = y
        y += 0.6
        
    if colorby == None:
        if lastgl != data.name[i]:
            color = N.random.rand(3,1)
    else:
        color = scalarMap.to_rgba(colorby[i])

        
    pt = ax.plot_date([data.date1[i],data.date2[i]], [y,y], '-',color=color,lw=1.8)

    if annotate:
        #print lastx,data.date1[i],lasty,lasty
        tdelta = lastx-data.date1[i]
        if lasty-y<0.15 and abs(tdelta.days)<2*365:
            x = data.date1[i]+datetime.timedelta(days=365*2)
        else:
            x = data.date1[i]
            #print data.name[i],x
        if re.sub(" Glacier",'',data.name[i]) in adjust.keys():
            print '^^^^^^^^'
            print data.name[i],x
            x=x+dtm.timedelta(days=adjust[re.sub(" Glacier",'',data.name[i])])
            print x
        ax.annotate(re.sub(" Glacier",'',data.name[i]), [x,y],fontsize=6)
        lastx=x#data.date1[i]
        lasty=y
    y+=0.1
    lastregion = data.region[i]
    lastgl = data.name[i]

#ax.annotate(re.sub(' ','\n',data.region[i-1])+'  ',xy=[min(data.date1)-dtm.timedelta(days=70),(lastrgbottom+y)/2.],annotation_clip=False,ha='right',fontsize=10)
ax.annotate(data.region[i-1],xy=[min(data.date1)+dtm.timedelta(days=70),y-0.07],annotation_clip=False,ha='left',fontsize=10)

#ax.fill_between(timeline,N.zeros(count.size)-5,count/len(data.date1)*y,color=[0.9,0.9,0.9],lw=0,zorder=0.1)

# format the ticks
ax.xaxis.set_major_locator(years)
ax.xaxis.set_major_formatter(yearsFmt)
ax.set_xlim((727809.0, 735110.0))
#ax2.set_xlim((727809.0, 735110.0))
ax.set_ylim([-0.3,y+0.3])
ax.set_xlabel("Time (yr)")



#ax.xaxis.set_minor_locator(months)
ax.yaxis.set_ticks([])
fig.autofmt_xdate()
for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)
ax.autoscale_view()
#ax2 = fig.add_axes([0.77,0.04,0.1,0.94]) 
cax, kw = clbr.make_axes(ax)
#clr = clbr.ColorbarBase(cax,cmap=colorbar)#,"right", size="5%", pad='2%',fig=fig)#)
clr = clbr.Colorbar(cax,colorbarim) 
clr.set_label('Mass Balance (m w. eq. yr'+"$\mathregular{^{-1})}$",size = ticklabelsize)
clr.ax.tick_params(labelsize=10)
clr.ax.set_aspect(30)

ax.set_axis_bgcolor('none')
#ax2 = ax.twinx()
#ax2.set_zorder(-1)
#ax2.plot_date(timeline,count,'-',color=[0.7,0.7,0.7],lw=2,zorder=0.1)
#ax.plot_date(timeline,count,'-',color=[0.7,0.7,0.7],lw=2,zorder=0.1)
#ax2.set_xlim((727809.0, 735110.0))
#ax2.yaxis.tick_left()
#ax2.set_ylim([0,116])
#ax.set_ylabel("Number of Mass Balance Estimates")
#ax.yaxis.labelpad = 20
#ax2 = ax.twinx()

#ax.text(-0.01, 1, "138 Glaciers", transform=ax.transAxes,fontsize=10, va='top',rotation=90)
#ax.text(0, 0, "0 Glaciers", transform=ax.transAxes,fontsize=10, va='bottom',rotation=90)
#ax.text(0, 0.51, "Number of Mass Balance Estimates", transform=ax.transAxes,fontsize=10, va='center',rotation=90)

fig.autofmt_xdate()
if type(outputfile) == str:
    fig.savefig(outputfile,dpi=500)
    plt.close()
if show:plt.show()