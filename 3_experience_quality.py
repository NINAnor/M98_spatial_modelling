"""
NAME:    M98 valuation of recreation areas
         3 - Experience quality

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\3_experience_quality.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")

## input data
# M98 areas
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

# study extent
v_ok = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

# elements
v_osm_poi_points     = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_pois_free_1.shp"
v_osm_poi_polys      = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_pois_a_free_1.shp"
v_osm_natural_points = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_natural_free_1.shp"
v_osm_natural_polys  = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_natural_a_free_1.shp"
v_bym_eventyrskog  = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\3_experience_quality.gdb\eventyrskog"
v_bym_flower_trees = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\ESTIMAP-R inputs\GUA\GUA_Nature_A.shp"
v_fkb_text = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\FKB\FKB_text_OK_2016.gdb\_0301_tekst1000_punkt"
v_kultur_local  = "C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\RIKSANTIKVAREN\kulturminner_localities_OK_2018.shp"
v_kultur_sefrak = "C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\RIKSANTIKVAREN\kulturminner_SEFRAK_OK_2018.shp"
v_kultur_freda  = "C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\RIKSANTIKVAREN\kulturminner_FREDA_OK_2018.shp"


## Go through input data
feature_classes = [v_osm_poi_points, v_osm_natural_points, v_osm_poi_polys, v_osm_natural_polys, v_bym_eventyrskog, v_bym_flower_trees, v_fkb_text, v_kultur_local, v_kultur_sefrak, v_kultur_freda]

i=0
v_merge_points   = "temp_merged_points"
v_merge_polygons = "temp_merged_polygons"

if arcpy.Exists(v_merge_points):
    arcpy.Delete_management(v_merge_points)           
if arcpy.Exists(v_merge_polygons):
    arcpy.Delete_management(v_merge_polygons)
    
for feature_class in feature_classes:

    arcpy.AddMessage("Processing {}...".format(feature_class))

    # feature class type
    desc = arcpy.Describe(feature_class)
    fc_type = desc.shapeType   
       
    # select categories of features
    l_feature_class = arcpy.MakeFeatureLayer_management (feature_class, "temp_layer")
    
    expression = ""
    if "pois" in feature_class:
        expression = "code IN (2721, 2723, 2724, 2725, 2731, 2732, 2733, 2734, 2735, 2736, 2742, 2737, 2904, 2950, 2953, 2955, 2962, 2963)"
    if "natural" in feature_class:
        expression = "code IN (4101, 4112, 4132, 4141)"
    if "GUA_Nature_A" in feature_class:
        expression = "name IN ('flower', 'old big trees')"
    if "FKB_text_OK_2016.gdb\_0301_tekst1000_punkt" in feature_class:
        expression = "NAVNTYPE IN (202, 204, 206, 207, 224, 225, 208)"     
    
    arcpy.SelectLayerByAttribute_management(l_feature_class, "NEW_SELECTION", expression)
    
    # select features in M98
    arcpy.SelectLayerByLocation_management(l_feature_class, "INTERSECT", v_m98_areas, "", "SUBSET_SELECTION")
    arcpy.AddMessage(" Features in M98 selected.")
    
    # select features which are not located too close to other feature (possible doublecounting)  
    if fc_type == "Point" and arcpy.Exists(v_merge_points):
        arcpy.SelectLayerByLocation_management(l_feature_class, "WITHIN_A_DISTANCE", v_merge_points, "10", "REMOVE_FROM_SELECTION")
        arcpy.AddMessage(" Close features removed.")
        
    # kulturminner must be counted only once (locality or point)
    if "SEFRAK" in feature_class:
        arcpy.SelectLayerByLocation_management(l_feature_class, "INTERSECT", v_kultur_local, "", "REMOVE_FROM_SELECTION")
    elif "FREDA" in feature_class:
        arcpy.SelectLayerByLocation_management(l_feature_class, "INTERSECT", v_kultur_local, "", "REMOVE_FROM_SELECTION")

    # intersect by recreation areas 
    v_intersect = "temp_intersect_{}".format(i)
    arcpy.Intersect_analysis([l_feature_class, v_m98_areas], v_intersect)

    # dissolve by area in case of Eventyrskog and Kulturminner localities to avoid doublecounting
    if "Eventyrskog" in feature_class:
        v_dissolve = "temp_dissolve_{}".format(i)
        arcpy.Dissolve_management(v_intersect, v_dissolve, ["JOIN_ID"])
        arcpy.Delete_management(v_intersect)
        arcpy.Rename_management(v_dissolve, v_intersect)
        
    if "kulturminner_localities_OK_2018" in feature_class:
        v_dissolve = "temp_dissolve_{}".format(i)
        arcpy.Dissolve_management(v_intersect, v_dissolve, ["JOIN_ID", "vernetype"])
        arcpy.Delete_management(v_intersect)
        arcpy.Rename_management(v_dissolve, v_intersect)
    
    # add field to store info about original layer
    AddFieldIfNotexists(v_intersect, "origin", "short")
    arcpy.CalculateField_management(v_intersect, "origin", i)
    arcpy.AddMessage(" Intersection done.")
    
    # merge together
    if fc_type == "Point":
        if not(arcpy.Exists(v_merge_points)):
            arcpy.Copy_management(v_intersect, v_merge_points)
            arcpy.AddMessage(" First point layer. Copying.")
        else:
            arcpy.AddMessage(" Other point layer. Merging.")
            v_merge_temp_points="v_merge_temp_points"
            arcpy.Merge_management([v_merge_points, v_intersect], v_merge_temp_points, field_mappings='JOIN_ID "JOIN_ID" true true false 4 Long 0 0 ,First,#,{v1},JOIN_ID,-1,-1,{v2},JOIN_ID,-1,-1;origin "origin" true true false 2 Short 0 0 ,First,#,{v1},origin,-1,-1,{v2},origin,-1,-1'.format(v1=v_merge_points, v2=v_intersect))              
            arcpy.Delete_management(v_merge_points)
            arcpy.Rename_management(v_merge_temp_points, v_merge_points)
    elif fc_type == "Polygon":
        if not(arcpy.Exists(v_merge_polygons)):
            arcpy.Copy_management(v_intersect, v_merge_polygons)
            arcpy.AddMessage(" First polygon layer. Copying.")
        else:
            arcpy.AddMessage(" Other polygon layer. Merging.")
            v_merge_temp_polygons="v_merge_temp_polygons"
            arcpy.Merge_management([v_merge_polygons, v_intersect], v_merge_temp_polygons, field_mappings='JOIN_ID "JOIN_ID" true true false 4 Long 0 0 ,First,#,{v1},JOIN_ID,-1,-1,{v2},JOIN_ID,-1,-1;origin "origin" true true false 2 Short 0 0 ,First,#,{v1},origin,-1,-1,{v2},origin,-1,-1'.format(v1=v_merge_polygons, v2=v_intersect))             
            arcpy.Delete_management(v_merge_polygons)
            arcpy.Rename_management(v_merge_temp_polygons, v_merge_polygons)
    
    arcpy.Delete_management(v_intersect)
    i= i+1

# Summarize points by JOIN_ID of recreation area
t_summary_points =  "temp_summary_points"
arcpy.Statistics_analysis(v_merge_points, t_summary_points, [["JOIN_ID","COUNT"]], "JOIN_ID") 
arcpy.AddMessage("Points summarized.")

t_summary_polygons =  "temp_summary_polygons"
arcpy.Statistics_analysis(v_merge_polygons, t_summary_polygons, [["JOIN_ID","COUNT"]], "JOIN_ID") # change this function if proportion of area for polygons is relevant     
arcpy.AddMessage("Polygons summarized.")

# Merge summary tables for points and polygons
t_merge = "temp_summary_merge"
arcpy.Merge_management([t_summary_points, t_summary_polygons], t_merge)
arcpy.Delete_management(t_summary_points)
arcpy.Delete_management(t_summary_polygons)   
   
# Summarize counts for each recreation area    
t_summary = "temp_summary_final"
arcpy.Statistics_analysis(t_merge, t_summary, [["COUNT_JOIN_ID","SUM"]], "JOIN_ID")
arcpy.AddMessage("Everything summarized.")
arcpy.Delete_management(t_merge)

# Compute scoring - natural breaks (manually compute breaks - 4 classes)
AddFieldIfNotexists(v_m98_areas, "n3_count", "Double")
AddFieldIfNotexists(v_m98_areas, "n3_score", "Double")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary, "JOIN_ID", ["SUM_COUNT_JOIN_ID"], ["n3_count"])
arcpy.Delete_management(t_summary)

expression = "scoring( !n3_count! )"
codeblock = """def scoring(attr):
        if attr is None:
            return 1
        if attr <= 2:
            return 2
        elif attr > 2 and attr <= 5:
            return 3
        elif attr > 5 and attr <= 13:
            return 4
        else:
            return 5"""
arcpy.CalculateField_management(v_m98_areas, "n3_score", expression, "PYTHON_9.3", codeblock)
arcpy.DeleteField_management(v_m98_areas, "n3_count")

    