import pandas as pd
#import numpy as np
import time
import matplotlib.pyplot as plt
import os
import seaborn as sns
from matplotlib import rc
sns.set()
#rc('font',**{'family':'DejaVu Sans', 'size':18})
#rc('text', usetex=True)
#import matplotlib.cm as colormaps
import argparse

def BarPlot(args):
    """Makes a stacked bar plot of the consumption and territorial footprints.
    Only plots direct CO2 emissions but will add option to plot midpoints and other footprints too."""

    if not args.datafile:
        print('Please give data file as argument. Use --help flag to see help on use of script\n')
        return 0

    df = pd.read_feather(args.datafile)
    df.set_index(['Region','Emission','Type'], inplace=True)

    data_name = os.path.dirname(args.datafile).split('/')[-2]


    fig, axes = plt.subplots(nrows=7, ncols=7, figsize=(70, 70), dpi=100)
    # axes = fig.subplots(7,7)
    for i, (ax, country) in enumerate(zip(axes.flatten(), df.reset_index()['Region'].unique())):
        # ax2 = ax.twinx()

        if i == 2:
            df.loc[(country, 'CO2 - combustion - air', ['Domestic', 'Abroad', 'Direct'])].T.plot(kind='bar',
                                                                                                     width=0.4,
                                                                                                     stacked=True,
                                                                                                     ax=ax, position=0)
            df.loc[(country, 'CO2 - combustion - air', 'Territorial')].T.plot(kind='bar', stacked=True, ax=ax,
                                                                                  width=0.4, position=1, color='gray',
                                                                                  alpha=0.6)
            ax.legend(['Domestic', 'Abroad', 'Direct', 'Territorial'], frameon=False, loc=2)
        else:
            df.loc[(country, 'CO2 - combustion - air', ['Domestic', 'Abroad', 'Direct'])].T.plot(kind='bar',
                                                                                                     width=0.4,
                                                                                                     stacked=True,
                                                                                                     ax=ax, position=0,
                                                                                                     legend=False)
            df.loc[(country, 'CO2 - combustion - air', 'Territorial')].T.plot(kind='bar', stacked=True, ax=ax,
                                                                                  width=0.4, position=1, color='gray',
                                                                                  alpha=0.6, legend=False)

        # ylim1 = ax.get_ylim()
        # ylim2 = ax2.get_ylim()
        # ylim = (min(ylim1[0],ylim2[0]), max(ylim1[1],ylim2[1]))
        # ax.set_ylim(ylim)
        # ax2.set_ylim(ylim)
        ax.tick_params(axis='both', which='both', labelsize=12, labelbottom=True)
        ax.set_title(r'{} CO2 emissions'.format(country))
        ax.set_xlabel('Year')
        # ax2.set_xlabel('Year')
        ax.set_ylabel(r'CO2 emissions [kg CO2]')
        xticks = ax.get_xticks()
        ax.set_xticks(xticks)
        # ax2.set_ylabel(r'Territorial CO2 emissions [kg CO2]')
    fig.suptitle(r'Time Series {}'.format(data_name))
    if args.outfile:
        outPath = args.outfile
    else:
        outPath = '/home/jakobs/Documents/IndEcol/Plots/PlanetaryBoundaries/TimeseriesCO2_49regions_{}.png'.format(
                                                                                                            data_name)
    if not os.path.exists(os.path.dirname(outPath)):
        os.makedirs(os.path.dirname(outPath))
        print("Created directory {}".format(os.path.dir(outPath)))
    fig.savefig(outPath)
    print('Saved figure to {}'.format(outPath))
    if args.show_plot:
        plt.show()
    plt.clf()


    return 0




def ParseArgs():
    '''
    ParsArgs parser the command line options
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--datafile", type=str, dest='datafile',
                        default=None,
                        help="Path to feather file with data frame as produced by Footprints.py")

    parser.add_argument("-o", "--outfile", type=str, dest='outfile',
                        default=None,
                        help="Optional filepath for output. Otherwise saved as figure_type_{date}"
                             "in subdir 'plots' in input dir")
    parser.add_argument("-s", "--show", action="store_true", dest="show_plot",
                        help="If passed it will show the plot, else only save the figure.")
    args = parser.parse_args()

    print("Arguments parsed.")
    return args


if __name__ == "__main__":
    t0 = time.time()
    args = ParseArgs()
    print("Running '{}' with the following arguments".format(BarPlot.__name__))
    for key, path in vars(args).items():
        print(key, ': ', path)
    print("\n")
    BarPlot(args)
    t1 = time.time()
    dt = t1-t0
    print("Total wall clock time was {} hours, {} minutes and {:.1f} seconds".format(dt//3600, dt%3600//60, dt%60))

