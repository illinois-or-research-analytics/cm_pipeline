"""
References:
https://realpython.com/python-subprocess/#an-example-of-exception-handling
"""
import subprocess
import logging

logger = logging.getLogger(__name__)

def run(cmd_list, check_errors= True):
    try:
        logger.info(f"Executing {' '.join(cmd_list)}")
        subprocess.run(cmd_list, check=check_errors)
        
    except FileNotFoundError as exc:
        error_msg = f"Process failed because the executable could not be found.\n{exc}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    except subprocess.CalledProcessError as exc:
        error_msg = f"Process failed because did not return a successful return code. \
                        Returned {exc.returncode}\n{exc}"
        logger.error(error_msg)
        raise subprocess.CalledProcessError(cmd_list,error_msg)

