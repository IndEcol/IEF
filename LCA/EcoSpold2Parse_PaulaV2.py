
# coding: utf-8

# ## Ecospold 2 parser

# In[]:

import xml.etree.ElementTree
import xlrd, xlwt
import numpy as np
import os
import os.path


# In[]:

DataListFile        = 'C:\\Users\\Paula\\Eigenes\\HiWi_Pauliuk\\Ecoinvent_3_4\\ei_34_rawdata_parse.xlsx'
DataListFileHandle  = xlrd.open_workbook(DataListFile)
DataListFileSheet   = DataListFileHandle.sheet_by_name('clinker_market')

FileNames = [] #List of ecospold filenames
m = 0
while True:
    try:
        FileNames.append(DataListFileSheet.cell_value(m +2, 2))
        m += 1
    except:
        break
        
#print(FileNames)        


# In[]:

# Open Excel for writing
myfont = xlwt.Font()
myfont.bold = True
mystyle = xlwt.XFStyle()
mystyle.font = myfont
Result_workbook  = xlwt.Workbook(encoding = 'ascii') 

for FN in FileNames:
    File = 'C:\\Users\\Paula\\Eigenes\\HiWi_Pauliuk\\Ecoinvent_3_4\\EI34_unlinked\\' + FN + '.spold'
    if os.path.isfile(File):
        e = xml.etree.ElementTree.parse(File).getroot()
        Result_worksheet = Result_workbook.add_sheet(FN[0:15]+ '...') 
        Result_worksheet.write(1, 1, label = 'Activity name', style = mystyle)  
        Result_worksheet.write(1, 2, label = 'Activity ID', style = mystyle)  
        Result_worksheet.write(1, 3, label = 'Activity region', style = mystyle)  
        Result_worksheet.write(1, 4, label = 'Activity start date', style = mystyle)  
        Result_worksheet.write(1, 5, label = 'Activity end date', style = mystyle)  
        Result_worksheet.write(1, 6, label = 'Activity description', style = mystyle)  
        Result_worksheet.write(4, 1, label = 'Flow data', style = mystyle)  
        
        Result_worksheet.write(4, 2, label = 'Good/substance', style = mystyle)  
        Result_worksheet.write(4, 3, label = 'Good/substance ID', style = mystyle)  
        Result_worksheet.write(4, 4, label = 'Amount', style = mystyle)  
        Result_worksheet.write(4, 5, label = 'Unit', style = mystyle)  
        Result_worksheet.write(4, 6, label = 'Uncertainty', style = mystyle)  
        Result_worksheet.write(4, 7, label = 'Group', style = mystyle)  
        Result_worksheet.write(4, 8, label = 'Direction', style = mystyle)  
        Result_worksheet.write(4, 9, label = 'Prive level', style = mystyle)  
        Result_worksheet.write(4, 10, label = 'Price unit', style = mystyle)  
        m0 = 0 # iterate over flow entries
        for child in e[0]: 
            # Check for activity description
            if child.tag == '{http://www.EcoInvent.org/EcoSpold02}activityDescription':
                for childx in child:
                    if childx.tag == '{http://www.EcoInvent.org/EcoSpold02}activity':
                        Act_ID = childx.attrib['id']
                        Result_worksheet.write(2, 2, label = Act_ID)                     
                        for childxx in childx:
                            if childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}activityName':                    
                                Act_Name = childxx.text
                                Result_worksheet.write(2, 1, label = Act_Name)     
                            if childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}generalComment':                    
                                for childxx3 in childxx:
                                    if childxx3.tag == '{http://www.EcoInvent.org/EcoSpold02}text':
                                        if childxx3.attrib['index'] == '1':
                                            Act_Description = childxx3.text            
                                            Result_worksheet.write(2, 6, label = Act_Description)     
                    if childx.tag == '{http://www.EcoInvent.org/EcoSpold02}geography':
                        for childxx2 in childx:
                            if childxx2.tag == '{http://www.EcoInvent.org/EcoSpold02}shortname':                    
                                Act_Region = childxx2.text                            
                                Result_worksheet.write(2, 3, label = Act_Region)    
                    if childx.tag == '{http://www.EcoInvent.org/EcoSpold02}timePeriod':
                        Act_startDate = childx.attrib['startDate']
                        Act_endDate   = childx.attrib['endDate']  
                        Result_worksheet.write(2, 4, label = Act_startDate) 
                        Result_worksheet.write(2, 5, label = Act_endDate) 
                        
            # Check for flow data
            if child.tag == '{http://www.EcoInvent.org/EcoSpold02}flowData':
                rowc = 5
                PriceLevel = None
                Uncert     = 'None'
                for childx in e[0][m0]: # Check for flows (exchanges)
                    TakeFlag = 0 # must be 1 if this flow is used for export (exlude parameters etc.)
                    if 'intermediateExchangeId' in childx.attrib:
                        FlowGroup = 'Intermediate Exchange'
                        ThisID = childx.attrib['id']
                        TakeFlag = 1
                    if 'elementaryExchangeId' in childx.attrib:
                        FlowGroup = 'Elementary Exchange'
                        ThisID = childx.attrib['id']
                        TakeFlag = 1
                    mx = 0  # iterate over attributes of flow entry
                    for childxx in childx: # iterate over all attributes of a given flow
                        #print(childxx.tag)
                        if  childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}name': # name of flowing good/substance
                            FlowName = childxx.text
                        if  childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}unitName': # name of unit
                            UnitName = childxx.text
                        if  childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}inputGroup': # flow is input
                            FlowDirection = 'Input'
                        if  childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}outputGroup': # flow is output
                            FlowDirection = 'Output'
                        if  childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}property': # property info
                            ThisAmount = childxx.attrib['amount']
                            for childxxa in childxx:
                                if childxxa.tag == '{http://www.EcoInvent.org/EcoSpold02}name':
                                    ThisName = childxxa.text
                                if childxxa.tag == '{http://www.EcoInvent.org/EcoSpold02}unitName': 
                                    ThisUnitName = childxxa.text
                            if ThisName == 'price':
                                PriceLevel = ThisAmount
                                PriceUnit  = ThisUnitName
                        if   childxx.tag == '{http://www.EcoInvent.org/EcoSpold02}uncertainty': # uncertainty info
                            for childxxx in childxx: # children of uncertainty
                                if childxxx.tag == '{http://www.EcoInvent.org/EcoSpold02}lognormal':
                                    #print(childxxx.attrib)
                                    Uncert = '2;' + str(childxxx.attrib['mu']) + ';' + str(np.sqrt(np.float(childxxx.attrib['varianceWithPedigreeUncertainty']))) + ';none;none;none'
                        mx += 1
    
    
                    if TakeFlag == 1:
                        # print(FlowName,'  ', childx.attrib['amount'],'  ',UnitName,'  ',FlowGroup + ', ' + FlowDirection)  
                        Result_worksheet.write(rowc, 2, label = FlowName)    
                        Result_worksheet.write(rowc, 3, label = ThisID)    
                        Result_worksheet.write(rowc, 4, label = childx.attrib['amount'])    
                        Result_worksheet.write(rowc, 5, label = UnitName)    
                        Result_worksheet.write(rowc, 6, label = Uncert)    
                        Result_worksheet.write(rowc, 7, label = FlowGroup)    
                        Result_worksheet.write(rowc, 8, label = FlowDirection)    
                        if PriceLevel is not None:
                            Result_worksheet.write(rowc, 9, label = PriceLevel) 
                            Result_worksheet.write(rowc, 10, label = PriceUnit) 
                        rowc +=1
                    
                    PriceLevel = None
    
            m0 += 1    

Result_workbook.save('C:\\Users\\Paula\\Eigenes\\HiWi_Pauliuk\\Ecoinvent_3_4\\Parsed_Data\\EI_34_rawdata_clinker_market_parsed.xls')           


