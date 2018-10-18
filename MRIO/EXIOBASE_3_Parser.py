# -*- coding: utf-8 -*-
"""
Created on Fri May 11 15:08:47 2018
@author: ghardadi

Edited on Thu Oct 17 2018
@author: arthur

This script takes the raw EXIObase 3 files and parses them into
numpy matrices that are then stored in a .mat binary file.
Also calulates Z and L matrices (optional)
For usage see EXIOBASE_3_parser --help
"""

#%%
import numpy as np
import scipy.io
import scipy
import pandas as pd
import os
import datetime
import argparse
import pdb
#%%

include_Z = True
def Main(args):
    
    mainPath = args.exio_dir
    subpath = 'satellite'

    #read in Y
    Path = os.path.join(mainPath,'Y.txt')
    print("Reading in Y from:\n{}".format(Path))
    MRIO_Y_raw = Read_file(Path, index_columns = [0,1], column_names=[0,1])
    MRIO_Y = MRIO_Y_raw.values
    
    #read in A
    Path = os.path.join(mainPath,'A.txt')
    print("Reading in A from:\n{}".format(Path))
    MRIO_A_raw = Read_file(Path, index_columns = [0,1], column_names=[0,1])
    MRIO_A = MRIO_A_raw.values
    
    #read in F
    Path = os.path.join(mainPath,subpath,'F.txt')
    print("Reading in F from:\n{}".format(Path))
    MRIO_F_raw = Read_file(Path, index_columns = [0], column_names=[0,1])
    MRIO_F = MRIO_F_raw.values
    
    #read in F_hh 
    Path = os.path.join(mainPath,subpath,'F_hh.txt')
    print("Reading in F_hh from:\n{}".format(Path))
    MRIO_Fhh_raw =  Read_file(Path, index_columns = [0], column_names=[0,1])
    MRIO_Fhh = MRIO_Fhh_raw.values
    MRIO_FCat= MRIO_Fhh_raw.index.values
    MRIO_FCat= MRIO_FCat[0:7]

    #read in unit
    Path = os.path.join(mainPath,subpath,'unit.txt')
    print("Reading in units from:\n{}".format(Path))
    MRIO_Funit = Read_file(Path, index_columns = [0], column_names=[0])
    MRIO_Funit = MRIO_Funit.reset_index()
    MRIO_Ftype = list(MRIO_Funit['index'])
    MRIO_Funit = list(MRIO_Funit['unit'])

    #read in industries
    Path = os.path.join(mainPath,'industries.txt')
    print("Reading in Industry names from:\n{}".format(Path))
    MRIO_Industries = Read_file(Path, index_columns = [0], column_names=[0])
    MRIO_Industries = list(MRIO_Industries['Name'])
    

    #get countries from Y
    MRIO_Country = MRIO_Y_raw.index.get_level_values('region').unique() #Take all countries in the index
    
    Nsize = MRIO_A.shape[0]
    #Calculate Leontief Inverse
    if args.Leontief == True:
        print("Calculating Leontief inverse. This may take a while..")
        I = np.identity(Nsize)
        MRIO_L = np.linalg.inv(I-MRIO_A)
        print("Done calcalating L")
    
    #Calculate total industry output x
    print("Calculating total industry output x...")
    MRIO_As = MRIO_A.sum(axis=0)
    MRIO_Fs = MRIO_F[0:9,:].sum(axis=0)
    MRIO_1s = np.ones(Nsize)
    MRIO_X = MRIO_Fs/(MRIO_1s-MRIO_As)
    print("Done calculating x")
    
    #Calculate Stressor per Industry expenditure
    print("Calculating Stressor per industry S")
    MRIO_S  = np.divide(MRIO_F, MRIO_X, where = MRIO_X!=0)#divides each row of F by X but only where X != 0 
    #(the i'th column of F i divided by the i'th element of X if the latter is not 0
    print("Done calculating S")

    #Calculate Z
    if args.include_Z == True:
        print("Calculating Z")
        MRIO_Z = MRIO_A.dot(np.diag(MRIO_X))
    
    ### Write to mat file:
    print("Saving matrices to file...")
    mdict = {'EB3_FinalDemand_Emissions':MRIO_Fhh,
             'EB3_A_ITC':MRIO_A,
             'EB3_S_ITC':MRIO_S, 
             'EB3_Y':MRIO_Y,
             'EB3_TableUnits':'MEUR',
             'EB3_Extensions':MRIO_Funit,
             'EB3_Extensions_Labels':MRIO_Ftype,
             'EB3_Extensions_Units':MRIO_Funit,
             'EB3_FDCats':MRIO_FCat,
             'EB3_IndustryNames163':MRIO_Industries,
             'EB3_ProductNames163':MRIO_Industries,
             'EB3_RegionList':MRIO_Country}

    if args.include_Z == True and args.Leontief == True:
        filestring = 'EXIOBASE_IO_incl_Z_L_Mon_49R_ITC'
        mdict['EB3_L_ITC'] = MRIO_L
        mdict['EB3_Z_ITC'] = MRIO_Z
    elif args.include_Z == True:
        filestring = 'EXIOBASE_IO_incl_Z_Mon_49R_ITC'
        mdict['EB3_Z_ITC'] = MRIO_Z
    elif args.Leontief == True:
        filestring = 'EXIOBASE_IO_incl_L_Mon_49R_ITC' 
        mdict['EB3_L_ITC'] = MRIO_L
    else:
        filestring = 'EXIOBASE_IO_Mon_49R_ITC'    
   
    outPath = Check_Output_dir(args)
    Filestring_Matlab_out = os.path.join(outPath,filestring+'_{}.mat'.format(datetime.datetime.date(datetime.datetime.now())))
    scipy.io.savemat(Filestring_Matlab_out, mdict = mdict)
    
    print("Matrices saved to: {}".format(Filestring_Matlab_out))
    print("Done {}".format(datetime.datetime.now()))

    return

def Check_Output_dir(args):
    if args.outdir:
        outPath = args.outdir
    else:
        outPath = os.path.join(args.exio_dir, 'mat_matrices')
    if not os.path.exists(outPath):
        os.makedirs(outPath)
        print("Created directory {}".format(outPath))
    return outPath

def Read_file(path, index_columns=[0,1], column_names=[0,1]):
    """
    returns data in csv file as pandas data frame

    path            path to csv file
    index_columns   list of locumns to use as index. Default [0,1]
    column_names    list of rows to use as column names. Default [0,1]
    """
    #data = pd.DataFrame.from_csv(path, sep = '\t', header=0, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error 
    #pd.DataFrame.from_csv has been depreciated in favor of pd.read_csv, main differences:
    #- `index_col` is ``0`` instead of ``None`` (take first column as index by default)
    #- `parse_dates` is ``True`` instead of ``False`` (try parsing the index as datetime by default)
    data = pd.read_csv(path, sep = '\t', header=column_names, index_col=index_columns, encoding = 'iso-8859-1' ) # standard UTF-8 encoding raises error
    return data


def ParseArgs():
    '''
    ParsArgs parser the command line options 
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-z","--Z", dest='include_Z',
                        action='store_true',
                        help="If included calculates Z matrix and saves it too")
    
    parser.add_argument("-l","--L", dest='Leontief', action='store_true',
                        help="If included calculates Leontief inverse and saves it too")
    
    parser.add_argument("-e","--exiodir", type=str, dest='exio_dir', 
                        default="/home/jakobs/data/EXIOBASE/exiobase3.4_iot_2011_pxp/IOT_2011_pxp",
                        help="Directory containing the EXIOBASE input files,\n\
                        should contain: A.txt, Y.txt, industries.txt and a \n\
                        folder satellite containing F_hh.txt, F.txt and unit.txt")
    
    parser.add_argument("-o","--outdir", type=str, dest='outdir', 
                        default=None,
                        help="Optional dir for output. Otherwise saved in subfolder in  input dir")
    


    args = parser.parse_args()
    
    print("Arguments parsed.")
    return args



if __name__ == "__main__":
    args = ParseArgs()    
    print("Parsing with the following arguments")
    for key, path in vars(args).items():
        print(key,': ', path)
    print("\n")
    Main(args)
#%%
    
