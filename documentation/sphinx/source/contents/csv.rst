Input Data: CSV files
================================

Input File 'resources.csv'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``resources.csv`` file describes the execution platform of the system by listing the different resources 
(CPUs, CAN bus etc.) and the scheduling policy that is applied on each resource. 
Currently static priority preemptive and static priority non-preemptive scheduling is supported.
The ``resources.csv`` file should have for each resource the following entries:

* | **[name]** Type: String 
  | Each computing core and each data bus, on which at least one chain task is executed, is represented by a so-called resource. This field specifies the name of the resource.
  
* | **[scheduler]** Type: String  
  | e.g., ``SPPScheduler`` or ``SPNPScheduler``



Input File 'tasks.csv'
^^^^^^^^^^^^^^^^^^^^^^
The ``tasks.csv`` file specifies tasks that are executed on the platform, it should have for each task the following entries:

* | **[task_name]** Type: String   
  | Unique task ID
  
* | **[period]** Type: Integer   
  | Activation period	
			
* | **[offset]** Type: Integer   
  | Release offset
		
* | **[priority]** Type: Integer   
  | Note that 0 is the highest priority.
		
* | **[wcet]** Type: Integer   
  | Worst Case Execution Time		
		
* | **[resource]** Type: String   
  | Resource that services the task. 
    The name should match a resource from file ``resources.csv``.
		
* | **[bcrt]** Type: Integer   
  | Best Case Response Time		
		
* | **[wcrt]** Type: Integer   
  | Worst Case Response Time
		
* | **[let]** Typ: Integer   
  | Logical Execution Time 


Input File 'chains.csv'
^^^^^^^^^^^^^^^^^^^^^^^^
The ``chains.csv`` file specifies which tasks are part of each cause-effect chain; 
it should have for each chain the following entries:


* | **[chain_name]** Type: String  
  | Unique cause-effect chain ID

* | **[e2e\_deadline]** Type: Integer 
  | End-to-end deadline 	
  	
* | **[members]** Type: String 
  | The member tasks must be listed in correct order and the task names must match those in the task definitions. The list of member tasks comprises as many cells in a row as needed.
