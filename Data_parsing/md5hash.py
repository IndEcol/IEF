# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 09:08:29 2018

@author: spauliuk
"""

import hashlib


def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    
FileName = 'C:\\Users\\spauliuk\\FILES\\Work_Archive\\_Data_Derived\\EXIOBASEv3.4_OFFICIAL\\EXIOBASE3.4_2011_ITC_Capital.zip'

print('The MD5 checksum is', md5Checksum(FileName))



# Check UUID from file
import scipy.io
scipy.io.loadmat('C:\\Users\\spauliuk\\FILES\\Work_Archive\\_Data_Derived\\EXIOBASEv3.4_OFFICIAL\\EXIOBASE3.4_2011_ITC.mat')['ScriptConfig']