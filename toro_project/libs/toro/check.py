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
 
Description
===========
This module contains classes and functions for input/output.
"""
import os

 
class SystemProperties(object):
    """
    This class provides functions to interactively check the properties of system to be analyzed.
    """
    
    def __init__(self):
        self.clks_sync = False
        self.pp_let = False   
        self.pp_bet = False 
        self.pp_mixed = False
        self.implicit_deadlines = False 
        self.wcrt_known = False
        self.wcrt_computable = False
        self.case = None

    def _start(self, path):
        """
        This function starts user interaction. 
        """
        print ("\n")
        print ("=======================================================================================") 
        print ("User-interactive property check for systems saved in " + path)    
        print ("---------------------------------------------------------------------------------------")        


    def _clock_sync(self):
        """
        This functions checks synchronization of clocks and synchronized start of schedules.
        """
        ans = input("Are the clocks in each system synchronized and all schedules start at the same time? [y/n]\n")
        if ans == "y" or ans == "yes":
            self.clks_sync = True
        elif ans == "n" or ans == "no":
            print("ERROR: The systems are not supported.")
            print("Toro terminates.")
            quit()
        else:
            print("ERROR: invalid input")    
        
        
    def  _programming_paradigm(self):
        """
        This functions checks the programming paradigm of tasks.
        """
        ans = input("For each system, are all tasks subject to the LET programming paradigm? [y/n] \n")
        if ans == "y" or ans == "yes":
            self.pp_let = True 
        elif ans == "n" or ans == "no":
            ans = input("For each system, are all tasks subject to the BET programming paradigm? [y/n] \n")
            if ans == "y" or ans == "yes":
                self.pp_bet = True 
            elif ans == "n" or ans == "no":      
                ans = input("For each system, are all tasks on a resource either subject to the LET or BET programming paradigm? [y/n] \n")
                if ans == "y" or ans == "yes":
                    self.pp_mixed = True 
                elif ans == "n" or ans == "no":                      
                    print("ERROR: The system is not supported.")
                    print("Toro terminates.")     
                    quit()
                else:
                    print("ERROR: invalid input")                      
            else:
                print("ERROR: invalid input") 
        else:
            print("ERROR: invalid input")          
                      
                                    
    def _task_deadlines(self):
        """
        This functions checks the type of task deadlines. 
        """
        ans = input("Do all tasks have implicit deadlines? [y/n] \n")
        if ans == "y" or ans == "yes":
            self.implicit_deadlines = True 
        elif ans == "n" or ans == "no":                        
            print("ERROR: The system is not supported.")
            print("Toro terminates.")
            quit()
        else:
            print("ERROR: invalid input")              
            
                        
    def _wcrt_knowledge(self):
        """
        This function checks whether the WCRTs of tasks are known or can be computed.
        """    
        ans = input("Are the WCRTs known from all BET tasks in the cause-effect chains? [y/n] \n")
        if ans == "y" or ans == "yes":
            self.wcrt_known = True
        elif ans == "n" or ans == "no":
            self.wcrt_known = False
        else:
            print("ERROR: invalid input")              


    def _wcrt_computation(self):
        """ 
        The function checks whether the computation of WCRTs is possible.
        """
        print("Toro checks now whether the computation of WCRTs is possible.")
        ans = input("\t Did you specify ALL tasks in the system (not only those in the listed cause-effect chains)? [y/n] \n")
        if ans == "y" or ans == "yes":
            input("\t Did you specify the task-to-resource mapping for ALL tasks? [y/n] \n")
            if ans == "y" or ans == "yes":
                input("\t Did you specify the scheduling algorithm for each resource? Either SPP or SPNP? [y/n] \n")      
                if ans == "y" or ans == "yes":      
                    print("\t Did you specify for ALL tasks: period, offset=0 (!), WCET, scheduling priority? [y/n] \n")    
                    if ans == "y" or ans == "yes":
                        self.wcrt_computable = True
                    elif ans == "n" or ans == "no":
                        print("ERROR: The system is not supported.")
                        print("Toro terminates.")
                        quit()
                    else:
                        print("ERROR: invalid input")                    
                elif ans == "n" or ans == "no":
                    print("ERROR: The system is not supported.")
                    print("Toro terminates.")
                    quit()
                else:
                    print("ERROR: invalid input")  
            elif ans == "n" or ans == "no":
                print("ERROR: The system is not supported.")
                print("Toro terminates.")
                quit()
            else:
                print("ERROR: invalid input")              
        elif ans == "n" or ans == "no":
            print("ERROR: The system is not supported.")
            print("Toro terminates.")
            quit()
        else:
            print("ERROR: invalid input")              
        
        
    def _determine_case(self): 
        """
        This function determines the case of the analysis.
        """
#         print(self.clks_sync)
#         print(self.pp_bet)
#         print(self.pp_let)
#         print(self.pp_mixed)
#         print(self.wcrt_known)
#         print(self.wcrt_computable)
        if (self.clks_sync == True and self.pp_bet == True and self.wcrt_known == True): 
            self.case = 1
        elif (self.clks_sync == True and self.pp_bet == True and self.wcrt_known == False 
              and self.wcrt_computable == True):
            self.case = 2            
        elif (self.clks_sync == True and self.pp_let == True and self.implicit_deadlines == True):
            self.case = 3
        elif (self.clks_sync == True and self.pp_mixed == True and self.wcrt_known == False 
              and self.wcrt_computable == True):
            self.case = 4 
        else:
            assert False, "Combination of system properties is not supported."           
        
        #print('Case ' + str(self.case))


  
    
    
    



    