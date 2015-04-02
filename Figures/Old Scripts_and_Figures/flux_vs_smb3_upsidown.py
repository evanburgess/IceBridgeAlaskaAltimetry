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
import statsmodels.api as sm
import ConfigParser
from glob import glob

def label_points(ax,x,y,text,miny=3,fontsize=8):
    for i,name in enumerate(text):
        if y[i]>miny:
            name2 = re.sub(" Glacier", "",name)
            
            if (x[i]-ax.get_xlim()[0])/(ax.get_xlim()[1]-ax.get_xlim()[0])<0.1:align='left'
            else:align='right'
            
            print name,(y[i]-ax.get_ylim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])
            if (y[i]-ax.get_ylim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])>0.95:align2='top'
            else:align2='bottom'
            
            ax.annotate(name2,[x[i],y[i]],fontsize=fontsize, horizontalalignment=align, verticalalignment=align2)
    

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

def lin(x,y,extend=None):
    corr = scipy.stats.pearsonr(x, y)
    z = N.polyfit(x, y, 1)
    f = N.poly1d(z)
    
    if type(extend)==NoneType:
        x_new = N.linspace(N.min(x),N.max(x), 50)
        #print [N.log(N.min(x)),N.log(N.max(x))]
    else:
        x_new = N.linspace(extend[0],extend[1], 50)
        #print 'extend',[N.log(extend[0]),N.log(extend[1])]
    y_new = f(x_new)
    
    return z,x_new,y_new,corr

from Altimetry.Interface import *

d = GetLambData(longest_interval=True,userwhere="ergi.gltype='1'", as_object=True,results=True)
d.fix_terminus()
d.remove_upper_extrap(remove_bottom=False)
d.normalize_elevation()


blue =N.array([45,80,150])/255.

flx = d.eb_bm_flx.astype(float)[:]*1000./d.area
smb = d.smb.astype(float)[:]

#Accomodating glaciers with no calving flux
flx = N.where(N.isnan(flx),0,flx)
smb = N.where(N.isnan(smb),d.rlt_totalkgm2,smb)


fig = plt.figure(figsize=[3.8,4.1]) 
ax = fig.add_axes([0.15,0.005,0.8,0.97])##############################################

plt.rc("font", **{"sans-serif": ["Arial"],"size": 11})


ax.xaxis.labelpad = -3
ax.yaxis.labelpad = -3

w = N.where(flx<3)

smb2 = smb[w]
flx2 = flx[w]
name2 = N.array(d.name)[w]

#ax.scatter(smb, flx,'ok',markersize=5)
#ax.scatter(smb2,flx2,'o',markersize=5)

colorbar = 'RdBu'
jet = cm = plt.get_cmap(colorbar) 
cNorm  = colors.Normalize(vmin=-1, vmax=1)
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

colorbarim1 = ax.imshow([d.bm_length.astype(float)],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=-1,vmax=1)
plt.clf()

ax = fig.add_axes([0.15,0.1,0.8,0.88])##############################################

wnans=N.where(N.isnan(d.bm_length.astype(float)))


ax.scatter(smb,flx,c=d.bm_length.astype(float),cmap=jet,norm=cNorm,s=40)
ax.scatter(smb[wnans],flx[wnans],c='0.5',s=40)
z,x_new,y_new,corr = lin(smb2,flx2)

ax.plot(x_new, y_new,'k-')

ax.plot([-5,10], [-5,10],'--',color=[0.5,0.5,0.5],lw=1.5)

#cax, kw = clbr.make_axes(ax,location='right',pad=0.1)##############################################
cax = fig.add_axes([0.78,0.3,0.05,0.5])
clr = clbr.Colorbar(cax,colorbarim1,ticks=N.arange(-1,1.1,0.5)) 
clr.set_label('Terminus Position Change (km year'+"$\mathregular{^{-1}})$", labelpad=-3)
clr.set_ticks([-1,0,1])

smblin = smb2[:]
smblin = sm.add_constant(smblin, prepend=False)
model=sm.OLS(flx2,smblin)
result=model.fit()
result.bse

intercepterr = N.arange(result.params[1]-result.bse[1],result.params[1]+result.bse[1],0.01)
sloperr = N.arange(result.params[0]-result.bse[0],result.params[0]+result.bse[0],0.01)

for i in intercepterr:
    for j in sloperr:
        ax.plot(smb2,j*smb2+i,'-',color=[0.8,0.8,0.8],zorder=0)


#REGRESSION SIG
ax.text(0.7,0.28,"r=%1.2f, sig=%1.3f"%(corr[0],corr[1]),fontsize=11,transform=ax.transAxes,ha='right')
ax.text(0.97,0.94,"Negative Total Mass Balance",fontsize=11,transform=ax.transAxes,ha='right', style='italic',bbox={'facecolor':'white', 'pad':4})
ax.text(0.97,0.04,"Positive Total Mass Balance",fontsize=11,transform=ax.transAxes,ha='right', style='italic',bbox={'facecolor':'white', 'pad':4})


label = ['Columbia','LeConte','Tsaa','Hubbard','Taku','Margerie','Yahtse']
va = ['top','bottom','bottom','top','top','top','top']
ha = ['left','right','left','left','left','left','left']
offs = [0.03,0.03,-0.05,0.03,0.03]
#LABELING COLUMBIA
j=0
for i in xrange(len(smb)):
    if re.sub(' Glacier','',d.name[i]) in label:
        w=N.where(re.sub(' Glacier','',d.name[i])==N.array(label))[0]
        if va[w]=='top':vo=-0.04
        else:vo=0.03
        if ha[w]=='left':ho=0.04
        else:ho=-0.04
        ax.text(smb[i]+ho, flx[i]+vo,re.sub(' Glacier','',d.name[i]),fontsize=11,va=va[w],ha=ha[w])
    #if flx[i]>3:ax.text(smb[i]+0.03, flx[i]-0.03,re.sub(' Glacier','',d.name[i]),fontsize=9,ha='left', va='top')
    #if smb[i]>flx[i]:
    #    print d.name[i]
    #    ax.text(smb[i]+0.03, flx[i]+offs[j],re.sub(' Glacier','',d.name[i]),fontsize=9,ha='left', va=va[j])
    #    j+=1
ax.set_xlabel("SMB (m w eq yr"+"$\mathregular{^{-1})}$",fontsize=11,labelpad=-1)
ax.set_ylabel("Norm. Calving Flux (m w eq yr"+"$\mathregular{^{-1}})$",fontsize=11,labelpad=0.5)

for label in ax.xaxis.get_ticklabels():label.set_size(11)
for label in ax.yaxis.get_ticklabels():label.set_size(11)

ax.yaxis.set_ticks(N.arange(0,5))
#ax.xaxis.set_ticks(N.arange(0,5))
ax.set_ylim([4,-0.5])
ax.set_xlim([-0.5,3])
ax.set_xticks([0,1,2,3])

plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/flux_vs_smb3.jpg",dpi=300)
#fig = plt.figure(figsize=[4,8])
#ax = fig.add_axes([lm,bm+h*2+mb*2,w,h])
#ax1 = fig.add_axes([lm,bm+h+mb,w,h])
#ax2 = fig.add_axes([lm,bm,w,h])


#ax.plot(d.bm_length.astype(float),d.eb_bm_flx.astype(float),'o',color=blue)
#ax.set_xlabel("Length Change (km)",fontsize=11)
#ax.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
#label_points(ax,d.bm_length.astype(float),d.eb_bm_flx.astype(float),d.name,miny=0.8)
#
#thinning = [N.ma.mean(dz[0:3]) for dz in d.normdz]
#ax1.plot(thinning,d.eb_bm_flx.astype(float),'o',color=blue)
#ax1.set_xlabel("Terminus Elevation Change (m yr"+"$^{-1}$"+")",fontsize=11)
#ax1.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
#label_points(ax1,thinning,d.eb_bm_flx.astype(float),d.name,miny=0.8)
#
#ax2.plot(d.rlt_totalkgm2,d.eb_bm_flx.astype(float),'o',color=blue)
#ax2.set_xlabel("Mass Balance (m w. eq. yr"+"$^{-1}$"+")",fontsize=11)
#ax2.set_ylabel("Calving Flux (Gt yr"+"$^{-1}$"+")",fontsize=11)
#label_points(ax2,d.rlt_totalkgm2,d.eb_bm_flx.astype(float),d.name,miny=0.8)
#    #for i,name in enumerate(d.name):
#    #if d.eb_bm_flx.astype(float)[i]>0.8:
#    #    name2 = re.sub(" Glacier", "",name)
#    #    if d.rlt_totalkgm2[i]<-3:align='left'
#    #    else:align='right'
#    #    
#    #    if d.eb_bm_flx.astype(float)[i]>3:align2='bottom'
#    #    else:align2='top'
#    #    
#    #    ax2.annotate(name2,[d.rlt_totalkgm2[i],d.eb_bm_flx.astype(float)[i]],fontsize=8, horizontalalignment=align, verticalalignment=align2)
#    
#ax.text(0.05, 0.05, "A.", transform=ax.transAxes,fontsize=13, fontweight='bold', va='bottom')
#ax1.text(0.05, 0.05, "B.", transform=ax1.transAxes,fontsize=13, fontweight='bold', va='bottom')
#ax2.text(0.05, 0.05, "C.", transform=ax2.transAxes,fontsize=13, fontweight='bold', va='bottom')
#
#ax2.xaxis.set_ticks(N.arange(ax2.get_xlim()[0],ax2.get_xlim()[1],1))
#
#plt.show()

#fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/flux_vs_advance.jpg",dpi=300)