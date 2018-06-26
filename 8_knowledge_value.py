"""
NAME:    M98 valuation of recreation areas
         8 - Knowledge value

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\8_knowledge_value.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
arcpy.env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

v_skole = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\BASISDATA\BYM_skoler_og_barnehager_OB_2017.shp"

r_red_speciesCR = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredCR_OK_2018.shp"
r_red_speciesDD = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredDD_OK_2018.shp"
r_red_speciesEN = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredEN_OK_2018.shp"
r_red_speciesNT = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredNT_OK_2018.shp"
r_red_speciesRE = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredRE_OK_2018.shp"
r_red_speciesVU = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\SPECIES\Artsdatabanken\Rodliste\artsdatabanken_artskartredVU_OK_2018.shp"


# ##################### #
# DISTANCE FROM SCHOOLS #
# ##################### #

r_distance_from_schools = "distance_from_schools_OK_2m"
arcpy.gp.EucDistance_sa(v_skole, r_distance_from_schools, "", "2", "")

# minimum distance per area
t_summary_distance = "temp_summary_distance"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_distance_from_schools, t_summary_distance, "DATA", "MINIMUM")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_distance, "n8_distance_class", "Short")
expression = "reclass( !MIN! )"
codeblock = """def reclass(distance):
  if distance <= 100:
    return 3
  elif distance <= 1000:
    return 2 
  else:
    return 1 """
arcpy.CalculateField_management(t_summary_distance, "n8_distance_class", expression, "PYTHON_9.3", codeblock)


# ################ #
# SPECIES RICHNESS #
# ################ #

# merge all occurrence points
v_redlisted_merged = "temp_redlisted_merge"
arcpy.Merge_management([r_red_speciesCR, r_red_speciesDD, r_red_speciesEN, r_red_speciesNT, r_red_speciesRE, r_red_speciesVU], v_redlisted_merged)

# add field to store area of recreation area
AddFieldIfNotexists(v_m98_areas, "orig_area", "Double")
arcpy.CalculateField_management(v_m98_areas, "orig_area", "!Shape!.area", "PYTHON_9.3")

# intersect with recreation areas
v_redlisted_intersect = "temp_redlisted_intersect"
arcpy.Intersect_analysis([v_redlisted_merged, v_m98_areas], v_redlisted_intersect)
arcpy.Delete_management(v_redlisted_merged)

# summarize per recreation area JOIN_ID
t_summary_redlisted =  "temp_summary_redlisted"
arcpy.Statistics_analysis(v_redlisted_intersect, t_summary_redlisted, [["JOIN_ID","COUNT"],["orig_area","FIRST"]], "JOIN_ID") 
arcpy.Delete_management(v_redlisted_intersect)

# calculate density
AddFieldIfNotexists(t_summary_redlisted, "n8_redlist_density", "Double")
arcpy.CalculateField_management(t_summary_redlisted, "n8_redlist_density", "[COUNT_JOIN_ID]*1000000/[FIRST_orig_area]")

# compute density class - breaks computed manually based on quantiles
AddFieldIfNotexists(t_summary_redlisted, "n8_redlist_class", "Short")
expression = "scoring( !n8_redlist_density! )"
codeblock = """def scoring(attr):
        if attr < 1:
            return 1
        elif attr <= 50:
            return 2
        else:
            return 3"""
arcpy.CalculateField_management(t_summary_redlisted, "n8_redlist_class", expression, "PYTHON_9.3", codeblock)


# ####### #
# COMBINE #
# ####### #

# join to recreation areas
AddFieldIfNotexists(v_m98_areas, "n8_distance_class", "Short")
AddFieldIfNotexists(v_m98_areas, "n8_redlist_class", "Short")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_distance, "JOIN_ID", ["n8_distance_class"], ["n8_distance_class"])
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_redlisted, "JOIN_ID", ["n8_redlist_class"], ["n8_redlist_class"])

# replace nulls
codeblock = """def replaceNulls(attr):
  if attr is None:
    return 1
  else:
    return attr"""
arcpy.CalculateField_management(v_m98_areas, "n8_redlist_class", "replaceNulls(!n8_redlist_class!)", "PYTHON_9.3", codeblock)
arcpy.CalculateField_management(v_m98_areas, "n8_distance_class", "replaceNulls(!n8_distance_class!)", "PYTHON_9.3", codeblock)

# compute score
AddFieldIfNotexists(v_m98_areas, "n8_score", "Short")
codeblock = """def reclass(distance,richness):
  if distance == 1 and richness == 1:
    return 1
  elif distance == 2 and richness == 2:
    return 3
  elif distance == 3 and richness == 3:
    return 5
  elif distance + richness == 3:
    return 2 
  else:
    return 4"""
arcpy.CalculateField_management(v_m98_areas, "n8_score", "reclass(!n8_distance_class!, !n8_redlist_class!)", "PYTHON_9.3", codeblock)

arcpy.DeleteField_management(v_m98_areas, "n8_distance_class")
arcpy.DeleteField_management(v_m98_areas, "n8_redlist_class")
arcpy.DeleteField_management(v_m98_areas, "orig_area")



