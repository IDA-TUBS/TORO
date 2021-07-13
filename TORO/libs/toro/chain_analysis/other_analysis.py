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

"""

from .analysis_LET_BET import ChainAnalysis


class ModifiedChainAnalysis(ChainAnalysis):
    def __init__(self, chain, task_res, vis=False, additionalChains=None, labels=None):
        """ constructor """
        super().__init__(chain, task_res, vis)

        # dict for storing the label each task in a chain is writing to.
        self.lables = labels

        if additionalChains is not None:
            for chain in additionalChains:
                self.__tasks.extend(chain.tasks)


    def build_graph(self):
        """
        """
        super().build_graph()
        self.__add_labels_to_edges()

    # def _calc_hyperperiod(self):
    #     """ This function calculates the hyper period of the chain tasks.
    #     """
    #     super().__calc_hyperperiod() # replace with new function to calculate hyperperiod

    
    def __add_labels_to_edges(self):
        """
        """
        pass

    def combine_graphs(self, graphs):
        """
        """
        pass

    def analyse(self):
        """
        """
        pass
        # use descendants?

    def get_graph(self):
        """
        """
        return self.__graph