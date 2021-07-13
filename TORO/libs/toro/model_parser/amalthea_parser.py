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
This module parses Amalthea models that describe a system.
"""

# import os
# import sys
from typing import Dict, List, Union, Tuple
from pycpa import model
from pycpa import schedulers
from pycpa import graph
from .. import model as toro_model

Semantics = toro_model.Semantic

import networkx as nx
import matplotlib.pyplot as plt

try:
    from Amalthea2PyCPA import Parser
except:
    print("------------------------------------------\
         \nWarning: Amalthea2PyCPA could not be found\
         \n------------------------------------------")


from .parser import ModelParser

## private Amalthea parser object
parser = None

## private copy of amalthea version number used by .amxmi file
amalthea_version = None

## private list of supported amalthea versions
supported_versions = ['0_9_5','0_9_6', '0_9_7', '0_9_8', '0_9_9']

## xsi scheme
xsi = '{http://www.w3.org/2001/XMLSchema-instance}'

## dict for mapping Amalthea units (time) to a common time base 
units = {"s":1, "ms":10**(-3), "us":10**(-6), "ns":10**(-9), "ps":10**(-12)}
## dict for mapping frequencies to a common base
freqUnits = {"Hz": 1.0, "MHz": 1000.0, "KHz": 1000000.0, "GHz": 1000000000.0}


class AmaltheaParser(ModelParser):
    """ """
    def __init__(self, args, file_name):
        """ load system model
        """
        global parser
        global amalthea_version

        parser = Parser.Parser(file_name)
        amalthea_version = parser.get_amaltheaVersion()

        assert amalthea_version in supported_versions, "The amalthea version used in the .amxmi file is not supported by this parser yet"

    
    def parse(self) -> Tuple[model.System, List[toro_model.extEffectChain]]:
        """ process the AMALTHEA model systematically translating the information
        into a pyCPA system and a list of extEffectChain objects.

        :rtype: pyCPA.model.System, list[extEffectChain]
        """
        self.__system = model.System()
        self.__chains = list()
        self.__pycpa_resources = dict()
        self.__frequencies = dict()
        self.__ipc = dict()
        self.__pycpa_tasks = dict()
        self.__pycpa_stimuli = dict()
        self.__writing_tasks = dict()
        self.__reading_tasks = dict()

        self._get_resources()
        assert len(self.__pycpa_resources) > 0, "[Amalthea Parser] No resources have been created."
        self._get_tasks()
        assert len(self.__pycpa_tasks) > 0, "[Amalthea Parser] No tasks have been created."
        self._get_chains()
        assert len(self. __chains) > 0, "[Amalthea Parser] No cause-effect chains have been created."

        g = graph.graph_system(self.__system, 'example_graph.pdf', dotout='example_graph.dot')

        return self.__system, self. __chains





    #######################
    ## tasks & runnables ##
    #######################

    def _get_tasks(self) -> None:
        """ retrieve all tasks stored in a given AMALTHEA model.
        Results are stored in dictionary self.__pycpa_tasks

        :rtype: None
        """
        # get all xml elements of type task, independent of the amalthea version used by the model
        if amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4', '0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
            path = ['Amalthea', 'swModel', 'tasks']
            filterArgs = None
        else:
            print("Class Task not part of Amalthea version %s" %amalthea_version)
            return None

        multipleElements = True
        xml_tasks = parser.getElement(path, multipleElements=multipleElements, filterArgs=filterArgs)

        print("\n[AmaltheaParser] get_tasks")

        for task in xml_tasks:
            name = parser.xml_get(task, 'name')

            # executing/transmitting computation/communication resource
            resource = self.__get_executing_resource(task)

            # task execution time
            bcet, wcet = self.__get_execution_time(task, resource)

            # parse label accesses
            read_labels, written_labels = self.__get_labels(task)

            # retrieve runnables of task, if some exist
            runnables = self.__get_runnables(task)
            if (runnables is not None) or (len(runnables) == 0):
                for runnable in runnables:
                    # add runnable execution time to task's bcer and wcet
                    bcet_run, wcet_run = self.__get_execution_time(runnable, resource, 'runnables')
                    assert bcet_run is not None and wcet_run is not None

                    if bcet is None:
                        bcet = 0
                    if wcet is None:
                        wcet = 0

                    bcet += bcet_run
                    wcet += wcet_run

            # TODO consider label accesses of runnables that are executed within the scope of a task as well 
            for label in written_labels:
                # assign the task that is writing to a label as the sole task to do so (publisher-subscriber communication)
                self.__writing_tasks[label] = task
            for label in read_labels:
                # keep track of which labels are read by which tasks
                if not(label in self.__reading_tasks.keys()):
                    self.__reading_tasks[label] = list()
                self.__reading_tasks[label].append(task)             
                

            # task deadlines
            deadline = self.__get_deadline(task)

            # task priority
            priority = self.__get_priority(task)
            # assert priority is not None, "priority of task " + name + " must not be undefined!"

            # task execution semantic
            semantic = self.__get_task_semantic(task)

            # specify let if neccessary
            let = None
            if (semantic == Semantics.LET) and (deadline is not None):
               let = deadline
            else:
                let = None

            # process Amalthea stimulus
            activation_pattern = self.__get_activation_pattern(task)

            # if deadline not defined, use period as implicit deadline, if task is periodically triggered
            if(activation_pattern[0] == 'pjd' and deadline is None):
                deadline = activation_pattern[1].P
            
            # create TORO task
            t = toro_model.extTask(name=name, release_offset=0,
                bcet=bcet, wcet=wcet,
                scheduling_parameter=priority,
                let=let,
                semantic=semantic,
                deadline=deadline)
            
            print("%s:\tbcet: %s, wcet: %s,\tsemantic: \'%s\', deadline: %s, \tpriority:%s \t- running on %s" %(name, str(bcet), str(wcet), str(semantic), str(deadline), str(priority), parser.xml_get(resource, 'name')))

            # set event model of task according to stimulus
            if activation_pattern is not None:
                if activation_pattern[0] == 'pjd':
                    # set release offset here. Only use TORO ExtTask offset instead of using pyCPA pjd model offset phi!
                    t.set_release_offset(activation_pattern[1].phi)
                    activation_pattern[1].phi = None
                    t.in_event_model = activation_pattern[1]
                    
                    print("\tperiod: %d, offset: %s" %(activation_pattern[1].P, str(t.release_offset)))
                else:
                    raise NotImplementedError("Mapping of stimulus pattern %s is not supported yet." % activation_pattern['type'])
            else:
                raise TypeError("Invalid activation pattern \'None\'. No stimulus found for task %s" % name)

            self.__pycpa_resources[resource].bind_task(t)
            self.__pycpa_tasks[task] = t



    # TODO check paths!
    def __get_runnables(self, task):
        """ retrieve all runnables executing in the context of a given task.

        :param task: xml entry
        :rtype: list of runnables (xml entries)
        """
        if amalthea_version in ['0_9_3', '0_9_4', '0_9_5', '0_9_6']:
            path = ['tasks', 'callGraph', 'graphEntries', 'calls']
            filterArgs = ['option', 'RunnableCall']
        elif amalthea_version in ['0_9_7', '0_9_8', '0_9_9']:
            path = [['tasks', 'activityGraph', 'items', 'items'], ['tasks', 'activityGraph', 'items']]
            filterArgs = ['option', 'RunnableCall']
        elif amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2']:
            print("Processing of Runnables currently not supported for Amalthea version %s" %amalthea_version)
            return None
        multipleElements = True    
    
        runnables = list() 

        runnableCalls = parser.getElement(path, root=task, multipleElements=multipleElements, filterArgs=filterArgs)
        if runnableCalls is not None:
            for call in runnableCalls:
                if amalthea_version in ['0_9_3', '0_9_4']:          
                    path = ['TaskRunnableCall', 'Runnable']
                elif amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                    path = ['RunnableCall', 'Runnable']
                else:
                    print("Processing of Runnables currently not supported for Amalthea version %s" %amalthea_version)
                    return None

                lst = parser.getAssocaitedElement(path=path, rootElem=call)                
                if lst is not None:
                    for runnable in lst:
                        # name = parser.xml_get(runnable, 'name')
                        runnables.append(runnable)

        return runnables




    def __get_execution_time(self, executableEntity, resource, elem='tasks'):
        """ Parsing the execution time of a given task or runnable. 
        Processes both ExecutionNeed and Tick metrics.

        :param executableEntity: xml entry of type Task or Runnable
        :param resource: xml entry of the processing unit executing a runnable or task
        :param elem: string
        :rtype: float, float
        """
        bcet, wcet = 0, 0

        freq = self.__frequencies[resource]
        # normally an association would be used to get from ExecutionNeed to HwFeature, but for some reason no association is used
        # in Amalthea here, just a key that cannot be processed by Amalthea2PyCPA
        ipc = self.__ipc[resource]

        needs_min, needs_max = self.__get_execution_needs(executableEntity, elem)        
        if (needs_min != 0 and needs_max != 0 and len(ipc) > 0):
            bcet += (needs_min/max(ipc) * (1/freq))
            wcet += (needs_max/min(ipc) * (1/freq))

        ticks_min, ticks_max = self.__get_ticks(executableEntity, elem)
        if (ticks_min is not None) and (ticks_max is not None):            
            bcet += (ticks_min/freq)
            wcet += (ticks_max/freq)

        if bcet != 0 and wcet != 0:
            return bcet, wcet
        else:
            return 0, None


    def __get_execution_needs(self, executableEntity, elem):
        """ parsing of ActivityGraph entry of type ExecutionNeed
        using param elem the function can be both used for "tasks" and "runnables"

        :param executableEntity: xml entry of type Task or Runnable
        :param elem: string
        :rtype: int, int
        """
        if amalthea_version in ['0_9_5', '0_9_6']:
            path = [elem, 'callGraph', 'items']
            filterArgs = ['option', 'ExecutionNeed']
        elif amalthea_version in ['0_9_7', '0_9_8', '0_9_9']:
            path = [elem, 'activityGraph', 'items']
            filterArgs = ['option', 'ExecutionNeed']
        elif amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4']:
            print("Class ExecutionNeed not part of Amalthea version %s" % amalthea_version)
            return 0, 0
            
        multipleElements = True
        exec_needs_xml = parser.getElement(path, root=executableEntity, multipleElements=multipleElements, filterArgs=filterArgs)
        if exec_needs_xml is not None:
            min, max = 0, 0
            for needs_entry in exec_needs_xml:
                if amalthea_version in ['0_9_5','0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                    # IDiscreteValueDeviation
                    sub_path = ['items', 'needs', 'value']
                    filterArgs = None
                    multipleElements = False

                    values = parser.getElement(sub_path, root=needs_entry, multipleElements=multipleElements, filterArgs=filterArgs)
                    if values is not None:
                        if values.attrib[xsi+'type'] == 'am:DiscreteValueConstant':
                            value = int(parser.xml_get(values, 'value'))
                            lowerBound = value
                            upperBound = value
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueHistogram':
                            print("ExecutionNeed - value type \'am:DiscreteValueHistogram\' not supported.")
                            continue
                        elif values.attrib[xsi+'type'] == 'am:BoundedDiscreteValueDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueBoundaries':
                            # samplingType = parser.xml_get(values, 'samplingType')
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueStatistics':
                            # average = float(parser.xml_get(values, 'average'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueUniformDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueWeibullEstimatorsDistribution':
                            # average = float(parser.xml_get(values, 'average'))
                            # pRemainPromille = float(parser.xml_get(values, 'pRemainPromille'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueBetaDistribution':
                            # alpha = float(parser.xml_get(values, 'alpha'))
                            # beta = float(parser.xml_get(values, 'beta'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:TruncatedDiscreteValueDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueGaussDistribution':
                            # mean = float(parser.xml_get(values, 'mean'))
                            # sd = float(parser.xml_get(values, 'sd'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        
                        min += lowerBound
                        max += upperBound
                        
            return min, max
            
        else:
            return 0, 0


    def __get_ticks(self, executableEntity, elem):
        """ parsing of ActivityGraph entry of type Ticks
        using param elem the function can be both used for "tasks" and "runnables"

        :param executableEntity: xml entry of type Task or Runnable
        :param elem: string
        :rtype: int, int
        """
        if amalthea_version in ['0_9_5', '0_9_6']:
            path = [elem, 'callGraph', 'items']
            filterArgs = ['option', 'Ticks']
        elif amalthea_version in ['0_9_7', '0_9_8', '0_9_9']:
            path = [elem, 'activityGraph', 'items']
            filterArgs = ['option', 'Ticks']
        elif amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4']:
            print("Class Ticks not part of Amalthea version %s" %amalthea_version)
            return 0, 0

        multipleElements = True
        ticks_xml = parser.getElement(path, root=executableEntity, multipleElements=multipleElements, filterArgs=filterArgs)

        if ticks_xml is not None:
            ticks_min, ticks_max = 0, 0
            for ticks_entry in ticks_xml:
                if amalthea_version in ['0_9_5','0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                    # IDiscreteValueDeviation
                    sub_path = ['items', 'default']
                    filterArgs = None
                    multipleElements = False

                    values = parser.getElement(sub_path, root=ticks_entry, multipleElements=multipleElements, filterArgs=filterArgs)
                    if values is not None:
                        if values.attrib[xsi+'type'] == 'am:DiscreteValueConstant':
                            value = int(parser.xml_get(values, 'value'))
                            lowerBound = value
                            upperBound = value
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueHistogram':
                            print("Ticks - value type \'am:DiscreteValueHistogram\' not supported")
                            continue
                        elif values.attrib[xsi+'type'] == 'am:BoundedDiscreteValueDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueBoundaries':
                            # samplingType = parser.xml_get(values, 'samplingType')
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueStatistics':
                            # average = float(parser.xml_get(values, 'average'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueUniformDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueWeibullEstimatorsDistribution':
                            # average = float(parser.xml_get(values, 'average'))
                            # pRemainPromille = float(parser.xml_get(values, 'pRemainPromille'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueBetaDistribution':
                            # alpha = float(parser.xml_get(values, 'alpha'))
                            # beta = float(parser.xml_get(values, 'beta'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:TruncatedDiscreteValueDistribution':
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        elif values.attrib[xsi+'type'] == 'am:DiscreteValueGaussDistribution':
                            # mean = float(parser.xml_get(values, 'mean'))
                            # sd = float(parser.xml_get(values, 'sd'))
                            lowerBound = int(parser.xml_get(values, 'lowerBound'))
                            upperBound = int(parser.xml_get(values, 'upperBound'))
                        
                        ticks_min += lowerBound
                        ticks_max += upperBound
            
            return ticks_min, ticks_max
        else:
            return 0, 0


    def __get_labels(self, task):
        """ parses all labels accessed by a given task.
        also determines whether a given label access (entry) is a reading or writing access

        :param task: xml element of type task
        :rtype: list, list
        """
        if amalthea_version in ['0_9_5', '0_9_6']:
            path = ['tasks', 'callGraph', 'items']
            filterArgs = ['option', 'LabelAccess']
        elif amalthea_version in ['0_9_7', '0_9_8', '0_9_9']:
            path = ['tasks', 'activityGraph', 'items']
            filterArgs = ['option', 'LabelAccess']
        elif amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4']:
            print("Processing of LabelAccess not implemented for Amalthea version %s" %amalthea_version)
            return [], []

        multipleElements = True

        accesses = parser.getElement(path, root=task, multipleElements=multipleElements, filterArgs=filterArgs)
        read = list()
        write = list()

        if accesses is not None:
            if amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                for entry in accesses:
                    # LabelAccessEnum will take on one of the following values: ['_undefined_', 'read', 'write']
                    rw = parser.xml_get(entry, 'access')
                    label = self.__get_accessedLabel(entry)
                    if rw == 'read':
                        read.append(label)
                    elif rw == 'write':
                        write.append(label)
        
        return read, write

    def __get_accessedLabel(self, entry):
        """ parses labels accessed by LabelAccess 

        :param entry: xml element of type LabelAccess
        """
        # LabelAccess -> Label
        if amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
            path = ['LabelAccess', 'Label']
        else:
            print("Processing of LabelAccess not implemented for Amalthea version %s" %amalthea_version)  
        
        lst = parser.getAssocaitedElement(path=path, rootElem=entry)                
        if lst is not None:
            if amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                for label in lst:
                    name = parser.xml_get(label, 'name')
                    # only one label expected, return after first result!
                    return label
                else:
                    return None



    def __get_activation_pattern(self, task):
        """ process stimulus pattern of a given task

        :param task: xml element of type task
        :rtype: pyCPA activation pattern
        """
        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['Task', 'Stimulus']
        else:
            return None

        lst = parser.getAssocaitedElement(path=path, rootElem=task)                
        if lst is not None:
            if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
                # note: only one result expected here! return the first result             
                for stimulus in lst:
                    name = parser.xml_get(stimulus, 'name')

                    xmlElement = stimulus                
                    if xmlElement.attrib[xsi+'type'] == 'am:PeriodicStimulus':
                        # Time recurrence
                        path = ['stimuli', 'recurrence']
                        filterArgs = None
                        multipleElements = False

                        recurrence = parser.getElement(path, root=stimulus, multipleElements=multipleElements, filterArgs=filterArgs)
                        # if multipleElements is True, <elem> is a list -> use for loop to iterate over all elements
                        if recurrence is not None:
                            value = int(parser.xml_get(recurrence, 'value'))
                            # TimeUnit will take on one of the following values: ['_undefined_', 's', 'ms', 'us', 'ns', 'ps']
                            unit = parser.xml_get(recurrence, 'unit')

                            recurrence = value #* units[unit]
                        else:                            
                            recurrence = None

                        # Time minDistance
                        path = ['stimuli', 'minDistance']
                        filterArgs = None
                        multipleElements = False

                        minDistance = parser.getElement(path, root=stimulus, multipleElements=multipleElements, filterArgs=filterArgs)
                        # if multipleElements is True, <elem> is a list -> use for loop to iterate over all elements
                        if minDistance is not None:
                            value = int(parser.xml_get(minDistance, 'value'))
                            # TimeUnit will take on one of the following values: ['_undefined_', 's', 'ms', 'us', 'ns', 'ps']
                            unit = parser.xml_get(minDistance, 'unit')

                            distance = value #* units[unit]
                        else:
                            distance = 0


                        # ITimeDeviation jitter
                        #...

                        jitter = 0

                        # subordinated element: Time offset
                        path = ['stimuli', 'offset']
                        filterArgs = None
                        multipleElements = False

                        offset = parser.getElement(path, root=stimulus, multipleElements=multipleElements, filterArgs=filterArgs)
                        # if multipleElements is True, <elem> is a list -> use for loop to iterate over all elements
                        if offset is not None:
                            #attributes:
                            value = int(parser.xml_get(offset, 'value'))
                            unit = parser.xml_get(offset, 'unit')

                            offset = value #* units[unit]
                        else:
                            offset = 0

                        activation_model = model.PJdEventModel(P=int(recurrence), J=jitter, dmin=distance, phi=offset)
                        return ['pjd', activation_model]
                if xmlElement.attrib[xsi+'type'] == 'am:RelativePeriodicStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:VariableRateStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:PeriodicSyntheticStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:SingleStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:PeriodicBurstStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:EventStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:CustomStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:InterProcessStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None
                if xmlElement.attrib[xsi+'type'] == 'am:ArrivalCurveStimulus':
                    print('[__get_activation_pattern] processing of stimulus %s not implemented yet' % xmlElement.attrib[xsi+'type'])
                    return None





    def __get_deadline(self, task):
        """ retrieve task deadlines

        :param task: xml element of type task
        :rtype: int
        """
        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['Task', 'ProcessRequirement']
        else:
            return None

        lst = parser.getAssocaitedElement(path=path, rootElem=task)                
        if lst is not None:                
            for requirement in lst:
                if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
                    # RequirementLimit limit
                    path = ['requirements', 'limit']
                    filterArgs = None
                    multipleElements = False

                    limit = parser.getElement(path, root=requirement, multipleElements=multipleElements, filterArgs=filterArgs)
                    if limit is not None:
                        xmlElement = limit
                        if xmlElement.attrib[xsi+'type'] == 'am:TimeRequirementLimit':
                            # Time limitValue
                            path = ['limit', 'limitValue']
                            filterArgs = None
                            multipleElements = False

                            limitValue = parser.getElement(path, root=limit, multipleElements=multipleElements, filterArgs=filterArgs)
                            # if multipleElements is True, <elem> is a list -> use for loop to iterate over all elements
                            if limitValue is not None:
                                value = int(parser.xml_get(limitValue, 'value'))
                                # TimeUnit will take on one of the following values: ['_undefined_', 's', 'ms', 'us', 'ns', 'ps']
                                unit = parser.xml_get(limitValue, 'unit')

                                return value #* units[unit]
        return None


    def __get_priority(self, task):
        """ parse scheduling parameters (task priorities)

        :param task: xml element of type task
        :rtype: int
        """
        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['Task', 'TaskAllocation']
        else:
            return None

        lst = parser.getAssocaitedElement(path=path, rootElem=task)                
        if lst is not None:
            for taskAlloc in lst:
                if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
                    # SchedulingParameters schedulingParameters
                    path = ['taskAllocation', 'schedulingParameters']
                    filterArgs = None
                    multipleElements = False

                    schedParam = parser.getElement(path, root=taskAlloc, multipleElements=multipleElements, filterArgs=filterArgs)
                    # if multipleElements is True, <elem> is a list -> use for loop to iterate over all elements
                    if schedParam is not None:
                        priority = int(parser.xml_get(schedParam, 'priority'))
                        return priority
                    else:
                        return None



    def __get_task_semantic(self, task):
        """ a task's semantic can be defined by its name (name includes 'let' or similar descriptors)
        , a custom property of tasks or otherwise if none of the above exists
        process label accesses and check implementation: timed = let

        :param task: xml element of type task
        :rtype: Semantics.LET/BET
        """
        semantic = None

        # option 1: task name
        name = parser.xml_get(task, 'name')
        if ('let' in name or 'Let' in name or 'LET' in name):
            return Semantics.LET
        elif ('bet' in name or 'Bet' in name or 'BET' in name):
            return Semantics.BET 
        
        # option 2: custom property
        try:
            # get custom property
            path = ['task', 'customProperties', 'value']
            customProperty = parser.getElement(path, root=task, multipleElements=False, filterArgs=None)
            value = parser.xml_get(customProperty, 'value')
            
            if value in ['LET', 'let', 'Let']:
                return Semantics.LET
            elif value in ['BET', 'bet', 'Bet']:
                return Semantics.BET
            
        except:
            # no matching custom property found
            pass


        # option 3: label accesses
        if amalthea_version in ['0_9_7', '0_9_8', '0_9_9']:
            path = ['tasks', 'activityGraph', 'items']
            filterArgs = ['option', 'LabelAccess']
        else:
            quit('no supported version for __get_task_semantic()')
        multipleElements = True

        accesses = parser.getElement(path, root=task, multipleElements=multipleElements, filterArgs=filterArgs)

        tmp = list()
        if accesses is not None:
            for access in accesses:
                # LabelAccessImplementation implementation will take on one of the following values: ['_undefined_', 'explicit', 'implicit', 'timed'] 
                try:
                    implementation = parser.xml_get(access, 'implementation')
                    if implementation == 'timed':
                        tmp.append(Semantics.LET)
                    elif (implementation == 'implicit' or implementation == 'explicit'):
                        tmp.append(Semantics.BET)
                except:
                    pass

        tmp = list(dict.fromkeys(tmp)) # remove duplicates
        if len(tmp) == 1:
            return tmp[0]

        print("Inconclusive information about the semantic of task %s" % name)

        return semantic





    ###############
    ## resources ##
    ###############

    def _get_resources(self):
        """ Retrieve all resources from the system description model,
        results are stored in the dictionary self.__pycpa_resources.
        Also determines clock frequencies and IPC classifications

        :rtype: None
        """

        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = [['Amalthea', 'hwModel', 'structures', 'structures', 'modules'], ['Amalthea', 'hwModel', 'structures', 'modules']]
            filterArgs = ['option', 'ProcessingUnit']
        else:
            return None

        multipleElements = True
        pus = parser.getElement(path, multipleElements=multipleElements, filterArgs=filterArgs)

        print("\n[AmaltheaParser] get_resources")

        for pu in pus:
            name = parser.xml_get(pu, 'name')

            frequency = self.__get_frequency(pu)

            print(name, frequency)
            if frequency is not None:
                self.__frequencies[pu] = frequency

            ipc = self.__get_ipc(pu)
            if ipc is not None:
                self.__ipc[pu] = ipc 

            scheduling_policy = self.__get_scheduling_policy(pu)
            r = self.__system.bind_resource(model.Resource(name, scheduling_policy))
            self.__pycpa_resources[pu] = r

            print("%s - Frequency: %s Hz, IPC: %s" %(name, str(frequency), str(ipc)))
            print('\t' + str(scheduling_policy.__class__.__name__))

        
    def __get_frequency(self, resource):
        """ retrieve clock frequencies of a processing unit

        :param resource: xml element of type ProcessingUnit
        :rtype: int
        """
        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['ProcessingUnit', 'FrequencyDomain']
        else:
            return None
        
        lst = parser.getAssocaitedElement(path=path, rootElem=resource)                
        if lst is not None:
            for freqDomain in lst:
                # Frequency defaultValue
                path = ['domains', 'defaultValue']
                filterArgs = None
                multipleElements = False

                freqElem = parser.getElement(path, root=freqDomain, multipleElements=multipleElements, filterArgs=filterArgs)
                if freqElem is not None:
                    value = float(parser.xml_get(freqElem, 'value'))
                    unit = parser.xml_get(freqElem, 'unit')

                    frequency = value * freqUnits[unit]

                    return frequency
        return None

    
    def __get_ipc(self, core):
        """ retrieve IPC classification of a processing unit

        :param resource: xml element of type ProcessingUnit
        :rtype: float
        """
        if amalthea_version in ["0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['ProcessingUnit', 'ProcessingUnitDefinition', 'HwFeature']
        else:
            return None

        ipc = list()

        lst = parser.getAssocaitedElement(path=path, rootElem=core)                
        if lst is not None:    
            for hwFeature in lst:
                if amalthea_version in ["0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:            
                # attributes
                    value = float(parser.xml_get(hwFeature, 'value'))
                    name = parser.xml_get(hwFeature, 'name')

                    ipc.append(value)
        return ipc


    def __get_scheduling_policy(self, resource):
        """ determine scheduling policy applied on a given resource

        :param resource: xml element of type ProcessingUnit
        :rtype: pycpa scheduler object
        """
        scheduler_mapping = {'am:FixedPriorityPreemptive': schedulers.SPPScheduler(), 'spnp': schedulers.SPNPScheduler()}

        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['ProcessingUnit', 'SchedulerAllocation', 'TaskScheduler']
            filterArg = 'responsibility'
        else:
            return None        

        lst = parser.getAssocaitedElement(path=path, rootElem=resource, filterArg=filterArg)
        if lst is not None:                
            for scheduler in lst:
                if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:             
                    # attributes
                    name = parser.xml_get(scheduler, 'name')

                    # TaskSchedulingAlgorithm schedulingAlgorithm
                    path = ['taskSchedulers', 'schedulingAlgorithm']
                    filterArgs = None
                    multipleElements = False

                    algorithm = parser.getElement(path, root=scheduler, multipleElements=multipleElements, filterArgs=filterArgs)
                    if algorithm is not None:
                        xmlElement = algorithm
                        policy = xmlElement.attrib[xsi+'type']

                        if policy not in scheduler_mapping.keys():
                            # get custom property
                            path = ['schedulingAlgorithm', 'customProperties', 'value']
                            customProperty = parser.getElement(path, root=algorithm, multipleElements=False, filterArgs=None)
                            policy = parser.xml_get(customProperty, 'value')

                        try:
                            return scheduler_mapping[policy]
                        except:
                            print("No corresponding pyCPA scheduler mapping found for Amalthea scheduling algorithm %s" % policy)
                            return None


    def __get_executing_resource(self, task):
        """ task to resource mapping

        :param task: xml element of type Task
        :rtype: None
        """
        if amalthea_version in ["0_9_3", "0_9_4", "0_9_5", "0_9_6", "0_9_7", "0_9_8", "0_9_9"]:
            path = ['Task', 'TaskAllocation', 'ProcessingUnit']
        else:
            return None

        lst = parser.getAssocaitedElement(path=path, rootElem=task)               
        if lst is not None:
            if len(lst) > 1:
                print('the mapping of %s is ambiguous! Check the corresponding TaskAllocation element to change this!' % parser.xml_get(task, 'name'))               
            for pu in lst:                
                # attributes
                name = parser.xml_get(pu, 'name')
                # here: only one result expected
                return pu

        return None





    #########################
    ## cause-effect chains ##
    #########################

    def _get_chains(self):
        """ derive cause-effect chains from the AMALHTEA model

        :rtype: None
        """
        print("\n[AmaltheaParser] get_chains")
        
        # option 1: use explicitly modeled label accesses and delay constraints to determine cause-effect chains
        # g = self.__build_data_dependency_graph()
        # delay_constraints = self.__get_delay_constraints()

        # for constraint in delay_constraints:
        #     # get all chain segments
        #     paths = self.__find_data_paths(g, self.__writing_tasks[constraint[1]], self.__writing_tasks[constraint[2]])
            
        #     for path in paths:
        #         tasks = list()
        #         for task in path:
        #             tasks.append(self.__pycpa_tasks[task])

        #         toro_chain = toro_model.extEffectChain(constraint[0], tasks, constraint[3])
        #         print('Chain %s:\t%s, deadline: %s' %(toro_chain.name, str(toro_chain.tasks), toro_chain.e2e_deadline))

        #         self.__chains.append(toro_chain)


        # option 2: Cause-Effect chain modelled using process events
        chains = self.__get_event_chains()
        for chain in chains:
            name = parser.xml_get(chain, 'name')

            # get all chain segments             
            tasks = self.__get_chain_segments(chain)   

            deadline = self.__get_chain_deadline(chain)

            toro_chain = toro_model.extEffectChain(name, tasks, deadline)
            print('Chain %s:\t%s, deadline: %s' %(name, str(toro_chain.tasks), str(deadline)))

            self.__chains.append(toro_chain)


        # option 3: Process Chains
        processChains = self.__get_process_chains()
        for chain in processChains:
            name = parser.xml_get(chain, 'name')

            if amalthea_version in ['0_7_2', '0_9_3', '0_9_8', '0_8_1', '0_9_9', '0_8_3', '0_8_2', '0_9_4', '0_9_5', '0_9_7', '0_9_0', '0_9_1', '0_9_2', '0_8_0']:
                path = ['ProcessChain', 'Task']
            else:
                return None
    
            lst = parser.getAssocaitedElement(path=path, rootElem=chain)
            tasks = list()         
            for t in lst:               
                tasks.append(self.__pycpa_tasks[t])

            deadline = self.__get_process_chain_deadline(chain)

            toro_chain = toro_model.extEffectChain(name, tasks, deadline)
            print('Chain %s:\t%s, deadline: %s' %(name, str(toro_chain.tasks), str(deadline)))

            self.__chains.append(toro_chain)


        

    ############
    # option 1 #
    ############

    # def __build_data_dependency_graph(self):
    #     """ build a graph representing label accesses across all tasks of a given system
    #     DEPRECATED

    #     :rtype: nx.DiGraph
    #     """
    #     data_dependency_graph = nx.DiGraph()

    #     graph_labels = dict()
    #     for label, task in self.__writing_tasks.items():
    #         data_dependency_graph.add_node(task)
    #         graph_labels[task] = parser.xml_get(task, 'name')

    #     for label, tasks in self.__reading_tasks.items():
    #         for task in tasks:
    #             if not(data_dependency_graph.has_node(task)):
    #                 data_dependency_graph.add_node(task)
    #                 graph_labels[task] = parser.xml_get(task, 'name')

    #     for label, tasks in self.__reading_tasks.items():
    #         writing_task = self.__writing_tasks[label]
    #         for task in tasks:
    #             reading_task = task
    #             data_dependency_graph.add_edge(writing_task, reading_task)

    #     nx.draw_networkx(data_dependency_graph, labels=graph_labels)
    #     # plt.show()

    #     return data_dependency_graph


    # def __find_data_paths(self, graph, start, end):
    #     """ graph search, to find end-to-end task dependencies
    #     DEPRECATED

    #     :param graph: nx.DiGraph
    #     :param start: start node
    #     :param end: target node
    #     :rtype: list 
    #     """
    #     return nx.all_simple_paths(graph, start, end)

    
    # def __get_delay_constraints(self):
    #     """ retrieve deadlines for label dependend CECs
    #     DEPRECATED

    #     :type: CEC name, label, label, deadline
    #     """
    #     if amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4', '0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
    #         path = ['Amalthea', 'constraintsModel', 'timingConstraints']
    #         filterArgs = ['option', 'DelayConstraint']
    #     else:
    #         return None
    #     multipleElements = True

    #     ret = list()
    #     constraints = parser.getElement(path, multipleElements=multipleElements, filterArgs=filterArgs)
    #     for constraint in constraints:
    #         name = parser.xml_get(constraint, 'name')

    #         mappingType = parser.xml_get(constraint, 'mappingType')
    #         if mappingType != 'Reaction':
    #             continue # skip constraint            

    #         path = ['timingConstraints', 'upper']
    #         filterArgs = None
    #         multipleElements = False

    #         deadline = None
    #         upper_limit = parser.getElement(path, root=constraint, multipleElements=multipleElements, filterArgs=filterArgs)
    #         if upper_limit is not None:
    #             #attributes:
    #             value = int(parser.xml_get(upper_limit, 'value'))
    #             unit = parser.xml_get(upper_limit, 'unit')

    #             deadline = value #* units[unit]
            
    #         # chain latency describe using LabelEvents (events of first and last label written in a path)
    #         try:            
    #             path = ['DelayConstraint', 'LabelEvent', 'Label']
    #             source = parser.getAssocaitedElement(path, rootElem=constraint, filterArg='source')[0]
                
    #             path = ['DelayConstraint', 'LabelEvent', 'Label']
    #             target = parser.getAssocaitedElement(path, rootElem=constraint, filterArg='target')[0]
                
    #             if deadline is not None:
    #                 ret.append((name, source, target, deadline))
    #         except:
    #             print("Delay constraint had no associations to Labels")
  

    #     return ret


    ############
    # option 2 #
    ############
    
    def __get_event_chains(self):
        """ retrieve all event chains (cf. TADL) from the model.

        :rtype: list of xml elements of type EventChain
        """
        if amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4', '0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
            path = ['Amalthea', 'constraintsModel', 'eventChains']
            filterArgs = None
        else:
            return None
        multipleElements = True

        xml_chains = parser.getElement(path, multipleElements=multipleElements, filterArgs=filterArgs)

        return xml_chains


    def __get_chain_segments(self, chain):
        """ Process chain segments

        :param chain: xml element of type EventChain
        :rtype: list of tasks (toro_model.extTask) 
        """
        if amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
            path = ['eventChains', 'items']
            filterArgs = ['option', 'EventChainContainer']
        else:
            return None
        filterArgs = None
        multipleElements = True

        task_list = list()

        segments = parser.getElement(path, root=chain, multipleElements=multipleElements, filterArgs=filterArgs)
        if segments is not None:
            if amalthea_version in ['0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
                for segment in segments:
                    path = ['items', 'eventChain']
                    ec = parser.getElement(path, root=segment, multipleElements=False, filterArgs=None)

                    # option 1: chain modeled using arbitrary ProcessEvents
                    try:
                        path = ['EventChain', 'ProcessEvent', 'Task']
                        stimulus = parser.getAssocaitedElement(path, rootElem=ec, filterArg='stimulus')[0]
                        if self.__pycpa_tasks[stimulus] not in task_list:
                            task_list.append(self.__pycpa_tasks[stimulus])

                        path = ['EventChain', 'ProcessEvent', 'Task']
                        response = parser.getAssocaitedElement(path, rootElem=ec, filterArg='response')[0]
                        if self.__pycpa_tasks[response] not in task_list:
                            task_list.append(self.__pycpa_tasks[response])

                        continue
                    except:
                        pass

                    # option 2: chain modeled using LabelEvents (read/write access to labels)
                    try:
                        path = ['EventChain', 'LabelEvent', 'Task']
                        stimulus = parser.getAssocaitedElement(path, rootElem=ec, filterArg='stimulus')[0]
                        if self.__pycpa_tasks[stimulus] not in task_list:
                            task_list.append(self.__pycpa_tasks[stimulus])

                        path = ['EventChain', 'LabelEvent', 'Task']
                        response = parser.getAssocaitedElement(path, rootElem=ec, filterArg='response')[0]
                        if self.__pycpa_tasks[response] not in task_list:
                            task_list.append(self.__pycpa_tasks[response])
                        
                        continue
                    except:
                        pass
                        # get tasks accesses the data according to publisher-subscriber communication

            return task_list
        else:
            return None
    

    ############
    # option 3 #
    ############

    def __get_process_chains(self):
        """ derive cause-effect chains from AMALTHEA ProcessChains
        
        :rtype: list(list(tasks))
        """
        if amalthea_version in ['0_7_2', '0_8_0', '0_8_1', '0_8_2', '0_8_3', '0_9_0', '0_9_1', '0_9_2', '0_9_3', '0_9_4', '0_9_5', '0_9_6', '0_9_7', '0_9_8', '0_9_9']:
            path = ['swModel', 'processChains']
            filterArgs = None
        elif amalthea_version in []:
            print("Processing of Runnables currently not supported for Amalthea version %s" %amalthea_version)
            return None

        multipleElements = True
        chains = parser.getElement(path, multipleElements=multipleElements, filterArgs=filterArgs)

        if chains is None:
            return list()
        else:
            return chains









    def __get_chain_deadline(self, chain):
        """ determine deadlines (EventChainLatencyConstraint) of event chains

        :param: xml element of type EventChain
        :rtype: int
        """
        if amalthea_version in ['0_7_2', '0_9_3', '0_9_8', '0_8_1', '0_9_9', '0_8_3', '0_8_2', '0_9_4', '0_9_5', '0_9_7', '0_9_0', '0_9_1', '0_9_2', '0_8_0']:
            path = ['EventChain', 'EventChainLatencyConstraint']
        else:
            return None
        
        lst = parser.getAssocaitedElement(path=path, rootElem=chain)                
        if lst is not None:
            constraint = lst[0] # only one result expected here
            # subordinated element: Time maximum
            path = ['timingConstraints', 'maximum']
            filterArgs = None
            multipleElements = False

            max_constraint = parser.getElement(path, root=constraint, multipleElements=multipleElements, filterArgs=filterArgs)
            if max_constraint is not None:
                #attributes:
                value = int(parser.xml_get(max_constraint, 'value'))
                # TimeUnit unit will take on one of the following values: ['_undefined_', 's', 'ms', 'us', 'ns', 'ps'] 
                unit = parser.xml_get(max_constraint, 'unit')

                deadline = value #* units[unit]
                return deadline

    def __get_process_chain_deadline(self, chain):
        """ determine deadline of an AMALTHEA ProcessChain

        :param chain: xml element of type ProcessChain
        :rtype: int
        """
        if amalthea_version in ['0_7_2', '0_9_3', '0_9_8', '0_8_1', '0_9_9', '0_8_3', '0_8_2', '0_9_4', '0_9_5', '0_9_7', '0_9_0', '0_9_1', '0_9_2', '0_8_0']:
            path = ['ProcessChain', 'ProcessChainRequirement']
        else:
            return None
        
        lst = parser.getAssocaitedElement(path=path, rootElem=chain)
        if lst is not None:
            elem = lst[0] # only a single results expected

            # Time limitValue
            path = ['requirements', 'limit', 'limitValue']
            filterArgs = None
            multipleElements = False

            limitValue = parser.getElement(path, root=elem, multipleElements=multipleElements, filterArgs=filterArgs)
            if limitValue is not None:
                value = int(parser.xml_get(limitValue, 'value'))
                # TimeUnit will take on one of the following values: ['_undefined_', 's', 'ms', 'us', 'ns', 'ps']
                unit = parser.xml_get(limitValue, 'unit')

                return value #* units[unit]