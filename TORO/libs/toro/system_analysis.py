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
    - Alex Bendrick
 
Description
===========
Contains the function perform_analysis() that calls all mandatory (and optional) functions
needed to analysis a system with multiple resources, tasks and cause-effect chains. Also parent module
of class SystemAnalysisResults that is used to aggregate analysis results for store or later processing.
"""

import copy
import sys
from collections import deque

sys.path.append(sys.path[0] + "/libs/")


import pycpa
from pycpa import analysis # NOTE: only here for pytest

from . import io
from . import model
from . import chain_analysis as ChainAnalysis

Semantic = model.Semantic
toro_analysis_BET_LET = ChainAnalysis.analysis_LET_BET

## dict of chain analysis objects for each sub_chain
analyses = dict()



class SystemAnalysisResults(object):
    """ class for storing analyses results """

    def __init__(self, system_name, chain_latencies, robustness_margins, delta_let, **kwargs):
        """
        :param system_name: string
        :param chain_latencies: dict
        :param robustness_margins: dict
        :param delta_let: dict
        """
        self.system_name = system_name
        self.chain_latencies = chain_latencies
        self.robustness_margins = robustness_margins
        self.delta_let = delta_let

        self.__dict__.update(kwargs)

    def __eq__(self, other):
        """ compare SystemAnalysisResults objects using their attributes

        :param other: SystemAnalysisResults object
        :rtype: bool
        """
        print(other.toString())
        print("---")
        if not(isinstance(other, SystemAnalysisResults)): # pragma: no cover
            return False
        else:
            assert self.system_name == other.system_name
            assert self.chain_latencies == other.chain_latencies, "chain latencies differ: " + str(self.chain_latencies) + " vs (reference): " + str(other.chain_latencies)
            assert self.robustness_margins == other.robustness_margins
            assert self.delta_let == other.delta_let
            return (self.system_name == other.system_name 
                and self.chain_latencies == other.chain_latencies 
                and self.robustness_margins == other.robustness_margins
                and self.delta_let == other.delta_let)

    def toString(self):
        """ print results to string

        :rtype: string
        """

        writer = io.ResultsWriter()
        s = writer.results_to_string(self)

        return s

    def toCSV(self, dir):
        """ print result to csv files

        :rtype: None
        """

        writer = io.ResultsWriter()

        writer.chain_results_to_csv(self, dir)
        writer.robustness_results_to_csv(self, dir)
        writer.task_results_to_csv(self, dir)
        if(self.slack is not None):
            writer.slack_to_csv(self, dir)




class argsDummy(object):
    """ dummy class for analyses arguments that can be used
    if the args perform_analyis received have to be altered
    for some operations to limit unneccessary overhead """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)




#----------------------------#
# analysis system properties #
#----------------------------#


def perform_analysis(args, system, chains, performance_eval=False):
    """ calls all functions for performing the latency
    and robustness analyses.

    :param args: list
    :param system: pyCPA System object
    :param chains: TORO extEffectChain object
    :param performance_eval: bool
    :rtype: SystemAnalysisResults object
    """

    # use pycpa to calculate response times of all tasks
    if (args.wcrt is True):
        task_results = calculate_wcrt(system)

    # check for implicit deadline violations
    if (check_task_deadlines(system) != 0) and (performance_eval is False):
        # Note: performance_eval addition only neccessary to use systems that might violate task deadlines for performance analysis as well
        assert False, "Analysis stops for this system because the assumption of satisfied implicit deadlines is violated!" # pragma: no cover

    # Analysis:
    if (args.rm is True or args.lat is True):
        # dict for storing the results of all latency chain analyses
        chain_latencies = dict()

        # list for storing the analysis results
        robustness_margins = list()
        delta_let = list()
        slack = list()   
        

        for chain in chains:
            io.PrintOuts.newline()
            io.PrintOuts.doubleline()
            print('Analyzing cause-effect chain: ' + chain.name + "\n" + str([task.name for task in chain.tasks]))

            # determine chain semantic
            if(not chain.determine_semantic()):
                quit("Cannot analyze chains with tasks of different semantic!")

                
            # calculate only robustness margins and delta let values of a chain
            args_tmp = argsDummy(lat=args.lat, rm=args.rm, plot=args.plot)
            lat, t_lat, rm, dlet, slk = analyse_chain(chain, previousChain=None, args=args_tmp)

            chain_latencies[chain.name] = lat

            if (args.rm is True):
                if bool(rm):
                    # create list of dictionaries
                    robustness_margins.append(rm)
                if bool(dlet):
                    # create list of dictionaries
                    delta_let.append(dlet)
                if(slk):
                    # create list of dictionaries
                    slack.append(slk)


        # calculate the largest possible robustness margin/delta let for each task based on the result from every cause-effect-chain
        if (args.rm is True):
            # robustness_margins and delta_let are dictionaries as of here
            robustness_margins, delta_let = calc_min_rm_and_dlet(robustness_margins, delta_let)
            slack = calc_min_slack(slack)

        # print results to console and TODO write results to csv/model
        if (args.lat is True):
            io.PrintOuts.newline() 
            io.PrintOuts.doubleline()
            for chain, latency in chain_latencies.items():                
                print("The maximum end-to-end latency of chain \"%s\" is %d." %(chain, latency))
        if (args.rm is True):
            io.PrintOuts.line()
            for task, rm in sorted(robustness_margins.items()):
                print("Robustness margin of task \"%s\" is %d." %(task, rm))
            io.PrintOuts.line() 
            for task, dlet in sorted(delta_let.items()):
                print("Delta LET of task \"%s\" is %d." %(task, dlet))

        # verify, whether the robustness margins actually do not lead to deadline misses
        if (args.test is True):
            verify_margins(chains, task_results, robustness_margins, delta_let)


        # return final analysis results       
        results = SystemAnalysisResults(system.name, chain_latencies, robustness_margins, delta_let, slack=slack, system=system, task_results=task_results)
        return results




def calculate_wcrt(pycpa_system):
    """ calculates the worst-case response times of the task set.
    If any wcrt are already defined in the processed model, use those values

    :param pycpa_system: pyCPA System object
    :rtype: dict
    """
    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    print("Calculating worst-case response times of tasks.")    
    io.PrintOuts.line() 

    task_results = dict()

    # intialize task result objects for all tasks of the system
    for r in pycpa_system.resources:
        for t in r.tasks:
            task_results[t] = pycpa.analysis.TaskResult()
            t.analysis_results = task_results[t]
    
    # list of tasks with unknown wcrt
    unknown = list()
    for r in pycpa_system.resources:
        for t in r.tasks:
            # first check whether wcrt and bcrt of a task are already known
            # if there are any let tasks in list of tasks with unknown wcrt, ignore those
            if (t.wcrt is None) and not (t.semantic == Semantic.LET):
                # wcrt unknown
                unknown.append(t)
            else:                    
                # bcrt and wcrt known
                task_results[t].wcrt = t.wcrt    
                task_results[t].bcrt = t.bcrt
                if not (t.semantic == Semantic.LET):
                    t.bcet = copy.copy(t.bcrt)    

    if len(unknown) > 0:
        # some tasks' wcrts are still unknown -> use pycpa to calculate those

        # wcrt calculation only possible, if wcet defined for all tasks!
        tmp = list()
        for r in pycpa_system.resources :
            for t in r.tasks:
                tmp.append(t)
                assert (t.wcet is not None), "Tasks with unknown worst case execution time were found in the processed System. The WCET has to be defined for every task. Therefore pyCPA is not able to calculate WCRTs."

        try:
            tmp_results = pycpa.analysis.analyze_system(pycpa_system)

            for r in pycpa_system.resources:
                for t in r.tasks:
                    # only update those result that have been unknown so far
                    if t in unknown:
                        t.bcrt = tmp_results[t].bcrt
                        t.wcrt = tmp_results[t].wcrt

                        task_results[t].wcrt = tmp_results[t].wcrt
                        task_results[t].bcrt = tmp_results[t].bcrt
        except:        
            assert False, "WCRT-computation with pyCPA failed."

    for task, results in task_results.items():
        print("%s: BCRT=%s,\tWCRT=%s" %(task, str(results.bcrt), str(results.wcrt)))

    return task_results




# TODO change do use the arbitrary deadline attribute of TORO extTasks
def check_task_deadlines(pycpa_system):
    """ check whether all tasks satisfy their deadline constraints

    :param pycpa_system: pyCPA system object
    :rtype: int
    """
    num_unsched_tasks = 0

    for r in pycpa_system.resources:
        for t in r.tasks:
            if not (isinstance(t.wcrt, int)):#(t.wcrt == None or t.wcrt == 'unknown' or t.wcrt == 'n/a'):   
                pass
            else:
                if (t.semantic == Semantic.BET):
                    if not (t.wcrt <= t.in_event_model.P - t.release_offset):
                        print('Task ' + t.name + ' violates its implicit deadline by ' + str(t.wcrt - t.in_event_model.P - t.release_offset))   
                        num_unsched_tasks += 1
                if (t.semantic == Semantic.LET):
                    if hasattr(t, 'sl_ic_task'):
                        if (t.sl_ic_task is True):
                            # skip since sl let ic tasks do not have implicit deadlines
                            continue
                    if not (t.wcrt <= t.let):
                        print('Task ' + t.name + ' violates its implicit deadline by ' + str(t.wcrt - t.let))   
                        num_unsched_tasks += 1
    
    return num_unsched_tasks




def group_synchronized_resources(system): # pragma: no cover
    """ create groups of resources which clocks are prefectly synchronized

    :param system: pyCPA system
    :rtype: pythons sets
    """
    pass




def analyse_chain(chain, previousChain, args):
    """ analyses a cause-effect chain

    :param prev_chain: TORO extEffectChain object
    :param args: argparse arguments
    """
    global analyses

    io.PrintOuts.line()
    print('Analyzing subchain: ' + chain.name + "\n" + str([task.name for task in chain.tasks]))

    e2e_lat = 0
    t_lat = 0
    robustness_margins = dict()
    delta_let = dict()
    task_slack = dict()

    chain_type = chain.semantic

    visualize = False
    if (args.plot is True): # pragma: no cover
        # initialize graph in preparation for plotting the reachability graph later
        visualize = True

    if chain not in analyses.keys():
        # the (sub)chain has not been processed yet:
        if (chain_type in [Semantic.BET, Semantic.LET]):
            analysis = toro_analysis_BET_LET.ChainAnalysis(chain, vis=visualize)
        elif (chain_type == Semantic.EVENT_TRIGGERED):
            raise NotImplementedError("The analysis of %s cause-effect-chains has not been implemented yet!" % chain_type)
        elif (chain_type == Semantic.SPORADIC):
            raise NotImplementedError("The analysis of %s cause-effect-chains has not been implemented yet!" % chain_type)
        else:
            raise NotImplementedError("The analysis of %s cause-effect-chains has not been implemented yet!" % chain_type)
        
        # store analysis object used for a (sub)chain for later use
        analyses[chain] = analysis

        # build the reachability graph
        analysis.build_graph()
    else:
        # load already exisiting analyses object for that (sub)chain with an already built data propagation graph
        analysis = analyses[chain]
    
    # for all instances:
    if (args.lat is True): # TODO: and chain.transition_latency is None possible as well!
        # option 1: execute e2e latency analysis
        print("Calculating maximum end-to-end latencies of cause-effect chains.")
        e2e_lat = analysis.calculate_e2e_lat(print_all=False)

    if (args.rm is True):
        # option 2: calculate robustness margins/delta let
        print("Calculating robustness margins of cause-effect chain %s." % chain.name)
        robustness_margins, delta_let, task_slack = analysis.calculate_robustness_margins()

    if (args.plot is True):
        # TODO only very basic plotting function that does not scale well, update/rewrite for better plots
        analysis.plot('drawIntervals')

    return e2e_lat, t_lat, robustness_margins, delta_let, task_slack




def verify_margins(chains, task_results, robustness_margins, delta_let):
    """ verifiy whether the robustness margins calculated for all of the system's tasks
    will not violate any CEC deadlines if applied to the CECs' tasks

    :param chains: list of TORO extEffectChains
    :param robustness_margins: dict
    :param delta_let: dict
    """
    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    print('Verify correctness of robustness margins and delta let values:')
    io.PrintOuts.line()

    failure_cnt = 0

    # rebuild data propagation graphs and reevalutate e2e latency (of subchains) as well as transition latencies
    for chain in chains:
        if chain.e2e_deadline is None:
            # skip chains, that do not have a predefined e2e latency
            continue

        print('Chain: ', chain.name)
            
        res, chain_latency = analyses[chain].test(robustness_margins, delta_let)

        if chain_latency <= chain.e2e_deadline:
            print("Applying robustness margins leads to no deadline miss for chain " + chain.name + "\n\tnew e2e latency: " + str(chain_latency) + " vs deadline: " + str(chain.e2e_deadline) + "\n")

    if failure_cnt == 0:
        print('Verification succeded:\nDeadlines are still adhered to after applying robustness margins and delta let to tasks')
    else:
        print('Verification failed:\nSome robustness margins or delta let values lead to the possibiliy of deadline misses')
    io.PrintOuts.newline()  
    io.PrintOuts.doubleline()




def calc_min_rm_and_dlet(list_rm, list_dlet):
    """ calculates the robustness margins/delta let values for all tasks
    based on the analyses of all cause-effect chains defined for a given system

    :param list_rm: list of dicts
    :param list_dlet: list of dicts
    :rtype: dict, dict
    """
    rm = dict()
    dlet = dict()
    
    if len(list_rm) > 0:
        for dictionary in list_rm:
            for key, value in dictionary.items():
                if (key not in rm.keys() or rm[key] > value) and not(isinstance(value, list)):
                    rm[key] = value
    
    if len(list_dlet) > 0:
        for dictionary in list_dlet:
            for key, value in dictionary.items():
                if (key not in dlet.keys() or dlet[key] > value) and not(isinstance(value, list)):
                    dlet[key] = value
    
    return rm, dlet

def calc_min_slack(lst_slack):
    """ calculates the min slack of all tasks based on the analyses 
    of all cause-effect chains defined for a given system

    :param list_rm: list of dict containing task slacks
    """
    slk = dict()
    
    if len(lst_slack) > 0:
        for dictionary in lst_slack:
            for key, value in dictionary.items():
                if (key not in slk.keys() or slk[key] > value) and not(isinstance(value, list)):
                    slk[key] = value
    
    return slk
