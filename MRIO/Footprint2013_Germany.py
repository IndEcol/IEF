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
if  MRIO_Name == 'EXIOBASE3_13_Mon_49R':
    Mylog.info('<p><b>Loading '+ MRIO_Name +' model from hard disc.</b><br>')
    Filestring_Matlab_in      = ProjectSpecs_DataPath1  + MRIO_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + '.mat'
    Filestring_ZMatlab_in     = ProjectSpecs_DataPath1  + 'ZMatrix_13_Mon_49R' + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + '.mat'                                                                                     
    Mylog.info('Reading '+ MRIO_Name + '_' + ScriptConfig['Datestamp'] + '_' + ScriptConfig['Construct'] + ' model from ' + Filestring_Matlab_in)
    Mylog.info('<p>Import L-Matrix (Leontief-Inverse).<br>')
    MRIO_L = scipy.io.loadmat(Filestring_Matlab_in)['EB3_L_ITC']
    Mylog.info('<p>Import S-Matrix (Emissions).<br>')
    MRIO_S = scipy.io.loadmat(Filestring_Matlab_in)['EB3_S_ITC']
    Mylog.info('<p>Import Y-Matrix (Final Demands).<br>')
    MRIO_Y = scipy.io.loadmat(Filestring_Matlab_in)['EB3_Y']
    Mylog.info('<p>Import FDE-Matrix (Direct Emissions from Final Demand).<br>')
    MRIO_FDE = scipy.io.loadmat(Filestring_Matlab_in)['EB3_FinalDemand_Emissions']
    Mylog.info('<p>Import the Names of Industry Sectors.<br>')
    MRIO_Prod = scipy.io.loadmat(Filestring_Matlab_in)['EB3_ProductNames200']
    Mylog.info('<p>Import the Names of Extension Codes.<br>')
    MRIO_Ext = scipy.io.loadmat(Filestring_Matlab_in)['EB3_Extensions_Labels']
    Mylog.info('<p>Import the Names of Regions.<br>')
    MRIO_Reg = scipy.io.loadmat(Filestring_Matlab_in)['EB3_RegionList']
    Mylog.info('<p>Import Z-Matrix (Intermediate Consumption).<br>')
    MRIO_Z = scipy.io.loadmat(Filestring_ZMatlab_in)['EB3_Z_CTC']
    
    # Importing numbers of parameters from Exiobase 3.1
    EB3_NoofCountries  = len(MRIO_Reg)
    EB3_NoofIndustries = len(MRIO_Prod)
    EB3_NoofFDCategories = len(MRIO_Y)
    EB3_NoofInventories = len(MRIO_Ext)
    
    # Selected Case Study: Environmental Footprints of Germany
    # Specify the country for which the accounts are to be calculated
    CountryNo = 5 # Note that Python indexing starts at 0! 5: Germany
    
    # Specify the number of midpoints, regions, sectors (products and industries), and final demand categories in the MRIO table:
    NoM    = 4 # number of midpoints
    NoR    = EB3_NoofCountries   # number of regions
    NoS    = EB3_NoofIndustries  # number of sectors
    NoY    = 7    # number of final demand categories per region
    NoYSel = 4 # only HH, Non-gov, gov, and GFCF  # number of final demand categories to be included in the footprint


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
ImpactFile  = xlrd.open_workbook(ProjectSpecs_DataPath1 + 'Characterization_EB36.xlsx')
ImpactSheet = ImpactFile.sheet_by_name('Emissions')
ImpactCategory_Names = []
for m in range(0,36):
    ImpactCategory_Names.append(ImpactSheet.cell_value(0,m))
    
MRIO_Char = np.zeros((36,1707))
for m in range(0,36):
    for n in range(0,1707):
        MRIO_Char[m,n] = ImpactSheet.cell_value(n+1,m+1)
        
               
#%%

# 1) total output X:
MRIO_X = MRIO_L.dot(MRIO_Y)
print(MRIO_X.shape)

# 2) total emissions f:
# 2a) determine midpoint multiplier by pre-multiplying the characterisation factors with the stressor matrix. 
# Select the midpoints that are in the scope of this work:
MRIO_C_S = MRIO_Char.dot(MRIO_S)
MRIO_C_S_CMLW = MRIO_C_S[[4,8,22,31],:]
print(MRIO_S.shape)
print(MRIO_Char.shape)
print(MRIO_C_S.shape)
print(MRIO_C_S_CMLW.shape)

# 2b) Determine midpoint by emitting industry (and region) and consuming region (and product)
MRIO_f_detail    = np.einsum('fi,iy->fiy',MRIO_C_S_CMLW,MRIO_X)
print(MRIO_f_detail.shape)

# 2c) Determine midpoint of final demand sector emissions by consuming region (and product)
MRIO_f_hh_detail = np.einsum('fs,sy->fy',MRIO_Char[[4,8,22,31],:],MRIO_FDE)
print(MRIO_f_hh_detail.shape) 

#%%

##########################################################
# 7. Step: Calculate Domestic Emissions and Resource Use #
##########################################################
# In order to calculate domestic emissions and resource use, all intermediate products and final demands
# needed in Germany are summed as domestic production demand. Then it is simply multiplied by
# characterization factors and emissions (or resource use) per spending matrix.
Mylog.info('<p>Calculate Domestic Emissions and Resources Use.<br>')

################################################################
# 9. Step: Calculate Export-Import of Environmental Footprints #
################################################################
# In order to calculate emissions and resource use embodied in Germany export and import
# activities, all final demand from other countries produced in Germany are summed as
# export demand and final demand of Germany produced in other countries is summed
# as import demand. Then it is simply multiplied by characterization factors, emissions (or
# resource use) per spending matrix, and L-matrix (Leontief-inverse matrix).
Mylog.info('<p>Calculate Export-Import of Environmental Footprints.<br>')

# 1) direct emissions of final demand sectors
FP_direct_f = MRIO_f_hh_detail[:,NoY * CountryNo : NoY * CountryNo + NoYSel].sum(axis =1) # Selected midpoints
print(FP_direct_f.shape)

# 2) domestic emissions for domestic consumption:
FP_dom_dom  = MRIO_f_detail[:,NoS * CountryNo : NoS * CountryNo + NoS,NoY * CountryNo : NoY * CountryNo + NoYSel].sum(axis =2) # Selected midpoints x industries x regions
print(FP_dom_dom.shape)

# 3) Consumption-based emissions
FP_cons   = MRIO_f_detail[:,:,NoY * CountryNo : NoY * CountryNo + NoYSel].sum(axis =2) # Selected midpoints x industries x regions
print(FP_cons.shape)
FP_cons_agg1 = np.zeros((NoM,NoS))
for m in range(0,NoR):
    FP_cons_agg1 = FP_cons_agg1 + FP_cons[:,NoS * m : NoS * m + NoS]

# 4) import-related emissions
FP_imp_agg1 = FP_cons_agg1 - FP_dom_dom

# 5) Territorial or production-based emissions
FP_terr_agg1 = np.zeros((NoM,NoS))
for m in range(0,NoR):
    FP_terr_agg1 = FP_terr_agg1 + MRIO_f_detail[:,NoS * CountryNo : NoS * CountryNo + NoS,NoY * m : NoY * m + NoYSel].sum(axis =2)

# 6) Export-related emissions
FP_exp_agg1 = FP_terr_agg1 - FP_dom_dom

# 7) Consumption-based emissions
FP_cons2 = np.zeros((NoM,NoR*NoS))
for m in range (0,4):
    FP_cons2 [m,:] = MRIO_C_S_CMLW[m,:].dot(MRIO_L).dot(np.diag((MRIO_Y)[:,NoY * CountryNo : NoY * CountryNo + NoYSel].sum(axis=1))) # Selected midpoints x industries x regions
print(FP_cons2.shape)

FP_cons2_agg1 = np.zeros((NoM,NoR,NoS))
for m in range(0,NoM):
    FP_cons2_agg1[m,:,:] = FP_cons2[m,:].reshape(NoM,NoS)

FP_cons2_agg1 = FP_cons2_agg1.sum(axis=1)

    
#%%

##################################################################
# 10. Step: Calculate Consumption-based Environmental Footprints #
##################################################################
# In order to calculate emissions and resource use embodied in Germany consumption activities,
# final demands needed for Germany globally are summed as domestic 
# consumption demand. Then it is simply multiplied by characterization factors, emissions (or
# resource use) per spending matrix, and L-matrix (Leontief-inverse matrix).

Mylog.info('<p><b>Save PB-, Export, Import, and CB- Environmental Footprints. </b><br>')
# By product type
#
Result_workbook  = xlsxwriter.Workbook(Path_Result + 'Environmental_Footprint.xlsx') 
bold = Result_workbook.add_format({'bold': True})
#
# Footprints per household
#
Mylog.info('<p>Production-Based Emissions, by industry<br>') 
Result_worksheet = Result_workbook.add_worksheet('Production-Based') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Domestic', bold)
Result_worksheet.write(0, 2, 'LF_Domestic', bold)
Result_worksheet.write(0, 3, 'MF_Domestic', bold)
Result_worksheet.write(0, 4, 'WF_Domestic', bold)
Result_worksheet.write(201,0, 'Direct Emission', bold)
Result_worksheet.write(204,0, 'Total Indirect', bold)
Result_worksheet.write(205,0, 'Total', bold)
for m in range(0,200):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, FP_terr_agg1[0,0+m]/1E6)
    Result_worksheet.write(m+1, 2, FP_terr_agg1[1,0+m])
    Result_worksheet.write(m+1, 3, FP_terr_agg1[2,0+m])
    Result_worksheet.write(m+1, 4, FP_terr_agg1[3,0+m])
   
Result_worksheet.write(201, 1, FP_direct_f[0,]/1E6)
Result_worksheet.write(201, 2, FP_direct_f[1,])
Result_worksheet.write(201, 3, FP_direct_f[2,])
Result_worksheet.write(201, 4, FP_direct_f[3,])

Result_worksheet.write(204,1, FP_terr_agg1[0,:].sum(axis=0)/1E6)
Result_worksheet.write(204,2, FP_terr_agg1[1,:].sum(axis=0))
Result_worksheet.write(204,3, FP_terr_agg1[2,:].sum(axis=0))
Result_worksheet.write(204,4, FP_terr_agg1[3,:].sum(axis=0))

Result_worksheet.write(205,1, FP_terr_agg1[0,:].sum(axis=0)/1E6+FP_direct_f[0,]/1E6)
Result_worksheet.write(205,2, FP_terr_agg1[1,:].sum(axis=0)+FP_direct_f[1,])
Result_worksheet.write(205,3, FP_terr_agg1[2,:].sum(axis=0)+FP_direct_f[2,])
Result_worksheet.write(205,4, FP_terr_agg1[3,:].sum(axis=0)+FP_direct_f[3,])

Mylog.info('<p>Traded Emissions, by industry<br>') 
Result_worksheet = Result_workbook.add_worksheet('Export-Import') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Export', bold)
Result_worksheet.write(0, 2, 'LF_Export', bold)
Result_worksheet.write(0, 3, 'MF_Export', bold)
Result_worksheet.write(0, 4, 'WF_Export', bold)
Result_worksheet.write(0, 5, 'CF_Import', bold)
Result_worksheet.write(0, 6, 'LF_Import', bold)
Result_worksheet.write(0, 7, 'MF_Import', bold)
Result_worksheet.write(0, 8, 'WF_Import', bold)
Result_worksheet.write(201,0, 'Total', bold)
for m in range(0,200):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, FP_exp_agg1[0,0+m]/1E6)
    Result_worksheet.write(m+1, 2, FP_exp_agg1[1,0+m])
    Result_worksheet.write(m+1, 3, FP_exp_agg1[2,0+m])
    Result_worksheet.write(m+1, 4, FP_exp_agg1[3,0+m])
    Result_worksheet.write(m+1, 5, FP_imp_agg1[0,0+m]/1E6)
    Result_worksheet.write(m+1, 6, FP_imp_agg1[1,0+m])
    Result_worksheet.write(m+1, 7, FP_imp_agg1[2,0+m])
    Result_worksheet.write(m+1, 8, FP_imp_agg1[3,0+m])

Result_worksheet.write(201,1, FP_exp_agg1[0,:].sum(axis=0)/1E6)
Result_worksheet.write(201,2, FP_exp_agg1[1,:].sum(axis=0))
Result_worksheet.write(201,3, FP_exp_agg1[2,:].sum(axis=0))
Result_worksheet.write(201,4, FP_exp_agg1[3,:].sum(axis=0))
Result_worksheet.write(201,5, FP_imp_agg1[0,:].sum(axis=0)/1E6)
Result_worksheet.write(201,6, FP_imp_agg1[1,:].sum(axis=0))
Result_worksheet.write(201,7, FP_imp_agg1[2,:].sum(axis=0))
Result_worksheet.write(201,8, FP_imp_agg1[3,:].sum(axis=0))

Mylog.info('<p>Total footprint, by industry<br>') 
Result_worksheet = Result_workbook.add_worksheet('Consumption-Based, by Industry') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Consumption', bold)
Result_worksheet.write(0, 2, 'LF_Consumption', bold)
Result_worksheet.write(0, 3, 'MF_Consumption', bold)
Result_worksheet.write(0, 4, 'WF_Consumption', bold)
Result_worksheet.write(0, 5, 'CF per Capita', bold)
Result_worksheet.write(0, 6, 'LF per Capita', bold)
Result_worksheet.write(0, 7, 'MF per Capita', bold)
Result_worksheet.write(0, 8, 'WF per Capita', bold)
Result_worksheet.write(201,0, 'Direct Emission', bold)
Result_worksheet.write(204,0, 'Total Indirect', bold)
Result_worksheet.write(205,0, 'Total', bold)
for m in range(0,200):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, FP_cons_agg1[0,0+m]/1E6)
    Result_worksheet.write(m+1, 2, FP_cons_agg1[1,0+m])
    Result_worksheet.write(m+1, 3, FP_cons_agg1[2,0+m])
    Result_worksheet.write(m+1, 4, FP_cons_agg1[3,0+m])
    Result_worksheet.write(m+1, 5, FP_cons_agg1[0,0+m]/(80274.98*1E6))
    Result_worksheet.write(m+1, 6, FP_cons_agg1[1,0+m]/80274.98)
    Result_worksheet.write(m+1, 7, FP_cons_agg1[2,0+m]/80274.98)
    Result_worksheet.write(m+1, 8, FP_cons_agg1[3,0+m]/80274.98)

    Result_worksheet.write(201, 1, FP_direct_f[0,]/1E6)
    Result_worksheet.write(201, 2, FP_direct_f[1,])
    Result_worksheet.write(201, 3, FP_direct_f[2,])
    Result_worksheet.write(201, 4, FP_direct_f[3,])
    Result_worksheet.write(201, 5, FP_direct_f[0,]/(80274.98*1E6))
    Result_worksheet.write(201, 6, FP_direct_f[1,]/80274.98)
    Result_worksheet.write(201, 7, FP_direct_f[2,]/80274.98)
    Result_worksheet.write(201, 8, FP_direct_f[3,]/80274.98)

Result_worksheet.write(204,1, FP_cons_agg1[0,:].sum(axis=0)/1E6)
Result_worksheet.write(204,2, FP_cons_agg1[1,:].sum(axis=0))
Result_worksheet.write(204,3, FP_cons_agg1[2,:].sum(axis=0))
Result_worksheet.write(204,4, FP_cons_agg1[3,:].sum(axis=0))
Result_worksheet.write(204,5, FP_cons_agg1[0,:].sum(axis=0)/(80274.98*1E6))
Result_worksheet.write(204,6, FP_cons_agg1[1,:].sum(axis=0)/80274.98)
Result_worksheet.write(204,7, FP_cons_agg1[2,:].sum(axis=0)/80274.98)
Result_worksheet.write(204,8, FP_cons_agg1[3,:].sum(axis=0)/80274.98)

Result_worksheet.write(205,1, (FP_cons_agg1[0,:].sum(axis=0)+FP_direct_f[0,])/1E6)
Result_worksheet.write(205,2, FP_cons_agg1[1,:].sum(axis=0)+FP_direct_f[1,])
Result_worksheet.write(205,3, FP_cons_agg1[2,:].sum(axis=0)+FP_direct_f[2,])
Result_worksheet.write(205,4, FP_cons_agg1[3,:].sum(axis=0)+FP_direct_f[3,])
Result_worksheet.write(205,5, (FP_cons_agg1[0,:].sum(axis=0)+FP_direct_f[0,])/(80274.98*1E6))
Result_worksheet.write(205,6, (FP_cons_agg1[1,:].sum(axis=0)+FP_direct_f[1,])/80274.98)
Result_worksheet.write(205,7, (FP_cons_agg1[2,:].sum(axis=0)+FP_direct_f[2,])/80274.98)
Result_worksheet.write(205,8, (FP_cons_agg1[3,:].sum(axis=0)+FP_direct_f[3,])/80274.98)

Result_worksheet.write(207,0, 'German Population', bold)
Result_worksheet.write(207,1, 80274.98)

Mylog.info('<p>Total footprint, by product<br>') 
Result_worksheet = Result_workbook.add_worksheet('Consumption-Based, by Products') 
Result_worksheet.write(0, 0, 'Product Type', bold)
Result_worksheet.write(0, 1, 'CF_Consumption', bold)
Result_worksheet.write(0, 2, 'LF_Consumption', bold)
Result_worksheet.write(0, 3, 'MF_Consumption', bold)
Result_worksheet.write(0, 4, 'WF_Consumption', bold)
Result_worksheet.write(0, 5, 'CF per Capita', bold)
Result_worksheet.write(0, 6, 'LF per Capita', bold)
Result_worksheet.write(0, 7, 'MF per Capita', bold)
Result_worksheet.write(0, 8, 'WF per Capita', bold)
Result_worksheet.write(201,0, 'Direct Emission', bold)
Result_worksheet.write(204,0, 'Total Indirect', bold)
Result_worksheet.write(205,0, 'Total', bold)
for m in range(0,200):    
    Result_worksheet.write(m+1, 0, MRIO_Prod[0+m])
    Result_worksheet.write(m+1, 1, FP_cons2_agg1[0,0+m]/1E6)
    Result_worksheet.write(m+1, 2, FP_cons2_agg1[1,0+m])
    Result_worksheet.write(m+1, 3, FP_cons2_agg1[2,0+m])
    Result_worksheet.write(m+1, 4, FP_cons2_agg1[3,0+m])
    Result_worksheet.write(m+1, 5, FP_cons2_agg1[0,0+m]/(80274.98*1E6))
    Result_worksheet.write(m+1, 6, FP_cons2_agg1[1,0+m]/80274.98)
    Result_worksheet.write(m+1, 7, FP_cons2_agg1[2,0+m]/80274.98)
    Result_worksheet.write(m+1, 8, FP_cons2_agg1[3,0+m]/80274.98)

    Result_worksheet.write(201, 1, FP_direct_f[0,]/1E6)
    Result_worksheet.write(201, 2, FP_direct_f[1,])
    Result_worksheet.write(201, 3, FP_direct_f[2,])
    Result_worksheet.write(201, 4, FP_direct_f[3,])
    Result_worksheet.write(201, 5, FP_direct_f[0,]/(80274.98*1E6))
    Result_worksheet.write(201, 6, FP_direct_f[1,]/80274.98)
    Result_worksheet.write(201, 7, FP_direct_f[2,]/80274.98)
    Result_worksheet.write(201, 8, FP_direct_f[3,]/80274.98)

Result_worksheet.write(204,1, FP_cons2_agg1[0,:].sum(axis=0)/1E6)
Result_worksheet.write(204,2, FP_cons2_agg1[1,:].sum(axis=0))
Result_worksheet.write(204,3, FP_cons2_agg1[2,:].sum(axis=0))
Result_worksheet.write(204,4, FP_cons2_agg1[3,:].sum(axis=0))
Result_worksheet.write(204,5, FP_cons2_agg1[0,:].sum(axis=0)/(80274.98*1E6))
Result_worksheet.write(204,6, FP_cons2_agg1[1,:].sum(axis=0)/80274.98)
Result_worksheet.write(204,7, FP_cons2_agg1[2,:].sum(axis=0)/80274.98)
Result_worksheet.write(204,8, FP_cons2_agg1[3,:].sum(axis=0)/80274.98)

Result_worksheet.write(205,1, (FP_cons2_agg1[0,:].sum(axis=0)+FP_direct_f[0,])/1E6)
Result_worksheet.write(205,2, FP_cons2_agg1[1,:].sum(axis=0)+FP_direct_f[1,])
Result_worksheet.write(205,3, FP_cons2_agg1[2,:].sum(axis=0)+FP_direct_f[2,])
Result_worksheet.write(205,4, FP_cons2_agg1[3,:].sum(axis=0)+FP_direct_f[3,])
Result_worksheet.write(205,5, (FP_cons2_agg1[0,:].sum(axis=0)+FP_direct_f[0,])/(80274.98*1E6))
Result_worksheet.write(205,6, (FP_cons2_agg1[1,:].sum(axis=0)+FP_direct_f[1,])/80274.98)
Result_worksheet.write(205,7, (FP_cons2_agg1[2,:].sum(axis=0)+FP_direct_f[2,])/80274.98)
Result_worksheet.write(205,8, (FP_cons2_agg1[3,:].sum(axis=0)+FP_direct_f[3,])/80274.98)

Result_worksheet.write(207,0, 'German Population', bold)
Result_worksheet.write(207,1, 80274.98)

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