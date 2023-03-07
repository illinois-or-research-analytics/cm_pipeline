# pylint: disable=missing-docstring
import os
import multiprocessing as mp
import random
import functools
import time

SPLIT_PROB = 0.1


def print_msg(print_lock, msg):
    print_lock.acquire()
    print(msg)
    print_lock.release()


def task(queue, print_lock):
    msg = functools.partial(print_msg, print_lock)
    my_pid = os.getpid()
    msg(f'Hi, I\'m process {my_pid}')
    while True:
        msg(f'I\'m pid {my_pid}, waiting for a task')
        try:
            item = queue.get()
        except EOFError:  # The queue has been closed.
            break
        msg(f'pid {my_pid}, got item {item}')
        time.sleep(0.1)
        if random.random() < SPLIT_PROB:
            queue.put((my_pid, item[1] + 1))
        queue.task_done()


def main():
    num_workers = 10
    num_initial_tasks = 20

    print_lock = mp.Lock()
    queue = mp.JoinableQueue()

    # Populate the queue with initial tasks.
    parent_pid = os.getpid()
    for k in range(num_initial_tasks):
        queue.put((parent_pid, k))

    workers = []
    for _ in range(num_workers):
        worker = mp.Process(target=task, args=(queue, print_lock))
        workers.append(worker)

    for worker in workers:
        worker.start()

    queue.join()

    for worker in workers:
        worker.terminate()


if __name__ == '__main__':
    main()
