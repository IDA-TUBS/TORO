#!/usr/bin/env python
# -*- coding: utf-8 -*- 
""" Toro
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes
         - Alex Bendrick

Description
-----------
This module parses the CSV files that specify a system.
"""

import os
import sys
from pycpa import model
from pycpa import schedulers
from .. import model as toro_model

from .check import SystemProperties

from .parser import ModelParser


class CSVParser(ModelParser):
    """
    This class contains functions to parse the system specification.
    """
    tasks = list()
    chains = list()
    resources = list()
    system = None
    oWCRT = False
    __error = False

    def __init__(self, args):
        """
        Parsing the files resources.csv, tasks.csv, chains.csv.
        """
        sys_properties  = self.__check_csv_properties(args)
        self.case = sys_properties.case

        # type of system determined by the user query
        assert (self.case in [1,2,3,4,5])


    def __check_csv_properties(self, args):
        """ verify whether system is analysable using TORO by
        prompting the user with questions about the system.

        :param args: args dummy class
        :rtype:  Check
        """
        check_properties = SystemProperties()

        check_properties._start(args.path)
        check_properties._clock_sync() 
        check_properties._programming_paradigm() 
        check_properties._activation_pattern()
        check_properties._task_deadlines()

        if check_properties.pp_bet == True or check_properties.pp_mixed == True: 
            check_properties._wcrt_knowledge()
            if check_properties.wcrt_known == False:
                check_properties._wcrt_computation()
        check_properties._determine_case()

        return check_properties

    
    def parse(self, folder_name):
        """ load and process system

        :rtype: pyCPA.model.system, list[extEffectChain]
        """
        assert folder_name is not None

        # parse resources.csv
        file = None
        try:
            file = open(os.path.join(folder_name, "resources.csv"),"r")
        except (OSError, IOError):
            print("ERROR: Parser cannot open resources file:\"" + str(folder_name) + "/resources.csv\"")

        if file != None:
            csv_resc = self.__read_csv_resc(file)
            self.resources = self._get_resources(csv_resc)
            self.system = model.System(folder_name.split("/")[-1])
            for resc in self.resources:
                self.system.bind_resource(resc)
        
        # parse tasks.csv
        file = None
        try:
            file = open(os.path.join(folder_name, "tasks.csv"),"r")
        except (OSError, IOError):
            print("ERROR: Parser cannot open resources file:\"" + str(folder_name) + "/tasks.csv\"")
        if file != None:
            csv_tasks = self.__read_csv_tasks(file)
            self.tasks = self._get_tasks(csv_tasks)

        # parse chains.csv
        file = None
        try: 
            file = open(os.path.join(folder_name, "chains.csv"),"r")
        except (OSError, IOError):
            print("ERROR: Parser cannot open resources file:\"" + str(folder_name) + "/chains.csv\"")
        if file != None:
            csv_chains = self.__read_csv_chains(file)
            self.chains = self._get_chains(csv_chains)
        
        if self.__error:
            print(">> QUIT")
            quit()

        return self.system, self.chains


    def _get_tasks(self, csv_tasks):
        """
        Each task in the parsed list of tasks is converted into an instance of a pyCPA task model.
        Each task is related to a resource.
        """
        tasks = list()

        for csv_task in csv_tasks:
            t_name = csv_task["name"]
            t_period = csv_task["period"]
            t_offset = csv_task["offset"]

            try:
                t_bcet = csv_task["bcet"]
            except:
                t_bcet = 0

            try:
                t_wcet = csv_task["wcet"]
            except:
                t_wcet = None

            try:
                t_bcrt = csv_task["bcrt"]
            except:
                t_bcrt = None

            try:
                t_wcrt = csv_task["wcrt"]
            except:
                t_wcrt = None          

            if 'BET' in t_name:
                t_semantic = toro_model.Semantic.BET
                t_let = None
                if (not isinstance(t_wcrt, int) or not isinstance(t_bcrt, int)):
                    if(not isinstance(t_wcet, int) or not isinstance(t_bcet, int)):
                        quit("Neither execution nor response times are defined for task " + t_name)

            elif 'LET' in t_name:
                t_semantic = toro_model.Semantic.LET
                t_let = csv_task["let"]
            t_prio = csv_task["priority"]

            t = toro_model.extTask(
                name = t_name,
                release_offset = t_offset,
                bcet = t_bcet,
                wcet = t_wcet,
                scheduling_parameter= t_prio,
                semantic = t_semantic,
                let = t_let,
                bcrt = t_bcrt,
                wcrt = t_wcrt)

            t.in_event_model = model.PJdEventModel(P = t_period)
            
            if t_semantic == toro_model.Semantic.LET:
                if t_let > t_period:
                    t.set_system_level_task()


            # Check that the task is assigned to a known resource.
            hit = False
            for resc in self.resources:
                if resc.name == csv_task["resource"]:
                    resc.bind_task(t)
                    hit = True
            if hit:
                tasks.append(t)
            else:
                self.__error = True
                assert False, ("ERROR: Parser cannot assign task \"" + csv_task["name"] + 
                               "\" to a unknown resource \"" + csv_task["resource"] + "\"")
       
        return tasks


    def _get_chains(self, csv_chains):
        """
        Check that cause-effect chains do not consist of tasks that are not specified in tasks.csv.
        Return list of pyCPA task instances as cause-effect chain.
        """
        chains = list()
        for csv_chain in csv_chains.keys():
            task_list = list()
            hit = False
            skippedTasks = ""
            for task_name in csv_chains[csv_chain]['tasks']:
                hit = False
                for task in self.tasks:
                    if task_name == task.name:
                        task_list.append(task)
                        hit = True
                        break
                if not hit:
                    skippedTasks +=  " \"" + task_name + "\""
            if hit:
                chains.append(toro_model.extEffectChain(csv_chain, task_list, csv_chains[csv_chain]['e2e_deadline']))
            else:
                self.__error = True
                assert False, "ERROR: Parser cannot find task(s) " + str(skippedTasks) + " in chain: \"" + str(csv_chain) + "\""
        return chains


    def _get_resources(self, csv_rescs):
        """
            Check that the specified schedulers are supported and 
            return resources with pyCPA-scheduler models if applicable. 
        """
        rescs = list()

        map = {'sppscheduler': schedulers.SPPScheduler(), 'spnpscheduler': schedulers.SPNPScheduler()}

        for csv_resc in csv_rescs:
            scheduler = csv_resc["scheduler"].lower()

            if scheduler in map.keys():
                scheduler = map[scheduler]
            else:
                scheduler = None

            r = model.Resource(csv_resc["name"], scheduler)
            rescs.append(r)  

        return rescs


    def __read_csv_chains(self, file):
        """
          This function returns a dictionary of cause-effect chains, where the key is the
          name of the cause-effect chain and the value is a list of tasks.
        """                
        chains = dict()
        
        l = file.readline()
        keys = list()
        if len(l) > 3:
            l = self.__remove_trailing_newline_char(l)
            # checking for correct keys
            line = l.split(";")
            for key in line[0:2]:
                key = key.lower()
                if  "chain_name" in key:
                    keys.append("chain_name")
                elif "e2e_deadline" in key:
                    keys.append("e2e_deadline")                      
                elif "members" in key:
                    keys.append("members")
                else:
                    assert False, ("ERROR: Parser found unknown key in chain.csv: \"" + str(key) + "\"")        
                    
            l = file.readline()
            while l:
                l = self.__remove_trailing_newline_char(l)
                line = l.split(";")
                tasks = list()
                for i in range(2,len(line)): # modified to start from 2
                    tasks.append(line[i])
                if str(line[1]) == 'n/a' or str(line[1]) == 'unknown':
                    e2e_deadline = None
                elif str(line[1]).isdigit():
                    e2e_deadline = int(line[1])   
                else:
                    assert False, "Entry for e2e deadline of chain " + str(line[0]) + " is not supported."
                chains[line[0]] = {'tasks': tasks, 'e2e_deadline': e2e_deadline}
                l = file.readline()
            return chains
        else:
            print("ERROR: Parser encountered unexpected input in chains.csv.")        


    def __read_csv_tasks(self, file):
        """
          This function returns a list of tasks specified in the file tasks.csv. 
          Each list element is a dictionary with entries for parameters. 
        """        
        tasks = list()
        
        l = file.readline()
        keys = list()
        if len(l) > 3:
            l = self.__remove_trailing_newline_char(l)
            # checking for correct keys
            line = l.split(";")
            for key in line:
                key = key.lower()
                if  "task_name" in key:
                    keys.append("name")
                elif  "period" in key:
                    keys.append("period")
                elif  "offset" in key:
                    keys.append("offset")                    
                elif  "priority" in key:
                    keys.append("priority")
                elif  "bcet" in key:
                    keys.append("bcet")
                elif  "wcet" in key:
                    keys.append("wcet")
                elif  "resource" in key:
                    keys.append("resource")  
                elif  "bcrt" in key:
                    keys.append("bcrt")                                      
                elif  "wcrt" in key:
                    keys.append("wcrt")
                elif  "let" in key:
                    keys.append("let")
                else:
                    print("ERROR: Parser found unknown key: \"" + key + "\"")
            # parsing tasks
            l = file.readline()
            while l:
                l = self.__remove_trailing_newline_char(l)
                line = l.split(";")
                task = dict()
                for i in range(len(keys)):
                    if keys[i] == "name":
                        task[keys[i]] = str(line[i])
                    elif keys[i] == "resource":
                        task[keys[i]] = str(line[i])
                    else: 
                        if str(line[i]) == 'n/a':
                            task[keys[i]] = None
                        else:    
                            task[keys[i]] = int(line[i])
                tasks.append(task)
                l = file.readline()
            return tasks
        else:
            print("ERROR: Parser encountered unexpected input in tasks.csv.")    


    def __read_csv_resc(self, file):
        """
          This function returns a list of resources specified in the file resources.csv. 
          Each list element is a dictionary with entries for resource name and scheduler. 
        """
        rescs = list()
         
        l = file.readline()
        keys = list()
        if len(l) > 3:
            # checking for correct keys
            l = self.__remove_trailing_newline_char(l)
            line = l.split(";")
            for key in line:
                key = key.lower()
                if  "name" in key:
                    keys.append("name")
                elif  "scheduler" in key:
                    keys.append("scheduler")
                else:
                    print("ERROR: Parser found unknown key: \"" + key + "\".")
            # parsing resources
            l = file.readline()
            while l:
                l = self.__remove_trailing_newline_char(l)   
                line = l.split(";")
                resc = dict()
                for i in range(len(keys)):
                        resc[keys[i]] = str(line[i])
                rescs.append(resc)
                l = file.readline()
            return rescs
        else:
            print("ERROR: Parser encountered unexpected input in resources.csv.")

        
    
    
    def __remove_trailing_newline_char(self, line):
        if line[-1] == "\n":
            line = line[0:-1] # remove \n
        if line[-1] == "\r":
            line = line[0:-1] # remove \r
        if line[-1] == "\n":
            line = line[0:-1] # remove \n     
        return line   