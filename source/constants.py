"""
This file has the list of all strings used in the param.config file to be used in the 
code.
"""

# Section names
DEFAULT = 'default'
CLEANUP_SECTION = 'cleanup'
CLUSTERING_SECTION = 'clustering'
FILTERING_BF_CM_SECTION = 'filtering_bf_cm'
CONNECTIVITY_MODIFIER_SECTION = 'connectivity_modifier'
FILTERING_AF_CM_SECTION = 'filtering_af_cm'
STATS_AF_FILTERING = 'stats_af_filtering'


# Keys used in param.config
NETWORK_NAME_KEY = 'network_name'
INPUT_FILE_KEY = 'input_file'
OUTPUT_DIR_KEY = 'output_dir'
ALGORITHM_KEY = 'algorithm'
RESOLUTION_KEY = 'resolution'
CLEANED_INPUT_FILE_KEY = 'cleaned_input_file'
INPUT_CLUSTERING_FILE_DIR_KEY = 'input_clustering_file_dir'
INPUT_CM_READY_FILE_DIR_KEY = 'input_cm_ready_file_dir'
INPUT_CM_FILE_DIR_KEY = 'input_cm_file_dir'
CLEANUP_SCRIPT_KEY = 'cleanup_script'
CLUSTERING_SCRIPT_KEY = 'clustering_script'
FILTERING_SCRIPT_KEY = 'filtering_script'
CM_READY_SCRIPT_KEY = 'cm_ready_script'
CM_VERSION_KEY = 'cm_version'
CLUSTERING_FILE_KEY = 'clustering_file'
OUTPUT_FILE_TAG_KEY = 'output_file_tag'
THRESHOLD_KEY = 'threshold'
CM_VERSION_NEW_VAL = 'new'
CM_VERSION_OLD_VAL = 'old'
RUNLEIDEN_SCRIPT_VALUE = 'runleiden'
LEIDEN_ALG_SCRIPT_VALUE = 'leidenalg'
NUMBER_OF_ITERATIONS_KEY = 'number_of_iterations'
# below config keys are used only for new version of CM
NPROCS = 'nprocs'
LABELONLY = 'labelonly'
QUIET = 'quiet'

EXISTING_OP_JSON = 'existing_op_json'
# KEYS used in existing_ip_files.json
CLEANED_NW_KEY = 'cleaned_nw'
CLUSTERED_NW_FILES = 'clustered_nw_files'
CM_READY_FILES = "cm_ready_files"
DOUBLE_HYP = "--"
SINGLE_HYP = "-"

# Stats script
STATS_SCRIPT = "stats_script"