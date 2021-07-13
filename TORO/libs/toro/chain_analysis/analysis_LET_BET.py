#!/usr/bin/env python
# -*- coding: utf-8 -*- 

""" Toro
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Alex Bendrick

Description
-----------
This module provides classes and functions to compute an upper bound on the end-to-end latency and robustness 
margins for a given time-triggered cause-effect chain. 
The latency analysis relies on Becker et al. 2016 [1] + 2017 [2]. Modifications with regards to offsets and the
robustness analysis added on top of the CEC latency analysis are described in [3]. To perform the analysis, graph
libraries are used, that can be accessed using the graph_wrapper interface. A detailed descriptions of the graph
based latency analysis as implemented here can be found in [4].
"""

import math
from typing import Dict, List, Union, Tuple

from .. import model
Semantics = model.Semantic

from .. import graph_wrappers as wrappers

from .analysis_bc import ChainBaseClass
from .analysis_bc import GraphNotBuiltException



Wrapper = "NX" # choose either "NX" or "GT"
if Wrapper == "NX":
    Graph = wrappers.networkx_wrapper
elif Wrapper == "GT":
    Graph = wrappers.graphtool_wrapper
else:
    raise NotImplementedError("Incompatible graph wrapper \"" + Wrapper + "\" selected!")



class ChainAnalysis(ChainBaseClass):
    """ This class contains function to compute the maximum end-to-end latency and the 
    robustness margins for a given cause-effect chain, that contains time-triggered
    LET or BET tasks only.
    """ 
    def __init__(self, chain:model.extEffectChain, vis:bool=False):
        """ constructor """

        ## networkx/graph-tool graph representing the reachability graph
        self.__data_prop_graph = None

        ## local copy of the cause effect chain
        self.__cec = chain
        cec_length = len(self.__cec.tasks)

        ## task set used ofr hyperperiod calculation
        self.__tasks = self.__cec.tasks

        ## identifier (name) of first task in cec 
        self.__first_task_name = self.__cec.tasks[0].name
        ## identifier (name) of last task in cec
        self.__last_task_name = self.__cec.tasks[cec_length - 1].name

        ## hyperperiod of task set used within the chain
        self.__hyperperiod = -1

        ## flag: enable/disable graph visualisation
        self.__vis = vis

        ## analysis results: max end-to-end latency of the cec
        self.__max_e2e_lat = None








    ############################
    # build reachability graph #
    ############################

    def build_graph(self) -> None:
        """ builds an actual graph based on the system information provided in the constructor call """

        # create empty graph
        self.__data_prop_graph = Graph.Graph()

        if (self.__vis is True): # pragma: no cover
            # prepare visualisation of graph
            self.__prepare_visualisation()

        # calculate hyperperiod of task set used in the cec
        self.__hyperperiod = self._calc_hyperperiod()
        
        ## __job_mtx: List of lists, each 'line' contains all jobs of the corresponding task from the chain, that could possibly be reached, compare set of jobs S []
        self.__job_mtx = list()
        
        # instantiate jobs and store them in job matrix
        self._init_relevant_jobs()
        
        # perform reachability analysis
        self._determine_dataPaths()

        # add edge weights to graph used for latency analysis
        self._add_weights()
        

    def _calc_hyperperiod(self):
        """ This function calculates the hyper period of the chain tasks.
        """
        periods = []
        i = 0
        while i < len(self.__tasks):
            periods.append(self.__tasks[i].in_event_model.P)
            i += 1
        # calculate hyper period
        hyperperiod = periods[0]
        for k in periods:
            hyperperiod = self.__lcm(k, hyperperiod)
        return hyperperiod


    def _init_relevant_jobs(self):
        """ create the set of jobs that may be reachable """

        l = 0
        for task in self.__cec.tasks:
            self.__set_jobs(task, l)
            l += 1

    
    def __set_jobs(self, task, l):
        """ This function instantiates the set of jobs needed for the reachability analysis
        and creates a node in the graph for each instantiated job

        :param self: the object pointer
        :param task TORO: extTask object
        :param l: integer corresponding to job index
        """
        mtx_line = list()
        job_number = 1

        if (task.name == self.__first_task_name):
            # root node: instantiate all jobs of the task that lie in the hyperperiod: HP / task period = highest task index
            for k in range(int(self.__hyperperiod / task.in_event_model.P)):
                job = task.instantiate_job(job_number=job_number, 
                                            wcrt=task.wcrt,
                                            bcrt=task.bcrt)
                mtx_line.append(job)
                job_number += 1

                # create graph node
                self.__data_prop_graph.add_node(job)               

                # add additional information for graph visualisation if flag is set to True
                if (self.__vis is True): # pragma: no cover
                    self.__data_prop_graph.set_node_position(job)
   
            # add line of jobs to matrix                
            self.__job_mtx.append(mtx_line)
        else:
            # not a root node: instantiate successor(consumer) jobs whose Rmin is smaller or equal to Dmax of the previous task's (producer) last job
            border = self.__job_mtx[l-1][-1].Dmax
            while True:
                job = task.instantiate_job(job_number=job_number,
                                            wcrt=task.wcrt,
                                            bcrt=task.bcrt)

                if (job.Rmin < border):
                    mtx_line.append(job)
                    job_number += 1

                    # create graph node
                    self.__data_prop_graph.add_node(job)
                    
                    # add additional information for graph visualisation if flag is set to True
                    if (self.__vis is True): # pragma: no cover
                        self.__data_prop_graph.set_node_position(job)

                else:
                    # add line of jobs to matrix 
                    self.__job_mtx.append(mtx_line)
                    break

            


    def _determine_dataPaths(self):
        """ determines data paths between previously instantiated job instances 
        based on their read and data intervals and connects the nodes in the graph accordingly
        """
        for i in range(len(self.__job_mtx) - 1):  # iterate over rows in matrix
            for k in range(len(self.__job_mtx[i])):  # iterate over columns in row
                # earliest possible self.__job_mtx[i+1][l] that may read from self.__job_mtx[i][k]
                # see Eq. (2) of Becker et al. 2016 [1] (adapted for offsets)
                # note that job index is by 1 smaller than the job number
                l = math.ceil((self.__job_mtx[i][k].Dmin - self.__job_mtx[i+1][0].offset) / self.__job_mtx[i + 1][0].period) - 1
                while (l < len(self.__job_mtx[i + 1])):
                    if (self.__follows(self.__job_mtx[i][k], self.__job_mtx[i + 1][l])):
                        producer = self.__job_mtx[i][k]
                        consumer =  self.__job_mtx[i + 1][l]                   

                        # add directed edge to graph signaling, that the consumer can read data from the producer
                        if (self.__data_prop_graph.get_in_degree(producer) == 0) and (producer.task_name != self.__first_task_name):
                            # do not add edges between node's, if the producer did not receive any data, because it's read interval did
                            # not match with any previous task's data intervals, happens especially for the first couple of tasks.
                            pass
                        else:
                            self.__data_prop_graph.add_edge(producer, consumer)
                    l += 1


    def _add_weights(self):
        """ This functions adds weights to each edge of the graph:
        The weight is equivalent to the change in response time/LET compared
        to the job predecessor.
        cf. [4] Equation (4.3) and (4.4)
        """
        
        edges = self.__data_prop_graph.get_edges()

        for e in edges:
            producer = e[0]
            consumer = e[1]

            if ((self.__data_prop_graph.get_out_degree(consumer) == 0) and (consumer.task_name != self.__last_task_name)):
                # if an edge will definitely not lead to a job instance of the last task in the chain, set edge weight to -infinity to avoid problems with longest/shortest path search
                weight = -math.inf

            elif (self.__data_prop_graph.get_in_degree(producer) == 0):
                # producer is an instance of the first task in the cec
                # [4] Equation (4.3) and (4.4) option: i = 0
                if(consumer.semantic == Semantics.LET):
                    tmp = consumer.let
                elif(consumer.semantic == Semantics.BET):
                    tmp = consumer.wcrt
                    
                # weight defined by the difference between the elapse of the consecutive job's WCRT or LET to the first job's activation instant (here defined by Rmin)
                weight = (consumer.Rmin + tmp) - (producer.Rmin)
            else:
                # producer is NOT an instance of the first task in the cec
                # [4] Equation (4.3) and (4.4) option: i > 0
                # modified to check producer and consumer separately to allow for analyzing 'heterogeneous' BET and LET CECs without prior decomposition
                if(consumer.semantic == Semantics.LET):                    
                    tmp_consumer = consumer.let                    
                elif(consumer.semantic == Semantics.BET):

                    tmp_consumer = consumer.wcrt
                if(producer.semantic == Semantics.LET): 
                    tmp_producer = producer.let
                elif(producer.semantic == Semantics.BET):
                    tmp_producer = producer.wcrt

                # weight defined as change (increase OR decrease) in max latency compared to latency from root to producer
                weight = (consumer.Rmin + tmp_consumer) - (producer.Rmin + tmp_producer)
            # add weight to corresponding edge (also as a value with inverted sign!)
            self.__data_prop_graph.set_edge_weight(producer, consumer, weight)


    def __follows(self, prod_job, cons_job):
        """ Check reachability between jobs using Eq. 1 of Becker et al. 2016 [1].

        :param prod_job: TORO Job object
        :param cons_job: TORO Job object
        :rtype: bool 
        """
        if ((cons_job.Rmax >= prod_job.Dmin) and (cons_job.Rmin < prod_job.Dmax)):
            return True
        else:
            return False










    ##################
    # chain analysis #
    ##################

    def calculate_e2e_lat(self, print_all=False) -> int:
        """ This functions calculcates the cause-effect-chain's maximum end-to-end latency
        by finding the longest path in the data propagation graph. A Bellman-Ford algorithm is
        exploited for this purpose, specifically using the inverted weights to find the longest
        path in the data propagation graph (cf. [4] Equation (4.6)).  

        :param print_all: bool
        :rtype: int
        """

        if (self.__data_prop_graph is None):
            raise GraphNotBuiltException('Data propagation graph has not been build yet! Call build_graph() before calling calculate_e2e_lat().')
        
        root_nodes = [x for x in self.__data_prop_graph.get_nodes() if self.__data_prop_graph.get_in_degree(x)==0 and x.task_name == self.__first_task_name]
        leaf_nodes = [x for x in self.__data_prop_graph.get_nodes() if self.__data_prop_graph.get_out_degree(x)==0 and x.task_name == self.__last_task_name]

        length = self.__data_prop_graph.get_longest_path_length(root_nodes=root_nodes, leaf_nodes=leaf_nodes)
        
        if (print_all is True): # pragma: no cover
            # print list of all data path of the cec and the corresponding latency
            # by finding all possible paths from all root and leaf nodes of the data propagation graph
            startNodes = [x for x in self.__data_prop_graph.get_nodes() if self.__data_prop_graph.get_out_degree(x)!=0 and self.__data_prop_graph.get_in_degree(x)==0 and x.task_name == self.__first_task_name]
            endNodes = [x for x in self.__data_prop_graph.get_nodes() if self.__data_prop_graph.get_out_degree(x)==0 and self.__data_prop_graph.get_in_degree(x)!=0 and x.task_name == self.__last_task_name]
 
            for start in startNodes:
                for end in endNodes:
                    # get all path
                    paths = self.__data_prop_graph.get_all_paths(start, end)

                    for path in paths:
                        
                        s = ""
                        for job in path[0]:
                            if s != "":
                                s += " -> "
                            s += job.name
                        print(s + "  | latency: " + str(path[1]))

        # store latency in instance
        self.__max_e2e_lat = length

        if self.__cec.e2e_deadline is not None:
            assert self.__max_e2e_lat <= self.__cec.e2e_deadline, "The end-to-end deadline of CEC " + self.__cec.name + " has been violated (latency : " + str(self.__max_e2e_lat) + ", deadline: " + str(self.__cec.e2e_deadline) + ")"

        return length
    

    def calculate_robustness_margins(self) -> Tuple[Dict, Dict]:
        """ This function calculates robustness margins of all tasks of the chain
        by comparing every job's data intervals with its own deadline, each successor's
        read interval or the maximum e2e latency defined for the cec. Also transition deadlines
        imposed on decomposed subchains are taken into acoount.
        Foundations are theorems 4, 5 and 6 from [3]. 
        Equations (2.13), (3.10) and (3.3) from [4] are used (equations adopted from [3]).
        The latter two are also extended taken arbitrary (non-implicit) deadlines into account as well.

        :rtype: dict, dict
        """
        if (self.__data_prop_graph is None):
            raise GraphNotBuiltException('Data propagation graph has not been build yet! Call build_graph() before calling calculate_e2e_lat().')

        # dictionaries to store results in
        tasks_rm = dict()
        tasks_delta_let = dict()

        # initialize dictionaries
        for task in self.__tasks:
            tasks_rm[task.name] = list()
            tasks_delta_let[task.name] = list()

        # calculate robustness margin for each job
        jobs = list(self.__data_prop_graph.get_nodes())
        
        for job in jobs:
            task_name = job.task_name

            # skip nodes, that have no predecessor and are no instance of the first task in the cec
            if(job.task_name != self.__first_task_name and self.__data_prop_graph.get_in_degree(job) == 0 ):
                continue



            # FIRST OPTION: compare let/wcrt against a task's own deadline - can be done for every task/job! 
            if(job.semantic == Semantics.BET):
                # if a deadline for a task exist use that deadline instead of the period
                if job.deadline is not None:
                    tasks_rm[task_name].append(job.deadline - job.offset - job.wcrt)
                else:
                    # d_tau_k^c - WCRT(tau_k^c), adjusted by offset
                    tasks_rm[task_name].append(job.period - job.offset - job.wcrt)

            elif(job.semantic == Semantics.LET):
                if not(job.wcrt is None or job.wcrt == 'unknown' or job.wcrt == 'n/a'):
                    # robustness of let task: let - wcrt
                    # [4] Equation (2.13) as adopted from [3] theorem 5
                    tasks_rm[task_name].append(job.let - job.wcrt)

                if (job.ic_task is False):
                    # following formula is not valid of (SL) LET interconnect tasks 
                    # as the LET may significantly exceeds a task's period
                    tasks_delta_let[task_name].append(job.period - job.offset - job.let)
                tasks_delta_let[task_name].append(job.period)



            # SECOND OPTION: job is not an instance of last task
            # Slack Theta: Calculate margin in a way, that there will be no new instance of a
            # consumer task that can read data from the job.
            # cf. [4] Equation (2.10) that is taken over from [3] theorem 4 
            if (job.task_name != self.__last_task_name):
                consumers = self.__data_prop_graph.get_successors(job)

                # get highest job_number of every task reading data from the job
                highest_index = 0
                for consumer in consumers:
                    if consumer.job_number > highest_index:
                        highest_index = consumer.job_number
                        task_name_suc = consumer.task_name

                # get first consumer job, that could not read data from the current job before and shall not be able to do so after adding the margin
                if (highest_index == 0):
                    # job has no consumers atm
                    # get next task (consumer) from chain and generate the first instance, that might be able to read data from the current job
                    # if the job's wcrt (and by doing so the upper bound of the data inter) is increased 
                    i = 0
                    for task in self.__cec.tasks:
                        i += 1
                        if (task.name == job.task_name):
                            break
                    
                    unreachable_job = self.__get_job2(job, self.__cec.tasks[i])
                else:
                    unreachable_job = self.__get_job(task_name_suc, highest_index + 1)

                # calculate max. slack theta and add to list of the corresponding task's robustness margins / delta let values
                theta = unreachable_job.Rmin - job.Dmax
                assert theta >= 0, ('per definition theta must not be < 0, but here theta = %d' %theta)
                job.set_slack(theta)
                if(job.semantic == Semantics.BET):
                    tasks_rm[task_name].append(theta)
                    
                elif(job.semantic == Semantics.LET):
                    tasks_delta_let[task_name].append(theta)




            # THIRD OPTION: job is an instance of last task
            # compare task wcrt or LET to chain deadlines
            else:
                # calculate maximum slack q, based on the e2e deadline of the cec and the previously calculated max. latency
                if (self.__max_e2e_lat is None): # pragma: no cover
                    print("The max. e2e latency of the chain has not been calculated before.\
                        \nUse calculate_e2e_lat() to calculate that value for more precise results.")
                    continue

                if (self.__max_e2e_lat is not None) and (self.__cec.e2e_deadline is not None):
                    if(job.semantic == Semantics.BET):
                        tasks_rm[task_name].append(self.__cec.e2e_deadline - self.__max_e2e_lat)
                    elif(job.semantic == Semantics.LET):
                        tasks_delta_let[task_name].append(self.__cec.e2e_deadline - self.__max_e2e_lat)
                
                # take transition deadlines into account as well:
                if(job.semantic == Semantics.BET):
                    # NOTE: adopted from updated "old" TORO implementation
                    if self.__cec.transition_deadline != None and self.__cec.transition_deadline != 0:
                        tasks_rm[task_name].append(self.__cec.transition_deadline - job.period - job.wcrt + job.bcrt)




        # the max. robustness margin of a task equals the min. value out of every value calculate above for all instances of the task
        for task_name, rm_list in tasks_rm.items():
            if (len(rm_list) != 0):
                # remove negative values from list
                rm_list = [x for x in rm_list if x >= 0]

                # prevent failures if no none-negative values exits for a given task
                if len(rm_list) == 0:
                    rm_list.append(0)

                # robustness margin equals smallest value remaining in list
                rm_min = min(rm_list)
                tasks_rm[task_name] = rm_min
    
        # the max. delta let value of a task equals the min. value out of every value calculate above for all instances of the task
        for task_name, d_let_list in tasks_delta_let.items():
            if (len(d_let_list) != 0):
                # remove negative values from list
                d_let_list = [x for x in d_let_list if x >= 0]

                # prevent failures if no none-negative values exits for a given task
                if len(d_let_list) == 0:
                    d_let_list.append(0)

                # robustness margin equals smallest value remaining in list
                delta_let = min(d_let_list)
                tasks_delta_let[task_name] = delta_let


        return tasks_rm, tasks_delta_let


    ###################################
    # chain analysis helper functions #
    ###################################

    def __get_job(self, task_name, job_number):
        """ return the job matching both the task name and the job number 
        
        :param task_name: string
        :param job_number: int
        :rtype: TORO job object
        """

        jobs = list(self.__data_prop_graph.get_nodes())

        ret = None
        # first check whether job already exists
        for job in jobs:
            if (job.task_name == task_name and job.job_number == job_number):
                ret = job
            
        # job not found in graph, instantiate new job
        if (ret is None):
            # find corresponding task in chain
            for task in self.__cec.tasks:
                if (task.name == task_name):
                    break
            # instantiante a new job of the corresponding task
            job = task.instantiate_job(job_number=job_number, 
                                        wcrt=task.wcrt, 
                                        bcrt=task.bcrt)
            ret = job

        return ret


    def __get_job2(self, producer_job, consumer_task):
        """ calculate index of first possible successor and return a corresponding job 
        
        :param producer_job: TORO Job object
        :param consumer_task: TORO extTask object
        :rtype: TORO job object
        """

        # earliest possible self.__job_mtx[i+1][l] that may read from self.__job_mtx[i][k]
        # see Eq. 2 of Becker et al. 2016 [1] (adapted for offsets)
        l = math.ceil((producer_job.Dmin - consumer_task.release_offset)/consumer_task.in_event_model.P)
        while True:           
            job = self.__get_job(consumer_task.name, l)

            if (job.Rmin > producer_job.Dmax):
                return job
            else:
                l += 1

        

         










    ################
    ## plot graph ##
    ################

    def __prepare_visualisation(self): # pragma: no cover
        """ prep graph for later visualisation by setting node positions and adding labels
        
        :rtype: None
        """
        ## dictionary for storing the y-axis shift for each task
        job_hierarchy = dict()
        i = 1
        for task in self.__cec.tasks:
            job_hierarchy[task.name] = i
            i += 1

        self.__data_prop_graph.prepare_visualisation(job_hierarchy)


    def plot(self, *args) -> None: # pragma: no cover
        """ This function draws the graph

        :param *args: strings
        :rtype: None
        """
        if (self.__data_prop_graph is None):
            raise GraphNotBuiltException('Data propagation graph has not been build yet! Call build_graph() before calling calculate_e2e_lat().')

        if (self.__vis is True):
            if ('drawIntervals' in args):
                self.__data_prop_graph.draw_intervals()

            self.__data_prop_graph.draw_reachability_graph(hyperperiod=self.__hyperperiod)
 
            self.__data_prop_graph.plot()
        else:
            print("Could not draw graph. Class initialisation has to be done with vis=True.")




    ##############################################
    ## verify correctness of robustness margins ##
    ##############################################

    def test(self, robustness_margins, delta_let=None):
        """ Verify whether perviously calculated robustness margins actually do not 
        lead to cec deadline misses, by updating task wcrts and lets. Builds a new
        graph and redetermines the max e2e latency of the cec using the updated tasks.
        Returns True if deadline constraint is not violated, else returns False.

        :param robustness_margins: dict
        :param delta_let: dict
        :rtype: bool
        """
        assert bool(robustness_margins) is True or bool(delta_let) is True

        # first update WCRT and LET values of tasks part of this chain
        for task in self.__cec.tasks:
            # update wcrt using the previously calculated robustness margins (for both LET and BET tasks)
            if task.name in robustness_margins.keys():
                task.wcrt += robustness_margins[task.name]

            # update LET of LET tasks using the delta let values
            if task.semantic is Semantics.LET:
                if task.name in delta_let.keys():
                    task.let += delta_let[task.name]


        # build new data propagation graph using the updated WCRT and LET values
        self.build_graph()
        # calculate chain latency using the updated WCRTs and LETs
        lat = self.calculate_e2e_lat()


        # undo updated wcrts and lets. Necessary as others chains use the same task objects
        # -> else leads to updating WCRTs/LETs multiple times if a task is part of more than one cec
        for task in self.__cec.tasks:
            if task.name in robustness_margins.keys():
                task.wcrt -= robustness_margins[task.name]
            if task.semantic is Semantics.LET:
                if task.name in delta_let.keys():
                    task.let -= delta_let[task.name]

        if self.__max_e2e_lat <= self.__cec.e2e_deadline:
            return True, lat
        else:
            return False, lat






    ###########################
    ## misc helper functions ##
    ###########################

    def __gcd(self, a, b):
        """ Helper function from pycpa.util, returns greatest common divisor using Euclid's Algorithm.

        :param a: int
        :param b: int
        :rtype: int
        """
        while b:
            a, b = b, a % b
        return a


    def __lcm(self, a, b): #from pycpa.util
        """ Helper function from pycpa.uti, returns lowest common multiple.
 
        :param a: int
        :param b: int
        :rtype: int
        """
        return a * b // self.__gcd(a, b)          