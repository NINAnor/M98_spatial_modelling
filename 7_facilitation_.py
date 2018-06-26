"""
NAME:    M98 valuation of recreation areas
         7 - Facilitation onsite

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\7_facilitation.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 33N")
 
## input data

# M98 areas
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

# ======================= #
# BYM facilities - points
# ======================= #
v_points_bym = [r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_hytter_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_markastue_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_informasjonstavle_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_fastgrill_OB_2018.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_badeplass_OK_2018.shp',r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Skog\BYM_godkjente_ildsteder_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Idrettsanlegg\BYM_svommeanlegg_OB_2018.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Samferdsel\BYM_sykkelparkering_OB_2018.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Drift\BYM_avfallsbeholdere_OB_2018.shp', r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_lekeplass_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_smabathavner_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_drinking_fountain_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_exercise_equipment_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_sitting_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_wc_OB_2015.shp']

v_points_bym_merge = "temp_points_bym_merge"
arcpy.Merge_management(v_points_bym, v_points_bym_merge)

# intersect with M98
v_points_bym_intersect_2 = "temp_points_bym_intersect_2"
arcpy.Intersect_analysis([v_points_bym_merge, v_m98_areas], v_points_bym_intersect_2)
arcpy.Delete_management(v_points_bym_merge)

# score
AddFieldIfNotexists(v_points_bym_intersect_2, "n7_temp_score", "Short")
expression = "scoring(!Type!)"
codeblock = """def scoring(code):
        if code in ('Informasjonstavle', 'Badeplass'):
            return 2
        elif code in ('Fastgrill', 'Ildsted', 'Friluftsbad', 'Sykkelparkering', 'Soppelkasse', 'Lekeplass', 'Toalett', 'Benk', 'Treningsplass', 'DNT-hytte', 'Privat hytte', 'Markastue','Smabathavn','Drikkefontene'):
            return 4
        elif code in ('HC-tilrettelagt badeplass'):
            return 5
        else:
            return None"""
arcpy.CalculateField_management(v_points_bym_intersect_2, "n7_temp_score", expression, "PYTHON_9.3", codeblock)

# remove rows with empty score
l_points_bym_intersect = arcpy.MakeFeatureLayer_management(v_points_bym_intersect_2, "temp_layer")
arcpy.SelectLayerByAttribute_management(l_points_bym_intersect, "NEW_SELECTION", "n7_temp_score IS NOT NULL")
v_points_bym_intersect = "temp_points_bym_intersect"
arcpy.FeatureClassToFeatureClass_conversion(l_points_bym_intersect, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\7_facilitation.gdb", v_points_bym_intersect)
arcpy.Delete_management(v_points_bym_intersect_2)

# attribute table
t_points_bym_summary = "temp_points_bym_summary"
arcpy.Statistics_analysis(v_points_bym_intersect, t_points_bym_summary, [["JOIN_ID","FIRST"], ["n7_temp_score", "FIRST"]], "OBJECTID_1") 


# ================== #
# OSM points
# ================== #
v_inp_osm = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_pois_free_1.shp"

# select facilities
# picnic site
l_points_osm_1 = arcpy.MakeFeatureLayer_management (v_inp_osm, "temp_layer1")
arcpy.SelectLayerByAttribute_management (l_points_osm_1, "NEW_SELECTION", "code in (2741)")

# tourist info, remove tourist info too close (10 m) to BYM tourist info
l_points_osm_2 = arcpy.MakeFeatureLayer_management (v_inp_osm, "temp_layer2")
arcpy.SelectLayerByAttribute_management (l_points_osm_2, "NEW_SELECTION", "code in (2701, 2704, 2705, 2706)")
arcpy.SelectLayerByLocation_management(l_points_osm_2, "WITHIN_A_DISTANCE", r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_informasjonstavle_OK_2015.shp', "10", "REMOVE_FROM_SELECTION")

# playground, remove playground info too close (10 m) to BYM lekeplass
l_points_osm_3 = arcpy.MakeFeatureLayer_management (v_inp_osm, "temp_layer3")
arcpy.SelectLayerByAttribute_management (l_points_osm_3, "NEW_SELECTION", "code in (2205)")
arcpy.SelectLayerByLocation_management(l_points_osm_3, "WITHIN_A_DISTANCE", r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_lekeplass_OB_2015.shp', "10", "REMOVE_FROM_SELECTION")

# toilet, remove playground info too close (10 m) to BYM toilet
l_points_osm_4 = arcpy.MakeFeatureLayer_management (v_inp_osm, "temp_layer40")
arcpy.SelectLayerByAttribute_management (l_points_osm_4, "NEW_SELECTION", "code in (2901)")
arcpy.SelectLayerByLocation_management(l_points_osm_4, "WITHIN_A_DISTANCE", r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_wc_OB_2015.shp', "10", "REMOVE_FROM_SELECTION")

# bench, remove playground info too close (10 m) to BYM bench
l_points_osm_5 = arcpy.MakeFeatureLayer_management (v_inp_osm, "temp_layer50")
arcpy.SelectLayerByAttribute_management (l_points_osm_5, "NEW_SELECTION", "code in (2902)")
arcpy.SelectLayerByLocation_management(l_points_osm_5, "WITHIN_A_DISTANCE", r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\uncategorized\BYM_sitting_OB_2015.shp', "10", "REMOVE_FROM_SELECTION")

# merge all layers
v_points_osm_merge = "temp_points_osm_merge"
arcpy.Merge_management([l_points_osm_1, l_points_osm_2, l_points_osm_3, l_points_osm_4, l_points_osm_5], v_points_osm_merge)

# intersect with M98
v_points_osm_intersect = "temp_points_osm_intersect"
arcpy.Intersect_analysis([v_points_osm_merge, v_m98_areas], v_points_osm_intersect)
arcpy.Delete_management(v_points_osm_merge)

# score
AddFieldIfNotexists(v_points_osm_intersect, "n7_temp_score", "Short")
expression = "scoring( !code!)"
codeblock = """def scoring(code):
        if code in (2701, 2704, 2705, 0706):
            return 2
        elif code in (2205, 2741, 2901, 2902):
            return 4
        else:
            return None"""
arcpy.CalculateField_management(v_points_osm_intersect, "n7_temp_score", expression, "PYTHON_9.3", codeblock)

# attribute table
t_points_osm_summary = "temp_points_osm_summary"
arcpy.Statistics_analysis(v_points_osm_intersect, t_points_osm_summary, [["JOIN_ID","FIRST"], ["n7_temp_score", "FIRST"]], "OBJECTID") 


# ======================= #
# BYM facilities - lines
# ======================= #
v_lines_bym = [r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_skiloyper_preparert_bym_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_skiloyper_upreparert_andre_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_sykkelruter_marka_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_tursti_byggesonen_OB_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_tursti_kommuneskogen_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_kyststi_OK_2015.shp',
r'R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_pilgrimsleden_NO_2015.shp']

v_lines_bym_merge = "temp_lines_bym_merge"
arcpy.Merge_management(v_lines_bym, v_lines_bym_merge)

# intersect with M98
l_lines_bym_merge = arcpy.MakeFeatureLayer_management (v_lines_bym_merge, "temp_layer3")
arcpy.SelectLayerByAttribute_management (l_lines_bym_merge, "NEW_SELECTION", "TYPE IS NULL OR TYPE <> 'Blamerket sti'")
v_lines_bym_intersect = "temp_lines_bym_intersect"
arcpy.Intersect_analysis([l_lines_bym_merge, v_m98_areas], v_lines_bym_intersect)

# dissolve by type and recreation area
v_lines_bym_dissolve = "temp_lines_bym_dissolve"
arcpy.Dissolve_management(v_lines_bym_intersect, v_lines_bym_dissolve, ["JOIN_ID", "TOSPOR", "Type"])
arcpy.Delete_management(v_lines_bym_intersect)

# delete tracks shorter than 100 m
l_lines_bym_select = arcpy.MakeFeatureLayer_management(v_lines_bym_dissolve, "temp_layer4")
arcpy.SelectLayerByAttribute_management(l_lines_bym_select, "NEW_SELECTION", "Shape_Length > 100")

v_lines_bym_select = "temp_lines_bym_select"
arcpy.FeatureClassToFeatureClass_conversion(l_lines_bym_select, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\7_facilitation.gdb", v_lines_bym_select)
arcpy.Delete_management(v_lines_bym_dissolve)

# score
AddFieldIfNotexists(v_lines_bym_select, "n7_temp_score", "Short")
expression = "scoring(!TOSPOR!, !Type!)"
codeblock = """def scoring(TOSPOR,Type):
        if Type == 'Skiloype':
            if TOSPOR == 'Ja':
                return 3
            else:
                return 2
        elif Type in ('Pilgrimsleden', 'Kyststi', 'Sykkelruter', 'Turvei', 'AnnenTurvei', 'Natursti', 'Kulturminnesti', 'Kulturlandskapssti'):
            return 2
        elif Type == 'Sti for bevegelseshemmede':
            return 5
        else:
            return None"""
        
arcpy.CalculateField_management(v_lines_bym_select, "n7_temp_score", expression, "PYTHON_9.3", codeblock)

# attribute table
t_lines_bym_summary = "temp_lines_bym_summary"
arcpy.Statistics_analysis(v_lines_bym_select, t_lines_bym_summary, [["JOIN_ID","FIRST"], ["n7_temp_score", "FIRST"]], "OBJECTID") 


# ======================= #
# N50 facilities - lines
# ======================= #
v_lines_n50_1 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_transport_lines_OAF_2017"

v_lines_n50_2 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_construction_and_facilitation_lines_OAF_2017"

# select paths
l_lines_n50_1 = arcpy.MakeFeatureLayer_management (v_lines_n50_1, "temp_layer5")
arcpy.SelectLayerByAttribute_management (l_lines_n50_1, "NEW_SELECTION", "(objtype = 'Sti' AND merking = 'JA')")

l_lines_n50_2 = arcpy.MakeFeatureLayer_management (v_lines_n50_2, "temp_layer6")
arcpy.SelectLayerByAttribute_management (l_lines_n50_2, "NEW_SELECTION", "(objtype = 'Lysloype')")

# merge
v_lines_n50_merge = "temp_lines_n50_merge"
arcpy.Merge_management([l_lines_n50_1, l_lines_n50_2], v_lines_n50_merge)

# intersect with M98
v_lines_n50_intersect = "temp_lines_n50_intersect"
arcpy.Intersect_analysis([v_lines_n50_merge, v_m98_areas], v_lines_n50_intersect)
arcpy.Delete_management(v_lines_n50_merge)

# dissolve by type and recreation area
v_lines_n50_dissolve = "temp_lines_n50_dissolve"
arcpy.Dissolve_management(v_lines_n50_intersect, v_lines_n50_dissolve, ["JOIN_ID", "objtype"])
arcpy.Delete_management(v_lines_n50_intersect)

# delete tracks shorter than 100 m
l_lines_n50_select = arcpy.MakeFeatureLayer_management(v_lines_n50_dissolve, "temp_layer6")
arcpy.SelectLayerByAttribute_management(l_lines_n50_select, "NEW_SELECTION", "Shape_Length > 100")

v_lines_n50_select = "temp_lines_n50_select"
arcpy.FeatureClassToFeatureClass_conversion(l_lines_n50_select, r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\7_facilitation.gdb", v_lines_n50_select)
arcpy.Delete_management(v_lines_n50_dissolve)

# score
AddFieldIfNotexists(v_lines_n50_select, "n7_temp_score", "Short")
expression = "scoring(!objtype!)"
codeblock = """def scoring(objtype):
        if objtype == 'Sti':
            return 2
        elif objtype == 'Lysloype':
            return 3"""
arcpy.CalculateField_management(v_lines_n50_select, "n7_temp_score", expression, "PYTHON_9.3", codeblock)

# attribute table
t_lines_n50_summary = "temp_lines_n50_summary"
arcpy.Statistics_analysis(v_lines_n50_select, t_lines_n50_summary, [["JOIN_ID","FIRST"], ["n7_temp_score", "FIRST"]], "OBJECTID")   


# ======================= #
# N50 - bridges
# ======================= #
v_bridges_n50 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_transport_lines_OAF_2017"

# select paths
l_bridges_n50 = arcpy.MakeFeatureLayer_management (v_bridges_n50, "temp_layer7")
arcpy.SelectLayerByAttribute_management (l_bridges_n50, "NEW_SELECTION", "objtype = 'Sti' AND medium = 'L'")

# intersect with M98
v_bridges_n50_intersect = "temp_bridges_n50_intersect"
arcpy.Intersect_analysis([l_bridges_n50, v_m98_areas], v_bridges_n50_intersect)

# score
AddFieldIfNotexists(v_bridges_n50_intersect, "n7_temp_score", "Short")
arcpy.CalculateField_management(v_bridges_n50_intersect, "n7_temp_score", "2", "PYTHON_9.3", codeblock)

# attribute table
t_bridges_n50_summary = "temp_bridges_n50_summary"
arcpy.Statistics_analysis(v_bridges_n50_intersect, t_bridges_n50_summary, [["JOIN_ID","FIRST"], ["n7_temp_score", "FIRST"]], "OBJECTID")   


# ======================= #
# SUMMARY
# ======================= #
t_summary_merge = "temp_summary_merge"
arcpy.Merge_management([t_points_bym_summary, t_points_osm_summary, t_lines_bym_summary, t_lines_n50_summary, t_bridges_n50_summary], t_summary_merge)

t_summary_final = "temp_summary_final"
arcpy.Statistics_analysis(t_summary_merge, t_summary_final, [["FIRST_JOIN_ID","COUNT"], ["FIRST_n7_temp_score", "SUM"], ["FIRST_n7_temp_score", "MEAN"], ["FIRST_n7_temp_score", "MIN"], ["FIRST_n7_temp_score", "MAX"]], "FIRST_JOIN_ID")  

## Compute scoring
AddFieldIfNotexists(v_m98_areas, "n7_score", "Double")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_final, "FIRST_JOIN_ID", ["MAX_FIRST_n7_temp_score"], ["n7_score"])
arcpy.Delete_management(t_summary)

expression = "scoring( !n7_score! )"
codeblock = """def scoring(score):
        if score is None:
            return 1
        else:
            return score"""
arcpy.CalculateField_management(v_m98_areas, "n7_score", expression, "PYTHON_9.3", codeblock)


