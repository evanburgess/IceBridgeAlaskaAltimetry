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
from osgeo import osr

import ConfigParser
from glob import glob

cfg = ConfigParser.ConfigParser()
cfg.read(os.path.dirname(__file__)+'/setup.cfg')
sys.path.append(re.sub('[/][^/]+$','',os.path.dirname(__file__)))

from Altimetry import *


def UpdateAltimetryDb():

    conn,cur = ConnectDb()
    print 'Are you sure you want to update  glnames, gltype, region, lamb tables?  This invloves DELETING and rewritting the following tables: glnames, gltype, region, lamb.'
    contin = raw_input("Enter 'yes/no':")
    if not contin == 'yes': 
        print "Not updating glnames, gltype, region, lamb."
    else:

        cur.execute("DROP TABLE IF EXISTS glnames, gltype, region,lamb;")
    
        # Make the changes to the database persistent
        conn.commit()
        
        #print help(UpdateGlnamesRegions)
        UpdateGlnamesRegions() 
        #print help(UpdateGlacierType)
        UpdateGlacierType()
        #print help(RestartLambTable)   
        RestartLambTable()  
    
    print 'Do you want to reload the ergi?  This invloves DELETING and rewritting the the ergi table from a shapefile.'
    contin2 = raw_input("Enter 'yes/no':")
    if contin2 == 'yes':
        ergifile1= '/Volumes/ProjectData/GlacierData/EvanTransfer/eRGI40.shp'
        lakesfile1= '/Volumes/ProjectData/GlacierData/EvanTransfer/LakePoints.shp'
        tidesfile1= '/Volumes/ProjectData/GlacierData/EvanTransfer/TidewaterPoints.shp'
        namesfile1= '/Volumes/ProjectData/GlacierData/EvanTransfer/GlacierNamepoints.shp'
        tablename1='ergi'
        lakesname1 = 'lakepoints'
        tidesname1 = 'tidepoints'
        placename1 = 'namepoints'
        lakeswhere1=""
        tideswhere1=""
        placewhere1=" WHERE PRIMARY_GL IN (0,2)"
        
        ergifile = raw_input("Enter full pathname to rgi/ergi shapfile to import (Default %s):" % ergifile1)
        lakesfile = raw_input("Enter full pathname to lakepoints shapfile to import (Default %s):" % lakesfile1)
        tidesfile = raw_input("Enter full pathname to tidepoints shapfile to import (Default %s):" % tidesfile1)
        namesfile = raw_input("Enter full pathname to glaciernamepoints shapfile to import (Default %s):" % namesfile1)
        
        tablename = raw_input("What should the new rgi/ergi table be called (Default %s):" % tablename1)
        lakesname = raw_input("What should the new lakes table be called (Default %s):" % lakesname1)
        tidesname = raw_input("What should the new tidewater table be called (Default %s):" % tidesname1)
        placenames = raw_input("What should the new placnames table be called (Default %s):" % placename1)

        lakeswhere = raw_input("Want to select only a portion of the lakes points? \n If so add a WHERE statement here:")
        tideswhere = raw_input("Want to select only a portion of the tidewater points? \n If so add a WHERE statement here:")
        placewhere = raw_input("Is this the rgi or the ergi (for the altimetry db) (lower case)?:")
        if placewhere == 'ergi': placewhere = " WHERE PRIMARY_GL IN (0,3)"
        elif placewhere == 'rgi': placewhere = " WHERE PRIMARY_GL IN (0,2)"    
        else: raise "Error: please enter either 'rgi' or 'ergi'"    
                        
        if ergifile == '': ergifile = ergifile1
        if lakesfile == '': lakesfile = lakesfile1
        if tidesfile == '': tidesfile = tidesfile1
        if namesfile == '': namesfile = namesfile1
        
        if tablename == '': tablename = tablename1
        if lakesname == '': lakesname = lakesname1
        if tidesname == '': tidesname = tidesname1
        if placenames == '': placenames = placename1

        reload_rgi(ergifile,lakesfile,tidesfile,namesfile,tablename,lakesname=lakesname,tidesname=tidesname,placenames=placenames,lakeswhere=lakeswhere,tideswhere=tideswhere,placewhere=placewhere)

    else: 
        print "Update to ergi canceled."
    
    contin3 = raw_input("Update tidewater_fluxes'yes/no':")
    if contin3 == 'yes':
        fluxfile1='/Users/igswahwsmcevan/Altimetry/Fluxes_import.csv'
        fluxfile = raw_input("Enter full path to flux file: (default: %s:" % fluxfile1)
        if fluxfile == '': fluxfile = fluxfile1 
        update_fluxes(fluxfile)


    # Close communication with the database
    cur.close()
    conn.close()   
    
    print 'Do you want to reload the xptfiles?  This invloves DELETING and xpt table. This takes a long time!'
    contin2 = raw_input("Enter 'yes/no':")
    if not contin2 == 'yes':
        print "Update to xpts canceled."
    else:
        
        
        conn,cur = ConnectDb()
        cur.execute("DROP TABLE IF EXISTS xpts;") 
        cur.execute("CREATE TABLE xpts (gid serial PRIMARY KEY,lambid integer,z1 real,z2 real,dz real,geog geography(POINT,4326));")

        cur.execute("CREATE INDEX lambid_xpts ON xpts (lambid);") 
        conn.commit()
        cur.close()
        conn.close()
        xpts = glob.glob("/Users/igswahwsmcevan/Altimetry/xpd/*selected.xpt")
        #while xpts.pop(0) != '/Users/igswahwsmcevan/Altimetry/xpd/DoubleNorth.1996.136.2008.148.selected.xpt':
        #    continue
        
        
        strttime = time.time()
        st = False
        for k,xpt in enumerate(xpts):
            
            
            if not st:
                print "Currently running %s" % xpt 
                st=True
            else:print "Currently running %s. Last runtime: %s Total Runtime: %s percent done: %s" % (xpt,time2-time1, time2-strttime,float(k)/float(len(xpts))) 
                
            time1 = time.time()
            importXpt(xpt,verbose=False)
            time2 = time.time()
        
        #cur.execute("SELECT AddGeometryColumn('public','xpts','albersgeom',3338,'MULTIPOLYGON',2);")
    print 'Update succeeded'
   	
    
#############################################################################################
#############################################################################################
def UpdateGlnamesRegions(globpath = cfg.get('Section One', 'lambpath'),xlfile = cfg.get('Section One', 'xlfilepath')):
    """====================================================================================================
Altimetry.UpdateDb.UpdateGlnamesRegions
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Update the glnames and region table by searching through the glob path listed for lamboutput files 
    with the name format *output.txt. THE NAMES OF THE LAMB FILES ARE THE NAMES THAT GO IN THE
    GLNAMES TABLE.  THE GLNAMES TABLE IS NOT COPPIED DIRECTLY FROM  GlType_list2.xlsx. The reason for this 
    is to not include glnames that we still dont have data for.  The region value is obtained by
    matching the lamb name in the GlType_list2.xlsx file. Only one entry per glacier is listed here.
    SO IF YOU CHANGE THE LAMB TABLE RUN UpdateGlnamesRegions BEFORE RUNNING RestartLambTable!!
    
Returns: Nothing

UpdateGlnamesRegions(globpath = lambpath from setup.cfg,xlfile=xlfilepath from setup.cfg) 

KEYWORD ARGUMENTS:
    globpath            The full pathname used to search for lamb output files eg.
                        /home/laser/analysis/*/results*.output.txt
    xlfile              The pathname to the excel file of glacier info and names etc.
====================================================================================================        
        """     
    conn,cur = ConnectDb()
    
    cur.execute("CREATE TABLE glnamestemp (gid serial PRIMARY KEY,name varchar,range varchar,region varchar,refpoint geometry(Point,4326));")
    #cur.execute("CREATE TABLE region (gid serial PRIMARY KEY, rgname varchar, lrg_regn varchar);")

    #A UNIQUE LIST OF GLACIER NAMES FROM THE LIST OF LAMB OUTPUT FILES
    lambs = glob.glob(globpath)
    lambs = [os.path.basename(x) for x in lambs]
    glnames = []
    for (i,lamb) in enumerate(lambs): glnames.append(re.findall('^([^\.]+)\.',lamb)[0])
    gls = list(set(glnames))
    
    #OPEN EXCEL FILE AND READ DATA FROM SHEET ALL
    wb = xlrd.open_workbook(xlfile)
    sh = wb.sheet_by_name(u'GlType_list.csv')
    
    header = N.array(sh.row_values(0))
    
    wrange=N.where(header == 'Mountain Range')[0]
    wregion=N.where(header == 'Region')[0]
    wglacier=N.where(header == 'Glacier')[0]
    wlon=N.where(header == 'Lon')[0]
    wlat=N.where(header == 'Lat')[0]
 
    #WRITING GLACIER NAMES TABLE
    rnge = []
    glref = []
    glregion = []
    lon = []
    lat = []
    
    values = {}
    labels = {}
    strings = {}
    templabels = ['range', 'region','refpoint','refpoint']
    keys = ['range', 'region','lon','lat']
    tempstrings = ["'%(range)s'","'%(region)s'","ST_GeomFromText('POINT(%(lon)s %(lat)s)',4326)","ST_GeomFromText('POINT(%(lon)s %(lat)s)',4326)"]
    
    #LOOPING THROUGH EACH ROW IN THE TABLE MAKING DICTIONARIES OF INFORMATION FOR INSERT STATEMENT  DICS ARE USED BECAUSE SOME CATEGORIES ARE MISSING
    for k in xrange(1,sh.nrows):
        
        if isinstance(sh.row_values(k)[wrange], unicode) and isinstance(sh.row_values(k)[wglacier], unicode):
            glaciername = unicodedata.normalize('NFKD', sh.row_values(k)[wglacier]).encode('ascii','ignore')
            mtnrange = unicodedata.normalize('NFKD', sh.row_values(k)[wrange]).encode('ascii','ignore')
            region = unicodedata.normalize('NFKD', sh.row_values(k)[wregion]).encode('ascii','ignore')

            temp = [mtnrange,region,sh.row_values(k)[wlon],sh.row_values(k)[wlat]]
            
            values[glaciername]={}
            labels[glaciername]=[]
            strings[glaciername]=[]
            for i,x in enumerate(temp):
                if x != '':
                    values[glaciername][keys[i]]=x
                    labels[glaciername].append(templabels[i])
                    strings[glaciername].append(tempstrings[i])
            if temp[2]!='':
                labels[glaciername] = labels[glaciername][0:3]
                strings[glaciername] = strings[glaciername][0:3]

    #INSERTING INTO GLNAMES TABLE
    for (i,gl) in enumerate(gls):
        if gl in values:
            st = "INSERT INTO glnamestemp (name,%s) VALUES ('%s', %s);" % (",".join(labels[gl]),gl,",".join(strings[gl]))
            cur.execute(st % (values[gl]))
    cur.execute("SELECT glnamestemp.*,ergi.glimsid into glnames from glnamestemp left join ergi on ST_Contains(ergi.geog::geometry,glnamestemp.refpoint);")
    cur.execute("DROP TABLE glnamestemp;")
    ## Make the changes to the database persistent
    #raise
    conn.commit()
    #
    ### Close communication with the database
    cur.close()
    conn.close()

##############################################################################################
##WRITING GLACIER TYPES TABLE
##############################################################################################
def UpdateGlacierType(xlfile = cfg.get('Section One', 'xlfilepath')):
    """====================================================================================================
Altimetry.UpdateDb.UpdateGlacierType
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Update the glacier type table using values from the GlType_list3.xlsx file found at this path: Altimetry.xlfilepath.  
    PLEASE DO NOT CHANGE THE COLUMN ARRANGMENT IN THIS TABLE WITHOUT TELLING EVAN. BUT FEEL FREE TO UPDATE VALUES
    OR ADD ROWS (glaciers) AS YOU SEE NECESSARY. Executing this will update the database to fit that table.  Names of 
    glaciers must correspond to the lamb file naming convention as they are used to connect to the lamb files.  Boolean 
    values must be entered into the excel file as a capital N or Y.      
    
Returns: Nothing

UpdateGlacierType(xlfile)  

KEYWORD ARGUMENTS:
    xlfile            The full pathname to the excel file. Default:  Altimetry.xlfilepath
====================================================================================================        
        """ 
    print 'Reinstalling gltype table from ',xlfile
    #CONNECT TO DATABASE
    conn,cur = ConnectDb()
    cur.execute("CREATE TABLE gltype (gid serial PRIMARY KEY, glid smallint, glimsid varchar(16), date date, surge bool, tidewater bool, lake bool, river bool, omit bool);")
    
    #OPEN EXCEL FILE AND READ DATA FROM SHEET ALL
    wb = xlrd.open_workbook(xlfile)
    sh = wb.sheet_by_name(u'GlType_list.csv')
    
    header = sh.row_values(0)
    
    #TABLE CONVERSION COLUMN NAMES
    name = {'Surges':'surge','Tidewater':u'tidewater','Lake':'lake','River':'river',
            'Mountain Range':'region','Glacier':'name','Date':'date','glimsid':'glimsid','Omit':'omit'}
    booleancols = ['Surges','Tidewater','Lake','River','Omit'] 
    
    #LOOPING THROUGH EACH ROW IN THE TABLE
    for k in xrange(1,sh.nrows):
    
        data  = sh.row_values(k)
        
        #CONVERTING DATA OUT OF UNICODE AND PLACING INTO DICTIONARY
        row = {}
        for (i, columnname) in enumerate(header):
            headerhold = unicodedata.normalize('NFKD', header[i]).encode('ascii','ignore')
            if isinstance(data[i], unicode): data[i] = unicodedata.normalize('NFKD', data[i]).encode('ascii','ignore')
            row[headerhold] = data[i]
            
        ##FILTERING OUT ALL BUT YS AND NS
        insert = '' 
        values = ''   
        for (i, key) in enumerate(row.keys()):
            for (j, cols) in enumerate(booleancols):
                if row[cols] == 42:         #EXCEL LEAVES A '42' FOR THE #N/A SYMBOL
                    row[cols] = ''
                else:
                    if not (re.search('^N$', row[cols]) or re.search('^Y$', row[cols])): row[cols] = ''
        
        #MAKING DATES
        try:
            row['Date'] = dtm.datetime(*xlrd.xldate_as_tuple(row['Date'], wb.datemode))
        except:
            row['Date'] = 'NULL'        
        #IDENTIFYING GLIDS
        cur.execute("SELECT gid FROM glnames WHERE name = '"+row['Glacier']+"'")
        row['Glid']  = cur.fetchall()
        if row['Glid'] == []:
            row['Glid'] = 'NULL'
        else: row['Glid'] = row['Glid'][0]
        
    
        #ADDING THE NECESSARY COLUMNS TO THE INSERT STATEMENT
        name = {'Surges':'surge','Tidewater':u'tidewater','Lake':'lake','River':'river',
                'Mountain Range':'region','Glacier':'name','Date':'date','Glid':'glid','glimsid':'glimsid','Omit':'omit'}
        keys = ['Glid','Date','Surges','Tidewater','Lake','River','glimsid','Omit']
        insert = '' 
        values = '' 
        row2 = {}
        for (i,key) in enumerate(keys):
            if row[key] != 'NULL' and row[key] != '':
                insert = insert + ', ' + name[key]
                values = values + '%(' + key + ')s, '
                        
                row2[key]=row[key] 
    
        insert = re.sub('^, ', '', insert)
        values = re.sub(', $', '', values)
            

        #INSERTING DATA INTO GLACIERS TABLE
        sql = "INSERT INTO gltype ("+insert+") VALUES (" + values + ");" # Note: no quotes
        if not insert == '': print sql, row2.keys(),'\n_________________\n'
        if not insert == '': cur.execute(sql, row2)
    
    add_type_column = "ALTER TABLE gltype ADD COLUMN glaciertype varchar(20);"
    add_type = """with new_values as
    (select gid,case 
	WHEN tidewater='f' AND lake='f' AND surge = 'f' THEN 'land' 
	WHEN tidewater='f' AND lake='t' AND surge = 'f' THEN 'lake' 
	WHEN tidewater='t' AND lake='f' AND surge = 'f' THEN 'tidewater' 
	WHEN tidewater='f' AND lake='f' AND surge = 't' THEN 'surgeland' 
	WHEN tidewater='f' AND lake='t' AND surge = 't' THEN 'surgelake' 
	WHEN tidewater='t' AND lake='f' AND surge = 't' THEN 'surgetidewater'
	ELSE 'NULL'
	END 
	from gltype)
	update gltype set glaciertype = new_values.case from new_values WHERE new_values.gid=gltype.gid;"""
	
    cur.execute(add_type_column)
    cur.execute(add_type)
    # Make the changes to the database persistent
    conn.commit()
    
    # Close communication with the database
    cur.close()
    conn.close()

##############################################################################################
##READ LAMB FILE
##############################################################################################
def ReadLambFile(lambfile,as_dict = None,as_string = None):

    f = open(lambfile)
    
    f.readline()#header trashed
    
    #reading glacierwide data on line 1
    (year1,jday1,year2,jday2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff) = [float(field) for field in f.readline().split()]
    
    #converting to datetime objects
    date1 = dtm.datetime(int(year1), 1, 1) + dtm.timedelta(int(jday1) - 1)
    date2 = dtm.datetime(int(year2), 1, 1) + dtm.timedelta(int(jday2) - 1)
    
    #vertically binned data - READING
    e=N.array([])
    dz=N.array([])
    dz25=N.array([])
    dz75=N.array([])
    aad=N.array([])
    masschange=N.array([])
    massbal=N.array([])
    numdata=N.array([])
    f.readline()  #second header trashed
    for line in f:
        (e_add,dz_add,dz25_add,dz75_add,aad_add,masschange_add,massbal_add,numdata_add) = [float(field) for field in line.split()]
        e = N.append(e,e_add)
        dz = N.append(dz,dz_add)
        dz25 = N.append(dz25,dz25_add)
        dz75 = N.append(dz75,dz75_add)
        aad = N.append(aad,aad_add)
        masschange = N.append(masschange,masschange_add)
        massbal = N.append(massbal,massbal_add)
        numdata = N.append(numdata,numdata_add)
    
    #print "***************\n%s" % e
        
    e = e.astype(int)
    e += (e[2]-e[1])/2    # DEALING WITH THE FACT THAT LAMB BINNING LABLES THE BOTTOM OF THE BIN AND WE WANT THE CENTER
    
    #print e
    numdata = numdata.astype(int)   
    
    #GETTING GLACIER NAME FROM FILENAME
    name = re.findall('(^[^\.]+)\.',os.path.basename(lambfile))[0]
    
    if as_string == 1:
        date1 = str(date1)
        date2 = str(date2)
        volmodel = str(volmodel)
        vol25diff = str(vol25diff)
        vol75diff = str(vol75diff)
        balmodel = str(balmodel)
        bal25diff = str(bal25diff)
        bal75diff = str(bal75diff)
        e = e.astype(str)
        dz = dz.astype(str)
        dz25 = dz25.astype(str)
        dz75 = dz75.astype(str)
        aad = aad.astype(str)
        masschange = masschange.astype(str)
        massbal = massbal.astype(str)
        numdata = numdata.astype(str) 
        
    if as_dict == 1:
        dic={} 
        dic['date1'] = date1
        dic['date2'] = date2
        dic['volmodel'] = volmodel
        dic['vol25diff'] = vol25diff
        dic['vol75diff'] = vol75diff
        dic['balmodel'] = balmodel
        dic['bal25diff'] = bal25diff
        dic['bal75diff'] = bal75diff
        dic['e'] = e
        dic['dz'] = dz
        dic['dz25'] = dz25
        dic['dz75'] = dz75
        dic['aad'] = aad
        dic['masschange'] = masschange
        dic['massbal'] = massbal
        dic['numdata'] = numdata
        dic['name'] = name 
        return dic
    else:
        out = LambOut(name,date1,date2,volmodel,vol25diff,vol75diff,balmodel,bal25diff,bal75diff,e,dz,dz25,dz75,aad,masschange,massbal,numdata)
        return out

##############################################################################################
##IMPORT LAMB FILE TO DATABASE
##############################################################################################
def import_lamb_file_to_db(lambfile,db):
    #READING LAMBFILE INTO DICTIONARY    
    data = ReadLambFile(lambfile, as_string = 1, as_dict = 1)
    
    #OPENING DATABASE 
    if isinstance(db,psycopg2._psycopg.cursor):cur=db
    else:conn,cur = ConnectDb()
    
    try:
        #print 'SELECT gid FROM glnames WHERE name = %s' % data['name']
        #print str(GetSqlData2("SELECT gid FROM glnames WHERE name = '%s'" % data['name'])['gid'][0])
        data['glid'] = str(GetSqlData2("SELECT gid FROM glnames WHERE name = '%s'" % data['name'])['gid'][0])
    except:
        print "%s not used because not in glnames." % lambfile
        return

    del data['name']
    
    
    data['date1'] = datetime.fromtimestamp(mktime(time.strptime(data['date1'],"%Y-%m-%d %H:%M:%S")))
    data['date2'] = datetime.fromtimestamp(mktime(time.strptime(data['date2'],"%Y-%m-%d %H:%M:%S")))
    data['interval'] = (data['date2'] - data['date1']).days
    data['date1'] = re.sub('T.*$','',data['date1'].isoformat())
    data['date2'] = re.sub('T.*$','',data['date2'].isoformat())
    
    #STRINGS FOR INSERT SQL STATEMENT
    insert = ''
    values = ''
    ss = ''          
    
    #LOOPING THROUGH EACH FIELD OF DATA AND ADDING TO THE INSERT AND VALUE STRINGS
    for (i,key) in enumerate(data.keys()):
            insert = insert + ', ' + key
            ss = ss+ '%s, '
            
            if type(data[key]) == N.ndarray:
                s = str(data[key])
                s = re.sub('\[\'','{',s)
                s = re.sub('\'\]','}',s)
                s = re.sub("'\n? \n?'",", ",s)
                s = re.sub("\n","",s)
                values = values + ', ' + s
            elif type(data[key]) == str:
                #s = re.sub(" 00:00:00","'",data[key])
                #print data[key]
                if re.search('\d{4}\-\d{2}\-\d{2}',data[key]): data[key] = "'"+data[key]+"'" 
                values = values + ', ' + data[key]
            else:values = values + ', ' + str(data[key])
            
                
    #STRING FORMATTING FOR SQL
    insert = re.sub('^, ', '', insert)
    values = re.sub('^, ', '', values)
    values = re.sub('\{', "'{", values)
    values = re.sub('\}', "}'", values)
    ss = re.sub(', $', '', ss)
    #print '----------------'                
    #print insert
    #print values
    #print ss
    
    sql = "INSERT INTO lamb ("+insert+") VALUES (" + values + ");" # Note: no quotes
    cur.execute(sql)
    
    # Make the changes to the database persistent
    conn.commit()
    
    # Close communication with the database only if db name is given
    if not isinstance(db,psycopg2._psycopg.cursor):
        cur.close()
        conn.close()
        
##############################################################################################
##restart_lamb_table
##############################################################################################
def RestartLambTable(globpath = cfg.get('Section One', 'lambpath')): 
    """====================================================================================================
Altimetry.UpdateDb.RestartLambTable
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    Update the lamb table by searching through the glob path listed for files with the name format *output.txt.  
    All of these files are read into the table. The name is used to match a gid in the existing glnames table. 
    SO IF YOU CHANGE THE GLNAMES TABLE RUN UpdateGlnamesRegions BEFORE RUNNING THIS!!
    
Returns: Nothing

RestartLambTable(globpath = Altimetry.lambpath) 

KEYWORD ARGUMENTS:
    globpath            The full pathname used to search for lamb output files eg.  
                        /home/laser/analysis/*/results*.output.txt
====================================================================================================        
        """ 
    lambfiles = glob.glob(globpath)
    db='altimetry'
    conn,cur = ConnectDb()    
    cur.execute("DROP TABLE IF EXISTS lamb")
    cur.execute("CREATE TABLE lamb (gid serial PRIMARY KEY, glid smallint, date1 date, date2 date, interval smallint, volmodel real, vol25diff real,vol75diff real, balmodel real, bal25diff real,bal75diff real,e integer[],dz real[],dz25 real[],dz75 real[],aad real[],masschange real[],massbal real[],numdata integer[]);")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print 'Importing lamb output files:'
    for (i,lambfile) in enumerate(lambfiles):
        print lambfile
        import_lamb_file_to_db(lambfile,db)

        
##############################################################################################
##glshp_into_gloutline
##############################################################################################
def glshp_into_gloutline(shpfile,dbname = cfg.get('Section One', 'dbname')):

    conn,cur = ConnectDb()
    
    
    
    glname = re.findall('^([^\.]+)\.',os.path.basename(shpfile))[0]
    
    #RETRIEVING GLACIER NAME
    cur.execute("SELECT gid FROM glnames WHERE name = '"+glname+"'")
    try:
        glid = str(cur.fetchall()[0][0])
    except IndexError:
        return None    
    #RETRIEVING DATASET MONTH
    try:
        year = int(re.findall('(\d{4})\.\w{3}$',os.path.basename(shpfile))[0])
        date = dtm.datetime(year,1,1).isoformat()
    except IndexError:
        date = '\N'
    
    
    #RETRIEIVING SQL STATEMENT TO GO INTO DATABASE
    sqlfile = re.sub('\.shp','.sql',shpfile)
    os.system(Altimetry.shp2pgsqlpath+" -c -D -G -i -I -t 2D "+shpfile+" public.gloutline > "+sqlfile)
    f = open(sqlfile)
    
    use = []
    for line in f:
        if re.search('^(SET|BEGIN|COPY|COMMIT|\\\.|.{600})',line):
            if re.search('^COPY',line):line = re.sub('\(.*\)','("glid","date",geog)',line)
            if re.search('.{600}',line):
                line = re.findall('\t([^\t]+)$',line)[0]
                line = glid +"\t"+date+"\t"+line
            use.append(line)
                    
    f = open(sqlfile, 'w')
    for (i,line) in enumerate(use):f.write(line) 
    f.close()
    print sqlfile
    print 'psql -d ' + dbname + ' -U evan -f '+sqlfile
    os.system(Altimetry.psqlpath+' -d ' + dbname + ' -U evan -f '+sqlfile)
    #os.remove(sqlfile) 


def prj2srid(shape_path):
   prj_file = open("%s.prj" % os.path.splitext(shape_path)[0], 'r')
   prj_txt = prj_file.read()
   srs = osr.SpatialReference()
   srs.ImportFromESRI([prj_txt])
   #print 'Shape prj is: %s' % prj_txt
   #print 'WKT is: %s' % srs.ExportToWkt()
   #print 'Proj4 is: %s' % srs.ExportToProj4()
   srs.AutoIdentifyEPSG()
   if srs.GetAuthorityCode(None) != None: return srs.GetAuthorityCode(None)
   else:
       if re.search('alaska.?albers',prj_txt,re.IGNORECASE) :return '3338'


def get_both_geom_columns(tablename):
    conn,cur = ConnectDb()
    
    #FINDING IF ALBERSGEOM OR GEOG COLUMNS EXIST AND ARE OF A POSTGIS DATATYPE (NOT IMPORTED AS A VARCHAR)
    cur.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_name='%s' and column_name='geog' AND data_type='USER-DEFINED';" % tablename)
    geogused= cur.fetchall()

    cur.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_name='%s' and column_name='albersgeom' AND data_type='USER-DEFINED';" % tablename)
    albersused= cur.fetchall()
    
    if len(geogused) == 1:
    
        print "Adding a albersgeometry column to %s" % tablename
        tpe = GetSqlData2("SELECT GeometryType(geog) as type from %s limit 1;" % tablename)['type'][0]

        cur.execute("ALTER TABLE %s DROP COLUMN IF EXISTS albersgeom;" % tablename)
        cur.execute("SELECT AddGeometryColumn ('public','%s','albersgeom',3338,'%s',2);" % (tablename,tpe))
        cur.execute("UPDATE %s SET albersgeom=ST_Transform(geog::geometry, 3338);" % tablename)
        cur.execute("CREATE INDEX %s_albersgeom ON %s USING GIST(albersgeom);" % (tablename,tablename))
        conn.commit()
    elif len(albersused) == 1:
        print "Adding a geography column to %s" % tablename
        tpe = GetSqlData2("SELECT GeometryType(albersgeom) as type from %s limit 1;" % tablename)['type'][0]
        cur.execute("ALTER TABLE %s DROP COLUMN IF EXISTS geog;" % tablename)
        cur.execute("SELECT AddGeometryColumn ('public','%s','geog',4326,'%s',2);" % (tablename,tpe))
        cur.execute("UPDATE %s SET geog=ST_Transform(albersgeom::geometry, 4326);" % tablename)
        cur.execute("CREATE INDEX %s_geog ON %s USING GIST(geog);" % (tablename,tablename))
        conn.commit()
    conn.close()
    cur.close()
    
def import_shp2db(shp,tablename):
    dbname = cfg.get('Section One', 'dbname')
    host = cfg.get('Section One', 'host')
    user = cfg.get('Section One', 'user')
    passwd = cfg.get('Section One', 'passwd')
    psqlpath=cfg.get('Section One', 'psqlpath')
    shp2pgsqlpath=cfg.get('Section One', 'shp2pgsqlpath')
    
    
    conn,cur = ConnectDb()
    cur.execute("DROP TABLE IF EXISTS %s;" % tablename) 
    conn.commit()
    conn.close()
    cur.close()
    
    srid = prj2srid(shp)
    if srid=='3338':
        geomname='albersgeom'
        asgeog=''
    elif srid=='4326':
        geomname='geog'
        asgeog='-G'    
    os.system("%s -d -D -i %s -I -t 2D -g %s -s %s %s public.%s > %s.tmp" % (shp2pgsqlpath,asgeog,geomname,srid,shp,tablename,os.path.splitext(shp)[0]))
    #print "%s -c -D -G -i -I -t 2D %s public.%s > %s.txt" % (shp2pgsqlpath,ergifile,tablename,os.path.splitext(ergifile)[0])
    
    #GETTING RID OF ODD USE OF \N AS NULL VALUE
    f=open("%s.tmp" % (os.path.splitext(shp)[0]),'r')
    w=open("%s2.tmp" % (os.path.splitext(shp)[0]),'w')
    for i in f:w.write( re.sub('\\\N','NULL',i))
    os.remove("%s.tmp" % (os.path.splitext(shp)[0]))
    w.close()
    
    #BRINGING INTO POSTGIS
    os.system("%s -h %s -d %s -U %s -w %s -f %s" % (psqlpath,host,dbname,user,passwd,"%s2.tmp" % (os.path.splitext(shp)[0])))
    os.remove("%s2.tmp" % (os.path.splitext(shp)[0]))    
    get_both_geom_columns(tablename)

def reload_rgi(rgifile,lakesfile,tidesfile,namesfile,tablename,lakesname='lakepoints',tidesname='tidepoints',placenames='placenames',lakeswhere="",tideswhere="",placewhere=""):

    dbname = cfg.get('Section One', 'dbname')
    host = cfg.get('Section One', 'host')
    user = cfg.get('Section One', 'user')
    passwd = cfg.get('Section One', 'passwd')
    psqlpath=cfg.get('Section One', 'psqlpath')
    shp2pgsqlpath=cfg.get('Section One', 'shp2pgsqlpath')
    
    import_shp2db(rgifile,tablename)
    import_shp2db(lakesfile,lakesname)
    import_shp2db(tidesfile,tidesname)
    import_shp2db(namesfile,placenames)

    
    conn,cur=ConnectDb()
    cur.execute("UPDATE %s as e SET glactype=overlay(glactype placing '0' from 2 for 1);" % tablename)
    cur.execute("UPDATE %s as e SET glactype=overlay(e.glactype placing (l.gid*0+2)::varchar from 2 for 1) FROM %s as l WHERE ST_Contains(e.albersgeom,l.albersgeom);" % (tablename,lakesname))
    cur.execute("UPDATE %s as e SET glactype=overlay(e.glactype placing (l.gid*0+1)::varchar from 2 for 1) FROM %s as l WHERE ST_Contains(e.albersgeom,l.albersgeom);" % (tablename,tidesname))
    cur.execute("ALTER TABLE %s ALTER COLUMN name TYPE varchar(45);" % tablename)
    cur.execute("UPDATE %s SET name=l.name FROM (SELECT * FROM %s %s) as l WHERE ST_Contains(%s.albersgeom,l.albersgeom);" % (tablename,placenames,placewhere,tablename))
    conn.commit() 
    
    print "Adding gltype"
    cur.execute("ALTER TABLE %s ADD COLUMN gltype int;" % tablename)
    cur.execute("UPDATE %s as e SET gltype=substring(glactype from 2 for 1)::int;" % (tablename))

    print "Adding region"
    cur.execute("ALTER TABLE %s ADD COLUMN region varchar(50);" % tablename)
    cur.execute("UPDATE %s as e SET region=a.region FROM burgessregions as a WHERE ST_Contains(a.albersgeom,e.albersgeom);" % tablename)
    conn.commit()
    conn.close()
    cur.close()  
        
    print 'Updating continentality'
    sys.stdout.flush()
    UpdateGeomWithGrid(insertfield = 'continentality',image = cfg.get('Section One', 'continentalitypath'), geometry_table = tablename)

    
        
  
    
def reload_gloutlines():

    shpfiles = glob.glob(Altimetry.shpglobpath)

    conn,cur = ConnectDb()
    cur.execute('DROP TABLE IF EXISTS gloutline;')
    cur.execute('CREATE TABLE gloutline (gid serial PRIMARY KEY,glid integer,date date,area real,minelev real,maxelev real,meanelev real,meanorient real,continentality real,geog geography(MULTIPOLYGON,4326));')
    conn.commit()
    cur.close()
    conn.close()
    #cur.execute("SELECT AddGColumn('public'::varchar,'gloutline'::varchar,'geom'::varchar,'4326','MULTIPOLYGON');")
    for (i,shpfile) in enumerate(shpfiles):
        print i,shpfile
        glshp_into_gloutline(shpfile)
        
def update_fluxes(fluxfile):
    if fluxfile==None:fluxfile=='/Users/igswahwsmcevan/Altimetry/Fluxes_import.csv'

    data = recfromcsv(fluxfile, delimiter=',')
    print data
    name,glimsid,eb_high_flx,eb_best_flx,eb_low_flx,bm_length,bm_flux,bm_flx_err,eb_bm_flx,eb_bm_err = zip(*data)
    
    #print 'here'
    
    conn,cur=ConnectDb()
    cur.execute("DROP TABLE IF EXISTS tidewater_flux;")
    cur.execute("CREATE TABLE tidewater_flux (gid serial PRIMARY KEY,name varchar(45),glimsid varchar(14),eb_high_flx real,eb_best_flx real,eb_low_flx real,bm_length real,bm_flux real,bm_flx_err real,eb_bm_flx real,eb_bm_err real);")
    
    #print 'asdf'
    
    for i in xrange(len(data)):
        if name[i]!='':
            #print i
            strin = "INSERT INTO tidewater_flux (name,glimsid,eb_high_flx,eb_best_flx,eb_low_flx,bm_length,bm_flux,bm_flx_err,eb_bm_flx,eb_bm_err) VALUES ('%s','%s',%s,%s,%s,%s,%s,%s,%s,%s);" % (name[i],glimsid[i],eb_high_flx[i],eb_best_flx[i],eb_low_flx[i],bm_length[i],bm_flux[i],bm_flx_err[i],eb_bm_flx[i],eb_bm_err[i])
            print strin
            strin = re.sub('nan','NULL',strin)
            cur.execute(strin)
    conn.commit()
    conn.close()
    cur.close()    
        
def UpdateGeomWithGrid(insertfield = None,image = None,stat = 'mean',geometry_table = 'ergi',addto = "", overwrite=False):
    """====================================================================================================
Altimetry.UpdateDb.UpdateGeomWithGrid
Evan Burgess 2013-08-22
====================================================================================================
Purpose:
    This script will take a table with a multipolygon geometry column and a geocoded image/grid and create 
    a new field (or update and existing field) in the geomtry table and assign values corresponding to either
    the mean,median,min,max, or stddev of the image pixels within each geometry.  Nunataks in polygons
    are supported.  Having a dataset with resolution finer than 300 m is reccommended as small glaciers
    that fill only portion of pixels return no value. BOTH THE GEOMETRY AND THE GRID MUST BE IN THE SAME
    PROJECTION! (if not, the locations will be off and the routine does NOT throw an error!) (all our
    stuff should be in AK albers anyway)
    
Returns: Nothing

UpdateGeomWithGrid(insertfield = None,image = None,stat = 'mean',geometry_table = 'ergi',addto = "",overwrite=False) 

    
KEYWORD ARGUMENTS:
    
insertfield         The name of the field as a string that should recieve the new gridded value.  
                    If the field already exists values will be written over if user agrees to prompt. 
                    Prompt can be bypassed by setting overwrite to True.
                            
image               The full pathname to a geocoded grid readable by GDAL.  GeoTIFFs are supported.
                    Other formats may work but are not yet tested.  If the geocoding of the image
                    is bad. No error will be thrown and the output values will be wrong because 
                    they are coming from the wrong location.
                    
stat                The statistic to calculate for all pixels within each polygon. 'mean','median',
                    'min','max', or 'stddev' are supported. 
                    
geometry_table      The name of the geometry table to be updated
addto               This allows you to only update specific rows in the geometry table by filtering
                    with the where portion of an sql statement.  This string is simply tagged onto the
                    end of the sql statement so a space is needed and a 'where'.  Fore example, to
                    only update glaciers with an area larger than 2km: addto=' WHERE area > 2'
                    
overwrite           Bypass user prompt to confirm overwrite of column
==================================================================================================== 
"""  
    print "start"
    sys.stdout.flush()     
    #geometry_table = 'ergi'
    #insertfield = 'mn_elev'
    ##raster = 'dist_coast'
    #image =  '/Users/igswahwsmcevan/Altimetry/dems/AK_DEM_albers_.tif'
    #stat = 'mean'
    #addto = " WHERE gid > 89 AND gid < 92";
            
    conn,cur = ConnectDb()
    #print "SELECT "+insertfield+" FROM "+geometry_table+";"
    #TESTING TO SEE IF THIS COLUMN EXISTS IN THIS TABLE IF SO DO NOTHING IF NOT ADD THAT COLUMN
    try: 
        #print 'try'
        GetSqlData("SELECT "+insertfield+" FROM "+geometry_table+";")
        #print "SELECT "+insertfield+" FROM "+geometry_table+";"
        contin = raw_input("Are you sure you want to update field "+insertfield+"? Enter yes/no:")
        if not contin == 'yes' or overwrite: 
            print "Update Canceled."
            return
    except:
        cur.execute("ALTER TABLE "+geometry_table+" ADD COLUMN " + insertfield + " real;")
        conn.commit()
        print "Column "+insertfield+" added to table "+geometry_table
    
    #RETRIEVING A LIST OF ALL GEOMETRIES
    print "select gid from "+geometry_table+addto+";"
    gids = GetSqlData("select gid from "+geometry_table+addto+";",bycolumn=1)['gid']

    
    #OPENING GRID
    dataset = gdal.Open(image)
    band = dataset.GetRasterBand(1).ReadAsArray()
    geotransform = dataset.GetGeoTransform()
    
    start_time = time.time()
    for (i,gid) in enumerate(gids):
        #if i > 40: break
        #if gid != 13827: continue
        #temp = GetSqlData("select glnames.name,gloutline.gid from gloutline inner \
            #join glnames on glnames.id=gloutline.glid where gloutline.gid= "+str(gid))[0]['glnames.name']
    
        #print 'area', GetSqlData("SELECT ST_area(albersgeom::geometry) as area FROM "+geometry_table+" WHERE gid = "+str(gid)+";")[0]['area']
        #try:
            #img = ClipRasterBySingleGeom(raster, "SELECT albersgeom::geometry FROM "+geometry_table+" WHERE gid = "+str(gid))
            #print "SELECT ST_AsText(albersgeom::geometry) FROM "+geometry_table+" WHERE gid = "+str(gid)+";"
        #print "SELECT albersgeom FROM "+geometry_table+" WHERE gid = "+str(gid)+";"
        
        img = PyClipRasterBySingleGeom("SELECT albersgeom FROM "+geometry_table+" WHERE gid = "+str(gid)+";",band=band,geotransform=geotransform)
        #except:
            #print "ERROR No clipped array was created failed for gid "+str(gid)
            #continue
        #print '_______________________________'
        #print img    
        #print i, gid,'timeleft','mean', N.ma.mean(img)     #"ClipRasterBySingleGeom("+raster+", 'SELECT albersgeom::geometry FROM "+geometry_table+" WHERE gid = "+str(gid)+"')"
        if i % 100 == 0:
            print float(i)/len(gids)
            sys.stdout.flush()
        #val = N.ma.min(img)
        #print type(val), str(val) 
        #print "UPDATE "+geometry_table+" SET "+insertfield+" = %s WHERE gid = %s", [val,gids[i]]

        #if img.size > 10:
        #    if stat == 'mean': val = N.ma.mean(img)
        #    elif stat == 'median': val = N.ma.median(img)
        #    elif stat == 'sum': val = N.ma.sum(img)
        #    elif stat == 'min': val = N.ma.min(img)
        #    elif stat == 'max': val = N.ma.max(img)
        #    elif stat == 'std': val = N.ma.std(img)
        #    print val, val == '--',type(val),img.size,(N.ma.getmask(img) == False).any()
        #    if val == '--': val = 'NULL'
        #    try:
        #        #print "UPDATE "+geometry_table+" SET "+insertfield+" = "+str(val)+" WHERE gid = "+str(gids[i])+" ;"
        #        cur.execute("UPDATE "+geometry_table+" SET "+insertfield+" = "+str(val)+" WHERE gid = "+str(gids[i])+";")#, [val, gids[i]])
        #        conn.commit()
        #    except Exception, e:
        #        #if e.pgerror != None: 
        #        print e.pgerror
            
        if (N.ma.getmask(img) == False).any():
            if stat == 'mean': val = N.ma.mean(img)
            elif stat == 'sum': val = N.ma.sum(img)
            elif stat == 'median': val = N.ma.median(img)
            elif stat == 'min': val = N.ma.min(img)
            elif stat == 'max': val = N.ma.max(img)
            elif stat == 'std': val = N.ma.std(img)
            #print val, val == '--',type(val),img.size,(N.ma.getmask(img) == False).any()
            if val == '--': val = 'NULL'
            cur.execute("UPDATE "+geometry_table+" SET "+insertfield+" = "+str(val)+" WHERE gid = "+str(gids[i])+";")
            conn.commit()
        else:
            print '--------------------------------'
            print 'Skipped gid because glacier is too small', gid
            print 'image shape',img.shape

def importXptfiles(filelist):
    for fle in filelist:importXpt(fle)

def importXpt(xptfile):
    def doy_to_datetime(doy,year):return dtm.date(year, 1, 1) + dtm.timedelta(doy - 1)
    
    #FINDING DATES OF FILE AND GLACIER NAME
    
    try:
        name,yr1,doy1,yr2,doy2 = re.findall('(\w+)\.(\d{4})\.(\d{3})\.(\d{4})\.(\d{3})\.selected',os.path.basename(xptfile))[0]
    except:
        raise "Could not understand filename, this is supposed to read a file with a name like: Allen.2000.238.2010.236.selected.xpt"
    date1 = doy_to_datetime(int(doy1),int(yr1))
    date2 = doy_to_datetime(int(doy2),int(yr2))
    
    #RETRIEVING ERGIID
    try:
        ergiid = GetSqlData2("SELECT ergiid FROM lamb_ergi_lookup WHERE name='{name}'".format(name=name))['ergiid'][0]
        lambid = GetSqlData2("SELECT lambid FROM lamb2 WHERE ergiid = {ergiid} AND date1= '{date1}' AND date2='{date2}'".format(ergiid=ergiid,date1=date1,date2=date2))['lambid'][0]
    except:
        print "ERROR failed to find an entry in lamb for this xpt file %s" % xptfile
        return
    
    zone = GetSqlData2("SELECT utmZone FROM lamb_ergi_lookup WHERE name='{name}'".format(name=name))['utmzone'][0]
    
    #READING TEXT FILE
    try:
        x,y,z1,z2,dz = N.loadtxt(xptfile,usecols=[0,1,2,3,4],unpack=True)
    except:
        raise "ERROR: Could not find or load file %s" % xptfile
            
    #REPROJECTING LOCATION OF CROSSING POINTS 
        #REFERENCE SYSTEM OF GRID
    old_cs = osr.SpatialReference()
    old_cs.ImportFromProj4('+proj=utm +zone=%i +ellps=WGS84 +datum=WGS84 +units=m +no_defs' % zone)
    
    ##WGS84 REFERNCE SYSTEM 
    #albers_wkt = """PROJCS["NAD83 / Alaska Albers",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]],UNIT["metre",1,AUTHORITY["EPSG","9001"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",55],PARAMETER["standard_parallel_2",65],PARAMETER["latitude_of_center",50],PARAMETER["longitude_of_center",-154],PARAMETER["false_easting",0],PARAMETER["false_northing",0],AUTHORITY["EPSG","3338"],AXIS["X",EAST],AXIS["Y",NORTH]]"""
    #albers = osr.SpatialReference()
    #albers.ImportFromWkt(albers_wkt)
    
    #ALBERS REFERNCE SYSTEM 
    albers_cs = osr.SpatialReference()
    albers_cs.ImportFromProj4("""+proj=aea +lat_1=55 +lat_2=65 +lat_0=50 +lon_0=-154 +x_0=0 +y_0=0 +ellps=GRS80 +datum=WGS84 +units=m +no_defs """)
    
    #PROJECTING COORDINATE TO ALASKA ALBERS 
    transformtoalbers = osr.CoordinateTransformation(old_cs, albers_cs)
    coordsalb=[]
    
    for i in xrange(len(x)):
        xy = transformtoalbers.TransformPoint(x[i],y[i])
        coordsalb.append(ppygis.Point(xy[0],xy[1],srid=3338).write_ewkb())
    
    #WRITTING THE INFO TO A BUFFER FOR IMPORT INTO DB
    buffer = StringIO.StringIO()
    for z1t,z2t,dzt,c in zip(z1,z2,dz,coordsalb):buffer.write("{z1t}\t{z2t}\t{dzt}\t{c}\t{lambid}\n".format(z1t=z1t,z2t=z2t,dzt=dzt,c=c,lambid=lambid))
    buffer.seek(0)
    
    alreadydone = GetSqlData2("SELECT COUNT(xptid) AS c FROM xpts2 WHERE lambid={lambid};".format(lambid=lambid))['c'][0]
    
    if alreadydone != 0: print "This file has already been loaded."
    
    conn,cur = ConnectDb()
    cur.copy_from(buffer, 'xpts2', columns=('z1', 'z2','dz','albersgeom','lambid'))
    conn.commit()
    buffer=None
    cur.close()
                
