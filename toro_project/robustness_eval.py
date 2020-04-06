#! python
# coding: utf-8

__author__     = 'Leonie Koehler'
__maintainer__ = 'Leonie Koehler'
__email__      = 'koehler@ida.ing.tu-bs.de'


import os
import glob
import re 
import csv 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from libs.toro import io 


#-----------------------------------------------------------------------------#
# constants                                                                   #
#-----------------------------------------------------------------------------#
DIR_SYSTEMS = './data/EMSOFT20/backup/2020-04-05_run'
DIR_RESULTS = os.path.join(DIR_SYSTEMS, 'rm_plots')
FILE_WCRT_RESULTS = 'wcrt_results.csv' 
FILE_LAT_RESULTS = 'lat_results.csv'
FILE_RM_RESULTS = 'rm_results.csv'

#-----------------------------------------------------------------------------#
# classes                                                                     #
#-----------------------------------------------------------------------------#

class Task(object): 
	def __init__(self, name):
		self.name = name 
		self.wcrt = -1 
		self.period = -1
		self.successor = None
		self.successor_period = None

	def set_wcrt(self, wcrt):
		self.wcrt = wcrt
		

class Chain(object):
	def __init__(self, name, deadline, tasks):
		self.name = name
		self.deadline = deadline
		self.tasks = tasks 
		self.lat = None



#-----------------------------------------------------------------------------#
# import data                                                                 #
#-----------------------------------------------------------------------------#	

def SetScheduler(path, scheduler):
	df = pd.read_csv(os.path.join(path, 'resources.csv'), sep=';')
	df["Scheduler"] = scheduler
	df.to_csv(os.path.join(path, 'resources.csv'), sep=';', index=False)


def ImportInfo(path): 
	u = -1 
	nTSeg = -1
	nSeg = -1

	with open(os.path.join(path, 'info.txt')) as file:
		csv_file = csv.reader(file, delimiter='=')
		for line in csv_file: 
			if (line[0] == 'U'):
				u = float(line[1].replace(',','.')) 
			elif (line[0] == 'N_T_Seg'): 
				nTSeg = int(line[1])
			elif (line[0] == 'N_Seg'): 
				nSeg = int(line[1]) 

	return u, nTSeg, nSeg


def ImportChains(path): 
	"""
	This function imports the info from chains.csv
	"""
	chains = list()
	
	with open(os.path.join(path, 'chains.csv'), mode='r') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter=';')
	    line_count = 0
	    for row in csv_reader:
	    	members = list()
	    	if line_count == 0:
	    		pass 
	    	else:
	        	for member_name in row[2:]:
	        		members.append(Task(member_name))
	        	chains.append(Chain(name = row[0], deadline = row[1], tasks = members))
	    	line_count += 1
	return chains 


def ImportTaskProperties(path,task): 
	"""
	read wcrts for each task
	""" 
	with open(os.path.join(path, 'tasks.csv'), mode='r') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter=';')
	    line_count = 0
	    for row in csv_reader:
	    	members = list()
	    	if line_count == 0:
	    		pass
	    	else:
	        	if row[0] == task.name: 
	        		task.period = int(row[1])
	        		break
	    	line_count += 1


def ImportWCRT(path,task): 
	"""
	read wcrts for each task
	""" 
	with open(os.path.join(path, 'wcrt_results.csv'), mode='r') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter=';')
	    line_count = 0
	    for row in csv_reader:
	    	if line_count == 0:
	    		pass
	    	else:
	        	if row[0] == task.name: 
	        		wcrt = int(row[1])
	        		break
	    	line_count += 1
	return wcrt
	        	

def ImportLAT(path, chain): 
	"""
	read wcrts for each task
	""" 
	with open(os.path.join(path, 'lat_results.csv'), mode='r') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter=';')
	    line_count = 0
	    for row in csv_reader:
	    	if line_count == 0:
	    		pass
	    	else:
	        	if row[0] == chain.name: 
	        		lat = int(row[1])
	        		break
	    	line_count += 1
	return lat


def ImportRM(path,task): 
	"""
	read wcrts for each task
	""" 
	with open(os.path.join(path, 'rm_results.csv'), mode='r') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter=';')
	    line_count = 0
	    for row in csv_reader:
	    	if line_count == 0:
	    		pass
	    	else:
	        	if row[0] == task.name: 
	        		rm = int(row[1])
	        		if row[2] == 'n/a':
	        			theta = float('Inf')
        			else:
	        		 	theta = int(row[2])
	        		break
	    	line_count += 1
	return (rm, theta)


def ImportSuccessorTask(task, chain):
	if task.name != chain.tasks[-1].name:
		task.successor = chain.tasks
		


	
	
#-----------------------------------------------------------------------------#
# eval function                                                               #
#-----------------------------------------------------------------------------#	
					
def eval(path): 	
	"""
	This function reads csv results.
	"""
	index = 0
	# get system folders
	sys_folder_paths = [ f.path for f in os.scandir(path = path) if f.is_dir() ]
	 
	#create one data frame for each system 
	frames =  list()
	for p in sys_folder_paths: 
		
		# check if all results files exist, otherwise skip and notify
		if (os.path.isfile(os.path.join(p, FILE_LAT_RESULTS)) and
			os.path.isfile(os.path.join(p, FILE_WCRT_RESULTS)) and 
			os.path.isfile(os.path.join(p, FILE_RM_RESULTS))):
			
			print('Evaluating ' + str(p))
			# enforce spp-scheduler
			#SetScheduler(path=p, scheduler='sppscheduler')
			
			# get sys info
			[u, nTSeg, nSeg] = ImportInfo(p)
			
			# get chains
			chains = ImportChains(p)
			for c in chains:
				# get chain tasks: 
				c.lat = ImportLAT(p, c)
				# get properties of chain task
				for t in c.tasks: 
					ImportTaskProperties(path=p, task=t)
					t.wcrt = ImportWCRT(path=p, task=t)
					(t.rm, t.theta) = ImportRM(path = p, task = t)
				# get properties of successor tasks
				for t in c.tasks:	
					if t.name != c.tasks[-1].name:
						t.successor = c.tasks[c.tasks.index(t)+1]
						t.successor_period = t.successor.period / float(1000)
					else:
						t.successor_period = 'n/a'
				# append task-related data frame
				for t in c.tasks:			
					frame = pd.DataFrame(
						{
							'task_name'      	: [t.name],
							'period [ms]'    	: [t.period/ float(1000)],
							'period of the successor task [ms]': [t.successor_period],
							'wcrt [ms]'		 	: [t.wcrt/ float(1000)],
							'slack [ms]'        : [(t.period - t.wcrt)/ float(1000)],
							'norm_slack' : [(t.period - t.wcrt)/t.period],							
							'rm [ms]'			: [t.rm/ float(1000)],
							'rm/period' 		: [t.rm / float(t.period)], 
							'rm/slack'          : [t.rm /(t.period - t.wcrt)],
							'theta [ms]'        : [t.theta/ float(1000)],
							'theta/period'      : [t.theta / float(t.period)],
							'sys_name'  : [os.path.basename(p)],
							'util' 		: [u],   
							'nSeg'      : [nSeg],
							'nTSeg' 	: [nTSeg], 
							'e2e-deadline' : c.deadline
							}, index = [index])
					index += 1
					#print('new frame: ')
					#print(frame)
					#print('\n\n')					
					frames.append(frame)
		else:
 			print('Skipped ' + str(p) + ' because no result files were available.')
		io.PrintOuts.line()
	#concatenate all frames
	
	
	io.PrintOuts.newline()
	io.PrintOuts.doubleline()
	print('Starting to plot.')
	
	# save frames to csv 
	frames_pd = pd.concat(frames)
	frames_pd.to_csv(os.path.join(DIR_RESULTS, 'rm_data.csv'), sep=';', decimal=',', float_format='%.3f')

	# make scatter plot
	scatter_plots = [
					 ("wcrt [ms]", "rm [ms]", "wcrt_rm.pdf"),	
					 ("slack [ms]", "rm [ms]", "slack_rm.pdf"),					 	
					 ("wcrt [ms]", "rm/slack", "wcrt_rm_norm.pdf"), 
					 ("slack [ms]", "rm/slack", "slack_rm_norm.pdf"),
					 ("norm_slack", "rm/slack", "norm_slack_rm.pdf"),
					 ("norm_slack", "rm [ms]", "norm_slack_norm_rm.pdf")					 					 
					 ]
	
 
	for (x,y,name) in scatter_plots:
		scatter_plot = sns.relplot(x=x, 
								y=y, 
								data=frames_pd, 
								hue = 'period [ms]',
								legend='full',
								palette = 'Spectral');
		scatter_plot.savefig(os.path.join(DIR_RESULTS, name))	


def select_systems():
	pass

def modify_e2e_deadlines():
	pass
	
			
if __name__ == '__main__':
	
	print('Evaluation of robustness margins starts.')
	io.PrintOuts.doubleline()
	
	select_systems()
	
	modify_e2e_deadlines()
	
	# Create target Directory if don't exist
	if not os.path.exists(DIR_RESULTS):
		os.mkdir(DIR_RESULTS)
	else:
		print('Removing generated files from results folder ' + DIR_RESULTS)
		files = glob.glob(DIR_RESULTS + '/*')
		for f in files:
		    print(f)
		    os.remove(f)
	io.PrintOuts.line()
	
	eval(path = DIR_SYSTEMS)
	
	io.PrintOuts.newline()
	io.PrintOuts.doubleline()
	print('Finished.')	
	
	
	
	
	
	