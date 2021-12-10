#!/usr/bin/env python3.6
"""
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Alex Bendrick

Description
-----------
pytest module: uses a test suite, defined in params of test_data to evaluate the tool's performance
"""

import os
import sys
import dill as pickle
import time
import timeit

sys.path.append(sys.path[0] + "/../libs/")

import pycpa
from toro import model
from toro import system_analysis

import pytest
import cProfile

## path to current file
p_file = os.path.dirname(os.path.abspath(__file__))

p_test_data = '/testData/'


class argsDummy(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)



###########################
## functional validation ##
###########################

@pytest.fixture(params = [
        ('system_model_0.pkl', 'system_model_0_results.pkl'),
        ('system_model_1.pkl', 'system_model_1_results.pkl'),
        ('system_model_2.pkl', 'system_model_2_results.pkl')#, 
        # ('system_model_3.pkl', 'system_model_3_results.pkl'), # decomposable chain
        # ('system_model_4.pkl', 'system_model_4_results.pkl'), # decomposable chain
        # ('system_model_5.pkl', 'system_model_5_results.pkl'), # decomposable chain
        # ('system_model_6.pkl', 'system_model_6_results.pkl')  # decomposable chain
])
def test_data(request):
    """ load test cases """
    # part one: system and cause-effect chain descriptions
    file_name_system = p_file + p_test_data + request.param[0]
    if os.path.exists(file_name_system):
        with open(file_name_system, 'rb') as f:
            sys_tuple = pickle.load(f)
    
    # part one: results for each system-chain pair
    file_name_results = p_file + p_test_data + request.param[1]
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

    assert results == new_results

















##################
## benchmarking ##
##################


def load_data(chainType, withWCRT=True, small=False):
    # choose system size
    if small is True:
        small = '_small'
    else:
        small = ''

    p_performanceTests = p_file + p_test_data + 'performanceTests/'

    test_data_dict_name = p_performanceTests + 'testData' + small + '.pkl'
    if os.path.exists(test_data_dict_name):
        with open(test_data_dict_name, 'rb') as f:
            test_data_dict = pickle.load(f)
    else:
        assert False, "No test data could be found"
    
    
    # test case = combination of system with cause effect chain + additional information about the test case (tuple)
    test_cases = list()

    for key, directory in test_data_dict.items():
        if withWCRT is True:
            p_system = p_performanceTests + 'systems' + small + '/' + key + '/system_with_wcrts.pkl'
        else:
            p_system = p_performanceTests + 'systems' + small + '/' + key + '/system_without_wcrts.pkl'

        if os.path.exists(p_system):
            with open(p_system, 'rb') as f:
                system = pickle.load(f)
        else:
            assert False, "Test data could not be found"

        
        if chainType == 'simple':
            files = directory['simple']
            case = 4 # only 1 or 2 possible, will this work? it should!
        elif chainType == 'mixed':
            files = directory['mixed2']
            case = 4
        
        # load list with chains, data is structured as follows:        
        # data = [actual chain, number of subchains, length of chain length of chain, list of subchain semantics, list of subchain hyperperiods]
        for f in files:
            filename = p_file + '/testData/performanceTests' + f
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    chains = pickle.load(f)
                    for chain in chains:    
                        # TODO needs some changes if systems with more than one chain are provided                    
                        # rebuild chain with task from system, since pickling objects in different locations does seem to lead to issues
                        actual_chain = chain[0]
                        actual_chain.tasks = rebuild_chain(actual_chain, system)

                        # retrieve additional test case data from data tuple
                        info = list(chain[1:len(chain)])

                        test_case = (system, [actual_chain], case, info)
                        test_cases.append(test_case)
            else:
                assert False, "Test data could not be found"

    return test_cases


def rebuild_chain(chain, system):
    """
    """
    tmp = list()
    for task in chain.tasks:
        for r in system.resources:
            for t in r.tasks:
                if task.name == t.name:
                    tmp.append(t)
    return tmp



def wrapper(func, *args, **kwargs):
    """
    """
    def wrapped():
        res = func(*args, **kwargs)
        return res
    return wrapped


def run_benchmark(chainType, withWCRT=True, useProfiler=False, small=False):
    """
    """
    # load test cases
    test_cases = load_data(chainType, withWCRT, small)

    # list for storing results
    perf_results = list()

    if useProfiler is True:
        # init profiler
        pr = cProfile.Profile()

    cnt = 0
    
    for test_case in test_cases:

        args = argsDummy(lat=True, rm=True, wcrt=True, plot=False, test=False)
        system = test_case[0]
        chains = test_case[1]
        case = test_case[2]
        info = test_case[3]

        wrapped_func = wrapper(system_analysis.perform_analysis, args, system, chains, True)

        if useProfiler is True:
            pr.enable()

        repetition_cnt = 1
        # execute function under test (here: system_analysis.perform_analysis)
        t = timeit.timeit(wrapped_func, number=repetition_cnt)
        
        if useProfiler is True:
            pr.disable()

        res = (cnt, info, t)
        perf_results.append(res)

        cnt += 1        
    
    # dump performance results to file system
    cnt = 0
    while (os.path.exists(p_file + '/perf_results/res_' + str(cnt) + '.pkl')):
        cnt += 1
    with open(p_file + '/perf_results/res_' + str(cnt) + '.pkl', 'wb') as f:
        pickle.dump(perf_results, f, pickle.HIGHEST_PROTOCOL)

    for res in perf_results:
        print(res)


    if useProfiler is True:
        # dump performance profile
        pr.dump_stats(p_file + '/perf_results/performance_gt_case59.prof')





if __name__ == "__main__":
    assert False, "No performance test data in this repo"
    run_benchmark('simple', withWCRT=True, useProfiler=True, small=True)

   