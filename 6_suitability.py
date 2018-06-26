"""
NAME:    M98 valuation of recreation areas
         6 - Suitability

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\6_suitability.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")

## input data
# M98 areas
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

# study extent
v_ok = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

# BYM points
v_bym_points = [r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Akebakke.shp", r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Fiske_krepsevann.shp", r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Badeplass.shp", r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Klatrefelt.shp", r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Isbane.shp", r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Roklubb.shp"]

# BYM lines
v_bym_lines = "Sykkelruter_marka"
v_bym_lines_path = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata"

# OSM lines
v_osm_lines = "osm_roads_free_1_OK"
v_bym_lines_path = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK"


## POINTS
# 1. merge data
v_points_merge = "temp_points_merge"
arcpy.Merge_management(v_bym_points, v_points_merge, field_mappings='Type "Type" true true false 80 Text 0 0 ,First,#,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Akebakke.shp,Type,-1,-1,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Badeplass.shp,Type,-1,-1,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Fiske_krepsevann.shp,Type,-1,-1,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Klatrefelt.shp,Type,-1,-1,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Isbane.shp,Type,-1,-1,R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM_temadata\Roklubb.shp,Type,-1,-1')

# 2. intersect data
v_points_intersect = "temp_points_intersect"
arcpy.Intersect_analysis([v_points_merge, v_m98_areas], v_points_intersect)
arcpy.Delete_management(v_points_merge)

# 3. correct types
AddFieldIfNotexists(v_points_intersect, "Type_corr", "text")
expression = "rcl( !Type! )"
codeblock = """def rcl(attr):
    if attr=="HC-tilrettelagt badeplass":
        return "Badeplass"
    elif attr=="HC-tilrettelagt fiskevann":
        return "Fiskevann"
    else:
        return attr"""
arcpy.CalculateField_management(v_points_intersect, "Type_corr", expression, "PYTHON_9.3", codeblock)

# 4. dissolve by type and recreational area
v_points_dissolve = "temp_points_dissolve"
arcpy.Dissolve_management(v_points_intersect, v_points_dissolve, ["JOIN_ID", "Type_corr"])
arcpy.Delete_management(v_points_intersect)

#5. go through points,
#   make a buffer, find if there are features of same type within buffer
env.workspace = r"in_memory"
AddFieldIfNotexists(v_points_dissolve, "Unique_in_1km", "Short")
l_points_intersect = arcpy.MakeFeatureLayer_management (v_points_dissolve, "temp_layer")
        
cursor = arcpy.da.UpdateCursor(v_points_dissolve, ["SHAPE@", "Type_corr", "Unique_in_1km"])
for row in cursor:
    geom = row[0]
    type = row[1]
   
    # Create buffer
    v_point_buffer = "temp_point_buffer"
    arcpy.Buffer_analysis(geom, v_point_buffer, "1000")
    
    # Select features with the same type which fall in buffer
    arcpy.SelectLayerByAttribute_management(l_points_intersect, "NEW_SELECTION", "Type_corr='{}'".format(type))
    arcpy.SelectLayerByLocation_management(l_points_intersect, "INTERSECT", v_point_buffer, "", "SUBSET_SELECTION")
    arcpy.SelectLayerByLocation_management(l_points_intersect, "ARE_IDENTICAL_TO", geom, "", "REMOVE_FROM_SELECTION")
    
    same_activity_count = int(arcpy.GetCount_management(l_points_intersect).getOutput(0)) 
    if same_activity_count == 0:
        row[2] = 1
    else:
        row[2] = 0
    cursor.updateRow(row)
    arcpy.Delete_management(v_point_buffer)

# 6. summarize by recreational area
t_points_summary =  "temp_points_summary"
arcpy.Statistics_analysis(v_points_dissolve, t_points_summary, [["JOIN_ID","COUNT"], ["Unique_in_1km", "SUM"]], "JOIN_ID")   

    
## LINES
# 1. merge data
l_lines_osm = arcpy.MakeFeatureLayer_management (v_osm_lines, "temp_layer")
arcpy.SelectLayerByAttribute_management(l_lines_osm, "NEW_SELECTION", "fclass='bridleway'")

v_lines_merge = "temp_lines_merge"
arcpy.Merge_management([l_lines_osm, v_bym_lines], v_lines_merge) 

# 2. correct types
AddFieldIfNotexists(v_lines_merge, "Type_corr", "text")
expression = "rcl( !fclass!, !LTEMA! )"
codeblock = """def rcl(attr1, attr2):
    if attr1=="bridleway":
        return "Riding"
    elif attr2==7427:
        return "Biking"
    else:
        return "Error" """
arcpy.CalculateField_management(v_lines_merge, "Type_corr", expression, "PYTHON_9.3", codeblock)    
    
# 3. intersect data
v_lines_intersect = "temp_lines_intersect"
arcpy.Intersect_analysis([v_lines_merge, v_m98_areas], v_lines_intersect)
arcpy.Delete_management(v_lines_merge)  

# 4. dissolve by type and recreational area
v_lines_dissolve = "temp_lines_dissolve"
arcpy.Dissolve_management(v_lines_intersect, v_lines_dissolve, ["JOIN_ID", "Type_corr"])
arcpy.Delete_management(v_lines_intersect)

# 5. go through lines,
#    make a buffer, find if there are features of same type within buffer
env.workspace = r"in_memory"
AddFieldIfNotexists(v_lines_dissolve, "Unique_in_1km", "Short")
l_lines_intersect = arcpy.MakeFeatureLayer_management (v_lines_dissolve, "temp_layer")
   
cursor = arcpy.da.UpdateCursor(v_lines_dissolve, ["SHAPE@", "Type_corr", "Unique_in_1km", "Shape_Length"])
for row in cursor:
    geom = row[0]
    type = row[1]
    length = row[3]
    
    # If too short, delete
    if length < 100:
       cursor.deleteRow()
   
    # Create buffer
    v_line_buffer = "temp_line_buffer"
    arcpy.Buffer_analysis(geom, v_line_buffer, "1000")
    
    # Select features with the same type which fall in buffer
    arcpy.SelectLayerByAttribute_management(l_lines_intersect, "NEW_SELECTION", "Type_corr='{}'".format(type))
    arcpy.SelectLayerByLocation_management(l_lines_intersect, "INTERSECT", v_line_buffer, "", "SUBSET_SELECTION")
    arcpy.SelectLayerByLocation_management(l_lines_intersect, "ARE_IDENTICAL_TO", geom, "", "REMOVE_FROM_SELECTION")
    
    same_activity_count = int(arcpy.GetCount_management(l_lines_intersect).getOutput(0)) 
    if same_activity_count == 0:
        row[2] = 1
    else:
        row[2] = 0
    cursor.updateRow(row)
    arcpy.Delete_management(v_line_buffer)


# 6. summarize by recreational area
t_lines_summary = "temp_lines_summary"
arcpy.Statistics_analysis(v_lines_dissolve, t_lines_summary, [["JOIN_ID","COUNT"], ["Unique_in_1km", "SUM"]], "JOIN_ID")   
    

## Merge summary tables for points and lines
t_merge = "temp_summary_merge"
arcpy.Merge_management([t_points_summary, t_lines_summary], t_merge)
arcpy.Delete_management(t_points_summary)
arcpy.Delete_management(t_lines_summary)   
   
## Summarize counts for each recreation area    
t_summary = "temp_summary_final"
 arcpy.Statistics_analysis(t_merge, t_summary, [["COUNT_JOIN_ID","SUM"], ["SUM_Unique_in_1km", "SUM"]], "JOIN_ID")
 arcpy.Delete_management(t_merge)

## Compute scoring
AddFieldIfNotexists(v_m98_areas, "n6_count_unique", "Double")
AddFieldIfNotexists(v_m98_areas, "n6_count", "Double")
AddFieldIfNotexists(v_m98_areas, "n6_score", "Double")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary, "JOIN_ID", ["SUM_COUNT_JOIN_ID", "SUM_SUM_Unique_in_1km"], ["n6_count","n6_count_unique"])
arcpy.Delete_management(t_summary)

expression = "scoring( !n6_count_unique!, !n6_count! )"
codeblock = """def scoring(unique, count):
        if unique > 0 and count > 0:
            return 5
        elif unique == 0 and count > 0:
            return 3
        elif unique == 0 and count == 0:
            return 1
        elif unique is None and count is None:
            return 1
        else:
            return 4"""
arcpy.CalculateField_management(v_m98_areas, "n6_score", expression, "PYTHON_9.3", codeblock)
arcpy.DeleteField_management(v_m98_areas, "n6_count_unique")
arcpy.DeleteField_management(v_m98_areas, "n6_count")

