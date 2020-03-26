#!/usr/bin/env python

'''This script takes the data output from CreateMatFiles.py and calculates
the footprint time series for all countries.

Date: March 18 2020
Author: Arthur Jakobs
Affiliation: Industrial Ecology Freiburg'''


import os
from scipy.io import loadmat
import pandas as pd
import argparse
import time
import getpass
import numpy as np


def Footprints(args):
    """Calculates footprints per FD category from the time series files."""

    maindir = args.exio_dir
    # Get the folder names for the different years.
    data_files = GetSubDirs(maindir)
    data_files = [x for x in data_files if x.endswith('.mat')]
    data_files.sort()  # sort for right order

    # folder in the directory, such as the outdir
    # Create output directory
    outPath = Check_Output_dir(args)
    # Create a timestamp file with parameters:
    with open(os.path.join(outPath, 'Timestamp_parameters.txt'), 'w') as fh:
        fh.write('Date and Time: {}\n'.format(time.ctime()))
        fh.write('Author: {}\n'.format(args.author))
        fh.write('Input Directory: {}\n'.format(args.exio_dir))
        fh.write('Output directory given was: {}\n'.format(args.outdir))

    # Only the first 4 Final demand categories are needed: 'Final consumption expenditure by households',
    # 'Final consumption expenditure by non-profit organisations serving households (NPISH)',
    # 'Final consumption expenditure by government',
    # 'Gross fixed capital formation                                                       '
    FD_indices = np.array([np.arange(0,343,7),np.arange(1,343,7),np.arange(2,343,7),np.arange(3,343,7)]).T.flatten()

    for i,file in enumerate(data_files):

        data = Read_Data(file)
        print('Year',data['year'])
        N_regions = len(data['Regions'])
        FD_by_country = data['Y'][:,FD_indices].reshape(data['Y'].shape[0],49,4).sum(axis=2)
        DE_by_country = data['Direct_Emissions'][:,FD_indices].reshape(
                                                                    data['Direct_Emissions'].shape[0],49,4).sum(axis=2)
        FD_total = data['Y'][:,FD_indices].sum(axis=1)
        footprints = np.empty((N_regions, data['S'].shape[0], data['L'].shape[1]))
        print('Calculating consumption based footprints...')
        for country_index in range(N_regions):
            footprints[country_index,:,:] = CalFootprints(np.nan_to_num(data['S']),data['L'],FD_by_country[:,country_index])
        print('Calculating territorial footprints...')
        footprints_total = CalFootprints(np.nan_to_num(data['S']),data['L'],FD_total)
        N_prod = len(data['productNames'])
        footprints_dom_import = np.zeros((N_regions, data['S'].shape[0], 2))
        footprints_ter = np.zeros((N_regions,data['S'].shape[0]))
        for t in range(N_regions):
            footprints_dom_import[t, :, :] = np.vstack((footprints[t, :, t * N_prod:t * N_prod + N_prod].sum(axis=1),
                                                  footprints[t, :, :t * N_prod].sum(axis=1) +\
                                                  footprints[t, :, t * N_prod + N_prod:].sum(axis=1))).T
            footprints_ter[t,:] = footprints_total[:, t * N_prod:t * N_prod + N_prod].sum(axis=1)
        footprints_ter += DE_by_country.T  # Direct Emissions also are territorial
        # now stack them together
        footprints_dom_import = np.dstack((footprints_dom_import, DE_by_country.T, footprints_ter))
        if i==0:  # if the first year, create a new data frame with multi_index for country, emisison, and type.
            mi = pd.MultiIndex.from_product([data['Regions'], data['Emission_Categories'],
                                             ['Domestic', 'Abroad', 'Direct', 'Territorial']])
            time_series_df = pd.DataFrame(data=footprints_dom_import.flatten(), index=mi, columns=[data['year'][0]])
            time_series_df.index.names = ['Region', 'Emission', 'Type']
        else:  # add just the current year info
            time_series_df[data['year'][0]] = footprints_dom_import.flatten()

    print(time_series_df)
    time_series_df.reset_index(inplace=True)
    # Remove trailing white spaces from Emissions column
    time_series_df['Emission'] = time_series_df['Emission'].str.strip()
    print(time_series_df.columns)
    outFilePath = os.path.join(outPath,'TimeSeries.feather')
    print('Writing data frame to {}'.format(outFilePath))
    time_series_df.to_feather(outFilePath)



    print("\n Done {}\n".format(time.ctime()))
    return


def CalFootprints(S,L,Y):
    '''This function performs the total footprint calculation for a given
    Leontief Inverse matrix, Final demand Vector and Stressor matrix.
    L: Leontief Inverse Matrix
    Y: Final Demand Vector
    S: Stressor Matrix'''
    # split out the multiplication because dot is fast, but using np.diag
    # is very very slow einsum in this case is much faster
    x = L.dot(Y)
    footprints = np.einsum('ij,j->ij',S,x)
    return footprints



def Check_Output_dir(args):
    """Check if output dir was given in arguments or make it if not."""
    if args.outdir:
        outPath = args.outdir
    else:
        outPath = os.path.join(args.exio_dir, 'feather_file')
    if not os.path.exists(outPath):
        os.makedirs(outPath)
        print("Created directory {}".format(outPath))
    return outPath


def Read_Data(file):
    """Read in the matfiles and return the contained dictionary"""
    print('Reading in data from {}'.format(file))
    data = loadmat(file)
    return data



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
                        #default="/media/jakobs/IEF Backups Arth/EB36/constant_prices/mat_matrices/",
                        default="/home/jakobs/data/PlanetaryBoundariesGroupWork/current_price/",
                        help="Directory containing the time series mat files for EXIOBASE.")

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
    print("Running '{}' with the following arguments".format(Footprints.__name__))
    for key, path in vars(args).items():
        print(key, ': ', path)
    print("\n")
    Footprints(args)
    t1 = time.time()
    dt = t1-t0
    print("Total wall clock time was {} hours, {} minutes and {:.1f} seconds".format(dt//3600, dt%3600//60, dt%60))
