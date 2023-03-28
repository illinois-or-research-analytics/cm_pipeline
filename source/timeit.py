"""
Reference: https://dev.to/kcdchennai/python-decorator-to-measure-execution-time-54hk
This is a decorator to calculate the execution time of any function
"""

from functools import wraps
import logging
import time

logger = logging.getLogger(__name__)

STAGE_KEY = "Stage"
TIME_TAKEN_KEY = "Time (HH:MM:SS)"
execution_info = {
    STAGE_KEY: [],
    TIME_TAKEN_KEY: []
    }


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        convert_h_m_s = time.strftime("%H:%M:%S", time.gmtime(total_time))
        function_name = f'{func.__name__}{args}{kwargs}'
        time_taken = f'{convert_h_m_s}'
        execution_info[STAGE_KEY].append(function_name)
        execution_info[TIME_TAKEN_KEY].append(time_taken)
        message = f'{function_name} Took (HH:MM:SS) {time_taken}'
        logger.info(message)
        return result

    return timeit_wrapper
