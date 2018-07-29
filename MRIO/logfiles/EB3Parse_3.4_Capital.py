# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 14:48:42 2014
Modified Aug 22 2017 to July 2018

@author: pauliuk
"""

# Script EB3Parse_3.4_Capital.py

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
import getpass
import shutil   
import uuid
import matplotlib.pyplot as plt   
import pylab
from scipy.sparse import csr_matrix
from pysut import SupplyUseTable
import pandas as pd
  
import MRIO_Paths # Import path file


####################################
# Define plot and other  functions #
####################################


#################
#     MAIN      #
#################
"""
Read configuration data
"""    

sys.path.append(MRIO_Paths.PackagePath)


# import packages whose location is now on the system path:    
#import matrix_view as mv
import Utils_Pauliuk as up
# import pymrio as mr
ProjectSpecs_User_Name     = getpass.getuser()
# Load project-specific config file
Project_Configfile  = xlrd.open_workbook('EB3.4_Config.xlsx')
Project_Configsheet = Project_Configfile.sheet_by_name('Config')

Name_Script        = Project_Configsheet.cell_value(6,3)
if Name_Script != 'EB3Parse_3.4_Capital': # Name of this script must equal the specified name in the Excel config file
    print('Fatal error: The name of the current script does not match to the sript name specfied in the project configuration file. Exiting the script.')
    sys.exit()
Name_Scenario      = Project_Configsheet.cell_value(5,3)
StartTime          = datetime.datetime.now()
TimeString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day) + '__' + str(StartTime.hour) + '_' + str(StartTime.minute) + '_' + str(StartTime.second)
DateString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day)
Path_Result        = MRIO_Paths.ProjectPath + 'Results\\' + Name_Script + '\\' + Name_Scenario + '_' + TimeString + '\\'

# Read control and selection parameters into dictionary
ScriptConfig = {'Scenario_Description': Project_Configsheet.cell_value(7,3)}
for m in range(10,12): # add all defined control parameters to dictionary
    ScriptConfig[Project_Configsheet.cell_value(m,1)] = Project_Configsheet.cell_value(m,3)

ScriptConfig['Current_UUID'] = str(uuid.uuid4())
ScriptConfig['RawDataPath']  = MRIO_Paths.RawDataPath
ScriptConfig['CurrentYear']  = int(ScriptConfig['YearSelect'])

if ScriptConfig['ModelType'] == 'ixi':
    ColC = 9
if ScriptConfig['ModelType'] == 'pxp':
    ColC = 10

DES_NoofCountries  = int(Project_Configsheet.cell_value(4,ColC))
DES_NoofProducts   = int(Project_Configsheet.cell_value(5,ColC))
DES_NoofIndustries = int(Project_Configsheet.cell_value(6,ColC))
DES_NoofIOSectors  = int(Project_Configsheet.cell_value(7,ColC))
DES_NoofFDCategories = int(Project_Configsheet.cell_value(8,ColC))

# Create scenario folder
up.ensure_dir(Path_Result)
#
#Copy script and Config file into that folder
shutil.copy(MRIO_Paths.ProjectPath + 'Calculation\\EB3.4_Config.xlsx', Path_Result + 'EB3.4_Config.xlsx')
shutil.copy(MRIO_Paths.ProjectPath + 'Calculation\\' + Name_Script + '.py', Path_Result + Name_Script + '.py')
# Initialize logger    
[Mylog,console_log,file_log] = up.function_logger(logging.DEBUG, Name_Scenario + '_' + TimeString, Path_Result, logging.DEBUG) 

# log header and general information
Mylog.info('<html>\n<head>\n</head>\n<body bgcolor="#ffffff">\n<br>')
Mylog.info('<font "size=+5"><center><b>Script ' + Name_Script + '.py</b></center></font>')
Mylog.info('<font "size=+5"><center><b>Version: 2014-09-05</b></center></font>')
Mylog.info('<font "size=+4"> <b>Current User: ' + ProjectSpecs_User_Name + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Path: ' + MRIO_Paths.ProjectPath + '.</b></font><br>')
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
   
DES_ProductNames200 = []    
for m in range(0,200):
    DES_ProductNames200.append(Project_Classification.cell_value(m+2,2))
    
DES_ProductNames163 = []    
for m in range(0,163):
    DES_ProductNames163.append(Project_Classification.cell_value(m+2,5))    
    
DES_ProductNames163_Cap = DES_ProductNames163.copy()
DES_ProductNames163_Cap.append('Fixed aggregate capital (augmentation)')    
    
DES_IndustryNames163_original = []    
for m in range(0,163):
    DES_IndustryNames163_original.append(Project_Classification.cell_value(m+2,8))   

DES_IndustryNames163_original_Cap = DES_IndustryNames163_original.copy()
DES_IndustryNames163_original_Cap.append('Fixed aggregate capital (augmentation)')    

DES_FD_Categories = []    
for m in range(163,170):
    DES_FD_Categories.append(Project_Classification.cell_value(m+2,8))   
    
Extensions_Codes     = []
for m in range(0,1104):
    Extensions_Codes.append(Project_Classification.cell_value(m+2,10))   
    
Extensions_Units     = []
for m in range(0,1104):
    Extensions_Units.append(Project_Classification.cell_value(m+2,11))   

# Read C-matrix
Project_CFile  = xlrd.open_workbook(MRIO_Paths.CFactorPath)
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
Mylog.info('<p>Read raw data. </p>')
Path = ScriptConfig['RawDataPath'] + 'IOT_' + str(ScriptConfig['CurrentYear']) + '_' + ScriptConfig['ModelType'] + '\\Y.txt'
MRIO_Y_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Y = MRIO_Y_raw.as_matrix()[2::,1::]
MRIO_Y = MRIO_Y.astype('float')

Path = ScriptConfig['RawDataPath'] + 'IOT_' + str(ScriptConfig['CurrentYear']) + '_' + ScriptConfig['ModelType'] + '\\A.txt'
MRIO_A_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_A = MRIO_A_raw.as_matrix()[2::,1::]
MRIO_A = MRIO_A.astype('float')

Path = ScriptConfig['RawDataPath'] + 'IOT_' + str(ScriptConfig['CurrentYear']) + '_' + ScriptConfig['ModelType'] + '\\satellite\\F.txt'
MRIO_F_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_F = MRIO_F_raw.as_matrix()[1::,0::]
MRIO_F = MRIO_F.astype('float')

Path = ScriptConfig['RawDataPath'] + 'IOT_' + str(ScriptConfig['CurrentYear']) + '_' + ScriptConfig['ModelType'] + '\\satellite\\F_hh.txt'
MRIO_Fhh_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Fhh = MRIO_Fhh_raw.as_matrix()[1::,0::]
MRIO_Fhh = MRIO_Fhh.astype('float')


Mylog.info('<p>Build L matrix and x vector.</p>')
MRIO_L = np.linalg.inv(np.eye(DES_NoofCountries * DES_NoofIOSectors) - MRIO_A)

MRIO_X = MRIO_L.dot(MRIO_Y.sum(axis = 1))

Mylog.info('<p>Build capital-augmented A matrix. </p>')

FixedCapitalConsumption     = MRIO_F[5,:].copy()
FixedCapitalConsumption_Rel = FixedCapitalConsumption / MRIO_X
FixedCapitalConsumption_Rel[np.isnan(FixedCapitalConsumption_Rel)] = 0

FixedCapitalFormation   = MRIO_Y[:,3::7].copy()
FixedCapitalInputStruct = FixedCapitalFormation / np.tile(FixedCapitalFormation.sum(axis =0),(DES_NoofCountries * DES_NoofIndustries,1))

MRIO_A_Cap = np.zeros((MRIO_A.shape[0] + DES_NoofCountries, MRIO_A.shape[1] + DES_NoofCountries))
for m in range(0,DES_NoofCountries):
    for n in range(0,DES_NoofCountries):
        MRIO_A_Cap[m*(DES_NoofIndustries +1) : (m + 1)*(DES_NoofIndustries + 1) -1 ,n*(DES_NoofIndustries + 1) : (n+1) * (DES_NoofIndustries + 1) -1] = MRIO_A[m*DES_NoofIndustries:(m+1)*DES_NoofIndustries,n*DES_NoofIndustries:(n+1)*DES_NoofIndustries].copy()
        
# Add capital consumption and formation
for m in range(0,DES_NoofCountries): # consumption
    MRIO_A_Cap[(m + 1) * (DES_NoofIndustries + 1) -1 , m*(DES_NoofIndustries +1) : (m + 1)*(DES_NoofIndustries + 1) -1] = FixedCapitalConsumption_Rel[m*DES_NoofIndustries:(m+1)*DES_NoofIndustries]
for m in range(0,DES_NoofCountries): # formation
    for n in range(0,DES_NoofCountries):
        MRIO_A_Cap[m*(DES_NoofIndustries +1) : (m + 1)*(DES_NoofIndustries + 1) -1 , (n+1)*(DES_NoofIndustries + 1) -1] = FixedCapitalInputStruct[m*DES_NoofIndustries : (m+1)*DES_NoofIndustries,n]

MRIO_Y_Cap = np.zeros((MRIO_Y.shape[0] + DES_NoofCountries, MRIO_Y.shape[1]))
for m in range(0,DES_NoofCountries):
    MRIO_Y_Cap[m*DES_NoofIndustries +m : (m+1)*DES_NoofIndustries +m,:] = MRIO_Y[m*DES_NoofIndustries:(m+1)*DES_NoofIndustries,:].copy()
    
Mylog.info('<p>Build S matrix. </p>')
MRIO_S = np.zeros(MRIO_F.shape)
for m in range(0,MRIO_A.shape[0]):
    if MRIO_X[m] > 1: # Threshold for sector output: 1 MEUR
        MRIO_S[:,m] = MRIO_F[:,m] / MRIO_X[m]
        
MRIO_S_Cap = np.zeros((MRIO_S.shape[0], MRIO_S.shape[1] + DES_NoofCountries))
for n in range(0,DES_NoofCountries):
    MRIO_S_Cap[:,n*(DES_NoofIndustries + 1) : (n+1) * (DES_NoofIndustries + 1) -1] = MRIO_S[:,n*DES_NoofIndustries:(n+1)*DES_NoofIndustries].copy()
        
Mylog.info('<p>Build IO model. </p>')
MRIO_L_Cap = np.linalg.inv(np.eye(MRIO_A_Cap.shape[0]) - MRIO_A_Cap)


Mylog.info('<p>Save MRIO model. </p>')        
if ScriptConfig['ModelType'] == 'ixi':        

    Filestring_Matlab_out = MRIO_Paths.IOModelPath + 'EXIOBASE3.4_' + str(ScriptConfig['CurrentYear']) + '_ITC_Capital.mat'
    scipy.io.savemat(Filestring_Matlab_out, mdict={'ScriptConfig':ScriptConfig,
                                                        'EB3_S_ITC_Cap':MRIO_S_Cap,
                                                        'EB3_TableUnits':'MEUR',
                                                        'EB3_Extensions_Labels':Extensions_Codes,
                                                        'EB3_Extensions_Units':Extensions_Units,
                                                        'EB3_FDCats':DES_FD_Categories,
                                                        'EB3_L_ITC_Cap':MRIO_L_Cap,
                                                        'EB3_RegionList':DES_CountryList,
                                                        'EB3_Y_Cap':MRIO_Y_Cap,
                                                        #'EB3_A_ITC_Cap':MRIO_A_Cap,
                                                        'EB3_ProductNames163_Cap':DES_ProductNames163_Cap,
                                                        'EB3_IndustryNames163_Cap':DES_IndustryNames163_original_Cap,
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
