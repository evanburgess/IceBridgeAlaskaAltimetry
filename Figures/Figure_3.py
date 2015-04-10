import numpy as N
from types import *
from pylab import Line2D
import matplotlib as plt
import pickle
from scipy.stats.mstats import kruskalwallis
from scipy.stats import mannwhitneyu
import matplotlib as mpl
from Altimetry.Interface import *


def plot_brace(ax,left,right,y,height,up=True,color='k',annotate=None,fontsize=12,bbox=None,zorder=4):
    if up:hgt = height/2.
    else: hgt = -height/2.
    
    mid = (left+right)/2.
    if type(bbox) != NoneType: bbox = dict(fc="white", lw=0)
    
    brace,tip = ax.plot([left,left,right,right],[y-hgt,y,y,y-hgt],'-%s' % color,[mid,mid],[y,y+hgt],'-%s' % color)
    if type(annotate)!=NoneType:
        if up:vert='bottom'
        else:vert='top'
        txt = ax.annotate(annotate,[mid,y+hgt*1.2],horizontalalignment='center',verticalalignment=vert,fontsize=fontsize,bbox=bbox,zorder=zorder)
        return brace,tip,txt
    else:
        return brace,tip
 
a = True
if a:
    survdata = GetSqlData2("SELECT t.glimsid,ergi.name,t.bal,ergi.region,ergi.continentality,ergi.gltype FROM ergi INNER JOIN (SELECT glimsid,SUM(mean*resultsauto.area)/SUM(resultsauto.area)*0.85 as bal, MAX(surveyed::int) as surveyed FROM resultsauto WHERE surveyed='t' GROUP BY glimsid) AS t ON ergi.glimsid=t.glimsid ORDER BY region;")  #zzz
    regions = GetSqlData2("SELECT DISTINCT region::text FROM ergi;")['region'].astype('a30')  #zzz
    d = GetSqlData2("SELECT gltype,surveyed,SUM(mean*area)/SUM(area)*0.85 as myr,SUM(mean*area)/1e9*0.85 as gt,(((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/SUM(area)*0.85)^2+(0)^2)^0.5::real as myrerr,(((((SUM(error*area)/SUM(mean*area))^2+(0.06/0.85)^2)^0.5)*SUM(mean*area)/1e9*0.85)^2 + (0)^2)^0.5::real as gterr,sum(area)/1e6::real as area from resultsauto group by gltype,surveyed order by gltype,surveyed;") #zzz 

    pickle.dump([survdata,regions,d], open( "/Users/igswahwsmcevan/Desktop/temp.p", "wb" ))
else:
    survdata,regions,d = pickle.load(open( "/Users/igswahwsmcevan/Desktop/temp.p", "rb" ))

#SWITICHING GLACIER FROM GROUP TO GROUP FOLLOWING CHRIS' SUGGESTIONS
survdata['region']=N.where([i in ("East Yakutat Glacier","West Yakutat Glacier","Battle Glacier","Hidden Glacier", "Novatak Glacier", "West Nunatak Glacier") for i in survdata['name']],"Yakutat",survdata['region'])##zzz
survdata['gltype']=N.where([i in ("Fairweather Glacier") for i in survdata['name']],0,survdata['gltype'])#zzz
survdata['gltype']=N.where([i in ("Riggs Glacier","Muir Glacier") for i in survdata['name']],1,survdata['gltype'])   #zzz
survdata['region']=N.where([i in ("Columbia Glacier","Yanert Glacier") for i in survdata['name']],"outliers2",survdata['region'])##zzz

#settings
ylim = [-4.,0.55]
zones = ['Interior','South-Central','Southeast'] 
gltype=[0,2,1]

# A FEW GLACIERS ARE OUTSIDE ANY REGION, WE WON'T SHOW THESE REGIONS HERE SO WE ARE REMOVING REGIONS OF NONE
regions = regions[N.where(regions!='None')]

# Removing the aleutian chain glaciers and the brooks range
regions = regions[[7,8,0,9,6,1,2,3]]

#CREATING A BROADER ZONE FIELD FROM THE MOUNTAIN RANGES FROM REGION KEY
survdata['zone'] = survdata['region'].astype(str)
for j,i in enumerate(survdata['zone']):
    survdata['zone'][j] = re.sub('Alaska Range','Interior',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Aluetian Range','South-Central',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Brooks Range','Interior',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Chugach Range','South-Central',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Coast Range BC','Southeast',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Fairweather Glacier Bay','Southeast',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Juneau Icefield','Southeast',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Kenai Mountains','South-Central',survdata['zone'][j])
    survdata['zone'][j] = re.sub('St. Elias Mountains','South-Central',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Stikine Icefield','Southeast',survdata['zone'][j])
    survdata['zone'][j] = re.sub('Wrangell Mountains','Interior',survdata['zone'][j])

#yakutat outliers
yakoutliers = survdata['bal'][N.where(survdata['region']=="Yakutat")[0]]
yaktype = survdata['gltype'][N.where(survdata['region']=="Yakutat")[0]]/2.+10

#yakutat outliers
outliers2 = survdata['bal'][N.where(survdata['region']=="outliers2")[0]]
type2 = survdata['gltype'][N.where(survdata['region']=="outliers2")[0]]*7

#FORMATTING DATA FOR BOXPLOT
boxdata = []
pointdata= []
xs=[]
xi=0
for reg in zones:
    for gl in gltype:
        pointdata.append(survdata['bal'][N.where(N.logical_and(survdata['zone']==reg,survdata['gltype']==gl))])
        xs.append(xi)
        xi+=1
    xi+=2
xs = N.array(xs)
    
#COLORS 
colors = N.array([[240,201,175],[163,100,57],[179,203,252],[45,80,150],[189,237,166],[75,150,38]])/255.

colorlistdark = N.array([[0,0,0]])
for i in xrange(len(pointdata)):colorlistdark = N.append(colorlistdark,colors[[1,5,3],:],axis=0)
colorlistdark = N.delete(colorlistdark,0,0)
colorlistdark=colorlistdark

#CHOOSING COLORS
picks=[]
ns = N.array([bd.size for bd in pointdata])
for i,n in enumerate(ns):
    if n!=0:picks.append(i)

#what side to put the median annotation
annosides = ['right','left','left','right','left','left','right','left','left']

#FIGURE SET UP
fig3 = plt.figure(figsize=[5,3.6])
ax3 = fig3.add_axes([0.1,0.02,0.48,0.94],frameon=True)
ax = fig3.add_axes([0.72,0.02,0.24,0.94],frameon=True)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 11})

#PLOTTING BOXPLOT
box = ax3.boxplot(pointdata,positions=N.array(xs),widths=1,sym='o',patch_artist=True,whis=[5,95])

#PLOTING OUTLIER FLIERS
wyak = ((yaktype-10)*4).astype(int)
ax3.scatter(yaktype,yakoutliers,marker='D',c=colorlistdark[wyak],alpha=1,lw=0.5)
ax3.scatter(type2,outliers2,marker='D',c=colorlistdark[[0,2]],alpha=1,lw=0.5)
  
#COLORING BOXPLOTS, WHISKERS AND FLIERS
for i,bx in enumerate(box['boxes']):
    bx.set_facecolor(colorlistdark[i])
    bx.set_edgecolor(colorlistdark[i])
for i,bx in enumerate(box['medians']):
    if annosides[i]=='right':
        tiepoint = bx.get_path()._vertices[0]
        offset = -2
    else:
        tiepoint = bx.get_path()._vertices[1]
        offset = 4
    ax3.annotate("%3.2f" % bx.get_path()._vertices[0][1],tiepoint,ha=annosides[i],va='center',size=8,xytext=(offset, 0), textcoords='offset points')
    bx.set_color(color='k')
    bx.set_lw(2)
for i,bx in enumerate(box['caps']):
    bx.set_lw(0)
for i,bx in enumerate(box['whiskers']):
    bx.set_color(color=N.repeat(colorlistdark,2,axis=0)[i])
    bx.set_ls('-')
    bx.set_lw(2)
for i,bx in enumerate(box['fliers']):
    bx.set_markerfacecolor(colorlistdark[i])
    bx.set_markeredgewidth(0.5)
    bx.set_markersize(5)
    bx.set_alpha(1)


#ANNOTATING N VAULES AT THE TOP OF FIGURE
ax3.annotate("N =",[-1.5,0.3],horizontalalignment='center',annotation_clip=False, weight='bold', size=10)
for n,x in zip(ns[picks],xs[picks]):
    y=0.3
    if n==28: x-=0.2
    ax3.annotate(n,[x,y],horizontalalignment='center',size=8)
    
#SETTING FIGURE LIMITS, TICKS, LABELS
ax3.set_ylim(ylim)
ax3.set_xlim([ax3.get_xlim()[0]-2.2,ax3.get_xlim()[1]+2.4])
ax3.set_ylabel("Mass Balance (m w. eq. yr"+"$\mathregular{^{-1})}$")
ax3.set_yticks(N.arange(ylim[0],ylim[1],1).astype(int))
ax3.axes.get_xaxis().set_visible(False)
ax3.get_yaxis().tick_left()

#PLOTTING HORIZONTAL GRID LINES
gridlines = [ax3.plot(ax3.get_xlim(),[yt,yt],'-',color='0.85',zorder=0,lw=0.5) for yt in N.arange(-5,2,0.5)]


#PLLOTTING BRACES FOR INTERIOR SC AND SE
begs=N.array(xs)[picks]-0.5
ends = N.array(xs)[picks]+0.5
braceys=[-2.5,-3,-2.5]
begs = begs[[0,2,5]]
ends = ends[[1,4,7]]
zones = ['Interior','Southcentral','Southeast']
for by,beg,end,reg in zip(braceys,begs,ends,zones):plot_brace(ax3,beg,end,by,0.2,up=False,annotate=reg,fontsize=10)

#PLOTTING THE ZERO LINE
xlim =ax3.get_xlim()
ax3.plot(xlim,[0,0],'-k')
ax3.set_xlim(xlim)


########################################################################
#FIGURE B 

#plot settings
width = 0.8
barlocs = [0,2,1]

#ADDING ERROR FOR SMALL GLACIER BIAS from output from balance_by_area2.py
uneven_error = [list(d['gterr']),list(d['gterr'])]
uneven_error[0][0]+=5

#PLOTTING
pl1 = ax.bar(N.array(barlocs), d['gt'][[1,3,5]], color=colors[[1,3,5]], width=width,yerr=N.array(uneven_error)[:,[1,3,5]],error_kw=dict(ecolor='k'))
pl2 = ax.bar(N.array(barlocs), d['gt'][[0,2,4]], color=colors[[0,2,4]], width=width,yerr=N.array(uneven_error)[:,[0,2,4]],error_kw=dict(ecolor='k'),bottom=d['gt'][[1,3,5]])

#ANNOTATIONS GLACIER TYPE
ax.annotate('Land',[0+width/2,-64],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
ax.annotate('Lake',[1+width/2,-25],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)
ax.annotate('Tidewater',[2+width/2,-10],rotation=90,horizontalalignment='center',verticalalignment='top',fontsize=10)

#AXES SETTINGS
ax.axes.get_xaxis().set_visible(False)
ax.get_yaxis().tick_left()
ax.set_ylim([-77,0])
for tick in ax.yaxis.get_major_ticks():tick.label.set_fontsize(11) 
xmin, xmax = ax.get_xaxis().get_view_interval()
ymin, ymax = ax.get_yaxis().get_view_interval()
ax.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=1.5))
ax.add_artist(Line2D((xmin, xmax), (0, 0), color='black', linewidth=1.))
ax.plot([0.7, xmax],[-74,-74],'--k')
ax.set_ylabel("Mass Balance (Gt yr"+"$\mathregular{^{-1}}$)",fontsize=11,labelpad=0)


#A,B PLOT ANNOTATIONS
font = mpl.font_manager.FontProperties(family='Arial', weight='bold', size=15)
ax3.annotate('A',[-1.3,-3.8],horizontalalignment='center',verticalalignment='center',fontproperties=font)
ax.annotate('B',[0.4,-74],horizontalalignment='center',verticalalignment='center',fontproperties=font, annotation_clip=False)

plt.show()
fig3.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/Figure_3.jpg",dpi=300)

#FINDING STATISTICAL DIFFERENCES BETWEEN GROUPS
lands = N.concatenate((pointdata[0],pointdata[3],pointdata[6]))
lakes = N.concatenate((pointdata[1],pointdata[4],pointdata[7]))
lakes2 = lakes.compress(lakes>-1.8)
lands2 = lands.compress(lands>-1.8)

print "Difference between Southcentral land/lake with outliers removed: %4.2f" % kruskalwallis(pointdata[3],pointdata[4])[1]
print "Difference between Southeast land/lake with outliers removed: %4.2f" % kruskalwallis(pointdata[6],pointdata[7])[1]
print "Difference between Southcentral land/Southeast land with outliers removed: %4.2f" % kruskalwallis(pointdata[3],pointdata[6])[1]
print "Difference between Southcentral land/Interior land with outliers removed: %4.2f" % mannwhitneyu(N.compress(pointdata[0]>-2.8,pointdata[0]),pointdata[3])[1]

plt.show()
