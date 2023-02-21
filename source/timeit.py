"""
Reference: https://dev.to/kcdchennai/python-decorator-to-measure-execution-time-54hk
This is a decorator to calculate the execution time of any function
"""

from functools import wraps
import logging
import time

logger = logging.getLogger(__name__)


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(
            f'Function {func.__name__}{args}{kwargs} '
            f'Took {total_time:.4f} seconds'
            )
        return result

    return timeit_wrapper
