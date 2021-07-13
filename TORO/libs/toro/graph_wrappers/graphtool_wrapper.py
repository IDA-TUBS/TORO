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
The graph wrapper for the networkx library
"""

from .graph_wrapper import GraphWrapper as wrapper

from graph_tool.all import *

from typing import Dict, List, Union, Tuple
from .. import model


class Graph(wrapper):
    """ This class implements the wrapper for the graph-tool library """

    def __init__(self):
        """ constructor """

        ## actual directed graph-tool (gt) graph
        self.__graph = graph_tool.Graph(directed=True)

        ## dictionary for mapping TORO jobs to gt vertices
        self.__node_to_vertex = dict()
        ## dictionary for mapping an connection between two TORO jobs to gt edges
        self.__nodes_to_edge = dict()
        ## dictionary only used for base class compliant return values of get_edges()
        self.__edges = dict()

        ## property map: TORO Job to gt vertex
        self.__vertex_objects = self.__graph.new_vertex_property("object")
        ## property map: edge weights
        self.__edge_weights = self.__graph.new_edge_property("float")
        ## property map: edge weights (multiplied by (-1))
        self.__edge_weights_neg = self.__graph.new_edge_property("float")
    
    #################
    ## build graph ##
    #################

    def add_node(self, node:model.Job) -> None:
        """ add a job to the graph
        
        :param node: TORO Job object
        """

        vertex = self.__graph.add_vertex()
        self.__vertex_objects[vertex] = node

        self.__node_to_vertex[node] = vertex 

    
    def add_edge(self, node1:model.Job, node2:model.Job):
        """ connects two nodes of the graph using a directed edge 
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        """

        edge = self.__graph.add_edge(self.__node_to_vertex[node1], self.__node_to_vertex[node2])
        self.__nodes_to_edge[str([node1, node2])] = edge
        self.__edges[str([node1, node2])] = [node1, node2]


    def set_edge_weight(self, node1:model.Job, node2:model.Job, weight:float, name:str='default'):
        """ annotates the edge between the two nodes with a weight (of an arbitrary name)
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        :param weight: int
        :param name: weight name
        """

        edge = self.__nodes_to_edge[str([node1, node2])]

        if(name == 'default'):
            self.__edge_weights[edge] = weight
            self.__edge_weights_neg[edge] = -weight
        else:
            print("set_edge_weight, name != default not implemented in graph-tool_wrapper.py")




    ##########################
    ## access graph objects ##
    ##########################


    def get_nodes(self) -> List[model.Job]:
        """ returns a list of all nodes (TORO jobs) that are currently being stored in the graph
        
        :rtype: list
        """
        return self.__node_to_vertex.keys()
    

    
    def get_edges(self) -> List[List[model.Job]]:
        """ returns a list of all edges of the graph.
        An edge itself is described as a list of two TORO jobs: [predecessor, successor]
        
        :rtype: list
        """
        return self.__edges.values()

    
    def get_predecessors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all predecessors (TORO jobs) of a given node
        
        :param node: TORO Job object
        :rtype: list
        """
        ret = list()

        predecessors = self.__node_to_vertex[node].in_neighbors()

        ret = [self.__vertex_objects[v] for v in predecessors]

        return ret

    
    def get_successors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all successors (TORO jobs) of a given node
        
        :param node: TORO Job object
        
        :rtype: list
        """
        ret = list()

        successors = self.__node_to_vertex[node].out_neighbors()

        ret = [self.__vertex_objects[v] for v in successors]
            
        return ret


    def get_in_degree(self, node:model.Job) -> int:
        """ returns the number of predecessors (args = 'in') of a given node (TORO job)
        
        :param node: TORO Job object
        :rtype: int
        """
        v = self.__node_to_vertex[node]

        return v.in_degree()


    def get_out_degree(self, node:model.Job) -> int:
        """ returns the number of successors (args = 'out) of a given node (TORO job)
        
        :param node: TORO Job object   
        :rtype: int
        """
        v = self.__node_to_vertex[node]

        return v.out_degree()
     




    ####################
    ## graph analysis ##
    ####################

    
    def get_longest_path_length(self, start:Union[None, model.Job] = None, end:Union[None, model.Job] = None,
                                root_nodes:Union[None, List[model.Job]] = None, leaf_nodes:Union[None, List[model.Job]] = None) -> int:
        """ Calculate the length of the longest path that connects two nodes (start and end)
        or just the longest path that can be found in the graph if start and end are None.
        graph-tool implementation

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """

        if ((root_nodes is not None) and (leaf_nodes is not None)):
            root_nodes_cnt = len(root_nodes)
            leaf_nodes_cnt = len(leaf_nodes)

            max_dist = list()

            # negative_weights=True triggers bellman_ford search
            dist_map = graph_tool.topology.shortest_distance(self.__graph, weights=self.__edge_weights_neg, negative_weights=True)
            i = 0
            for v in self.__graph.vertices():
                if i < root_nodes_cnt:
                    dist_to_leaves = dist_map[self.__graph.vertex(v)][len(dist_map[self.__graph.vertex(v)]) - leaf_nodes_cnt:]
                    # max_dist.append(min(dist_map[self.__graph.vertex(v)]))
                    max_dist.append(min(dist_to_leaves))
                    i += 1
            return -min(max_dist)
        elif ((start is not None) and (end is not None)):
            max_dist = list()

            # negative_weights=True triggers bellman_ford search
            dist_map = graph_tool.topology.shortest_distance(self.__graph, source=self.__node_to_vertex[start] , target=self.__node_to_vertex[end],
                                                                weights=self.__edge_weights_neg, negative_weights=True)
            for v in self.__graph.vertices():
                max_dist.append(min(dist_map[self.__graph.vertex(v)]))
            return -min(max_dist)
        

    
    def get_shortest_path_length(self, start:model.Job, end:model.Job) -> int:
        """ calculates the length of the shortest path that connects two nodes (start and end)

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """
        min_dist = list()

        # use bellman ford here as well, because there can be negative edge weights (triggered by negative_weights=True)
        dist_map = graph_tool.topology.shortest_distance(self.__graph, source=self.__node_to_vertex[start] , target=self.__node_to_vertex[end],
                                                            weights=self.__edge_weights_neg, negative_weights=True)
        for v in self.__graph.vertices():
            min_dist.append(min(dist_map[self.__graph.vertex(v)]))
        return min(min_dist)
        

    
    def get_all_paths(self, start:model.Job, end:model.Job) -> List[Tuple[Tuple[model.Job, model.Job], int]]:
        """ returns a list of all paths that connect start and end as well as the corresponding path length
        A path is a list of edges: edge = [predecnessor, successor]

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: list of paths and lengths
        """
        
        p_list = list()

        paths = graph_tool.topology.all_paths(self.__graph, self.__node_to_vertex[start], self.__node_to_vertex[end], edges=True)

        i = 0
        for path in paths:
            p = list()
            length = 0
            for edge in path:
                length += self.__edge_weights[edge]
                p.append(self.__vertex_objects[edge.source()])                
            p.append(self.__vertex_objects[edge.target()])
            p_list.append((p, length))
        
        return p_list
        

    
    ###########################
    ## plot helper functions ##
    ###########################

    
    def prepare_visualisation(self, hierarchy): # pragma: no cover
        """ """
        raise NotImplementedError("The graph-tool implementation does not support plooting the reachability graph yet!")

    
    def set_node_position(self, node): # pragma: no cover
        """ place a node in a coordinate system and assign a label

        :param node: TORO Job object
        """
        raise NotImplementedError("The graph-tool implementation does not support plooting the reachability graph yet!")

    
    def draw_reachability_graph(self, **kwargs): # pragma: no cover
        """ draw the reachability graph generated for a given cause-effect-chain """
        raise NotImplementedError("The graph-tool implementation does not support plooting the reachability graph yet!")

    
    def draw_intervals(self): # pragma: no cover
        """ draw read and data intervals """
        raise NotImplementedError("The graph-tool implementation does not support plooting the reachability graph yet!")

    
    def plot(self): # pragma: no cover
        """ plot reachability graph """
        raise NotImplementedError("The graph-tool implementation does not support plooting the reachability graph yet!")