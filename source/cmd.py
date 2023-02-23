"""
References:
https://realpython.com/python-subprocess/#an-example-of-exception-handling
"""
import os
import subprocess
import logging
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


class Cmd(object):
    def __init__(self, default_config_obj):
        self.default_config = default_config_obj
        self.executed_cmds_folder = os.path.join(
            ROOT_DIR, '..', 'logs', 'executed-cmds'
            )
        os.makedirs(self.executed_cmds_folder, exist_ok=True)
        self.executed_cmds_text = os.path.join(
            self.executed_cmds_folder,
            f'ex_cmds-{self.default_config.timestamp}.txt'
            )

    def run(self, cmd_list, check_errors=True):
        try:
            cmd = ' '.join(cmd_list)
            logger.debug("Executing Command: %s", cmd)
            self.write_cmds_to_file(cmd)
            # Comment the below 2 lines for quick testing of workflow paths
            result = subprocess.run(
                cmd_list, check=check_errors, capture_output=True, text=True
                )
            logger.debug("Output: %s", result.stdout)
        except FileNotFoundError as exc:
            error_msg = f"Process failed because the executable " \
                        f"could not be found.\n{exc}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except subprocess.CalledProcessError as exc:
            error_msg = f"Process failed because did not return a " \
                        f"successful return code. \
                        Returned {exc.returncode}\n{exc.output}"
            logger.error(error_msg)
            raise subprocess.CalledProcessError(cmd_list, error_msg)

    def write_cmds_to_file(self, cmd):
        with open(self.executed_cmds_text, 'a+') as fp:
            cmd_pl_h1 = cmd.replace(
                self.default_config.output_dir, '/placeholder1'
                )
            cmd_pl_h2 = cmd_pl_h1.replace(
                self.default_config.root_output_dir, '/placeholder2'
                )
            fp.write(cmd_pl_h2)
            fp.write("\n\n")

    def write_placeholder(self):
        with open(self.executed_cmds_text, 'a+') as fp:
            fp.write(f"placeholder1: {self.default_config.output_dir}")
            fp.write("\n\n")
            fp.write(f"placeholder2: {self.default_config.root_output_dir}")
