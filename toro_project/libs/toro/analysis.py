#!/usr/bin/env python
# -*- coding: utf-8 -*- 

""" Toro
| Copyright (C) 2019 Innovationsgesellschaft Technische Universitaet Braunschweig mbH (iTUBS)
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes
         - Simon Bagschik

Description
-----------
This module provides classes and functions to compute an upper bound on the end-to-end latency and robustness 
margins for a given cause-effect chain. 
The latency analysis relies on Becker et al. 2017 + 2018.
"""

from __future__ import division
from toro import plot
from toro import io
import copy
import math
import pycpa

class ChainProperties(object):
    """
    This class contains function to compute the maximum end-to-end latency and the 
    robustness margins for a given cause-effect chain.
    """
    def __init__(self, args, chain, results, case):
        """ 
        If the class 'ChainProperties' is initialized, it will compute the
        maximum end-to-end latency and the robustness margins for 'chain'. 
        """
        self.results = results
        self.chain = chain
        self.hyperperiod = None
        self.job_matrix = list()
        self.log_robustness_margins = dict()
        self.path_matrix = None
        self.path_matrix_adapted = None
        self.max_e2e_lat = None        
        
        # copied data structures for test
        self.copied_results = dict()        
        self.copied_chain = copy.deepcopy(chain)
        self.copied_hyperperiod = None          
        self.copied_job_matrix = list()        
        self.copied_path_matrix = None
        self.copied_path_matrix_adapted = None
        self.copied_max_e2e_lat = None           
        
        
        #1) calculate hyper period of chain tasks
        self.hyperperiod = self.__calc_hyperperiod(chain)      
        
        
        #2) build a matrix of instantiated jobs
        l = 0
        for k in chain.tasks:
            if(l==0):
                root = True
            else:
                root = False
            self.__set_jobs(k, results, self.hyperperiod, self.job_matrix, root, l)
            l += 1

             
        # 3) determine possible paths & calculate maximum data age
        self.path_matrix = self.__determine_paths(self.job_matrix)
        self.max_e2e_lat = self.__determine_max_e2e_lat(self.path_matrix, test = False)
         
               
        assert self.max_e2e_lat != None 
        if chain.e2e_deadline != None:
            assert self.max_e2e_lat <= chain.e2e_deadline, "The max. latency violates the specified e2e-deadline!"
        else:
            io.PrintOuts.line()
            print('INFO: Since no end-to-end deadline is specified, the default e2e_deadline := max_e2e_lat applies.')
            chain.e2e_deadline = self.max_e2e_lat
        

        # 4) calculate robustness margins resp. Delta LET
        if args.lat == False:
            if (case == 1 or case == 2 or case == 3): 
                self.task_robustness_margins_dict = dict()
                self.task_delta_let_dict = dict()
                self.task_theta_dict = dict()
                for task in chain.tasks:
                    self.task_robustness_margins_dict[task.name] = None
                    self.task_delta_let_dict[task.name] = None
                    self.task_theta_dict[task.name] = None
                self.__calc_robustness_margins(self.job_matrix, chain, results, case)
                
                # test robustness margins resp. Delta LET
                if args.test == True:
                    self.__test()
                
            else:
                print('WARNING: The robustness analysis does not support this kind of system model.')


        
        

    def __calc_hyperperiod(self, chain):
        """
        This function calculates the hyper period of the chain tasks.
        """
        periods = []
        i = 0
        while i < len(chain.tasks):
            periods.append(chain.tasks[i].in_event_model.P)
            i += 1
        # calculate hyper period
        hyperperiod = periods[0]
        for k in periods:
            hyperperiod = self.__lcm(k, hyperperiod)
        return hyperperiod


    def __set_jobs(self, task, results, HP, job_matrix, root, l):
        """
        This functions instantiates the set of jobs needed for the reachability analysis.
        """
        job_line = list()
        job_number = 1
   
        if(root):
            # instantiate all jobs of the root task in the hyper period 
            for k in range(int(HP / task.in_event_model.P)):
                current_job = task.instantiate_job(job_number=job_number, 
                                                   wcrt=results[task].wcrt, 
                                                   bcrt=results[task].bcrt)
                current_job.parent_task = task
                job_line.append(current_job)
                job_number += 1
            job_matrix.append(job_line)
        else:
            # instantiate successor jobs whose Rmin is smaller or equal to Dmax of the task last job
            border = job_matrix[l-1][-1].Dmax
            while True:
                #print('Chain task #' + str(l) + ': job ' + str(job_number))
                current_job = task.instantiate_job(job_number=job_number, wcrt=results[task].wcrt, 
                                                   bcrt=results[task].bcrt)
                current_job.parent_task = task
                if (current_job.Rmin <= border):
                    job_line.append(current_job)
                    job_number += 1
                else:
                    job_matrix.append(job_line)
                    break
        return


    def __determine_paths(self, job_matrix):
        """
        This function determines paths in the job matrix and returns path matrix. 
        :param: path_matrix: first list index = path, second list index = job
        """
        # assign successor jobs to jobs in job_matrix
        for i in range(len(job_matrix) - 1):  # iterate over rows in matrix
            for k in range(len(job_matrix[i])):  # iterate over columns in row
                # earliest possible job_matrix[i+1][l] that may read from job_matrix[i][k]
                # see Eq. 2 of Becker et al. 2016 (adapted for offsets)
                # note that job index is by 1 smaller than job number
                l = math.ceil((job_matrix[i][k].Dmin - job_matrix[i+1][0].offset) / job_matrix[i + 1][0].period) - 1
                while (l < len(job_matrix[i + 1])):
                    if (self.__follows(job_matrix[i][k], job_matrix[i + 1][l])):
                        job_matrix[i][k].successor_jobs.append(job_matrix[i + 1][l])
                    l += 1
        # use recursive approach of building path_matrix
        path_matrix = list()
        for a in job_matrix[0]: 
            a.iterate(list(), path_matrix, len(job_matrix))
        return path_matrix


    def __follows(self, prod_job, cons_job):
        """Check reachability between jobs using Eq. 1 of Becker et al. 2016 """
        if ((cons_job.Rmax >= prod_job.Dmin) and (cons_job.Rmin < prod_job.Dmax)):
            return True
        else:
            return False


    def __determine_max_e2e_lat(self, path_matrix, test):
        """Function determines the path with the longest latency according to maximumd data age semantics,
           i.e, release of header job to earliest data of tail job in the worst case.
        """
        if (len(path_matrix) == 0):
            assert False, "No reachable paths!"
            return 0
        else:
            data_ages = []
            for k in range(len(path_matrix)): 
                # first and last task is LET
                if (path_matrix[k][0].let_semantics == True and 
                    path_matrix[k][-1].let_semantics == True): 
                    # with LET the last chain deterministically produces a result already at Dmin
                    data_ages.append(path_matrix[k][-1].Dmin - path_matrix[k][0].Rmin)
                # first and last task is BET
                elif (path_matrix[k][0].bet_semantics == True and 
                      path_matrix[k][-1].bet_semantics == True): 
                    data_ages.append(path_matrix[k][-1].Rmin + path_matrix[k][-1].wcrt - path_matrix[k][0].Rmin)                                   
                # first task is LET and last task is BET
                elif (path_matrix[k][0].let_semantics == True and 
                      path_matrix[k][-1].bet_semantics == True):
                    data_ages.append(path_matrix[k][-1].Rmin + path_matrix[k][-1].wcrt - path_matrix[k][0].Rmin)                      
                # first task is BET and last task is LET
                elif (path_matrix[k][0].bet_semantics == True and 
                      path_matrix[k][-1].let_semantics == True):             
                    data_ages.append(path_matrix[k][-1].Dmin - path_matrix[k][0].Rmin)              
                else:
                    raise               
        
        if test == False:
            p =-1    
            for k in path_matrix:
                p += 1
                s = ""
                for i in k:
                    s += " -> " + i.name
                print(s + "  |  max: " + str(data_ages[p]))
        
        return max(data_ages)


    def __calc_robustness_margins(self, job_matrix, chain, results, case):
        """
        This function computes robustness margins that relate to an isolated cause-effect chain 
        (not the set of cause-effect chains).
        
        job_matrix[task][job].rm_job:  \tau_{k+1}(q_{\tau_k(j_k)})  
        => note that the job-index of job_matrix starts at 0 but job_number (as an attribute of Job) starts at 1
        """
        # tasks \tau_1^c ... \tau_{n-1}^c find q for each job in job matrix
        for task in range(len(job_matrix)-1):
            for job in range(len(job_matrix[task])):
                q = None
                # no successor jobs
                if len(job_matrix[task][job].successor_jobs) == 0: 
                    # earliest possible job_matrix[task+1][l] that may read from job_matrix[task][job]
                    # see Eq. 2 of Becker et al. 2016 (adapted for offsets)
                    # note that job index is by 1 smaller than job number                    
                    l = math.ceil((job_matrix[task][job].Dmin 
                                   - job_matrix[task + 1][0].offset)/ job_matrix[task + 1][0].period) -1
                    while (True):
                        if l < len(job_matrix[task+1]):
                            # first job of (task+1) that could be reached if disturbances are present
                            if (job_matrix[task + 1][l].Rmin > job_matrix[task][job].Dmax): 
                                q = l+1 
                                job_matrix[task][job].rm_job = job_matrix[task+1][q-1] 
                                break
                            else:
                                l += 1
                        elif l >= len(job_matrix[task+1]): 
                            copy_chain = copy.copy(self.chain)                     
                            test_job_l = self.chain.tasks[task+1].instantiate_job(job_number= l+1, \
                                                                                wcrt=results[copy_chain.tasks[task+1]].wcrt, \
                                                                                bcrt=results[copy_chain.tasks[task+1]].bcrt)
                            if (test_job_l.Rmin > job_matrix[task][job].Dmax): 
                                q = l+1 
                                job_matrix[task][job].rm_job = copy.deepcopy(test_job_l)
                                break
                            else:
                                l += 1                            
                        else:
                            raise
                        
                # successor jobs
                else:
                    # job number for q, but index in job matrix must be smaller by one
                    q = job_matrix[task][job].successor_jobs[-1].job_number + 1 
                    
                    # check if \tau_{k+1}(q) is in job matrix
                    if q-1 < len(job_matrix[task+1]):
                        job_matrix[task][job].rm_job = job_matrix[task+1][q-1] 
                    else:
                        copy_chain = copy.copy(self.chain)                   
                        job_matrix[task][job].rm_job = self.chain.tasks[task+1].instantiate_job(job_number=q, \
                                                                                                wcrt=results[copy_chain.tasks[task+1]].wcrt, \
                                                                                                bcrt=results[copy_chain.tasks[task+1]].bcrt)
                
                # compute theta for each job_matrix[task][job]                             
                job_matrix[task][job].theta = job_matrix[task][job].rm_job.Rmin -  job_matrix[task][job].Dmax 
                assert job_matrix[task][job].theta >= 0
                #print("Job: %s -> %s -  theta: %d" % (job_matrix[task][job].name, job_matrix[task][job].rm_job.name, job_matrix[task][job].theta))



        # compute job-related robustness margin resp. delta let    
        j=-1      
        for task in job_matrix:  
            j += 1    
            for job in task: 
                if task == job_matrix[-1]:
                    if job_matrix[j][0].bet_semantics == True: 
                        if chain.e2e_deadline == None or chain.e2e_deadline == 'n/a':
                            job.robustness_margin = job_matrix[j][0].period \
                                                    - job_matrix[j][0].offset \
                                                    - job_matrix[j][0].wcrt
                        elif isinstance(chain.e2e_deadline, int):
                            job.robustness_margin = min(chain.e2e_deadline - self.max_e2e_lat,
                                                        job_matrix[j][0].period 
                                                        - job_matrix[j][0].offset 
                                                        - job_matrix[j][0].wcrt)
                             
                        else:
                            raise
                        assert job.robustness_margin >= 0   
                    elif job_matrix[j][0].let_semantics == True :  
                        if chain.e2e_deadline == None or chain.e2e_deadline == 'n/a':
                            job.delta_let = min(job_matrix[j][0].period 
                                                - job_matrix[j][0].offset 
                                                - job_matrix[j][0].let,
                                                job_matrix[j][0].period)
                        elif isinstance(chain.e2e_deadline, int):
                            job.delta_let = min(chain.e2e_deadline - self.max_e2e_lat,
                                                job_matrix[j][0].period
                                                - job_matrix[j][0].offset 
                                                - job_matrix[j][0].let,
                                                job_matrix[j][0].period)                       
                    else:  
                        raise  
                        assert job.delta_let >= 0                      
                else:            
                    if job_matrix[j][0].bet_semantics == True: 
                        job.robustness_margin = min(job.theta, 
                                                    job_matrix[j][0].period
                                                    - job_matrix[j][0].offset 
                                                    - job_matrix[j][0].wcrt) 
                        assert job.robustness_margin >= 0, 'RM of job ' + job.name + ' is negative.' 
                    elif job_matrix[j][0].let_semantics == True :   
                        job.delta_let = min(job.theta, 
                                            job_matrix[j][0].period 
                                            - job_matrix[j][0].offset 
                                            - job_matrix[j][0].let,
                                            job_matrix[j][0].period)
                        assert job.delta_let >= 0                          
                    else:  
                        raise                    
                


        # setting min theta/robustness margin/delta let for the task based on job results
        i=-1   
        for task in job_matrix:
            i += 1
            self.task_robustness_margins_dict[chain.tasks[i].name] = float('inf')
            self.task_delta_let_dict[chain.tasks[i].name] = float('inf')
            self.task_theta_dict[chain.tasks[i].name] = float('inf')
            for job in task: 
                if job_matrix[i][0].bet_semantics == True: 
                    if job.robustness_margin < self.task_robustness_margins_dict[chain.tasks[i].name]:
                        self.task_robustness_margins_dict[chain.tasks[i].name] = job.robustness_margin
                    if task == job_matrix[-1]:
                        self.task_theta_dict[chain.tasks[i].name] = 'n/a'
                    else:
                        if job.theta < self.task_theta_dict[chain.tasks[i].name]:
                            self.task_theta_dict[chain.tasks[i].name] = job.theta
                elif job_matrix[i][0].let_semantics == True :
                    # delta let
                    if job.delta_let < self.task_delta_let_dict[chain.tasks[i].name]:
                        self.task_delta_let_dict[chain.tasks[i].name] = job.delta_let
                    if task == job_matrix[-1]:
                        self.task_theta_dict[chain.tasks[i].name] = 'n/a'                        
                    else:
                        if job.theta < self.task_theta_dict[chain.tasks[i].name]:
                            self.task_theta_dict[chain.tasks[i].name] = job.theta 
                    # robustness margin    
                    if job_matrix[i][0].wcrt == 'n/a' or job_matrix[i][0].wcrt == None:
                        self.task_robustness_margins_dict[chain.tasks[i].name] = 'n/a since WCRT unknown'
                    elif isinstance(job_matrix[i][0].wcrt, int):
                        self.task_robustness_margins_dict[chain.tasks[i].name] = job_matrix[i][0].let - job_matrix[i][0].wcrt
                    else: 
                        raise
                    
                else:
                    raise
            
            if not (job_matrix[i][0].wcrt == 'n/a' or job_matrix[i][0].wcrt == None):
                assert self.task_robustness_margins_dict[chain.tasks[i].name] != float('inf')
                assert self.task_robustness_margins_dict[chain.tasks[i].name] >= 0
                assert self.task_robustness_margins_dict[chain.tasks[i].name] <= (chain.tasks[i].in_event_model.P 
                                                                                  - chain.tasks[i].wcrt 
                                                                                  - chain.tasks[i].release_offset) 
            if not task == job_matrix[-1]:
                assert self.task_theta_dict[chain.tasks[i].name] != float('inf')
                assert self.task_theta_dict[chain.tasks[i].name] >= 0
            
            if case == 3:
                assert self.task_delta_let_dict[chain.tasks[i].name] != float('inf') 
                

    
    def __gcd(self, a, b):
        """Helper function from pycpa.util, returns greatest common divisor using Euclid's Algorithm."""
        while b:
            a, b = b, a % b
        return a


    def __lcm(self, a, b):#from pycpa.util
        """Helper function from pycpa.uti, returns lowest common multiple."""
        return a * b // self.__gcd(a, b)          
    


    def __test(self):
        """
        Test for validity of robustness margins.
        """
        
        # add maximum disturbances to WCRT / LET
        wcrt_dict = dict() 
        let_dict = dict()
        for task in self.chain.tasks: 
            if task.bet_semantics == True:
                wcrt_dict[task.name] = task.wcrt 
            elif task.let_semantics == True:
                let_dict[task.name] = task.let
            
        for copied_task in self.copied_chain.tasks: 
            if copied_task.bet_semantics == True: 
                new_wcrt = (wcrt_dict[copied_task.name] + self.task_robustness_margins_dict[copied_task.name] - 1)
                assert new_wcrt <= copied_task.in_event_model.P - copied_task.release_offset
                copied_task.wcrt  = new_wcrt
                # create new results data structure
                self.copied_results[copied_task] = pycpa.analysis.TaskResult()
                self.copied_results[copied_task].wcrt = new_wcrt
                self.copied_results[copied_task].bcrt = copied_task.bcrt                 
                copied_task.analysis_results = self.copied_results[copied_task]                
            elif copied_task.let_semantics == True:
                # create new results data structure
                self.copied_results[copied_task] = pycpa.analysis.TaskResult()
                self.copied_results[copied_task].wcrt = copied_task.wcrt
                self.copied_results[copied_task].bcrt = copied_task.bcrt 
                copied_task.analysis_results = self.copied_results[copied_task]                  
                # update let
                new_let = (let_dict[copied_task.name] + self.task_delta_let_dict[copied_task.name] - 1)
                assert new_let <= copied_task.in_event_model.P - copied_task.release_offset
                copied_task.let = new_let
            else:
                raise
         
         
        #1) calculate hyper period of chain tasks
        self.copied_hyperperiod = self.__calc_hyperperiod(self.copied_chain)      
        
        
        #2) build a matrix of instantiated jobs
        l = 0
        for k in self.copied_chain.tasks:
            if(l==0):
                root = True
            else:
                root = False
            self.__set_jobs(k, self.copied_results, self.copied_hyperperiod, self.copied_job_matrix, root, l)
            l += 1
         
         
        # re-run latency analysis for increased WCRT resp. LET
        self.copied_path_matrix = self.__determine_paths(self.copied_job_matrix)
        self.copied_max_e2e_lat = self.__determine_max_e2e_lat(self.copied_path_matrix, test = True)         
               
        assert self.copied_max_e2e_lat != None 
        if self.copied_chain.e2e_deadline != None:
            assert self.copied_max_e2e_lat <= self.copied_chain.e2e_deadline, "The max. latency violates the specified e2e-deadline!"        
        
        

    
def compute_rm_min_all_chains(chain_results_dict, tasks, chains):
    """
    This function takes the robustness margins computed for each chain task of the isolated chains
    and computes the respective minimum over the set of cause-effect chains in the system.
    """   

    rm_min_all_chains_dict = dict()
    theta_min_all_chains_dict = dict()
    for task in tasks:
        rm_min_all_chains_dict[task.name]=float('Inf')     
        theta_min_all_chains_dict[task.name]=float('Inf')
    for task in tasks:
        for chain in chains:
            if task in chain.tasks:
                if task.let_semantics == True:
                    if task.wcrt == 'n/a' or task.wcrt == None or task.wcrt == 0: 
                        rm_min_all_chains_dict[task.name] = 'n/a since WCRT unknown'
                elif task.bet_semantics == True:
                    if rm_min_all_chains_dict[task.name] > chain_results_dict[chain.name].task_robustness_margins_dict[task.name]:
                        rm_min_all_chains_dict[task.name] = chain_results_dict[chain.name].task_robustness_margins_dict[task.name]
                    if task != chain.tasks[-1]:
                        if theta_min_all_chains_dict[task.name] > chain_results_dict[chain.name].task_theta_dict[task.name]:
                            theta_min_all_chains_dict[task.name] = chain_results_dict[chain.name].task_theta_dict[task.name]  
                    else:
                        theta_min_all_chains_dict[task.name] = 'n/a'
    chain_results_dict['RMs_system']= rm_min_all_chains_dict
    chain_results_dict['Theta_system'] = theta_min_all_chains_dict




def compute_delta_let_all_chains(chain_results_dict, tasks, chains):
    """
    This function takes the Delta LETs computed for each chain task of the isolated chains
    and computes the respective minimum over the set of cause-effect chains in the system.    
    """
    delta_let_all_chains_dict = dict()
    for task in tasks:
        delta_let_all_chains_dict[task.name]=float('Inf')     
    for task in tasks:
        for chain in chains:
            if task in chain.tasks:
                if delta_let_all_chains_dict[task.name] > chain_results_dict[chain.name].task_delta_let_dict[task.name]:
                    delta_let_all_chains_dict[task.name] = chain_results_dict[chain.name].task_delta_let_dict[task.name]
    chain_results_dict['Delta_LET_system']= delta_let_all_chains_dict    
    
   