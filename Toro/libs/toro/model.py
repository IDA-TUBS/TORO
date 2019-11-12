""" Toro
| Copyright (C) 2019 TU Braunschweig, Institute for Computer and Network Engineering
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
    def __init__(self, name, release_offset, let_semantics, bet_semantics, let, *args, **kwargs):
        model.Task.__init__(self, name, *args, **kwargs)
        self.release_offset = release_offset
        self.let_semantics = let_semantics
        self.bet_semantics = bet_semantics
        self.let = let
 
    def instantiate_job(self, job_number, semantics, wcrt, bcrt):
        """This function instantiates a job with ID job_number."""
        job = Job(name=self.name, 
                  period=self.in_event_model.P, 
                  offset=self.release_offset,
                  wcet=self.wcet, 
                  let=self.let, 
                  job_number=job_number, 
                  knowledge_base=semantics, 
                  wcrt=wcrt,
                  bcrt=bcrt)
        return job


class Job(object):
    """ Parameterized job model."""
    def __init__(self, name, period, offset=None, wcet=None, let=None, bcrt=None,
                 job_number=None, knowledge_base=None, wcrt=None):
        self.period = period
        self.offset = offset
        self.job_number = job_number
        self.name = (name + ",%d" % self.job_number)
        self.wcet = wcet
        self.wcrt = wcrt
        self.bcrt = bcrt
        self.let = let
        self.Rmin = 0
        self.Rmax = 0
        self.Dmin = 0
        self.Dmax = 0
        self.robustness_margin = None
        self.successor_jobs = list() # stores successor jobs for that follows() returns True
        self.set_RI_DI(knowledge_base)

    def set_RI_DI(self, knowledge_base):
        """
        The function computes minimum and maximum read and data intervals of a job.
        """
        if(knowledge_base == 'BET_with_known_WCRTs'):
            if self.wcet != None:
                # case 2
                self.Rmin = self.offset + (self.job_number -1 ) * self.period
                self.Rmax = self.Rmin + self.wcrt - self.wcet
                self.Dmin = self.Rmin + self.wcet
                self.Dmax = self.offset + self.job_number * self.period + self.wcrt
            else:
                # case 1
                self.Rmin = self.offset + (self.job_number -1 ) * self.period
                self.Rmax = self.job_number * self.period - self.bcrt
                self.Dmin = self.Rmin + self.bcrt
                self.Dmax = self.offset + self.job_number * self.period + self.wcrt                
                
        elif(knowledge_base == 'LET'):
            self.Rmin = self.offset + (self.job_number -1 ) * self.period
            self.Rmax = self.Rmin
            self.Dmin = self.Rmin + self.let
            self.Dmax =  self.offset + self.job_number * self.period + self.let

        else:
            print("No valid knowledge base. Valid: BET_with_known_WCRTs,"
                  "LET")
            raise SystemExit(1)
        
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
