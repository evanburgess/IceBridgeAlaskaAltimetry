import psycopg2
import xlrd
import re
import unicodedata
import numpy as N
import datetime as dtm
import os
import glob
import simplekml as kml
import subprocess
from types import *
from osgeo.gdalnumeric import *
from osgeo import gdal
from osgeo.gdalnumeric import *
from osgeo import osr as osr
from osgeo import gdal
import gdal
import shapefile

def build_lat_lon_grids(xsize,ysize,projectionwkt,geotransform): 
    
    #REFERENCE SYSTEM OF GRID
    old_cs = osr.SpatialReference()
    old_cs.ImportFromWkt(projectionwkt)
    
    #REFERNCE SYSTEM OF GRID AND LAT LONG REF SYSTEM
    wgs84_wkt = """GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]"""
    new_cs = osr.SpatialReference()
    new_cs.ImportFromWkt(wgs84_wkt)
    
    #GRIDS
    mesh = N.mgrid[0:ysize, 0:xsize]
    xs = mesh[1]
    ys = mesh[0]
    
    xs,ys = pix_to_coord(geotransform,xs,ys)
    
    xs = list(N.reshape(xs,xs.size))
    ys = list(N.reshape(ys,ys.size))
    
    # create a transform object to convert between coordinate systems
    transform = osr.CoordinateTransformation(old_cs, new_cs) 
    
    #couldn't figure out how to loop a numpy array so this is the easy slow way
    lat = []
    lon = []
    
    for i,x in enumerate(xs):
        latlong = transform.TransformPoint(xs[i],ys[i])
        lat.append(latlong[1])
        lon.append(latlong[0])
    
    lat = N.array(lat)
    lon = N.array(lon)
    
    lat = N.reshape(lat,[ysize, xsize])
    lon = N.reshape(lon,[ysize, xsize])
    
    return lat,lon
  
def pix_to_coord(transform,x1,y1=None):

    if type(x1) == float or type(x1) == int:
        x = x1
        y = y1
    elif type(x1) == numpy.ndarray:
        #print 'here1', type(y1), x1.shape, y1.shape
        if x1.shape[0] == 2 and y1 == None:
            x = x1[0,:]
            y = x1[1,:]
            
        if x1.shape[0] >= 2 and type(y1) == numpy.ndarray:
            if x1.shape == y1.shape:
                x = x1[:]
                y = y1[:]
                #print 'here'
    elif type(x1) == tuple:
        x = x1[0]
        y = x1[1]
    elif type(x1) == list:
        #print 'here', type(x1[0]) 
        if type(x1[0]) == list:
            x = N.array([x2[0] for x2 in x1])
            y = N.array([x2[1] for x2 in x1])
        if type(x1[0]) == float or type(x1[0]) == int:
            x = x1[0]
            y = x1[1]
    
    x = x.astype(N.float64)
    y = y.astype(N.float64)
                   
    x *= transform[1]
    y *= transform[5]
    x += transform[0]
    y += transform[3]
 
    return x,y
    
def coord_to_pix(trans,x1,y1=None):
    
    if type(x1) == float or type(x1) == int:
        x = x1
        y = y1
    elif type(x1) == numpy.ndarray:
        #print 'here1', type(y1), x1.shape, y1.shape
        if x1.shape[0] == 2 and y1 == None:
            x = x1[0]
            y = x1[1]
            
        if x1.shape[0] > 2 and type(y1) == numpy.ndarray:
            if x1.shape == y1.shape:
                x = x1[:]
                y = y1[:]
                #print 'here'
    elif type(x1) == tuple:
        x = x1[0]
        y = x1[1]
    elif type(x1) == list:
        if type(x1[0]) == list:
            x = N.array([x2[0] for x2 in x1])
            y = N.array([x2[1] for x2 in x1])
        if type(x1[0]) == float or type(x1[0]) == int:
            x = x1[0]
            y = x1[1]
     
    x = x.astype(N.float64)
    y = y.astype(N.float64)
    #print 'minmaxin ' ,N.min(x),N.max(x)               
    x -= trans[0]
    y -= trans[3]
    x /= trans[1]
    y /= trans[5]
     
    return x,y

def shp_to_dic(shppath):
    ex = shapefile.Reader(shppath)
    shapes = ex.shapes()
    
    #print shapes[5].points
    
    shapes2 = []
    for i,shape in enumerate(shapes):
        tshape = []
        for j in xrange(len(shape.parts)-1):
            tshape.append(shape.points[shape.parts[j]:shape.parts[j+1]])
        
        dic = {}
        dic['outer']= tshape.pop(0)
        dic['inner']= tshape
        if len(dic['inner']) == 0: dic['inner']=None
        shapes2.append(dic)
    return shapes2
    
    
#def latlon_to_AkAlbers(lat,lon): 
#    
#    wgs84_wkt = """GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]"""
#    akalbers_wkt = """"PROJCS["NAD83 / Alaska Albers",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",55],PARAMETER["standard_parallel_2",65],PARAMETER["latitude_of_center",50],PARAMETER["longitude_of_center",-154],PARAMETER["false_easting",0],PARAMETER["false_northing",0],AUTHORITY["EPSG","3338"],AXIS["X",EAST],AXIS["Y",NORTH]]"""
#
#    #REFERENCE SYSTEM OF GRID
#    projectionwkt = '/Users/igswahwsmcevan/Altimetry/code/EPSG_3338_Alaska_albers.txt'
#    old_cs = osr.SpatialReference()
#    old_cs.ImportFromWkt(wgs84_wkt)
#    
#    new_cs = osr.SpatialReference()
#    new_cs.ImportFromWkt(akalbers_wkt)
#    
#    # create a transform object to convert between coordinate systems
#    transform = osr.CoordinateTransformation(old_cs, new_cs) 
#    print lat,lon
#    latlong = transform.TransformPoint(lat,lon)
#    
#    return latlong   