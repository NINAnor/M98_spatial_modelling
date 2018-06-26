"""
NAME:    M98 valuation of recreation areas
         9 - Noise environment

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\9_noise_environment.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
arcpy.env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833"

# input data
r_noise = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833"
v_paths = "temp_n50_pedestrian_selection_OK"
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"


# ##################### #
# AVERAGE NOISE IN AREA #
# ##################### #
t_summary_noise = "temp_summary_noise"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_noise, t_summary_noise, "DATA", "MEAN")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_noise, "n9_noise_class", "Short")
expression = "reclass( !MEAN! )"
codeblock = """def reclass(noise):
  if noise > 60:
    return 1
  elif noise > 50:
    return 3 
  else:
    return 4 """
arcpy.CalculateField_management(t_summary_noise, "n9_noise_class", expression, "PYTHON_9.3", codeblock)


# ################### #
# DISTANCE FROM PATHS #
# ################### #
r_distance_from_paths = "distance_from_paths_OK_2m"
arcpy.gp.EucDistance_sa(v_paths, r_distance_from_paths, "", "2", "")

# mean distance per area
t_summary_distance = "temp_summary_distance"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_distance_from_paths, t_summary_distance, "DATA", "MEAN")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_distance, "n9_distance_class", "Short")
expression = "reclass( !MEAN! )"
codeblock = """def reclass(distance):
  if distance <= 180:
    return 4
  else:
    return 5 """
arcpy.CalculateField_management(t_summary_distance, "n9_distance_class", expression, "PYTHON_9.3", codeblock)

# ####### #
# COMBINE #
# ####### #
AddFieldIfNotexists(v_m98_areas, "n9_distance_class", "Short")
AddFieldIfNotexists(v_m98_areas, "n9_noise_class", "Short")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_distance, "JOIN_ID", ["n9_distance_class"], ["n9_distance_class"])
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_noise, "JOIN_ID", ["n9_noise_class"], ["n9_noise_class"])

AddFieldIfNotexists(v_m98_areas, "n9_score", "Short")
expression = "reclass( !n9_distance_class!, !n9_noise_class! )"
codeblock = """def reclass(distance,noise):
  if noise < 4:
    return noise
  else:
    return distance"""
arcpy.CalculateField_management(v_m98_areas, "n9_score", expression, "PYTHON_9.3", codeblock)






