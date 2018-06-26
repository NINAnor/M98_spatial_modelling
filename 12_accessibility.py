"""
NAME:    M98 valuation of recreation areas
         12 - Accessibility

AUTHOR(S): Zofie Cimburova < zofie.cimburova AT nina.no>
"""

"""
To Dos:
"""

import arcpy
import time
import math  

from arcpy import env
from arcpy.sa import *

from helpful_functions import *
  
env.overwriteOutput = True

# workspace settings
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\12_accessibility.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
arcpy.env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833"

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"
v_borders = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\built_marka_fjord_boundary_OK.shp"
v_parking_stops = "parkings_stops_OK"
v_residential_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SSB\landuse.gdb\ssb_landuse_OAF_2017"
v_paths_n50 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_transport_lines_OAF_2017"
v_paths_bym_sykkel = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_sykkelruter_marka_OK_2015.shp"
v_paths_bym_tursti = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_tursti_kommuneskogen_OK_2015.shp"
v_paths_bym_ski = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_skiloyper_preparert_bym_OK_2015.shp"


# ############################################################### #
# DISTINGUISH BETWEEN M98 AREAS IN BUILTUP AREAS, MARKA AND FJORD #
# ############################################################### #
# add temporary field to store original area
AddFieldIfNotexists(v_m98_areas, "temp_orig_area", "Double")
arcpy.CalculateField_management(v_m98_areas, "temp_orig_area", "[Shape_Area]")

# intersect M98 areas with zone
v_m98_areas_intersect = "temp_m98_areas_intersect"
arcpy.Intersect_analysis([v_m98_areas, v_borders], v_m98_areas_intersect)

# dissolve by zone and JOIN_ID
v_m98_areas_dissolve = "temp_m98_areas_dissolve"
arcpy.Dissolve_management(v_m98_areas_intersect, v_m98_areas_dissolve, ["JOIN_ID", "zone"], [["temp_orig_area","FIRST"]])
arcpy.Delete_management(v_m98_areas_dissolve)
arcpy.DeleteField_management(v_m98_areas, "temp_orig_area")

# compute proportion of area to original area
AddFieldIfNotexists(v_m98_areas_dissolve, "area_proportion", "Double")
arcpy.CalculateField_management(v_m98_areas_dissolve, "area_proportion", "[Shape_Area]/[FIRST_temp_orig_area]")

# assuming that each area is located in either one or two zones, select the larger proportions
l_m98_areas_dissolve = arcpy.MakeFeatureLayer_management (v_m98_areas_dissolve, "temp_layer2")
arcpy.SelectLayerByAttribute_management(l_m98_areas_dissolve, "NEW_SELECTION", "area_proportion >= 0.5")

t_summary_zone = "temp_summary_zone"
arcpy.Statistics_analysis(l_m98_areas_dissolve, t_summary_zone, [["zone","FIRST"]], "JOIN_ID")  
arcpy.Delete_management(v_m98_areas_dissolve)

# join to M98 areas
AddFieldIfNotexists(v_m98_areas, "zone", "Text")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_zone, "JOIN_ID", ["FIRST_zone"], ["zone"]) 
arcpy.Delete_management(t_summary_zone)

# ##################################################### #
# DISTANCE FROM PARKING LOTS AND PUBLIC TRANSPORT STOPS #
# ##################################################### #
r_distance_parking_stops = "temp_distance_parking_stops"
arcpy.gp.EucDistance_sa(v_parking_stops, r_distance_parking_stops, "", "2", "")

# store the minimum distance to parking or stop
t_summary_parking_stops = "temp_summary_parking_stops"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_distance_parking_stops, t_summary_parking_stops, "DATA", "MINIMUM")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_parking_stops, "n12_parking_class", "Short")
expression = "reclass( !MIN! )"
codeblock = """def reclass(distance):
  if distance > 500:
    return 1
  elif distance > 250:
    return 2 
  else:
    return 3 """
arcpy.CalculateField_management(t_summary_parking_stops, "n12_parking_class", expression, "PYTHON_9.3", codeblock)


# ############################### #
# DISTANCE FROM RESIDENTIAL AREAS #
# ############################### #
l_residential_areas = arcpy.MakeFeatureLayer_management (v_residential_areas, "temp_layer")
arcpy.SelectLayerByAttribute_management(l_residential_areas, "NEW_SELECTION", "SsbAreal_1 = 'Boligbebyggelse'")

r_distance_residential = "temp_distance_residential"
arcpy.gp.EucDistance_sa(l_residential_areas, r_distance_residential, "", "2", "")

# store the minimum distance to parking or stop
t_summary_residential = "temp_summary_residential"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_distance_residential, t_summary_residential, "DATA", "MINIMUM")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_residential, "n12_residential_class", "Short")
expression = "reclass( !MIN! )"
codeblock = """def reclass(distance):
  if distance > 500:
    return 1
  elif distance > 250:
    return 2 
  else:
    return 3 """
arcpy.CalculateField_management(t_summary_residential, "n12_residential_class", expression, "PYTHON_9.3", codeblock)


# ############ #
# PATH DENSITY #
# ############ #
# select paths
l_paths_n50 = arcpy.MakeFeatureLayer_management (v_paths_n50, "temp_layer3")
arcpy.SelectLayerByAttribute_management(l_paths_n50, "NEW_SELECTION", "objtype = 'Sti' AND merking = 'JA'")

l_paths_bym_tursti = arcpy.MakeFeatureLayer_management (v_paths_bym_tursti, "temp_layer4")
arcpy.SelectLayerByAttribute_management(l_paths_bym_tursti, "NEW_SELECTION", "Type IN( 'Kulturlandskapssti' , 'Kulturminnesti' , 'Natursti' )")

# merge paths
v_paths_merge = "temp_paths_merge"
arcpy.Merge_management([v_paths_bym_ski, l_paths_n50, v_paths_bym_sykkel, l_paths_bym_tursti], v_paths_merge)

# path density in 100 m
r_path_density = "temp_path_density_100_2m"
arcpy.gp.LineDensity_sa(v_paths_merge, "NONE", r_path_density, "2", "100", "SQUARE_KILOMETERS")

# store the mean density of paths [km/km2]
t_summary_path_density = "temp_summary_path_density"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_path_density, t_summary_path_density, "DATA", "MEAN")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_path_density, "n12_path_density_class", "Short")
expression = "reclass( !MEAN! )"
codeblock = """def reclass(density):
  if density > 8.5: 
    return 3
  elif density > 3.5:
    return 2 
  else:
    return 1 """
arcpy.CalculateField_management(t_summary_path_density, "n12_path_density_class", expression, "PYTHON_9.3", codeblock)


# ############################### #
# PATH LENGTH PER AREA (not used) #
# ############################### #
# intersect with areas
v_paths_intersect = "temp_paths_intersect"
arcpy.Intersect_analysis([v_m98_areas, v_paths_merge], v_paths_intersect)

t_summary_path_length = "temp_summary_path_length"
arcpy.Statistics_analysis(v_paths_intersect, t_summary_path_length, [["Shape_Length","SUM"]], "JOIN_ID")  



# ####### #
# COMBINE #
# ####### #
AddFieldIfNotexists(v_m98_areas, "n12_parking_class", "Short")
AddFieldIfNotexists(v_m98_areas, "n12_residential_class", "Short")
AddFieldIfNotexists(v_m98_areas, "n12_path_density_class", "Short")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_parking_stops, "JOIN_ID", ["n12_parking_class"], ["n12_parking_class"])
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_residential, "JOIN_ID", ["n12_residential_class"], ["n12_residential_class"])
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_path_density, "JOIN_ID", ["n12_path_density_class"], ["n12_path_density_class"])

AddFieldIfNotexists(v_m98_areas, "n12_score", "Short")
expression = "reclass( !zone!, !n12_parking_class!, !n12_residential_class!, !n12_path_density_class! )"
codeblock = """def reclass(zone, parking, residential, path):
  if zone == 'byggesonen':
    if residential==1 and parking==1:
      return 1
    elif residential==2 and parking==2:
      return 3
    elif residential==3 and parking==3:
      return 5
    elif residential+parking==3:
      return 2
    else:
      return 4
  else:
    if path==1 and parking==1:
      return 1
    elif path==2 and parking==2:
      return 3
    elif path==3 and parking==3:
      return 5
    elif path+parking==3:
      return 2
    else:
      return 4 """
arcpy.CalculateField_management(v_m98_areas, "n12_score", expression, "PYTHON_9.3", codeblock)

arcpy.DeleteField_management("n12_parking_class")
arcpy.DeleteField_management("n12_residential_class")
arcpy.DeleteField_management("n12_path_density_class")
arcpy.DeleteField_management("zone")







