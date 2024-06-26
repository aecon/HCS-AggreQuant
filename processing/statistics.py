import os
import sys
import glob

from utils import printer as p
from utils.dataset import Dataset
from utils import printer as p
from statistics.statistics import *


me = "statistics.py"


def statistics(dataset, verbose, debug):

    if dataset.type_of_run == "production":
        statistics = Statistics(dataset, verbose, debug)
        statistics.generate_statistics()

    else:
        p.msg("Statistics are not computed in a validation run.", me)

