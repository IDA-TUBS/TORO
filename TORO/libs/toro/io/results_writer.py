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
This module contains a writer class processing SystemAnalysisResults objects and
translating those results to strings or to csv files.
"""

# import os
# import sys
import csv

from .. import system_analysis





class ResultsWriter(object):
    """ class for writing results to csv-files """
    def __init__(self):
        """ constructor """
        pass

    def chain_results_to_csv(self, res, dir):
        """ write chain latency and deadline results to csv file

        :param res: system_analysis SystemAnalysisResults
        :param dir: string
        """

        with open(dir + '/chain_results.csv', 'w', newline='') as file:
            csv_writer = csv.writer(file, delimiter=';')
            csv_writer.writerow(['chain', 'latency', 'subchain', 'deadline', 'transition_latency', 'transition_deadline'])

            for chain, latency in res.chain_latencies.items():
                csv_writer.writerow([chain, latency])
                if hasattr(res, 'sub_deadlines'):
                    if chain in res.sub_deadlines.keys():
                        i=1
                        for entry in res.sub_deadlines[chain]:
                            csv_writer.writerow(['', '', i, entry[0], res.transition_latencies[chain][i-1], entry[1]])
                            i += 1

    
    def task_results_to_csv(self, res, dir):
        """ task bcrt and wcrt results to csv file

        :param res: system_analysis SystemAnalysisResults
        :param dir: string
        """

        with open(dir + '/task_results.csv', 'w', newline='') as file:
            csv_writer = csv.writer(file, delimiter=';')
            csv_writer.writerow(['task', 'bcrt', 'wcrt'])

            if hasattr(res, 'task_results'):
                for task, results in res.task_results.items():
                    csv_writer.writerow([task, results.wcrt, results.wcrt])


    def robustness_results_to_csv(self, res, dir):
        """ write robustness results to csv file

        :param res: system_analysis SystemAnalysisResults
        :param dir: string
        """

        with open(dir + '/robustness_results.csv', 'w', newline='') as file:
            csv_writer = csv.writer(file, delimiter=';')
            csv_writer.writerow(['task', 'rm', 'dLET'])

            keys = set(res.robustness_margins.keys()).union(res.delta_let.keys())
            for task in keys:
                csv_writer.writerow([task, (res.robustness_margins[task] if task in res.robustness_margins.keys() else None), (res.delta_let[task] if task in res.delta_let.keys() else None)])

    def slack_to_csv(self, res, dir):
        """ write slack results to csv file

        :param res: system_analysis SystemAnalysisResults
        :param dir: string
        """

        with open(dir + '/slack_results.csv', 'w', newline='') as file:
            csv_writer = csv.writer(file, delimiter=';')
            csv_writer.writerow(['task', 'slack'])

            for task in res.slack.keys():
                csv_writer.writerow([task, res.slack[task]])


    
    def results_to_string(self, res):
        """ combine all results in a single string

        :param res: system_analysis SystemAnalysisResults
        :rtype: string
        """

        s = ""
        s += "Analysis results for system: " + res.system_name
        s += "\nWorst case chain latencies:"
        for chain, latency in res.chain_latencies.items():
            s += "\n\t" + str(chain) + ": " + str(latency)
            if hasattr(res, 'sub_deadlines'):
                if chain in res.sub_deadlines.keys():
                    s += "\n\t\tdevided into " + str(len(res.sub_deadlines[chain])) + " subchains:"
                    i=1
                    for entry in res.sub_deadlines[chain]:
                        s+= "\n\t\t" + str(i) + ". deadline: " + str(entry[0]) + ", transition latency: " + str(res.transition_latencies[chain][i-1]) + ", transition deadline: " + str(entry[1])
                        i += 1
        s += "\nRobustness margins:"
        for task, rm in res.robustness_margins.items():
            s += "\n\t" + str(task) + ": " + str(rm)
        s += "\nDelta LET:"
        for task, rm in res.delta_let.items():
            s += "\n\t" + str(task) + ": " + str(rm)

        return s