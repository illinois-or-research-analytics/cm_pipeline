import multiprocessing as mp
from os import getpid

def par_task(x):
    return {getpid(): getpid()*k}

def main():
    global k
    k = 3
    with mp.Pool(5) as p:
        out = p.map(par_task, [{}, {}, {}])
    print(out)

if __name__ == '__main__':
    main()