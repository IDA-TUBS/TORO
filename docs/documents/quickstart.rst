Quickstart
================================
This section gives an overview how to use the tool TORO.


Installation
------------
This section explains how to install the tool TORO. 

* Install a Python Interpreter (version 3). 
  You may want to install a distribution, e.g., Python(x,y), which already 
  contains many useful packages.

* The tool TORO will be delivered in a folder ``toro_project``. 
  This folder has the following content: 
	* **Main script** ``toro_main.py``
	* The libraries **pycpa** and  **toro** in the folder ``./libs``. 
	  The libraries under ``./libs`` are dynamically included and do not need 
	  to be installed unless you want to change their location. 
	* **Input folder** ``data``. Systems to be analyzed can be stored here. 
	
* Save the folder ``toro_project`` to your preferred destination.


Use
---
* Open a terminal and change to the ``/toro_project`` folder.
* The tool TORO is called via the script ``toro_main.py``. 
 




Command Line Switches
^^^^^^^^^^^^^^^^^^^^^^
* ``--path``: 
  A path is passed to the script as an argument to specify the location of 
  the systems to be analyzed. 
  It is recommended to store the system in the provided ``data`` folder. 
  If several systems are to be analyzed, a subfolder can be created in ``data`` 
  for each system to be analyzed. the folder structure is illustrated below.
  
  .. figure:: ../figures/folder_structure.jpg
    :width: 400px
    :align: center
    :alt: alternate text
    :figclass: align-center
  
  
* ``--wcrt``: 
  This options causes that *only* WCRTs for tasks are computed and written to 
  ``data/system1/wcrt_results.csv``. 


* An exemplary call of the tool would then look as follows:
  ::
  
	user@computer:~/toro_project$ python toro_main.py --path ./data 
	




Input Files
------------
This section explains how to specify systems that the tool TORO should analyze.
Firstly, TORO calls the method ``get_system_dirs(dir)`` and searches in the specified
path for systems to be analyzed. Each individual system should be encapsulated
in a dedicated folder as illustrated in the above figure. This system folder should contain three semicolon-separated csv-files, namely

* chains.csv,
* resources.csv,
* tasks.csv.