# -*- coding: utf-8 -*-
import numpy as N
import matplotlib.pyplot as plt
import pickle
from Altimetry.Altimetry import *

colors = N.array([[209,150,111],[163,100,57],[128,162,232],[45,80,150],[138,212,102],[75,150,38]])/255.  

#PLOTTING LAND FIGURE
land = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="ergi_mat_view.gltype=0 AND ergi_mat_view.surge='f'") 
land.convert085()
land.fix_terminus()
land.remove_upper_extrap(remove_bottom=False)
land.normalize_elevation()
land.calc_dz_stats(too_few=4)
land.extend_upper_extrap()
fig = full_plot_extrapolation_curves(land,color=colors[0])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS6_land_stats1.jpg",dpi=300)
fig=None


#PLOTTING TIDEWATER FIGURE
tide = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="ergi_mat_view.gltype=1 AND ergi_mat_view.name!='Columbia Glacier'",results=True) 
tide.convert085()
tide.fix_terminus()
tide.remove_upper_extrap(remove_bottom=False)
tide.normalize_elevation()
tide.calc_dz_stats(too_few=4)
tide.extend_upper_extrap()
fig = full_plot_extrapolation_curves(tide,color=colors[2])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS7_tide_stats1.jpg",dpi=300)
fig=None

#PLOTTING LAKE TERMINATING FIGURE
lake = GetLambData(verbose=False,longest_interval=True,interval_max=30,interval_min=5,by_column=True,as_object=True, userwhere="ergi_mat_view.gltype=2 AND ergi_mat_view.name!='East Yakutat Glacier' AND ergi_mat_view.name!='West Yakutat Glacier' AND ergi_mat_view.surge='f'") 
lake.convert085()
lake.fix_terminus()
lake.remove_upper_extrap(remove_bottom=False)
lake.normalize_elevation()
lake.calc_dz_stats(too_few=4)
lake.extend_upper_extrap()
fig = full_plot_extrapolation_curves(lake,color=colors[4])
fig.savefig("/Users/igswahwsmcevan/Papers/AK_altimetry/Figures/FigS8_lake_stats1.jpg",dpi=300)
fig=None
plt.show()

plt.plot(lake.normdz)