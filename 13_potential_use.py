"""
NAME:    M98 valuation of recreation areas
         13 - Potential use

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\13_potential_use.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
arcpy.env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833"

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"
v_population = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\DEMOGRAPHY\befolkning_grunnkretser_NO_2015.shp" # Bosatte


# Save original area in population
AddFieldIfNotexists(v_population, "orig_area", "Double")
arcpy.CalculateField_management(v_population, "orig_area", "!Shape!.area", "PYTHON_9.3")

# Compute set of bufferes of each area - 100, 250, 500, 1000 m
for buffer_distance in [100,250,500,1000]:
    arcpy.AddMessage("Computing buffer {}".format(buffer_distance))

    v_buffer = "temp_buffer_{}".format(buffer_distance)
    arcpy.Buffer_analysis(v_m98_areas, v_buffer, "{} Meters".format(buffer_distance))

    # intersect each buffer with census units
    v_intersect = "temp_intersect_{}".format(buffer_distance)
    arcpy.Intersect_analysis([v_buffer, v_population], v_intersect)
    
    # add field with recomputed population number (assuming uniform distribution)
    AddFieldIfNotexists(v_intersect, "estimate_pop_number", "Double")
    arcpy.CalculateField_management(v_intersect, "estimate_pop_number", "[Bosatte]*[Shape_Area]/[orig_area]")
    
    # summarize numbers per recreation areas
    t_summary = "temp_summary_{}".format(buffer_distance)
    arcpy.Statistics_analysis(v_intersect, t_summary, [["estimate_pop_number", "SUM"]], "JOIN_ID")

    # join to recreation areas
    f_pop = "n13_pop_{}".format(buffer_distance)
    AddFieldIfNotexists(v_m98_areas, f_pop, "Double")    
    join_and_copy(v_m98_areas, "JOIN_ID", t_summary, "JOIN_ID", ["SUM_estimate_pop_number"], [f_pop]) 

    
# Assign temporary score based on population in 1km influence zone
AddFieldIfNotexists(v_m98_areas, "n13_score", "Short")
codeblock = """def reclass(attr):
  if attr <= 5000:
    return 1
  elif attr <= 10000:
    return 2 
  elif attr <= 15000:
    return 3 
  elif attr <= 20000:
    return 4 
  else:
    return 5 """
arcpy.CalculateField_management(v_m98_areas, "n13_score", "reclass(!n13_pop_1000!)", "PYTHON_9.3", codeblock)






