# pylint: disable=missing-docstring
import os
import multiprocessing as mp
import random
import functools
import time

SPLIT_PROB = 0.1


def print_msg_with_lock(print_lock, msg):
    print_lock.acquire()
    print(msg)
    print_lock.release()


def task(queue, print_lock):
    print_msg = functools.partial(print_msg_with_lock, print_lock)
    my_pid = os.getpid()
    print_msg(f'Hi, I\'m process {my_pid}, ready to work')
    while True:
        print_msg(f'I\'m pid {my_pid}, waiting for a task')
        item = queue.get()
        if item is None:
            print_msg(f'I\'m pid {my_pid}, I have been set free!')
            queue.task_done()
            break
        print_msg(f'I\'m pid {my_pid}, got item {item}')
        time.sleep(0.1)
        if random.random() < SPLIT_PROB:
            queue.put((my_pid, item[1] + 1))
        queue.task_done()


def main():
    num_workers = 10
    num_initial_tasks = 20

    print_lock = mp.Lock()
    queue = mp.JoinableQueue()

    # Create and start the workers.
    workers = []
    for _ in range(num_workers):
        worker = mp.Process(target=task, args=(queue, print_lock))
        workers.append(worker)

    for worker in workers:
        worker.start()

    # Populate the queue with initial tasks.
    parent_pid = os.getpid()
    for k in range(num_initial_tasks):
        queue.put((parent_pid, k))

    # Wait for all tasks to be completed.
    queue.join()

    # Place dummy tasks to signal that all work has been completed.
    # Each worker will receive one dummy task to be set free.
    for _ in range(len(workers)):
        queue.put(None)

    # Wait for all workers to be free.
    queue.join()

    # Close all workers.
    for worker in workers:
        worker.join()


if __name__ == '__main__':
    main()
