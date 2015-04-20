# -*- coding: utf-8 -*-
#import xlrd
#import re
#import unicodedata
import numpy as np
#import datetime as dtm
#import os
#import glob
#import simplekml as kml
#import subprocess
import matplotlib.pyplot as plt
#from osgeo import gdal
#from types import *
#import sys
#import time
## from mpl_toolkits.basemap import Basemap
#from matplotlib.collections import PatchCollection
#from osgeo.gdalnumeric import *
#import matplotlib.path as mpath
#import matplotlib.patches as mpatches
#import matplotlib.mlab as mlab
#import scipy.misc
#import matplotlib
#import matplotlib.colors as colors
#import matplotlib.cm as cmx
#import scipy.stats as stats
import scipy.stats.mstats as mstats
#from numpy.ma import MaskedArray, masked, nomask
#import numpy.ma as ma
import pickle
from Altimetry.Altimetry import *
#from itertools import product

#FUNCTION TO FIGURE OUT WHAT COLOR EACH BOXPLOT SHOULD BE IN FIGURE 12B
def set_colors(allwhere,condition,usethis,colors=None):
    
    if type(colors)==NoneType:colors=N.repeat('0.5',len(allwhere))
    
    a=[]
    for i,boo in enumerate([re.search(condition,i)!=None for i in allwhere]):

        if boo:a.append(usethis)
        else:a.append(colors[i])
    return a

#A FUNCTION TO PLOT EACH GROUP OF BOXPLOTS FOR EACH PARTITIONING CASE
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
    

#################################################################################
#IN ORDER TO GENERATE THIS FIGURE THE ENTIRE PARTITIONING, AND EXTRAPLATION HAS BE BE RERUN FOR EACH OF THESE CASES, 
#THIS DOES NOT GO QUICKLY (ON MY COMPUTER) SO HERE YOU HAVE THE OPTION TO DO THIS ANALYSIS AND SAVE THE RESULTS
#USING PICKLE AND THEN RETREIVE THE RESULTS MORE QUICKLY TO GENERATE THE FIGURE.
#################################################################################
#INPUT VARIABLES
min_interval=5
intervalsmax=30
user = 'evan'
runall=False
if runall:    
    
    #THE SURVEYED GLACIER DATA HERE USED PURELY TO APPLY TO SURVEYED GLACIERS AND NOT TO DETERMINE PARTITIONING OR EXTRAPOLATION
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
    
    #For each case we first run get lamb data with surgers because those are appropriate to show in the boxplots in figure S12.
    #The we rerun GetLambData to get the same sample without surgers that is needed for extrapolation.  In each case we assemble a list of the laser 
    #altimetry mass balance measurement groups that we intend to use for the extrapolation.  We then apply each of these groups to the extrapolation
    #using the partitioning rules specified. 
    #################################################################################
    ##All data excluding Columbia, Yakutat and surge-type glaciers
    #################################################################################
    titles.append("No partition")
    outputs.append(GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, userwhere="name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')",get_hypsometry=True))
    outputs[-1].fix_terminus()
    outputs[-1].remove_upper_extrap()
    outputs[-1].normalize_elevation()
    outputs[-1].calc_dz_stats()
    outputs[-1].extend_upper_extrap()
    outputs[-1].calc_mb()
    
    outp=GetLambData(verbose=False,longest_interval=True,interval_max=intervalsmax,interval_min=min_interval,by_column=True,as_object=True, userwhere="surge='f' AND name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')",get_hypsometry=True)
    outp.fix_terminus()
    outp.remove_upper_extrap()
    outp.normalize_elevation()
    outp.calc_dz_stats()
    outp.extend_upper_extrap()

    results.append(extrapolate(user,[outp],[""],insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    allwheres.append("surge='f' AND name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')")
    
    ###Partitioning Tidewaters
    ##################################################################################
    titles.append("Partitioning\ntidewater")
    types = ["gltype IN (0,2)","gltype=1"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    ###Partitioning Lakes
    ##################################################################################
    titles.append("Partitioning\nlake")
    types = ["gltype IN (0,1)","gltype=2"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    ##Partitioning Tidewater and Lakes
    #################################################################################
    titles.append("Partitioning\ntidewater and lake")
    types = ["gltype=0","gltype=1","gltype=2"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    outputs.append(lamb)  
    allwheres.append(whereswo)
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Climate regions with no gltypes
    ################################################################################
    titles.append("Climate zone")
    regs = ["region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"])   
    
    #REMOVING GLACIERS OUTSIDE THESE REGIONS, VERY FEW - ~100 KM2
    whereswo.append("region IS NULL")
    lamb.append(lamb[1])
    
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Arendt regions with no gltypes
    ################################################################################
    titles.append("Regions from (9)")
    regs = ["region IN ('Aluetian Range','Alaska Range','Brooks Range')","region IN ('Juneau Icefield','Stikine Icefield','Coast Range BC')","region IN ('Kenai Mountains')","region IN ('Fairweather Glacier Bay','St. Elias Mountains')","region IN ('Chugach Range')","region IN ('Wrangell Mountains')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(regs,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    
    #REMOVING GLACIERS OUTSIDE THESE REGIONS, VERY FEW - ~100 KM2
    whereswo.append("region IS NULL")
    lamb.append(lamb[2])
    
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    

    #Climate regions and gltypes 
    ################################################################################
    titles.append("Climate zone\nand terminus type")
    types = ["gltype=0","gltype=1","gltype=2"]
    regs = ["region IN ('Fairweather Glacier Bay','Juneau Icefield','Stikine Icefield','Coast Range BC')","region IN ('Aluetian Range','Chugach Range','St. Elias Mountains','Kenai Mountains')","region IN ('Alaska Range','Wrangell Mountains','Brooks Range')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    
    #REMOVING GLACIERS OUTSIDE THESE REGIONS, VERY FEW - ~100 KM2
    whereswo.append("region IS NULL")
    lamb.append(lamb[1])
    
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Arendt regions and gltypes 
    ################################################################################
    titles.append("Regions from (9)\nand terminus type")
    types = ["gltype=0","gltype=1","gltype=2"]
    regs = ["region IN ('Aluetian Range','Alaska Range','Brooks Range')","region IN ('Juneau Icefield','Stikine Icefield','Coast Range BC')","region IN ('Kenai Mountains')","region IN ('Fairweather Glacier Bay','St. Elias Mountains')","region IN ('Chugach Range')","region IN ('Wrangell Mountains')"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    outputs.append(lamb) 
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,regs,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],too_few=None)   
    
    #NO SURVEYED CHUGACH TIDES REPLACING WITH KENAI TIDES
    whereswo.append(notswo[1])
    lamb.append(lamb[7])
    
    #NO WRANGELL LAKES REPLACING WITH Alaska range lakes
    whereswo.append(notswo[3])
    lamb.append(lamb[9])
    
    #OUTSIDE GLACIERS JUST A 100 KM2
    whereswo.append("region IS NULL")
    lamb.append(lamb[3])
    
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Partitioning Tidewater and Lakes min interval 4
    #################################################################################
    titles.append("Partitioning\ntidewater and lake\n min. interval 4 years")
    types = ["gltype=0","gltype=1","gltype=2"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=4)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=4)
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Partitioning Tidewater and Lakes min interval 8
    #################################################################################
    titles.append("Partitioning\ntidewater and lake\n min. interval 8 years")
    types = ["gltype=0","gltype=1","gltype=2"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=8)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=8)
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    #Partitioning Tidewater and Lakes min interval 10
    #################################################################################
    titles.append("Partitioning\ntidewater and lake\n min. interval 10 years")
    types = ["gltype=0","gltype=1","gltype=2"]
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=10)
    outputs.append(lamb)  
    allwheres.append(whereswo)
    
    lamb,userwheres,notused,whereswo,notswo = partition_dataset(types,applytoall=["surge='f'","name NOT IN ('Columbia Glacier','West Yakutat Glacier','East Yakutat Glacier')"],interval_min=10)
    results.append(extrapolate(user,lamb,whereswo,insert_surveyed_data=surveyeddata,keep_postgres_tbls=False))
    
    pickle.dump([results,outputs,titles,allwheres], open("/Users/igswahwsmcevan/Altimetry/results/all_partitioningoptions.p", "wb" ))
else:
    results,outputs,titles,allwheres = pickle.load(open("/Users/igswahwsmcevan/Altimetry/results/all_partitioningoptions.p", "rb" ))

#DATA PREP FOR FIGURE 
#######################################################################################
#CLEANING UP FORMATTING OF LABELS TO GO ON THE BOTTOM
titles[-1] = re.sub('Separating','Partitioning',titles[-1])
titles[-1] = re.sub('tide','tidewater',titles[-1])
titles[-1] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-1])  
titles[-2] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-2])  
titles[-3] = re.sub('Partitioning\ntidewater and lake\n m','M',titles[-3])  

titles[-1] = re.sub('10','\n10',titles[-1])  
titles[-2] = re.sub('8','\n8',titles[-2])  
titles[-3] = re.sub('4','\n4',titles[-3])  

#THE CHOICE WE USE IN THE PAPER WAS EXCECUTED IN THIS SCRIPT AS OPTION 3, FOR PURPOSES OF PLOTTING, MOVING IT TO THE FRONT OF THE LIST
titles.insert(0,titles.pop(3))
results.insert(0,results.pop(3))
outputs.insert(0,outputs.pop(3))
allwheres.insert(0,allwheres.pop(3))

#GETTING REGIONAL MASS BALANCE ESTIMATES FOR EACH CASE
gts = [r['all']['totalgt'] for r in results]
err = [r['all']['errgt'] for r in results]

#MAKING A LIST OF THE NUMBER OF GLACIERS IN EACH SAMPLE TO BE PUT ALONG THE TOP
outputst = outputs[:]
outputst[1]=[outputst[1]]
n=[N.array([len(i.name) for i in lamb]).sum() for lamb in outputst]

#ESTABLISHING A VARIABLE CONTROLING THE LOCATIONS OF THE POINTS AND BOXPLOTS IN THE FIGURE
x=N.arange(len(err)) 

#######################################################################################
#FIGURE SETTINGS 
fig = plt.figure(figsize=[7,5])
ax = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
fig.subplots_adjust(left=0.145,right=0.92,bottom=0.36,top=0.95)
plt.rc("font", **{"sans-serif": ["Arial"],"size": 12})

#TOP PLOT
#PLOTTING TOTAL MASS BALANCE, MAGNITUDE AND ERROR ESTIMATE
errs1 = ax.errorbar(x[0], gts[0], yerr=[err[0], err[0]],fmt='o',color='k')
errs = ax.errorbar(x[1:], gts[1:], yerr=[err[1:], err[1:]],fmt='o',color='0.7')
ax.plot([0,15],[gts[0],gts[0]],'-',color='0.',zorder=0)

#ANNOTATING THE NUMBER OF SAMPLES ACROSS THE TOP OF THE PLOT
ax.annotate(n[0]+3,[x[0],errs1.get_children()[2].get_ydata()],fontsize=9,ha='center',xytext=[0,2],textcoords='offset points')
for i,j,k in zip(n[8:],x[8:],errs.get_children()[2].get_ydata()[7:]):
    ax.annotate(i+3,[j,k],fontsize=9,ha='center',xytext=[0,2],textcoords='offset points')

#LIMITS, TICKS, LABELS
ax.set_xlim([-0.5,len(err)-0.5])
ax.set_ylim([-100,-50])
ax.set_xticks([])
ax.set_ylabel("Mass Balance\n(Gt yr"+"$\mathregular{^{-1})}$")
for i in ax.yaxis.get_ticklabels():i.set_size(11)

#PLOTTING DIVIDER LINES BETWEEN EACH CASE
for k in x+0.5:
    ax.plot([k,k],ax.get_ylim(),'--',color='0.75',zorder=0)
    if k == 7.5:ax.plot([k,k],ax.get_ylim(),'-k',zorder=0)

#CREATING A TWIN AXIS FOR THE PERCENT CHANGE   
tax = ax.twinx()
tax.set_ylim(N.abs(N.array(ax.get_ylim())/75*100)-100)
tax.set_ylabel("% difference")
tax.yaxis.set_ticks([-10,0,10])


##################################################################
#BOTTOM PLOT WITH BOXPLOTS
#FIGURE PREP
totalwidth = 0.6
spacing = 0.005
color = N.array([[240,201,175],[163,100,57],[179,203,252],[45,80,150],[189,237,166],[75,150,38]])/255.
sigcolor = color[[0,2,4]]
#color = ['r','g','g']
center = 0

#SETTING THE COLOR OF EACH BOX
allcolors=[]
for al in allwheres:
    tcolors = set_colors(al,'gltype=0',list(color[0]),colors=None)
    tcolors = set_colors(al,'gltype=1',color[2],colors=tcolors)
    allcolors.append(set_colors(al,'gltype=2',color[4],colors=tcolors))

#PLOTTING THE BOXPLOT FOR THE CASE OF NO PARITION
partitionbox(ax2, [outputs[1].mb],[1],[0.5],spacing,['0.5'],showfliers=False,boxwidth=0.2)

#NOW REMOVING THAT 'NO PARTITION' CASE FROM THE LIST
outputs.pop(1)
x = N.delete(x,1)
allwheres.pop(1)
allcolors.pop(1)

#LOOPING THROUGH EACH PARTITIONING CASE AND PLOTTING THE BOXPLOTS
outputs2 = outputs[:]
ws=[]
for j,it in enumerate(zip(outputs,allwheres,allcolors)):
    w=N.where(N.array([re.search('NULL',i)!=None for i in it[1]]))[0]
    if len(w)>0:
        outputs[j].pop(w)
        allcolors[j].pop(w)
        
    w2 = N.where(N.array([re.search('gltype=1',i)!=None for i in it[1]]))[0]
    if len(w2)>0:
        outputs2[j]=N.delete(outputs2[j],w2)

for xpos,o,clrs in zip(x,outputs,allcolors):
    partitionbox(ax2, [i.mb for i in o],xpos,totalwidth,spacing,clrs,showfliers=False)
    
#PLOTTING THE MEDIAN LINE OF LAND TERMINATING GLACIERS FROM THE PAPER   
ax2.plot([-0.25,15],[N.median(outputs[0][0].mb),N.median(outputs[0][0].mb)],'k-',color='0.',zorder=0)

#LABELS,TICKS
ax2.set_xlabel("Partitioning Method")
ax2.set_xticks(N.arange(0,11))
ax2.set_xticklabels(titles,rotation=90,fontsize=11,verticalalignment='top')
ax2.set_xlim([-0.5,len(err)-0.5])
ax2.set_ylabel("Mass Balance\n(m w. eq. yr"+"$\mathregular{^{-1})}$")

#ANNOTATING A,B
ax.annotate("A.",[5,5],xycoords='axes points',fontsize=12,weight='bold')
ax2.annotate("B.",[5,5],xycoords='axes points',fontsize=12,weight='bold')

#PLOTTING DIVIDER LINES BETWEEN EACH CASE
x = N.append(x,1)
for k in x+0.5:
    #print k
    ax2.plot([k,k],ax2.get_ylim(),'--',color='0.75',zorder=0)
    if k==7.5:ax2.plot([k,k],ax2.get_ylim(),'-k',zorder=0)
    
#SHOW AND SAVE FIGURE
plt.show()
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/playing_with_partitioning2b.jpg",dpi=500)

