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
Calculation of an upper bound on the end-to-end latency of a cause-effect chain. 
The analysis relies on Becker et al. 2017 + 2018.
"""

from pycpa import model
import copy

class extTask(model.Task):
    """
        Derived task class from pyCPA.
        It includes BET and LET semantics.
        It provides a function to instantiate jobs.
    """
    def __init__(self, name, release_offset, bcet, wcet,
                 scheduling_parameter,   
                 let_semantics, bet_semantics, let):
        model.Task.__init__(self, name) 
        self.release_offset = release_offset        
        self.bcet = bcet
        self.wcet = wcet
        self.scheduling_parameter = scheduling_parameter
        self.let_semantics = let_semantics
        self.bet_semantics = bet_semantics
        self.let = let
 
    def instantiate_job(self, job_number, wcrt, bcrt):
        """This function instantiates a job with ID job_number."""
        job = Job(name=self.name, 
                  task_name = self.name,
                  period=self.in_event_model.P, 
                  offset=self.release_offset, 
                  bcet = self.bcet,
                  wcet=self.wcet, 
                  let=self.let, 
                  job_number=job_number, 
                  wcrt=wcrt,
                  bcrt=bcrt,
                  let_semantics = self.let_semantics,
                  bet_semantics = self.bet_semantics)
        return job


class Job(object):
    """ Parameterized job model."""
    def __init__(self, name, task_name, period, offset=None, bcet=None, wcet=None, let=None, bcrt=None,
                 job_number=None, wcrt=None, let_semantics=None, bet_semantics=None):
        self.task_name = task_name
        self.period = period
        self.offset = offset
        self.job_number = job_number
        self.name = (name + ",%d" % self.job_number)
        self.bcet = bcet
        self.wcet = wcet
        self.wcrt = wcrt
        self.bcrt = bcrt
        self.let = let
        self.Rmin = None
        self.Rmax = None
        self.Dmin = None
        self.Dmax = None
        self.robustness_margin = None
        #self.robustness_margin_corrected = None      
        self.delta_let = None  
        self.successor_jobs = list() # stores successor jobs for that follows() returns True
        self.let_semantics = let_semantics
        self.bet_semantics = bet_semantics        
        self.set_RI_DI()

    def set_RI_DI(self):
        """
        The function computes minimum and maximum read and data intervals of a job.
        """
        # job belongs to BET task
        if self.bet_semantics == True: 
            #print('Set R/D intervals for BET job.')
            assert self.wcet != None or self.wcet != 0, 'Unset WCET values for task! '+ self.task_name
            assert self.let == None or self.let == 0, 'Contradictory task parameters!'  
            self.Rmin = self.offset + (self.job_number -1 ) * self.period
            self.Rmax = self.Rmin + self.wcrt - self.bcet            
            self.Dmin = self.Rmin + self.bcrt
            self.Dmax = self.offset + self.job_number * self.period + self.wcrt              
        elif self.let_semantics == True:
            #print('Set R/D intervals for LET job.')         
            self.Rmin = self.offset + (self.job_number -1 ) * self.period
            self.Rmax = self.Rmin
            self.Dmin = self.Rmin + self.let
            self.Dmax = self.offset + self.job_number * self.period + self.let
        else:
            raise
        
    def iterate(self, current_path, path_matrix, size):
        """Recursive function to extract possible paths and store in path_matrix."""
        current_path.append(self)
        for c in self.successor_jobs:
            c.iterate(list(current_path), path_matrix, size) # copy
        # a possible path is only appended if the length is equal to the number of tasks (=size)
        if ((len(self.successor_jobs) == 0) and (len(current_path) == size)):
            path_matrix.append(copy.deepcopy(current_path))


class extEffectChain(model.EffectChain):
    def __init__(self, name, tasks=None, e2e_deadline=None):
        model.EffectChain.__init__(self, name, tasks)
        self.e2e_deadline = e2e_deadline
        self.next_chains = list()
        
    #link dependent chain for visualization
    def link_dependent_chain(self, c):
        self.next_chains.append(c)
        if isinstance(c, extEffectChain):
            c.prev_chain = self
        else:
            pass
        return c
