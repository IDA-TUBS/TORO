# TORO

**TORO** (Analysis **TO**ol to evaluate the latencies and **RO**bustness of cause-effect chains) can be used to determine end-to-end latencies as well perform robustness analyses on cause-effect chains.

For calculating of cause-effect chains comprised of BET or LET tasks a data propagation graph is the foundation of the analysis that was proposed by Becker et al. [1,2].

Köhler et al. [3] extended the latency analysis to also support task offsets and based up on the graph-based latency analysis added an additional robustness robustness analysis on top. Furthermore [3] contains principle ideas used for processing heterogeneous cause-effect chains by decomposing such chains into chains that can be analysed. This decomposition has been implemented in TORO and been extended to also determine deadlines for decomposed "subchains".

As part of [4] the existing TORO implementation has been rewritten to be implemented using open-source graph libraries (NetworkX and graph-tool) to improve comprehensibility and performance. In doing so the latency analysis has been  changed to work using a longest (shortest) path search to find the end-to-end path in the data propagation graph that leads to the worst-case latency that can be exhibited for a given cause-effect chain. The Bellman-Ford algorithm is used for this purpose.

As Input TORO accepts specifically constructed csv-files as well as Amalthea system models [[APP4MC](https://www.eclipse.org/app4mc/)]. The csv-files construction is outlined in the sphinx documentation while Amalthea system model prerequisites have been presented as part of [4] .



## Documentation

The code documentation can be built using [sphinx](https://www.sphinx-doc.org/en/master/):

Install [sphinx](https://www.sphinx-doc.org/en/master/usage/installation.html), [recommonmark](https://github.com/readthedocs/recommonmark) extension and the [RTD](https://sphinx-rtd-theme.readthedocs.io/en/stable/installing.html) theme prior to building the documentation.

```bash
$ cd documentation/sphinx
$ ./build_doc.sh
```

or manually:

```bash
$ cd documentation/sphinx

# only needed if new modules have been added to TORO
$ sphinx-apidoc -o source/code/ ../../TORO/libs/toro

# symbolic link to README
$ cd source/contents
$ ln -s ../../../../README.md
$ cd ../..

# always call make from /documentation/sphinx 
$ make html
```



## Requirements

A basic Python environment is required. On Linux installations Python should already be installed. If that's not the case check the internet for information on how to install Python for your current Linux distribution. The same goes for Windows.

The code is only verified to work with Python 3.6!

Later versions should also work but have not been verified to work properly.

**TORO** requires the following python packages:

- **argparse** [[docu](https://docs.python.org/3/library/argparse.html "argparse documentation")]

  creates user-friendly command-line interfaces

- **dill** [[link](https://pypi.org/project/dill/ "pypi dill project")]

  storing and accessing static data 

- **NetworkX** [[link](https://networkx.org/ "NetworkX website")]

  python graph library

- **graph-tool** [[link](https://graph-tool.skewed.de/ "graph-tool website")]

  python graph library

- **pyCPA** [[link](https://pycpa.readthedocs.io/en/latest/ "pyCPA website")]

  python graph library

- **Amalthea2PyCPA** [[link](https://git.ida.ing.tu-bs.de/kaige/Amalthea2PyCPA "project repository")]

  Amalthea Parser (optional, only needed if Amalthea system models shall be used for analysis in TORO)

  

Note: **argparse**, **dill** and **NetworkX** will be installed automatically when following the installation procedure outline beneath. **graph-tool**, **pyCPA** and **Amalthea2PyCPA** need to be manually installed by the user before starting the installation procedure.

## Installation

Clone tool's repository:

```bash
$ git clone https://git.ida.ing.tu-bs.de/TORO/Wirkketten_Tool.git
$ cd Wirkketten_Tool
```

For general usage:

```bash
$ pip install --user .
```

For development work:

```bash
$ pip install --user -e .
```

Note: make sure to install the tool using the right pip version if multiple Python versions (e.g. v.2.7 and 3.x) are installed on the system.



## Work Flow

**TORO** can be used by calling the main script *toro_main.py*: 

```bash
$ python3 toro_main.py -m <modelType>
```

The attribute behind **`-m`** is mandatory and defines the input data. So far *csv* and *amalthea* are supported.

Other options include:

- **`--disableWCRT`**: disables task WCRT calculation using pyCPA
- **`--disableLat`**: disable end-to-end latency calculations
- **`--disableRM`**: disable robustness analysis
- **`--plot`**: plot data propagation graphs
- **`--store`**: write results to csv files

As a reference for model and chain csv-descriptions check the examples in `TORO\data\csv`.



## Reuse of existing functions outside of TORO

Only exemplary code snippets listed that do not work as stand-alone code.

```python
from TORO.libs.toro import model
Task = model.extTask
Cec = model.extEffectChain 

from TORO.libs.toro import system_analysis
from TORO.libs.toro import chain_analysis
from TORO.libs.toro import model_parser

###############################################
#example 1 - system analysis (mutliple chains):
###############################################

system = None #create new or load existing (pycpa) system instead of None
chain = [None] #create new or load existing list of chains (extEffectChain) instead of None
args_tmp = system_analysis.argsDummy(lat=True, rm=True, wcrt=True, plot=False, test=False)

results = system_analysis.perform_analysis(args_tmp, system, chains)

###########################################
#example 2 - chain analysis (single chain):
###########################################

system = None #create new or load existing (pycpa) system instead of None
chain = None #create new or load existing chain (extEffectChain) instead of None

args_tmp = system_analysis.argsDummy(lat=True, rm=True, wcrt=True, plot=False, test=False)

# calculate miscellaneous attributes
task_results = system_analysis.calculate_wcrt(system)
lat, t_lat, rm, dlet, slack = system_analysis.analyse_chain(chain, previousChain=None, args=args_tmp)            
res = system_analysis.SystemAnalysisResults('system', {chain.name: lat}, rm, dlet, slack=slack, task_results=task_results, system=system)

print(res.toString())
res.toCSV()

#########################
#example 3 - other parts:
#########################

parser = model_parser.CSVParser(<arguments dict needed by CSVParser>)
res = system_analysis.SystemAnalysisResults('name', dict(), dict(), dict())
analysis = chain_analysis.analysis_LET_BET.ChainAnalysis(Cec('name'), dict())
#...
```



## Code Structure

See sphinx documentation



## Examples

See sphinx documentation



## Literature

[1] M. Becker, D. Dasari, S. Mubeen, M. Behnam, and T. Nolte, “**Synthesizing job-level dependencies for automotive multi-rate effect chains**”, in 2016 IEEE 22nd International Conference on Embedded and Real-Time Computing Systems and Applications (RTCSA), 2016,pp. 159–169.

[2] M.   Becker,   D.   Dasari,   S.   Mubeen,   M.   Behnam,   and   T.   Nolte,   “**End-to-end timing  analysis  of  cause-effect  chains  in  automotive  embedded  systems**”, Journal of  Systems  Architecture,   vol.  80,   pp.  104  –  113,   2017.  [[Online](http://www.sciencedirect.com/science/article/pii/S1383762117300681)]. 

[3] L. Köhler, P. Hertha, M. Beckert, A. Bendrick, R. Ernst, "**Robust Cause-Effect Chains with Bounded Execution Time and System-Level Logical Execution Time**"

[4] A. Bendrick, "**Optimisation and improvement of graph analysis in connection with the TORO tool**", Institute of Computer and Network Engineering, TU Braunschweig, Masterthesis, 2021. 

[5] R. Ernst,  L. Ahrendts,  and K.-B. Gemlau,  “**System Level LET:  Mastering cause-effect chains in distributed systems**”, in IECON 2018-44th Annual Conference of the IEEE Industrial Electronics Society.    IEEE, 2018, pp. 4084–4089.







## Changelog

| Author        | Description                                                  | Date          |
| ------------- | ------------------------------------------------------------ | ------------- |
| Alex Bendrick | Updated TORO tool that utilizes NetworkX or graph-tool as graph libraries for implementing the latency analysis (Becker) and was extended to also feature new input data format (Amalthea) as well as  theoretically support SL LET | early 2021    |
| Alex Bendrick | Ready for release, removed chain decomposition from master branch | December 2021 |
|               |                                                              |               |

