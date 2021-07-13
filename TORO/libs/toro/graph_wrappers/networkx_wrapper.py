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
The graph wrapper for the NetworkX library
"""

from .graph_wrapper import GraphWrapper as wrapper

import networkx as nx

import matplotlib.pyplot as plt
#from networkx.drawing.nx_agraph import graphviz_layout


from typing import Dict, List, Union, Tuple
from .. import model
Semantics = model.Semantic


class Graph(wrapper):
    """ This class implements the wrapper for the networkx library """

    def __init__(self) -> None:
        """ constructor """

        ## actual networkx graph
        self.__graph = nx.DiGraph()

               


    
    #################
    ## build graph ##
    #################

    def add_node(self, node:model.Job) -> None:
        """ add a job to the graph
        
        :param node: TORO Job object
        """
        self.__graph.add_node(node)

    
    def add_edge(self, node1:model.Job, node2:model.Job) -> None:
        """ connects two nodes of the graph using a directed edge 
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        """
        assert self.__graph.has_node(node1) and self.__graph.has_node(node2)

        self.__graph.add_edge(node1, node2)


    def set_edge_weight(self, node1:model.Job, node2:model.Job, weight:float, name:str='default') -> None:
        """ annotates the edge between the two nodes with a weight (of an arbitrary name)
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        :param weight: int
        :param name: weight name
        """
        assert self.__graph.has_node(node1) and self.__graph.has_node(node2)

        if (name == 'default'):
            self.__graph[node1][node2]['weight'] = weight
            self.__graph[node1][node2]['negativeWeight'] = -weight
        else:
            self.__graph[node1][node2][name] = weight




    ##########################
    ## access graph objects ##
    ##########################


    def get_nodes(self) -> List[model.Job]:
        """ returns a list of all nodes (TORO jobs) that are currently being stored in the graph
        
        :rtype: list
        """
        return self.__graph.nodes()

    
    def get_edges(self) -> List[List[model.Job]]:
        """ returns a list of all edges of the graph.
        An edge itself is described as a list of two TORO jobs: [predecessor, successor]
        
        :rtype: list
        """
        return self.__graph.edges()

    
    def get_predecessors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all predecessors (TORO jobs) of a given node
        
        :param node: TORO Job object
        :rtype: list
        """
        assert self.__graph.has_node(node)

        return self.__graph.predecessors(node)

    
    def get_successors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all successors (TORO jobs) of a given node
        
        :param node: TORO Job object
        
        :rtype: list
        """
        assert self.__graph.has_node(node)

        return self.__graph.successors(node)

     
    def get_in_degree(self, node:model.Job) -> int:
        """ returns the number of predecessors (args = 'in') of a given node (TORO job)
        
        :param node: TORO Job object
        :rtype: int
        """
        assert self.__graph.has_node(node)

        return self.__graph.in_degree(node)


    def get_out_degree(self, node:model.Job) -> int:
        """ returns the number of successors (args = 'out) of a given node (TORO job)
        
        :param node: TORO Job object   
        :rtype: int
        """
        assert self.__graph.has_node(node)
        
        return self.__graph.out_degree(node)




    ####################
    ## graph analysis ##
    ####################

    
    def get_longest_path_length(self, start:Union[None, model.Job]=None, end:Union[None, model.Job]=None,
                                root_nodes:Union[None, List[model.Job]]=None, leaf_nodes:Union[None, List[model.Job]]=None) -> int:
        """ Calculates the length of the longest path that connects two nodes (start and end)
        or just the longest path that can be found in the graph if start and end are None.
        NetworkX implementation.

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """

        if not ((start is not None) and (end is not None)):
            roots = [x for x in root_nodes if self.get_out_degree(x) != 0]
            leaves = [x for x in leaf_nodes if self.get_in_degree(x) != 0]
            
            distances = list()
            ## option 1:
            # for root in roots:
            #     for leaf in leaves:
            #         try:
            #             dist = -(nx.bellman_ford_path_length(self.__graph, root, leaf, weight='negativeWeight'))
            #             distances.append(dist)
            #         except:
            #             pass

            # for leaf in leaves:
            #     ancestors = nx.ancestors(self.__graph, leaf)
            #     ancestors = [x for x in ancestors if x in roots]
            #     for root in ancestors:                
            #         dist = -(nx.bellman_ford_path_length(self.__graph, root, leaf, weight='negativeWeight'))
            #         distances.append(dist)

            ## option 2:
            # distance_map = nx.all_pairs_bellman_ford_path_length(self.__graph, weight='negativeWeight')
            # for map in distance_map:
            #     if map[0] in roots:
            #         for key, value in map[1].items():
            #             if key in leaves:
            #                 distances.append(-value)

            ## option 3
            for job in roots:
                pred, dist = nx.bellman_ford_predecessor_and_distance(self.__graph, job, weight='negativeWeight')
                for key, value in dist.items():
                    if key in leaves:
                        distances.append(-value)

            return max(distances)
        else:
            assert self.__graph.has_node(start) and self.__graph.has_node(end)

            return -(nx.bellman_ford_path_length(self.__graph, start, end, weight='negativeWeight'))
        

    
    def get_shortest_path_length(self, start:model.Job, end:model.Job) -> int:
        """ calculates the length of the shortest path that connects two nodes (start and end)

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """
        assert self.__graph.has_node(start) and self.__graph.has_node(end)

        # use bellman ford here as well, because there can be negative edge weights
        return nx.bellman_ford_path_length(self.__graph, start, end, weight='weight')
        

    
    def get_all_paths(self, start:model.Job, end:model.Job) -> List[Tuple[Tuple[model.Job, model.Job], int]]:
        """ returns a list of all paths that connect start and end as well as the corresponding path length
        A path is a list of edges: edge = [predecnessor, successor]

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: list of paths and lengths
        """
        assert self.__graph.has_node(start) and self.__graph.has_node(end)

        paths = (nx.all_simple_paths(self.__graph, start, end))

        p_list = list()
        for path in paths:
            p = list()
            length = 0
            prev = None
            for job in path:
                p.append(job)

                if prev is not None:
                    length += self.__graph[prev][job]['weight']
                prev = job

            p_list.append((p, length))
        
        return p_list
        


    
    ###########################
    ## plot helper functions ##
    ###########################

    def prepare_visualisation(self, hierarchy): # pragma: no cover
        """ """
        ## dictionary for storing node labels that should be used when plotting the graph
        self.__nx_labels = dict()
        ## dictionary for storing a node's position
        self.__job_position = dict()
        ## dictionary: store order of tasks in the caue-effect-chain
        self.__node_hierarchy = hierarchy
        ## offset for y-spacing of nodes when drawing reachability graph
        self.__hierarchy_offset = 15 # TODO calculate based on the actual graph

        i = 0
        for task_name in self.__node_hierarchy.keys():
            if (i == 0):
                self.__first_task_name = task_name
                i = 1
            else:
                self.__last_task_name = task_name       


    def set_node_position(self, node): # pragma: no cover
        """ place a node in a coordinate system and assign a label

        :param node: TORO Job object
        """

        #self.__nx_labels[node] = node.task_name + "_" + str(node.job_number)
        self.__nx_labels[node] = str(node.job_number)
        self.__job_position[node] = ((node.job_number - 1) * node.period + node.offset, self.__node_hierarchy[node.task_name]*self.__hierarchy_offset)


    def draw_reachability_graph(self, **kwargs): # pragma: no cover
        """ draw the reachability graph generated for a given cause-effect-chain """

        # plt.title('chain: ' + self.__cec.name)

        # draw nodes and labels
        nx.set_node_attributes(self.__graph, self.__job_position, 'coord')
        nx.draw_networkx_nodes(self.__graph, self.__job_position, node_size = 300, node_color="white", edgecolors='black')
        nx.draw_networkx_labels(self.__graph, self.__job_position, self.__nx_labels, font_size=12)

        # draw edges with weights
        edge_labels = nx.get_edge_attributes(self.__graph,'weight')
        nx.draw_networkx_edges(self.__graph, self.__job_position)
        nx.draw_networkx_edge_labels(self.__graph, self.__job_position, edge_labels=edge_labels)

        # configure axis
        ax = plt.subplot()
        ax.tick_params(left=False, bottom=True, labelleft=False, labelbottom=True)
        plt.xlim(left=-2)

        # Hide the right, left and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.grid(axis='x', linestyle=':')
        plt.xlabel("t")

        hp = kwargs.get('hyperperiod', None)
        if hp is not None:            
            # draw hyperperiod
            x, y = [hp, hp], [self.__node_hierarchy[self.__first_task_name]*self.__hierarchy_offset-2, self.__node_hierarchy[self.__last_task_name]*self.__hierarchy_offset+2]
            plt.plot(x, y, marker = '', color="black", linestyle='--')            
            ax.text(hp + 0.1, self.__node_hierarchy[self.__first_task_name]*self.__hierarchy_offset-1, 'HP', fontsize=12)

        # draw task names
        cnt = 0
        for task_name in self.__node_hierarchy.keys():
            ax.text(-10, self.__node_hierarchy[self.__first_task_name]*self.__hierarchy_offset - 1 + (cnt*self.__hierarchy_offset), task_name, fontsize=16)
            cnt += 1

    def draw_intervals(self): # pragma: no cover
        """ draw read and data intervals """
        jobs = list(self.__graph.nodes)
           
        for job in jobs:

            if (job.semantic is Semantics.BET):
                tmp = (job.job_number - 1) * job.period + job.offset + job.wcrt
            elif (job.semantic is Semantics.LET):
                tmp = (job.job_number - 1) * job.period + job.offset + job.let
            x, y = [(job.job_number - 1) * job.period + job.offset + 0.5, tmp], [self.__node_hierarchy[job.task_name]*self.__hierarchy_offset, self.__node_hierarchy[job.task_name]*self.__hierarchy_offset]
            # plt.plot(x, y, marker = '|', color="blue")

            if (job.job_number % 2 == 1):
                y_drawingOffset = 1
            else:
                y_drawingOffset = 2


            if (job.task_name != self.__first_task_name) and (self.get_in_degree(job) == 0):
                continue

            if (job.task_name != self.__first_task_name):
                x, y = [job.Rmin, job.Rmax], [self.__node_hierarchy[job.task_name]*self.__hierarchy_offset - 1 - 1, self.__node_hierarchy[job.task_name]*self.__hierarchy_offset - 1 - 1]
                plt.plot(x, y, marker = 'o', color="green")

            if (job.task_name != self.__last_task_name):
                x, y = [job.Dmin, job.Dmax], [self.__node_hierarchy[job.task_name]*self.__hierarchy_offset + 1 + y_drawingOffset, self.__node_hierarchy[job.task_name]*self.__hierarchy_offset + 1 + y_drawingOffset]
                plt.plot(x, y, marker = 'o', color="red")

    
    def plot(self): # pragma: no cover
        """ plot reachability graph """
        plt.show()
