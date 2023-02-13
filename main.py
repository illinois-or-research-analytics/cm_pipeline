from argparse import ArgumentParser
from source.workflow import Workflow
import configparser
import logging
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) 
LOG_FILE = os.path.join(ROOT_DIR, 'cm_pipeline.log')

def setup_logger(log_file):
    #instantiate root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(LOG_FILE)

    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger
    
if __name__ == "__main__":
    setup_logger(LOG_FILE)

    logger = logging.getLogger(__name__)
    
    parser = ArgumentParser(
                    prog = 'cm_pp',
                    description = 'Test the CM pipeline with test dataset')
    parser.add_argument('param_config', help='Config file with CM pipeline parameters')
    args = parser.parse_args()

    # Read the contents of Config file
    config = configparser.ConfigParser()
    config.read(args.param_config)

    logger.debug("Program started")
    try:
        cm_workflow = Workflow(config)
        cm_workflow.run()
        logger.debug("Program finished")
    except Exception as e:
        error_message="An error occured in the CM Workflow"
        logger.exception(error_message + ": %s", e)