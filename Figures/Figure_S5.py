import numpy as N
import matplotlib as plt
from scipy.stats import pearsonr
from Altimetry.Interface import *
import time

#a log-linear fit
def loglin(x,y,extend=None):
    #n.log is a natural log
    corr = pearsonr(N.log(x), y)
    z = N.polyfit(N.log(x), y, 1)
    f = N.poly1d(z)
    
    if type(extend)==NoneType:
        x_new = N.linspace(N.log(N.min(x)),N.log(N.max(x)), 50)
        #print [N.log(N.min(x)),N.log(N.max(x))]
    else:
        x_new = N.linspace(N.log(extend[0]),N.log(extend[1]), 50)
        #print 'extend',[N.log(extend[0]),N.log(extend[1])]
    y_new = f(x_new)
    
    return z,x_new,y_new,corr
    
def query_glacier_results(*argv,**kwargs):
    a=list(argv[:])
    if len(a)>0:a[0] ="surveyed='%s'" % a[0]
    if len(a)>1:a[1] ="gltype=%s" % a[1]

    if 'gltype' in kwargs and len(a)>1:raise "CANT INPUT A GLTYPE TWICE"
    if 'gltype' in kwargs and len(a)<2:a.append("gltype=%s" % kwargs['gltype'])
    if 'add_wheres' in kwargs:a.append(kwargs['add_wheres'])

    return GetSqlData2("SELECT area::real,bal,surveyed FROM byglacier_results WHERE %s;" % " AND ".join(a))#ZZZ

#PLOTTING A LOG LINEAR FIT GIVEN INPUT DATA
def plot_loglindata(axis,area,bal):
    z,x_new,y_new,corr = loglin(area,bal)
    axis.plot(N.exp(x_new), y_new,'k')    
    
conn,cur = ConnectDb()  

#THIS IS RETRIEVING THE TOTAL GLACIER AREA OF THE REGION
cur.execute("REFRESH MATERIALIZED VIEW byglacier_results;")
conn.commit()

totalarea = GetSqlData2("SELECT SUM(area)::real as totalarea FROM byglacier_results;")['totalarea']#ZZZ

lm=0.17
bm=0.07
h=0.28
w=0.7
mb = 0.02

colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.

fig = plt.figure(figsize=[4,8])
ax = fig.add_axes([lm,bm,w,h])
ax2 = fig.add_axes([lm,bm+h+mb,w,h])
ax1 = fig.add_axes([lm,bm+h*2+mb*2,w,h])

ax.set_xscale('log')
ax1.set_xscale('log')
ax2.set_xscale('log')

tax=ax.twinx()
tax1=ax1.twinx()
tax2=ax2.twinx()

plt.rc("font", **{"sans-serif": ["Arial"],"size": 10})


def area_plot(axis,gltype,colors,outliers=None,notoutliers=None,correct=False):
    
    #UNSRUVEYED DATA
    d = query_glacier_results('f',gltype)
    axis.plot(d['area'],d['bal'],'.b',markersize=5,alpha=0.7,markeredgewidth=0.01,color=colors[0])#b)
    
    #PLOTTING FIT TO UNSURVEYED DATA
    z,x_new,y_new,corr = loglin(d['area'],d['bal'])
    axis.plot(N.exp(x_new), y_new,'k')
    
    #SURVEYED DATA
    #plotting outliers as black dots
    doutlier = query_glacier_results('t',gltype,add_wheres=outliers)
    ax.plot(doutlier['area'],doutlier['bal'],'ok')
    
    #plotting all of the other data (not outliers)
    d = query_glacier_results('t',gltype,add_wheres=notoutliers)
    ax.plot(d['area'],d['bal'],'ob',color=colors[1])
    
    #fitting a loglin function to the data without outliers and plotting
    z,x_new,y_new,corr0 = loglin(d['area'],d['bal'])
    ax.plot(N.exp(x_new), y_new,'k',linewidth=2)
    
    #PLOTTING THE GLACIER AREA CUMULATIVE PLOT
    tax=axis.twinx()
    d = query_glacier_results(gltype=gltype)
    tax.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')
    
    axis.set_xlim([10e-2,10e3])
    axis.set_ylim([-4,0.4])
    tax.set_ylim([0,100])


####################################
#NOT SURVEYED
####################################
markersz = 5
d = query_glacier_results('f',1)
ax.plot(d['area'],d['bal'],'.b',markersize=markersz,alpha=0.7,markeredgewidth=0.01,color=colors[2])#b)
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k')

d = query_glacier_results('f',0)
ax1.plot(d['area'],d['bal'],'.r',markersize=markersz,alpha=0.1,markeredgewidth=0.01,color=colors[1])#r
z_u1,x_new_u1,y_new_u1,corr_u1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new_u1), y_new_u1,'k')

d = query_glacier_results('f',2)
ax2.plot(d['area'],d['bal'],'.g',markersize=markersz,alpha=0.7,markeredgewidth=0.01,color=colors[4])#g
z,x_new,y_new,corr = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k')


####################################
#SURVEYED
####################################
#TIDEWATER
dcol = query_glacier_results('t',1,add_wheres=" name = 'Columbia Glacier'")
ax.plot(dcol['area'],dcol['bal'],'ok')
d = query_glacier_results('t',1,add_wheres=" name != 'Columbia Glacier'")
ax.plot(d['area'],d['bal'],'ob',color=colors[3])
z,x_new,y_new,corr0 = loglin(d['area'],d['bal'])
ax.plot(N.exp(x_new), y_new,'k',linewidth=2)

d = query_glacier_results(gltype=1)

tax.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')

#LAND
d = query_glacier_results('t',0,add_wheres="bal<-1.8")
ax1.plot(d['area'],d['bal'],'ok')
d = query_glacier_results('t',0,add_wheres="bal>-1.8")
ax1.plot(d['area'],d['bal'],'or',color=colors[1])
z1,x_new1,y_new1,corr1 = loglin(d['area'],d['bal'],extend=[0.1,5000])
ax1.plot(N.exp(x_new1), y_new1,'k',linewidth=2)

ax1.fill_between(N.exp(x_new1),y_new1,y_new_u1,zorder=4,alpha=0.3,color='k')

d = query_glacier_results(gltype=0)

tax1.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')

#LAKE
d = query_glacier_results('t',2,add_wheres="name = 'East Yakutat Glacier'")
ax2.plot(d['area'],d['bal'],'ok')
d = query_glacier_results('t',2,add_wheres="name != 'East Yakutat Glacier'")
ax2.plot(d['area'],d['bal'],'og',color=colors[5])
z,x_new,y_new,corr2 = loglin(d['area'],d['bal'])
ax2.plot(N.exp(x_new), y_new,'k',linewidth=2)


d = query_glacier_results(gltype=2)
tax2.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')

#plt.show()

ax.set_xlabel("Glacier Area (km"+"$\mathregular{^2)}$", labelpad=0)
ax2.set_ylabel("Mass Balance (m w eq yr"+"$\mathregular{^{-1})}$", labelpad=0)
tax1.set_ylabel("Cumulative Glacier Area (%)", labelpad=0)

ax.set_xlim([10e-2,10e3])
ax1.set_xlim([10e-2,10e3])
ax2.set_xlim([10e-2,10e3])

ax.set_ylim([-4,0.4])
ax1.set_ylim([-4,0.4])
ax2.set_ylim([-4,0.4])


tax.set_ylim([0,100])
tax1.set_ylim([0,100])
tax2.set_ylim([0,100])

#print [i.get_position() for i in ax.yaxis.get_ticklabels()]
tax1.annotate("b = %1.4f ln(area) - %1.4f\nr = %1.2f,p-value = Z%1.2f"%(z[0],abs(z[1]),corr1[0],corr1[1]),[6000,5],fontsize=10,zorder=4,ha='right')
ax2.annotate("r = %1.2f,p = %1.2f"%(corr2[0],corr2[1]),[0.2,-3.5],fontsize=10)
ax.annotate("r = %1.2f,p = %1.2f"%(corr0[0],corr0[1]),[0.2,-3.5],fontsize=10)
#print [0.2,ax.yaxis.get_ticklabels()[1].get_position()[1]]
#print ax.yaxis.get_ticklabels()[1].get_position()
ax2.annotate("B",[0.2,-0.1],fontsize=13, fontweight='bold')
ax1.annotate("A",[0.2,-0.1],fontsize=13, fontweight='bold')
ax.annotate("C",[0.2,-0.1],fontsize=13, fontweight='bold')

#for label in ax.yaxis.get_ticklabels():label.set_size(10)
#for label in ax1.yaxis.get_ticklabels():label.set_size(10)
#for label in ax2.yaxis.get_ticklabels():label.set_size(10)
#
#for label in tax.yaxis.get_ticklabels():label.set_size(10)
#for label in tax1.yaxis.get_ticklabels():label.set_size(10)
#for label in tax2.yaxis.get_ticklabels():label.set_size(10)

ax1.xaxis.set_tick_params(labeltop='on')
ax1.xaxis.set_tick_params(labelbottom='off')
ax.xaxis.set_tick_params(labelbottom='on')
ax2.xaxis.set_tick_params(labelbottom='off')

#for label in ax.xaxis.get_ticklabels():label.set_size(10)
#for label in ax2.xaxis.get_ticklabels():label.set_size(10)

print 'Conversion Function'
print "Balance = %1.5fln(area)+%1.5f-(%1.5fln(area)+%1.5f)"%(z1[0],z1[1],z_u1[0],z_u1[1])

cur.execute("ALTER TABLE temp2 DROP COLUMN IF EXISTS area_corr;")
cur.execute("ALTER TABLE temp2 ADD COLUMN area_corr real;")
cur.execute("UPDATE temp2 SET area_corr=%1.5f*ln(area)+%1.5f-(%1.5f*ln(area)+%1.5f) WHERE gltype=0 and surveyed=0;"%(z1[0],z1[1],z_u1[0],z_u1[1]))

conn.commit()
print "Small Glacier Correction in Gts yr -1: %s" % GetSqlData2("SELECT SUM(area*1000000*area_corr)/1e9 as correction FROM temp2;")['correction']
print "Small Glacier Correction in m w eq yr -1: %s" % GetSqlData2("SELECT SUM(area*area_corr)/SUM(area) as correction FROM temp2 WHERE gltype=0 and surveyed=0;")['correction']
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS3_area_correction4.jpg",dpi=300)