#!/usr/bin/env python

"""This script takes raw csv input from the EXOIBASE data
as provided by Simon Schulte and turns them into binary file dictionaries
per year in the matlab binary file format .mat

Date: March 17 2020
Author: Arthur Jakobs
Affiliation: Industrial Ecology Freiburg

"""


import os
from scipy.io import savemat
import pandas as pd
import argparse
import time
import getpass
import datatable as dt


def MakeDataDicts(args):
    """This function reads the constant price EXIOBASE data and
    creates a time series of binary .mat files containing dictionaries
    of with the relevant information for footprint calculation.
    The A and Z matrices are not included. This functionality could
    be added later on"""

    maindir = args.exio_dir
    subpath = 'constant_prices'
    # Get the folder names for the different years.
    data_dirs = GetSubDirs(os.path.join(maindir, subpath))
    data_dirs.sort()  # sort for right order

    year_dirs = [os.path.basename(x) for x in data_dirs]
    year_dirs = [x for x in year_dirs if len(x.split('_')) == 3]  # this check is in case there is another
                                                                  # folder in the directory, such as the outdir
    # Create output directory
    outPath = Check_Output_dir(args)
    # Create a timestamp file with parameters:
    with open(os.path.join(outPath, 'Timestamp_parameters.txt'), 'w') as fh:
        fh.write('Date and Time: {}\n'.format(time.ctime()))
        fh.write('Author: {}\n'.format(args.author))
        fh.write('Input Directory: {}\n'.format(args.exio_dir))
        fh.write('Output directory given was: {}\n'.format(args.outdir))



    for year_dir,data_dir in zip(year_dirs,data_dirs):
        print('Processing year {}'.format(year_dir.split('_')[1]))
        x,L,S,Y = Read_Data(data_dir)  # should be 2011
        #x,L,S,Y = 0,0,0,0
        Final_Demand_Categories, Emission_Categories, \
        Direct_Emissions, Regions, productNames, productCodes, \
        Emission_Units = Get_Direct_emission_data(maindir, year_dir)
        dict = {'year':year_dir.split('_')[1],
                'time_stamp':time.ctime(),
                'L':L,
                'S':S,
                'x':x,
                'Y':Y,
                'Direct_Emissions':Direct_Emissions,
                'Final_Demand_Categories':Final_Demand_Categories,
                'Emission_Categories':Emission_Categories,
                'Regions':Regions,
                'productNames':productNames,
                'productCodes':productCodes,
                'Emission_Units':Emission_Units
                }

        print('Writing matrices as dictionary...')
        filestring = 'exiobase_constant_price_{}.mat'.format(year_dir.split('_')[1])
        Filestring_Matlab_out = os.path.join(outPath, filestring)
        savemat(Filestring_Matlab_out, mdict=dict)

        print("Matrices saved to: {}".format(Filestring_Matlab_out))
    print("\n Done {}\n".format(time.ctime()))
    return


def Check_Output_dir(args):
    """Check if output dir was given in arguments or make it if not."""
    if args.outdir:
        outPath = args.outdir
    else:
        outPath = os.path.join(args.exio_dir, 'constant_prices', 'mat_matrices')
    if not os.path.exists(outPath):
        os.makedirs(outPath)
        print("Created directory {}".format(outPath))
    return outPath


def Read_Data(dir):
    """Read in the constant price data from the csv tables.
    (These do not contain headers or row indices at this point)"""
    #data_files = GetSubDirs(dir)
    #data_files.sort()
    print('Reading in L...')
    L = dt.fread(os.path.join(dir, 'L.txt'), sep=',', header=None).to_numpy()
    print('Reading in S...')
    S = dt.fread(os.path.join(dir, 'S.txt'), sep=',', header=None).to_numpy()
    print('Reading in Y...')
    Y = dt.fread(os.path.join(dir, 'Y.txt'), sep=',', header=None).to_numpy()
    print('Reading in x...')
    x = dt.fread(os.path.join(dir, 'x.txt'), sep=',', header=None).to_numpy()
    return x,L,S,Y

def Get_Direct_emission_data(datadir, subdir):
    """Read in the Direct emission data as well as the
    metadata such as product names etc."""
    satellite_path = os.path.join(datadir,subdir,'satellite')
    F_hh = pd.read_csv(os.path.join(satellite_path, 'F_hh.txt'), sep = '\t', index_col = [0], header=[0,1],
                       skiprows=lambda x: x in range(2,25), encoding='iso-8859-1')  # exclude va added rows 3-25
    Final_Demand_Categories = F_hh.columns.get_level_values(1).unique().tolist()
    Emission_Categories = F_hh.index.tolist()
    Direct_Emissions = F_hh.values
    Regions = F_hh.columns.get_level_values(0).unique().tolist()

    units = pd.read_csv(os.path.join(satellite_path, 'unit.txt'), sep='\t', header=[0], index_col=[0],
                        skiprows=lambda x: x in range(1,24))  # exclude Value Added rows 2-24
    Emission_Units = units.unit.tolist()

    products = pd.read_csv(os.path.join(datadir, subdir, 'products.txt'), sep='\t', index_col=[0], header=[0])
    productNames = products.Name.tolist()
    productCodes = products.CodeNr.tolist()

    return Final_Demand_Categories, Emission_Categories,\
           Direct_Emissions, Regions, productNames, productCodes,\
           Emission_Units


def GetSubDirs(main_dir):
    """Return a list of subdirectories in the given directory"""
    dirlist = os.listdir(main_dir)
    return [os.path.join(main_dir,dir) for dir in dirlist]


def ParseArgs():
    '''
    ParsArgs parser the command line options
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, dest='exio_dir',
                        default="/media/jakobs/IEF Backups Arth/EB36/",
                        help="Directory containing the time series for EXIOBASE including\n\
                        a constant price folder. The folders are structered as provided by Simon.")

    parser.add_argument("-o", "--outdir", type=str, dest='outdir',
                        default=None,
                        help="Optional dir for output. Otherwise saved in subfolder in  input dir")
    parser.add_argument("-a", "--author", type=str, dest="author", default=getpass.getuser(),
                        help="Give the author name of the person running the script. Default is computer user.")

    args = parser.parse_args()

    print("Arguments parsed.")
    return args


if __name__ == "__main__":
    t0 = time.time()
    args = ParseArgs()
    print("Running '{}' with the following arguments".format(MakeDataDicts.__name__))
    for key, path in vars(args).items():
        print(key, ': ', path)
    print("\n")
    MakeDataDicts(args)
    t1 = time.time()
    dt = t1-t0
    print("Total wall clock time was {} hours, {} minutes and {:.1f} seconds".format(dt//3600, dt%3600//60, dt%60))
