# cm_pipeline
Modular pipeline for testing and using an improved version of CM for generating well-connected clusters.

## Overview 
![cm_pipeline Overview](figures/cm_pp_overview.png)

## Input
- The input to the pipeline script is a [param.config](param.config) file.
- Description of the supported key-value pairs in the config file can be found here [param_template.config](param_template.config) 

## Requirements [WIP]
- Create a python venv with necessary packages (runleiden, [CM](https://www.notion.so/Lab-Journal-2fcb00b0f77543fa932ff3cec650125f))
- `cmake` version `3.2.0` and above should be installed.
- `python39-devel` or higher should be installed
- `openmpi` and `gcc` of any version
     - In our analysis, `openmpi 4.2.0` and `gcc 9.2.0` were used.
### EngrIT Systems
- You can get all the needed packages to run the pipeline via the following commands
```bash
module load python3/3.10.0
module load cmake/3.25.1
module load openmpi/4.0.1
module load gcc/9.2.0
```

## Setup and Running Instructions
- Clone the cm_pipeline repository
- Activate the venv which has the necessary packages 
- Set up `python-mincut`:
     - Initiate the submodules via the following commands being run from the root of this repository
     ```bash
     git submodule update --init --recursive
     cd hm01/tools/python-mincut
     mkdir build
     cd build
     cmake .. && make
     cd ../../../..
     ```
- Edit the `network_name`, `output_dir`  and `resolution` values in `[default]` section of [param.config](param.config); and `input_file` under `[cleanup]` section of the cloned repository (‘~’ is allowed for user home in the `output_dir` path and this directory need not exist)
- Run `python -m main param.config`

## Setting the levels for logging
- cm pipeline logs the data on to console and file.
- Log levels for each of these can be modified in [log.config](./log.config)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL [logging levels](https://docs.python.org/3/library/logging.html#logging-levels)
- Log files are created in `./logs` directory.

## Output Files [WIP]
- The commands executed during the workflow are captured in `./logs/executed-cmds/executed-cmds-timestamp.txt`
- The Output files generated during the workflow are stored in the folder `user-defined-output-dir/network_name-cm-pp-output-timestamp/`
- The descriptive analysis files can be found in the folder `user-defined-output-dir/network_name-cm-pp-output-timestamp/analysis` with the `*.csv` file for each of the resolution values.

## Note:
- At present the new version of `CM` is by default executed in quiet mode. If you want to run it in verbose mode then 
comment out the [--quiet](https://github.com/illinois-or-research-analytics/cm_pipeline/blob/main/source/connectivity_modifier_new.py#:~:text=cm.py%22%2C-,%22%2D%2Dquiet%22%2C,-%22%2Di%22%2C) argument in [source/connectivity_modifier_new.py](source/connectivity_modifier_new.py). Better still, request the ability to turn it on and off easily.

## References
- [https://engineeringfordatascience.com/posts/python_logging/](https://engineeringfordatascience.com/posts/python_logging/)
- [https://docs.python.org/3/library/logging.config.html#logging-config-fileformat](https://docs.python.org/3/library/logging.config.html#logging-config-fileformat)

## TODOs:
- Support to run the workflow with individual stages (as opposed to "end to end")
- Integrate `leiden_alg` script by GC. [DONE]
- Add edge_coverage in the analysis file for `*treestar_counts.tsv`
- Add fraction of clusters untouched by the central CM module of pipeline in the analysis file.
- Copy the log file to `user-defined-output-dir/network_name-cm-pp-output-timestamp/` at the end of the pipeline. [DONE]
- Mechanism to sync the scripts used within cm_pipeline with the latest changes.
- Add more log messages in the source code for different levels (Currently INFO, DEBUG, ERROR log messages are added). 

