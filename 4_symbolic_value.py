"""
NAME:    M98 valuation of recreation areas
         4 - Symbolic value

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

## workspace settings
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\4_symbolic_value.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")

## input data
# M98 areas
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

# study extent
v_ok = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

# place names
v_place_names = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Stedsnavn.shp"

# N50 streams and rivers
v_water_lines = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_water_lines_OAF_2017"
v_water_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_water_areas_OAF_2017"


## NAMES OF POINTS
# select appropriate names
l_points_names = arcpy.MakeFeatureLayer_management (v_place_names, "temp_layer_points")
expression = "NAVNTYPEDE IN ('Badeplass', 'Berg', 'Dam', 'Dal', 'Foss', 'Gammel bosettingsplass', 'Gard', 'Gravplass', 'Haug', 'Holme', 'Holme i sjø', 'Høyde', 'Søkk', 'Terrengdetalj', 'Tjern', 'Tjern i gruppe', 'Turisthytte', 'Jorde', 'Kai', 'Li', 'Mo', 'Myr', 'Nes', 'Nes i sjø', 'Os', 'Park', 'Pytt', 'Skar', 'Skog', 'Sund', 'Sund i sjø', 'Utmark', 'Vik', 'Vik i sjø', 'Ås', 'Øy', 'Øy i sjø')"
arcpy.SelectLayerByAttribute_management(l_points_names, "NEW_SELECTION", expression)

# intersect by recreation areas 
v_points_intersect = "temp_points_intersect"
arcpy.Intersect_analysis([l_points_names, v_m98_areas], v_points_intersect) 

# summarize per recreation area
t_points_summary =  "temp_points_summary"
arcpy.Statistics_analysis(v_points_intersect, t_points_summary, [["JOIN_ID","COUNT"]], "JOIN_ID") 


# NAMES OF STREAMS AND RIVERS
select appropriate names
l_rivers_names = arcpy.MakeFeatureLayer_management (v_place_names, "temp_layer_lines")
arcpy.SelectLayerByAttribute_management(l_rivers_names, "NEW_SELECTION", "NAVNTYPEDE IN ('Bekk', 'Elv')")
v_rivers_names = "BYM_names_rivers_corrected_OK"
arcpy.FeatureClassToFeatureClass_conversion(l_rivers_names, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\4_symbolic_value.gdb", v_rivers_names)

# select geometry of streams and rivers from N50 to replace point names
l_rivers_areas = arcpy.MakeFeatureLayer_management (v_water_areas, "temp_layer_n50")
arcpy.SelectLayerByAttribute_management(l_rivers_areas, "NEW_SELECTION", "objtype IN ('ElvBekk')")

# create buffer of 15 m of rivers
v_rivers_buffer_lines = "temp_rivers_lines_buffer"
v_rivers_buffer_areas = "temp_rivers_lines_areas"
arcpy.Buffer_analysis(v_water_lines, v_rivers_buffer_lines, "15")
arcpy.Buffer_analysis(l_rivers_areas, v_rivers_buffer_areas, "15")

v_rivers_merge = "temp_rivers_merge"
arcpy.Merge_management([v_rivers_buffer_lines, v_rivers_buffer_areas], v_rivers_merge)
arcpy.Delete_management(v_rivers_buffer_lines)
arcpy.Delete_management(v_rivers_buffer_areas)

# manually check if some name points (v_rivers_names) were not overlapped by buffer (v_rivers_merge)
# find reason and correct
# 184 name points, 49 does not intersect
# named moved to stream moved if close and clear taht it belongs (42 names moved)
# name removed if far from any river (7 names removed)

# manually check that one name is only in one river - check for multiple TARGET_FID
# if in many rivers - check which one is correct and move name (2 cases with three overlapping rivers)
arcpy.SpatialJoin_analysis(v_rivers_names, v_rivers_merge, out_feature_class="temp_test_one_name_in_more_rivers", join_operation="JOIN_ONE_TO_MANY", join_type="KEEP_COMMON")
arcpy.Delete_management("temp_test_one_name_in_more_rivers")

# join names to geometries of rivers and streams
# one stream might have two names - one (stream) to many (names)
v_rivers_join = "temp_rivers_join"
arcpy.SpatialJoin_analysis(v_rivers_merge, v_rivers_names, v_rivers_join, "JOIN_ONE_TO_MANY", "KEEP_COMMON")

# check for multiple TARGET_FID
 AddFieldIfNotexists(v_rivers_join, "duplicate", "Short")
 expression = "isDuplicate( !TARGET_FID! )"
 codeblock = """uniqueList = []
 def isDuplicate(inValue):
  if inValue in uniqueList:
    return 1
  else:
    uniqueList.append(inValue)
    return 0"""
arcpy.CalculateField_management(v_rivers_join, "duplicate", expression, "PYTHON_9.3", codeblock)

# if same name - delete one of them
# if different names - find out correct solution - e.g. split river, delete name
# compared to Toporaster WMS (N5)

# some rivers have name with space at the beginning
AddFieldIfNotexists(v_rivers_names, "STRENG2", "text")
expression = replaceSpace( !STRENG!)
codeblock = """def replaceSpace(name):
    if name[0] == ' ':
        return name[1:]
    else:
        return name"""
arcpy.CalculateField_management(v_rivers_names, "STRENG2", expression, "PYTHON_9.3", codeblock)
arcpy.CalculateField_management(v_rivers_names, "STRENG", "!STRENG2!", "PYTHON_9.3")

# manually check in v_rivers_join that same river names refer to same rivers
# if the same river -> ok
# if different river - rename to name1, name2

# dissolve geometries of rivers by river names
v_rivers_dissolve = "temp_rivers_dissolve"
arcpy.Dissolve_management(v_rivers_join, v_rivers_dissolve, ["STRENG"])
arcpy.Delete_management(v_rivers_join)

# intersect by recreation areas 
v_rivers_intersect = "temp_rivers_intersect"
arcpy.Intersect_analysis([v_rivers_dissolve, v_m98_areas], v_rivers_intersect) 

# dissolve 
v_dissolve = "temp_rivers_dissolve2"
arcpy.Dissolve_management(v_rivers_intersect, v_dissolve, ["JOIN_ID", "STRENG"])
arcpy.Delete_management(v_rivers_intersect)
arcpy.Rename_management(v_dissolve, v_rivers_intersect)

# summarize per recreation area
t_rivers_summary =  "temp_rivers_summary"
arcpy.Statistics_analysis(v_rivers_intersect, t_rivers_summary, [["JOIN_ID","COUNT"]], "JOIN_ID") 


# NAMES OF LAKES
# select appropriate names
l_lakes_names = arcpy.MakeFeatureLayer_management (v_place_names, "temp_layer_lakes")
arcpy.SelectLayerByAttribute_management(l_lakes_names, "NEW_SELECTION", "NAVNTYPEDE IN ('Vann')")

v_lakes_names = "BYM_names_lakes_corrected_OK"
arcpy.FeatureClassToFeatureClass_conversion(l_lakes_names, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\4_symbolic_value.gdb", v_lakes_names)

# select geometry of lakes from N50 to replace point names
l_lakes_areas = arcpy.MakeFeatureLayer_management (v_water_areas, "temp_layer_n50_lakes")
arcpy.SelectLayerByAttribute_management(l_lakes_areas, "NEW_SELECTION", "objtype IN ('Innsjø', 'InnsjøRegulert')")

v_lakes_areas = "temp_lakes_select"
arcpy.FeatureClassToFeatureClass_conversion(l_lakes_areas, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\4_symbolic_value.gdb", v_lakes_areas)

# manually check if some name points (v_lakes_names) were not overlapped by lakes (l_lakes_areas)
# find reason and correct
# 58 name points, 1 does not intersect -> moved

# join names to geometries of lakes
# one lake might have two names - one (lake) to many (names)
v_lakes_join = "temp_lakes_join"
arcpy.SpatialJoin_analysis(v_lakes_areas, v_lakes_names, v_lakes_join, "JOIN_ONE_TO_MANY", "KEEP_COMMON")

# check for multiple TARGET_FID
AddFieldIfNotexists(v_lakes_join, "duplicate", "Short")
expression = "isDuplicate( !TARGET_FID! )"
codeblock = """uniqueList = []
def isDuplicate(inValue):
 if inValue in uniqueList:
   return 1
 else:
   uniqueList.append(inValue)
   return 0"""
arcpy.CalculateField_management(v_lakes_join, "duplicate", expression, "PYTHON_9.3", codeblock)
# -> split lake (v_lakes_areas) in two
# -> remove duplicate names (v_lakes_names)

# manually check in v_lakes_join for duplicate lake names
# -> rename to name1, name2

# intersect by recreation areas 
v_lakes_intersect = "temp_lakes_intersect"
arcpy.Intersect_analysis([v_lakes_join, v_m98_areas], v_lakes_intersect) 

# dissolve 
v_dissolve = "temp_lakes_dissolve2"
arcpy.Dissolve_management(v_lakes_intersect, v_dissolve, ["JOIN_ID", "STRENG"])
arcpy.Delete_management(v_lakes_intersect)
arcpy.Rename_management(v_dissolve, v_lakes_intersect)

# summarize per recreation area
t_lakes_summary =  "temp_lakes_summary"
arcpy.Statistics_analysis(v_lakes_intersect, t_lakes_summary, [["JOIN_ID","COUNT"]], "JOIN_ID") 


# MERGE SUMMARY TABLES
# Merge summarization tables for points, rivers and lakes
t_merge = "temp_summary_merge"
arcpy.Merge_management([t_points_summary, t_rivers_summary, t_lakes_summary], t_merge)

# Summarize counts for each recreation area    
t_summary = "temp_summary_final"
arcpy.Statistics_analysis(t_merge, t_summary, [["COUNT_JOIN_ID","SUM"]], "JOIN_ID")
arcpy.Delete_management(t_merge)

# Compute count
AddFieldIfNotexists(v_m98_areas, "n4_count", "Double")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary, "JOIN_ID", ["SUM_COUNT_JOIN_ID"], ["n4_count"])
arcpy.Delete_management(t_summary)

# Compute density
AddFieldIfNotexists(v_m98_areas, "n4_density", "Double")
expression = "density(!n4_count!,!Shape_Area!)"
codeblock = """def density(count, area):
        if count is None:
            return None
        else:
            return count/(area/10000)"""
arcpy.CalculateField_management(v_m98_areas, "n4_density", expression, "PYTHON_9.3", codeblock)

# Compute scoring - quantiles of density (manually compute breaks - 4 classes)
AddFieldIfNotexists(v_m98_areas, "n4_score", "Double")
expression = "scoring( !n4_density! )"
codeblock = """def scoring(attr):
        if attr is None:
            return 1
        if attr <= 0.047039:
            return 2
        elif attr > 0.047039 and attr <= 0.079870:
            return 3
        elif attr > 0.079870 and attr <= 0.186673:
            return 4
        else:
            return 5"""
arcpy.CalculateField_management(v_m98_areas, "n4_score", expression, "PYTHON_9.3", codeblock)
arcpy.DeleteField_management(v_m98_areas,"n4_density")
arcpy.DeleteField_management(v_m98_areas,"n4_count")



