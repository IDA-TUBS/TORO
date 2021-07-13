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
         - Marie-Therese Harnau
         - Alex Bendrick
 
Description
===========
This module contains classes and functions for interpreting user inputs (prompts)
to determine whether a system is analysable using TORO.
"""
import os
from .. import io

valid_results = ['y', 'Y', 'j', 'J', 'yes', 'Yes', 'ja', 'Ja', 'N', 'n', 'no', 'No', 'nein', 'Nein']
positive = ['y', 'Y', 'j', 'J', 'yes', 'Yes', 'ja', 'Ja']
negative = ['N', 'n', 'no', 'No', 'nein', 'Nein']
    
 
class SystemProperties(object):
    """
    This class provides functions to interactively check the properties of system to be analyzed.
    """
    
    def __init__(self):
        self.clks_sync = False
        self.subchain_sync = True
        self.pp_let = False   
        self.pp_bet = False 
        self.pp_mixed = False 
        self.periodic_tasks = False         
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
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.clks_sync = True
            return

        ans = input("Is each subchain exclusively executed on an arbitrary number of synchronized resources\
                    \nor uses LET interconnect tasks to communicate between those resources? [y/n]\n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.subchain_sync = True
            return
        else:
            quit("ERROR: Such systems (subchains across unsynchronized resources) are not supported.\nTORO terminates.")
        
        


    def  _programming_paradigm(self):
        """
        This functions checks the programming paradigm of tasks.
        """
        
        ans = input("For each system, are all tasks subject to the LET programming paradigm? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.pp_let = True
            return    


        ans = input("For each system, are all tasks subject to the BET programming paradigm? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.pp_bet = True
            return
        
        ans = input("For each system, are all tasks on a resource either subject to the LET or BET programming paradigm? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:                      
            self.pp_mixed = True
            return
        else:                      
            quit("ERROR: The system is not supported - invalid combination of programming paradigms. \n TORO terminates")       
                      

    def _activation_pattern(self):
        """
        This functions checks the activation pattern. 
        """
        ans = input("Are all tasks periodically activated? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.periodic_tasks = True 
        elif ans in negative:                        
            quit("ERROR: Systems with not-periodic tasks are not supported yet.\nTORO terminates.")  

                                    
    def _task_deadlines(self):
        """
        This functions checks the type of task deadlines. 
        """
        ans = input("Do all tasks have implicit deadlines if not specified otherwise? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.implicit_deadlines = True 
        elif ans in negative:                        
            quit("ERROR: The system is not supported.\nTORO terminates.")           
            
                        
    def _wcrt_knowledge(self):
        """
        This function checks whether the WCRTs of tasks are known or can be computed.
        """    
        ans = input("Are the WCRTs known from all BET tasks in the cause-effect chains? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')

        if ans in positive:
            self.wcrt_known = True
        elif ans in negative:
            self.wcrt_known = False           


    def _wcrt_computation(self):
        """ 
        The function checks whether the computation of WCRTs is possible.
        """
        print("Toro checks now whether the computation of WCRTs is possible.")
        ans = input("\t Did you specify ALL tasks in the system (not only those in the listed cause-effect chains)? [y/n] \n")

        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')
        if ans in negative:
            quit("ERROR: All tasks need to be described.\nTORO terminates")

        ans = input("\t Did you specify the task-to-resource mapping for ALL tasks? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')
        if ans in negative:
            quit("ERROR: A complete task-to-resource mapping needs to be specified.\nTORO terminates")

    
        ans = input("\t Did you specify the scheduling algorithm for each resource? Either SPP or SPNP? [y/n] \n")   
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')
        if ans in negative:
            quit("ERROR: A scheduling algorithm has to be specified - Only SPP and SPNP supported so far.\nTORO terminates")
         
        ans = input("\t Did you specify for ALL tasks: period, offset=0 (!), WCET, scheduling priority? [y/n] \n")
        while(ans not in valid_results):            
            ans = input('Invalid input - try again [y/n]: ')
        if ans in positive:
            self.wcrt_computable = True  
        else:
            quit("ERROR: Without detailed information on each task's period, offsetm wcet and priority the analysis will not worj.\nTORO terminates.")           
        
        
    def _determine_case(self): 
        """
        This function determines the case of the analysis.
        """

        # Periodic BET tasks with known WCRT
        if (self.clks_sync == True and 
            self.pp_bet == True and 
            self.periodic_tasks == True and 
            self.implicit_deadlines == True and 
            self.wcrt_known == True): 
            self.case = 1
        # Periodic BET tasks with unknown WCRT            
        elif (self.clks_sync == True and
              self.pp_bet == True and 
              self.periodic_tasks == True and 
              self.implicit_deadlines == True and 
              self.wcrt_known == False and 
              self.wcrt_computable == True):
            self.case = 2            
        # LET tasks
        elif (self.clks_sync == True and
              self.pp_let == True and 
              self.implicit_deadlines == True):
            self.case = 3
        # Mixed programming paradigms but periodic tasks
        elif (self.clks_sync == True and 
              self.pp_mixed == True and 
              self.periodic_tasks == True and 
              self.implicit_deadlines == True and 
              self.wcrt_known == True): # NOTE CHANGED THIS LINE!!
            self.case = 4
        # arbitrary programming paradigms with sl let tasks
        elif (self.subchain_sync == True and
              self.periodic_tasks == True and 
              self.implicit_deadlines == True): # NOTE implicit deadlines not relevant for let ic tasks!!
            self.case = 5 
        else:
            assert False, "Combination of system properties is not supported."
        io.PrintOuts.line()
        print('System properties represent case=' + str(self.case))
        io.PrintOuts.line()

  
    
    
    



    