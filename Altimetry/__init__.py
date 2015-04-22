#Altimetry/__init__.py
__all__ = ['Altimetry','UpdateDb','GeoTools','timeout','lambpath',
    'xlfilepath','shpglobpath','psqlpath','shp2pgsqlpath','pgsql2shppath',
    'analysispath','continentalitypath','defaulthost','thor']

#from Altimetry import ConnectDb,kurtosistest_evan,skewtest_evan,GetSqlData2,GetLambData,convert085
#from Altimetry import normalize_elevation,calc_mb,calc_dz_stats,calc_residuals_zscores,get_approx_location
#from Altimetry import fix_terminus,remove_upper_extrap,extend_upper_extrap,LambToColumn,partition_dataset
#from Altimetry import coords_to_polykml,mad,extrapolate,glaciertype_to_gltype,full_plot_extrapolation_curves
#from Altimetry import create_extrapolation_table,remove_extrap_tables,destable,hard_return
#from UpdateDb import importXpt,importXptfiles

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
ice2oceanslocal = {"host":'localhost',"dbname":'spatial_database',"user":'postgres',"password":'postgres'}
ice2oceansremote = {"host":'ice2oceans.cloudapp.net',"dbname":'spatial_database',"user":'postgres',"password":'postgres'}