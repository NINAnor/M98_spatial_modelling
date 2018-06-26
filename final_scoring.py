"""
NAME:    M98 valuation of recreation areas
         Final scoring

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\12_accessibility.gdb"

# input data
v_m98_areas = r"C:\Users\zofie.cimburova\OneDrive - NINA\ESTIMAP\RECREATION_OSLO\RECREATION_LOCAL\M98\DATA\M98_areas\M98_areas.gdb\M98_recreational_areas_OK_11_17"


# ###################################### #
# General scoring - median of all scores #
# (main and supporting criteria)         #
# ###################################### #
AddFieldIfNotexists(v_m98_areas, "final_score_general", "Double")

expression = "median([!n3_score!,!n4_score!,!n5_score!,!n6_score!,!n7_score!,!n8_score!,!n9_score!,!n10_score!,!n11_score!,!n12_score!,!n13_score!])"
codeblock = """def median(list):
  list.sort()     
  i = len(list)/2     
  if len(list)%2 == 0:         
    #have to take avg of middle two         
    median = float(list[i] + list[i-1])/2     
  else:         
    #find the middle (remembering that lists start at 0)         
    median = list[i]             
  return median"""
arcpy.CalculateField_management(v_m98_areas, "final_score_general", expression, "PYTHON_9.3", codeblock)

# ####################################### #
# Main scoring - maximum of main criteria #
# ####################################### #
#AddFieldIfNotexists(v_m98_areas, "final_score_main", "Double")

#expression = "main([!n3_score!,!n4_score!,!n5_score!,!n6_score!,!n7_score!])"
codeblock = """def main(list):
  list.sort()     
  max = list[-1]             
  return max"""
#arcpy.CalculateField_management(v_m98_areas, "final_score_main", expression, "PYTHON_9.3", codeblock)


# ################################## #
# Final scoring - according to table #
# ################################## #
AddFieldIfNotexists(v_m98_areas, "final_score", "Text")

codeblock = """def final(general, main):
  if general > 3.5 and main == 5:
    return "A"
  elif general > 3.5 and (main == 3 or main == 4):
    return "B+"
  elif (general >= 2.5 and general <= 3.5) and main == 5:
    return "B+"
  elif (general >= 2.5 and general <= 3.5) and (main == 3 or main == 4):
    return "B"
  elif (general >= 2.5 and general <= 3.5) and (main == 1 or main == 2): 
    return "C+"
  elif (general < 2.5) and (main == 3 or main == 4): 
    return "C+"
  elif (general < 2.5) and (main == 1 or main == 2): 
    return "C"
  elif (general < 2.5) and main == 5: 
    return "?"
  else:
    return "?" """
arcpy.CalculateField_management(v_m98_areas, "final_score", "final(!final_score_general!,!final_score_main!)", "PYTHON_9.3", codeblock)

AddFieldIfNotexists(v_m98_areas, "final_score_numeric", "Double")
codeblock = """def final_numeric(letter):
  if letter == 'A':
    return 3
  elif letter == 'B+':
    return 2.5
  elif letter == 'B':
    return 2
  elif letter == 'C+':
    return 1.5
  elif letter == 'C':
    return 1
  else:
    return None """
arcpy.CalculateField_management(v_m98_areas, "final_score_numeric", "final_numeric(!final_score!)", "PYTHON_9.3", codeblock)
