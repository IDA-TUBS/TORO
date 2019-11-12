""" Toro
| Copyright (C) 2019 TU Braunschweig, Institute for Computer and Network Engineering
| All rights reserved.
| See LICENSE file for copyright and license details.

:Authors:
         - Leonie Koehler
         - Nikolas Brendes

Description
-----------
This script is used to call the tool Toro, which calculates robustness margins for 
cause-effect chains.
"""

import os
import sys
from __builtin__ import True
sys.path.append(sys.path[0] + "/libs/")

from pycpa import analysis
from toro import plot as draw_chain
from toro import analysis as toro_analysis
from toro import csv_parser

def __banner():
    _str  = "Toro, Analysis TOol to evaluate the RObustness of cause-effect chains \n"
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



def __get_input(_s):
    if sys.version_info[0] < 3:
        return raw_input(_s)
    else:
        return input(_s)
    

def get_system_dirs(_dir):
    print "======================================================================================="
    print "Searching for systems to analyze in: " 
    print str(_dir)
    print "---------------------------------------------------------------------------------------"     
    folders = list()
    dirs = list()
    for folder in os.listdir(_dir):
        d = os.path.join(_dir, folder)
        if os.path.isdir(d):
            valid = True
            if not os.path.exists(os.path.join(d,"resources.csv")):
                print("ERROR: file not found: " + os.path.join(d,"resources.csv"))
                valid = False
            if not os.path.exists(os.path.join(d,"tasks.csv")):
                print("ERROR: file not found: " + os.path.join(d,"tasks.csv"))
                valid = False
            if not os.path.exists(os.path.join(d,"chains.csv")):
                print("ERROR: file not found: " + os.path.join(d,"chains.csv"))
                valid = False
            if valid:
                folders.append(folder)

    if len(folders) == 1:
        dirs.append(os.path.join(_dir, folders[0]))
    elif len(folders) > 1:
        print("The following systems have been found:")
        for i in range(len(folders)):
            print("  " + str(i + 1) + ": " + folders[i])
        print("  0: all")

        print "---------------------------------------------------------------------------------------"            
        print "To select systems enter their ID or a comma-separated list of IDs."
        print "For instance, enter 1 to select the first of the listed systems,"
        print "enter 1,3 to select the first and the third of the listed systems,"
        print "or enter '0' to select all systems: \n"

        valid_input = False
        while(not valid_input):
            valid_input = True
            ans = __get_input("Enter your choice: ")
            ans = ans.replace("(","").replace(")","")
            for s in range(len(ans)):
                if not (ans[s] is "1" or 
                    ans[s] is "2" or 
                    ans[s] is "3" or 
                    ans[s] is "4" or 
                    ans[s] is "5" or 
                    ans[s] is "6" or 
                    ans[s] is "7" or 
                    ans[s] is "8" or 
                    ans[s] is "9" or 
                    ans[s] is "0" or
                    ans[s] is ","):
                    valid_input = False  
            if valid_input:
                nums = list(set(ans.split(",")))
                nums = list(map(int, nums))
                for n in nums:
                    if not (-1 <= n <= len(folders)):
                        print("ERROR: " + str(n) + " is an invalid input! Try again.")
                        valid_input = False
                        break
            else:
                print("ERROR: Unknown characters! Try again.")
            
        if 0 in nums:
            for folder in folders:
                dirs.append(os.path.join(_dir, folder))
        else:
            for n in nums:
                dirs.append(os.path.join(_dir, folders[n - 1]))

    else:
        print("ERROR: No systems have been found under " + _dir + ".")
        print("Toro terminates.")
        quit()

    return dirs


def perform_analysis(_dir):
    """
        The function calls the main scripts.
    """
    print "\n"
    print "=======================================================================================" 
    print "User-interactive checking of system properties " + "(" + str(os.path.basename(_dir)) + ")"    
    print "---------------------------------------------------------------------------------------"
    # check clock synchronization for distributed cause-effect chains
    clks_sync = False
    while(True):
        if clks_sync == True:
            break
        else:
            print "Is at least one cause-effect chain in the system distributed among several resources?"
            ans = __get_input("(y/n): ") 
            if ans == "y" or ans == "yes":
                
                while(True):
                    print "Are the clocks in the system synchronized and all schedules start at the same time?"
                    ans = __get_input("(y/n): ")
                    if ans == "y" or ans == "yes":
                        clks_sync = True
                        break
                    elif ans == "n" or ans == "no":
                        print("ERROR: The system is not supported.")
                        print("Toro terminates.")
                        quit()
                    else:
                        print("ERROR: invalid input")   
            elif ans == "n" or ans == "no":
                break
            else:
                print("ERROR: invalid input")  

    # check programming paradigm of tasks
    case = 0
    while(True):
        if case == 1 or case == 2 or case == 3:
            break                    
        else:        
            print "Are all cause-effect chains built from LET tasks?"
            ans = __get_input("(y/n): ").lower() 
            if ans == "y" or ans == "yes":
                case = 3
                print "INFO: The setting corresponds to case 3 (see documentation)."
                break
            elif ans == "n" or ans == "no":
                while(True):
                    if case == 1 or case == 2:
                        break                    
                    else:
                        print "Are all cause-effect chains built from BET tasks with implicit deadlines?"
                        ans = __get_input("(y/n): ").lower()
                        if ans == "y" or ans == "yes":
                            while(True):
                                if case == 1 or case == 2:
                                    break
                                else: 
                                    print "Are the WCRTs known from all BET tasks in the cause-effect chains?"
                                    ans = __get_input("(y/n): ").lower()
                                    if ans == "y" or ans == "yes":
                                        case = 1
                                        print "INFO: The setting corresponds to case 1 (see documentation)."                                    
                                        break
                                    elif ans == "n" or ans == "no":
                                        while(True):
                                            print "Toro checks now whether the computation of WCRTs is possible:"
                                            print "> Did you specify ALL tasks in the system (not only those in the listed cause-effect chains)"
                                            print "> Did you specify the task-to-resource mapping for ALL tasks?"
                                            print "> Did you specify the scheduling algorithm for each resource?"
                                            print "> Is the scheduling algorithm for each resource either SPP or SPNP?"
                                            print "> Did you specify for ALL tasks: period, offset=0 (!), WCET, scheduling priority?"
                                            print "> Are task deadlines implicit (=deadline is at the end of the period)?"
                                            print ">> If the answers to all above questions are 'yes', then type 'y'."
                                            print ">> If the answer to at least one question is 'no', then type 'n'."
                                            ans = __get_input(">> (y/n): ").lower()                            
                                            if ans == "y" or ans == "yes":
                                                case = 2
                                                print "INFO: The system corresponds to type 2 (see documentation)."                                            
                                                break
                                            elif ans == "n" or ans == "no":
                                                print("ERROR: The system is not supported.")
                                                print("Toro terminates.")
                                                quit()
                                            else:
                                                print("ERROR: invalid input")                                      
                                    else:
                                        print("ERROR: invalid input")                           
                        elif ans == "n" or ans == "no":
                            print("ERROR: The system is not supported.")
                            print("Toro terminates.")
                            quit()
                        else:
                            print("ERROR: invalid Input")   
            else:
                print("ERROR: invalid Input")                  
    print "\n"
    print "======================================================================================="
    print "Parsing " + str(os.path.basename(_dir))    
    print "---------------------------------------------------------------------------------------"    
    read_data = csv_parser.parse_csv(_dir, case)
    system = read_data.system
    print("Parsing system: " + system.name)
    print("in directory " + _dir)
    print "\n"
    print "======================================================================================="
    print "Calculating maximum end-to-end latencies and robustness margins of cause-effect chains."    
    print "---------------------------------------------------------------------------------------"    
    semantics = ""
    if case == 1:
        task_results = dict()
        for r in system.resources:
            for t in r.tasks:
                task_results[t] = analysis.TaskResult()
                t.analysis_results = task_results[t]
        # override wcrt in task_results
        for t in task_results.keys():
            task_results[t].wcrt = t.wcrt    
            task_results[t].bcrt = t.bcrt          
        semantics = "BET_with_known_WCRTs"
  
    elif case == 2:
        try:
            task_results = analysis.analyze_system(system)
        except:        
            assert False, "WCRT-computation with pyCPA failed."
        semantics = "BET_with_known_WCRTs"
        
    elif case == 3:
        task_results = dict()
        for r in system.resources:
            for t in r.tasks:
                task_results[t] = analysis.TaskResult()
                t.analysis_results = task_results[t]
        for t in task_results.keys():  
            task_results[t].bcrt = t.bcrt                
        semantics = "LET"        
    else:
        print("ERROR: unexpected internal error.")
        
    chain_results = list()
    for chain in read_data.chains:
        print("Analyzing cause-effect chain: " + chain.name)
        try:
            chain_results = toro_analysis.calc_latencies_robustness(chain, semantics, task_results)
        except:
            assert False, ("ERROR: calc_latencies_robustness() failed!")
            return
        print "---------------------------------------------------------------------------------------"         
        chain_results.chain = chain
        chain.results = chain_results
        chain.max_data_age = chain_results.max_data_age
        print "\n"
        print "======================================================================================="
        print "Generating diagrams."    
        print "---------------------------------------------------------------------------------------"          
    for chain in read_data.chains:        
        print "Generating interval graph for chain \"" + chain.name + "_intervals.svg\"."
        draw_chain.draw_read_data_intervals(chain_results, robustness_margin="first", dependency_polygon=True, max_data_age="last").save_file(os.path.join(_dir, chain.name + "_intervals.svg"))
        print "Generating reachability graph for chain \"" + chain.name + "_tree.svg\"."
        draw_chain.draw_dependency_graph(chain_results).save_file(os.path.join(_dir, chain.name + "_tree.svg"))
        print "---------------------------------------------------------------------------------------"          
    print "Generating summarizing diagram \"results.svg\"."
    #draw_chain.draw_results(chains = read_data.chains, tasks = read_data.tasks).save_file(os.path.join(_dir,"Results.svg")
    print "\n"
    print "======================================================================================="
    print "Results."    
    print "---------------------------------------------------------------------------------------"
    print "MAXIMUM END-TO-END LATENCIES:"
    for chain in read_data.chains:
        print("\t Max. end-to-end latency of chain \"" + chain.name + "\" is " + str(chain.max_data_age) + ".")
    print "---------------------------------------------------------------------------------------"
    print "ROBUSTNESS MARGINS:"      
    for task in read_data.tasks:
        print("\t Robustness margin of task \"" + task.name + "\" is " + str(task.robustness_margin) + ".")      
    print "---------------------------------------------------------------------------------------"        
    print("Detailed information can be found in the RESULTS_LOG.txt file.")    
    
    
    log = ""
    chain_log = ""
    for chain in read_data.chains:
        chain_log += log_chain_results(chain.results, chain, os.path.join(_dir, chain.name + "_results.txt"))
    with open(_dir + "/RESULTS_LOG.txt", "w") as log_file:
        log_file.write(__banner() + log + chain_log[1:])    
    print "\n"
    print "======================================================================================="
    print "Done. Toro quits."     
    
    


def log_chain_results(results, chain, _dir):
    """
    This function produces the major content of the file "RESULTS_LOG.txt".
    """
    log = "\n"
    log += "==================================================================\n"
    log += "DETAILED RESULTS FOR CHAIN \"" + chain.name + "\" \n"
    log += "==================================================================\n"
    log += "1) DEFINITION OF THE ANALYZED CAUSE-EFFECT CHAIN \n"    
    log += "------------------------------------------------------------------\n"
    log += " CHAIN: " + chain.name + "\n   sequence: "
    for task in chain.tasks:
        log += " -> " + task.name
    log += "==================================================================\n"
    log += "2) SUMMARY: MAXIMUM END-TO-END LATENCY AND ROBUSTNESS MARGINS \n"    
    log += "------------------------------------------------------------------\n"    
    log += "max end-to-end latency: " + str(results.max_data_age) + "\n"
    for task in results.job_matrix:
        min_rm = float("inf")
        _task_name = task[0].parent_task.name
        _task_next_name = "End Of Chain"
        for t in range(len(chain.tasks) - 1):
            if chain.tasks[t].name == _task_name:
                _task_next_name = chain.tasks[t +1].name
        for job in task:
            if job.robustness_margin != None:
                if job.robustness_margin < min_rm:
                    min_rm = job.robustness_margin 
        log += "robustness margin of " + _task_name + " -> " + _task_next_name + ": " + str(min_rm) + "\n"
    log += "\n"
    log += "==================================================================\n"
    log += "3) DETAILS OF THE LATENCY ANALYSIS: INDIVIDUAL MAX PATH LATENCIES \n"    
    log += "------------------------------------------------------------------\n"  
    log += "Maximum end-to-end latency for each path \n"
    for k in results.path_matrix:
        s = ""
        for i in k:
            s += " -> " + i.name
        if (results.semantics == "LET"):
            data_age = k[-1].Dmin - k[0].Rmin
        if (results.semantics == "BET_with_known_WCRTs"):
            data_age = k[-1].Rmax + k[-1].wcrt - k[0].Rmin
        log += s + "  |  max: " + str(data_age) + "\n"
    log += "==================================================================\n"
    log += "4) DETAILS OF THE ROBUSTNESS ANALYSIS: ROB. MARGINS FOR JOB PAIRS \n"    
    log += "------------------------------------------------------------------\n"  
    for task in results.job_matrix:
        for job in task:
            if job.robustness_margin != None:
                log += " -> " + job.name + " -> " + job.rm_job.name + "  |  RM: " + str(job.robustness_margin) + "\n"
    log += "\n \n \n"
    # write to file
    with open(_dir, "w") as log_file:
        log_file.write(__banner() + log)
    
    return log





if __name__ == "__main__":
    print(__banner())
    _dir = sys.path[0] + "/data"
    if len(sys.argv) > 1:
        _dir = sys.argv[1]

    dirs = get_system_dirs(_dir)
    for d in dirs:
        perform_analysis(d)
