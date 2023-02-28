from argparse import ArgumentParser
from source.workflow import Workflow
import configparser
from datetime import datetime
import logging
import logging.config
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG = os.path.join(ROOT_DIR, 'log.config')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')


def setup_logger():

    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S")
    log_file_name = os.path.join(LOG_DIR, f"cm_pipeline_{timestamp}.log")

    logging.config.fileConfig(
        LOG_CONFIG,
        disable_existing_loggers=False,
        defaults={"logfilename": log_file_name},
        )
    return log_file_name


if __name__ == "__main__":
    log_file = setup_logger()

    logger = logging.getLogger(__name__)

    parser = ArgumentParser(
        prog='cm_pp',
        description='Test the CM pipeline with test dataset'
        )
    parser.add_argument(
        'param_config', help='Config file with CM pipeline parameters'
        )
    args = parser.parse_args()

    # Read the contents of Config file
    config = configparser.ConfigParser()
    config.read(args.param_config)

    logger.debug("Program started")
    try:
        cm_workflow = Workflow(config)
        cm_workflow.start()
        cm_workflow.generate_analysis_report()
        logger.debug("Program finished")
        # Copy the log file and executed-cmds file to the target folder
        shutil.copy(log_file, cm_workflow.default_config.output_dir)
        shutil.copy(
            cm_workflow.cmd_obj.executed_cmds_text,
            cm_workflow.default_config.output_dir
            )
    except Exception as e:
        error_message = "An error occurred in the CM Workflow"
        logger.exception(error_message + ": %s", e)
