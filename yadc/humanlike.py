import numpy as np
from time import sleep
from logging import getLogger
import logging

logger = getLogger(__name__)
logger.setLevel(logging.DEBUG)


def randsleep(target: int, max_: int = None):
    """Sleep for a random length of time around target but less than max.

    We use a poisson distribution, since that models human action a bit better
    than a linear.
    """
    max_ = max_ or target * 10
    multiplier = 1
    while target < 100:
        multiplier *= 10
        target *= 10
        max_ *= 10
    duration = min(np.random.poisson(target), max_)
    logger.debug(f"Sleeping for {duration/multiplier} s")
    print(f"Sleeping for {duration/multiplier} s")
    print(duration, multiplier, target, target / multiplier, duration / multiplier)
    sleep(duration / multiplier)