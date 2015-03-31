# -*- coding: utf-8 -*-
#import xlrd
import re
import unicodedata
import numpy as np
import datetime as dtm
import os
import glob
import simplekml as kml
import subprocess
import matplotlib.pyplot as plt
from osgeo import gdal
from types import *
import sys
import time
# from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from osgeo.gdalnumeric import *
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.mlab as mlab
import scipy.misc
import matplotlib
import matplotlib.colors as colors
import matplotlib.cm as cmx
import scipy.stats as stats
import scipy.stats.mstats as mstats
from numpy.ma import MaskedArray, masked, nomask
import numpy.ma as ma
import pickle
from itertools import product

import ConfigParser

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry.Interface import *

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
    #return 1,2,3

    
def plotthis(data):
    fig = plt.figure(figsize=[10,8])
    ax = fig.add_axes([0.11,0.31,0.74,0.6])
    for line in data.normdz:pl1 = ax.plot(data.norme, line,'r-',alpha=0.2)
    pl1 = ax.plot(data.norme, data.dzs_mean,'k-')
    pl2 = ax.plot(data.norme, data.dzs_mean-data.dzs_sem,'k--',data.norme, data.dzs_mean+data.dzs_sem,'k--')    
    plt.show()
    
def partitionbox(axes,data,center,totalwidth,spacing,cchoice,boxwidth=None,showfliers=True):
    
    if type(boxwidth)==NoneType:boxwidth = (totalwidth-spacing*(len(data)-1))/len(data)
    
    if len(data)>1:positions = N.linspace(center-totalwidth/2+boxwidth/2,center+totalwidth/2-boxwidth/2,len(data))
    else:positions=center
    
    if showfliers:fly = 'o'
    else:fly=''
    box = axes.boxplot(data,positions=positions,widths=boxwidth,sym=fly,patch_artist=True,whis=[5,95])
    
    for clr,bx in zip(cchoice,box['boxes']):
        bx.set_facecolor(clr)
        bx.set_edgecolor(clr)
    for bx in box['medians']:
        bx.set_color(color='k')
        bx.set_lw(1)
    for i,bx in enumerate(box['caps']):
        #bx.set_color(color=N.repeat(colorlist,2,axis=0)[i])
        bx.set_lw(0)
    for clr,bx in zip([x1 for pair in zip(cchoice,cchoice) for x1 in pair],box['whiskers']):
        bx.set_color(color=clr)
        bx.set_ls('-')
        bx.set_lw(2)
    
    if showfliers:
        for clr,bx in zip(cchoice,box['fliers']):
            bx.set_markerfacecolor(clr)
            bx.set_markeredgecolor(clr)
            bx.set_markeredgewidth(0.5)
            bx.set_markersize(3)
            bx.set_alpha(0.5)


                
    return box

def set_colors(allwhere,condition,usethis,colors=None):
    
    if type(colors)==NoneType:colors=N.repeat('0.5',len(allwhere))
    
    a=[]
    for i,boo in enumerate([re.search(condition,i)!=None for i in allwhere]):

        if boo:a.append(usethis)
        else:a.append(colors[i])
    return a


    
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

runall=False

if runall:    
    surveyeddata = GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True)
    surveyeddata.fix_terminus()
    #surveyeddata.remove_upper_extrap()
    surveyeddata.normalize_elevation()
    surveyeddata.calc_dz_stats()
    #surveyeddata.extend_upper_extrap()


    outputs = []
    titles = []
    results = []
    allwheres = []
    
    #################################################################################
    ##All data excluding Columbia, Yakutat and surge-type glaciers
    #################################################################################
    titles.append("No partition")
    outputs.append(GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, userwhere="glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')",get_hypsometry=True))
    outputs[-1].fix_terminus()
    outputs[-1].remove_upper_extrap()
    outputs[-1].normalize_elevation()
    outputs[-1].calc_dz_stats()
    outputs[-1].extend_upper_extrap()
    outputs[-1].calc_mb()
    
    outp=GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, userwhere="gltype.surge='f' AND glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')",get_hypsometry=True)
    outp.fix_terminus()
    outp.remove_upper_extrap()
    outp.normalize_elevation()
    outp.calc_dz_stats()
    outp.extend_upper_extrap()

    results.append(extrapolate3([outp],[""],insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    allwheres.append("gltype.surge='f' AND glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')")
    
    ###Separating Tidewaters
    ##################################################################################
    titles.append("Partitioning\ntidewater")
    types = ["ergi.gltype IN (0,2)","ergi.gltype=1"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    #
    ###Separating Lakes
    ##################################################################################
    titles.append("Partitioning\nlake")
    types = ["ergi.gltype IN (0,1)","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    ##Separating Tidewater and Lakes
    #################################################################################
    titles.append("Partitioning\ntidewater and lake")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"])
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Climate regions with no gltypes
    ################################################################################
    titles.append("Climate zone")
    regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["gltype.surge='f'","ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    #OUTSIDE GLACIERS JUST A 100 KM2
    whereswo.append("ergi.region IS NULL")
    lamb.append(lamb[1])
    
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Arendt regions with no gltypes
    ################################################################################
    titles.append("Regions from (9)")
    regs = ["ergi.region IN ('Aluetian Range','Alaska Range','Brooks Range')","ergi.region IN ('Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Kenai Mountains')","ergi.region IN ('Fairweather Glacier Bay','St. Elias Mountains')","ergi.region IN ('Chugach Range')","ergi.region IN ('Wrangell Mountains')"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["gltype.surge='f'","ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    #OUTSIDE GLACIERS JUST A 100 KM2
    whereswo.append("ergi.region IS NULL")
    lamb.append(lamb[2])
    
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Climate regions and gltypes 
    ################################################################################
    titles.append("Climate zone\nand terminus type")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["gltype.surge='f'","ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    #OUTSIDE GLACIERS JUST A 100 KM2
    whereswo.append("ergi.region IS NULL")
    lamb.append(lamb[1])
    
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Arendt regions and gltypes 
    ################################################################################
    titles.append("Regions from (9)\nand terminus type")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    regs = ["ergi.region IN ('Aluetian Range','Alaska Range','Brooks Range')","ergi.region IN ('Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Kenai Mountains')","ergi.region IN ('Fairweather Glacier Bay','St. Elias Mountains')","ergi.region IN ('Chugach Range')","ergi.region IN ('Wrangell Mountains')"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["gltype.surge='f'","ergi.name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    #NO SURVEYED CHUGACH TIDES REPLACING WITH KENAI TIDES
    whereswo.append(notswo[1])
    lamb.append(lamb[7])
    
    #NO WRANGELL LAKES REPLACING WITH Alaska range lakes
    whereswo.append(notswo[3])
    lamb.append(lamb[9])
    
    #OUTSIDE GLACIERS JUST A 100 KM2
    whereswo.append("ergi.region IS NULL")
    lamb.append(lamb[3])
    
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    ##Separating Tidewater and Lakes min interval 4
    #################################################################################
    titles.append("Partitioning\ntidewater and lake\n min. interval 4 years")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=4)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=4)
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Separating Tidewater and Lakes min interval 8
    #################################################################################
    titles.append("Partitioning\ntidewater and lake\n min. interval 8 years")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=8)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=8)
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    #Separating Tidewater and Lakes min interval 10
    #################################################################################
    titles.append("Separating\ntide and lake\n min. interval 10 years")
    types = ["ergi.gltype=0","ergi.gltype=1","ergi.gltype=2"]
    #regs = ["ergi.region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","ergi.region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","ergi.region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=10)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["gltype.surge='f'","glnames.name NOT IN ('Columbia','YakutatWest','YakutatEast')"],interval_min=10)
    results.append(extrapolate3(lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=True))
    
    pickle.dump([results,outputs,titles,allwheres], open("/Users/igswahwsmcevan/Altimetry/results/all_partitioningoptions.p", "wb" ))
else:
    results,outputs,titles,allwheres = pickle.load(open("/Users/igswahwsmcevan/Altimetry/results/all_partitioningoptions.p", "rb" ))

titles[-1] = re.sub('Separating','Partitioning',titles[-1])
titles[-1] = re.sub('tide','tidewater',titles[-1])
titles[-1] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-1])  
titles[-2] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-2])  
titles[-3] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-3])  

titles[-1] = re.sub('10','\n10',titles[-1])  
titles[-2] = re.sub('8','\n8',titles[-2])  
titles[-3] = re.sub('4','\n4',titles[-3])  

titles.insert(0,titles.pop(3))
results.insert(0,results.pop(3))
outputs.insert(0,outputs.pop(3))
allwheres.insert(0,allwheres.pop(3))

gts = [r['all']['totalgt'] for r in results]
err = [r['all']['errgt'] for r in results]

outputst = outputs[:]
outputst[1]=[outputst[1]]
n=[N.array([len(i.name) for i in lamb]).sum() for lamb in outputst]


x=N.arange(len(err)) 

fig = plt.figure(figsize=[7,5])
ax = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)

plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})
errs1 = ax.errorbar(x[0], gts[0], yerr=[err[0], err[0]],fmt='o',color='k')
errs = ax.errorbar(x[1:], gts[1:], yerr=[err[1:], err[1:]],fmt='o',color='0.7')
ax.plot([0,15],[gts[0],gts[0]],'-',color='0.',zorder=0)

ax.annotate(n[0]+3,[x[0],errs1.get_children()[2].get_ydata()],fontsize=9,ha='center',xytext=[0,2],textcoords='offset points')
for i,j,k in zip(n[8:],x[8:],errs.get_children()[2].get_ydata()[7:]):
    ax.annotate(i+3,[j,k],fontsize=9,ha='center',xytext=[0,2],textcoords='offset points')

ax.set_xlim([-0.5,len(err)-0.5])
ax.set_ylim([-100,-50])
ax.set_xticks([])
ax.set_ylabel("Mass Balance\n(Gt yr"+"$\mathregular{^{-1})}$")
for k in x+0.5:
    print k
    ax.plot([k,k],ax.get_ylim(),'--',color='0.75',zorder=0)
    if k == 7.5:ax.plot([k,k],ax.get_ylim(),'-k',zorder=0)
tax = ax.twinx()
tax.set_ylim(N.abs(N.array(ax.get_ylim())/75*100)-100)
tax.set_ylabel("% difference")
tax.yaxis.set_ticks([-10,0,10])



for i in ax.yaxis.get_ticklabels():i.set_size(11)

totalwidth = 0.6
spacing = 0.005
color = N.array([[240,201,175],[163,100,57],[179,203,252],[45,80,150],[189,237,166],[75,150,38]])/255.
sigcolor = color[[0,2,4]]
#color = ['r','g','g']
center = 0

allcolors=[]
for al in allwheres:
    print al  
    tcolors = set_colors(al,'ergi.gltype=0',list(color[0]),colors=None)
    #print tcolors
    tcolors = set_colors(al,'ergi.gltype=1',color[2],colors=tcolors)
    #print tcolors
    allcolors.append(set_colors(al,'ergi.gltype=2',color[4],colors=tcolors))
    print allcolors[-1]
    


partitionbox(ax2, [outputs[1].mb],[1],[0.5],spacing,['0.5'],showfliers=False,boxwidth=0.2)

outputs.pop(1)
x = N.delete(x,1)
allwheres.pop(1)
allcolors.pop(1)

outputs2 = outputs[:]
ws=[]

for j,it in enumerate(zip(outputs,allwheres,allcolors)):
    w=N.where(N.array([re.search('NULL',i)!=None for i in it[1]]))[0]
    if len(w)>0:
        outputs[j].pop(w)
        allcolors[j].pop(w)
        
    w2 = N.where(N.array([re.search('ergi.gltype=1',i)!=None for i in it[1]]))[0]
    if len(w2)>0:
        outputs2[j]=N.delete(outputs2[j],w2)

for xpos,o,clrs in zip(x,outputs,allcolors):
    partitionbox(ax2, [i.mb for i in o],xpos,totalwidth,spacing,clrs,showfliers=False)
    
    #print [i.mb for i in o]
for o2 in outputs2:
    print '#################################################'
    print scipy.stats.mstats.kruskalwallis(*[i.mb for i in o2])
#partitionbox(ax2, [i.mb for i in outputs[2]],2,totalwidth,spacing,color)    
    
ax2.plot([-0.25,15],[N.median(outputs[0][0].mb),N.median(outputs[0][0].mb)],'k-',color='0.',zorder=0)
ax2.set_xlabel("Partitioning Method")
ax2.set_xticks(N.arange(0,11))
ax2.set_xticklabels(titles,rotation=90,fontsize=11,verticalalignment='top')


ax.annotate("A.",[5,5],xycoords='axes points',fontsize=12,weight='bold')
ax2.annotate("B.",[5,5],xycoords='axes points',fontsize=12,weight='bold')
ax2.set_xlim([-0.5,len(err)-0.5])
x = N.append(x,1)
for k in x+0.5:
    print k
    ax2.plot([k,k],ax2.get_ylim(),'--',color='0.75',zorder=0)
    if k==7.5:ax2.plot([k,k],ax2.get_ylim(),'-k',zorder=0)
ax2.set_ylabel("Mass Balance\n(m w. eq. yr"+"$\mathregular{^{-1})}$")
plt.subplots_adjust(left=0.145,right=0.92,bottom=0.36,top=0.95)
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/playing_with_partitioning2a.jpg",dpi=500)

