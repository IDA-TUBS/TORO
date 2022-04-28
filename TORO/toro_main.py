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
This script calls the tool Toro, which calculates upper bounds on latencies and robustness margins for 
cause-effect chains. It combines all parts of TORO, providing the functionality to users in form of a
console application.
"""


import sys
import argparse
# import dill as pickle

sys.path.append(sys.path[0] + "/libs/")

# model parsing
from toro import io
from toro import model_parser as ModelParser

# chain analyses
from toro import model
Semantic = model.Semantic
from toro import chain_analysis as ChainAnalysis
toro_analysis_TT = ChainAnalysis.analysis_LET_BET
from toro import system_analysis


## dict of chain analysis objects for each sub_chain
analyses = dict()





########################
## parse input models ##
########################     

def parse_model(parser, dir):
    """ parse a system description model located at dir

    :param parser: Parser object (implements abstract ModelParser)
    :paran dir: string
    :rtype: pyCPA System object, TORO extEffectChain object
    """    
    assert dir is not None
    system, chains = parser.parse(dir)    

    return system, chains






##########
## main ##
##########

if __name__ == "__main__":
    toro_parser = argparse.ArgumentParser(description='TORO tool.')
    toro_parser.add_argument('-m',
                        action = 'store',
                        default = None,
                        dest = 'model_type',
                        help = '[mandatory] model types: csv, amalthea (only with optional parser)')
    toro_parser.add_argument('--path',  
                        type=str,
                        default='./data',
                        help='the path to the folder where the system model is located')
    toro_parser.add_argument('--plot', 
                        dest='plot', 
                        action='store_true',
                        help='diagrams are generated')   
    toro_parser.add_argument('--disableWCRT', 
                        dest='wcrt', 
                        action='store_false',
                        help='disables computation of upper bounds on task response times')     
    toro_parser.add_argument('--disableLat', 
                        dest='lat', 
                        action='store_false',
                        help='disables computation of upper bounds on latencies')
    toro_parser.add_argument('--disableRM', 
                        dest='rm', 
                        action='store_false',
                        help='disables computation of robustness margins for the given task set')
    toro_parser.add_argument('--test', 
                        dest='test', 
                        action='store_true',
                        help='enables verification of robustness margins')
    toro_parser.add_argument('--store', 
                        dest='store', 
                        action='store_true',
                        help='write results to csv files')
    toro_args = toro_parser.parse_args()    
    
    io.PrintOuts.banner()

    # parse models
    systems = list()
    if toro_args.model_type is not None:
        file_manager = io.FileManagement()
        if toro_args.model_type == 'csv':
            # parse csv model descriptions
            dirs = file_manager.get_system_dirs(toro_args)

            # initialize csv parser
            parser = ModelParser.CSVParser(toro_args)

            for d in dirs:
                # parse each model description seperatly
                system, chains = parser.parse(d)
                systems.append((system, chains, d))

                # # dump parsed systems using pickle
                # s = (d.split('/')[3].replace(".", "_"))
                # file_name = 'test_n'
                # with open(file_name + str(s) + '.pkl', 'wb') as f:
                #     pickle.dump((system, chains), f, pickle.HIGHEST_PROTOCOL)

        elif toro_args.model_type == 'amalthea':
            dir = file_manager.get_system_dirs(toro_args)

            try:
                parser = ModelParser.AmaltheaParser(toro_args, dir)
            except:
                quit("[ERROR] AmaltheaParser not complete, install Amalthea2PyCPA to use TORO's Amalthea parser.")
                
            system, chains = parser.parse()
            systems.append((system, chains, dir))
        else:
            raise NotImplementedError("Processing of a model of type %s is not supported! Only \"csv\" and \"amalthea\" will work.")
    else:
        print('\t[-m] Missing model selection: Choose either \'csv\' or \'amalthea\'')
        sys.exit()
    


    # analyse all systems
    for sys_tuple in systems:
        results = system_analysis.perform_analysis(toro_args, sys_tuple[0], sys_tuple[1])

        if toro_args.store is True:
            # write result to csv files
            if toro_args.model_type == 'amalthea':
                c = sys_tuple[2].rfind("/")
                path = sys_tuple[2][0:c]
            else:
                path = sys_tuple[2]
            results.toCSV(path)   
