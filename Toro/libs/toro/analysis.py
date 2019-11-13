#!/usr/bin/env python
# -*- coding: utf-8 -*- 
""" Toro
| Copyright (C) 2019 Innovationsgesellschaft Technische Universit�t Braunschweig mbH (iTUBS)
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes
         - Simon Bagschik

Description
-----------
Calculation of an upper bound on the end-to-end latency of a cause-effect chain. 
The analysis relies on Becker et al. 2017 + 2018.
"""

from toro import plot
import copy

class calc_latencies_robustness(object):
    """
    This class contains function to compute the maximum end-to-end latency and the 
    robustness margins for a given cause-effect chain.
    """
    log_robustness_margins = dict()
    log_max_data_age = dict()

    def __init__(self, chain, semantics, results):
        """ 
        If the class 'calc_latencies_robustness' is initialized, it will compute the
        maximum end-to-end latency and the robustness margins for 'chain'. 
        """
        self.chain = chain
        self.job_matrix = list()
        self.semantics = semantics 
        #1) calculate hyper period of chain tasks
        self.hyperperiod = self.__calc_hyperperiod(chain)       
        #2) build a matrix of instantiated jobs
        l = 0
        for k in chain.tasks:
            if(l==0):
                root = True
            else:
                root = False
            self.__set_jobs(k, semantics, results, self.hyperperiod, self.job_matrix, root, l)
            l += 1
        # 3) determine possible paths & calculate maximum data age
        self.path_matrix = self.__determine_paths(self.job_matrix)
        self.max_data_age = self.__determine_age_max(self.path_matrix, semantics)
        assert self.max_data_age == 'n/a' or self.max_data_age == None or \
        self.max_data_age <= chain.e2e_deadline, \
        "The max. latency violates the specified e2e-deadline!"
        # 4) calculate robustness margins
        self.task_robustness_margins_dict = dict()
        for task in chain.tasks:
            self.task_robustness_margins_dict[task.name] = None
        self.__calc_robustness_margins(self.job_matrix, chain)


    def __calc_hyperperiod(self, chain):
        """This function calculates the hyper period of the chain tasks."""
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


    def __set_jobs(self, task, semantics, results, HP, job_matrix, root, l):
        """Instantiate the set of jobs needed for the reachability analysis in a job matrix."""
        job_line = list()
        job_number = 1
   
        if(root):
            # instantiate all jobs of the root task in the hyper period 
            for k in range(int(HP / task.in_event_model.P)):
                current_job = task.instantiate_job(job_number=job_number, semantics=semantics, wcrt=results[task].wcrt, bcrt=results[task].bcrt)
                current_job.parent_task = task
                job_line.append(current_job)
                job_number += 1
            job_matrix.append(job_line)
        else:
            # instantiate successor jobs whose Rmin is smaller or equal to Dmax of the task last job
            border = job_matrix[l-1][-1].Dmax
            while True:
                current_job = task.instantiate_job(job_number, semantics, results[task].wcrt, bcrt=results[task].bcrt)
                current_job.parent_task = task
                if (current_job.Rmin <= border):
                    job_line.append(current_job)
                    job_number += 1
                else:
                    job_matrix.append(job_line)
                    break
        return


    def __determine_paths(self, job_matrix):
        """This function determines paths in the job matrix and returns path matrix."""
        # assign successor jobs to jobs in job_matrix
        for i in range(len(job_matrix) - 1):  # iterate over rows in matrix
            for k in range(len(job_matrix[i])):  # iterate over columns in row
                # determine starting job of successor, see Eq. 2 of Becker et al. [2]
                l = int(job_matrix[i][k].Dmin / job_matrix[i + 1][0].period)
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
        """Check reachability between jobs using Eq. 1 of Becker et al. [2] """
        if ((cons_job.Rmax >= prod_job.Dmin) and (cons_job.Rmin < prod_job.Dmax)):
            return True
        else:
            return False


    def __determine_age_max(self, possible_paths, semantics):
        """Function determines the path with the longest latency."""
        if (len(possible_paths) == 0):
            assert False, "No reachable paths!"
            return 0
        else:
            data_ages = []
            for k in range(len(possible_paths)):
                if (semantics == "BET_with_known_WCRTs"):
                    data_ages.append((possible_paths[k][-1].Rmax + possible_paths[k][-1].wcrt)
                                     - possible_paths[k][0].Rmin)
                if(semantics == "LET"):
                    data_ages.append(possible_paths[k][-1].Dmin - possible_paths[k][0].Rmin)
            data_ages = []
            for k in possible_paths:
                s = ""
                for i in k:
                    s += " -> " + i.name  
                if (semantics == "LET"):
                    data_age = k[-1].Dmin - k[0].Rmin
                if (semantics == "BET_with_known_WCRTs"):
                    data_age = k[-1].Rmax + k[-1].wcrt - k[0].Rmin
                data_ages.append(data_age)
                #print(s + " | Max: " + str(data_age))
            return max(data_ages)
        

    def __calc_robustness_margins(self, job_matrix, chain):
        """
        This function computes robustness margins that relate to an isolated cause-effect chain 
        (not the set of cause-effect chains).
        
        Variables:
        \tau_{k+1}(q+1): next_task_next_job_num: 
        \tau_{k+1}(q): job_matrix[task][job].rm_job
        => note that the job-index of job_matrix starts at 0 but job_number starts at 1
        """        
        for task in range(len(job_matrix)-1):
            i = 0
            for job in range(len(job_matrix[task])):
                if len(job_matrix[task][job].successor_jobs) == 0:
                    pass
                else:
                    next_task_next_job_num = job_matrix[task][job].successor_jobs[-1].job_number 
    
                    if next_task_next_job_num < len(job_matrix[task+1]):
                        job_matrix[task][job].robustness_margin = job_matrix[task+1][next_task_next_job_num].Rmin - job_matrix[task][job].Dmax
                        job_matrix[task][job].rm_job = job_matrix[task+1][next_task_next_job_num]
                        #print("Job: %s -> %s -  RM: %d" % (job_matrix[task][job].name,job_matrix[task+1][next_task_next_job_num].name , job_matrix[task][job].robustness_margin))
                    else:
                        i += 1
                        job_matrix[task][job].robustness_margin = \
                        job_matrix[task+1][next_task_next_job_num - 1].Rmin + \
                        job_matrix[task+1][next_task_next_job_num - 1].period * i - \
                        job_matrix[task][job].Dmax 
                        job_matrix[task][job].rm_job = job_matrix[task+1][next_task_next_job_num - 1]
                        #print("Job: %s -> %s -  RM: %d" % (job_matrix[task][job].name,job_matrix[task+1][next_task_next_job_num - 1].name , job_matrix[task][job].robustness_margin))

        # ensure that also task deadline is satisfied
        max_rm_dict = dict()
        for task in self.chain.tasks:        
            if self.semantics == 'BET_with_known_WCRTs':
                max_rm_dict[task.name] = task.in_event_model.P - task.release_offset - task.wcrt 
            elif self.semantics == 'LET':
                max_rm_dict[task.name] = task.in_event_model.P - task.release_offset - task.let
                #print max_rm_dict[task.name]
            else:
                assert False, 'Error: specified semantics are not supported.'
              
        for task in job_matrix:                
            for job in task:
                if job.robustness_margin != None:
                    job.robustness_margin = min(job.robustness_margin, max_rm_dict[job.task_name]) 

        # setting the robustness margin for the task based on job robustness margins
        i=-1
        for task in job_matrix:          
            i += 1
            self.task_robustness_margins_dict[chain.tasks[i].name] = float('inf')
            for job in task:         
                if job.robustness_margin != None:
                    if job.robustness_margin < self.task_robustness_margins_dict[chain.tasks[i].name]:
                        self.task_robustness_margins_dict[chain.tasks[i].name] = job.robustness_margin
            if not chain.tasks[i].name == chain.tasks[-1].name:
                assert self.task_robustness_margins_dict[chain.tasks[-1].name] != float('inf'), \
                'ERROR: unexpected value for robustness margin'
            else:
                assert self.task_robustness_margins_dict[chain.tasks[i].name] == float('inf'), \
                'ERROR: unexpected value for robustness margin'                
                
        # set robustness margin for tail task
        if chain.e2e_deadline == None or chain.e2e_deadline == 'n/a':
            self.task_robustness_margins_dict[chain.tasks[-1].name] = \
            max_rm_dict[chain.tasks[-1].name]
        elif isinstance(chain.e2e_deadline, int):
            self.task_robustness_margins_dict[chain.tasks[-1].name] = \
            min(chain.e2e_deadline - self.max_data_age, max_rm_dict[chain.tasks[-1].name])        
            
    
    def __gcd(self, a, b):
        """Helper function from pycpa.util, returns greatest common divisor using Euclid's Algorithm."""
        while b:
            a, b = b, a % b
        return a


    def __lcm(self, a, b):#from pycpa.util
        """Helper function from pycpa.uti, returns lowest common multiple."""
        return a * b // self.__gcd(a, b)          
    
    
def compute_rm_min_all_chains(chain_results_dict, tasks, chains):
    """
    This function takes the robustness margins computed for each chain task of the isolated chains
    and computes the respective minimum over the set of cause-effect chains in the system.
    """   
    rm_min_all_chains_dict = dict()
    for task in tasks:
        rm_min_all_chains_dict[task.name]=float('Inf')    
                      
    for task in tasks:
        for chain in chains:
            if task in chain.tasks:
                if rm_min_all_chains_dict[task.name] > chain_results_dict[chain.name].task_robustness_margins_dict[task.name]:
                    rm_min_all_chains_dict[task.name] = chain_results_dict[chain.name].task_robustness_margins_dict[task.name]

    
    chain_results_dict['RMs_system']= rm_min_all_chains_dict