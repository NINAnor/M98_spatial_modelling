"""
NAME:    M98 valuation of recreation areas
         5 - Function

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\5_function\5_function.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")

## input data
# M98 areas
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

# study extent
v_ok = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

# betweenness of paths - computed in QGIS
v_3_paths = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\5_function\n50_transport_lines_selection_OK_simplified_analysis.shp"

# aktivitetssoner i marka
v_3_aktivitetssoner = r"R:\Prosjekter\OpenNESS\GIS\Surveys\Survey recreation phase II\Aktivitetssoner.shp"


# ####################### #
# SCORE 3 - Infallsporter #
# ####################### #
# Add temporary column to store area into M98 areas
AddFieldIfNotexists(v_m98_areas, "temp_area_m98", "Double")
arcpy.CalculateField_management(v_m98_areas,"temp_area_m98","!Shape.area@squaremeters!","PYTHON_9.3")

# Intersect
v_3_zones_intersect = "temp_3_zones_intersect"
arcpy.Intersect_analysis([v_m98_areas, v_3_aktivitetssoner], v_3_zones_intersect)

# Dissolve by ID of M98
v_3_zones_dissolve = "temp_3_zones_dissolve"
arcpy.Dissolve_management(v_3_zones_intersect, v_3_zones_dissolve, "JOIN_ID", [["temp_area_m98","FIRST"]])
arcpy.Delete_management(v_3_zones_intersect)
arcpy.DeleteField_management(v_m98_areas, "temp_area_m98")

# Compute percentage of M98 taken by aktivitetssone
AddFieldIfNotexists(v_3_zones_dissolve, "n5_3_zones_ratio", "Double")
arcpy.CalculateField_management(v_3_zones_dissolve, "n5_3_zones_ratio", "[Shape_Area]/[FIRST_temp_area_m98]")

# Summarize
t_3_zones_summary = "temp_3_zones_summary"
arcpy.Statistics_analysis(v_3_zones_dissolve, t_3_zones_summary, [["n5_3_zones_ratio", "FIRST"]], "JOIN_ID")

# Give score 3 to areas where ratio is > 50 %
AddFieldIfNotexists(t_3_zones_summary, "n5_score", "Short")
expression = "score( !FIRST_n5_3_zones_ratio! )"
codeblock = """def score(ratio):
  if ratio >= 0.5:
    return 3
  else:
    return 1"""
arcpy.CalculateField_management(t_3_zones_summary, "n5_score", expression, "PYTHON_9.3", codeblock)


# ##################### #
# SCORE 3 - Betweenness #
# ##################### #
# shrink recreational areas by 10 m to avoid inaccuarcies
v_3_paths_m98_shrink = "temp_3_paths_m98_shrink"
arcpy.Buffer_analysis(v_m98_areas, v_3_paths_m98_shrink, "-10 Meters")

v_3_paths_intersect = "temp_3_paths_intersect_undissolved"
arcpy.Intersect_analysis([v_3_paths, v_3_paths_m98_shrink], v_3_paths_intersect)
arcpy.Delete_management(v_3_paths_m98_shrink)

v_3_paths_dissolve = "temp_3_paths_intersect"
arcpy.Dissolve_management(v_3_paths_intersect, v_3_paths_dissolve, ["JOIN_ID", "CH"], "", "SINGLE_PART")
arcpy.Delete_management(v_3_paths_intersect)

# Add weighted score of betweenness
AddFieldIfNotexists(v_3_paths_dissolve, "n5_3_paths_weighted_betweenness", "Double")
arcpy.CalculateField_management(v_3_paths_dissolve, "n5_3_paths_weighted_betweenness", "[CH]*[Shape_Length]")

# Select only segments longer than 10 m
l_3_paths_dissolve = arcpy.MakeFeatureLayer_management (v_3_paths_dissolve, "temp_layer")
arcpy.SelectLayerByAttribute_management(l_3_paths_dissolve, "NEW_SELECTION", "Shape_Length > 10")

# Summarize by recreational area
t_3_paths_summary = "temp_3_paths_summary"
arcpy.Statistics_analysis(l_3_paths_dissolve, t_3_paths_summary, [["Shape_Length","SUM"],["n5_3_paths_weighted_betweenness","SUM"]], "JOIN_ID")

# Calculated weighted average betweenness
AddFieldIfNotexists(t_3_paths_summary, "n5_3_paths_average_betweenness", "Double")
arcpy.CalculateField_management(t_3_paths_summary, "n5_3_paths_average_betweenness", "[SUM_n5_3_paths_weighted_betweenness]/[SUM_Shape_Length]")

# Give score 3 to areas where betweenness is > limit
AddFieldIfNotexists(t_3_paths_summary, "n5_score", "Short")
expression = "score( !n5_3_paths_average_betweenness! )"
codeblock = """def score(value):
  limit = 1366759
  if value > limit:
    return 3
  else:
    return 1"""
arcpy.CalculateField_management(t_3_paths_summary, "n5_score", expression, "PYTHON_9.3", codeblock)


# ######################### #
# SCORE 3 - Neighbour count #
# ######################### #
t_3_polygons_neighbors = "temp_3_polygon_neighbors"
arcpy.PolygonNeighbors_analysis(v_m98_areas, t_3_polygons_neighbors, in_fields="JOIN_ID", area_overlap="AREA_OVERLAP", both_sides="BOTH_SIDES", cluster_tolerance="10 Meters")

# Summarize by recreational area
t_3_polygons_summary = "temp_3_polygon_summary"
arcpy.Statistics_analysis(t_3_polygons_neighbors, t_3_polygons_summary, [["src_JOIN_ID","COUNT"]], "src_JOIN_ID")
arcpy.Delete_management(t_3_polygons_neighbors)
arcpy.AlterField_management(t_3_polygons_summary, "src_JOIN_ID", 'JOIN_ID', 'JOIN_ID')

# Give score 3 to areas where COUNT is > limit 
AddFieldIfNotexists(t_3_polygons_summary, "n5_score", "Short")
expression = "score( !COUNT_src_JOIN_ID! )"
codeblock = """def score(value):
  limit = 4
  if value > limit:
    return 3
  else:
    return 1"""
arcpy.CalculateField_management(t_3_polygons_summary, "n5_score", expression, "PYTHON_9.3", codeblock)


# #################### #
# SCORE 5 - Omradetype #
# #################### #
# Select areas where Omradetype = "Grønnkorridor" or "Utfartsområde"
l_m98_areas = arcpy.MakeFeatureLayer_management(v_m98_areas, "temp_layer2")
arcpy.SelectLayerByAttribute_management(l_m98_areas, "NEW_SELECTION", "Omradetype LIKE 'Gr%nnkorridor' OR Omradetype LIKE 'Utfartsomr%'")

# Summarize
t_5_areas_summary = "temp_5_areas_summary"
arcpy.Statistics_analysis(l_m98_areas, t_5_areas_summary, [["Omradetype", "FIRST"]], "JOIN_ID")

# Score
AddFieldIfNotexists(t_5_areas_summary, "n5_score", "Short")
arcpy.CalculateField_management(t_5_areas_summary, "n5_score", "5")


# ################ #
# SUMMARIZE SCORES #
# ################ #
t_summary_merge = "temp_summary_merge"
arcpy.Merge_management([t_5_areas_summary, t_3_polygons_summary, t_3_paths_summary, t_3_zones_summary], t_summary_merge)

t_summary_final = "temp_summary_final"
arcpy.Statistics_analysis(t_summary_merge, t_summary_final, [["n5_score","MAX"]], "JOIN_ID")  

# Compute scoring
AddFieldIfNotexists(v_m98_areas, "n5_score", "Double")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_final, "JOIN_ID", ["MAX_n5_score"], ["n5_score"])
arcpy.Delete_management(t_summary_merge)

# Replace nulls
expression = "replaceNull( !n5_score! )"
codeblock = """def replaceNull(value):
  if value is None:
    return 1
  else:
    return value"""
arcpy.CalculateField_management(v_m98_areas, "n5_score", expression, "PYTHON_9.3", codeblock)



