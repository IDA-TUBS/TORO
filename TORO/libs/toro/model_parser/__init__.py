'''
Created on 29.10.2020

:Authors:
         - Alex Bendrick
'''

from .csv_parser import CSVParser

try:
    from .amalthea_parser import AmaltheaParser
except:
    print("-------------------------------------------------------------------\
         \nWarning: AmaltheaParser incomplete. check installation requirements\
         \n-------------------------------------------------------------------")