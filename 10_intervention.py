"""
NAME:    M98 valuation of recreation areas
         10 - Intervention

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\10_intervention.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
arcpy.env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833"

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"

r_naturalness = r"R:\Prosjekter\15883000 - URBAN EEA\ESTIMAP\ESTIMAP Recreation\Recreation 2018\DATA\E_step01.gdb\q9_1_degree_naturalness_OAF_10m"

v_transport = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_transport_lines_OAF_2017"
v_construction = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\N50\n50.gdb\n50_construction_and_facilitation_lines_OAF_2017"

# ============ #
# == Rank 3 == #
# ============ #
# Select layers
l_transport_3 = arcpy.MakeFeatureLayer_management (v_transport, "temp_layer1")
arcpy.SelectLayerByAttribute_management(l_transport_3, "NEW_SELECTION", "((objtype = 'Bane') OR ( objtype = 'VegSenterlinje' AND vegkategori <> 'P')) AND medium <> 'U'")

l_construction_3 = arcpy.MakeFeatureLayer_management (v_construction, "temp_layer2")
arcpy.SelectLayerByAttribute_management(l_construction_3, "NEW_SELECTION", "objtype IN ('Ledning' , 'LuftledningLH')")

# Merge layers
v_merge_3 = "temp_merge_3"
arcpy.Merge_management([l_transport_3, l_construction_3], v_merge_3)

# Create influence zone
r_dist_3 = "temp_dist_3"
arcpy.gp.EucDistance_sa(v_merge_3, r_dist_3, "100", "10", "")
arcpy.Delete_management(v_merge_3)

# Reclass
r_class_3 = "temp_class_3"
arcpy.gp.RasterCalculator_sa('Con(IsNull("{}"),0,3)'.format(r_dist_3), r_class_3)
arcpy.Delete_management(r_dist_3)


# ============ #
# == Rank 2 == #
# ============ #
# Select layers
l_transport_2 = arcpy.MakeFeatureLayer_management (v_transport, "temp_layer3")
arcpy.SelectLayerByAttribute_management(l_transport_2, "NEW_SELECTION", "((objtype = 'Traktorveg') OR (objtype = 'VegSenterlinje' AND vegkategori = 'P')) AND medium <> 'U'")

l_construction_2 = arcpy.MakeFeatureLayer_management (v_construction, "temp_layer4")
arcpy.SelectLayerByAttribute_management(l_construction_2, "NEW_SELECTION", "objtype IN ('Lysloype' , 'Molo')")

# Merge layers
v_merge_2 = "temp_merge_2"
arcpy.Merge_management([l_transport_2, l_construction_2], v_merge_2)

# Create influence zone
r_dist_2 = "temp_dist_2"
arcpy.gp.EucDistance_sa(v_merge_2, r_dist_2, "100", "10", "")
arcpy.Delete_management(v_merge_2)

# Reclass
r_class_2 = "temp_class_2"
arcpy.gp.RasterCalculator_sa('Con(IsNull("{}"),0,2)'.format(r_dist_2), r_class_2)
arcpy.Delete_management(r_dist_2)


# ============ #
# == Rank 1 == #
# ============ #
# Select layers
l_transport_1 = arcpy.MakeFeatureLayer_management (v_transport, "temp_layer5")
arcpy.SelectLayerByAttribute_management(l_transport_1, "NEW_SELECTION", "objtype = 'GangSykkelveg'")

l_construction_1 = arcpy.MakeFeatureLayer_management (v_construction, "temp_layer6")
arcpy.SelectLayerByAttribute_management(l_construction_1, "NEW_SELECTION", "objtype IN ('Dam' , 'Flytebrygge', 'KaiBrygge', 'Pir')")

# Merge layers
v_merge_1 = "temp_merge_1"
arcpy.Merge_management([l_transport_1, l_construction_1], v_merge_1)

# Create influence zone
r_dist_1 = "temp_dist_1"
arcpy.gp.EucDistance_sa(v_merge_1, r_dist_1, "100", "10", "")
arcpy.Delete_management(v_merge_1)

# Reclass
r_class_1 = "temp_class_1"
arcpy.gp.RasterCalculator_sa('Con(IsNull("{}"),0,1)'.format(r_dist_1), r_class_1)
arcpy.Delete_management(r_dist_1)


# ============================================================================= #
# == Merge influence zones and degree of naturalness with the maximum on top == #
# ============================================================================= #
r_ranking = "temp_ranking"
arcpy.gp.RasterCalculator_sa('Con("{rn}"==0,3,Con("{r3}">"temp_class_2", "{r3}", Con("{r2}">"{r1}","{r2}","{r1}")))'.format(rn=r_naturalness,r3=r_class_3, r2=r_class_2, r1=r_class_1), r_ranking)
arcpy.Delete_management(r_class_1)
arcpy.Delete_management(r_class_2)
arcpy.Delete_management(r_class_3)


# ============================= #
# == Average ranking in area == #
# ============================= #
t_summary_intervention = "temp_summary_intervention"
arcpy.gp.ZonalStatisticsAsTable_sa(v_m98_areas, "JOIN_ID", r_ranking, t_summary_intervention, "DATA", "MEAN")

# reclass based on minimum distance
AddFieldIfNotexists(t_summary_intervention, "n10_intervention_class", "Short")
codeblock = """def reclass(attr):
  if attr <= 0.8:
    return 5
  elif attr <= 1.7:
    return 4 
  elif attr <= 2.3:
    return 3 
  elif attr <= 2.7:
    return 2 
  else:
    return 1 """
arcpy.CalculateField_management(t_summary_intervention, "n10_intervention_class", "reclass(!MEAN!)", "PYTHON_9.3", codeblock)

AddFieldIfNotexists(v_m98_areas, "n10_score", "Short")
join_and_copy(v_m98_areas, "JOIN_ID", t_summary_intervention, "JOIN_ID", ["n10_intervention_class"], ["n10_score"])

