# -*- coding: utf-8 -*-
"""
Created on Fri May 11 15:08:47 2018

@author: ghardadi
"""

#%%
import numpy as np
import scipy.io
import scipy
import pandas as pd

#%%

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\Y.txt'
MRIO_Y_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Y = MRIO_Y_raw.as_matrix()[2::,1::]
MRIO_Y = MRIO_Y.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\A.txt'
MRIO_A_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_A = MRIO_A_raw.as_matrix()[2::,1::]
MRIO_A = MRIO_A.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\satellite\\F.txt'
MRIO_F_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_F = MRIO_F_raw.as_matrix()[1::,0::]
MRIO_F = MRIO_F.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\satellite\\F_hh.txt'
MRIO_Fhh_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Fhh = MRIO_Fhh_raw.as_matrix()[1::,0::]
MRIO_Fhh = MRIO_Fhh.astype('float')
MRIO_FCat= MRIO_Fhh_raw.loc['category']
MRIO_FCat= MRIO_FCat[0:7]

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\satellite\\unit.txt'
MRIO_Funit = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Funit = MRIO_Funit.astype('str')
MRIO_Funit = MRIO_Funit.reset_index()
MRIO_Ftype = list(MRIO_Funit['index'])
MRIO_Funit = list(MRIO_Funit['unit'])

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\industries.txt'
MRIO_Industries = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Industries = MRIO_Industries.astype('str')
MRIO_Industries = MRIO_Industries.reset_index()
MRIO_Industries = list(MRIO_Industries['Name'])

MRIO_Countries = list(MRIO_Y_raw)
MRIO_Country = list(MRIO_Countries[i] for i in np.arange(1,338,7))

I = np.identity(7987)

MRIO_L = np.linalg.inv(I-MRIO_A)

MRIO_As = MRIO_A.sum(axis=0)
MRIO_Fs = MRIO_F[0:9,:].sum(axis=0)
MRIO_1s = [1]*7987
MRIO_X = MRIO_Fs/(MRIO_1s-MRIO_As)

MRIO_S = np.zeros(MRIO_F.shape)
for m in range(0,MRIO_A.shape[0]):
    if MRIO_X[m] > 0: # Threshold for sector output: 0 MEUR
             MRIO_S[:,m] = MRIO_F[:,m] / MRIO_X[m]
 
Filestring_Matlab_out = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2011_ixi' + '\\satellite\\' + 'EXIOBASE3_Mon_49R_2018_06_01_ITC.mat'
scipy.io.savemat(Filestring_Matlab_out, mdict={'EB3_FinalDemand_Emissions':MRIO_Fhh,
                                               'EB3_A_ITC':MRIO_A,
                                               'EB3_S_ITC':MRIO_S,
                                               'EB3_L_ITC':MRIO_L,
                                               'EB3_Y':MRIO_Y,
                                               'EB3_TableUnits':'MEUR',
                                               'EB3_Extensions':MRIO_Funit,
                                               'EB3_Extensions_Labels':MRIO_Ftype,
                                               'EB3_Extensions_Units':MRIO_Funit,
                                               'EB3_FDCats':MRIO_FCat,
                                               'EB3_IndustryNames163':MRIO_Industries,
                                               'EB3_ProductNames163':MRIO_Industries,
                                               'EB3_RegionList':MRIO_Country})
    
#%%

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\Y.txt'
MRIO_Y_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Y = MRIO_Y_raw.as_matrix()[2::,1::]
MRIO_Y = MRIO_Y.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\A.txt'
MRIO_A_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_A = MRIO_A_raw.as_matrix()[2::,1::]
MRIO_A = MRIO_A.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\satellite\\F.txt'
MRIO_F_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_F = MRIO_F_raw.as_matrix()[1::,0::]
MRIO_F = MRIO_F.astype('float')
    
Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\satellite\\F_hh.txt'
MRIO_Fhh_raw = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Fhh = MRIO_Fhh_raw.as_matrix()[1::,0::]
MRIO_Fhh = MRIO_Fhh.astype('float')
MRIO_FCat= MRIO_Fhh_raw.loc['category']
MRIO_FCat= MRIO_FCat[0:7]

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\satellite\\unit.txt'
MRIO_Funit = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Funit = MRIO_Funit.astype('str')
MRIO_Funit = MRIO_Funit.reset_index()
MRIO_Ftype = list(MRIO_Funit['index'])
MRIO_Funit = list(MRIO_Funit['unit'])

Path = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\industries.txt'
MRIO_Industries = pd.DataFrame.from_csv(Path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
MRIO_Industries = MRIO_Industries.astype('str')
MRIO_Industries = MRIO_Industries.reset_index()
MRIO_Industries = list(MRIO_Industries['Name'])

MRIO_Countries = list(MRIO_Y_raw)
MRIO_Country = list(MRIO_Countries[i] for i in np.arange(1,338,7))

I = np.identity(7987)

MRIO_L = np.linalg.inv(I-MRIO_A)

MRIO_As = MRIO_A.sum(axis=0)
MRIO_Fs = MRIO_F[0:9,:].sum(axis=0)
MRIO_1s = [1]*7987
MRIO_X = MRIO_Fs/(MRIO_1s-MRIO_As)

MRIO_S = np.zeros(MRIO_F.shape)
for m in range(0,MRIO_A.shape[0]):
    if MRIO_X[m] > 0: # Threshold for sector output: 0 MEUR
             MRIO_S[:,m] = MRIO_F[:,m] / MRIO_X[m]
 
Filestring_Matlab_out = 'C:\\Users\\ghardadi\\EXIOBASE_3\\IOT_2007_ixi' + '\\satellite\\' + 'EXIOBASE3_Mon_49R_2018_06_01_ITC.mat'
scipy.io.savemat(Filestring_Matlab_out, mdict={'EB3_FinalDemand_Emissions':MRIO_Fhh,
                                               'EB3_A_ITC':MRIO_A,
                                               'EB3_S_ITC':MRIO_S,
                                               'EB3_L_ITC':MRIO_L,
                                               'EB3_Y':MRIO_Y,
                                               'EB3_TableUnits':'MEUR',
                                               'EB3_Extensions':MRIO_Funit,
                                               'EB3_Extensions_Labels':MRIO_Ftype,
                                               'EB3_Extensions_Units':MRIO_Funit,
                                               'EB3_FDCats':MRIO_FCat,
                                               'EB3_IndustryNames163':MRIO_Industries,
                                               'EB3_ProductNames163':MRIO_Industries,
                                               'EB3_RegionList':MRIO_Country})
    
