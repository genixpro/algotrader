import analyzer
import cProfile
import pstats
from pstats import SortKey

def run():
    # for symbol in constants.symbolsToTrade:
    #     historicals = historicaldata.HistoricalPrices()
    #     historicals.saveRawDataLocally(symbol)
    analyzer.analyzeSymbolOptions()
    # analyzer.optimizeNumberOfHistoricalDays()

    # cProfile.run('analyzer.optimizeNumberOfHistoricalDays()', 'restats')
    # p = pstats.Stats('restats')
    # p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()
    # p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_callers()



if __name__ == '__main__':
    run()
