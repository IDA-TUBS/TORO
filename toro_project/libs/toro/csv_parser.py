#!/usr/bin/env python
# -*- coding: utf-8 -*- 
""" Toro
| Copyright (C) 2019 Innovationsgesellschaft Technische Universitaet Braunschweig mbH (iTUBS)
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes

Description
-----------
This module parses the CSV files that specify a system.
"""

import os
import sys
from pycpa import model
from pycpa import schedulers
from toro import model as toro_model


class parse_csv(object):
    """
    This class contains functions to parse the system specification.
    """
    tasks = list()
    chains = list()
    resources = list()
    system = None
    oWCRT = False
    __error = False

    def __init__(self, folder_name, case):
        """
        Parsing the files resources.csv, tasks.csv, chains.csv.
        """
        # type of system determined by the user query
        assert (case == 1 or case == 2 or case == 3 or case == 4)
        self.case = case
        
        # parse resources.csv
        file = None
        try:
            file = open(os.path.join(folder_name, "resources.csv"),"r")
        except (OSError, IOError):
            print("ERROR: Parser cannot open resources file:\"" + str(folder_name) + "/resources.csv\"")
        if file != None:
            csv_resc = self.__read_csv_resc(file)
            self.resources = self.__get_resources(csv_resc)
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
            self.tasks = self.__get_tasks(csv_tasks)

        # parse chains.csv
        file = None
        try: 
            file = open(os.path.join(folder_name, "chains.csv"),"r")
        except (OSError, IOError):
            print("ERROR: Parser cannot open resources file:\"" + str(folder_name) + "/chains.csv\"")
        if file != None:
            csv_chains = self.__read_csv_chains(file)
            self.chains = self.__get_chains(csv_chains)
        
        if self.__error:
            print(">> QUIT")
            quit()


    def __get_tasks(self, csv_tasks):
        """
        Each task in the parsed list of tasks is converted into an instance of a pyCPA task model.
        Each task is related to a resource.
        """
        tasks = list()
        for csv_task in csv_tasks:
            # instantiate pyCPA task model
            if self.case == 1 or self.case == 2:
                t = toro_model.extTask(
                    name = csv_task["name"],
                    release_offset = csv_task["offset"],
                    bcet = 0,
                    wcet = csv_task["wcet"],
                    scheduling_parameter= csv_task["priority"],
                    let_semantics = False,
                    bet_semantics = True,
                    let = None              
                    )
                t.in_event_model = model.PJdEventModel(P=csv_task["period"])
                if self.case == 1:
                    assert (isinstance(csv_task["wcrt"],int) and csv_task["wcrt"] > 0), ("WCRT of task " + csv_task["name"] + "is not specified.")
                    t.bcrt = csv_task["bcrt"]
                    t.wcrt = csv_task["wcrt"]
                elif self.case == 2:
                    t.bcet = 0
                    assert t.release_offset == 0, "Task offsets contradicts initial assumptions."
                    
            elif self.case ==3: 
                t = toro_model.extTask(
                    name = csv_task["name"],
                    release_offset = csv_task["offset"],                    
                    bcet = 0,
                    wcet = csv_task["wcet"],
                    scheduling_parameter= csv_task["priority"],
                    let_semantics = True,
                    bet_semantics = False,
                    let = csv_task["let"]
                    )
                t.in_event_model = model.PJdEventModel(P=csv_task["period"]) 
                t.bcrt = csv_task["bcrt"]
                
            if self.case == 4:
                if 'BET' in csv_task["name"] or 'bet' in csv_task["name"]: 
                    t = toro_model.extTask(
                        name = csv_task["name"],
                        release_offset = csv_task["offset"],
                        bcet = 0,
                        wcet = csv_task["wcet"],
                        scheduling_parameter= csv_task["priority"],
                        let_semantics = False,
                        bet_semantics = True,
                        let = None              
                        )
                    t.in_event_model = model.PJdEventModel(P=csv_task["period"])
                    t.bcet = 0
                    assert t.release_offset == 0, "Task offsets contradicts initial assumptions."  
                                          
                elif 'LET' in csv_task["name"] or 'let' in csv_task["name"]:                    
                    t = toro_model.extTask(
                        name = csv_task["name"],
                        release_offset = csv_task["offset"],                    
                        bcet = 0,
                        wcet = 0,
                        scheduling_parameter= csv_task["priority"],
                        let_semantics = True,
                        bet_semantics = False,
                        let = csv_task["let"]
                        )
                    t.in_event_model = model.PJdEventModel(P=csv_task["period"]) 
                    t.bcrt = csv_task["bcrt"]    
                    
                else:
                    assert False, "Tasks not correctly named."                                 
                                        
            else:
                assert False
            
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


    def __get_chains(self, csv_chains):
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
                assert False, "ERROR: Parser cannot find task(s) " + str(skippedTasks) + " in chain: \"" 
                + str(csv_chain) + "\""
        return chains


    def __get_resources(self, csv_rescs):
        """
            Check that the specified schedulers are supported and 
            return resources with pyCPA-scheduler models if applicable. 
        """
        rescs = list()
        if self.case == 1 or self.case == 3:
            for csv_resc in csv_rescs:
                r = model.Resource(csv_resc["name"], csv_resc["scheduler"].lower())
                rescs.append(r)                
            return rescs   
        elif self.case == 2 or self.case == 4:
            for csv_resc in csv_rescs:
                scheduler = None
                if csv_resc["scheduler"].lower() == "sppscheduler":
                    scheduler = schedulers.SPPScheduler()
                elif csv_resc["scheduler"].lower() == "spnpscheduler":
                    scheduler = schedulers.SPNPScheduler()
                if scheduler != None:
                    r = model.Resource(csv_resc["name"], scheduler)
                    rescs.append(r)
                else:
                    print("ERROR: Scheduler \"" + csv_resc["scheduler"] + "\" in resource: \"" + csv_resc["name"] + "not supported for case 2.")
                    self.__error = True
            return rescs
        else:
            assert True


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