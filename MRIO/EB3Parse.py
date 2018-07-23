# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 14:48:42 2014
Modified Aug 22 2017 to Dec 2017

@author: pauliuk
"""

# Script IoC_SupplyChains.py

# Import required libraries:
#%%
import os  
import sys
import logging
import xlrd, xlwt
import numpy as np
import time
import datetime
import scipy.io
# import string as string
# import scipy.sparse.linalg as slinalg
import scipy
#import pandas as pd
import imp
#import csv
import shutil   
import uuid
import matplotlib.pyplot as plt   
import pylab
from scipy.sparse import csr_matrix
from pysut import SupplyUseTable
import pandas as pd
  
    
####################################
# Define plot and other  functions #
####################################
def config_string_cutout(String, Code, leftstart, rightstart): # Returns substring between = and EoL for given identifier in config file
# example: if Config_File_Line is "Data_Path_Network_1=K:\Research_Data" the function call
# config_string_cutout(Config_File_Line,'Data_Path_Network_1','=','\n') will return 'K:\Research_Data'
    Codeindex = String.find(Code,0,len(String))
    if Codeindex == -1:
        return 'None'
    else:
        Startindex = String.find(leftstart,Codeindex,len(String)) 
        Endindex   = String.find(rightstart,Codeindex,len(String))
        return String[Startindex +1:Endindex]

#################
#     MAIN      #
#################
"""
Read configuration data
"""    
FolderPath = os.path.expanduser("~/PythonConfigFile.txt") ## machine-dependent but OS independent path finder
FolderFile = open(FolderPath, 'r') 
FolderText = FolderFile.read()
#Extract path names from main file
ProjectSpecs_User_Name     = config_string_cutout(FolderText,'UserName','=','\n').strip()
ProjectSpecs_Path_Main     = config_string_cutout(FolderText,'Project_Path_1','=','\n').strip()
ProjectSpecs_Name_ConFile  = config_string_cutout(FolderText,'Configuration_File_1','=','\n').strip()
ProjectSpecs_DataPath1     = config_string_cutout(FolderText,'EXIOBASE3_Path','=','\n').strip()
ProjectSpecs_PackagePath1  = config_string_cutout(FolderText,'Package_Path_1','=','\n').strip()
sys.path.append(ProjectSpecs_PackagePath1)


# import packages whose location is now on the system path:    
#import matrix_view as mv
import Utils_Pauliuk as up
# import pymrio as mr

# Load project-specific config file
Project_Configfile  = xlrd.open_workbook(ProjectSpecs_Path_Main + 'Calculation\\' + ProjectSpecs_Name_ConFile)
Project_Configsheet = Project_Configfile.sheet_by_name('Config')

Name_Script        = Project_Configsheet.cell_value(6,3)
if Name_Script != 'EB3Parse': # Name of this script must equal the specified name in the Excel config file
    print('Fatal error: The name of the current script does not match to the sript name specfied in the project configuration file. Exiting the script.')
    sys.exit()
Name_Scenario      = Project_Configsheet.cell_value(5,3)
StartTime          = datetime.datetime.now()
TimeString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day) + '__' + str(StartTime.hour) + '_' + str(StartTime.minute) + '_' + str(StartTime.second)
DateString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day)
Path_Result        = ProjectSpecs_Path_Main + 'Results\\' + Name_Script + '\\' + Name_Scenario + '_' + TimeString + '\\'

DES_NoofCountries  = int(Project_Configsheet.cell_value(4,9))
DES_NoofProducts   = int(Project_Configsheet.cell_value(5,9))
DES_NoofIndustries = int(Project_Configsheet.cell_value(6,9))
DES_NoofIOSectors  = int(Project_Configsheet.cell_value(7,9))
DES_NoofFDCategories = int(Project_Configsheet.cell_value(8,9))

# Read control and selection parameters into dictionary
ScriptConfig = {'Scenario_Description': Project_Configsheet.cell_value(7,3)}
for m in range(10,16): # add all defined control parameters to dictionary
    ScriptConfig[Project_Configsheet.cell_value(m,1)] = Project_Configsheet.cell_value(m,3)

ScriptConfig['Current_UUID'] = str(uuid.uuid4())

# Create scenario folder
up.ensure_dir(Path_Result)
#
#Copy script and Config file into that folder
shutil.copy(ProjectSpecs_Path_Main + 'Calculation\\' + ProjectSpecs_Name_ConFile, Path_Result +ProjectSpecs_Name_ConFile)
shutil.copy(ProjectSpecs_Path_Main + 'Calculation\\' + Name_Script + '.py', Path_Result + Name_Script + '.py')
# Initialize logger    
[Mylog,console_log,file_log] = up.function_logger(logging.DEBUG, Name_Scenario + '_' + TimeString, Path_Result, logging.DEBUG) 

# log header and general information
Mylog.info('<html>\n<head>\n</head>\n<body bgcolor="#ffffff">\n<br>')
Mylog.info('<font "size=+5"><center><b>Script ' + Name_Script + '.py</b></center></font>')
Mylog.info('<font "size=+5"><center><b>Version: 2014-09-05</b></center></font>')
Mylog.info('<font "size=+4"> <b>Current User: ' + ProjectSpecs_User_Name + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Path: ' + ProjectSpecs_Path_Main + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Scenario: ' + Name_Scenario + '.</b></font><br>')
Mylog.info(ScriptConfig['Scenario_Description'])
Mylog.info('Unique ID of scenario run: <b>' + ScriptConfig['Current_UUID'] + '</b>')

Time_Start = time.time()
Mylog.info('<font "size=+4"> <b>Start of simulation: ' + time.asctime() + '.</b></font><br>')

Mylog.info('<p><b>Reading EXBIOBASE country, product and country classification and mappings.</b></p>')
# Read Country classification and aggregation info
Project_Countries = Project_Configfile.sheet_by_name('EXIOBASE3_Countries')
DES_Population_2007 = []
DES_Countries_Abb = []
DES_CountryList = []
for m in range(0,DES_NoofCountries):
    DES_Population_2007.append(Project_Countries.cell_value(m+4,12))
    DES_Countries_Abb.append(Project_Countries.cell_value(m+4,4))
    DES_CountryList.append(Project_Countries.cell_value(m+4,5))
    
Project_Classification = Project_Configfile.sheet_by_name('EXIOBASE3_pxi')
   
DES_ProductNames163_original = []    
for m in range(0,163):
    DES_ProductNames163_original.append(Project_Classification.cell_value(m+2,5))
    
DES_IndustryNames163_original = []    
for m in range(0,163):
    DES_IndustryNames163_original.append(Project_Classification.cell_value(m+2,8))   

DES_FD_Categories = []    
for m in range(164,171):
    DES_FD_Categories.append(Project_Classification.cell_value(m+2,8))   
    
Extensions_Codes     = []
for m in range(0,1330):
    Extensions_Codes.append(Project_Classification.cell_value(m+2,10))   
    
Extensions_Units     = []
for m in range(0,1330):
    Extensions_Units.append(Project_Classification.cell_value(m+2,12))   

# Read C-matrix
Project_CFile  = xlrd.open_workbook(ScriptConfig['CFactorPath'])
Project_CSheet = Project_CFile.sheet_by_name('midpoints')    

MidpointNames = []
for m in range(0,36):
    MidpointNames.append(Project_CSheet.cell_value(m+4,0))  
    
MidpointUnits = []
for m in range(0,36):
    MidpointUnits.append(Project_CSheet.cell_value(m+4,4))     
    
MRIO_C = np.zeros((len(MidpointNames),len(Extensions_Codes)))
for m in range(0,len(MidpointNames)):
    for n in range(0,len(Extensions_Codes)):
        MRIO_C[m,n] = Project_CSheet.cell_value(m +4,n +5)

# Read raw data and build model
for m in range(1995,2016):
    CurrentYear = m
    print(CurrentYear)
        
    Mylog.info('<p>Read raw data. </p>')
    Path = ScriptConfig['RawDataPath'] + str(CurrentYear) + '\\Y.txt'
    MRIO_Y_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
    MRIO_Y = MRIO_Y_raw.as_matrix()[2::,1::]
    MRIO_Y = MRIO_Y.astype('float')
    
    Path = ScriptConfig['RawDataPath'] + str(CurrentYear) + '\\Z.txt'
    MRIO_Z_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
    MRIO_Z = MRIO_Z_raw.as_matrix()[2::,1::]
    MRIO_Z = MRIO_Z.astype('float')
    
    Path = ScriptConfig['RawDataPath'] + str(CurrentYear) + '\\satellite\\F.txt'
    MRIO_F_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
    MRIO_F = MRIO_F_raw.as_matrix()[2::,1::]
    MRIO_F = MRIO_F.astype('float')
    
    Path = ScriptConfig['RawDataPath'] + str(CurrentYear) + '\\satellite\\F_hh.txt'
    MRIO_Fhh_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
    MRIO_Fhh = MRIO_Fhh_raw.as_matrix()[2::,1::]
    MRIO_Fhh = MRIO_Fhh.astype('float')
    
    
    Mylog.info('<p>Build A matrix. </p>')
    MRIO_X = MRIO_Z.sum(axis =1) + MRIO_Y.sum(axis =1)
    MRIO_A = np.zeros(MRIO_Z.shape)
    for m in range(0,MRIO_A.shape[0]):
        if MRIO_X[m] > 1: # Threshold for sector output: 1 MEUR
            MRIO_A[:,m] = MRIO_Z[:,m] / MRIO_X[m]
    
    Mylog.info('<p>Build S matrix. </p>')
    MRIO_S = np.zeros(MRIO_F.shape)
    for m in range(0,MRIO_A.shape[0]):
        if MRIO_X[m] > 1: # Threshold for sector output: 1 MEUR
            MRIO_S[:,m] = MRIO_F[:,m] / MRIO_X[m]
            
    Mylog.info('<p>Build IO model. </p>')
    MRIO_L = np.linalg.inv(np.eye(MRIO_A.shape[0]) - MRIO_A)
    
    
    Filestring_Matlab_out = ScriptConfig['IOModelPath'] + str(CurrentYear) + '_ITC.mat'
    scipy.io.savemat(Filestring_Matlab_out, mdict={'ScriptConfig':ScriptConfig,
                                                        'EB3_S_ITC':MRIO_S,
                                                        'EB3_TableUnits':'MEUR',
                                                        'EB3_Extensions_Labels':Extensions_Codes,
                                                        'EB3_Extensions_Units':Extensions_Units,
                                                        'EB3_FDCats':DES_FD_Categories,
                                                        'EB3_L_ITC':MRIO_L,
                                                        'EB3_RegionList':DES_CountryList,
                                                        'EB3_Y':MRIO_Y,
                                                        'EB3_A_ITC':MRIO_A,
                                                        'EB3_ProductNames163':DES_ProductNames163_original,
                                                        'EB3_IndustryNames163':DES_IndustryNames163_original,
                                                        'EB3_FinalDemand_Emissions':MRIO_Fhh,
                                                        'EB3_CharacterisationFactors': MRIO_C,
                                                        'EB3_Midpoints': MidpointNames,
                                                        'EB3_CharacterisationUnits': MidpointUnits,
                                                      })


#                         
Mylog.info('<br> Script is finished. Terminating logging process and closing all log files.<br>')
Time_End = time.time()
Time_Duration = Time_End - Time_Start
Mylog.info('<font "size=+4"> <b>End of simulation: ' + time.asctime() + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Duration of simulation: %.1f seconds.</b></font><br>' % Time_Duration)
logging.shutdown()
# remove all handlers from logger
root = logging.getLogger()
root.handlers = [] # required if you don't want to exit the shell
#
#
# The End
