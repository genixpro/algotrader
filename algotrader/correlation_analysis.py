import pyximport
pyximport.install()

from algotrader import historical_data
from algotrader import constants
import datetime
import matplotlib.pyplot as plt
import numpy
import scipy.stats
import random
from pprint import pprint

def getNormalizedPriceTimeSeries(symbol, startDate, daysOfHistory, historicals):
    symbolDatapoints = historicals.getProcessedTimeSeries(symbol, startDate, daysOfHistory)
    changes = [
        d.gapPrevious * d.dayChange for d in symbolDatapoints if
        d.gapPrevious is not None and d.dayChange is not None
    ]
    currentValue = 1.0
    for n in range(len(changes)):
        currentValue = currentValue * changes[n]
        changes[n] = currentValue
    
    return changes

def getPriceDirectionalTimeSeries(symbol, startDate, daysOfHistory, historicals):
    movingAverageEpsilon = 1.0 / constants.correlationAnalysisMovingAveragePeriodDays

    symbolDatapoints = historicals.getProcessedTimeSeries(symbol, startDate, daysOfHistory)
    changes = [
        d.gapPrevious * d.dayChange for d in symbolDatapoints if
        d.gapPrevious is not None and d.dayChange is not None
    ]

    currentValue = changes[0]
    for n in range(len(changes)):
        currentValue = currentValue * (1.0 - movingAverageEpsilon) + changes[n] * movingAverageEpsilon
        changes[n] = currentValue

    # Now convert it into purely positive or negative
    for n in range(len(changes)):
        if changes[n] > 1:
            changes[n] = 1
        elif changes[n] < 1:
            changes[n] = -1
        else:
            changes[n] = 0

    return changes

def outputPriceChart(symbols, fileName):
    historicals = historical_data.HistoricalPrices()
    today = datetime.datetime.now()

    priceLists = [
        (symbol, getPriceDirectionalTimeSeries(symbol, today, 250, historicals))
        for symbol in symbols
    ]

    minLength = int(min(*[len(priceList[1]) for priceList in priceLists]))

    priceListsForComparison = []
    for symbol, priceList in priceLists:
        if len(priceList) > minLength:
            shortenedPriceList = priceList[-minLength:]
        else:
            shortenedPriceList = priceList

        priceListsForComparison.append((symbol, shortenedPriceList))

    fig, ax = plt.subplots(figsize=(12, 6))
    for symbol, priceList in priceListsForComparison:
        ax.plot(range(len(priceList)), priceList, label=symbol)
    ax.legend()
    # ax.set_ylim([0.99, 1.01])
    ax.axhline(0, color='black')

    plt.savefig(fileName)
    # plt.show()
    plt.close(fig)

def computeCrossCorrelationTable():
    historicals = historical_data.HistoricalPrices()
    today = datetime.datetime.now()
    allPairs = []
    correlationGrid = []
    correlationTable = {}
    for firstSymbol in constants.symbolsToTrade:
        firstPrices = getPriceDirectionalTimeSeries(firstSymbol, today, 250, historicals)

        symbolCorrelations = []
        symbolTable = {}

        for secondSymbol in constants.symbolsToTrade:
            # Skip correlating a symbol against itself
            if firstSymbol == secondSymbol:
                symbolCorrelations.append(1)
                continue
            secondPrices = getPriceDirectionalTimeSeries(secondSymbol, today, 250, historicals)

            if len(firstPrices) > len(secondPrices):
                firstPricesForComparison = firstPrices[-len(secondPrices):]
            else:
                firstPricesForComparison = firstPrices

            if len(firstPrices) < len(secondPrices):
                secondPricesForComparison = secondPrices[-len(firstPrices):]
            else:
                secondPricesForComparison = secondPrices

            correlation = scipy.stats.pearsonr(firstPricesForComparison, secondPricesForComparison)[0]
            allPairs.append((correlation, firstSymbol, secondSymbol))
            symbolCorrelations.append(correlation)
            symbolTable[secondSymbol] = correlation
        correlationGrid.append(symbolCorrelations)
        correlationTable[firstSymbol] = symbolTable
    return allPairs, correlationGrid, correlationTable


def outputCorrelationGrid(correlationGrid):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    ax.set_xticks(range(len(constants.symbolsToTrade)))
    ax.set_yticks(range(len(constants.symbolsToTrade)))
    ax.set_xticklabels(constants.symbolsToTrade, rotation=-90, size=5)
    ax.set_yticklabels(constants.symbolsToTrade, size=5)
    im = ax.imshow(correlationGrid, label="Correlations", cmap=plt.get_cmap("inferno"))

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Correlation Coefficient", rotation=-90, va="bottom")

    plt.savefig("correlation-grid.png")
    # plt.show()
    plt.close(fig)


def performCrossCorrelationAnalysis():
    allPairs, correlationGrid, correlationTable = computeCrossCorrelationTable()

    allPairs = list(sorted(allPairs, reverse=True))
    pprint(allPairs[:10])

    outputPriceChart([allPairs[0][1], allPairs[0][2]], "correlation.png")
    outputPriceChart([allPairs[-1][1], allPairs[-1][2]], "anti-correlation.png")

    outputCorrelationGrid(correlationGrid)


def findNextNonCorrelationSymbol(chain, correlationTable, remainingSymbols):
    averageCorrelations = []
    for symbol in remainingSymbols:
        symbolCorrelations = [
            abs(correlationTable[symbol][existingSymbolInChain])
            for existingSymbolInChain in chain
        ]
        averageCorrelationWithChain = numpy.average(symbolCorrelations)
        averageCorrelations.append((averageCorrelationWithChain, symbol))

    # print(averageCorrelations)
    averageCorrelations = sorted(averageCorrelations)
    return averageCorrelations[0][1], averageCorrelations[0][0]


def computeAntiCorrelations(startSymbol, count):
    allPairs, correlationGrid, correlationTable = computeCrossCorrelationTable()

    remainingSymbols = list(constants.symbolsToTrade)
    remainingSymbols.remove(startSymbol)

    chain = [
        startSymbol
    ]

    print(f"Starting with symbol {startSymbol}")
    for n in range(count):
        nextSymbolToAdd, correlation = findNextNonCorrelationSymbol(chain, correlationTable, remainingSymbols)
        remainingSymbols.remove(nextSymbolToAdd)
        chain.append(nextSymbolToAdd)
        print(f"Next: {nextSymbolToAdd} at correlation {correlation:.3f}")
    outputPriceChart(chain, "chain.png")





if __name__ == "__main__":
    # performCrossCorrelationAnalysis()
    # randomStartSymbol = random.choice(constants.symbolsToTrade)
    # computeAntiCorrelations(randomStartSymbol, 3)
    computeAntiCorrelations("SAP", 3)
