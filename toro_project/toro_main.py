#!/usr/bin/env python
# -*- coding: utf-8 -*- 
 
"""
Copyright Notice
================
Toro
| Copyright (C) 2019 Innovationsgesellschaft Technische Universitaet Braunschweig mbH (iTUBS)
| All rights reserved.
| See LICENSE file for copyright and license details.
 
:Authors:
         - Leonie Koehler
         - Nikolas Brendes
 
Description
===========
This script calls the tool Toro, which calculates upper bounds on latencies and robustness margins for 
cause-effect chains.
"""
 
import os
import sys
import argparse 
import copy
import csv
#from __builtin__ import True
sys.path.append(sys.path[0] + "/libs/")
 
import pycpa
from toro import io
from toro import check
from toro import plot as draw_chain
from toro import analysis as toro_analysis
from toro import csv_parser


 
def __banner():
    _str  = "Toro, Analysis TOol to evaluate the latencies and RObustness of cause-effect chains \n"
    _str += "Copyright (C) 2019 iTUBS Germany \n"
    _str += "All rights reserved. \n"
    _str += "See LICENSE file for copyright and license details. \n"
    _str += "     _____\n"
    _str += "    /__   \___  _ __ ___  \n"
    _str += "      / /\/ _ \| '__/ _ \  \n"
    _str += "     / / | (_) | | | (_) | \n"
    _str += "     \/   \___/|_|  \___/  \n"
    _str += "\n \n"
    return _str
 

 
 

def perform_analysis(args, case, _dir):
    """
        This function manages the entire analysis process.
    """
    
    # Parsing
    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    print("Parsing " + str(os.path.basename(_dir)))    
    io.PrintOuts.line()
    read_data = csv_parser.parse_csv(_dir, case)
    system = read_data.system
    print("Parsing system: " + system.name + "in directory " + _dir + "\n")

    
    # WCRTS    
    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    print("Calculating worst-case response times of tasks.")    
    io.PrintOuts.line()   
    semantics = ""
    if case == 1:
        task_results = dict()
        for r in system.resources:
            for t in r.tasks:
                task_results[t] = pycpa.analysis.TaskResult()
                t.analysis_results = task_results[t]
        # override wcrt in task_results
        for t in task_results.keys():
            task_results[t].wcrt = t.wcrt    
            task_results[t].bcrt = t.bcrt          
        semantics = "BET_with_known_WCRTs"
    
    elif case == 2:
        try:
            task_results = pycpa.analysis.analyze_system(system)
            for r in system.resources:
                for t in r.tasks:            
                    t.wcrt = task_results[t].wcrt
                    t.bcrt = task_results[t].bcrt
        except:        
            assert False, "WCRT-computation with pyCPA failed."
        semantics = "BET_with_known_WCRTs"
          
    elif case == 3:
        task_results = dict()
        for r in system.resources:
            for t in r.tasks:
                task_results[t] = pycpa.analysis.TaskResult()
                t.analysis_results = task_results[t]
        for t in task_results.keys():  
            task_results[t].bcrt = t.bcrt   
            task_results[t].wcrt = t.wcrt              
        semantics = "LET"        
        
    elif case == 4: 
        try:
            task_results = pycpa.analysis.analyze_system(system)
            # override wcrt in task_results for LET tasks
            for t in task_results.keys():
                if 'LET' in t.name or 'let' in t.name: 
                    task_results[t].wcrt = 'n/a'   
                    task_results[t].bcrt = 'n/a'                 
            for r in system.resources:
                for t in r.tasks:            
                    t.wcrt = task_results[t].wcrt
                    t.bcrt = task_results[t].bcrt
        except:        
            assert False, "WCRT-computation with pyCPA failed."        
        semantics = "Mixed_programming_paradigms_with_known_WCRTs"
        
        
    else:
        print("ERROR: unexpected internal error.")


    with open(_dir+'/wcrt_results.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';') 
        writer.writerow(['task_name', 'wcrt'])
        for t in task_results.keys():     
            writer.writerow([t.name, task_results[t].wcrt])
            print(t.name + ': WCRT=' + str(task_results[t].wcrt) + ', BCRT = ' + str(task_results[t].bcrt))   

    if args.wcrt == True and args.lat == False:    
        return     

 
    # Analysis    
    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    if args.lat == True:  
        print("Calculating maximum end-to-end latencies of cause-effect chains.")
    else:
        print("Calculating maximum end-to-end latencies and robustness margins of cause-effect chains.")        
    io.PrintOuts.line()   
    chain_results_dict = dict()
    for chain in read_data.chains:  
        print("Analyzing cause-effect chain: " + chain.name) 
        print(chain.tasks)
        try:
            chain_results = toro_analysis.ChainProperties(args, chain, task_results, case)
        except:
            assert False, ("ERROR: calc_latencies_robustness() failed!")
            return        
        chain_results_dict[chain.name] = chain_results
        io.PrintOuts.newline()
    toro_analysis.compute_rm_min_all_chains(chain_results_dict, read_data.tasks, read_data.chains)   
    toro_analysis.compute_delta_let_all_chains(chain_results_dict, read_data.tasks, read_data.chains)  
        
        
    # Analysis: latency results.    
    io.PrintOuts.line() 
    for chain in read_data.chains:
        print("The maximum end-to-end latency of chain \"" + chain.name + "\" is " 
              + str(chain_results_dict[chain.name].max_e2e_lat) + ".")
        
    with open(_dir+'/lat_results.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';') 
        writer.writerow(['chain_name', 'lat'])
        for chain in read_data.chains:    
            writer.writerow([chain.name, chain_results_dict[chain.name].max_e2e_lat])
        
        
    # Analysis: robustness results.         
    if args.lat == False: 
        io.PrintOuts.line()        
        for task in read_data.tasks: 
            if case == 1 or case == 2:            
                print("Robustness margin of task \"" + task.name + "\" in " + \
                        " is " + str(chain_results_dict['RMs_system'][task.name]))     
            elif case == 3: 
                print("Robustness margin of task \"" + task.name + "\" in " + \
                        " is " + str(chain_results_dict['RMs_system'][task.name]))                           
            else:
                raise

            if case == 3: 
                print("Delta LET of task \"" + task.name + "\" in " + \
                        " is " + str(chain_results_dict['Delta_LET_system'][task.name]))               
            
        io.PrintOuts.line()  
      
    with open(_dir+'/rm_results.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';') 
        if case == 1 or case == 2:
            writer.writerow(['task_name', 'rm'])
            for task in read_data.tasks:     
                writer.writerow([task.name, chain_results_dict['RMs_system'][task.name]])
        elif case == 3:
            writer.writerow(['task_name', 'rm','delta_let'])
            for task in read_data.tasks:  
                writer.writerow([task.name, 
                                 chain_results_dict['RMs_system'][task.name],
                                 chain_results_dict['Delta_LET_system'][task.name]])
        else:
            raise
  
#     io.PrintOuts.newline()
#     io.PrintOuts.doubleline()
#     print("Generating diagrams.")    
#     io.PrintOuts.line()          
#     for chain in read_data.chains:     
#         pass   
# #         print("Generating interval graph for chain \"" + chain.name + "_intervals.svg\".")
# #         draw_chain.draw_read_data_intervals(chain_results_dict[chain.name], 
# #                                             semantics=semantics, 
# #                                             robustness_margin="none", 
# #                                             dependency_polygon=True, 
# #                                             max_data_age="last").save_file(os.path.join(_dir, chain.name + "_intervals.svg"))
# #         print("Generating reachability graph for chain \"" + chain.name + "_tree.svg\".")
# #         draw_chain.draw_dependency_graph(chain_results_dict[chain.name]).save_file(os.path.join(_dir, chain.name + "_tree.svg"))
# #         io.PrintOuts.line()          
# #     print("Generating task graph \"task_graph.svg\".")
# #     draw_chain.draw_results(chains = read_data.chains, 
# #                             tasks = read_data.tasks, 
# #                             chain_results_dict=chain_results_dict).save_file(os.path.join(_dir,"task_graph.svg"))
#     io.PrintOuts.line()


 
 
 
if __name__ == "__main__":
    
    toro_parser = argparse.ArgumentParser(description='TORO tool.')
    toro_parser.add_argument('--path',  
                        type=str,
                        default='./data',
                        help='the path to the systems folder')
    toro_parser.add_argument('--wcrt', 
                        dest='wcrt', 
                        action='store_true',
                        help='computes only upper bounds on task response times')     
    toro_parser.add_argument('--lat', 
                        dest='lat', 
                        action='store_true',
                        help='computes only upper bounds on latencies')                                             
    toro_args = toro_parser.parse_args()    
    
    print(__banner())   
    
    
    dirs = io.FileManagement()._get_system_dirs(toro_args)
    
    
    check_properties = check.SystemProperties()
    check_properties._start(toro_args.path)
    check_properties._clock_sync() 
    check_properties._programming_paradigm() 
    check_properties._activation_pattern()
    check_properties._task_deadlines()
    if check_properties.pp_bet == True or check_properties.pp_mixed == True: 
        check_properties._wcrt_knowledge()
        if check_properties.wcrt_known == False:
            check_properties._wcrt_computation()
    check_properties._determine_case()        
   
   
    for d in dirs:
        chain_results_dict = perform_analysis(toro_args, check_properties.case, d)


    io.PrintOuts.newline()
    io.PrintOuts.doubleline()
    print("Done. Toro quits.")   