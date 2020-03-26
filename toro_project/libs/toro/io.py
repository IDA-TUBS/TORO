#!/usr/bin/env python
# -*- coding: utf-8 -*- 
 
"""
Copyright Notice
================
Toro
| Copyright (C) 2019 Innovationsgesellschaft Technische Universitaet Braunschweig mbH (iTUBS)
| All rights reserved.
| See LICENSE file for copyright and license details.
 
:Authors:
         - Leonie Koehler
         - Nikolas Brendes
 
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
    
    
    def _get_system_dirs(self,args):
        print("=======================================================================================")
        print("Searching for systems to analyze in: ") 
        print(str(args.path))
        print("---------------------------------------------------------------------------------------")     
        folders = list()
        dirs = list()
        for folder in os.listdir(args.path):
            d = os.path.join(args.path, folder)
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
            dirs.append(os.path.join(args.path, folders[0]))
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
                    dirs.append(os.path.join(args.path, folder))
            else:
                for n in nums:
                    dirs.append(os.path.join(args.path, folders[n - 1]))
     
        else:
            print("ERROR: No systems have been found under " + _dir + ".")
            print("Toro terminates.")
            quit()
     
        return dirs
    
    
def log_chain_results(results, chain, _dir, chain_results_dict):
    """
    This function produces the major content of the file "RESULTS_LOG.txt".
    """
    log = "\n"
    log += "==================================================================\n"
    log += "DETAILED RESULTS FOR CHAIN \"" + chain.name + "\" \n"
    log += "==================================================================\n"
    log += "1) DEFINITION OF THE ANALYZED CAUSE-EFFECT CHAIN \n"    
    log += "------------------------------------------------------------------\n"
    log += " CHAIN: " + chain.name + "\n   sequence: "
    for task in chain.tasks:
        log += " -> " + task.name
    log += "\n"
    log += "==================================================================\n"
    log += "2) SUMMARY: MAXIMUM END-TO-END LATENCY \n"    
    log += "------------------------------------------------------------------\n"    
    log += "max end-to-end latency: " + str(results.max_data_age) + "\n"
    log += "==================================================================\n"
    log += "3) DETAILS OF THE LATENCY ANALYSIS: INDIVIDUAL MAX PATH LATENCIES \n"    
    log += "------------------------------------------------------------------\n"  
    log += "Maximum end-to-end latency for each path \n"
    for k in results.path_matrix:
        s = ""
        for i in k:
            s += " -> " + i.name
        if (results.semantics == "LET"):
            data_age = k[-1].Dmin - k[0].Rmin
        if (results.semantics == "BET_with_known_WCRTs"):
            data_age = k[-1].Rmax + k[-1].wcrt - k[0].Rmin
        log += s + "  |  max: " + str(data_age) + "\n"
         
    log += "==================================================================\n"
    log += "4) SUMMARY: ROBUSTNESS MARGINS W.R.T. THE ISOLATED CAUSE-EFFECT CHAIN \n"    
    log += "------------------------------------------------------------------\n"           
    for task in chain.tasks:
        log += ("RM of task \"" + task.name + "\"" + \
                " for the isolated chain " + chain.name + " is " + \
                  str(chain_results_dict[chain.name].task_robustness_margins_dict[task.name]) + \
                  " (e2e-deadline satisfied).\n")       
        log += ("RM of task \"" + task.name + "\"" + \
                " for the isolated chain " + chain.name + " is " + \
                  str(chain_results_dict[chain.name].task_robustness_margins_corrected_dict[task.name]) + \
                  " (e2e-deadline & task deadlines satisfied).\n")           
    log += "==================================================================\n"
    log += "5) DETAILS OF THE ROBUSTNESS ANALYSIS: ROB. MARGINS FOR JOB PAIRS \n"    
    log += "------------------------------------------------------------------\n"  
    for task in results.job_matrix:
        for job in task:
            if job.robustness_margin != None:
                log += " -> " + job.name + " -> " + job.rm_job.name + "  |  RM: " + str(job.robustness_margin) + \
                " (e2e-deadline satisfied).\n"
                log += " -> " + job.name + " -> " + job.rm_job.name + "  |  RM: " + str(job.robustness_margin_corrected) + \
                " (e2e-deadline & task deadlines satisfied).\n"                
    log += "The robustness margin for the tail task results from the constraint \n"
    log += "imposed by the task deadline and the end-to-end deadline of the chain. \n"
    log += "\n \n \n"
    # write to file
    with open(_dir, "w") as log_file:
        log_file.write(__banner() + log)
     
    return log        