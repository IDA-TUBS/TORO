#!/usr/bin/env python3.6
"""
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Alex Bendrick

Description
-----------
pytest module: validate the analysis class for BET and LET chains
"""

import os
import sys
import random
import dill as pickle

sys.path.append(sys.path[0] + "/../libs/")

from pycpa import model as pycpaModel
from pycpa import schedulers as pycpaSchedulers
from toro import model
from toro import system_analysis

Semantic = model.Semantic

import pytest

## path to current file
p_file = os.path.dirname(os.path.abspath(__file__))

p_test_data = '/testData/csv_topology_test/pickled_combined/'
p_results = '/testData/csv_topology_test/results/'

p_results_rand = '/testData/randomModels_topologies/res/'


class argsDummy(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


###########################
## functional validation ##
###########################

@pytest.fixture(params = [x for x in os.listdir(p_file + p_test_data)])
def test_data(request):
    """ load test cases """
    # part one: system and cause-effect chain descriptions
    file_name_system = p_file + p_test_data + request.param
    if os.path.exists(file_name_system):
        with open(file_name_system, 'rb') as f:
            sys_tuple = pickle.load(f)
    
    # part two: results for each system-chain pair
    res_pickled = request.param.replace("test_n", "").replace(".pkl", "_results.pkl")
    file_name_results = p_file + p_results + res_pickled
    if os.path.exists(file_name_results):
        with open(file_name_results, 'rb') as f:
            results = pickle.load(f)
    yield (sys_tuple, results)
    # finalizer not needed!


def test_perform_analysis(test_data):
    """
    """
    # TODO when testing for code coverage, vis and test = True as well?
    args = argsDummy(lat=True, rm=True, wcrt=True, plot=False, test=True)

    system_description = test_data[0]
    results = test_data[1]
    new_results = system_analysis.perform_analysis(args, system_description[0], system_description[1])

    assert len(new_results.chain_latencies) == 1, "No decomposed chains expected here"
    assert new_results == results


n = 100
# also test random models
@pytest.fixture(params = [x for x in range(0,n)])
def test_data_random(request):
    """ create n random test cases """

    # create resource
    system = pycpaModel.System()
    r = system.bind_resource(pycpaModel.Resource('resource', pycpaSchedulers.SPPScheduler()))

    # create tasks an chain
    seed = request.param
    random.seed(seed)

    name = 'chain_' + str(request.param)

    taskSemantics = [Semantic.BET, Semantic.LET]
    semantic = random.choice([0,1])

    tasks = list()

    for k in range(0,3):
        task_name = str(semantic) + '_task' + str(k)

        # 2 <= P < 20
        period = random.randrange(2,20,1)        
        bcet = 0
        if taskSemantics[semantic] is Semantic.LET:
            let = random.randrange(1,period+1,1)
            wcrt = None
            bcrt = None
            try:
                offset = random.randrange(0,period-let,1)
            except:
                offset = 0
            wcet = None
        # relevant data
        elif taskSemantics[semantic] is Semantic.BET:
            let = None
            wcrt = random.randrange(2,period+1,1)
            bcrt = random.randrange(1,wcrt+1,1)
            try:
                offset = random.randrange(0,period-wcrt,1)
            except:
                offset = 0
            wcet = random.randrange(1,wcrt,1)

        task = model.extTask(task_name, offset, bcet, wcet, k, taskSemantics[semantic], bcrt=bcrt, wcrt=wcrt, let=let)                
        task.in_event_model = pycpaModel.PJdEventModel(P=period)
        r.bind_task(task)

        tasks.append(task)

    semantic = int((semantic + 1) % 2)

    chain = model.extEffectChain(name, tasks)

    # chain has no deadline itself, results only derived from implicit job attributes and the graph's topology

    # load results
    file_name_results = p_file + p_results_rand + "rand_n3_seed" + str(seed) + "_results.pkl"
    if os.path.exists(file_name_results):
        with open(file_name_results, 'rb') as f:
            results = pickle.load(f)
        
    yield (system, [chain], seed, results)

    # file_name = "rand_n3_seed" + str(seed)
    # with open(file_name + '.pkl', 'wb') as f:
    #     case = 3 if taskSemantics == Semantic.LET else 1
    #     tuple = (system, [chain], case)
    #     pickle.dump(tuple, f, pickle.HIGHEST_PROTOCOL)


    


def test_perform_analysis_rand(test_data_random):
    """
    """
    # TODO when testing for code coverage, vis and test = True as well?
    args = argsDummy(lat=True, rm=True, wcrt=True, plot=False, test=True)

    system_description = test_data_random[0]
    chain_description = test_data_random[1]
    seed = test_data_random[2]
    results = test_data_random[3]

    new_results = system_analysis.perform_analysis(args, system_description, chain_description)

    # print(new_results.toString())
    # print(results.toString())
    assert len(new_results.chain_latencies) == 1, "No decomposed chains expected here"
    assert new_results == results