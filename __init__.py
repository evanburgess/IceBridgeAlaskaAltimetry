#Altimetry/__init__.py
__all__ = ['Interface','Analytics','UpdateDb','GeoTools','timeout','lambpath',
    'xlfilepath','shpglobpath','psqlpath','shp2pgsqlpath','pgsql2shppath',
    'analysispath','continentalitypath','defaulthost','thor']

lambpath = '/Users/igswahwsmcevan/Altimetry/lamb/*????*.????*.output.txt'
xlfilepath = '/Users/igswahwsmcevan/Altimetry/GlType_list3.xlsx'
shpglobpath = '/Users/igswahwsmcevan/Altimetry/shp/*extent.????.shp'
psqlpath = '/Applications/Postgres.app/Contents/Versions/9.3/bin/psql'
shp2pgsqlpath = '/Applications/Postgres.app/Contents/Versions/9.3/bin/shp2pgsql'
pgsql2shppath = '/Applications/Postgres.app/Contents/Versions/9.3/bin/pgsql2shp'
analysispath = '/Volumes/laser/analysis/'
continentalitypath = '/Users/igswahwsmcevan/Altimetry/data/coast_dist_albers_100.tif'

defaulthost = {"host":'localhost',"dbname":'altimetry',"user":'evan',"password":'evan'}
thor = {"host":'thor.gi.alaska.edu',"dbname":'spatial_database',"user":'postgres',"password":'postgres'}

