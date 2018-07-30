# -*- coding: utf-8 -*-
"""
Created: Mon Jun 16 2018
Last change: Mon Jun 30 2018, 10:45

@author: Gilang Hardadi
"""
# Script MRIO_Results.py
# Define version
version = str('Jul-30-2018')
#%%

################
# INTRODUCTION #
################
# This script is written in order to calculate four different income-specific environmental
# footprints of German household consumption: carbon, land use, material use and water use.
# To do so, it will import the MRIO table Exiobase 2.2 and data from a consumer survey
# that was conducted by the Federal Statistical Office of Germany.
# Within this script monetary flows on commodities from the consumer survey data will be 
# redistributed to the different Exiobase categories using an imported correspondence matrix.
# Since the consumer survey came with uncertainty information (Relative Standard Error of Mean), 
# this redistribution is done via a Monte-Carlo-Simulation to pick random values from a uniform distribution.
# The MC-Simulation will contain x iterations resulting in x different final demand vectors. 
# Thus, this script will calculate x different results for each footprint, that can be expressed 
# as Boxplots.
# Additionally, two extreme cases, namely the best and the worst case scenario will be included.
# Those scenarios consist of the highest and the lowest possible spending.
# Results will be saved in two different matrices and the following vector:
    # 1) A footprint type * iteration matrix
    # 2) A product type * iteration matrix
    # 3) A vector containing the overall amount of money spent during an iteration
# Before the start:    
# Define the number of iterations for the MC-Simulation
#iterations = 1

#%%

#########################################
# 1. Step: Import of required libraries #
#########################################
# In this step all the libraries needed within the script are imported
import os  
import sys
import logging
import xlrd, xlsxwriter
import numpy as np
import time
import datetime
import scipy.io
import scipy
import shutil   
import uuid
#%%

############################################
# 2. Step: Definition of cut out functions #
############################################
# By Stefan Pauliuk
# Definition of a funtion that allows to cut out parts of a given string
def config_string_cutout(String, Code, leftstart, rightstart): 
    # Returns substring between = and EoL for given identifier in config file
    # example: if Config_File_Line is "Data_Path_Network_1=K:\Research_Data" the function call
    # config_string_cutout(Config_File_Line,'Data_Path_Network_1','=','\n') will return 'K:\Research_Data'
    Codeindex = String.find(Code,0,len(String))
    if Codeindex == -1:
        return 'None'
    else:
        Startindex = String.find(leftstart,Codeindex,len(String)) 
        Endindex   = String.find(rightstart,Codeindex,len(String))
        return String[Startindex +1:Endindex]
#%%

########################################
# 3. Step: Configuration of the script #
########################################
# By Stefan Pauliuk
# In this step the script will be configurated be reading the configuration text and excel file
# and by importing custom functions made by Stefan Pauliuk
# Read configuration data
FolderPath = os.path.expanduser("~/PythonConfigFile.txt") ## machine-dependent but OS independent path finder
FolderFile = open(FolderPath, 'r') 
FolderText = FolderFile.read()
#Extract path names from main file
ProjectSpecs_User_Name     = config_string_cutout(FolderText,'UserName','=','\n').strip()
ProjectSpecs_Path_Main     = config_string_cutout(FolderText,'Project_Path_1','=','\n').strip()
ProjectSpecs_Name_ConFile  = config_string_cutout(FolderText,'Configuration_File_1','=','\n').strip()
ProjectSpecs_DataPath1     = config_string_cutout(FolderText,'MRIO_Model_Path','=','\n').strip()
ProjectSpecs_PackagePath1  = config_string_cutout(FolderText,'Package_Path_1','=','\n').strip()
sys.path.append(ProjectSpecs_PackagePath1)
ProjectSpecs_DataBaseUser  = config_string_cutout(FolderText,'DB_User','=','\n').strip()
ProjectSpecs_DataBasePW    = config_string_cutout(FolderText,'DB_PW','=','\n').strip()
#import packages whose location is now on the system path:    
import Utils_Pauliuk as up
# Load project-specific config file
Project_Configfile  = xlrd.open_workbook(ProjectSpecs_Path_Main + 'Calculation\\' + ProjectSpecs_Name_ConFile)
Project_Configsheet = Project_Configfile.sheet_by_name('Config')
# Naming script and defining of name specifications (e.g. date when the script was used)
Name_Script        = Project_Configsheet.cell_value(6,3)
if Name_Script != 'Footprint2011_Results': # Name of this script must equal the specified name in the Excel config file
    print('Fatal error: The name of the current script does not match to the sript name specfied in the project configuration file. Exiting the script.')
    sys.exit()
Name_Scenario      = Project_Configsheet.cell_value(5,3)
StartTime          = datetime.datetime.now()
TimeString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day) + '__' + str(StartTime.hour) + '_' + str(StartTime.minute) + '_' + str(StartTime.second)
DateString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day)
Path_Result        = ProjectSpecs_Path_Main + 'Results\\' + Name_Script + '\\' + Name_Scenario + '_' + TimeString + '\\'
# Importing information about Exiobase 2.2 from excel file
EB2_NoofCountries  = int(Project_Configsheet.cell_value(4,8))
EB2_NoofProducts   = int(Project_Configsheet.cell_value(5,8))
EB2_NoofIndustries = int(Project_Configsheet.cell_value(6,8))
EB2_NoofIOSectors  = int(Project_Configsheet.cell_value(7,8))
EB2_NoofFDCategories = int(Project_Configsheet.cell_value(8,8))
# Read control and selection parameters into dictionary
ScriptConfig = {'Scenario_Description': Project_Configsheet.cell_value(7,3)}
for m in range(10,16): # add all defined control parameters to dictionary
    ScriptConfig[Project_Configsheet.cell_value(m,1)] = Project_Configsheet.cell_value(m,3)
ScriptConfig['Current_UUID'] = str(uuid.uuid4())
# Create scenario folder
up.ensure_dir(Path_Result)
#Copy script and Config file into that folder
shutil.copy(ProjectSpecs_Path_Main + 'Calculation\\' + ProjectSpecs_Name_ConFile, Path_Result +ProjectSpecs_Name_ConFile)
shutil.copy(ProjectSpecs_Path_Main + 'Calculation\\' + Name_Script + '.py', Path_Result + Name_Script + '.py')
# Initialize logger    
[Mylog,console_log,file_log] = up.function_logger(logging.DEBUG, Name_Scenario + '_' + TimeString, Path_Result, logging.DEBUG) 
# log header and general information
Mylog.info('<html>\n<head>\n</head>\n<body bgcolor="#ffffff">\n<br>')
Mylog.info('<font "size=+5"><center><b>Script ' + Name_Script + '.py</b></center></font>')
Mylog.info('<font "size=+5"><center><b>Version: ' + version +'.</b></center></font>')
Mylog.info('<font "size=+4"> <b>Current User: ' + ProjectSpecs_User_Name + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Path: ' + ProjectSpecs_Path_Main + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Scenario: ' + Name_Scenario + '.</b></font><br>')
Mylog.info(ScriptConfig['Scenario_Description'])
Mylog.info('Unique ID of scenario run: <b>' + ScriptConfig['Current_UUID'] + '</b>')
# Start the timer
Time_Start = time.time()
Mylog.info('<font "size=+4"> <b>Start of simulation: ' + time.asctime() + '.</b></font><br>')
  
#%%

################################
# 4. Step: Import Exiobase 3.1 #
################################ 
# Now, Exiobase 3.1 will be imported. This includes the following:
    # L-Matrix containing the Leontief-Inverse
    # S-Matrix containing the emissions
    # Y-Matrix containing the final demands
    # FDE-Matrix containing the direct emissions caused by the final demands
Mylog.info('<p>Loading Exiobase 3.1 data. <br>')
MRIO_Name = ScriptConfig['DataBase'] + '_' + ScriptConfig['Layer'] + '_' + ScriptConfig['Regions']
if  MRIO_Name == 'EXIOBASE3_Mon_49R':
    Mylog.info('<p><b>Loading '+ MRIO_Name +' model from hard disc.</b><br>')
    Filestring_Matlab_in      = ProjectSpecs_DataPath1  + MRIO_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + '.mat' 
    Mylog.info('Reading '+ MRIO_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + ' model from ' + Filestring_Matlab_in)
    Mylog.info('<p>Import L-Matrix (Leontief-Inverse).<br>')
    MRIO_L = scipy.io.loadmat(Filestring_Matlab_in)['EB3_L_ITC']
    Mylog.info('<p>Import A-Matrix (Leontief).<br>')
    MRIO_A = scipy.io.loadmat(Filestring_Matlab_in)['EB3_A_ITC']
    Mylog.info('<p>Import S-Matrix (Emissions).<br>')
    MRIO_S = scipy.io.loadmat(Filestring_Matlab_in)['EB3_S_ITC']
    Mylog.info('<p>Import Y-Matrix (Final Demands).<br>')
    MRIO_Y = scipy.io.loadmat(Filestring_Matlab_in)['EB3_Y']
    Mylog.info('<p>Import FDE-Matrix (Direct Emissions from Final Demand).<br>')
    MRIO_FDE = scipy.io.loadmat(Filestring_Matlab_in)['EB3_FinalDemand_Emissions']
    Mylog.info('<p>Import the Names of Industry Sectors.<br>')
    MRIO_Ind = scipy.io.loadmat(Filestring_Matlab_in)['EB3_IndustryNames163']
    Mylog.info('<p>Import the Names of Extension Codes.<br>')
    MRIO_Ext = scipy.io.loadmat(Filestring_Matlab_in)['EB3_Extensions']
    Mylog.info('<p>Import the Names of Regions.<br>')
    MRIO_Reg = scipy.io.loadmat(Filestring_Matlab_in)['EB3_RegionList']
    # Importing numbers of parameters from Exiobase 3.1
    EB3_NoofCountries  = len(MRIO_Reg)
    EB3_NoofIndustries = len(MRIO_Ind)
    EB3_NoofFDCategories = len(MRIO_Y)
    EB3_NoofInventories = len(MRIO_Ext)

Mylog.info('<p>Loading Z-Matrix Exiobase 3.1 data. <br>')
ZMat_Name = 'ZMatrix' + '_' + ScriptConfig['Layer'] + '_' + ScriptConfig['Regions']
if  ZMat_Name == 'ZMatrix_Mon_49R':
    Mylog.info('<p><b>Loading '+ ZMat_Name +' model from hard disc.</b><br>')
    Filestring_ZMatlab_in      = ProjectSpecs_DataPath1  + ZMat_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + '.mat' 
    Mylog.info('Reading '+ ZMat_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + ' model from ' + Filestring_ZMatlab_in)
    Mylog.info('<p>Import Z-Matrix (Intermediate).<br>')
    MRIO_Z = scipy.io.loadmat(Filestring_ZMatlab_in)['EB3_Z_ITC']

#%%

############################################
# 5. Step: Import characterisation factors #
############################################
# In order to calculate the environmental footprints, characterisation factors are needed
# to convert the emissions received by S*L*y to midpoint indicators
Mylog.info('<p>Import characterisation factors to calculate midpoint indicators.<br>')
# Import excel file containing the midpoint indicator characterisation factors.
# Excel file created by Pius Zähringer based on the excel file named
# characterisation_CREEA_version2.2.2.xlsx
ImpactFile  = xlrd.open_workbook(ProjectSpecs_DataPath1 + 'Characterization_EB34.xlsx')
ImpactSheet = ImpactFile.sheet_by_name('Emissions')
ImpactCategory_Names = []
for m in range(0,36):
    ImpactCategory_Names.append(ImpactSheet.cell_value(0,m))
    
MRIO_Char = np.zeros((36,1104))
for m in range(0,36):
    for n in range(0,1104):
        MRIO_Char[m,n] = ImpactSheet.cell_value(n+1,m+1)
        
MRIO_Prod = MRIO_Ind
               
#%%

##########################################################
# 7. Step: Calculate Domestic Emissions and Resource Use #
##########################################################
# In order to calculate domestic emissions and resource use, all intermediate products and final demands
# needed in Germany are summed as domestic production demand. Then it is simply multiplied by
# characterization factors and emissions (or resource use) per spending matrix.
Mylog.info('<p>Calculate Domestic Emissions and Resources Use.<br>')

Domestic = np.zeros((1,7987))
for m in range(163*5,163*5+163):
    Domestic[0,m] = MRIO_Z[m,0:7987].sum(axis=0)+MRIO_Y[m,0:343].sum(axis=0)

CF_Domestic = (MRIO_Char[4,:].dot(MRIO_S)).dot(np.diag(Domestic[0,:])).reshape(49,163).transpose().sum(axis=1)
LF_Domestic = (MRIO_Char[8,:].dot(MRIO_S)).dot(np.diag(Domestic[0,:])).reshape(49,163).transpose().sum(axis=1)
MF_Domestic = (MRIO_Char[22,:].dot(MRIO_S)).dot(np.diag(Domestic[0,:])).reshape(49,163).transpose().sum(axis=1)
WF_Domestic = (MRIO_Char[31,:].dot(MRIO_S)).dot(np.diag(Domestic[0,:])).reshape(49,163).transpose().sum(axis=1)

CD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[4,:]).sum(axis=1)
LD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[8,:]).sum(axis=1)
MD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[22,:]).sum(axis=1)
WD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[31,:]).sum(axis=1)

Mylog.info('<p><b>Save Domestic Emissions and Resources Use. </b><br>')
# By product type
#
Result_workbook  = xlsxwriter.Workbook(Path_Result + 'Footprint_Domestic.xlsx') 
bold = Result_workbook.add_format({'bold': True})
#
# Footprints per household
#
Mylog.info('<p>Total footprint, by product<br>') 
Result_worksheet = Result_workbook.add_worksheet('Total, by product') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Domestic', bold)
Result_worksheet.write(0, 2, 'LF_Domestic', bold)
Result_worksheet.write(0, 3, 'MF_Domestic', bold)
Result_worksheet.write(0, 4, 'WF_Domestic', bold)
Result_worksheet.write(164,0, 'Direct Household', bold)
Result_worksheet.write(165,0, 'Direct NPISH', bold)
Result_worksheet.write(166,0, 'Direct Capital', bold)
Result_worksheet.write(167,0, 'Total Indirect', bold)
Result_worksheet.write(168,0, 'Total', bold)
for m in range(0,163):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, CF_Domestic[0+m]/1E6)
    Result_worksheet.write(m+1, 2, LF_Domestic[0+m])
    Result_worksheet.write(m+1, 3, MF_Domestic[0+m])
    Result_worksheet.write(m+1, 4, WF_Domestic[0+m])

for m in range(0,3):    
    Result_worksheet.write(m+164, 1, CD_EX[0+m]/1E6)
    Result_worksheet.write(m+164, 2, LD_EX[0+m])
    Result_worksheet.write(m+164, 3, MD_EX[0+m])
    Result_worksheet.write(m+164, 4, WD_EX[0+m])

Result_worksheet.write(167,1, CF_Domestic[:].sum(axis=0)/1E6)
Result_worksheet.write(167,2, LF_Domestic[:].sum(axis=0))
Result_worksheet.write(167,3, MF_Domestic[:].sum(axis=0))
Result_worksheet.write(167,4, WF_Domestic[:].sum(axis=0))

Result_worksheet.write(168,1, CF_Domestic[:].sum(axis=0)/1E6+CD_EX[:].sum(axis=0)/1E6)
Result_worksheet.write(168,2, LF_Domestic[:].sum(axis=0)+LD_EX[:].sum(axis=0))
Result_worksheet.write(168,3, MF_Domestic[:].sum(axis=0)+MD_EX[:].sum(axis=0))
Result_worksheet.write(168,4, WF_Domestic[:].sum(axis=0)+WD_EX[:].sum(axis=0))
Result_workbook.close()

#%%

################################################################
# 8. Step: Calculate Production-based Environmental Footprints #
################################################################
# In order to calculate emissions and resource use embodied in Germany production activities,
# all final demands needed from all countries made in Germany are summed as domestic 
# production demand. Then it is simply multiplied by characterization factors, emissions (or
# resource use) per spending matrix, and L-matrix (Leontief-inverse matrix).
Mylog.info('<p>Calculate Production-based Environmental Footprints.<br>')

Prod = np.zeros((1,7987))
for m in range(163*5,163*5+163):
    Prod[0,m] = MRIO_Y[m,0:343].sum(axis=0)

CF_Prod = (MRIO_Char[4,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Prod[0,:]))).reshape(49,163).transpose().sum(axis=1)
LF_Prod = (MRIO_Char[8,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Prod[0,:]))).reshape(49,163).transpose().sum(axis=1)
MF_Prod = (MRIO_Char[22,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Prod[0,:]))).reshape(49,163).transpose().sum(axis=1)
WF_Prod = (MRIO_Char[31,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Prod[0,:]))).reshape(49,163).transpose().sum(axis=1)

CD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[4,:]).sum(axis=1)
LD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[8,:]).sum(axis=1)
MD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[22,:]).sum(axis=1)
WD_EX = (MRIO_FDE[:,35:42].transpose()*MRIO_Char[31,:]).sum(axis=1)

Mylog.info('<p><b>Save Production-based Environmental Footprints. </b><br>')
# By product type
#
Result_workbook  = xlsxwriter.Workbook(Path_Result + 'Footprint_Production.xlsx') 
bold = Result_workbook.add_format({'bold': True})
#
# Footprints per household
#
Mylog.info('<p>Total footprint, by product<br>') 
Result_worksheet = Result_workbook.add_worksheet('Total, by product') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Production', bold)
Result_worksheet.write(0, 2, 'LF_Production', bold)
Result_worksheet.write(0, 3, 'MF_Production', bold)
Result_worksheet.write(0, 4, 'WF_Production', bold)
Result_worksheet.write(164,0, 'Direct Household', bold)
Result_worksheet.write(165,0, 'Direct NPISH', bold)
Result_worksheet.write(166,0, 'Direct Capital', bold)
Result_worksheet.write(167,0, 'Total Indirect', bold)
Result_worksheet.write(168,0, 'Total', bold)
for m in range(0,163):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, CF_Prod[0+m]/1E6)
    Result_worksheet.write(m+1, 2, LF_Prod[0+m])
    Result_worksheet.write(m+1, 3, MF_Prod[0+m])
    Result_worksheet.write(m+1, 4, WF_Prod[0+m])

for m in range(0,3):    
    Result_worksheet.write(m+164, 1, CD_EX[0+m]/1E6)
    Result_worksheet.write(m+164, 2, LD_EX[0+m])
    Result_worksheet.write(m+164, 3, MD_EX[0+m])
    Result_worksheet.write(m+164, 4, WD_EX[0+m])

Result_worksheet.write(167,1, CF_Prod[:].sum(axis=0)/1E6)
Result_worksheet.write(167,2, LF_Prod[:].sum(axis=0))
Result_worksheet.write(167,3, MF_Prod[:].sum(axis=0))
Result_worksheet.write(167,4, WF_Prod[:].sum(axis=0))

Result_worksheet.write(168,1, CF_Prod[:].sum(axis=0)/1E6+CD_EX[:].sum(axis=0)/1E6)
Result_worksheet.write(168,2, LF_Prod[:].sum(axis=0)+LD_EX[:].sum(axis=0))
Result_worksheet.write(168,3, MF_Prod[:].sum(axis=0)+MD_EX[:].sum(axis=0))
Result_worksheet.write(168,4, WF_Prod[:].sum(axis=0)+WD_EX[:].sum(axis=0))
Result_workbook.close()

#%%

################################################################
# 9. Step: Calculate Export-Import of Environmental Footprints #
################################################################
# In order to calculate emissions and resource use embodied in Germany export and import
# activities, all final demand from other countries produced in Germany are summed as
# export demand and final demand of Germany produced in other countries is summed
# as import demand. Then it is simply multiplied by characterization factors, emissions (or
# resource use) per spending matrix, and L-matrix (Leontief-inverse matrix).
Mylog.info('<p>Calculate Export-Import of Environmental Footprints.<br>')

Export = np.zeros((1,7987))
for m in range(163*5,163*5+163):
    Export[0,m] = MRIO_Y[m,0:35].sum(axis=0)+MRIO_Y[m,42:343].sum(axis=0)
    
Import = np.zeros((1,7987))
for m in range(0,7987):
    for n in range(163*5,163*5+163):
        Import[0,m] = MRIO_Y[m,35:42].sum(axis=0)
        Import[0,n] = 0

CF_Export = (MRIO_Char[4,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Export[0,:]))).reshape(49,163).transpose().sum(axis=1)
CF_Import = (MRIO_Char[4,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Import[0,:]))).reshape(49,163).transpose().sum(axis=1)
LF_Export = (MRIO_Char[8,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Export[0,:]))).reshape(49,163).transpose().sum(axis=1)
LF_Import = (MRIO_Char[8,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Import[0,:]))).reshape(49,163).transpose().sum(axis=1)
MF_Export = (MRIO_Char[22,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Export[0,:]))).reshape(49,163).transpose().sum(axis=1)
MF_Import = (MRIO_Char[22,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Import[0,:]))).reshape(49,163).transpose().sum(axis=1)
WF_Export = (MRIO_Char[31,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Export[0,:]))).reshape(49,163).transpose().sum(axis=1)
WF_Import = (MRIO_Char[31,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(Import[0,:]))).reshape(49,163).transpose().sum(axis=1)

Mylog.info('<p><b>Save Export Import footprints. </b><br>')
# By product type
#
Result_workbook  = xlsxwriter.Workbook(Path_Result + 'Footprint_ExportImport.xlsx') 
bold = Result_workbook.add_format({'bold': True})
#
# Footprints per household
#
Mylog.info('<p>Total footprint, by product<br>') 
Result_worksheet = Result_workbook.add_worksheet('Total, by product') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Export', bold)
Result_worksheet.write(0, 2, 'LF_Export', bold)
Result_worksheet.write(0, 3, 'MF_Export', bold)
Result_worksheet.write(0, 4, 'WF_Export', bold)
Result_worksheet.write(0, 5, 'CF_Import', bold)
Result_worksheet.write(0, 6, 'LF_Import', bold)
Result_worksheet.write(0, 7, 'MF_Import', bold)
Result_worksheet.write(0, 8, 'WF_Import', bold)
Result_worksheet.write(164,0, 'Total', bold)
for m in range(0,163):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, CF_Export[0+m]/1E6)
    Result_worksheet.write(m+1, 2, LF_Export[0+m])
    Result_worksheet.write(m+1, 3, MF_Export[0+m])
    Result_worksheet.write(m+1, 4, WF_Export[0+m])
    Result_worksheet.write(m+1, 5, CF_Import[0+m]/1E6)
    Result_worksheet.write(m+1, 6, LF_Import[0+m])
    Result_worksheet.write(m+1, 7, MF_Import[0+m])
    Result_worksheet.write(m+1, 8, WF_Import[0+m])

Result_worksheet.write(164,1, CF_Export[:].sum(axis=0)/1E6)
Result_worksheet.write(164,2, LF_Export[:].sum(axis=0))
Result_worksheet.write(164,3, MF_Export[:].sum(axis=0))
Result_worksheet.write(164,4, WF_Export[:].sum(axis=0))
Result_worksheet.write(164,5, CF_Import[:].sum(axis=0)/1E6)
Result_worksheet.write(164,6, LF_Import[:].sum(axis=0))
Result_worksheet.write(164,7, MF_Import[:].sum(axis=0))
Result_worksheet.write(164,8, WF_Import[:].sum(axis=0))
Result_workbook.close()
    
#%%

##################################################################
# 10. Step: Calculate Consumption-based Environmental Footprints #
##################################################################
# In order to calculate emissions and resource use embodied in Germany consumption activities,
# final demands needed for Germany globally are summed as domestic 
# consumption demand. Then it is simply multiplied by characterization factors, emissions (or
# resource use) per spending matrix, and L-matrix (Leontief-inverse matrix).
Mylog.info('<p>Calculate Production-based Environmental Footprints.<br>')

FD_EX = MRIO_Y[:,35:42].sum(axis=1)

CF_Cons = (MRIO_Char[4,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(FD_EX))).reshape(49,163).transpose().sum(axis=1)
LF_Cons = (MRIO_Char[8,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(FD_EX))).reshape(49,163).transpose().sum(axis=1)
MF_Cons = (MRIO_Char[22,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(FD_EX))).reshape(49,163).transpose().sum(axis=1)
WF_Cons = (MRIO_Char[31,:].dot(MRIO_S)).dot(MRIO_L.dot(np.diag(FD_EX))).reshape(49,163).transpose().sum(axis=1)

AD_EX = FD_EX.reshape(49,163).transpose().sum(axis=1)

Mylog.info('<p><b>Save Consumption-based Environmental Footprints. </b><br>')
# By product type
#
Result_workbook  = xlsxwriter.Workbook(Path_Result + 'Footprint_Consumption.xlsx') 
bold = Result_workbook.add_format({'bold': True})
#
# Footprints per household
#
Mylog.info('<p>Total footprint, by product<br>') 
Result_worksheet = Result_workbook.add_worksheet('Total, by product') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'FD_Consumption', bold)
Result_worksheet.write(0, 2, 'CF_Consumption', bold)
Result_worksheet.write(0, 3, 'LF_Consumption', bold)
Result_worksheet.write(0, 4, 'MF_Consumption', bold)
Result_worksheet.write(0, 5, 'WF_Consumption', bold)
Result_worksheet.write(0, 6, 'FD per Capita', bold)
Result_worksheet.write(0, 7, 'CF per Capita', bold)
Result_worksheet.write(0, 8, 'LF per Capita', bold)
Result_worksheet.write(0, 9, 'MF per Capita', bold)
Result_worksheet.write(0, 10, 'WF per Capita', bold)
Result_worksheet.write(164,0, 'Direct Household', bold)
Result_worksheet.write(165,0, 'Direct NPISH', bold)
Result_worksheet.write(166,0, 'Direct Capital', bold)
Result_worksheet.write(167,0, 'Total Indirect', bold)
Result_worksheet.write(168,0, 'Total', bold)
for m in range(0,163):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, AD_EX[0+m])
    Result_worksheet.write(m+1, 2, CF_Cons[0+m]/1E6)
    Result_worksheet.write(m+1, 3, LF_Cons[0+m])
    Result_worksheet.write(m+1, 4, MF_Cons[0+m])
    Result_worksheet.write(m+1, 5, WF_Cons[0+m])
    Result_worksheet.write(m+1, 6, AD_EX[0+m]/80274.98)
    Result_worksheet.write(m+1, 7, CF_Cons[0+m]/(80274.98*1E6))
    Result_worksheet.write(m+1, 8, LF_Cons[0+m]/80274.98)
    Result_worksheet.write(m+1, 9, MF_Cons[0+m]/80274.98)
    Result_worksheet.write(m+1, 10, WF_Cons[0+m]/80274.98)

for m in range(0,3):    
    Result_worksheet.write(m+164, 1, 0)
    Result_worksheet.write(m+164, 2, CD_EX[0+m]/1E6)
    Result_worksheet.write(m+164, 3, LD_EX[0+m])
    Result_worksheet.write(m+164, 4, MD_EX[0+m])
    Result_worksheet.write(m+164, 5, WD_EX[0+m])
    Result_worksheet.write(m+164, 6, 0)
    Result_worksheet.write(m+164, 7, CD_EX[0+m]/(80274.98*1E6))
    Result_worksheet.write(m+164, 8, LD_EX[0+m]/80274.98)
    Result_worksheet.write(m+164, 9, MD_EX[0+m]/80274.98)
    Result_worksheet.write(m+164, 10, WD_EX[0+m]/80274.98)

Result_worksheet.write(167,1, AD_EX[:].sum(axis=0))
Result_worksheet.write(167,2, CF_Cons[:].sum(axis=0)/1E6)
Result_worksheet.write(167,3, LF_Cons[:].sum(axis=0))
Result_worksheet.write(167,4, MF_Cons[:].sum(axis=0))
Result_worksheet.write(167,5, WF_Cons[:].sum(axis=0))
Result_worksheet.write(167,6, AD_EX[:].sum(axis=0)/80274.98)
Result_worksheet.write(167,7, CF_Cons[:].sum(axis=0)/(80274.98*1E6))
Result_worksheet.write(167,8, LF_Cons[:].sum(axis=0)/80274.98)
Result_worksheet.write(167,9, MF_Cons[:].sum(axis=0)/80274.98)
Result_worksheet.write(167,10, WF_Cons[:].sum(axis=0)/80274.98)

Result_worksheet.write(168,1, AD_EX[:].sum(axis=0))
Result_worksheet.write(168,2, (CF_Cons[:].sum(axis=0)+CD_EX[:].sum(axis=0))/1E6)
Result_worksheet.write(168,3, LF_Cons[:].sum(axis=0)+LD_EX[:].sum(axis=0))
Result_worksheet.write(168,4, MF_Cons[:].sum(axis=0)+MD_EX[:].sum(axis=0))
Result_worksheet.write(168,5, WF_Cons[:].sum(axis=0)+WD_EX[:].sum(axis=0))
Result_worksheet.write(168,6, AD_EX[:].sum(axis=0)/80274.98)
Result_worksheet.write(168,7, (CF_Cons[:].sum(axis=0)+CD_EX[:].sum(axis=0))/(80274.98*1E6))
Result_worksheet.write(168,8, (LF_Cons[:].sum(axis=0)+LD_EX[:].sum(axis=0))/80274.98)
Result_worksheet.write(168,9, (MF_Cons[:].sum(axis=0)+MD_EX[:].sum(axis=0))/80274.98)
Result_worksheet.write(168,10, (WF_Cons[:].sum(axis=0)+WD_EX[:].sum(axis=0))/80274.98)

Result_worksheet.write(170,0, 'German Population', bold)
Result_worksheet.write(170,1, 80274.98)
Result_workbook.close()

#%%



###########################
# 16. Step: Finish script #
###########################                   
Mylog.info('<br> Script is finished. Terminating logging process and closing all log files.<br>')
Time_End = time.time()
Time_Duration = Time_End - Time_Start
Mylog.info('<font "size=+4"> <b>End of simulation: ' + time.asctime() + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Duration of simulation: %.1f seconds.</b></font><br>' % Time_Duration)
logging.shutdown()
# remove all handlers from logger
root = logging.getLogger()
root.handlers = [] # required if you don't want to exit the shell
# The End