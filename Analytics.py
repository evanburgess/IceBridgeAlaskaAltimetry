# -*- coding: utf-8 -*-
import simplekml as kml
import psycopg2
import re
import numpy as N
import os
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter
import scipy.stats as stats
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.colorbar as clbr
import matplotlib.cm as cmx
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import time
import itertools
from itertools import product as iterproduct
import sys
from types import *

from Interface import *

#import xlrd
#import unicodedata
#import datetime as dtm
#import glob
#import subprocess
#import matplotlib.patches as mpatches
#import scipy.misc
#import matplotlib
#import ConfigParser

#cfg = ConfigParser.ConfigParser()
#cfg.read(os.path.dirname(__file__)+'/setup.cfg')
#sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))
#sys.path.append('/Users/igswahwsmcevan/Altimetry/code')

 

#con,curr = ConnectDb()

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
    
    
    for items in iterproduct(*list(args)):
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

def coords_to_polykml (outputfile, inpt,inner=None, name=None,setcolors=None):

    colors = ['e6d8ad','8A2BE2','A52A2A','DEB887','5F9EA0','7FFF00','D2691E','FF7F50','6495ED','FFF8DC','DC143C','00FFFF','00008B','008B8B','B8860B','A9A9A9','006400','BDB76B','8B008B','556B2F','FF8C00','9932CC','8B0000','E9967A','8FBC8F','483D8B','2F4F4F','00CED1','9400D3','FF1493','00BFFF','696969','1E90FF','B22222','FFFAF0','228B22','FF00FF','DCDCDC','F8F8FF','FFD700','DAA520','808080']        
    print len(colors)
    c = 0
    #START KML FILE
    kmlf = kml.Kml()
    
    if type(inpt) == dict:
        lst = [inpt]
    
    elif type(inpt) == list:

        if type(inpt[0]) ==list:

            lst=[{}]
            lst[0]['outer'] = inpt
            lst[0]['inner'] = inner
        else: lst = inpt
    
    for i,poly in enumerate(lst):
        
        if not 'name' in poly.keys():
            poly['name']='Glacier'

        if type(poly['inner']) == list: 
            test = type(poly['inner'][0])
        else: 
            test = type(poly['inner'])
            
        if test == NoneType:
            pol = kmlf.newpolygon(name=poly['name'],outerboundaryis=poly['outer'])
        else:
            pol = kmlf.newpolygon(name=poly['name'],outerboundaryis=poly['outer'],innerboundaryis=poly['inner'])

        #APPEARANCE FORMATTING
        if setcolors == 'random': 
            #print 'random'
            color = colors[c]
            if c < 41:c += 1
            else:c=0
        else: color = colors[0]
        pol.style.polystyle.color = kml.Color.hexa(color+'55')
        pol.style.polystyle.outline = 0
            
    kmlf.savekmz(outputfile) 
    
def PlotByGlacier(s,x,y,separators,forlegend,xtitle=None,ytitle=None,title = None, colors=['bo','ro','go','yo','mo','ko','co'],label=False,savefile=None,show=False,yrange=[-5,5],alpha=0.5, xlog = False,labelsize=15,ticklabelsize=13,lgdlabelsize=13,showfit=False):

    allx = []
    ally = []
    leglbl = forlegend[:]
    #print 'forlegend', forlegend
    fig1 = plt.figure(facecolor='white',figsize=[10,8])
    ax1 = fig1.add_subplot(111)
    if xtitle != None: ax1.set_xlabel(xtitle,size=labelsize)
    if ytitle != None: ax1.set_ylabel(ytitle,size=labelsize)
    if title != None: ax1.set_title(title)
    ax1.set_ylim(yrange[0],yrange[1])
    if xlog: ax1.set_xscale('log')
    for i in xrange(len(s)):
        if x in s[i]:
            for j,separate in enumerate(separators):
                
                #print '_______________________________'
                #print s[i].keys()
                #print separate.keys(),len(separate.keys()),i,j, s[i][x], s[i][y],j,colors
                if len(separate.keys()) == 1:
                    if s[i][separate.keys()[0]] == separate[separate.keys()[0]]:
                        if showfit:
                            allx.append(s[i][x])
                            ally.append(s[i][y])
                        if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
                        else:
                            ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
                            leglbl[j]='donezo'
                        if label:
                            if type(s[i][x]) == int or type(s[i][x]) == float:
                                lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
                                lbl.set_size(7)
                            if type(s[i][x]) == N.ndarray:
                                lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
                                lbl.set_size(7) 
                if len(separate.keys()) == 2:
                    if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]]:
                        if showfit:
                            allx.append(s[i][x])
                            ally.append(s[i][y])
                        if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
                        else:
                            ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
                            leglbl[j]='donezo'
                        if label:
                            if type(s[i][x]) == int or type(s[i][x]) == float:
                                lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
                                lbl.set_size(7)
                            if type(s[i][x]) == N.ndarray:
                                lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
                                lbl.set_size(7) 
                if len(separate.keys()) == 3:
                    if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]]:
                        if showfit:
                            allx.append(s[i][x])
                            ally.append(s[i][y])
                        if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
                        else:
                            ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
                            leglbl[j]='donezo'
                        if label:
                            if type(s[i][x]) == int or type(s[i][x]) == float:
                                lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
                                lbl.set_size(7)
                            if type(s[i][x]) == N.ndarray:
                                lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
                                lbl.set_size(7) 
                if len(separate.keys()) == 4:
                    if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]] and s[i][separate.keys()[3]] == separate[separate.keys()[2]]:
                        if showfit:
                            allx.append(s[i][x])
                            ally.append(s[i][y])
                        if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
                        else:
                            ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
                            leglbl[j]='donezo'
                        if label:
                            if type(s[i][x]) == int or type(s[i][x]) == float:
                                lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
                                lbl.set_size(7)
                            if type(s[i][x]) == N.ndarray:
                                lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
                                lbl.set_size(7) 

    if showfit:
        fit = N.polyfit(allx,ally,1)
        print fit
        fittxt = "%s = %.6f * %s + %.2f" % (y,fit[0],x,fit[1])
        fit_fn = N.poly1d(fit)
    	ax1.plot(allx,fit_fn(allx),'-k')
        ax1.text(N.max(allx), N.max(fit_fn(allx)),fittxt,horizontalalignment='right')
        
    ax1.legend(prop={'size':lgdlabelsize})
    for tick in ax1.yaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)
    for tick in ax1.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)
    
    if savefile != None:fig1.savefig(savefile,dpi=300)
    if show:plt.show()
    else:
        fig1.clear()
        plt.close(fig1)
        fig1=None  
    #def PlotDzRanges(s,x,y,separators,forlegend,xtitle=None,ytitle=None,title = None, colors=['bo','ro','go','yo','mo','ko','co'],label=False,savefile=None,show=False,yrange=[-5,5],alpha=0.5, xlog = False):
    #
    #leglbl = forlegend[:]
    ##print 'forlegend', forlegend
    #fig1 = plt.figure(facecolor='white',figsize=[10,8])
    #ax1 = fig1.add_subplot(111)
    #if xtitle != None: ax1.set_xlabel(xtitle)
    #if ytitle != None: ax1.set_ylabel(ytitle)
    #if title != None: ax1.set_title(title)
    #ax1.set_ylim(yrange[0],yrange[1])
    #if xlog: ax1.set_xscale('log')
    #
    #
    #                        ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
    #                        leglbl[j]='donezo'
    #                    if label:
    #                        if type(s[i][x]) == int or type(s[i][x]) == float:
    #                            
    #                            lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
    #                            lbl.set_size(7)
    #                        if type(s[i][x]) == N.ndarray:
    #                            lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
    #                            lbl.set_size(7) 
    #            if len(separate.keys()) == 2:
    #                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]]:
    #                    if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
    #                    else:
    #                        ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
    #                        leglbl[j]='donezo'
    #                    if label:
    #                        if type(s[i][x]) == int or type(s[i][x]) == float:
    #                            lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
    #                            lbl.set_size(7)
    #                        if type(s[i][x]) == N.ndarray:
    #                            lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
    #                            lbl.set_size(7) 
    #            if len(separate.keys()) == 3:
    #                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]]:
    #                    if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
    #                    else:
    #                        ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
    #                        leglbl[j]='donezo'
    #                    if label:
    #                        if type(s[i][x]) == int or type(s[i][x]) == float:
    #                            lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
    #                            lbl.set_size(7)
    #                        if type(s[i][x]) == N.ndarray:
    #                            lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
    #                            lbl.set_size(7) 
    #            if len(separate.keys()) == 4:
    #                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]] and s[i][separate.keys()[3]] == separate[separate.keys()[2]]:
    #                    if re.search('donezo',leglbl[j]):ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha)
    #                    else:
    #                        ax1.plot(s[i][x], s[i][y],colors[j],mew = 0,alpha = alpha,label=leglbl[j])
    #                        leglbl[j]='donezo'
    #                    if label:
    #                        if type(s[i][x]) == int or type(s[i][x]) == float:
    #                            lbl = ax1.text(s[i][x], s[i][y],s[i]['name'])
    #                            lbl.set_size(7)
    #                        if type(s[i][x]) == N.ndarray:
    #                            lbl = ax1.text(s[i][x][-1], s[i][y][-1],s[i]['name'])
    #                            lbl.set_size(7) 
    #ax1.legend()
    #
    #if savefile != None:fig1.savefig(savefile,dpi=300)
    #if show:plt.show()
    #else:
    #    fig1.clear()
    #    plt.close(fig1)

def PlotByGlacierLines(s,x,y,separators,forlegend,xtitle,ytitle,colors=['b','r','g','y','k','m'],label=False,savefile=None,show=False,yrange=[-5,5],alpha=0.5,labelsize = 0.9):

    leglbl = forlegend[:]
    #print 'forlegend', forlegend
    fig1 = plt.figure(facecolor='white',figsize=[10,8])
    ax1 = fig1.add_subplot(111)
    ax1.set_xlabel(xtitle)
    ax1.set_ylabel(ytitle)
    #ax1.set_ylim(yrange[0],yrange[1])
    names = list(set([i['name'] for i in s]))
    
    def plotlines(axis,s2,x,y,color,alpha=0.5,labelsize = 9,label=False,forleg = None):
        
        if len(s2[y]) == 1: symbol = color+'.'
        else:symbol = color+'-'
        axis.plot(s2[x], s2[y],symbol,mew = 0,alpha = alpha,label=forleg)
        if label:
            #if type(s[x][0]) == int or type(s[i][0]) == float:
            if i % 2 == 0:
                ytext = min(s2[y])
            else:
                ytext = max(s2[y])
            lbl = axis.text(s2[x][0], ytext,s2['name'][0],clip_on=True)
            lbl.set_size(9)
    print colors
    for i,name in enumerate(names):
        s2 = LambToColumn(extract_records(s, 'name',name))
        #print len(s2['lamb.date1'])
        for j,separate in enumerate(separators):
            if len(separate.keys()) == 1:
                if s[i][separate.keys()[0]] == separate[separate.keys()[0]]: 
                    plotlines(ax1,s2,x,y,colors[j],alpha=alpha,labelsize = labelsize,label=label,forleg = leglbl[j])
                    leglbl[j]=None
            if len(separate.keys()) == 2:
                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]]:
                    plotlines(ax1,s2,x,y,colors[j],alpha=alpha,labelsize = labelsize,label=label,forleg = leglbl[j])
                    leglbl[j]=None
            if len(separate.keys()) == 3:
                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]]:
                    plotlines(ax1,s2,x,y,colors[j],alpha=alpha,labelsize = labelsize,label=label,forleg = leglbl[j])
                    leglbl[j]=None
            if len(separate.keys()) == 4:
                if s[i][separate.keys()[0]] == separate[separate.keys()[0]] and s[i][separate.keys()[1]] == separate[separate.keys()[1]] and s[i][separate.keys()[2]] == separate[separate.keys()[2]] and s[i][separate.keys()[3]] == separate[separate.keys()[2]]:
                    plotlines(ax1,s2,x,y,colors[j],alpha=alpha,labelsize = labelsize,label=label,forleg = leglbl[j])
                    leglbl[j]=None
    
    ax1.legend()
    
    if savefile != None:fig1.savefig(savefile)
    if show:plt.show()
    else:
        fig1.clear()
        plt.close(fig1)

def extract_records(data, field,value,operator = '=='):
    ext = []
    if operator == '==': 
        for i,one in enumerate(data):
            if one[field] == value:ext.append(data[i])
    elif operator == '<=': 
        for i,one in enumerate(data):
            if one[field] <= value:ext.append(data[i])
    elif operator == '>=': 
        for i,one in enumerate(data):
            if one[field] >= value:ext.append(data[i])
    elif operator == '<': 
        for i,one in enumerate(data):
            if one[field] < value:ext.append(data[i])
    elif operator == '>': 
        for i,one in enumerate(data):
            if one[field] > value:ext.append(data[i])
    elif operator == '!=': 
        for i,one in enumerate(data):
            if one[field] != value:ext.append(data[i])
    return ext
    

    
# def mapLamb(s, scale,colorbar = mpl.cm.spectral,
#     resolution = 'i',position = [0.03,0.03,0.90,0.92],outfile = None,
#     dpi = 300,landcolor = '#f0f0f0',backgroundcolor = 'white',title = None,
#     colorbarlabel = None,colorrng = None,show=False):
#     """====================================================================================================
# Altimetry.Analytics.mapLamb
#
# Evan Burgess 2013-10-18
# ====================================================================================================
# Purpose:
#     Lamb Lamb Data
#
#     This ingests output from GetLambData when the following keywords are set: get_geog=True,
#     by_column = True.
#
# Usage:
#     lambobject, scale,colorbar = mpl.cm.spectral,
#     resolution = 'i',position = [0.03,0.03,0.90,0.92],outfile = None,
#     dpi = 300,landcolor = '#f0f0f0',backgroundcolor = 'white',title = None,
#     colorbarlabel = None,colorrng = None,show=True
#
#     lambObject         output from GetLambData when the following keywords are set: get_geog=True,
#                        by_column = True
#
#     scale              The LambObject attribute to be used in coloring glaciers
#
#     colorbar           Colorscale specify a matplotlib color map DEFAULT:mpl.cm.spectral
#
#     resolution         The finess of the coastlines drawn.  Options are from low to high:
#                        c,l,i,h or f DEFAULT: i
#
#     position           The postion of the map in the figure [xmin,ymin,xmax,ymax]
#
#     outfile            Full path to save location
#
#     dpi                Resolution of output image
#
#     landcolor          Color of land as hexadecimal (defualt #e8e8e8) or name of color
#
#     backgroundcolor    Color of background as hexadecimal (defualt #e8e8e8) or name of color
#
#     title              Map Title
#
#     colorlabel         Colorbar scale label
#
#     colorrng           Min and max of colorbar range  [min,max]. Default: min and max of plotting variable.
#
#     show               Toggle Display Figure (Default=True)
# ====================================================================================================
#         """
#
#
#     #CREATING COLOR BARS
#     cm = plt.get_cmap(colorbar)
#     if type(colorrng) == NoneType:colorrng = [scale.min(),scale.max()]
#     cNorm  = colors.Normalize(vmin=colorrng[0], vmax=colorrng[1])
#     scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
#
#
#     #CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
#     fig = plt.figure(figsize=[15,10])
#     ax = fig.add_axes(position)
#     colorbarim = ax.imshow([scale],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=colorrng[0], vmax=colorrng[1])
#     plt.clf()
#
#
#     #NOW CREATING REAL FIGURE
#     ax = fig.add_axes(position)
#     m = Basemap(width=1500000,height=1100000,
#                 resolution=resolution,projection='aea',\
#                 lat_1=55.,lat_2=65.,lon_0=-142,lat_0=60)
#     m.drawcoastlines(linewidth=0.4)
#     m.drawcountries()
#     if landcolor != 'white':m.fillcontinents(color=landcolor,lake_color=None)
#
#     # draw parallels and meridians.
#     m.drawparallels(N.arange(-80.,81.,5.))
#     m.drawmeridians(N.arange(-180.,181.,10.))
#     m.drawmapboundary(fill_color=backgroundcolor)
#
#     #DRAWING LAMB DATA OBJECT
#     patches = []
#
#     for j,poly in enumerate(s.geog):
#         print s.name[j]
#         coords = [[m(s2.x, s2.y) for s2 in ring.points] for ring in poly.polygons[0].rings]
#
#         paths = []
#         for i,ring in enumerate(coords):
#             codes = []
#             codes += [mpath.Path.MOVETO] + (len(ring)-1)*[mpath.Path.LINETO]
#             path = mpath.Path(ring,codes)
#             paths.append(path)
#
#         for i,path in enumerate(paths):
#
#             if i == 0:
#                 color = scalarMap.to_rgba(scale[j])
#                 print i,color
#             else:color = landcolor
#
#             patch = mpatches.PathPatch(path,facecolor=color, edgecolor=None,lw=0)
#             if j == 0: ax.add_patch(patch)
#             ax.add_patch(patch)
#             print ax.patches
#
#
#
#     clr = m.colorbar(colorbarim,"right", size="5%", pad='2%',fig=fig,label=colorbarlabel)
#
#
#     if not title == None:plt.title(title)
#             #patches.append(patch)
#     #patch = mpatches.PathPatch(path,facecolor='red', edgecolor='black')
#     #coll = PatchCollection(patches)
#
#     #ax.add_collection(coll)
#     #m.shadedrelief(scale = 0.5)
#     #m.bluemarble()
#
#
#     if show:plt.show()
#     if not outfile == None:
#         fig.savefig(outfile, dpi=dpi)
#         plt.close()
def PlotIntervals(data,outputfile=None,show=True,annotate=False,colorby=None,colorbar = mpl.cm.RdYlBu,colorrng = None,ticklabelsize=13,categorysize=15):
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
    
    #regions = sorted(list(set(s.region)))
    #names = (list(set(s.name)))
  

    
    
    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')
    
    fig = plt.figure(figsize=[14,15])
    ax = fig.add_axes([0.22,0.04,0.77,0.94])

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
    ax = fig.add_axes([0.22,0.04,0.77,0.94])
    
    y = 0.1
    lastregion = data.region[0]
    lastgl = ''
    lastrgbottom = 0.1
    for i in xrange(len(data.name)): 
        if lastregion != data.region[i]:
            
            ax.annotate(data.region[i-1]+'  ',xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
            
            lastrgbottom = y
            y += 0.6
            
        if colorby == None:
            if lastgl != data.name[i]:
                color = N.random.rand(3,1)
        else:
            color = scalarMap.to_rgba(colorby[i])

            
        pt = ax.plot_date([data.date1[i],data.date2[i]], [y,y], '-',color=color,lw=1.5)
        #print dir(ax.xaxis)
        if annotate: ax.annotate(data.name[i], [data.date1[i],y],fontsize=8)
        y +=0.1
        lastregion = data.region[i]
        lastgl = data.name[i]
    
    ax.set_ylim([0.,y])        
    ax.annotate(data.region[i]+'  ',xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right',size=categorysize)
    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.yaxis.set_ticks([])
    for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)
    ax.autoscale_view()
    #ax2 = fig.add_axes([0.77,0.04,0.1,0.94]) 
    cax, kw = clbr.make_axes(ax)
    #clr = clbr.ColorbarBase(cax,cmap=colorbar)#,"right", size="5%", pad='2%',fig=fig)#)
    clr = clbr.Colorbar(cax,colorbarim) 
    clr.set_label('Balance (m)',size = ticklabelsize)

#    # format the coords message box
#    #def price(x): return '$%1.2f'%x
#    #ax.fmt_xdata = DateFormatter('%Y-%m-%d')
#    #ax.fmt_ydata = price
#    #ax.grid(True)
    
    fig.autofmt_xdate()
    if type(outputfile) == str:
        fig.savefig(outputfile,dpi=500)
        plt.close()
    if show:plt.show()
    
def PlotIntervals2(ax,data,outputfile=None,show=True,annotate=False,colorby=None,colorbar = mpl.cm.RdYlBu,colorrng = None,ticklabelsize=13,categorysize=15):
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
    
    #regions = sorted(list(set(s.region)))
    #names = (list(set(s.name)))
  

    
    
    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')
    
    #fig = plt.figure(figsize=[14,15])
    #ax = fig.add_axes([0.22,0.04,0.77,0.94])
    
    #CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
    #fig = plt.figure(figsize=[15,10])
    ##ax = fig.add_axes(position)
    #colorbarim = ax.imshow([colorby],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=colorrng[0], vmax=colorrng[1])
    #plt.clf()
    #ax = fig.add_axes([0.22,0.04,0.77,0.94])
    print N.c_[data.region,data.name,data.balmodel,data.date1]

    regions,date1,date2,name,colorby2 = zip(*sorted(zip(data.region,data.date1,data.date2,data.name,colorby)))
    print N.c_[regions,name,colorby2,date1]
    #regions = sorted(data.region)

    #if type(colorby) != NoneType:colorby2 = [x for (t,x) in sorted(zip(data.region,colorby))]
    
    #CREATING COLOR BARS
    cm = plt.get_cmap(colorbar) 
    if type(colorrng) == NoneType:colorrng = [colorby.min(),colorby.max()]
    cNorm  = colors.Normalize(vmin=colorrng[0], vmax=colorrng[1])
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm) 
#[x for (y,x) in sorted(zip(a,b))]

    
    y = 0.1
    lastregion = regions[0]
    lastgl = ''
    lastrgbottom = 0.1
    for i in xrange(len(data.name)): 
        if lastregion != regions[i]:
            
            ax.annotate(regions[i-1]+'  ',xy=[min(date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
            
            lastrgbottom = y
            y += 0.6
            
        if colorby == None:
            if lastgl != name[i]:
                color = N.random.rand(3,1)
        else:
            color = scalarMap.to_rgba(colorby2[i])

            
        pt = ax.plot_date([date1[i],date2[i]], [y,y], '-',color=color,lw=1.5)
        #print dir(ax.xaxis)
        if annotate: ax.annotate(name[i], [date1[i],y],fontsize=8)
        y +=0.1
        lastregion = regions[i]
        lastgl = name[i]
    
    ax.set_ylim([0.,y])        
    ax.annotate(regions[i]+'  ',xy=[min(date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right',fontsize=8)
    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.yaxis.set_ticks([])
    #for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)
    #ax.autoscale_view()
    ##ax2 = fig.add_axes([0.77,0.04,0.1,0.94]) 
    #cax, kw = clbr.make_axes(ax)
    ##clr = clbr.ColorbarBase(cax,cmap=colorbar)#,"right", size="5%", pad='2%',fig=fig)#)
    #clr = clbr.Colorbar(cax,colorbarim) 
    #clr.set_label('Balance (m)',size = ticklabelsize)

#    # format the coords message box
#    #def price(x): return '$%1.2f'%x
#    #ax.fmt_xdata = DateFormatter('%Y-%m-%d')
#    #ax.fmt_ydata = price
#    #ax.grid(True)
    #
    #fig.autofmt_xdate()
    #if type(outputfile) == str:
    #    fig.savefig(outputfile,dpi=500)
    #    plt.close()
    #if show:plt.show()
    
def PlotIntervalsByType(data,outputfile=None,show=True,annotate=False,colorby=None,colorbar = mpl.cm.RdYlBu,colorrng = None,ticklabelsize=13):
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
    
    #regions = sorted(list(set(s.region)))
    #names = (list(set(s.name)))
  

    
    
    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')
    
    fig = plt.figure(figsize=[14,15])
    ax = fig.add_axes([0.22,0.04,0.77,0.94])

    #CREATING COLOR BARS
    cm = plt.get_cmap(colorbar) 
    if type(colorrng) == NoneType:colorrng = [colorby.min(),colorby.max()]
    cNorm  = colors.Normalize(vmin=colorrng[0], vmax=colorrng[1])
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    
    #CREATING TEMPORARY PLOT TO RETRIEVE COLORBAR
    #fig = plt.figure(figsize=[15,10])
    #ax = fig.add_axes(position)
    colorbarim = ax.imshow([colorby2],extent=[0,0.1,0,0.1],cmap=colorbar,vmin=colorrng[0], vmax=colorrng[1])
    plt.clf()
    ax = fig.add_axes([0.22,0.04,0.77,0.94])
    
    y = 0.1
    lastregion = data.glaciertype[0]
    lastgl = ''
    lastrgbottom = 0.1
    for i in xrange(len(data.name)): 
        if lastregion != data.glaciertype[i]:
            
            ax.annotate(data.glaciertype[i-1]+'  ',xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
            
            lastrgbottom = y
            y += 0.6
            
        if colorby == None:
            if lastgl != data.name[i]:
                color = N.random.rand(3,1)
        else:
            color = scalarMap.to_rgba(colorby2[i])

            
        pt = ax.plot_date([data.date1[i],data.date2[i]], [y,y], '-',color=color,lw=2)
        #print dir(ax.xaxis)
        if annotate: ax.annotate(data.name[i], [data.date1[i],y],fontsize=6)
        y +=0.1
        lastregion = data.glaciertype[i]
        lastgl = data.name[i]
    
    ax.set_ylim([0.,y])        
    ax.annotate(data.glaciertype[i]+'   ',xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.yaxis.set_ticks([])
    for tick in ax.xaxis.get_major_ticks():tick.label.set_fontsize(ticklabelsize)

    ax.autoscale_view()
    #ax2 = fig.add_axes([0.77,0.04,0.1,0.94]) 
    cax, kw = clbr.make_axes(ax)
    #clr = clbr.ColorbarBase(cax,cmap=colorbar)#,"right", size="5%", pad='2%',fig=fig)#)
    clr = clbr.Colorbar(cax,colorbarim) 
   
#    # format the coords message box
#    #def price(x): return '$%1.2f'%x
#    #ax.fmt_xdata = DateFormatter('%Y-%m-%d')
#    #ax.fmt_ydata = price
#    #ax.grid(True)
    
    fig.autofmt_xdate()
    if type(outputfile) == str:
        fig.savefig(outputfile,dpi=400)
        plt.close()
    if show:plt.show()
    
#def PlotIntervals(data,outputfile=None,show=True,annotate=False):
#    """====================================================================================================
#Altimetry.Analytics.PlotIntervals
#
#Evan Burgess 2013-10-18
#====================================================================================================
#Purpose:
#    Plotting intervals retreived from Lamboutput data.
#    
#Usage:PlotIntervals(data,outputfile=None,show=True)
#
#    data        Output from GetLambData.  Keywords bycolumn = True and ,orderby = 'glnames.region,glnames.name,lamb.date1,lamb.date2'
#        
#    outputfile  Full path
#    
#    show        Set to False to not display figure
#====================================================================================================        
#        """
#    
#    #regions = sorted(list(set(s.region)))
#    #names = (list(set(s.name)))
#    
#
#    
#    
#    years    = YearLocator()   # every year
#    months   = MonthLocator()  # every month
#    yearsFmt = DateFormatter('%Y')
#    
#    fig = plt.figure(figsize=[9,15])
#    ax = fig.add_axes([0.22,0.04,0.77,0.94])
#    
#    y = 0.1
#    lastregion = data.region[0]
#    lastgl = ''
#    lastrgbottom = 0.1
#    for i in xrange(len(data.name)): 
#        if lastregion != data.region[i]:
#            
#            ax.annotate(data.region[i-1],xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
#            
#            lastrgbottom = y
#            y += 0.6
#            
#        if lastgl != data.name[i]:
#            color = N.random.rand(3,1)
#        ax.plot_date([data.date1[i],data.date2[i]], [y,y], '-',color=color)
#        if annotate: ax.annotate(data.name[i], [data.date1[i],y],fontsize=6)
#        y +=0.1
#        lastregion = data.region[i]
#        lastgl = data.name[i]
#        
#    ax.annotate(data.region[i],xy=[min(data.date1),(lastrgbottom+y)/2.],annotation_clip=False,ha='right')
#    # format the ticks
#    ax.xaxis.set_major_locator(years)
#    ax.xaxis.set_major_formatter(yearsFmt)
#    ax.xaxis.set_minor_locator(months)
#    ax.yaxis.set_ticks([])
#    ax.autoscale_view()
#    
#    # format the coords message box
#    #def price(x): return '$%1.2f'%x
#    #ax.fmt_xdata = DateFormatter('%Y-%m-%d')
#    #ax.fmt_ydata = price
#    #ax.grid(True)
#    
#    fig.autofmt_xdate()
#    if type(outputfile) == str:
#        fig.savefig(outputfile)
#        plt.close()
#    if show:plt.show()
    
def mad (inpu,axis=None,normalized=False):
    data = N.ma.masked_array(inpu,N.isnan(inpu))

    if axis == None:
        out = N.ma.median(N.ma.abs(data-N.ma.median(data)))
        if normalized: return 1.4826*out
        else: return out
    else:
        out = []
        print data.shape
        med = N.ma.median(data,axis=axis)

        if axis==1:
            out = N.ma.median(N.ma.abs(data-med[:,None]),axis=1)
        elif axis==0:
            out = N.ma.median(N.ma.abs(data-med[None,:]),axis=0)

        if normalized: return 1.4826*out
        else: return out

def PlotDzRange(s,axes,gaussian = 60,color = 'b',label=None,alphafill=0.2,plotindiviudallines=False,robust=False,normalize_elev=False,dontplot=False):
    step = 10
    mn = N.min([N.min(x['e']) for x in s])
    mx = N.max([N.max(x['e']) for x in s])
    if  normalize_elev:
	newx = N.arange(0,1,0.01,dtype=N.float32)
	print 'newx', newx
    else:
        newx = N.arange(mn,mx+step,step,dtype=N.float32)
        
        
        
    newys = []

    for obj in s:
      
        if gaussian != None:
            interval = obj['e'][1]-obj['e'][0]
            sigma_intervals = gaussian / interval
            
            y = gaussian_filter(obj['dz'],sigma_intervals)
        else: y = obj['dz']
        
        if  normalize_elev:
            e = obj['e'].astype(N.float32)
            x = (e-N.min(e))/(N.max(e)-N.min(e))
        else:
            x = obj['e']
        #print 'x',x
        
        newys.append(N.interp(newx,x,y,N.nan,N.nan))

    newys2 = N.c_[newys]

    print type(newys2)
    print newys2.size
    
    if label != None: label = "%s N=%s" % (label,len(s))
    newys3 = N.ma.masked_array(newys2,N.isnan(newys2))

    if robust == False:
        std = N.ma.std(newys3,axis=0)
        mean = N.ma.mean(newys3,axis=0)
    elif robust == True:
        print 'robust'
        std = mad(newys3,axis=1,normalized=True)
        mean = N.ma.median(newys3,axis=0)
    elif robust == 'both':
        std = N.ma.std(newys3,axis=0)
        mean = N.ma.mean(newys3,axis=0)
        madn = mad(newys3,axis=1,normalized=True)
        median = N.ma.median(newys3,axis=0)
    #print '*********************'
    #print newx
    #if  normalize_elev:
        #newx = (newx-N.min(newx))/(N.max(newx)-N.min(newx))

    #print newx
    if not dontplot:    
        if robust != 'both':
            axes.plot(newx,mean,color+'-',linewidth=2,label=label)
            axes.fill_between(newx,mean+std,mean-std,alpha=alphafill,color= color,lw=0)
            
        else:
            axes.plot(newx,mean,color+'-',linewidth=2,label=label)
            axes.fill_between(newx,mean+std,mean-std,alpha=alphafill,color= color,lw=0)
            axes.plot(newx,median,color+'--',linewidth=2,label='Median')
            axes.plot(newx,mean+madn,color+'-',linewidth=0.5,label='MADn')
            axes.plot(newx,mean-madn,color+'-',linewidth=0.5)
    #axes.fill_between(newx,,mean-std,alpha=alphafill,color= color,lw=0)
        
        if plotindiviudallines:
    
            for ys in newys:axes.plot(newx,ys,color+'-',alpha=0.4,linewidth=0.5)
    
    if robust == False:return newx,newys3,mean,std
    elif robust == True:return newx,newys3,median,madn
    elif robust == 'both':return newx,newys3,mean,std,median,madn
            
def fix_terminus(lambobj,slope=-0.05,error=1):

    if type(lambobj) == dict:
        cumulative = N.cumsum(lambobj['numdata'])
        
        for i,val in enumerate(cumulative):
            if val != 0:break
    
        lambobj['dz'] = N.where(cumulative == 0, N.nan,lambobj['dz'])
        lambobj['dz25'] = N.where(cumulative == 0, N.nan,lambobj['dz25'])
        lambobj['dz75'] = N.where(cumulative == 0, N.nan,lambobj['dz75'])
        
        deriv = N.ediff1d(lambobj['dz'])#ediff1d
        #print lambobj.dz
        #print deriv
        
        for i,bn in enumerate(deriv):
            if not N.isnan(bn):
                if bn < slope: 
                    lambobj['dz'][i]=N.nan
                else:break
        nanreplace = N.isnan(lambobj['dz'])
        lambobj['dz'] = N.where(nanreplace, lambobj['dz'][i],lambobj['dz'])
        lambobj['dz25'] = N.where(nanreplace, lambobj['dz25'][i]-error,lambobj['dz25'])
        lambobj['dz75'] = N.where(nanreplace, lambobj['dz75'][i]+error,lambobj['dz75'])
        return deriv
    else:
        cumulative = N.cumsum(lambobj.numdata)
        
        for i,val in enumerate(cumulative):
            if val != 0:break
    
        lambobj.dz = N.where(cumulative == 0, N.nan,lambobj.dz)
        lambobj.dz25 = N.where(cumulative == 0, N.nan,lambobj.dz25)
        lambobj.dz75 = N.where(cumulative == 0, N.nan,lambobj.dz75)
        
        deriv = N.ediff1d(lambobj.dz)#ediff1d
        #print lambobj.dz
        #print deriv
        
        for i,bn in enumerate(deriv):
            if not N.isnan(bn):
                if bn < slope: 
                    lambobj.dz[i]=N.nan
                else:break
        nanreplace = N.isnan(lambobj.dz)
        lambobj.dz = N.where(nanreplace, lambobj.dz[i],lambobj.dz)
        lambobj.dz25 = N.where(nanreplace, lambobj.dz25[i]-error,lambobj.dz25)
        lambobj.dz75 = N.where(nanreplace, lambobj.dz75[i ]+error,lambobj.dz75)
        return deriv
        
#def extrapolate(groups,insert_surveyed_data=None, extrap_tbl='extrapolation_curves',keep_postgres_tbls=False, resulttable='resultsauto',export_shp=None,export_csv=None):
#
#    
#    for grp in groups:
#        if not hasattr(grp,'interquartile_rng'):raise "Run statistics on groups first"
#    
#    #print 'connecting'    
#    conn,cur = ConnectDb()
#    cur.execute("DROP TABLE IF EXISTS extrapolation_curves;")
#    conn.commit()
#
#    #print 'creating'
#    cur.execute("CREATE TABLE extrapolation_curves (gid serial PRIMARY KEY,matchcol real,normelev real,gltype int,mean double precision,median real,std real,sem real, iqr real,stdlow real, stdhigh real, q1 real,q3 real,perc5 real,perc95 real);")
#    conn.commit()
#
#    for grp in groups:
#    
#        #l=0.11
#        #w=0.8
#        #
#        #fig = plt.figure(figsize=[6,10])
#        #ax = fig.add_axes([l,0.56,w,0.4])
#        #ax.set_ylabel('Balance (m w.e./yr)')
#        #ax.set_ylim([-10,3])
#        #ax.set_xlim([0,1])
#        #ax.set_title('Dz for %s Glaciers  Gltype code %s' % (outroot[j],gltype[j]))
#        #color = 'r'
#        #ax.plot(grp.norme,grp.dzs_mean,'-%s' % color,linewidth=2)
#        #ax.plot(grp.norme,grp.dzs_median,'--%s' % color,linewidth=2)
#        #ax.plot(grp.norme,grp.dzs_median-grp.dzs_madn,'-%s' % color,linewidth=0.7)
#        #ax.plot(grp.norme,grp.dzs_median+grp.dzs_madn,'-%s' % color,linewidth=0.7)
#        #ax.fill_between(grp.norme,grp.dzs_mean+grp.dzs_std,grp.dzs_mean-grp.dzs_std,alpha=0.2,color=color,lw=0)
#        ##for profile in grp.normdz: 
#        #ax.plot(grp.norme,grp.normdz[3],'-r',alpha=0.2)
#        #plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=True, shadow=True)
#        #plt.show()
#        
#        
#        stdlow = grp.dzs_mean-grp.dzs_std
#        stdhigh = grp.dzs_mean+grp.dzs_std
#        
#        for i in xrange(len(grp.norme)):
#            #print "INSERT INTO extrapolation_curves (normelev,gltype,mean,median,std,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (grp.norme[i],gltype[j],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i])
#            cur.execute("INSERT INTO %s (normelev,gltype,mean,median,std,sem,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,grp.norme[i],gltype[j],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
#            if abs(grp.norme[i]-0.99)<0.0001:cur.execute("INSERT INTO %s (normelev,gltype,mean,median,std,sem,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,1.,gltype[j],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
#            conn.commit()
#    
#    #print "Producing Results Table!"
#    cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#    cur.execute("SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,ext.sem,ext.iqr,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,eb.area*ext.mean as volchange,eb.normbins < -100 as surveyed, eb.geom into %s from ergibins2 as eb inner join ergi on eb.glimsid=ergi.glimsid left join %s as ext on (ergi.gltype*10+eb.normbins)::numeric=round((ext.gltype*10+ext.normelev)::numeric,2);" % (resulttable, extrap_tbl))
#    conn.commit()
#    cur.execute("CREATE INDEX glimid_index ON %s (glimsid);" % resulttable)
#    cur.execute("CREATE INDEX normbins_index ON %s (normbins);" % resulttable)
#    conn.commit()
#    #cur.execute("VACUUM ANALYZE;")
#    
#    #INSERTING SURVEYED GLACIER DATA
#    if type(insert_surveyed_data) == instance:
#    #s2 = GetLambData(verbose=False,longest_interval=True,interval_min=min_interval,by_column=True,as_object=True)
#    #s2.fix_terminus()
#    #s2.normalize_elevation()
#    #s2.calc_dz_stats()
#    
#    #LOOPING THROUGH EACH GLIMS ID
#        for i in xrange(len(insert_surveyed_data.normdz)):
#            
#            data = GetSqlData2("SELECT normbins::real FROM %s WHERE glimsid = '%s'" % (resulttable,insert_surveyed_data.glimsid[i]))['normbins']
#            uninormbins = N.unique(data)
#            indices = (uninormbins*100).astype(int)
#            indices = N.where(indices == 100,99,indices)
#            
#            surveyed = [s2.normdz[i][indc] for indc in indices]
#            
#            for j in xrange(len(surveyed)):
#        
#                #if verbose: print "UPDATE %s SET mean = %s,surveyed='t' WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],s2.glimsid[i],uninormbins[j])
#                cur.execute("UPDATE %s SET mean = %s,surveyed='t' WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],s2.glimsid[i],uninormbins[j]))
#            
#            conn.commit()
#        
#    if type(export_shp) != Nonetype:
#        os.system("/Applications/Postgres.app/Contents/MacOS/bin/pgsql2shp -f %s -h localhost altimetry %s" % (resultshp,resulttable))
#    
#    if type(export_csv) != Nonetype:
#        cur.execute("COPY (SELECT surveyed, SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY surveyed) TO '%s/final_results_divd_surveyed.csv' DELIMITER ',' CSV HEADER;" % (resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY gltype,surveyed) TO '%s/final_results_divd_surveyed_gltype.csv' DELIMITER ',' CSV HEADER;" % (resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT gltype, SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY gltype) TO '%s/final_results_divd_gltype.csv' DELIMITER ',' CSV HEADER;" % (resulttable,os.path.dirname(export_csvpe)))
#        cur.execute("COPY (SELECT SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM  %s) TO '%s/final_results_one_group.csv' DELIMITER ',' CSV HEADER;" % (resulttable,os.path.dirname(export_csv)))
#
#        
#        files = ['final_results_one_group.csv','final_results_divd_gltype.csv','final_results_divd_surveyed_gltype.csv','final_results_divd_surveyed.csv'] 
#        out = open(export_csv,'w')
#        
#        
#        for ope in files:
#            f = open("%s/%s" % (os.path.dirname(export_csv),ope),'r')
#            for i in f:
#                i=re.sub('^0,','Land,',i)
#                i=re.sub('^1,','Tidewater,',i)
#                i=re.sub('^2,','Lake,',i)
#                out.write(i)
#            os.remove("%s/%s" % (os.path.dirname(export_csv,ope)))
#            out.write('\n\n')
#        out.close() 
#        
#        
#        
#        if not keep_postgres_tbls:
#            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
#            conn.commit()
#        cur.close()
#        conn.close()
#
#    else:
#        out = {}
#        out['bysurveyed'] = GetSqlData2("SELECT surveyed, SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY surveyed;" % resulttable)
#        out['bytype_survey'] = GetSqlData2("SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY gltype,surveyed;" % resulttable)
#        out['bytype'] = GetSqlData2("SELECT gltype, SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s GROUP BY gltype;" % resulttable)
#        out['all'] = GetSqlData2("SELECT SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*0.9 as totalGt, SUM(mean*area)/SUM(area)*0.9 as totalkgm2, SUM(std*area)/1000000000.*0.9 as stdGt, SUM(sem*area)/1000000000.*0.9 as semGt, SUM(iqr*area)/1000000000.*0.9 as iqrGt FROM %s;" % resulttable)
#        if not keep_postgres_tbls:
#            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
#            conn.commit()
#        cur.close()
#        conn.close()
#        return out

#def extrapolate2(groups,insert_surveyed_data=None, extrap_tbl='extrapolation_curves',keep_postgres_tbls=False, resulttable='resultsauto',export_shp=None,export_csv=None,density=0.850, density_err= 0.06,acrossgl_err=0.0):
#    
#    cfg = ConfigParser.ConfigParser()
#    cfg.read(os.path.dirname(__file__)+'/setup.cfg')
#    sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))
#
#    for grp in groups:
#        if not hasattr(grp,'interquartile_rng'):raise "Run statistics on groups first"
#    
#    #print 'connecting'    
#    conn,cur = ConnectDb()
#    cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
#    conn.commit()
#
#    #print 'creating'
#    cur.execute("CREATE TABLE %s (gid serial PRIMARY KEY,curveid numeric,normelev real,gltype int,mean double precision,median real,std real,sem real,quadsum real, iqr real,stdlow real, stdhigh real, q1 real,q3 real,perc5 real,perc95 real);" % extrap_tbl)
#    conn.commit()
#
#    for grp in groups:
#    
#        #l=0.11
#        #w=0.8
#        #
#        #fig = plt.figure(figsize=[6,10])
#        #ax = fig.add_axes([l,0.56,w,0.4])
#        #ax.set_ylabel('Balance (m w.e./yr)')
#        #ax.set_ylim([-10,3])
#        #ax.set_xlim([0,1])
#        #ax.set_title('Dz for %s Glaciers  Gltype code %s' % (outroot[j],gltype[j]))
#        #color = 'r'
#        #ax.plot(grp.norme,grp.dzs_mean,'-%s' % color,linewidth=2)
#        #ax.plot(grp.norme,grp.dzs_median,'--%s' % color,linewidth=2)
#        #ax.plot(grp.norme,grp.dzs_median-grp.dzs_madn,'-%s' % color,linewidth=0.7)
#        #ax.plot(grp.norme,grp.dzs_median+grp.dzs_madn,'-%s' % color,linewidth=0.7)
#        #ax.fill_between(grp.norme,grp.dzs_mean+grp.dzs_std,grp.dzs_mean-grp.dzs_std,alpha=0.2,color=color,lw=0)
#        ##for profile in grp.normdz: 
#        #ax.plot(grp.norme,grp.normdz[3],'-r',alpha=0.2)
#        #plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=True, shadow=True)
#        #plt.show()
#
#        gltype = grp.gltype
#
#        if not all([x == gltype[0] for x in gltype]): 
#            raise "All in group are not same glacier type."
#        else:
#            gltype = gltype[0]
#        
#        stdlow = grp.dzs_mean-grp.dzs_std
#        stdhigh = grp.dzs_mean+grp.dzs_std
#
#
#        for i in xrange(len(grp.norme)):
#            #print "INSERT INTO extrapolation_curves (normelev,gltype,mean,median,std,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (grp.norme[i],gltype[j],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i])
#            cur.execute("INSERT INTO %s (curveid,normelev,gltype,mean,median,std,sem,quadsum,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,gltype*10+grp.norme[i],grp.norme[i],gltype,grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.quadsum[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
#            if abs(grp.norme[i]-0.99)<0.0001:cur.execute("INSERT INTO %s (curveid,normelev,gltype,mean,median,std,sem,quadsum,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,gltype*10+grp.norme[i],1.,gltype,grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.quadsum[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
#            conn.commit()
#    cur.execute("DROP INDEX IF EXISTS curveid_index;")
#    cur.execute("CREATE INDEX curveid_index ON %s (curveid);" % extrap_tbl)
#    
#    
#    glimsidlist =[item for sublist in [grp.glimsid for grp in groups] for item in sublist]
#    #print [item for sublist in [grp.name for grp in groups] for item in sublist]
#    
##    bigselect = """
##SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
##ext.sem,ext.quadsum,ext.iqr,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,
##eb.area*ext.mean as volchange,0 as surveyed, ext.sem as error, eb.geom into %s 
##from ergibins2 as eb inner join ergi on eb.glimsid=ergi.glimsid
##left join %s as ext on (ergi.gltype*10+eb.normbins)::numeric=round((ext.gltype*10+ext.normelev)::numeric,2)
##WHERE ergi.glimsid NOT IN ('%s')
##UNION
##SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
##ext.sem,ext.quadsum,ext.iqr,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,
##eb.area*ext.mean as volchange,1 as surveyed, ext.quadsum as error, eb.geom 
##from ergibins2 as eb inner join ergi on eb.glimsid=ergi.glimsid
##left join %s as ext on (ergi.gltype*10+eb.normbins)::numeric=round((ext.gltype*10+ext.normelev)::numeric,2)
##WHERE ergi.glimsid IN ('%s');"""  % (resulttable, extrap_tbl,"','".join(glimsidlist), extrap_tbl,"','".join(glimsidlist))
#
#    bigselect = """
#SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
#ext.sem::double precision,ext.quadsum::double precision,ext.iqr::double precision,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,eb.curveid as ebcurve,ext.curveid,
#eb.area*ext.mean::double precision as volchange,false as surveyed, ext.sem::double precision as error, eb.albersgeom into %s 
#from ergibins3 as eb inner join ergi on eb.glimsid=ergi.glimsid
#left join %s as ext on eb.curveid=ext.curveid
#WHERE ergi.glimsid NOT IN ('%s')
#UNION
#SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
#ext.sem::double precision,ext.quadsum::double precision,ext.iqr::double precision,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,eb.curveid as ebcurve,ext.curveid,
#eb.area*ext.mean::double precision as volchange,true as surveyed, ext.quadsum::double precision as error, eb.albersgeom 
#from ergibins3 as eb inner join ergi on eb.glimsid=ergi.glimsid
#left join %s as ext on eb.curveid=ext.curveid
#WHERE ergi.glimsid IN ('%s');"""  % (resulttable, extrap_tbl,"','".join(glimsidlist), extrap_tbl,"','".join(glimsidlist))
#
#    #print bigselect
#    
#    start_time = time.time()
#
#
#    print "Producing Results Table!"
#    sys.stdout.flush()
#    cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#    cur.execute(bigselect)
#    conn.commit()
#    cur.execute("CREATE INDEX glimid_index ON %s (glimsid);" % resulttable)
#    cur.execute("CREATE INDEX normbins_index ON %s (normbins);" % resulttable)
#    
#    #MULTIPLYING THE ERROR FOR TIDEWATERS BY 2 TO ACCOUNT FOR THE POOR DISTRIBUTION (THIS IS DISCUSSED IN THE PAPER)
#    cur.execute("UPDATE %s SET error = error*1.5 WHERE gltype='1' AND surveyed='f';" % resulttable)
#    
#    
#    cur.execute("ALTER TABLE resultsauto add column singl_std real DEFAULT NULL;")   # this is to put the stdev of the xpts for surveyed glaciers rather than the std dev of the group
#    conn.commit()
#    print "Joining ergibins3 took",time.time() - start_time,'seconds'
#    sys.stdout.flush()
#    #cur.execute("VACUUM ANALYZE;")
#     
#    #INSERTING SURVEYED GLACIER DATA
#    if type(insert_surveyed_data) != NoneType:
#    #s2 = GetLambData(verbose=False,longest_interval=True,interval_min=min_interval,by_column=True,as_object=True)
#    #s2.fix_terminus()
#    #s2.normalize_elevation()
#    #s2.calc_dz_stats()
#        print "Insert surveyed Data"
#        sys.stdout.flush()
#        start_time = time.time()
#    #LOOPING THROUGH EACH GLIMS ID
#        for i in xrange(len(insert_surveyed_data.normdz)):
#            #print insert_surveyed_data.name[i]
#            data = GetSqlData2("SELECT normbins::real FROM %s WHERE glimsid = '%s'" % (resulttable,insert_surveyed_data.glimsid[i]))['normbins']
#            #if insert_surveyed_data.glimsid[i]=='G212334E61307N':print data
#            uninormbins = N.unique(data)
#            indices = (uninormbins*100).astype(int)
#            indices = N.where(indices > 99,99,indices)
#            indices = N.where(indices < 0,0,indices)
#            
#            #print i,indices
#            #sys.stdout.flush()
#            #insert_surveyed_data.normdz[i]
#            #not every glacier will have a bin for every normalized elevation band from 0.01 to 0.99 so we are selecting the survey data for only those bands that the 
#            #binned rgi has
#            surveyed = [insert_surveyed_data.normdz[i][indc] for indc in indices]
#            print surveyed
#            print len(surveyed)
#            normstd = [insert_surveyed_data.survIQRs[i][indc]*0.7413 for indc in indices]
#            #normstd = [insert_surveyed_data.survIQRs[i][indc] for indc in indices]
#            
#            for j in xrange(len(surveyed)):
#                
#                #if insert_surveyed_data.glimsid[i]=='G212334E61307N':print       "UPDATE %s SET mean = %s,surveyed='t' WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],insert_surveyed_data.glimsid[i],uninormbins[j])
#                cur.execute("UPDATE %s SET mean = %s,surveyed='t',singl_std=%s WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],normstd[j],insert_surveyed_data.glimsid[i],uninormbins[j]))
#            
#            conn.commit()
#        print "Insert surveyed Data took",time.time() - start_time,'seconds'
#        sys.stdout.flush()
#        print "here * %s *" % export_shp
#    if type(export_shp) != NoneType:
#        start_time = time.time()
#        print "Exporting To Shpfile"
#        sys.stdout.flush()
#        os.system("%s -f %s -h localhost altimetry %s" % (cfg.get('Section One', 'pgsql2shppath'),export_shp,resulttable))
#        print "Exporting To Shpfile took",time.time() - start_time,'seconds'
#    if type(export_csv) != NoneType:
#        print "Exporting to CSV"
#        sys.stdout.flush()                                                                                                                                    
#        #THESE ONES ARE OLD AND INCORRECT SAVING JUST IN CASE
#        #cur.execute("COPY (SELECT surveyed, SUM(area)/1000000. as area,        SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY surveyed ORDER BY surveyed) TO '%s/final_results_divd_surveyed.csv' DELIMITER ',' CSV HEADER;" %               (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        #cur.execute("COPY (SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype,surveyed ORDER BY gltype,surveyed) TO '%s/final_results_divd_surveyed_gltype.csv' DELIMITER ',' CSV HEADER;" % (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        #cur.execute("COPY (SELECT gltype, SUM(area)/1000000. as area,          SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype ORDER BY gltype) TO '%s/final_results_divd_gltype.csv' DELIMITER ',' CSV HEADER;" %                   (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csvpe)))
#        #cur.execute("COPY (SELECT SUM(area)/1000000. as area,                  SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s) TO '%s/final_results_one_group.csv' DELIMITER ',' CSV HEADER;" %                                     (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT surveyed,         SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY surveyed ORDER BY surveyed) TO '%s/final_results_divd_surveyed.csv' DELIMITER ',' CSV HEADER;" %                      (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT gltype, surveyed, SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype,surveyed ORDER BY gltype,surveyed) TO '%s/final_results_divd_surveyed_gltype.csv' DELIMITER ',' CSV HEADER;" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT gltype,           SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype ORDER BY gltype) TO '%s/final_results_divd_gltype.csv' DELIMITER ',' CSV HEADER;" %                            (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        cur.execute("COPY (SELECT                   SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s) TO '%s/final_results_one_group.csv' DELIMITER ',' CSV HEADER;" %                                                              (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
#        
#        files = ['final_results_one_group.csv','final_results_divd_gltype.csv','final_results_divd_surveyed_gltype.csv','final_results_divd_surveyed.csv'] 
#        out = open(export_csv,'w')
#        
#        
#        for ope in files:
#            f = open("%s/%s" % (os.path.dirname(export_csv),ope),'r')
#            for i in f:
#                i=re.sub('^0,','Land,',i)
#                i=re.sub('^1,','Tidewater,',i)
#                i=re.sub('^2,','Lake,',i)
#                out.write(i)
#            os.remove("%s/%s" % (os.path.dirname(export_csv,ope)))
#            out.write('\n\n')
#        out.close() 
#        
#        
#        
#        if not keep_postgres_tbls:
#            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
#            conn.commit()
#        cur.close()
#        conn.close()
#
#    else:
#        print "Summing up totals" 
#        sys.stdout.flush()
#        start_time = time.time()
#        out = {}
#        #THESE ARE OLD AND BAD
#        #out['bysurveyed'] =    GetSqlData2("SELECT surveyed, SUM(area)/1000000.::real as area,        SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY surveyed;" %        (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
#        #out['bytype_survey'] = GetSqlData2("SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype,surveyed;" % (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
#        #out['bytype'] =        GetSqlData2("SELECT gltype, SUM(area)/1000000. as area,          SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype;" %          (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
#        #out['all'] =           GetSqlData2("SELECT SUM(area)/1000000. as area,                  SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s;" %                          (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
#        
#        out['bysurveyed'] =    GetSqlData2("SELECT surveyed,         SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY surveyed;" %         (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
#        out['bytype_survey'] = GetSqlData2("SELECT gltype, surveyed, SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype,surveyed;" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
#        out['bytype'] =        GetSqlData2("SELECT gltype,           SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype;" %          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
#        out['all'] =           GetSqlData2("SELECT                   SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s;" %                          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
#
#        
#        print "Summing up totals",time.time() - start_time,'seconds'
#        sys.stdout.flush()
#        #print out['bytype_survey']
#        
#        if not keep_postgres_tbls:
#            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
#            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
#            conn.commit()
#        cur.close()
#        conn.close()
#        return out

def extrapolate3(groups,selections,insert_surveyed_data=None, extrap_tbl='extrapolation_curves',keep_postgres_tbls=False, resulttable='resultsauto',export_shp=None,export_csv=None,density=0.850, density_err= 0.06,acrossgl_err=0.0):
    import __init__ as init

    for grp in groups:
        if not hasattr(grp,'interquartile_rng'):raise "Run statistics on groups first"
    
    #print 'connecting'    
    conn,cur = ConnectDb()
    cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
    conn.commit()

    #print 'creating'
    cur.execute("CREATE TABLE %s (gid serial PRIMARY KEY,curveid real,normbins real,mean double precision,median real,std real,sem real,quadsum real, iqr real,stdlow real, stdhigh real, q1 real,q3 real,perc5 real,perc95 real);" % extrap_tbl)
    conn.commit()

    glimsidlist = "','".join(list(itertools.chain.from_iterable([grp.glimsid for grp in groups])))
    
    
    for grpid,grp in enumerate(groups):
    
        #gltype = grp.gltype

        #if not all([x == gltype[0] for x in gltype]): 
            #raise "All in group are not same glacier type."
        #else:
            #gltype = gltype[0]
        
        stdlow = grp.dzs_mean-grp.dzs_std
        stdhigh = grp.dzs_mean+grp.dzs_std


        for i in xrange(len(grp.norme)):
            #print "INSERT INTO extrapolation_curves (normbins,gltype,mean,median,std,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%1.0f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (grp.norme[i],gltype[j],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i])
            cur.execute("INSERT INTO %s (curveid,normbins,mean,median,std,sem,quadsum,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%4.2f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,grpid,grp.norme[i],grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.quadsum[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
            if abs(grp.norme[i]-0.99)<0.0001:cur.execute("INSERT INTO %s (curveid,normbins,mean,median,std,sem,quadsum,iqr,stdlow,stdhigh,q1,q3,perc5,perc95) VALUES ('%4.2f','%4.2f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f','%7.4f')" % (extrap_tbl,grpid,1.,grp.dzs_mean[i],grp.dzs_median[i],grp.dzs_std[i],grp.dzs_sem[i],grp.quadsum[i],grp.interquartile_rng[i],stdlow[i],stdhigh[i],grp.quartile_1[i],grp.quartile_3[i],grp.percentile_5[i],grp.percentile_95[i]))
            conn.commit()
            
    cur.execute("DROP INDEX IF EXISTS curveid_index;")
    cur.execute("CREATE INDEX curveid_index ON %s (curveid);" % extrap_tbl)
    
    for grpid,grp in enumerate(groups):
        #print 'groupid',grpid    
        #glimsidlist =[item for sublist in [grp.glimsid for grp in groups] for item in sublist]
        #glimsidlist="','".join(grp.glimsid)
        #print [item for sublist in [grp.name for grp in groups] for item in sublist]
        #print glimsidlist
        if selections[grpid]!="":selections[grpid]="WHERE %s" % selections[grpid]
        if grpid==0:intotbl = "INTO %s" % resulttable
        else:intotbl=""
        
        bigselect = """
    SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.surge,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
    ext.sem::double precision,ext.quadsum::double precision,ext.iqr::double precision,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,eb.curveid as ebcurve,ext.curveid,
    eb.area*ext.mean::double precision as volchange,false as surveyed, ext.sem::double precision as error, eb.albersgeom %s 
    FROM ergibins3 as eb 
    INNER JOIN (SELECT ergi.*,gltype.surge FROM ergi LEFT JOIN gltype on ergi.glimsid=gltype.glimsid %s) as ergi on eb.glimsid=ergi.glimsid
    LEFT JOIN (SELECT * FROM %s WHERE curveid=%s) as ext on eb.normbins::real=ext.normbins
    
    WHERE ergi.glimsid NOT IN ('%s')
    
    UNION
    
    SELECT ergi.name,eb.glimsid,ergi.gltype,ergi.surge,ergi.area as glarea, eb.bins,eb.normbins,eb.area,ext.mean,ext.median,ext.std,
    ext.sem::double precision,ext.quadsum::double precision,ext.iqr::double precision,ext.stdlow,ext.stdhigh,ext.q1,ext.q3,ext.perc5,ext.perc95,eb.curveid as ebcurve,ext.curveid,
    eb.area*ext.mean::double precision as volchange,true as surveyed, ext.quadsum::double precision as error, eb.albersgeom 
    FROM ergibins3 AS eb 
    INNER JOIN (SELECT ergi.*,gltype.surge FROM ergi LEFT JOIN gltype on ergi.glimsid=gltype.glimsid %s) as ergi on eb.glimsid=ergi.glimsid
    LEFT JOIN (SELECT * FROM %s WHERE curveid=%s) as ext on eb.normbins::real=ext.normbins
    LEFT JOIN gltype on ergi.glimsid=gltype.glimsid
    WHERE ergi.glimsid IN ('%s') """  % (intotbl, selections[grpid], extrap_tbl,grpid,glimsidlist, selections[grpid], extrap_tbl,grpid,glimsidlist)
        if grpid==0:
            finalselect = bigselect
        else:
            finalselect="%s \nUNION \n%s" % (finalselect,bigselect)
    finalselect="%s;" % finalselect
    print finalselect
    #print bigselect
    import time
    start_time = time.time()

    print "Producing Results Table!"
    sys.stdout.flush()
    cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
    cur.execute(finalselect)
    conn.commit()
    cur.execute("CREATE INDEX glimid_index ON %s (glimsid);" % resulttable)
    cur.execute("CREATE INDEX normbins_index ON %s (normbins);" % resulttable)
    
    #MULTIPLYING THE ERROR FOR TIDEWATERS BY 2 TO ACCOUNT FOR THE POOR DISTRIBUTION (THIS IS DISCUSSED IN THE PAPER)
    cur.execute("UPDATE %s SET error = error*1.5 WHERE gltype='1' AND surveyed='f';" % resulttable)
    
    
    cur.execute("ALTER TABLE resultsauto add column singl_std real DEFAULT NULL;")   # this is to put the stdev of the xpts for surveyed glaciers rather than the std dev of the group
    conn.commit()
    print "Joining ergibins3 took",time.time() - start_time,'seconds'
    sys.stdout.flush()
    #cur.execute("VACUUM ANALYZE;")
     
    #INSERTING SURVEYED GLACIER DATA
    if type(insert_surveyed_data) != NoneType:
    #s2 = GetLambData(verbose=False,longest_interval=True,interval_min=min_interval,by_column=True,as_object=True)
    #s2.fix_terminus()
    #s2.normalize_elevation()
    #s2.calc_dz_stats()
        print "Insert surveyed Data"
        sys.stdout.flush()
        start_time = time.time()
    #LOOPING THROUGH EACH GLIMS ID
        for i in xrange(len(insert_surveyed_data.normdz)):
            #print "SELECT normbins::real FROM %s WHERE glimsid = '%s'" % (resulttable,insert_surveyed_data.glimsid[i])
            data = GetSqlData2("SELECT normbins::real FROM %s WHERE glimsid = '%s'" % (resulttable,insert_surveyed_data.glimsid[i]))['normbins']
            #if insert_surveyed_data.glimsid[i]=='G212334E61307N':print data
            uninormbins = N.unique(data)
            indices = (uninormbins*100).astype(int)
            indices = N.where(indices > 99,99,indices)
            indices = N.where(indices < 0,0,indices)
            
            #print i,indices
            #sys.stdout.flush()
            #insert_surveyed_data.normdz[i]
            #not every glacier will have a bin for every normalized elevation band from 0.01 to 0.99 so we are selecting the survey data for only those bands that the 
            #binned rgi has
            surveyed = [insert_surveyed_data.normdz[i][indc] for indc in indices]
            #print surveyed
            #print len(surveyed)
            normstd = [insert_surveyed_data.survIQRs[i][indc]*0.7413 for indc in indices]
            #normstd = [insert_surveyed_data.survIQRs[i][indc] for indc in indices]
            
            for j in xrange(len(surveyed)):
                
                #if insert_surveyed_data.glimsid[i]=='G212334E61307N':print       "UPDATE %s SET mean = %s,surveyed='t' WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],insert_surveyed_data.glimsid[i],uninormbins[j])
                cur.execute("UPDATE %s SET mean = %s,surveyed='t',singl_std=%s WHERE glimsid='%s' AND normbins = %s;" % (resulttable,surveyed[j],normstd[j],insert_surveyed_data.glimsid[i],uninormbins[j]))
            
            conn.commit()
        print "Insert surveyed Data took",time.time() - start_time,'seconds'
        sys.stdout.flush()
        print "here * %s *" % export_shp
    if type(export_shp) != NoneType:
        start_time = time.time()
        print "Exporting To Shpfile"
        sys.stdout.flush()
        os.system("%s -f %s -h localhost altimetry %s" % (init.pgsql2shppath,export_shp,resulttable))
        print "Exporting To Shpfile took",time.time() - start_time,'seconds'
    if type(export_csv) != NoneType:
        print "Exporting to CSV"
        sys.stdout.flush()                                                                                                                                    
        #THESE ONES ARE OLD AND INCORRECT SAVING JUST IN CASE
        #cur.execute("COPY (SELECT surveyed, SUM(area)/1000000. as area,        SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY surveyed ORDER BY surveyed) TO '%s/final_results_divd_surveyed.csv' DELIMITER ',' CSV HEADER;" %               (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        #cur.execute("COPY (SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype,surveyed ORDER BY gltype,surveyed) TO '%s/final_results_divd_surveyed_gltype.csv' DELIMITER ',' CSV HEADER;" % (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        #cur.execute("COPY (SELECT gltype, SUM(area)/1000000. as area,          SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype ORDER BY gltype) TO '%s/final_results_divd_gltype.csv' DELIMITER ',' CSV HEADER;" %                   (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csvpe)))
        #cur.execute("COPY (SELECT SUM(area)/1000000. as area,                  SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s) TO '%s/final_results_one_group.csv' DELIMITER ',' CSV HEADER;" %                                     (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        cur.execute("COPY (SELECT surveyed,         SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY surveyed ORDER BY surveyed) TO '%s/final_results_divd_surveyed.csv' DELIMITER ',' CSV HEADER;" %                      (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        cur.execute("COPY (SELECT gltype, surveyed, SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype,surveyed ORDER BY gltype,surveyed) TO '%s/final_results_divd_surveyed_gltype.csv' DELIMITER ',' CSV HEADER;" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        cur.execute("COPY (SELECT gltype,           SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype ORDER BY gltype) TO '%s/final_results_divd_gltype.csv' DELIMITER ',' CSV HEADER;" %                            (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        cur.execute("COPY (SELECT                   SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s) TO '%s/final_results_one_group.csv' DELIMITER ',' CSV HEADER;" %                                                              (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable,os.path.dirname(export_csv)))
        
        files = ['final_results_one_group.csv','final_results_divd_gltype.csv','final_results_divd_surveyed_gltype.csv','final_results_divd_surveyed.csv'] 
        out = open(export_csv,'w')
        
        
        for ope in files:
            f = open("%s/%s" % (os.path.dirname(export_csv),ope),'r')
            for i in f:
                i=re.sub('^0,','Land,',i)
                i=re.sub('^1,','Tidewater,',i)
                i=re.sub('^2,','Lake,',i)
                out.write(i)
            os.remove("%s/%s" % (os.path.dirname(export_csv,ope)))
            out.write('\n\n')
        out.close() 
        
        
        
        if not keep_postgres_tbls:
            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
            conn.commit()
        cur.close()
        conn.close()

    else:
        print "Summing up totals" 
        sys.stdout.flush()
        start_time = time.time()
        out = {}
        #THESE ARE OLD AND BAD
        #out['bysurveyed'] =    GetSqlData2("SELECT surveyed, SUM(area)/1000000.::real as area,        SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY surveyed;" %        (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
        #out['bytype_survey'] = GetSqlData2("SELECT gltype, surveyed,SUM(area)/1000000. as area, SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype,surveyed;" % (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
        #out['bytype'] =        GetSqlData2("SELECT gltype, SUM(area)/1000000. as area,          SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s GROUP BY gltype;" %          (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
        #out['all'] =           GetSqlData2("SELECT SUM(area)/1000000. as area,                  SUM(mean*area)/1000000000.*%5.3f as totalGt, SUM(mean*area)/SUM(area)*%5.3f as totalkgm2, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/1000000000. as errGt, SUM(((error*%5.3f)^2+%5.3f^2+%5.3f^2)^0.5*area)/SUM(area) as errkgm2 FROM %s;" %                          (density,density,density,density_err,acrossgl_err,density,density_err,acrossgl_err,resulttable))
        
        out['bysurveyed'] =    GetSqlData2("SELECT surveyed,         SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY surveyed;" %         (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
        out['bytype_survey'] = GetSqlData2("SELECT gltype, surveyed, SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype,surveyed;" % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
        out['bytype'] =        GetSqlData2("SELECT gltype,           SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s GROUP BY gltype;" %          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))
        out['all'] =           GetSqlData2("SELECT                   SUM(area)/1e6::real as area,SUM(mean*area)/1e9*%5.3f::real as totalGt,SUM(mean*area)/SUM(area)*%5.3f::real as totalkgm2,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as errGt,(((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as errkgm2 FROM %s;" %                          (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,resulttable))

        
        print "Summing up totals",time.time() - start_time,'seconds'
        sys.stdout.flush()
        #print out['bytype_survey']
        
        if not keep_postgres_tbls:
            cur.execute("DROP TABLE IF EXISTS %s;" % resulttable)
            cur.execute("DROP TABLE IF EXISTS %s;" % extrap_tbl)
            conn.commit()
        cur.close()
        conn.close()
        return out
        
                        
def glaciertype_to_gltype(indata):
    out = []
    for i in indata:
        if re.search('land',i):out.append(0)
        elif re.search('tidewater',i):out.append(1)
        elif re.search('lake',i):out.append(2)
    return out
    
def full_plot_extrapolation_curves(data,samples_lim=None,err_lim=None,title=None):
    alphafill = 0.1
    fig = plt.figure(figsize=[6,10])
    ax = fig.add_axes([0.11,0.56,0.8,0.4])
    #ax.set_title('Surface Elevation Change: %s Glaciers' % outroot[i])
    
    ax.set_ylabel('Balance (m w.e./yr)')
    ax.set_ylim([-10,3])
    ax.set_xlim([0,1])
    
    
    for dz in data.normdz:ax.plot(data.norme,dz,'-k',linewidth=0.5,alpha=0.4)
    ax.plot(data.norme,data.dzs_mean,'-k',linewidth=2,label='Mean')
    ax.plot(data.norme,data.dzs_median,'--k',linewidth=2,label='Median')
    #ax.plot(data.norme,data.dzs_median-data.dzs_madn,'--k')
    #ax.plot(data.norme,data.dzs_median+data.dzs_madn,'--k')
    ax.plot(data.norme,data.dzs_mean+data.dzs_sem,'-r',linewidth=0.7,label='Unsurvyed\nErr')
    ax.plot(data.norme,data.dzs_mean-data.dzs_sem,'-r',linewidth=0.7)
    ax.fill_between(data.norme,data.dzs_mean+data.dzs_std,data.dzs_mean-data.dzs_std,alpha=alphafill,color= 'black',lw=0)
    plt.legend(loc=4,fontsize=11)
    
    sort = N.argsort([dz[2] for dz in data.normdz])
    
    #print data.name[sort[0]],data.name[sort[1]],data.name[sort[2]],data.name[sort[0]],data.name[sort[-2]],data.name[sort[-1]]
    #print data.name[sort[0]], data.norme[25], data.normdz[sort[0]][25]
    ax.annotate(data.name[sort[0]], xy=(data.norme[25], data.normdz[sort[0]][25]), xytext=(0.4, -8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    ax.annotate(data.name[sort[1]], xy=(data.norme[20], data.normdz[sort[1]][20]), xytext=(0.4, -6),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    ax.annotate(data.name[sort[2]], xy=(data.norme[15], data.normdz[sort[2]][15]), xytext=(0.4, -9.),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    ax.annotate(data.name[sort[3]], xy=(data.norme[10], data.normdz[sort[3]][10]), xytext=(0.4, -7),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    ax.annotate(data.name[sort[-2]], xy=(data.norme[10], data.normdz[sort[-1]][10]), xytext=(0.4, 2.3),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    ax.annotate(data.name[sort[-1]], xy=(data.norme[15], data.normdz[sort[-2]][15]), xytext=(0.4, 1.8),arrowprops=dict(facecolor='black', headwidth=6, width=0.4,shrink=0.02))
    
    ax2 = fig.add_axes([0.11,0.35,0.8,0.18])
    ax2.plot(data.norme,N.zeros(data.norme.size),'-',color='grey')
    ax2.plot(data.norme,N.array(data.kurtosis)-3,'g-',label='Excess Kurtosis')     
    ax2.plot(data.norme,N.array(data.skew),'r-',label='Skewness')
    ax2.set_ylim([-6,6])
    ax2.set_ylabel('Test Statistic')
    plt.legend(loc='upper center', bbox_to_anchor=(0.24, -0.1),ncol=1, fancybox=True, shadow=True,fontsize=11)
    ax3 = ax2.twinx()
    ax3.plot(data.norme,N.zeros(data.norme.size)+0.05,'-',color='grey')
    ax3.plot(data.norme,N.sqrt(N.array(data.normalp)),'k-',label='Shapiro-Wilk')
    #ax3.plot(data.norme,N.array(normal2),'k-',label='DiAgostino')
    ax3.set_xlabel('Normalized Elevation')
    ax3.set_ylabel('p-values')
    ax3.set_ylim([0,1.1])
    plt.legend(loc='upper center', bbox_to_anchor=(0.78, -0.1),ncol=2, fancybox=True, shadow=True,fontsize=11) 
    
    ax4 = fig.add_axes([0.11,0.11,0.8,0.15])      
    #print data.dzs_n
    ax4.plot(data.norme,data.dzs_n,'k',label='n Samples')
    ax4.set_xlabel('Normalized Elevation')
    ax4.set_ylabel('N Samples')
    ax4.set_ylim([0,N.max(data.dzs_n)*1.1])
    plt.legend(loc='upper center',bbox_to_anchor=(0.24, -0.3),ncol=1, fancybox=True, shadow=True,fontsize=11) 
    ax5 = ax4.twinx()
    ax5.plot(data.norme,data.quadsum,'r-',label='Surveyed Err.')
    ax5.plot(data.norme,data.dzs_sem,'b-',label='Unsurveyed Err.')
    ax5.set_ylim(err_lim)
    ax4.set_ylim(samples_lim)
    ax.set_title(title)
    plt.legend(loc='upper center',bbox_to_anchor=(0.78, -0.3),ncol=1, fancybox=True, shadow=True,fontsize=11) 
    plt.show()

    return ax,ax2,ax3,ax4,ax5
