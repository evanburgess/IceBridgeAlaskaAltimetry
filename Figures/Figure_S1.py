#import psycopg2
import numpy as N
import datetime as dtm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib
import matplotlib.cm as cmx
import matplotlib.colorbar as clbr
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from Altimetry.Altimetry import *

#generate a divergent colorscale with the colorranges provided
def make_divergent(pos,negs,maxval,minval): 
    """Generate a divergent colorscale with the colorranges provided"""
    normzero = N.abs(minval)/(maxval-minval)
    
    pos = N.where(pos<=1,pos*(1-normzero)+normzero,pos/255.)
    negs = N.where(negs<=1,negs*normzero,negs/255.)
    
    x,r,g,b = N.append(negs,pos,axis=0).T
    
    #print N.c_[x,r,g,b]
    
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
    #print cdict
    return cdict, mcolors.LinearSegmentedColormap('CustomMap', cdict)
    
outputfile="/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/Figure_S1.jpg"
#outputfile=None
show=True
annotate=True
#colorby=net
colorbar = matplotlib.cm.RdYlBu
colorrng = None
ticklabelsize=10

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
#    QUERY DATABASE FOR INTERVALS USED IN LARSEN ET AL., 2015    
data = GetLambData(longest_interval=True,as_object=True, orderby="ergi.region,ergi.name",interval_min=5)


#ADD HOC SOLUTION FO MOVING THESE GLACIERS TO FAIRWEATHER GLACIER BAY
data.region = N.where([i in ("East Yakutat Glacier","West Yakutat Glacier","Battle Glacier","Hidden Glacier", "Novatak Glacier", "West Nunatak Glacier") for i in data.name],"Fairweather Glacier Bay",data.region)

#EXTRACTING EASTING COORDINATES SO LINES CAN BE ORGANIZED BY LONGITUDE 
easting = N.array([re.findall('G(.*)E',glimsid)[0] for glimsid in data.glimsid]).astype(int)
#sorting data by longitude
data.region,easting,data.name,data.glimsid = (list(x) for x in zip(*sorted(zip(data.region, easting, data.name,data.glimsid))))

#RETREIVING GLACIER MASS BALANCE FOR EACH SURVEYED GLACIER zzz this can now be cleaned up with calc_mb
net = GetSqlData2("SELECT glimsid,SUM(mean*area)/SUM(area)*0.85 as net from resultsauto WHERE glimsid IN ('%s') GROUP BY glimsid;" %  "','".join(data.glimsid))

#MAKING SURE THE MB IS IN THE SAME ORDER AS DATA ZZZ
net2 = []
for ele in data.glimsid:
    net2.append(net['net'][N.where(net['glimsid']==ele)[0]][0])

net = N.array(net2)
colorby=net[:]

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

#CREATING FIGURE
fig = plt.figure(figsize=[7,9])
ax = fig.add_axes([0.08,0.06,0.93,0.92])

#CREATING COLOR BARS
cm = plt.get_cmap(colorbar) 
if type(colorrng) == NoneType:colorrng = [colorby.min(),colorby.max()]
cNorm  = colors.Normalize(vmin=colorrng[0], vmax=colorrng[1])
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

#CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
colorbarim = ax.imshow([colorby],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=colorrng[0], vmax=colorrng[1])

#CLEARING FIGURE AND READDING AXIS
plt.clf()
ax = fig.add_axes([0.08,0.06,0.93,0.92])

#FONT SETTINGS
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})


y = 0.1
lastregion = data.region[0]
lastgl = ''
lastrgbottom = 0.1
lastx=dtm.date(1900,1,1) 
lasty=1000

#MANUAL ADJUSTMENTS TO LABEL LOCATIONS FORWARD AND BACKWARDS
adjust={"East Yakutat":-720,"Battle":200,"Llewellyn":400,"Dinglestadt":-700,"McCarty":0,"Bear":-250,"Steele":100,"Donjek":-700,"Triumph":400,'LeConte':200,"Little Jarvis":30,"Warm Creek":30}


#LOOPING THROUGH EACH LINE AND PLOTTING IT
for i in xrange(len(data.name)): 
    if lastregion != data.region[i]:
        
        regi = data.region[i-1] # re.sub(' ','\n',data.region[i-1])
        if "Kenai" in regi:ax.annotate(regi,xy=[min(data.date1)+dtm.timedelta(days=70),y+0.05],annotation_clip=False,ha='left',fontsize=10)
        else:ax.annotate(regi,xy=[min(data.date1)+dtm.timedelta(days=70),y],annotation_clip=False,ha='left',fontsize=10)
        pt = ax.plot_date([dtm.datetime(1980,2,1),dtm.datetime(2020,2,1)], [y+0.3,y+0.3], ':',color=[0.5,0.5,0.5],lw=1.5)
        lastrgbottom = y
        y += 0.6
        
    if colorby == None:
        if lastgl != data.name[i]:
            color = N.random.rand(3,1)
    else:
        color = scalarMap.to_rgba(colorby[i])

        
    pt = ax.plot_date([data.date1[i],data.date2[i]], [y,y], '-',color=color,lw=1.8)

    if annotate:
        tdelta = lastx-data.date1[i]
        
        if lasty-y<0.15 and abs(tdelta.days)<2*365:
            x = data.date1[i]+dtm.timedelta(days=365*2)
        else:
            x = data.date1[i]

        if re.sub(" Glacier",'',data.name[i]) in adjust.keys():
            print "Moving %s Label over %i days" % (data.name[i],adjust[re.sub(" Glacier",'',data.name[i])])
            x=x+dtm.timedelta(days=adjust[re.sub(" Glacier",'',data.name[i])])

        ax.annotate(re.sub(" Glacier",'',data.name[i]), [x,y],fontsize=6)
        lastx=x
        lasty=y
    y+=0.1
    lastregion = data.region[i]
    lastgl = data.name[i]

ax.annotate(data.region[i-1],xy=[min(data.date1)+dtm.timedelta(days=70),y-0.07],annotation_clip=False,ha='left',fontsize=10)

#GETTING DATE FORMATTING FOR FIGURE
years    = YearLocator()   # every year
months   = MonthLocator()  # every month
yearsFmt = DateFormatter('%Y')

# format the ticks
ax.xaxis.set_major_locator(years)
ax.xaxis.set_major_formatter(yearsFmt)
ax.yaxis.set_ticks([])
#ax.xaxis.set_minor_locator(months)

#LIMITS AND LABELS
ax.set_xlim((727809.0, 735110.0))
ax.set_ylim([-0.3,y+0.3])
ax.set_xlabel("Time (yr)")

fig.autofmt_xdate()
for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)

#COLORBAR
cax, kw = clbr.make_axes(ax)
clr = clbr.Colorbar(cax,colorbarim) 
clr.set_label('Mass Balance (m w. eq. yr'+"$\mathregular{^{-1})}$",size = ticklabelsize)
clr.ax.tick_params(labelsize=10)
clr.ax.set_aspect(30)

if type(outputfile) == str:
    fig.savefig(outputfile,dpi=500)
    plt.close()
if show:plt.show()