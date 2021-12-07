#!/usr/bin/env python
# -*- coding: utf-8 -*- 
""" Toro
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes
         - Simon Bagschik
         - Alex Bendrick

Description
-----------
Parent module for software parts of a system. extTask and extEffectChain are derived from pyCPA,
with class Job added specifically for the BET/LET chain analysis. Class extEffectChain contains
functions for decomposing CECs and determining subchain deadlines. 
"""

from enum import Enum, auto
import math
from collections import deque

from pycpa import model

class extTask(model.Task): # pragma: no cover
    """
        Derived task class from pyCPA.
        It includes BET and LET semantics.
        It provides a function to instantiate jobs.
    """
    def __init__(self, name, release_offset, bcet, wcet,
                 scheduling_parameter,
                 semantic, let=None, wcrt=None, bcrt=None, deadline=None):
        model.Task.__init__(self, name) 
        self.release_offset = release_offset        
        self.bcet = bcet
        self.wcet = wcet
        self.scheduling_parameter = scheduling_parameter
        self.semantic = semantic
        self.let = let
        self.deadline = deadline
        self.wcrt = wcrt
        self.bcrt = bcrt

    def set_scheduling_paramter(self, scheduling_parameter):
        """ Define a task's priority if not already defined at a task's initilisation
        
        :param scheduling_parameter: task priority (int)
        :rtype: None
        """
        self.scheduling_parameter = scheduling_parameter

    def set_release_offset(self, release_offset):
        """ Define a task's release/activation offset, if not already defined at a task's initilisation
        
        :param release_offset: task release/activation offset (int)
        :rtype: None
        """
        self.release_offset = release_offset

    def set_system_level_task(self):
        """ Set flag showing a task is used as a LET interconnect task.
        
        :rtype: None
        """
        assert self.semantic == Semantic.LET, "Task " + self.name + " is not a LET task, therefore cannot be defined as LET interconnect task."
        self.sl_ic_task = True
 
    def instantiate_job(self, job_number, wcrt, bcrt):
        """ This function instantiates a job with ID job_number.
        
        :param job_number: job_index
        :param wcrt: task WCRT
        :param bcrt: task BCRT
        :rtype: None
        """
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
                  semantic=self.semantic,
                  deadline = self.deadline)

        if self.semantic == Semantic.BET: # NOTE added that line
            assert bcrt == self.bcet, ('Warning: check relation between bcrt = ' + str(bcrt) 
                                   +  ' and bcet = ' + str(self.bcet) 
                                   + ' for task ' + self.name + '.')
        elif (self.semantic == Semantic.LET) and (hasattr(self, 'sl_ic_task')):
            job.set_ic_task()
        return job
    
    

class Job(object): # pragma: no cover
    """ Parameterized job model."""
    def __init__(self, name, task_name, period, offset=None, bcet=None, wcet=None, let=None, bcrt=None,
                 job_number=None, wcrt=None, semantic=None, deadline=None):
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
        self.ic_task = False
        if deadline is None:
            self.deadline = period # implicit deadline
        else:
            self.deadline = deadline # arbitrary deadline
        self.Rmin = None
        self.Rmax = None
        self.Dmin = None
        self.Dmax = None
        self.robustness_margin = None
        self.slack = None      
        self.delta_let = None
        self.semantic = semantic
        self.set_RI_DI()

    def set_ic_task(self):
        """ set flag showing a job is used as a LET interconnect task.
        
        :rtype: None
        """
        self.ic_task = True

    def set_RI_DI(self):
        """ The function computes minimum and maximum read and data intervals of a job.
        [4] Equations (2.2a)-(2.2d) and (2.3a)-(2.3d).

        :rtype: None
        """
        # job belongs to BET task
        if self.semantic == Semantic.BET:
            assert self.wcet != None or self.wcet != 0, 'Unset WCET values for task! '+ self.task_name
            assert self.let == None or self.let == 0, 'Contradictory task parameters!'  
            self.Rmin = self.offset + (self.job_number - 1) * self.period
            self.Rmax = self.Rmin + self.wcrt - self.bcet            
            self.Dmin = self.Rmin + self.bcrt
            self.Dmax = self.offset + self.job_number * self.period + self.wcrt              
        elif self.semantic == Semantic.LET: 
            self.Rmin = self.offset + (self.job_number - 1) * self.period
            self.Rmax = self.Rmin
            self.Dmin = self.Rmin + self.let
            self.Dmax = self.offset + self.job_number * self.period + self.let
        else:
            raise NotImplementedError("Task semantic " + self.semantic + "not supported yet")

    
    def set_slack(self, theta):
        """ Update the job's maximum possible slack theta. 
        Results are stored on a job level. 

        :param theta: int
        :rtype: None
        """
        if theta >= 0:
            if (self.slack is None) or ((self.slack is not None) and (theta < self.slack)):
                self.slack = theta
    


class extEffectChain(model.EffectChain):
    """ Cause-effect chain representation in TORO. Derived from pyCPA

    Contains methods for decomposing chains and analysing those
    decomposed chains with regards to transition latencies and
    deadlines. Can also calculate subchain deadlines.
    """
    def __init__(self, name, tasks=None, e2e_deadline=None, subchain=False):
        model.EffectChain.__init__(self, name, tasks)
        self.e2e_deadline = e2e_deadline
        self.next_chains = list()

        if subchain is False:
            self.combined_latency = None

            self.combined_transistion_latencies = dict()
            self.combined_transistion_latencies['let'] = None
            self.combined_transistion_latencies['bet'] = None

        if subchain is True:
            # init subchains with additional parameters: latency, transition_latency, transition deadline, ...?
            self.transition_latency = None
            self.latency = None
            self.transition_deadline = None

        

    def set_semantic(self, semantic):
        """ set chain semantic

        :param semantic: Semantic
        :rtype: None
        """
        self.semantic = semantic

    
    def determine_semantic(self) -> bool:
        """ Determine and set semantic of chain. Must not work work if tasks with
        different semantics are included.
        
        :rtype: bool
        """
        
        semantic_tmp = None
        prev = None
        for task in self.tasks:
            print(task)
            if semantic_tmp is None:
                semantic_tmp = task.semantic
                print(semantic_tmp)
            else:
                # compare semantic/activation pattern with previous task
                if task.semantic != prev.semantic:
                    return False                    
            prev = task

        self.set_semantic(semantic_tmp)   
        
        return True


    def calculate_transition_latency(self, prevChain):
        """ Calculate the transition latency between the previous and current (self) subchain.
        (cf. [3] theorem 2 and [4] Equation (3.4)
        Function does save the value directly in prevChain AND returns the result seperatly.


        :param prevChain: TORO extEffectChain
        :rtype: int
        """
        assert (prevChain is not None), "Chain has not been initialized yet"

        if self.semantic == 'event-triggered':
            t_lat = 0
        elif prevChain.semantic == Semantic.BET:
            t = prevChain.tasks[-1]
            t_lat = t.in_event_model.P + t.wcrt - t.bcrt # TODO would imo still be valid after adding: - (t.wcrt - t.bcrt) --> = P
        elif prevChain.semantic == Semantic.LET:
            t = prevChain.tasks[-1]
            t_lat = t.in_event_model.P
        else:
            raise NotImplementedError("Calculation of transistion latencies between " + prevChain.semantic + " and " + self.semantic + "chains has not been implemented yet")

        prevChain.transition_latency = t_lat
        return t_lat
        
  
    def calculate_preliminary_deadline(self, total_deadline, sum_latencies, known_transition_deadlines):
        """
        This function calculates a preliminary subchain deadline (deadline_tilde).
        The more precise subchain deadlines are computed based on this preliminary one.
        (Cf. [4] Equation (3.7): BET transition deadlines are expected to be 0 at this point of time!)

        :param total_deadline: int
        :param sum_latencies: int
        :param known_transition_deadlines: dict
        """

        if total_deadline is None:
            # if no deadline has been defined, the maximum deadline has to be defined in a different way
            total_deadline = sum_latencies + known_transition_deadlines['let'] + known_transition_deadlines['bet']

        deadline_tilde = (self.latency / sum_latencies) * (total_deadline - known_transition_deadlines['let'])
        
        self.e2e_deadline = deadline_tilde


    def update_deadline(self, total_deadline, sum_latencies, chain_transition_deadlines):
        """ Update a subchain's e2e deadline (Equation (3.9) [4])

        :param total_deadline: int
        :param sum_latencies: int
        :param chain_transition_deadline: float
        """
        if total_deadline is None:
            total_deadline = sum_latencies # TODO + transition latencies?

        assert self.latency is not None, "Error: updating subchain deadlines without subchain latency not possible."
        deadline = (self.latency / sum_latencies) * (total_deadline - chain_transition_deadlines)

        assert self.latency <= (deadline), "Error: subchain deadline (" + str(deadline) + ") was violated: latency = " + str(self.latency)
        # results are always rounded of!
        self.e2e_deadline = math.floor(deadline) 
    
    
    def update_transition_deadline(self):
        """ Calculate a subchain's transition deadline (Equation (3.8) [4]).
        Only used for BET subchains.

        :rtype: int
        """
        if self.transition_latency is None:
            return 0

        transition_deadline = self.e2e_deadline - self.latency + self.transition_latency

        # TODO some assertion here as well?
        self.transition_deadline = transition_deadline
        return transition_deadline


    def calc_actual_deadlines(self):
        """ Implementation of Algorithm 6 [4].
        Updating preliminary deadlines and transition latencies repeatitly until
        a fix point has been reached.

        :rtype: list
        """
        # counter
        cnt = 0
        
        # ring buffer for checking for a basic form of convergence 
        ring_buffer = deque(maxlen=2)

        while True:
            results = list()
            sum_transition_deadlines = 0

            # accumulate transition deadlines of all subchains belonging to a cause-effect chain
            for subchain in self.decomposed_chains:
                if (subchain.semantic == Semantic.BET):
                    sum_transition_deadlines += subchain.update_transition_deadline()
                elif (subchain.semantic == Semantic.LET):
                    if subchain.transition_latency is not None:
                        # LET subchain transition latencies is either = P (per def) or 0 if consecutive subchain is event-triggered
                        sum_transition_deadlines += subchain.transition_latency
                else:
                    raise NotImplementedError("Procesing of chains that use a %s semantic has not been implemented yet" % subchain.semantic)
            
            # update subchain deadline and create result vector used for convergence testing
            sum_deadlines = 0
            for subchain in self.decomposed_chains:
                subchain.update_deadline(self.e2e_deadline, self.combined_latency, sum_transition_deadlines)
                res = (subchain.e2e_deadline, subchain.transition_deadline)
                results.append(res)

                sum_deadlines += subchain.e2e_deadline
                if subchain.transition_deadline is not None:
                    sum_deadlines += subchain.transition_deadline

            # check for convergence
            if results in ring_buffer:
                # if the results vector can be found in the ring buffer, a fix point has been reached
                # the ring buffer is used to be prone to alternating values that might occur
                # Note: sum_deadlines already contains both "normal" and transition deadlines
                assert sum_deadlines <= self.e2e_deadline, "Chain end-to-end deadline has been violated: deadline = " + str(self.e2e_deadline) +  " - latency = " + str(sum_deadlines)
                return results
            
            ring_buffer.append(results)

            cnt += 1






class Semantic(Enum): # pragma: no cover
    """ enum for storing all task semantics """
    LET = auto()
    BET = auto()
    EVENT_TRIGGERED = auto()
    SPORADIC = auto()
    MISC = auto()