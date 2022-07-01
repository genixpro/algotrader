import pyximport
pyximport.install(pyimport=True)

import analyzer
import cProfile
import pstats
from pstats import SortKey
import constants
import historical_data

def run():
    analyzer.optimizeNumberOfHistoricalDays()

    # cProfile.run('analyzer.optimizeNumberOfHistoricalDays()', 'restats')
    # p = pstats.Stats('restats')
    # p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()
    # p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_callers()



if __name__ == '__main__':
    run()
