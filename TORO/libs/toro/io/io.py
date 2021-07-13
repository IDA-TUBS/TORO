#!/usr/bin/env python
# -*- coding: utf-8 -*- 
 
"""
Copyright Notice
================
Toro
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.
 
:Authors:
         - Leonie Koehler
         - Nikolas Brendes
         - Alex Bendrick
Description
===========
This module contains classes and functions for input/output.
"""

import os
import sys



class PrintOuts(object):
    """
    This class contains functions for console printing.
    """
    
    def __init__(self):
        pass
    
    @staticmethod
    def line():
        print("---------------------------------------------------------------------------------------") 

    @staticmethod
    def doubleline():
        print("=======================================================================================")
        
    @staticmethod        
    def newline():
        print('\n')

    @staticmethod 
    def banner():
        _str  = "Toro, Analysis TOol to evaluate the latencies and RObustness of cause-effect chains \n"
        _str += "Copyright (C) 2019 iTUBS Germany \n"
        _str += "All rights reserved. \n"
        _str += "See LICENSE file for copyright and license details. \n"
        _str += "     _____\n"
        _str += "    /__   \___  _ __ ___  \n"
        _str += "      / /\/ _ \| '__/ _ \  \n"
        _str += "     / / | (_) | | | (_) | \n"
        _str += "     \/   \___/|_|  \___/  \n"
        _str += "\n \n"
        print(_str)



class FileManagement(object):
    '''
    This class contains functions for reading and writing files.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    
    def __get_input(self,_s):
        if sys.version_info[0] < 3:
            return raw_input(_s)
        else:
            return input(_s)    
    
    
    def get_system_dirs(self,args):
        print("=======================================================================================")
        print("Searching for systems to analyze in: ") 
        print(str(args.path))
        print("---------------------------------------------------------------------------------------")     
        folders = list()
        dirs = list()

        if args.model_type == 'csv':
            for folder in os.listdir(args.path + '/csv'):
                if folder == 'AmaltheaModels':
                    continue
                d = os.path.join(args.path + '/csv', folder)
                if os.path.isdir(d):
                    valid = True
                    if not os.path.exists(os.path.join(d,"resources.csv")):
                        print("ERROR: file not found: " + os.path.join(d,"resources.csv"))
                        valid = False
                    if not os.path.exists(os.path.join(d,"tasks.csv")):
                        print("ERROR: file not found: " + os.path.join(d,"tasks.csv"))
                        valid = False
                    if not os.path.exists(os.path.join(d,"chains.csv")):
                        print("ERROR: file not found: " + os.path.join(d,"chains.csv"))
                        valid = False
                    if valid:
                        folders.append(folder)
        
            if len(folders) == 1:
                dirs.append(os.path.join(args.path + '/csv', folders[0]))
            elif len(folders) > 1:
                print("The following systems have been found:")
                for i in range(len(folders)):
                    print("  " + str(i + 1) + ": " + folders[i])
                print("  0: all")
        
                print("---------------------------------------------------------------------------------------")            
                print("To select systems enter their ID or a comma-separated list of IDs.")
                print("For instance, enter 1 to select the first of the listed systems,")
                print("enter 1,3 to select the first and the third of the listed systems,")
                print("or enter '0' to select all systems: \n")
        
                valid_input = False
                while(not valid_input):
                    valid_input = True
                    ans = self.__get_input("Enter your choice: ")
                    ans = ans.replace("(","").replace(")","")
                    for s in range(len(ans)):
                        if not (ans[s] == "1" or 
                            ans[s] == "2" or 
                            ans[s] == "3" or 
                            ans[s] == "4" or 
                            ans[s] == "5" or 
                            ans[s] == "6" or 
                            ans[s] == "7" or 
                            ans[s] == "8" or 
                            ans[s] == "9" or 
                            ans[s] == "0" or
                            ans[s] == ","):
                            valid_input = False  
                    if valid_input:
                        nums = list(set(ans.split(",")))
                        nums = list(map(int, nums))
                        for n in nums:
                            if not (-1 <= n <= len(folders)):
                                print("ERROR: " + str(n) + " is an invalid input! Try again.")
                                valid_input = False
                                break
                    else:
                        print("ERROR: Unknown characters! Try again.")
                    
                if 0 in nums:
                    for folder in folders:
                        dirs.append(os.path.join(args.path + '/csv', folder))
                else:
                    for n in nums:
                        dirs.append(os.path.join(args.path + '/csv', folders[n - 1]))
        
            else:
                print("ERROR: No systems have been found under " + args.path + ".")
                print("Toro terminates.")
                quit()
        
            return dirs

        elif args.model_type == 'amalthea':
            d = os.path.join(args.path, 'AmaltheaModels')
            # retrieve all file names from the relevant directories
            file_list = list()
            for path, subdirs, files in os.walk(d):
                pathToFile = None
                for name in files:
                    pathToFile = os.path.join(path, name)
                    file_list.append(pathToFile)
            # remove all non python files
            file_list = [x for x in file_list if (".amxmi" in x)]

            if len(file_list) > 0:
                print("The following systems have been found:")
                i = 1
                for f in file_list:
                    tmp = f.split('/')                    
                    print("  " + str(i) + ": " + tmp[len(tmp) - 1])
                    i += 1
                    
                if len(file_list) == 1:
                    valid_inputs = [1]
                else:
                    valid_inputs = list(range(1, i))
                    
                while True:
                    
                    res = input("Enter your choice: ")
                    try:
                        res = int(res)
                    except:
                        print("ERROR: " + str(res) + " is an invalid input! Try again.")
                        continue

                    if res in valid_inputs:
                        return file_list[res - 1]
                    else:
                        print("ERROR: " + str(res) + " is an invalid input! Try again.")
            
            else:
                print("ERROR: No systems have been found under " + d + ".")
                print("Toro terminates.")
                quit()

                       