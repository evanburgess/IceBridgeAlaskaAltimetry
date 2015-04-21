import numpy as N
import matplotlib.pyplot as plt
from Altimetry.Altimetry import *
 
#LISTS OF GLACIERS AND INTERVALS TO CHOOSE AS EXAMPLES
names=["Baird Glacier","Field Glacier","Gillam Glacier","Kaskawulsh Glacier"]
year1s=[2001,2007,2000,1995]
year2s=[2010,2011,2010,2000]

#FIGURE LETTERS
letter=["A","B","C","D"]

#FIGURE SETUP
lm=0.15
bm=0.07
h=0.213
w=0.79
mb = 0.02

fig = plt.figure(figsize=[4,8])
ax4 = fig.add_axes([lm,bm,w,h])
ax3 = fig.add_axes([lm,bm+h+mb,w,h])
ax2 = fig.add_axes([lm,bm+h*2+mb*2,w,h])
ax1 = fig.add_axes([lm,bm+h*3+mb*3,w,h])
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})


#LOOPING THROUGH EACH AXIS AND PLOTTING EACH GLACIER
axes=[ax1,ax2,ax3,ax4]
for i,ax in enumerate(axes):
   
    data = GetLambData(removerepeats=False,verbose=True,by_column=False,as_object=True,userwhere="name='%s' AND extract(year from date1)=%s AND extract(year from date2)=%s" % (names[i],year1s[i],year2s[i]))[0]
    data.convert085()
    data.remove_upper_extrap(remove_bottom=True)
    data.normalize_elevation()
    
    pts = GetSqlData2("SELECT z1,dz FROM xpts2 WHERE lambid=%i" % data.lambid)  
    x = pts['z1']
    y = pts['dz']
    
    y*=0.85  # converting to mweq
    
    ax.plot((x - data.min)/(data.max-data.min),y,'o',alpha=0.04,color=[0.7,0.7,0.7])    #PLOTTING POINTS 
    ax.plot(data.norme,data.normdz,'r',linewidth=1.5,zorder=3) #PLOTTING LINES

    #PLOTTING FIGURE CORRECTION
    data.fix_terminus()
    data.remove_upper_extrap()
    data.normalize_elevation()

    ax.plot(data.norme,data.normdz,color=[0,1,51/255.],linewidth=1.5,zorder=2)

    #LIMITS, LABELS, ANNOTATIONS
    ax.set_xlim([0,0.5])
    ax.set_ylim([-7,2])

    if i==3:ax.set_xlabel("Normalized Elevation (m)")
    if i!=3:ax.xaxis.set_tick_params(labelbottom='off')
    ax.annotate(letter[i],[0.02,1],fontsize=12, fontweight='bold')

#YAXIS LABEL
plt.figtext(0.01,0.52,"Elevation Change (m w. eq. yr"+"$\mathregular{^{-1})}$",rotation='vertical',verticalalignment='center',horizontalalignment='left')

plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/terminus_fix.jpg",dpi=300)


    