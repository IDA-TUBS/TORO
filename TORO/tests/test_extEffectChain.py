#!/usr/bin/env python3.6
"""
| Copyright (C) 2021 Institute of Computer and Network Engineering (IDA) at TU BS
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Alex Bendrick

Description
-----------
pytest module: validate the decomposition of chains and the determination of deadlines for decomposed chains (class extEffectChain)
"""

import os
import sys
import random

sys.path.append(sys.path[0] + "/../libs/")

from pycpa import model as pmodel

from toro import model
Semantic = model.Semantic

import pytest

## number of test cases per test
n = 100

# @pytest.fixture
# def test_data_decomp():
#     """ create n random test cases """
#     chains = list()
#     for i in range(0,n):
#         name = 'chain' + str(i)
        
#         subchain_cnt = random.randrange(1,11,1) 

#         tasks = list()

#         taskSemantics = [Semantic.BET, Semantic.LET]
#         semantic = random.choice([0,1])

#         for j in range(1, subchain_cnt+1):
#             for k in range(0,3):
#                 # task bcet, etc not relevant, only semantics of importance here 
#                 task_name = 'task' + str(i) + str(j) + str(k) + str(semantic)
#                 offset = 0
#                 bcet = 0
#                 wcet = 1
#                 task = model.extTask(task_name, offset, bcet, wcet, k, taskSemantics[semantic])
#                 tasks.append(task)

#             semantic = int((semantic + 1) % 2)

#         chain = model.extEffectChain(name, tasks)
#         chains.append(chain)
#     yield chains



# def test_decomp(test_data_decomp):
#     """ test cec decomposition """
#     for chain in test_data_decomp:
#         chain.decompose()

#         prev = None
#         for subchain in chain.decomposed_chains:
#             if prev is None:
#                 prev = subchain
#             else:
#                 assert prev.semantic is not subchain.semantic, "semantics of consecutive subchains does not differ!"
#                 prev = subchain

#             for task in subchain.tasks:
#                 assert task.semantic == subchain.semantic, "task semantics do not match subchains semantics"




# @pytest.fixture
# def test_data_tlat():
#     """ create n random test cases """
#     chains = list()

#     for i in range(0,n):
#         name = 'chain' + str(i)

#         taskSemantics = [Semantic.BET, Semantic.LET]
#         semantic = random.choice([0,1])

#         tasks = list()

#         for j in range(0, 2):
#             subchain = model.extEffectChain(name + str(j))

#             for k in range(0,2):
#                 task_name = 'task' + str(i) + str(j) + str(k) + str(semantic)
#                 offset = 0
#                 bcet = 0
#                 wcet = 1
#                 # relevant data
#                 period = random.randrange(2,20,1)

#                 if taskSemantics[semantic] is Semantic.LET:
#                     let = random.randrange(1,period+1,1)
#                     wcrt = None
#                     bcrt = None
#                 elif taskSemantics[semantic] is Semantic.BET:
#                     wcrt = random.randrange(1,period+1,1)
#                     bcrt = random.randrange(1,wcrt+1,1)
#                     let = None

#                 task = model.extTask(task_name, offset, bcet, wcet, k, taskSemantics[semantic], bcrt=bcrt, wcrt=wcrt, let=let)                
#                 task.in_event_model = pmodel.PJdEventModel(P=period)

#                 tasks.append(task)

#             semantic = int((semantic + 1) % 2)

#         chain = model.extEffectChain(name, tasks)
#         chain.decompose()
#         chains.append(chain)
    
#     yield chains


# def test_tlat(test_data_tlat):
#     """ test cec decomposition """
#     for chain in test_data_tlat:
#         prev = chain.decomposed_chains[0]
#         next = chain.decomposed_chains[1]
#         next.calculate_transition_latency(prev)

#         if prev.semantic == Semantic.LET:
#             assert prev.transition_latency == prev.tasks[-1].in_event_model.P, "transition latency of a LET subchain incorrect"
#         elif prev.semantic == Semantic.BET:
#             assert prev.transition_latency == prev.tasks[-1].in_event_model.P + prev.tasks[-1].wcrt - prev.tasks[-1].bcrt, "transition latency of a BET subchain incorrect"




# @pytest.fixture
# def test_data_deadlineCalc():
#     """ create n random test cases """
#     chains = list()

#     for i in range(0,n):
#         name = 'chain' + str(i)

#         random.seed(i+100000)

#         taskSemantics = [Semantic.BET, Semantic.LET]
#         semantic = random.choice([0,1])

#         tasks = list()

#         subchain_cnt = random.randrange(2,6,1)

#         for j in range(0, subchain_cnt):
#             subchain = model.extEffectChain(name + str(j))

#             for k in range(0,5):
#                 task_name = 'task' + str(i) + str(j) + str(k) + str(semantic)
#                 offset = 0
#                 bcet = 0
#                 wcet = 1
#                 # relevant data
#                 period = random.randrange(2,20,1)

#                 if taskSemantics[semantic] is Semantic.LET:
#                     let = random.randrange(1,period+1,1)
#                     wcrt = None
#                     bcrt = None
#                 elif taskSemantics[semantic] is Semantic.BET:
#                     wcrt = random.randrange(1,period+1,1)
#                     bcrt = random.randrange(1,wcrt+1,1)
#                     let = None

#                 task = model.extTask(task_name, offset, bcet, wcet, k, taskSemantics[semantic], bcrt=bcrt, wcrt=wcrt, let=let)                
#                 task.in_event_model = pmodel.PJdEventModel(P=period)

#                 tasks.append(task)

#             semantic = int((semantic + 1) % 2)


#         chain = model.extEffectChain(name, tasks)
#         chain.decompose()

#         chain_latency = 0
#         prev = None

#         sum_let_transistion_latencies = 0
#         sum_bet_transistion_latencies = 0

#         for subchain in chain.decomposed_chains:            
#             subchain_latency = 0
#             for task in subchain.tasks:
#                 subchain_latency += 2* task.in_event_model.P
#             subchain.latency = subchain_latency
#             chain_latency += subchain_latency

#             if prev is None:
#                 prev = subchain
#             else:
#                 subchain.calculate_transition_latency(prev)
#                 if prev.semantic == Semantic.LET:
#                     prev.transition_deadline = prev.transition_latency
#                     sum_let_transistion_latencies += prev.transition_latency
#                 elif prev.semantic == Semantic.BET:
#                     sum_bet_transistion_latencies += prev.transition_latency
#                 prev = subchain
    
#         chain.combined_latency = chain_latency
#         chain.combined_transistion_latencies['let'] = sum_let_transistion_latencies
#         chain.combined_transistion_latencies['bet'] = sum_bet_transistion_latencies

#         chain.e2e_deadline = (chain_latency + sum_let_transistion_latencies + sum_bet_transistion_latencies) * 1.5

#         chains.append(chain)
    
#     yield chains



# def test_deadlineCalc(test_data_deadlineCalc):
#     """ test subchain deadline determination """

#     for chain in test_data_deadlineCalc:
#         for subchain in chain.decomposed_chains:
#             subchain.calculate_preliminary_deadline(chain.e2e_deadline, chain.combined_latency, chain.combined_transistion_latencies)

#         chain_deadline_results = chain.calc_actual_deadlines()
#         # print(chain_deadline_results)