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
This class is to be used as an interface for all cause-effect chain analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Union, Tuple

from .. import model

class ChainBaseClass(ABC): # pragma: no cover
    """ This abstract base class is used as an interface all
    e2e latency and robustness analyses have to implement. 
    """
    
    def __init__(self, chain:model.extEffectChain, vis:bool = False): 
        """ constructor
        Implementing the parameters defined here is necessary, extending the parameter list is possible.

        :param chain: TORO ExtEffectChain
        :param task_res: dictionary containing the wcrt of all tasks found in chain
        :param vis: bool, enable/disable graph visualisation
        """

    @abstractmethod
    def build_graph(self) -> None:
        """ builds a reachability graph """
        pass

    @abstractmethod
    def calculate_e2e_lat(self) -> int:
        """ This functions calculcates the cause-effect-chain's maximum end-to-end latency
        by finding the longest path in the data propagation graph. The length of the longest
        path is returned by the function
        
        :rtype: int
        """
        pass

    @abstractmethod
    def calculate_robustness_margins(self) -> Tuple[Dict, Dict]:
        """ This function calculates robustness margins of all tasks of the chain
        by comparing every job's data intervals with its own deadline, each successor's
        read interval or the maximum e2e latency defined for the cec. The results for both
        robustness margins and delta LET values (if the chain consist of LET tasks) are
        returned as dictionaries {'T1': RM_min(T1); 'T2': RM_min(T2)}. For non-LET chains
        the second dictionary remains empty!
        
        :rtype: dict, dict"""
        pass

    @abstractmethod
    def plot(self, *args) -> None:
        """ This function plots the reachability graph. """
        pass


class GraphNotBuiltException(Exception):
    """ Exception to signal, if the graph required for the actual analyses
    has not been generated yet """
    pass