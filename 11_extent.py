"""
NAME:    M98 valuation of recreation areas
         11 - Extent

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

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"


# Rank based on size
# size limits computed manually
AddFieldIfNotexists(v_m98_areas, "n11_score", "Short")
codeblock = """def extent(type, size):
  if type == "Andre friluftsomrader" and size >= 44781:
    return 5 
  elif type == "Gronnkorridor" and size >= 10950:
    return 5 
  elif type == "Jordbrukslandskap" and size >= 5609:
    return 5 
  elif type == "Leke- og rekreasjonsomrade" and size >= 6553:
    return 5 
  elif type == "Naerturterreng" and size >= 67819:
    return 5 
  elif type == "Store turomrader med tilrettelegging" and size >= 206610:
    return 5 
  elif type == "Strandsone med tilhorende sjo og vassdrag" and size >= 1509:
    return 5 
  elif type == "Utfartsomrade" and size >= 43344:
    return 5 
  else:
    return 1 
"""
arcpy.CalculateField_management(v_m98_areas, "n11_score", "extent(!Omradetype!, !Shape_Area!)", "PYTHON_9.3", codeblock)

