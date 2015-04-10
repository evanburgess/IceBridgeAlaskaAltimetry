import psycopg2
import ppygis
import scipy.stats.mstats as mstats
import scipy.stats as stats
from scipy.stats import distributions
import warnings
import re
import numpy as N
import datetime as dtm
import os
from types import *

from Analytics import *
#from osgeo.gdalnumeric import *
#import unicodedata
#import xlrd
#import glob
#import simplekml as kml
#import subprocess

#from osgeo import gdal
#import sys
#import matplotlib.pyplot as plt
#import time
#import copy as c

#from GeoTools import *
#from Analytics import *
#import ConfigParser
#from functools import wraps
#import errno
#import signal

#from Analytics import *


#def doy_to_datetime(doy,year):return dtm.date(year, 1, 1) + dtm.timedelta(doy - 1)

#class SqlObject:
#    def __init__(self, fields):
#        self.fields = fields
#        aliases = []
#
#        for (i,alias) in enumerate(fields):
#            if re.search('\sas\s',alias,re.IGNORECASE):
#                aliases.append(re.findall('as\s(.*)$',alias,re.IGNORECASE)[0])
#            else:
#                aliases.append(alias)
#        self.aliases = aliases
#
#def parse_sql(sql):
#
#    if re.search('^select',sql, re.IGNORECASE):
#        fields = re.findall('select (.*) from',sql, re.IGNORECASE)[0]
#        fields = re.sub('\s*,\s*',',',fields)
#        fields = re.sub('\(.*\)','()',fields).split(',')
#        
#        outfields = []
#        for i,field in enumerate(fields):
#            if re.search('\*',field):
#                if re.search('^\*$',field):
#                    table = re.findall('from\s+(\w+)[\s\;]',sql, re.IGNORECASE)[0] 
#                if re.search('\w+\.\*$',field):
#                    table = re.findall('(\w+)\.\*',field)[0]
#
#                conn,cur=ConnectDb()
#                
#                #find all fields in table
#                cur.execute("select column_name from information_schema.columns where table_name='"+table+"';")
#                columns = cur.fetchall()
#                cur.close
#                
#                fieldsinsert = [table+'.'+x[0] for x in columns]
#                outfields.extend(fieldsinsert)
#            else:outfields.append(field)
#            
#        out = SqlObject(outfields)
#        return out
#        #dbname = cfg.get('Section One', 'dbname'), host=cfg.get('Section One', 'host'), user=cfg.get('Section One', 'user')
        
def ConnectDb(server=None, get_host=None, get_user=None, get_dbname=None, verbose=False):

    if server == None:server='defaulthost'

    import __init__ as init
    serv = getattr(init,server)

    st = "dbname='%s' host='%s' user='%s' password='%s'" % (serv['dbname'],serv['host'],serv['user'],serv['password'])

    if get_host != None and get_user == None and get_dbname == None: return serv['host']
    if get_host == None and get_user != None and get_dbname == None: return serv['user']
    if get_host == None and get_user == None and get_dbname != None: return serv['dbname']
    
    if verbose: print st     
    
    if get_host==None and get_user == None and get_dbname == None:
        conn = psycopg2.connect(st)
        cur = conn.cursor()
        return conn,cur
    
#class LambOut:
#    def __init__(self, name, date1,date2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff,e,dz,dz25,dz75,aad,masschange,massbal,numdata):
#        self.name = name
#        self.date1 = date1
#        self.date2 = date2
#        self.volmodel = volmodel
#        self.vol25diff =vol25diff
#        self.vol75diff =vol75diff
#        self.balmodel = balmodel
#        self.bal25diff = bal25diff
#        self.bal75diff = bal75diff
#        self.e = e
#        self.dz = dz
#        self.dz25 = dz25
#        self.dz75 = dz75
#        self.aad = aad
#        self.masschange = masschange
#        self.massbal = massbal
#        self.numdata = numdata
#        self.interval = (date2 - date1).days

def kurtosistest_evan(a, axis=0):
    #a, axis = stats._chk_asarray(a, axis)
    n = N.ma.count(a,axis=axis)
    if N.min(n) < 5 and n.size==1:
        raise ValueError(
            "kurtosistest requires at least 5 observations; %i observations"
            " were given." % N.min(n))
    elif N.min(n) < 8 and n.size>1:
        warnings.warn("kurtosistest requires at least 5 observations; Outputting masked array")
    if N.min(n) < 20:
        warnings.warn(
            "kurtosistest only valid for n>=20 ... continuing anyway, n=%i" %
            N.min(n))
    b2 = mstats.kurtosis(a, axis, fisher=False)
    E = 3.0*(n-1) / (n+1)
    varb2 = 24.0*n*(n-2)*(n-3) / ((n+1)*(n+1)*(n+3)*(n+5))
    x = (b2-E)/ N.ma.sqrt(varb2)
    sqrtbeta1 = 6.0*(n*n-5*n+2)/((n+7)*(n+9)) * N.sqrt((6.0*(n+3)*(n+5)) /
                                                        (n*(n-2)*(n-3)))
    A = 6.0 + 8.0/sqrtbeta1 * (2.0/sqrtbeta1 + N.sqrt(1+4.0/(sqrtbeta1**2)))
    term1 = 1 - 2./(9.0*A)
    denom = 1 + x* N.ma.sqrt(2/(A-4.0))
    if N.ma.isMaskedArray(denom):
        # For multi-dimensional array input
        denom[denom < 0] = N.ma.masked
    elif denom < 0:
        denom = N.ma.masked
    
    term2 = N.ma.power((1-2.0/A)/denom,1/3.0)
    Z = (term1 - term2) / N.sqrt(2/(9.0*A))
    if N.min(n) < 5 and n.size>1: 
        return N.ma.masked_array(Z,mask=n<8), N.ma.masked_array(2 * distributions.norm.sf(N.abs(Z)),mask=n<8)
    else:
        return Z, 2 * distributions.norm.sf(N.abs(Z))
    
    
def skewtest_evan(a, axis=0):
    #a, axis = _chk_asarray(a, axis)
    if axis is None:
        a = a.ravel()
        axis = 0
    b2 = mstats.skew(a,axis)
    n = N.ma.count(a,axis=axis)
    if N.min(n) < 8 and n.size==1:
        raise ValueError(
            "skewtest is not valid with less than 8 samples; %i samples"
            " were given." % N.min(n))
    elif N.min(n) < 8 and n.size>1:
        warnings.warn("WARNING: Outputting masked array as some rows have less than the 8 samples required")
    y = b2 * N.ma.sqrt(((n+1)*(n+3)) / (6.0*(n-2)))
    beta2 = (3.0*(n*n+27*n-70)*(n+1)*(n+3)) / ((n-2.0)*(n+5)*(n+7)*(n+9))
    W2 = -1 + N.ma.sqrt(2*(beta2-1))
    delta = 1/N.ma.sqrt(0.5* N.ma.log(W2))
    alpha = N.ma.sqrt(2.0/(W2-1))
    y = N.ma.where(y == 0, 1, y)
    Z = delta*N.ma.log(y/alpha + N.ma.sqrt((y/alpha)**2+1))
    if N.min(n) < 8 and n.size>1: 
        return N.ma.masked_array(Z,mask=n<8), N.ma.masked_array(2 * distributions.norm.sf(N.abs(Z)),mask=n<8)
    else:
        return Z, 2 * distributions.norm.sf(N.abs(Z))
#############################################################################################
#############################################################################################    
#def read_geom_text(sin):
#    
#    s = c.deepcopy(sin) 
#    if re.search('MULTIPOLYGON',s):          
#        s = re.sub(r'MULTIPOLYGON\(\(\(','',s)
#        s = re.sub('\)\)\)','',s)
#        s2 = re.split('\)\,\(',s)
#        
#        #print len(s2)
#        s3=[]
#        for (i,ring) in enumerate(s2):
#    
#            ring = re.split(',',ring)
#        
#            for (j,tupl) in enumerate(ring):
#        #    #s3.append(tupl.split[' ']) 
#                temp = tupl.split(' ')
#                #print temp[0], temp[1]
#                sys.stdout.flush()
#                temp[0] = float(temp[0])
#                temp[1] = float(temp[1])
#                ring[j]=temp
#            s3.append(ring)
#        if len(s3) > 1:
#            outer = s3.pop(0)
#            inner = s3
#        else:
#            outer = s3[0]
#            inner = None
#            
#        return outer,inner
#        
#    if re.search('POINT',s):
#        s=re.sub('POINT\(','',s) 
#        s=re.sub('\)','',s) 
#        x,y = s.split() 
#        return x,y
#
#def GetSqlData(select,bycolumn = False):
#    """====================================================================================================
#Altimetry.Interface.GetSqlData
#
#Evan Burgess 2013-08-22
#====================================================================================================
#Purpose:
#    Extract data from postgres database using sql query and return data organized by either row or column.  
#    
#Returns: 
#    If data is returned by row (default) the requested data will be stored as a list of dictionaries where each
#    row in the output table is stored as a dictionary where the keys are the column names.  If you set aliases
#    in your sql query, the key names will follow those aliases.  If you request bycolumn, each column in the output
#    table is accessed though a dictionary where the key is the column name.  Each column of data is stored in that 
#    dictionary as a list or as a numpy array.  Special data formats are supported:
#        
#        If you request a MULTIPOLYGON geometry, the geometry will be extracted into a list of coordinates for the
#        outer ring and another list of inner rings (which is another list of coordinates).  Data is stored in the 
#        dictionary as keys 'inner' and 'outer'.  If there are no inner rings, None is returned.
#        
#        If you request ST_SummaryStats() from a raster stats are separated into values output by that function
#        including, count, sum, mean, stddev, min, max.
#        
#
#GetSqlData(select,bycolumn = False):   
#
#ARGUMENTS:        
#    select              Any postgresql select statement as string including ';'  This should be robust but
#                        let evan know if you hit a snag or want added functionality.
#KEYWORD ARGUMENTS:
#    bycolumn            Set to True to request that data be returned by column instead of row.
#====================================================================================================        
#        """
#    #connect to database and execute sql and retrieve data
#    conn,cur = ConnectDb()
#    cur.execute(select)
#    data = cur.fetchall()
#    
#    #RETRIEVING REQUESTED FIELDS AND ALIASES FOR KEYS TO OUTPUT DICTIONARY
#    sql = parse_sql(select)
#    #print sql.aliases
#    
#    
#    lst=[]
#             
#    #looping through data and setting each output to list format
#    for (j,row) in enumerate(data):
#        dic = {}
#        
#        for i,alias in enumerate(sql.aliases):
#    
#            guesstype=NoneType
#            guesstype = type(data[j][i])
#            #print alias, guesstype
#    
#            if guesstype == int or guesstype == float or guesstype == dtm.date:
#                dic[alias] = data[j][i]
#            
#            elif guesstype == list:
#                
#                listtype = type(data[j][i][0])
#                #IF INPUT IS OUTPUT FROM SUMMARY STATS OF A RASTER    -- this has to be before type float or the code will try to process as float and fail
#                if re.search('^ST_SummaryStats',sql.fields[i]):
#                    try:
#                        dic['count'],dic['sum'],dic['mean'],dic['stddev'],dic['min'],dic['max'] = [float(x) for x in re.split(',',data[j][i])] 
#                    except: pass 
#                        
#                elif listtype == int:
#                    try:
#                        dic[alias] = N.array(data[j][i],dtype=int)
#                    except:print 'Warning: Conversion of ',alias, ' to type numpy int failed.'
#                
#                elif listtype == float:
#                    try:
#                        dic[alias] = N.array(data[j][i],dtype=float)
#                    except: print 'Warning: Conversion of ',alias, ' to type numpy float failed.'
#                
#                elif listtype == dtm.date:
#                    try:
#                        dic[alias] = N.array(data[j][i],dtype=dtm.date)
#                    except: print 'Warning: Conversion of ',alias, ' to type numpy date failed.'
#                
#                elif guesstype == str:
#                    try:
#                        dic[alias] = N.core.defchararray.asarray(data[j][i])
#                    except:
#                        print 'Warning: Conversion of ',alias, ' to chararray failed.'
#                else:dic[alias] = data[j][i]
#                    
#            elif guesstype == str:
#                #IF INPUT IS A GEOGRAPHY/GEOMETRY STRING
#                #IF A MULTIPOLYGON
#                if re.search('geom',alias,re.IGNORECASE):
#                    dic['geom'] = ppygis.Geometry.read_ewkb(data[j][i])
#                elif re.search('geog',alias,re.IGNORECASE):
#                    dic['geog'] = ppygis.Geometry.read_ewkb(data[j][i])
#                else: 
#                    dic[alias] = data[j][i]
#            
#            elif guesstype == bool:
#                dic[alias] = data[j][i]
#            else:dic[alias] = data[j][i]
#                    
#    
#        lst.append(dic)
#        #if len(lst) == 1: lst = lst[0] 
#        dic = None
# 
#    
#    if bycolumn:
#        out = {}
#        for j,column in enumerate(lst[0].keys()):out[column]=[]
#            
#        for i,row in enumerate(lst):
#            for j,column in enumerate(row.keys()):
#                out[column].append(row[column])
#        
#        for j,column in enumerate(lst[0].keys()):
#            if type(out[column][-1]) == int and type(out[column][0]) == int or \
#            type(out[column][-1]) == float and type(out[column][0]) == float:
#                try:
#                    out[column] = N.array(out[column][:])
#                except:pass
#        lst=out
#    return lst
 
def GetSqlData2(select,bycolumn=True):
    """====================================================================================================
Altimetry.Interface.GetSqlData

Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Extract data from postgres database using sql query and return data organized by either row or column.  
    
Returns: 
    If data is returned by row (default) the requested data will be stored as a list of dictionaries where each
    row in the output table is stored as a dictionary where the keys are the column names.  If you set aliases
    in your sql query, the key names will follow those aliases.  If you request bycolumn, each column in the output
    table is accessed though a dictionary where the key is the column name.  Each column of data is stored in that 
    dictionary as a list or as a numpy array.  Special data formats are supported:
        
        If you request a MULTIPOLYGON geometry, the geometry will be extracted into a list of coordinates for the
        outer ring and another list of inner rings (which is another list of coordinates).  Data is stored in the 
        dictionary as keys 'inner' and 'outer'.  If there are no inner rings, None is returned.
        
        If you request ST_SummaryStats() from a raster stats are separated into values output by that function
        including, count, sum, mean, stddev, min, max.
        
GetSqlData2(select,bycolumn = False):   

ARGUMENTS:        
    select              Any postgresql select statement as string including ';'  This should be robust but
                        let evan know if you hit a snag or want added functionality.
KEYWORD ARGUMENTS:
    bycolumn            Set to True to request that data be returned by column instead of row.
====================================================================================================        
        """
    #connect to database and execute sql and retrieve data
    conn,cur = ConnectDb()
    cur.execute(select)
    fields = [d.name for d in cur.description]

    data = cur.fetchall()
    if len(data)==0:return None

    #print N.c_[fields,data[0]]

    if bycolumn:
        data = zip(*data)
        #print fields, len(data),len(data[0]),data[0][0]        
        dic = {}
        while fields:
            field = fields.pop(0)
            
            #IF DATA IS GEOM OR GEOG
            if re.search('geog|geom',field,re.IGNORECASE):
                #print field, len(data),len(data[0]),data[0][0]
                geoms = data.pop(0)
                dic[field] = [ppygis.Geometry.read_ewkb(poly) for poly in geoms]
                if hasattr(dic[field][0], 'polygons'):
                    #print dir()
                    outerring = dic[field][0].polygons[0].rings.pop(0)
                    dic['outer'] = [[point.x,point.y] for point in outerring.points]
                    dic['inner'] = [[[point.x,point.y] for point in ring.points] for ring in dic[field][0].polygons[0].rings]
                    #dic[field][0].polygons[0].rings[0].points]
                elif hasattr(dic[field][0], 'x'):
                    dic['x'] = [item.x for item in dic[field]]
                    dic['y'] = [item.y for item in dic[field]]
            else:dic[field] = N.array(data.pop(0))
            
        return dic
    else:
       lst = [] 
       while data:
            dic = {}
            row = data.pop(0)
            
            for i,field in enumerate(fields):
            
                #IF DATA IS GEOM OR GEOG
                if re.search('geog|geom',field,re.IGNORECASE):
                    #print 'here'
                    dic[field] = ppygis.Geometry.read_ewkb(row[i])
                    #if hasattr(dic[field], 'polygons'):
                    outerring = dic[field].polygons[0].rings.pop(0)
                    dic['outer'] = [[point.x,point.y] for point in outerring.points]
                    dic['inner'] = [[[point.x,point.y] for point in ring.points] for ring in dic[field].polygons[0].rings]
                    #elif hasattr(dic[field], 'x'):
                    #        dic['x'] = [item.x for item in dic[field]]
                    #        dic['y'] = [item.y for item in dic[field]]

                elif type(row[i]) == list or type(row[i]) == tuple:
                    dic[field] = N.array(row[i])
                else:
                    dic[field] = row[i]
            lst.append(dic)
       return lst


#def postgres_table_to_numpy(table):
#    
#        """
#    dbname = ConnectDb(get_dbname=1)
#    user = ConnectDb(get_user=1)
#    host = ConnectDb(get_host=1)
#
#    tempfile = '/Users/igswahwsmcevan/AK/DEM/test1.tiff'
#    
#    #print """/Applications/Postgres.app/Contents/MacOS/bin/gdal_translate -of GTiff "PG:host="""+host+" port=5432 dbname='"+dbname+"' user='"+user+"' schema='public' table="+table+""" mode=1" '"""+tempfile+"'"
#    os.system("""/Applications/Postgres.app/Contents/MacOS/bin/gdal_translate -of GTiff "PG:host="""+host+" port=5432 dbname='"+dbname+"' user='"+user+"' schema='public' table="+table+""" mode=1" '"""+tempfile+"'")
#    dataset = gdal.Open(tempfile)    
#    raster = BandReadAsArray(dataset.GetRasterBand(1))
#    #raster = N.where(raster < -1e12,N.nan,raster)
#    raster = N.ma.masked_array(raster,raster < -1e12)
#    
#    os.remove(tempfile)
#    
#    return raster
#    
#def PyClipRasterBySingleGeom(sql,gridfile=None,band=None,geotransform=None, showplot=None):
#    
#    #print type(gridfile),type(band), type(geotransform)
#    
#    if type(gridfile) == str:
#        dataset = gdal.Open(gridfile)
#        band = dataset.GetRasterBand(1).ReadAsArray()
#        geotransform = dataset.GetGeoTransform()
#    elif type(band) == N.ndarray and type(geotransform) == tuple:
#        pass
#    else: raise EvanError('check inputs')
#
#    
#    if geotransform[5] > 0: raise EvanError('This script is not yet ready for geotransforms with a ll corner tie point')
#    geom = GetSqlData2(sql,bycolumn=False)
#    
#    #OUTER BOUNDARY COORDINATES
#    pix_x,pix_y = coord_to_pix(geotransform,geom[0]['outer'])
#    
#    #print 'maxmin',N.max(pix_y), N.min(pix_y),N.max(pix_x), N.min(pix_x)
#    
#    boxl = math.floor(N.min(pix_x))
#    boxr = math.ceil(N.max(pix_x))
#    boxt = math.ceil(N.max(pix_y))
#    boxb = math.floor(N.min(pix_y))
#    
#    #CORRECTING COORDS TO CROPPED COORDS
#    pix_x -= boxl
#    pix_y -= boxb
#    
#    #print 'maxmin',N.max(pix_y), N.min(pix_y),N.min(pix_x), N.max(pix_x)
#    
#    #INNER BOUNDARY COORDINATES
#    if not type(geom[0]['inner']) == NoneType:
#        inpix_x = []
#        inpix_y = []
#        for i in xrange(len(geom[0]['inner'])):
#            tinpix_x,tinpix_y = coord_to_pix(geotransform,geom[0]['inner'][i])
#            
#            #CORRECTING COORDS TO CROPPED COORDS
#            tinpix_x -= boxl
#            tinpix_y -= boxb
#        
#            inpix_x.append(tinpix_x)
#            inpix_y.append(tinpix_y)
#        
#    #CROPPING GRID
#    crop = band[boxb:boxt+1,boxl:boxr+1]
#    
#    
#    from PIL import Image, ImageDraw
#    
#    #RASTERIZING GRID
#    img = Image.new('L', (crop.shape[1], crop.shape[0]), 0)
#    ImageDraw.Draw(img).polygon(zip(pix_x, pix_y), outline=None, fill=1)
#    if not type(geom[0]['inner']) == NoneType:
#        for i in xrange(len(geom[0]['inner'])):
#            ImageDraw.Draw(img).polygon(zip(inpix_x[i], inpix_y[i]), outline=None, fill=0)
#    
#    mask = N.array(img)
#            
#    raster = N.ma.masked_array(crop,N.logical_or(mask != 1, N.isnan(crop)))
#    
#    if showplot != None:
#        fig1 = plt.figure()
#        ax1 = fig1.add_subplot(111)
#        im = ax1.imshow(raster,extent=[0,mask.shape[1],mask.shape[0],0])
#
#        if not type(geom[0]['inner']) == NoneType:
#            for i in xrange(len(geom[0]['inner'])):
#                ax1.plot(inpix_x[i], inpix_y[i],'r')
#        ax1.plot(pix_x,pix_y)
#    
#        plt.show()
#        time.sleep(2)
#        fig1.close()
#    return raster
    
##################################################################################################################  
##################################################################################################################    
def GetLambData(removerepeats=True, days_from_year = 30,interval_min = 0,interval_max = None ,earliest_date = None,\
latest_date = None, userwhere = "",verbose = False,orderby=None,join='inner',longest_interval=False,get_geom=False,get_geog=False,\
by_column=True,as_object=False,omit=True,generalize=None,results=False,density=0.850, density_err= 0.06,acrossgl_err=0.0,get_hypsometry=False):
    """====================================================================================================
Altimetry.Interface.GetLambData
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Extract lamb data using query built from keywords input here.  Any field in glnames,gltype, or lamb can be 
    used in the query.  
    
Returns: 
    List of dictionaries of requested data. Where each item in the list is a lamb file and each dictionary key
    corresponds to the name of the column in the database.

GetLambData(help, removerepeats=True, days_from_year = 30,interval_min = 0,interval_max = None,
    earliest_date = None, latest_date = None, userwhere = "",verbose = True)    

KEYWORD ARGUMENTS:        
    removerepeats       Set to True to only select the shortest/non-overlapping intervals.  Set to false to 
                        include all data.  Default Value=True
                        
    longest_interval    Set to True to only retreive the single longest interval for each glacier.
                        
    days_from_year      Set the number of days away from 365 to be considered.  For example if you want annual 
                        intervals to be within  month of each other leave default of 30. If you want sub-annual 
                        (seasonal data) set to 365.  Default Value = 30
                        
    interval_min        Minimum length of interval in years. This is a rounded value so inputing 1 will include
                        an interval of 0.8 years if it passes the days_from_year threshold above. Default = 0 
                        
    interval_max        Maximum length of interval in years. This is a rounded value so inputing 3 will include
                        an interval of 3.1 years if it passes the days_from_year threshold  above. Default = None
                        
    earliest_date       Earliest date of first acquistion. Enter as string 'YYYY-MM-DD'. Default = None
    
    latest_date         Latest date of second acquistion. Enter as string 'YYYY-MM-DD'. Default = None
    
    userwhere = ""      User can input additional queries as a string to a where statement.
                        Example input:"glnames.name like '%Columbia%' AND ergi.area > 10"
                        
    verbose             Verbose output. Default = True
    
    get_geom            Set to True to retrieve the Geometry of the glacier polygon
    
    generalize          Set to a value to simplify geometries
    
    join                You can either select 'inner' joins or 'left' joins to the other tables. If inner
                        joins are selected only lamb entries with a glimsid and an entry in the gltype table
                        are considered.  Others are removed.  Let will include all entries in the lamb table
                        whether or not they have other attributes attached to them.
                
    by_column           Get data organized by column instead of by lamb file
    
    as_object           Get data output as a LambObject.  Only works if by_column = True (Default=True)
    
    omit                Default will ignore glaciers labeled as omit in the gltype table.  Set to false
                        to include these glaciers
====================================================================================================        
        """
    
    select1 = """select \
lamb.gid,\
lamb.glid,\
lamb.date1,\
lamb.date2,\
lamb.interval,\
lamb.volmodel,\
lamb.vol25diff,\
lamb.vol75diff,\
lamb.balmodel,\
lamb.bal25diff,\
lamb.bal75diff,\
ergi.glimsid,\
gltype.surge,\
gltype.tidewater,\
gltype.lake,\
gltype.river,\
gltype.glaciertype,\
glnames.name as lambname,\
glnames.region,\
lamb.e,\
lamb.dz,\
lamb.dz25,\
lamb.dz75,\
lamb.aad,\
lamb.masschange,\
lamb.massbal,\
lamb.numdata,\
ergi.gltype,\
ergi.glactype,\
ergi.region,\
ergi.max::real,\
ergi.min::real,\
flx.eb_bm_flx,\
flx.eb_best_flx,\
flx.eb_low_flx,\
flx.eb_high_flx,\
flx.eb_bm_err,\
flx.bm_length,\
flx.smb,\
ergi.continentality,\
ergi.area::double precision,\
ergi.name,\
"""

#eb_bm_flx

#ergi.max,\
#ergi.mn_dist_coast,\
#ergi.mn_elev,\
#ergi.meanVel,\


    if get_geom:
        if generalize != None: select2 = "ST_Simplify(ergi.albersgeom, %s) as albersgeom," % generalize
        else: select2 = "ergi.albersgeom as albersgeom,"
    elif get_geog: 
        if generalize != None: select2 = "ST_Simplify(ergi.geog::geometry, %s) as geog," % generalize
        else: select2 = "ergi.geog as geog,"
    else: select2 = ''

    select3 = """lamb.numdata \
from lamb inner join glnames on glnames.gid=lamb.glid inner join gltype on glnames.gid=gltype.glid
inner join ergi on glnames.glimsid=ergi.glimsid left join tidewater_flux as flx on ergi.glimsid=flx.glimsid """    

    if results:
        select1 = select1 + "rlt.rlt_totalGt,rlt.rlt_totalkgm2,rlt.rlt_errGt,rlt.rlt_errkgm2,rlt.rlt_singlerrGt,rlt.rlt_singlerrkgm2,"
        
        #select3 = select3 + """ LEFT JOIN (SELECT rlt.glimsid,
        #SUM(rlt.area)/1e6::real as area, 
        #SUM(rlt.mean*rlt.area)/1e9*%5.3f::real as rlt_totalGt,
        #(((((SUM(rlt.error*rlt.area)/SUM(rlt.mean*rlt.area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(rlt.mean*rlt.area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as rlt_errGt,
        #SUM(rlt.mean*rlt.area)/SUM(rlt.area)*%5.3f::real as rlt_totalkgm2,
        #(((((SUM(rlt.error*rlt.area)/SUM(rlt.mean*rlt.area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(rlt.mean*rlt.area)/SUM(rlt.area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_errkgm2,
        #(((((SUM(rlt.singl_std*rlt.area)/SUM(rlt.mean*rlt.area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(rlt.mean*rlt.area)/1e9*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_singlerrkgm2,
        #(((((SUM(rlt.singl_std*rlt.area)/SUM(rlt.mean*rlt.area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(rlt.mean*rlt.area)/SUM(rlt.area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_singlerrGt
        #FROM resultsauto as rlt GROUP BY rlt.glimsid) as rlt on ergi.glimsid=rlt.glimsid """ % (density,density_err,density, density, acrossgl_err,density,
        #density_err,density, density, acrossgl_err,density_err,density, density, acrossgl_err,density_err,density, density, acrossgl_err)

        select3 = select3 + """ LEFT JOIN (SELECT glimsid,
        SUM(area)/1000000. as area,
        SUM(mean*area)/1e9*%5.3f::real as rlt_totalGt,
        SUM(mean*area)/SUM(area)*%5.3f::real as rlt_totalkgm2,
        (((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as rlt_errGt,
        (((((SUM(error*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_errkgm2,
        (((((SUM(singl_std*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/SUM(area)*%5.3f)^2+(%5.3f)^2)^0.5::real as rlt_singlerrkgm2,
        (((((SUM(singl_std*area)/SUM(mean*area))^2+(%5.3f/%5.3f)^2)^0.5)*SUM(mean*area)/1e9*%5.3f)^2 + (%5.3f)^2)^0.5::real as rlt_singlerrGt 
        FROM resultsauto GROUP BY glimsid) as rlt on ergi.glimsid=rlt.glimsid """ % (density,density,density_err,density,density, acrossgl_err,density_err,density,density,acrossgl_err,density_err,density,density,acrossgl_err,density_err,density,density,acrossgl_err)

    select = select1+select2+select3


#ST_AsText(ergi.albersgeom) as geom \

    if longest_interval:removerepeats = False

    if join != 'inner': re.sub('inner join','left join',select)     
    
    if longest_interval:
        order = """ order by glnames.name,lamb.interval DESC;"""
        removerepeats = False
    else:order = """ order by glnames.name,lamb.date1,lamb.interval;"""
    
    where = 'WHERE' 
    
    if days_from_year != None: where = where+' AND ((interval % 365) > '+str(365-days_from_year)+' OR (interval % 365) < '+str(days_from_year)+')'
    if interval_min != None: where = where+' AND (ROUND(interval/365.) >= '+str(interval_min)+')'
    if interval_max != None: where = where+' AND (ROUND(interval/365.) <= '+str(interval_max)+')'
    if earliest_date != None: where = where+" AND date1 >= '"+str(earliest_date)+"'"
    if latest_date != None: where = where+" AND date2 <= '"+str(latest_date)+"'"
    if omit: where = where+" AND omit='f'"
    
    
    userwhere2 = re.sub('where','',userwhere, re.IGNORECASE)
    userwhere2 = re.sub('^\s*and\s*','',userwhere2, re.IGNORECASE)
    userwhere2 = re.sub('^\s*','',userwhere2)
    userwhere2 = re.sub('\s*$','',userwhere2)
    if userwhere != '':userwhere2 = ' AND '+userwhere2+' '
    
    where = where+userwhere2
    
    where = re.sub('WHERE AND','WHERE',where)
     
    if verbose:print select+where+order
    
    s = GetSqlData2(select+where+order,bycolumn=False)
    if type(s)==NoneType: return None
    #print s[0].keys()
    deletelist = []
    keeplist = []
    lastgl = ''
    lastdate = dtm.date(1900,1,1)
    
    if removerepeats:
        if verbose: print'Filtering lamb entries:'
        for i,row in enumerate(s):

            if row['name'] == lastgl:
                #print '  ',row['lamb.date1'],lastdate
                if row['date1'] < lastdate:
                    deletelist.append(i)
                    if verbose:print '  ',row['name'],row['date1'],row['date2'],'-- Omitted'
                else:
                    lastdate = row['date2']
                    if verbose:print row['name'],row['date1'],row['date2']
                    keeplist.append(row['gid'])
            else: 
                lastgl = row['name']
                lastdate = row['date2']
                if verbose:print row['name'],row['date1'],row['date2']
                keeplist.append(row['gid'])
                
    if longest_interval:
        if verbose: print'Filering for longest interval:'
        for i,row in enumerate(s):

            if row['name'] == lastgl:
                #print '  ',row['lamb.date1'],lastdate
                #if row['lamb.date1'] < lastdate:
                deletelist.append(i)
                if verbose:print '  ',row['name'],row['date1'],row['date2'],row['interval'],'-- Omitted'
                #else:
                #    lastdate = row['lamb.date2']
                #    if verbose:print row['glnames.name'],row['lamb.date1'],row['lamb.date2']
                #    keeplist.append(row['lamb.gid'])
            else: 
                lastgl = row['name']
                lastdate = row['date2']
                if verbose:print row['name'],row['date1'],row['date2'],row['interval']
                keeplist.append(row['gid'])
        
    if orderby == None:
        #print len(s)
        s = N.delete(N.array(s),deletelist)
        if get_hypsometry:
            for i in s:
                hyps = GetSqlData2("SELECT area::real as binned_area,bins::real,normbins::real FROM ergibins3 WHERE glimsid='%s' ORDER BY normbins" % i['glimsid'])
                for key in ('binned_area','bins','normbins'):i[key]=hyps[key]
        
        if by_column:s = LambToColumn(s)
    else:
        s = GetSqlData2(select+'WHERE lamb.gid IN ('+re.sub('[\[\]]','',str(keeplist))+") ORDER BY "+orderby+";", bycolumn=by_column)
        
        if get_hypsometry:
            s['binned_area'] = []
            s['bins'] = []
            s['normbins'] = []
            for glimsidt in s['glimsid']:
                print glimsidt
                hyps = GetSqlData2("SELECT area as binned_area,bins,normbins FROM ergibins3 WHERE glimsid='%s' ORDER BY normbins" % glimsidt)
                s['binned_area'].append(hyps['binned_area'])
                s['bins'].append(hyps['bins'])
                s['normbins'].append(hyps['normbins'])
                                                                
    #                                                                            
    #if orderby == None:
    #    #print len(s)
    #    s = N.delete(N.array(s),deletelist)
    #    #print len(s)
    #    if by_column:s = LambToColumn(s)
    #else:
    #    s = GetSqlData2(select+'WHERE lamb.gid IN ('+re.sub('[\[\]]','',str(keeplist))+") ORDER BY "+orderby+";", bycolumn=by_column)
    #    
    #if verbose:print len(s),' of rows in lamb selected.'


    if len(s) == 0: return None

    if as_object:
        if type(s) == dict:
            s=LambObject(s)
            print 'object'
        elif type(s) == list or type(s) == N.ndarray:
            s = [LambObject(row) for row in s]
            print 'list'
       
    return s  
    
    #def norm_e(self):return (self.e - self.min) / (self.max - self.min)
    
#def quadrat(region):
#    #quadrat method to find variance between regions. Stastical Methods in Geography Rogerson pg 157
#    regions = list(set(region))
#    ptspercell = N.array([N.where(N.array(region) == x)[0].size for x in regions])
#    var = (N.sum((ptspercell - N.mean(ptspercell))**2))/(ptspercell.size-1)   
#    return  var/N.mean(ptspercell)
    
class LambObject:
    def __init__(self, indata):
        #print indata.keys()
        for i,key in enumerate(indata.keys()):
            if 'gid' in indata.keys():self.gid = indata['gid']
            if 'glid' in indata.keys():self.glid = indata['glid']
            if 'date1' in indata.keys():self.date1 = indata['date1']
            if 'date2' in indata.keys():self.date2 = indata['date2']
            if 'interval' in indata.keys():self.interval = indata['interval']
            if 'volmodel' in indata.keys():self.volmodel = indata['volmodel']
            if 'vol25diff' in indata.keys():self.vol25diff = indata['vol25diff']
            if 'vol75diff' in indata.keys():self.vol75diff = indata['vol75diff']
            if 'balmodel' in indata.keys():self.balmodel = indata['balmodel']
            if 'bal25diff' in indata.keys():self.bal25diff = indata['bal25diff']
            if 'bal75diff' in indata.keys():self.bal75diff = indata['bal75diff']
            if 'surge' in indata.keys():self.surge = indata['surge']
            if 'tidewater' in indata.keys():self.tidewater = indata['tidewater']
            if 'lake' in indata.keys():self.lake = indata['lake']
            if 'river' in indata.keys():self.river = indata['river']
            if 'name' in indata.keys():self.name = indata['name']
            if 'region' in indata.keys():self.region = indata['region']
            if 'e' in indata.keys():self.e = indata['e']
            if 'dz' in indata.keys():self.dz = indata['dz']
            if 'dz25' in indata.keys():self.dz25 = indata['dz25']
            if 'dz75' in indata.keys():self.dz75 = indata['dz75']
            if 'aad' in indata.keys():self.aad = indata['aad']
            if 'masschange' in indata.keys():self.masschange = indata['masschange']
            if 'massbal' in indata.keys():self.massbal = indata['massbal']
            if 'geom' in indata.keys():self.geom = indata['geom']
            if 'geog' in indata.keys():self.geog = indata['geog']
            if 'min' in indata.keys():self.min = indata['min']
            if 'max' in indata.keys():self.max = indata['max']
            if 'glaciertype' in indata.keys():self.glaciertype = indata['glaciertype']
            if 'gltype' in indata.keys():self.gltype = indata['gltype']
            if 'numdata' in indata.keys():self.numdata = indata['numdata']
            if 'glimsid' in indata.keys():self.glimsid = indata['glimsid']
            if 'continentality' in indata.keys():self.continentality = indata['continentality']
            if 'eb_best_flx' in indata.keys():self.eb_best_flx = indata['eb_best_flx']
            if 'eb_high_flx' in indata.keys():self.eb_high_flx = indata['eb_high_flx']
            if 'eb_low_flx' in indata.keys():self.eb_low_flx = indata['eb_low_flx']
            if 'eb_bm_flx' in indata.keys():self.eb_bm_flx = indata['eb_bm_flx']
            if 'eb_bm_err' in indata.keys():self.eb_bm_err = indata['eb_bm_err']
            if 'smb' in indata.keys():self.smb = indata['smb']
            if 'area' in indata.keys():self.area = indata['area']
            if 'bm_length' in indata.keys():self.bm_length = indata['bm_length']
            if 'rlt_totalgt' in indata.keys():self.rlt_totalgt = indata['rlt_totalgt']
            if 'rlt_errgt' in indata.keys():self.rlt_errgt = indata['rlt_errgt']
            if 'rlt_totalkgm2' in indata.keys():self.rlt_totalkgm2 = indata['rlt_totalkgm2']
            if 'rlt_errkgm2' in indata.keys():self.rlt_errkgm2 = indata['rlt_errkgm2']
            if 'rlt_singlerrkgm2' in indata.keys():self.rlt_singlerrkgm2 = indata['rlt_singlerrkgm2']
            if 'rlt_singlerrgt' in indata.keys():self.rlt_singlerrgt = indata['rlt_singlerrgt']     
            if 'binned_area' in indata.keys():self.binned_area = indata['binned_area']
            if 'bins' in indata.keys():self.bins = indata['bins']
            if 'normbins' in indata.keys():self.normbins = indata['normbins']    
            
    def convert085(self):
        self.dz = [dz * 0.85 for dz in self.dz]
        self.dz25 = [dz * 0.85 for dz in self.dz25]
        self.dz75 = [dz * 0.85 for dz in self.dz75]
            

    def normalize_elevation(self,gaussian = None):
        
        if type(self.name) == list:
        
            #mn = N.min([N.min(x) for x in self.e])
            #mx = N.max([N.max(x) for x in self.e])
            
       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
       	
            self.normdz = []
            self.norm25 = []
            self.norm75 = []
            self.survIQRs = []
            
            for j,obj in enumerate(self.dz):
            
                if gaussian != None:
                    interval = self.e[j][1]-self.e[j][0]
                    sigma_intervals = gaussian / interval
                    
                    y = gaussian_filter(obj,sigma_intervals)
                    y25 = gaussian_filter(self.dz25[j],sigma_intervals)
                    y75 = gaussian_filter(self.dz75[j],sigma_intervals)
                else: 
                    y = obj
                    y25 = self.dz25[j]
                    y75 = self.dz75[j]
                
                e = self.e[j].astype(N.float32)
                #x = (e-N.min(e))/(N.max(e)-N.min(e))
                x = (e-self.min[j])/(self.max[j]-self.min[j])
                
                normdzhold = N.interp(self.norme,x,y)
                new25shold = N.interp(self.norme,x,y25)
                new75shold = N.interp(self.norme,x,y75)
                iqr = new75shold - new25shold 
                #print 'ehrererasdfa'
                
                
                if type(obj) == N.ma.core.MaskedArray: 
                     #print 'masked!!!!'
                     mask = N.interp(self.norme,x,N.ma.getmask(obj).astype(float),N.nan,N.nan).round().astype(bool)
                     normdzhold = N.ma.masked_array(normdzhold,mask)
                     new25shold = N.ma.masked_array(new25shold,mask)
                     new75shold = N.ma.masked_array(new75shold,mask)
                     iqr = N.ma.masked_array(iqr,mask)
                
                self.normdz.append(normdzhold)
                self.norm25.append(new25shold)         
                self.norm75.append(new75shold) 
                self.survIQRs.append(iqr)

#            for j,obj in enumerate(self.dz25):
#            
#                if gaussian != None:
#                    interval = self.e[j][1]-self.e[j][0]
#                    sigma_intervals = gaussian / interval
#                    
#
#                else: 
#                    y25 = obj
#                    y75 = self.dz75[j]
#                
#                e = self.e[j].astype(N.float32)
#                x = (e-N.min(e))/(N.max(e)-N.min(e))
#            
#                new25shold = N.interp(self.norme,x,y25,N.nan,N.nan)
#                new75shold = N.interp(self.norme,x,y75,N.nan,N.nan)
#                iqr = new75shold - new25shold 
#                
#
#
#                
#                self.norm25.append(new25shold)         
#                self.norm75.append(new75shold) 
#                self.survIQRs.append(iqr)
#                
            return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
        else:
                  
            #mn = N.min([N.min(x) for x in self.e])
            #mx = N.max([N.max(x) for x in self.e])
            
       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
       	
            #self.normdz = []
            #self.norm25 = []
            #self.norm75 = []
            #self.survIQRs = []
            
            #for j,obj in enumerate(self.dz):
            
            if gaussian != None:
                interval = self.e[1]-self.e[0]
                sigma_intervals = gaussian / interval
                
                y = gaussian_filter(self.dz,sigma_intervals)
                y25 = gaussian_filter(self.dz25,sigma_intervals)
                y75 = gaussian_filter(self.dz75,sigma_intervals)
            else: 
                y = self.dz
                y25 = self.dz25
                y75 = self.dz75
            
            e = self.e.astype(N.float32)
            #x = (e-N.min(e))/(N.max(e)-N.min(e))
            x = (e-self.min)/(self.max-self.min)    
                    
            normdzhold = N.interp(self.norme,x,y,N.nan,N.nan)
            new25shold = N.interp(self.norme,x,y25,N.nan,N.nan)
            new75shold = N.interp(self.norme,x,y75,N.nan,N.nan)
            iqr = new75shold - new25shold 
            #print 'ehrererasdfa'
            if type(self.dz) == N.ma.core.MaskedArray: 
                #print 'masked!!!!'
                mask = N.interp(self.norme,x,N.ma.getmask(self.dz).astype(float),N.nan,N.nan).round().astype(bool)
                normdzhold = N.ma.masked_array(normdzhold,mask)
                new25shold = N.ma.masked_array(new25shold,mask)
                new75shold = N.ma.masked_array(new75shold,mask)
                iqr = N.ma.masked_array(iqr,mask)
            
            self.normdz=normdzhold
            self.norm25=new25shold        
            self.norm75=new75shold
            self.survIQRs=iqr
            
        return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
        
#    def normalize_elevation(self,gaussian = None):
#        
#        if type(self.name) == list:
#        
#            #mn = N.min([N.min(x) for x in self.e])
#            #mx = N.max([N.max(x) for x in self.e])
#            
#       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
#       	
#            self.normdz = []
#            self.norm25 = []
#            self.norm75 = []
#            self.survIQRs = []
#            
#            for j,obj in enumerate(self.dz):
#            
#                if gaussian != None:
#                    interval = self.e[j][1]-self.e[j][0]
#                    sigma_intervals = gaussian / interval
#                    
#                    y = gaussian_filter(obj,sigma_intervals)
#                    y25 = gaussian_filter(self.dz25[j],sigma_intervals)
#                    y75 = gaussian_filter(self.dz75[j],sigma_intervals)
#                else: 
#                    y = obj
#                    y25 = self.dz25[j]
#                    y75 = self.dz75[j]
#                
#                e = self.e[j].astype(N.float32)
#                #x = (e-N.min(e))/(N.max(e)-N.min(e))
#                x = (e-self.min[j])/(self.max[j]-self.min[j])
#                
#                normdzhold = N.interp(self.norme,x,y)
#                new25shold = N.interp(self.norme,x,y25)
#                new75shold = N.interp(self.norme,x,y75)
#                iqr = new75shold - new25shold 
#                #print 'ehrererasdfa'
#                
#                
#                if type(obj) == N.ma.core.MaskedArray: 
#                     #print 'masked!!!!'
#                     mask = N.interp(self.norme,x,N.ma.getmask(obj).astype(float),N.nan,N.nan).round().astype(bool)
#                     normdzhold = N.ma.masked_array(normdzhold,mask)
#                     new25shold = N.ma.masked_array(new25shold,mask)
#                     new75shold = N.ma.masked_array(new75shold,mask)
#                     iqr = N.ma.masked_array(iqr,mask)
#                
#                self.normdz.append(normdzhold)
#                self.norm25.append(new25shold)         
#                self.norm75.append(new75shold) 
#                self.survIQRs.append(iqr)
#
##            for j,obj in enumerate(self.dz25):
##            
##                if gaussian != None:
##                    interval = self.e[j][1]-self.e[j][0]
##                    sigma_intervals = gaussian / interval
##                    
##
##                else: 
##                    y25 = obj
##                    y75 = self.dz75[j]
##                
##                e = self.e[j].astype(N.float32)
##                x = (e-N.min(e))/(N.max(e)-N.min(e))
##            
##                new25shold = N.interp(self.norme,x,y25,N.nan,N.nan)
##                new75shold = N.interp(self.norme,x,y75,N.nan,N.nan)
##                iqr = new75shold - new25shold 
##                
##
##
##                
##                self.norm25.append(new25shold)         
##                self.norm75.append(new75shold) 
##                self.survIQRs.append(iqr)
##                
#            return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
#        else:
#                  
#            #mn = N.min([N.min(x) for x in self.e])
#            #mx = N.max([N.max(x) for x in self.e])
#            
#       	    self.norme = N.arange(0,1,0.01,dtype=N.float32)
#       	
#            #self.normdz = []
#            #self.norm25 = []
#            #self.norm75 = []
#            #self.survIQRs = []
#            
#            #for j,obj in enumerate(self.dz):
#            
#            if gaussian != None:
#                interval = self.e[1]-self.e[0]
#                sigma_intervals = gaussian / interval
#                
#                y = gaussian_filter(self.dz,sigma_intervals)
#                y25 = gaussian_filter(self.dz25,sigma_intervals)
#                y75 = gaussian_filter(self.dz75,sigma_intervals)
#            else: 
#                y = self.dz
#                y25 = self.dz25
#                y75 = self.dz75
#            
#            e = self.e.astype(N.float32)
#            x = (e-N.min(e))/(N.max(e)-N.min(e))
#            
#            normdzhold = N.interp(self.norme,x,y,N.nan,N.nan)
#            new25shold = N.interp(self.norme,x,y25,N.nan,N.nan)
#            new75shold = N.interp(self.norme,x,y75,N.nan,N.nan)
#            iqr = new75shold - new25shold 
#            #print 'ehrererasdfa'
#            if type(self.dz) == N.ma.core.MaskedArray: 
#                #print 'masked!!!!'
#                mask = N.interp(self.norme,x,N.ma.getmask(self.dz).astype(float),N.nan,N.nan).round().astype(bool)
#                normdzhold = N.ma.masked_array(normdzhold,mask)
#                new25shold = N.ma.masked_array(new25shold,mask)
#                new75shold = N.ma.masked_array(new75shold,mask)
#                iqr = N.ma.masked_array(iqr,mask)
#            
#            self.normdz=normdzhold
#            self.norm25=new25shold        
#            self.norm75=new75shold
#            self.survIQRs=iqr
#            
#        return self.norme,self.normdz,self.norm25,self.norm75,self.survIQRs
#    
    def calc_mb (self,units='area normalized'):
        
        if not 'binned_area' in dir(self):raise "ERROR: Need to first run GetLambData with 'get_hypsometry=True'"
        if not 'normdz' in dir(self):raise "ERROR: need to run normalize_elevation method first."
        if not type(self.name) == list:raise "ERROR: Object needs to be BY column"
        
        binvol = []
        for binarea,nomdz,nobin in zip(self.binned_area,self.normdz,self.normbins):
            if units == 'area normalized':
                binvol.append(N.sum(binarea*nomdz[(nobin*100).astype(int)])/N.sum(binarea)*0.85)
            elif units == 'gt':
                binvol.append(N.sum(binarea*nomdz[(nobin*100).astype(int)])/1e9*0.85)
            else:raise "ERROR: units key must be 'area normalized' or 'gt'"
        self.mb = N.array(binvol)
        
    def calc_dz_stats(self,masked_array=False,too_few=None):
        if not type(self.name) == list:raise "ERROR: Object needs to be BY column"
        if not hasattr(self, 'normdz'):raise "ERROR: need to run normalize_elevation method first."
    
        newys2 = N.c_[self.normdz]
   
        if type(self.normdz[0]) == N.ma.core.MaskedArray: 
            mask = N.c_[[list(N.ma.getmask(x)) for x in self.normdz]]
            newys2 = N.ma.masked_array(newys2,mask)
            
        #if masked_array: 
        #    newys2 = N.ma.masked_array(newys2,N.isnan(newys2))
            #survIQR = N.ma.masked_array(survIQR,N.isnan(new25))
        
        #print type(newys3)
        #print newys3.shape
            
            #if label != None: label = "%s N=%s" % (label,len(s))
            #newys3 = N.ma.masked_array(newys2,N.isnan(newys2))
    
        if type(self.normdz[0]) == N.ma.core.MaskedArray:
            survIQRs2 = N.c_[self.survIQRs]
            mask = N.c_[[list(N.ma.getmask(x)) for x in self.survIQRs]]
            survIQRs2 = N.ma.masked_array(survIQRs2,mask)
            
            self.dzs_n = N.sum((mask == False).astype(int),axis=0)
            dzs_n_nozero= N.where(N.logical_or(self.dzs_n==0,self.dzs_n==1),N.nan,self.dzs_n)
            self.quadsum = N.ma.sqrt(N.ma.sum((survIQRs2.T*0.7413)**2,axis=1))/N.sqrt(dzs_n_nozero*(dzs_n_nozero-1))
            #print N.ma.sum((survIQRs2.T*0.7413)**2,axis=1)
        else: 
            self.dzs_n = len(self.normdz)
            dzs_n_nozero= N.where(N.logical_or(self.dzs_n==0,self.dzs_n==1),N.nan,self.dzs_n)
            self.quadsum = N.sqrt(N.sum(((N.array(self.survIQRs).T)*0.7413)**2,axis=1))/N.sqrt(dzs_n_nozero*(dzs_n_nozero-1))  #SCALING TO A STANDARD DEVIATION EQUIVALENT then calculating quadrature sum


        self.dzs_std = N.ma.std(newys2,axis=0)

        self.dzs_sem = self.dzs_std/N.ma.sqrt(dzs_n_nozero)
        self.dzs_mean = N.ma.mean(newys2,axis=0)
        self.dzs_madn = mad(newys2,axis=0,normalized=True)
        self.dzs_median = N.ma.median(newys2,axis=0)
        
        #IF THERE ARE TOO FEW VALUES TO PRODUCE A MEAN THEN EXTEND USING THE LAST GOOD MEAN ESTIMATE.
        if type(too_few) != NoneType:
            wenough = N.where(self.dzs_n>too_few)[0]
            x = N.arange(len(self.dzs_n))[wenough]
            print wenough,x
            
            quadsum = self.quadsum[wenough]
            dzs_std = self.dzs_std[wenough]
            dzs_sem = self.dzs_sem[wenough]
            dzs_mean = self.dzs_mean[wenough]
            dzs_madn = self.dzs_madn[wenough]
            dzs_median = self.dzs_median[wenough]
                                    
            self.quadsum = N.interp(N.arange(len(self.dzs_n)),x,quadsum)
            self.dzs_std = N.interp(N.arange(len(self.dzs_n)),x,dzs_std)
            self.dzs_sem = N.interp(N.arange(len(self.dzs_n)),x,dzs_sem)
            self.dzs_mean = N.interp(N.arange(len(self.dzs_n)),x,dzs_mean)
            self.dzs_madn = N.interp(N.arange(len(self.dzs_n)),x,dzs_madn)
            self.dzs_median = N.interp(N.arange(len(self.dzs_n)),x,dzs_median)

         
        self.normalp=[] 
        for ty in newys2.T:
            if type(self.normdz[0]) == N.ma.core.MaskedArray: ty = ty.compressed()  # remove masked values since shapiro doesn't deal with masks
            if ty.size > 2:
                Wstat,pval1 = stats.shapiro(ty)
                self.normalp.append(pval1)
            else:  self.normalp.append(N.nan)
             
        self.skewz,self.skewp = skewtest_evan(N.ma.masked_array(newys2,mask=N.isnan(newys2)),axis=0)
        self.kurtz,self.kurtp = kurtosistest_evan(newys2,axis=0)  
        self.skew = stats.skew(newys2,axis=0)
        self.kurtosis = stats.kurtosis(newys2,axis=0)
        
        self.percentile_5, self.quartile_1,self.percentile_33,self.percentile_66,self.quartile_3,self.percentile_95 = mstats.mquantiles(newys2,prob=[0.05,0.25,0.33,0.66,0.75,0.95],axis=0)
        self.interquartile_rng = self.quartile_3-self.quartile_1
        
        #quadrat method to find variance between regions. Stastical Methods in Geography Rogerson pg 157
        regions = list(set(self.region))
        ptspercell = N.array([N.where(N.array(self.region) == x)[0].size for x in regions])
        var = (N.sum((ptspercell - N.mean(ptspercell))**2))/(ptspercell.size-1)   
        self.quadratcluster = var/N.mean(ptspercell)
        
        
        #
    def calc_residuals_zscores(self):
        if not hasattr(self, 'normdz'):raise "ERROR: need to run normalize_elevation method first."
        if not hasattr(self, 'dzs_mean'):raise "ERROR: need to run calc_dz_stats method first."
        
        self.resids=[]
        self.zscores=[]
        for curve in self.normdz:self.resids.append(curve-self.dzs_mean)
        for curve in self.resids:self.zscores.append(curve/self.dzs_std)
    
    def get_approx_location(self):
        
        self.approxlon=[]
        self.approxlat=[]
        
        for k,gid in enumerate(self.gid):
            print k
            xpts=GetSqlData2("SELECT z1,geog from xpts WHERE lambid=%s" % gid)
            
            print 'len xpts',len(xpts['z1'])
            
            srt = N.argsort(xpts['z1'])
            sortd = [xpts['z1'][item] for item in srt]
            sortgeog = [xpts['geog'][item] for item in srt]
            
            normz = (sortd - N.min(self.e[k]))/(N.max(self.e[k])-N.min(self.e[k]))
            
            print 'normz',len(normz)
            print 'e',N.max(self.e[k]),N.min(self.e[k])
            print 'sorted',N.max(sortd),N.min(sortd)
            print 'normz',N.max(normz),N.min(normz)
            print 'normk',self.norme[k]
            
            x=[xy.x for xy in sortgeog]
            y=[xy.y for xy in sortgeog]
            
            self.approxlon.append(N.interp(self.norme, normz, x,N.nan,N.nan))
            self.approxlat.append(N.interp(self.norme, normz, y,N.nan,N.nan))
          
    def fix_terminus(self,slope=-0.05,error=1):
        if not type(self.numdata) == list:
            cumulative = N.cumsum(self.numdata)
            
            for i,val in enumerate(cumulative):
                if val != 0:break
        
            self.dz = N.where(cumulative == 0, N.nan,self.dz)
            self.dz25 = N.where(cumulative == 0, N.nan,self.dz25)
            self.dz75 = N.where(cumulative == 0, N.nan,self.dz75)
            
            deriv = N.ediff1d(self.dz)#ediff1d
            #print lambobj.dz
            #print deriv
            
            for i,bn in enumerate(deriv):
                if not N.isnan(bn):
                    if bn < slope and self.dz[i]<0.1: 
                        self.dz[i]=N.nan
                    else:break
            nanreplace = N.isnan(self.dz)
            self.dz = N.where(nanreplace, self.dz[i],self.dz)
            self.dz25 = N.where(nanreplace, self.dz25[i]-error,self.dz25)
            self.dz75 = N.where(nanreplace, self.dz75[i ]+error,self.dz75)
            return deriv
            
        else:
            for j in xrange(len(self.numdata)):
                
                cumulative = N.cumsum(self.numdata[j])
                
                for i,val in enumerate(cumulative):
                    if val != 0:break
            
                self.dz[j] = N.where(cumulative == 0, N.nan,self.dz[j])
                self.dz25[j] = N.where(cumulative == 0, N.nan,self.dz25[j])
                self.dz75[j] = N.where(cumulative == 0, N.nan,self.dz75[j])
                
                deriv = N.ediff1d(self.dz[j])#ediff1d
                #print lambobj.dz
                #print deriv
                
                for i,bn in enumerate(deriv):
                    if not N.isnan(bn):
                        if bn < slope and self.dz[j][i]<0.1: 
                            self.dz[j][i]=N.nan
                        else:break
                nanreplace = N.isnan(self.dz[j])
                #print 'self.dz',self.dz[j]
                #print 'i',i
                self.dz[j] = N.where(nanreplace, self.dz[j][i],self.dz[j])
                self.dz25[j] = N.where(nanreplace, self.dz25[j][i] - error,self.dz25[j])
                self.dz75[j] = N.where(nanreplace, self.dz75[j][i] + error,self.dz75[j])
                
    def remove_upper_extrap(self,remove_bottom=True,erase_mean=True,add_mask=True):
        
        if type(self.name)==list:
            for i in xrange(len(self.name)):
                cum = self.numdata[i].cumsum()
                
                if remove_bottom:
                    logic = N.logical_and(self.numdata[i]==0,N.logical_or(cum==cum[0],cum==cum[-1]))  
                else:
                    logic = N.logical_and(self.numdata[i]==0,cum==cum[-1])
                #print'****************'
                #print logic
                #print N.c_[logic,self.numdata[i]]
                #print'****************'    
                if erase_mean:self.dz[i] = N.ma.masked_array(self.dz[i],logic)
                self.dz25[i] = N.ma.masked_array(self.dz25[i],logic)
                self.dz75[i] = N.ma.masked_array(self.dz75[i],logic)

                self.mask=logic
        else:
            for i in xrange(len(self.name)):
                cum = self.numdata.cumsum()
                
                if remove_bottom:
                    logic = N.logical_and(self.numdata==0,N.logical_or(cum==cum[0],cum==cum[-1]))  
                else:
                    logic = N.logical_and(self.numdata==0,cum==cum[-1])
                #print'****************'
                #print logic
                #print N.c_[self.e,logic,self.numdata]
                #print'****************'    
                if erase_mean:self.dz = N.ma.masked_array(self.dz,logic)
                self.dz25 = N.ma.masked_array(self.dz25,logic)
                self.dz75 = N.ma.masked_array(self.dz75,logic)

                self.mask=logic

    def extend_upper_extrap(self):
        if not hasattr(self, 'kurtosis'):raise "ERROR: need to run calc_dz_stats method first."
        
        if not (self.dzs_n != 1).all():
            
            w = N.where(self.dzs_n ==1)[0]
            #if len(w) > 10: raise "ERROR: more than 10% of glaciers with only one glacier surveyed"
            
            top = [x for x in w if x >50]
            bottom = [x for x in w if x <=50]
            
            if len(top)>0: 
                repltop = N.min(N.array(top))-1   
                #print top, repltop
                #self.survIQRs2[top]=self.survIQRs2[repltop]
                self.quadsum[top]=self.quadsum[repltop]
                self.dzs_std[top]=self.dzs_std[repltop]
                self.dzs_sem[top]=self.dzs_sem[repltop]
                #self.dzs_mean[top]=self.dzs_mean[repltop]
                #self.dzs_madn[top]=self.dzs_madn[repltop]
                #self.dzs_median[top]=self.dzs_median[repltop]
                ##self.normalp[top]=self.normalp[repltop]
                #self.skewz[top]=self.skewz[repltop]
                #self.skewp[top]=self.skewp[repltop]
                #self.kurtz[top]=self.kurtz[repltop]
                #self.kurtp[top]=self.kurtp[repltop]
                #self.skew[top]=self.skew[repltop]
                #self.kurtosis[top]=self.kurtosis[repltop]
                #self.percentile_5[top]=self.percentile_5[repltop]
                #self.quartile_1[top]=self.quartile_1[repltop]
                #self.percentile_33[top]=self.percentile_33[repltop]
                #self.percentile_66[top]=self.percentile_66[repltop]  
                #self.quartile_3[top]=self.quartile_3[repltop]
                #self.percentile_95[top]=self.percentile_95[repltop]
                #self.interquartile_rng[top]=self.interquartile_rng[repltop]
                #
                    
            if len(bottom)>0:
                replbottom = N.max(N.array(bottom))+1
                #print replbottom
                #print self.quadsum
                #print bottom

                #self.survIQRs2[bottom]=self.survIQRs2[replbottom]
                self.quadsum[bottom]=self.quadsum[replbottom]
                self.dzs_std[bottom]=self.dzs_std[replbottom]
                self.dzs_sem[bottom]=self.dzs_sem[replbottom]
                #self.dzs_mean[bottom]=self.dzs_mean[replbottom]
                #self.dzs_madn[bottom]=self.dzs_madn[replbottom]
                #self.dzs_median[bottom]=self.dzs_median[replbottom]
                ##self.normalp[bottom]=self.normalp[replbottom]
                #self.skewz[bottom]=self.skewz[replbottom]
                #self.skewp[bottom]=self.skewp[replbottom]
                #self.kurtz[bottom]=self.kurtz[replbottom]
                #self.kurtp[bottom]=self.kurtp[replbottom]
                #self.skew[bottom]=self.skew[replbottom]
                #self.kurtosis[bottom]=self.kurtosis[replbottom]
                #self.percentile_5[bottom]=self.percentile_5[replbottom]
                #self.quartile_1[bottom]=self.quartile_1[replbottom]
                #self.percentile_33[bottom]=self.percentile_33[replbottom]
                #self.percentile_66[bottom]=self.percentile_66[replbottom]  
                #self.quartile_3[bottom]=self.quartile_3[replbottom]
                #self.percentile_95[bottom]=self.percentile_95[replbottom]
                #self.interquartile_rng[bottom]=self.interquartile_rng[replbottom]
            
            
            
        if not (self.dzs_n != 0).all():
            
            w = N.where(self.dzs_n ==0)[0]
            #if len(w) > 5: raise "ERROR: more than 5% of glaciers unsurveyed"
            
            top = [x for x in w if x >50]
            bottom = [x for x in w if x <=50]
            
            if len(top)>0: 
                repltop = N.min(N.array(top))-1   
                #print top, repltop
                #self.survIQRs2[top]=self.survIQRs2[repltop]
                self.quadsum[top]=self.quadsum[repltop]
                self.dzs_std[top]=self.dzs_std[repltop]
                self.dzs_sem[top]=self.dzs_sem[repltop]
                self.dzs_mean[top]=self.dzs_mean[repltop]
                self.dzs_madn[top]=self.dzs_madn[repltop]
                self.dzs_median[top]=self.dzs_median[repltop]
                #self.normalp[top]=self.normalp[repltop]
                self.skewz[top]=self.skewz[repltop]
                self.skewp[top]=self.skewp[repltop]
                self.kurtz[top]=self.kurtz[repltop]
                self.kurtp[top]=self.kurtp[repltop]
                self.skew[top]=self.skew[repltop]
                self.kurtosis[top]=self.kurtosis[repltop]
                self.percentile_5[top]=self.percentile_5[repltop]
                self.quartile_1[top]=self.quartile_1[repltop]
                self.percentile_33[top]=self.percentile_33[repltop]
                self.percentile_66[top]=self.percentile_66[repltop]  
                self.quartile_3[top]=self.quartile_3[repltop]
                self.percentile_95[top]=self.percentile_95[repltop]
                self.interquartile_rng[top]=self.interquartile_rng[repltop]
                
                    
            if len(bottom)>0:
                replbottom = N.max(N.array(bottom))+1

                #self.survIQRs2[bottom]=self.survIQRs2[replbottom]
                self.quadsum[bottom]=self.quadsum[replbottom]
                self.dzs_std[bottom]=self.dzs_std[replbottom]
                self.dzs_sem[bottom]=self.dzs_sem[replbottom]
                self.dzs_mean[bottom]=self.dzs_mean[replbottom]
                self.dzs_madn[bottom]=self.dzs_madn[replbottom]
                self.dzs_median[bottom]=self.dzs_median[replbottom]
                #self.normalp[bottom]=self.normalp[replbottom]
                self.skewz[bottom]=self.skewz[replbottom]
                self.skewp[bottom]=self.skewp[replbottom]
                self.kurtz[bottom]=self.kurtz[replbottom]
                self.kurtp[bottom]=self.kurtp[replbottom]
                self.skew[bottom]=self.skew[replbottom]
                self.kurtosis[bottom]=self.kurtosis[replbottom]
                self.percentile_5[bottom]=self.percentile_5[replbottom]
                self.quartile_1[bottom]=self.quartile_1[replbottom]
                self.percentile_33[bottom]=self.percentile_33[replbottom]
                self.percentile_66[bottom]=self.percentile_66[replbottom]  
                self.quartile_3[bottom]=self.quartile_3[replbottom]
                self.percentile_95[bottom]=self.percentile_95[replbottom]
                self.interquartile_rng[bottom]=self.interquartile_rng[replbottom]
                
def LambToColumn(data):

    out = {}
    for j,column in enumerate(data[0].keys()):out[column]=[]
        
    for i,row in enumerate(data):
        for j,column in enumerate(row.keys()):
            out[column].append(row[column])
    
    for j,column in enumerate(data[0].keys()):
        
        if type(out[column][-1]) == int and type(out[column][0]) == int or \
        type(out[column][-1]) == float and type(out[column][0]) == float:
            #print 'yes'
            try:
                out[column] = N.array(out[column][:])
            except:pass
    return out
