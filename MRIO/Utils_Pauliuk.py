# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 19:23:50 2014

@author: pauliuk
"""

"""
Define logging module and functions
"""

import os
import logging
import numpy as np
import pandas as pd
from difflib import SequenceMatcher

def function_logger(file_level, Name_Scenario, Path_Result, console_level):
    # remove all handlers from logger
    logger = logging.getLogger()
    logger.handlers = [] # required if you don't want to exit the shell
    logger.setLevel(logging.DEBUG) #By default, logs all messages

    if console_level != None:
        console_log = logging.StreamHandler() #StreamHandler logs to console
        console_log.setLevel(console_level)
        console_log_format = logging.Formatter('%(message)s') # ('%(asctime)s - %(message)s')
        console_log.setFormatter(console_log_format)
        logger.addHandler(console_log)

    file_log = logging.FileHandler(Path_Result + '\\' + Name_Scenario + '.html', mode='w', encoding=None, delay=False)
    file_log.setLevel(file_level)
    #file_log_format = logging.Formatter('%(asctime)s - %(lineno)d - %(levelname)-8s - %(message)s<br>')
    file_log_format = logging.Formatter('%(message)s<br>')
    file_log.setFormatter(file_log_format)
    logger.addHandler(file_log)

    return logger, console_log, file_log
    
"""
Other functions
"""
def similarX(a, b): # Determine similarity of two strings
    return SequenceMatcher(None, a, b).ratio()
    
def ensure_dir(f): # Checks whether a given directory f exists, and creates it if not
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)         
    
def string_truncate(String, Separator): # Returns substring between leftmost and rightmost occurence of the separator
    if str.find(String,Separator) == -1:
        result = ''
    else:
        result = String[str.find(String,Separator)+1:str.rfind(String,Separator)]
    return result
    
def Build_Aggregation_Matrix_samesize(Position_Vector): # matrix that re-arranges rows of the table it is multiplied to from the left (or columns, if multiplied transposed from the right)
    AM_length = Position_Vector.max() + 1 # Maximum row number of new matrix (+1 to get the right length)
    AM_width  = len(Position_Vector) # Number of rows of the to-be-aggregated matrix
    Rearrange_Matrix = np.zeros((AM_length,AM_width))
    for m in range(0,len(Position_Vector)):
        Rearrange_Matrix[Position_Vector[m].item(0),m] = 1 # place 1 in aggregation matrix at [PositionVector[m],m], so that column m is aggregated with Positionvector[m] in the aggregated matrix
    return Rearrange_Matrix

def Build_Aggregation_Matrix_newsize(Position_Vector,newrows,newcols): # matrix that re-arranges rows of the table it is multiplied to from the left (or columns, if multiplied transposed from the right)
    Rearrange_Matrix = np.zeros((newrows,newcols)) # new size is given
    for m in range(0,len(Position_Vector)):
        Rearrange_Matrix[Position_Vector[m].item(0),m] = 1 # place 1 in aggregation matrix at [PositionVector[m],m], so that column m is aggregated with Positionvector[m] in the aggregated matrix
    return Rearrange_Matrix    
    
def Define_Boynton_Optimized_Colour_Scheme():
    BoyntonOpt=np.array([[0,0,255,255],
                [255,0,0,255],
                [0,255,0,255],
                [255,255,0,255],
                [255,0,255,255],
                [255,128,128,255],
                [128,128,128,255],
                [128,0,0,255],
                [255,128,0,255],]) / 255
    return BoyntonOpt    

def ExcelRedBlueGreenBrown5():
    return       np.array([[99/255,37/255,35/255],  # red_1
                  [149/255,55/255,53/255],    # red_2
                  [217/255,151/255,149/255],  # red_3
                  [230/255,185/255,184/255],  # red_4
                  [242/255,221/255,220/255],  # red_5
                  [33/255,88/255,103/255],    # blue_1
                  [49/255,132/255,155/255],   # blue_2
                  [147/255,205/255,221/255],  # blue_3
                  [182/255,221/255,232/255],  # blue_4
                  [219/255,238/255,243/255],  # blue_5
                  [79/255,98/255,40/255],     # green_1
                  [117/255,146/255,60/255],   # green_2
                  [194/255,214/255,154/255],  # green_3
                  [215/255,228/255,188/255],  # green_4
                  [234/255,241/255,221/255],  # green_5
                  [29/255,27/255,17/255],     # brown_1
                  [74/255,69/255,42/255],     # brown_2
                  [148/255,139/255,84/255],   # brown_3
                  [197/255,190/255,151/255],  # brown_4
                  [221/255,217/255,195/255],  # brown_5
                  ])
 
def Aggregation_read(file, sheetname):
    """
    Read the aggregation excel file and build the aggregation matrix. The excel
    file shall have one aggregation scheme per sheet and have size:
            original number of sector x new number of sector
    """
    df = pd.io.excel.read_excel(file, sheetname=sheetname, header=0, index_col=0)
    Aggregation_Matrix = np.asarray(df)
    Aggregation_List = df.columns.values.tolist()
    for w1 in range(np.shape(Aggregation_Matrix)[0]):
        for w2 in range(np.shape(Aggregation_Matrix)[1]):
            if np.isnan(Aggregation_Matrix[w1,w2]) == True:
                Aggregation_Matrix[w1,w2] = 0
            else:
                pass
    return Aggregation_Matrix, Aggregation_List
    
def Projection_matrix(Agg_mat, nb_of_regions, Type='Multi'):
    """
    Build a projection matrix that sorts/aggregates a Multi-regional table.
    If type is 'One' it reproduces Agg_mat according to nb_of_region on top of each other
    If type is 'Multi' it reproduces Agg_mat on the diagonal of a larger matrix of zeros as long as nb_of_regions
    """    
    if Type == 'One':
        Projector = np.concatenate([Agg_mat for i in range(nb_of_regions)], axis=0)
    elif Type == 'Multi':
        h, w = Agg_mat.shape[0], Agg_mat.shape[1]
        blank = np.zeros((h*nb_of_regions, w*nb_of_regions))
        for r1 in range(nb_of_regions):
            for r2 in range(nb_of_regions):
                if r1==r2:
                    blank[r1*h:h*(r1+1),r2*w:w*(r2+1)] = Agg_mat
        Projector = blank
    return Projector    
    
def ExcelSheetRead_1Label(Workbook,Sheetname, RowNo, ColNo, RowOffset =0, ColOffset =0): # Offset: index of label rows and columns
    Sheet = Workbook.sheet_by_name(Sheetname)
    try:
        CornerLabel = Sheet.cell_value(RowOffset,ColOffset)
    except:
        CornerLabel = ''
    RowLabels = []
    for m in range(RowOffset,RowOffset +RowNo):
        RowLabels.append(Sheet.cell_value(m +1,ColOffset))
    ColLabels = []
    for m in range(ColOffset,ColOffset +ColNo):
        ColLabels.append(Sheet.cell_value(RowOffset,m +1))
    Data = np.zeros((RowNo,ColNo))
    for m in range(0,RowNo):
        for n in range(0,ColNo): 
            try:
                Data[m,n] = Sheet.cell_value(RowOffset +m+1, ColOffset +n+1)
            except:
                Data[m,n] = np.nan
    return Data, RowLabels, ColLabels, CornerLabel    
    
def ExcelSheetFill(Workbook,Sheetname, values, topcornerlabel = None, rowlabels = None, collabels = None, Style = None, rowselect = None, colselect = None):
    Sheet = Workbook.add_sheet(Sheetname)
    if topcornerlabel is not None:
        if Style is not None:
            Sheet.write(0,0,label = topcornerlabel, style = Style) #write top corner label
        else:
            Sheet.write(0,0,label = topcornerlabel) #write top corner label
    if rowselect is None: # assign row select if not present (includes all rows in that case)
        rowselect = np.ones((values.shape[0]))
    if colselect is None: # assign col select if not present (includes all columns in that case)
        colselect = np.ones((values.shape[1]))        
    if rowlabels is not None: # write row labels
         rowindexcount = 0
         for m in range(0,len(rowlabels)):
             if rowselect[m] == 1: # True if True or 1
                 if Style is None:
                     Sheet.write(rowindexcount +1, 0, label = rowlabels[m])
                 else:
                     Sheet.write(rowindexcount +1, 0, label = rowlabels[m], style = Style)
                 rowindexcount += 1
    if collabels is not None: # write column labels
         colindexcount = 0
         for m in range(0,len(collabels)):
             if colselect[m] == 1: # True if True or 1
                 if Style is None:
                     Sheet.write(0, colindexcount +1, label = collabels[m])
                 else:
                     Sheet.write(0, colindexcount +1, label = collabels[m], style = Style)
                 colindexcount += 1   
    # write values:
    rowindexcount = 0
    for m in range(0,values.shape[0]): # for all rows
        if rowselect[m] == 1:
            colindexcount = 0
            for n in range(0,values.shape[1]): # for all columns
                if colselect[n] == 1:
                    Sheet.write(rowindexcount +1, colindexcount +1, label = values[m,n])  
                    colindexcount += 1
            rowindexcount += 1
                     
                     
                     
#
#
#
# End of file