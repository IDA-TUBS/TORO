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
This base class is used for all graph library wrappers in the context of cause-effect chain analysis
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Union, Tuple

from .. import model

class GraphWrapper(ABC): # pragma: no cover
    """ This abstract base class is used as an interface
    all graph library wrappers have to implement. 
    """
    def __init__(self) -> None:
        """ constructor """

        ## graph object
        self.__graph = None

        # call network lib's constructor in lib specific wrapper

    #################
    ## build graph ##
    #################
    
    @abstractmethod
    def add_node(self, node:model.Job) -> None:
        """ add a job to the graph
        
        :param node: TORO Job object
        """
        pass

    @abstractmethod
    def add_edge(self, node1:model.Job, node2:model.Job) -> None:
        """ connects two nodes of the graph using a directed edge 
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        """
        pass

    @abstractmethod
    def set_edge_weight(self, node1:model.Job, node2:model.Job, weight:float, name:str = 'default') -> None:
        """ annotates the edge between the two nodes with a weight (of an arbitrary name)
        
        :param node1: TORO Job object
        :param node1: TORO Job object
        :param weight: int
        :param name: weight name
        """
        pass


    ##########################
    ## access graph objects ##
    ##########################

    @abstractmethod
    def get_nodes(self) -> List[model.Job]:
        """ returns a list of all nodes (TORO jobs) that are currently being stored in the graph
        
        :rtype: list
        """
        pass

    @abstractmethod
    def get_edges(self) -> List[List[model.Job]]:
        """ returns a list of all edges of the graph.
        An edge itself is described as a list of two TORO jobs: [predecessor, successor]
        
        :rtype: list
        """
        pass

    @abstractmethod
    def get_predecessors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all predecessors (TORO jobs) of a given node
        
        :param node: TORO Job object
        :rtype: list
        """
        pass

    @abstractmethod
    def get_successors(self, node:model.Job) -> List[model.Job]:
        """ returns a list of all successors (TORO jobs) of a given node
        
        :param node: TORO Job object
        
        :rtype: list
        """
        pass

    @abstractmethod 
    def get_in_degree(self, node:model.Job) -> int:
        """ returns the number of predecessors of a given node (TORO job)
        
        :param node: TORO Job object        
        :rtype: int
        """
        pass

    abstractmethod 
    def get_out_degree(self, node:model.Job) -> int:
        """ returns the number of successors (args = 'out) of a given node (TORO job)
        
        :param node: TORO Job object        
        :rtype: int
        """
        pass




    ####################
    ## graph analysis ##
    ####################

    @abstractmethod
    def get_longest_path_length(self, start:Union[None, model.Job] = None, end:Union[None, model.Job] = None,
                                root_nodes:Union[None, List[model.Job]] = None, leaf_nodes:Union[None, List[model.Job]] = None) -> int:
        """ Calculates the length of the longest path that connects two nodes (start and end)
        or just the longest path that can be found in the graph if start and end are None.

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """
        pass

    @abstractmethod
    def get_shortest_path_length(self, start:model.Job, end:model.Job) -> int:
        """ calculates the length of the shortest path that connects two nodes (start and end)

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: int
        """
        pass

    @abstractmethod
    def get_all_paths(self, start:model.Job, end:model.Job) -> List[Tuple[Tuple[model.Job, model.Job], int]]:
        """ returns a list of all paths that connect start and end as well as the corresponding path length
        A path is a list of edges: edge = [predecnessor, successor]

        :param start: TORO Job object
        :param end: TORO Job object
        :rtype: list of paths and lengths
        """
        pass





    ###########################
    ## plot helper functions ##
    ###########################

    @abstractmethod
    def prepare_visualisation(self, hierarchy:dict) -> None:
        """ """
        pass

    @abstractmethod
    def set_node_position(self, node:model.Job) -> None:
        """ place a node in a coordinate system and assign a label

        :param node: TORO Job object
        """
        pass

    @abstractmethod
    def draw_reachability_graph(self, **kwargs) -> None:
        """ draw the reachability graph generated for a given cause-effect-chain """
        pass

    @abstractmethod
    def draw_intervals(self) -> None:
        """ draw read and data intervals """
        pass

    @abstractmethod
    def plot(self) -> None:
        """ plot reachability graph """
        pass