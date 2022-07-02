import pyximport
pyximport.install()

from algotrader import historical_data
from algotrader import constants
import datetime
import matplotlib.pyplot as plt
import numpy
import scipy.stats
import random

def outputGapVSDayChange():
    historicals = historical_data.HistoricalPrices()
    allGapPrevious = []
    allGapNext = []
    allDayChanges = []
    today = datetime.datetime.now()
    for symbol in constants.symbolsToTrade:
        datapoints = historicals.getProcessedTimeSeries(symbol, today, 250)

        allGapPrevious.extend(d.gapPrevious for d in datapoints if d.gapPrevious is not None and d.dayChange is not None and d.gapNext is not None)
        allGapNext.extend(d.gapNext for d in datapoints if d.gapPrevious is not None and d.dayChange is not None and d.gapNext is not None)
        allDayChanges.extend(d.dayChange for d in datapoints if d.gapPrevious is not None and d.dayChange is not None and d.gapNext is not None)

    correlation = scipy.stats.pearsonr(allGapPrevious, allDayChanges)
    print(correlation)
    correlation = scipy.stats.pearsonr(allGapPrevious, allGapNext)
    print(correlation)
    correlation = scipy.stats.pearsonr(allDayChanges, allGapNext)
    print(correlation)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim([0.9, 1.1])
    ax.set_ylim([0.9, 1.1])
    ax.scatter(allGapPrevious, allDayChanges)
    plt.savefig("gap-vs-day.png")
    plt.show()


if __name__ == "__main__":
    outputGapVSDayChange()

