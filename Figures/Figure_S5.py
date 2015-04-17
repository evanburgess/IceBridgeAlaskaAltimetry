import numpy as N
import matplotlib as plt
from scipy.stats import pearsonr
from Altimetry.Altimetry import *
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
    
#FUNTION TO PLOT EACH PLOT INCLUDING SURVEYED/UNSURVEYED POINTS, FITS, AND ANNOTATIONS
def area_plot(axis,gltype,colors,outliers=None,notoutliers=None,correct=False):
    
    if gltype==0:alpha=0.1
    else:alpha=0.7
    
    #UNSRUVEYED DATA
    d = query_glacier_results('f',gltype)
    axis.plot(d['area'],d['bal'],'.b',markersize=5,alpha=alpha,markeredgewidth=0.01,color=colors[0])#b)
    
    #PLOTTING FIT TO UNSURVEYED DATA
    if gltype!=0:
        uz,ux_new,uy_new,ucorr = loglin(d['area'],d['bal'])
    else: 
        uz,ux_new,uy_new,ucorr = loglin(d['area'],d['bal'],extend=[0.1,5000])

    axis.plot(N.exp(ux_new), uy_new,'k')
    
    #SURVEYED DATA
    #plotting outliers as black dots
    doutlier = query_glacier_results('t',gltype,add_wheres=outliers)
    axis.plot(doutlier['area'],doutlier['bal'],'ok')
    
    #plotting all of the other data (not outliers)
    d = query_glacier_results('t',gltype,add_wheres=notoutliers)
    axis.plot(d['area'],d['bal'],'ob',color=colors[1])
    
    #fitting a loglin function to the data without outliers and plotting
    if gltype!=0:
        z,x_new,y_new,corr = loglin(d['area'],d['bal'])
    else: 
        z,x_new,y_new,corr = loglin(d['area'],d['bal'],extend=[0.1,5000])
    axis.plot(N.exp(x_new), y_new,'k',linewidth=2)
    
    if correct: axis.fill_between(N.exp(x_new),y_new,uy_new,zorder=4,alpha=0.3,color='k')
    
    #PLOTTING THE GLACIER AREA CUMULATIVE PLOT
    tax=axis.twinx()
    d = query_glacier_results(gltype=gltype)
    tax.plot(N.sort(d['area']),N.cumsum(N.sort(d['area']))/totalarea*100,'r')
    
    #ANNOTING FIT STATS
    if not correct:
        axis.annotate("r = %1.2f,p = %1.2f"%(corr[0],corr[1]),[0.2,-3.5],fontsize=10)
    else:
        tax.annotate("b = %1.4f ln(area) - %1.4f\nr = %1.2f,p-value = %1.2f"%(z[0],abs(z[1]),corr[0],corr[1]),[6000,5],fontsize=10,zorder=4,ha='right')
    
    axis.set_xlim([10e-2,10e3])
    axis.set_ylim([-4,0.4])
    tax.set_ylim([0,100])


    return tax,z,uz 



#THIS IS RETRIEVING THE TOTAL GLACIER AREA OF THE REGION
conn,cur = ConnectDb()  
cur.execute("REFRESH MATERIALIZED VIEW byglacier_results;")
conn.commit()
cur.close()

#GETTING TOTAL AREA FOR CUMUALTIVE GLACIER AREA LINES
totalarea = GetSqlData2("SELECT SUM(area)::real as totalarea FROM byglacier_results;")['totalarea']#ZZZ

#FIGURE SETTINGS
lm=0.17
bm=0.07
h=0.28
w=0.7
mb = 0.02

colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.

#FIGURE SETUP
fig = plt.figure(figsize=[4,8])
ax = fig.add_axes([lm,bm,w,h])
ax2 = fig.add_axes([lm,bm+h+mb,w,h])
ax1 = fig.add_axes([lm,bm+h*2+mb*2,w,h])

ax.set_xscale('log')
ax1.set_xscale('log')
ax2.set_xscale('log')

plt.rc("font", **{"sans-serif": ["Arial"],"size": 10})


#####################################
#TIDEWATER FIGURE
area_plot(ax,1,colors=colors[[2,3]],outliers="name = 'Columbia Glacier'",notoutliers="name != 'Columbia Glacier'",correct=False)
#####################################
#LAND FIGURE
tax,z,uz = area_plot(ax1,0,colors=colors[[1,1]],outliers="bal<-1.8",notoutliers="bal>-1.8",correct=True)
#####################################
#LAKE FIGURE
lake_tax,lake_z,lake_uz = area_plot(ax2,2,colors=colors[[4,5]],outliers="name = 'East Yakutat Glacier'",notoutliers="name != 'East Yakutat Glacier'",correct=False)

#LABELS, ANNOTATIONS, TICKS
ax.set_xlabel("Glacier Area (km"+"$\mathregular{^2)}$", labelpad=0)
ax2.set_ylabel("Mass Balance (m w eq yr"+"$\mathregular{^{-1})}$", labelpad=0)
lake_tax.set_ylabel("Cumulative Glacier Area (%)", labelpad=0)

ax2.annotate("B",[0.2,-0.1],fontsize=13, fontweight='bold')
ax1.annotate("A",[0.2,-0.1],fontsize=13, fontweight='bold')
ax.annotate("C",[0.2,-0.1],fontsize=13, fontweight='bold')

ax1.xaxis.set_tick_params(labeltop='on')
ax1.xaxis.set_tick_params(labelbottom='off')
ax.xaxis.set_tick_params(labelbottom='on')
ax2.xaxis.set_tick_params(labelbottom='off')

plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS3_area_correction4_1.jpg",dpi=300)


#ESTIMATING MASS BALANCE DEPENDENCY ON AREA BIAS 
area = GetSqlData2("SELECT area::double precision FROM byglacier_results WHERE gltype=0 and surveyed='f';")['area']#ZZZ
areacorrection = z[0]*N.log(area)+z[1]-(uz[0]*N.log(area)+uz[1])
totalcorrection = N.sum(area*areacorrection)

print 'Conversion Function to be applied only to unsurveyed land-terminating glaciers:'
print "Balance = %1.5fln(area)+%1.5f-(%1.5fln(area)+%1.5f)"%(z[0],z[1],uz[0],uz[1])

print "Small Glacier Correction: %2.2f (Gts yr -1)" % (totalcorrection/1e3)
print "Small Glacier Correction: %2.2f (m w eq yr -1)" % (totalcorrection/N.sum(area))
