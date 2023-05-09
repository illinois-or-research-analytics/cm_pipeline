# CM Benchmark Tests
This is an instruction manual to run, interpret the CM benchmark results.
## Versions of CM
We tested three versions of CM on odesa Platform
| Version | Description |
| ------ | ------ |
| cm | original connectivity modifier |
| cm+ | quiet mode and python mincut wrapper |
| cm++ | parallel processing |

## odesa platform specification
CM benchmark tests were run on `odesa` with the following specifications:
```
Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
Byte Order:          Little Endian
CPU(s):              96
On-line CPU(s) list: 0-95
Thread(s) per core:  2
Core(s) per socket:  48
Socket(s):           1
NUMA node(s):        1
Vendor ID:           AuthenticAMD
CPU family:          25
Model:               1
Model name:          AMD EPYC 7J13 64-Core Processor
Stepping:            1
CPU MHz:             2445.352
BogoMIPS:            4890.70
Virtualization:      AMD-V
Hypervisor vendor:   KVM
Virtualization type: full
L1d cache:           64K
L1i cache:           64K
L2 cache:            512K
L3 cache:            16384K
NUMA node0 CPU(s):   0-95
```
## Input Networks
We ran the benchmark tests on 3 networks
| Network | Description |Nodes|Edges|
| ------ | ------ | ------ |------ |
| cit | cit patents |3774768|16518947|
| cen | exosome data |13989436|92051051|
| oc | open citations data |75 million|1.4 billion|

## Tools

To run the benchmark tests we used the following tools:
- [CM pipeline](https://github.com/illinois-or-research-analytics/cm_pipeline) - A modular pipeline for testing and using an improved version of CM for generating well-connected clusters.
- [multitime](https://tratt.net/laurie/src/multitime/) - To capture the walltime, cpu time and memory usage across multiple runs of the test. 
As mentioned by the author "multitime, in essence, a simple extension to time which runs a command multiple times and prints the timing means, standard deviations, mins, medians, and maxes having done so. This can give a much better understanding of the command's performance."

## Installation and Test Environment setup 
To use the CM pipeline for different versions of CM clone the specific tags using the below commands.

> NOTE: `cm+` benchmark tests were executed with the source code at commit id `3c74541d4f6a48c52ee810a723893651ad813862`. Improvements on the `cm_pipeline` were made to support the execution of different stages of the pipeline using the existing clusterings. This included the `v2.1` changes of the connectivity modifier.
## Cloning the repository
1. To clone the latest version of `cm_pipeline` 
    ```
    git clone https://github.com/illinois-or-research-analytics/cm_pipeline.git
    ```
2. To create a new local branch and checkout a specific tag
    1. Fetch all the tags from remote
        ```
         git fetch --all --tags
        ```
    2. To list all the tags
        ```
        git tag 
        ```
    3. To checkout 
        ```
        git checkout -b version2_1 v2.1
        ```
3. To create a new branch and checkout a specific commit id
    ```
    git checkout -b new_branch 3c74541d
    ```

## Creating a venv
1. The benchamrk tests for `cm ` were run using the `connectivity-modifier==0.1.0b13` package. A virtual environment with below requirements was created for `cm` tests.
2. We used `Python 3.9.13` version to create the venv.
3. Copy the below package list into a file named `requirements.txt`
    ```
    attrs==22.2.0
    click==8.1.3
    colorama==0.4.6
    coloredlogs==15.0.1
    connectivity-modifier==0.1.0b13
    exceptiongroup==1.1.1
    graphviz==0.20.1
    HeapDict==1.0.1
    humanfriendly==10.0
    igraph==0.10.4
    iniconfig==2.0.0
    jsonpickle==2.2.0
    leidenalg==0.9.1
    networkit==10.1
    numpy==1.24.2
    packaging==23.0
    pandas==1.5.3
    pip==20.2.4
    pluggy==1.0.0
    pytest==7.2.2
    python-dateutil==2.8.2
    pytz==2023.2
    scipy==1.10.1
    setuptools==50.3.2
    six==1.16.0
    structlog==22.3.0
    texttable==1.6.7
    tomli==2.0.1
    treeswift==1.1.33
    typer==0.6.1
    typing-extensions==4.5.0
    ```
4. Run the below commands to create and activate the venv
    ```
    python3.9 -m venv cm_venv
    source ./cm_venv/bin/activate
    pip install -r requirements.txt
    ```
5. To create venv for `cm+` and `cm++` benchmark tests, follow the above steps but use the below requirements
    ```
    attrs==22.2.0
    click==8.1.3
    colorama==0.4.6
    coloredlogs==15.0.1
    exceptiongroup==1.1.1
    graphviz==0.20.1
    HeapDict==1.0.1
    humanfriendly==10.0
    igraph==0.10.4
    iniconfig==2.0.0
    jsonpickle==2.2.0
    leidenalg==0.9.1
    networkit==10.1
    numpy==1.24.2
    packaging==23.0
    pandas==1.5.3
    pip==20.2.4
    pluggy==1.0.0
    pytest==7.2.2
    python-dateutil==2.8.2
    pytz==2023.2
    scipy==1.10.1
    setuptools==50.3.2
    six==1.16.0
    structlog==22.3.0
    texttable==1.6.7
    tomli==2.0.1
    treeswift==1.1.33
    typer==0.6.1
    typing-extensions==4.5.0
    ```
## Running the benchmark tests
1. Change the working directory to the `cm_pipeline` repository. 
2. Activate the venv (corresponding to cm/cm+/cm++)
3. Prepare the config file for the cm_pipeline (Refer the FAQ section below)
4. Run the below command with the correct config file and nohup.out file
    ```
    nohup multitime -n 3 -f rusage ./run.sh /data3/vidya_d3/cm_benchmark/configs/oc_cm++_nproc2_tl_3r_cm_stage.config &>/data3/vidya_d3/cm_benchmark/nohup_res/oc_cm++_nproc2_tl_3r_cm_stage_nohup.out&
    ```
5. Example:
    ```
      cd /data3/vidya_d1/repos/cm++/
      source /data3/vidya_d1/venvs/cm_pp_2.1/bin/activate
      nohup multitime -n 3 -f rusage ./run.sh /data3/vidya_d3/cm_benchmark/configs/oc_cm++_nproc2_tl_3r_cm_stage.config &>/data3/vidya_d3/cm_benchmark/nohup_res/oc_cm++_nproc2_tl_3r_cm_stage_nohup_rep2.out&
    ```
> Note: For detailed test plan see the below excel sheet
> [cm_benchamrk_test_plan](https://docs.google.com/spreadsheets/d/1jHlygdK6iHFAQkwnX08yBL3uUYfy5rp5_6h6clo-aNs/edit?usp=sharing)
## Interpreting CM benchmark Results
CM benchmark results are located on valhalla and odesa in the below root directories:
| system | Root Directory |
| ------ | ------ | 
|odesa | `/data3/vidya_d3/cm_benchmark` |
|valhalla|`/shared/cm_benchmark`|

| Folder | Description |
| ------ | ------ | 
|cm | cm pipeline output for cm |
|cm+ | cm pipeline output for cm+ |
|cm++ |cm pipeline output for cm++|
|configs|config files used as an input to the pipeline to run the benchmark tests|
|jsons|json files used as an input to the pipeline to use the exisiting clusterings (skip cleanup, clustering stages)|
|multitime_res|csv files with multitime statistics across multiple runs of a test|
|nohup_res|nohup.out files with the console output|

> Note: The folder names in `cm`, `cm+`, `cm++` and the file names in `configs`, `multtime_res`, `nohup_res` folders have one of the below prefixes which is described below.

- For cm and cm+
`<network_name>_<cm_version>_<number_of_multitime_runs>_<stages_executed_in_cm_pipeline>`
- For cm++
`<network_name>_<cm_version>_nproc<number_of_processors>_<tl_OR_None>_<number_of_multitime_runs>_<stages_executed_in_cm_pipeline>`
`<network_name>_<cm_version>_nproc<number_of_processors>_<number_of_multitime_runs>_<stages_executed_in_cm_pipeline>`


> Note: Names inside `<>` are placeholders

| Placeholder | Values| Description |
| ------ | ------ | ------ |
|`<network_name>`| cit, cen, oc| indicates the input network name|
|`<cm_version>`|cm, cm+, cm++| version of cm used in the cm pipeline|
|`<number_of_processors>`| 2,4,6,8,16,32,64 ..| indicates the number of parallel processes used for cm stage. Applicable only for cm++|
|`<tl_OR_None>`|tl|tl indicates tree logging is enabled during the CM stage (cm2univeral)|
|`<number_of_multitime_runs>`|1r,2r, 3r ..|indicates the number of times the test was performed|
|`<stages_executed_in_cm_pipeline>`|cm_stage, all_stage| indicates the stages executed with the cm pipeline|

> Examples:
- `cit_cm++_nproc2_tl_3r_cm_stage.config` - config file used to run cm_pipeline with cm stage only on cit network using cm++ using 2 parallel processes with tree logging enabled.
- `cit_cm++_nproc2_3r_cm_stage.config` -  config file used to run cm_pipeline with cm stage only on cit network using cm++ using 2 parallel processes with tree logging disabled.
- `cit_cm++_nproc2_tl_3r_cm_stage_multitime.csv` - multitime results for 3 runs of cm_pipeline rexecuted with cm stage only on cit network using cm++ using 2 parallel processes with tree logging enabled.

## FAQs 
#### Example config file with all stages
Refer `cen_cm+_1r_all_stage.config`
```
[default]
network_name = cen 
output_dir = /data3/vidya_d3/cm_benchmark/cm+
algorithm = leiden
resolution = 0.5,0.01,0.0001
number_of_iterations = 2
cm_version = new

[cleanup]
cleanup_script =./scripts/cleanup_el.R
input_file = /data3/vidya_d1/no_head_exosome_14m_retraction_depleted_jc250_corrected_edgelist.csv

[clustering]
clustering_script = leidenalg

[filtering_bf_cm]
filtering_script=./scripts/subset_graph_nonetworkit_treestar.R
cm_ready_script =./scripts/make_cm_ready.R

[connectivity_modifier]
threshold = 1log10

[filtering_af_cm]
filtering_script=./scripts/post_cm_filter.R
```

##### How to choose between different versions of cm in the config file?
1. To run the cm pipeline with the legacy `cm` set `cm_version = old` and to run `cm+` or `cm++` set `cm_version = new` in the default section of config file. Refer the example config file: `cen_cm_1r_all_stage.config` 
    ```
    [default]
    network_name = cen 
    output_dir = /data3/vidya_d3/cm_benchmark/cm
    algorithm = leiden
    resolution = 0.5,0.01,0.0001
    number_of_iterations = 2
    cm_version = old
    ```
##### How to run CM pipleine with existing clusterings?
Refer the example config file: `cen_cm+_3r_filter_cm_stage_filter.config`
1. Create copy of the example config file
2. Modify the value for the key `network_name` and `existing_op_json`.

Refer the example existing_op_files.json: `cen_existing_clusters.json`
1. Create copy of the example json file
2. Modify the values for the key `clustered_nw_files` by adding the complete file paths that point to the existing clustering files.

##### How to run CM pipeline with existing clusterings filterd for N>10 ?
Refer the example config file: `cen_cm+_3r_cm_stage.config`
1. Create copy of the example config file
2. Modify the value for the key `network_name` and `existing_op_json`.

Refer the example existing_op_files.json: `cen_existing_op.json`
1. Create a copy of the example json file
2. Modify the values for the key `cm_ready_files` by adding the complete file paths that point to the existing files that contain clusters filtered for tree, star and N>10.

##### How to choose different number of processes for cm++?
Add the `nprocs` in the config file under the `connectivity_modifier` section. If this key is not added then by default 4 processes will be used. Seting `nprocs` to 1 is same as running `cm+`.
```
[connectivity_modifier]
threshold = 1log10
nprocs = 4
```
example config file: `cen_cm++_nproc4_tl_3r_cm_stage.config `
##### How to use quiet mode in cm++?
Set `quiet=1` in the config file under the `connectivity_modifier` section. If this key is not added then by default quiet mode is enabled. Set `quiet=0` to enable the console logging of connectivity modifier.
```
[connectivity_modifier]
threshold = 1log10
nprocs = 4
quiet = 1
```
example config file `cen_cm++_nproc4_tl_3r_cm_stage.config`
##### How to enable tree logging (run cm2universal) in cm++?
Set the `labelonly=0` in the config file under the `connectivity_modifier` section. If this key is not added then by default, the tree logging is disabled (labelonly=1)
```
[connectivity_modifier]
threshold = 1log10
nprocs = 4
quiet = 1
labelonly = 0
```
example config file `cen_cm++_nproc4_tl_3r_cm_stage.config`
