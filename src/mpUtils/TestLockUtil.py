#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import time
from threading import Thread

import LockUtil # Local module

GDICT = dict() # Globally shared resource

@LockUtil.locker
def shingle():
    key = len(GDICT)
    print('shingle', key, GDICT)
    GDICT[2] = GDICT.get(2, 0) - 1
    return GDICT

@LockUtil.locker
def phingle():
    key = len(GDICT)
    print('phingle', key, GDICT)
    GDICT[2] = GDICT.get(2, 0) + 2
    return GDICT

@LockUtil.retryable
def retrier(func, *args, **kwargs):
    results = func(*args, **kwargs)
    return results

def main():
    for i in range(40):
        if i & 1:
            func = shingle
        else:
            func = phingle

        runnable = Thread(target=retrier, args=(func,))
        runnable.start()

    counter = 0
    while counter < 20:
        time.sleep(1)
        counter = GDICT.get(2, 0)
        # print('Refresh', m)

if __name__ == '__main__':
    main()
