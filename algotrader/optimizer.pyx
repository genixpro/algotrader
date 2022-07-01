import pyximport
pyximport.install()

import datetime
from pprint import pprint
from matplotlib import pyplot as plt
import numpy
import numpy.random
from algotrader import historical_data
from algotrader import analyzer
from algotrader import constants
from algotrader import global_services

def backtestPriceSimulationOneSymbol(symbol, predictionDays, daysOfHistoricalData):
    constants.priceSimulationNumberOfSimulations = 100

    yearLength = 250

    nextDay = datetime.datetime.now() + datetime.timedelta(days=1)
    historicals = historical_data.HistoricalPrices()
    datapoints = historicals.getProcessedTimeSeries(symbol, nextDay, yearLength)

    bufferDays = 3

    differences = []
    for n in range(1, len(datapoints) - daysOfHistoricalData - predictionDays - bufferDays):
        predictionPoint = len(datapoints) - n - 1
        dataEndPoint = predictionPoint - predictionDays
        dataStartPoint = dataEndPoint - daysOfHistoricalData

        simulationDataPoints = datapoints[dataStartPoint:dataEndPoint]

        historicalsEndDate = datetime.datetime.now() - datetime.timedelta(days=(n + predictionDays))

        actualDataPoint = datapoints[predictionPoint]
        actualClosingPrice = actualDataPoint.close

        (simulation, currentOpenPrice) = analyzer.runPriceSimulation(symbol, historicalsEndDate, predictionDays, datapoints=simulationDataPoints)

        simulationDifferences = numpy.array(simulation.endingPrices) - numpy.array(actualClosingPrice)
        simulationDifferences /= numpy.array(actualClosingPrice)

        differences.extend(simulationDifferences)

    lossSquared = numpy.square(differences)
    meanSquaredError = numpy.mean(lossSquared)
    return meanSquaredError


def backtestPriceSimulation(predictionDays=22, daysOfHistoricalData=constants.priceSimulationTradingDaysOfHistoricalDataToUse):
    simulationExecutions = []
    for symbol in constants.symbolsToTrade:
        future = global_services.globalExecutor.submit(backtestPriceSimulationOneSymbol, symbol, predictionDays, daysOfHistoricalData)
        simulationExecutions.append((symbol, future))

    errors = []
    for simulationTuple in simulationExecutions:
        (symbol, future) = simulationTuple
        meanSquaredError = future.result()
        # print(f"Symbol {symbol} - Average error {meanSquaredError:.4f}")
        errors.append(meanSquaredError)

    averageError = numpy.mean(errors)

    return averageError

def optimizeNumberOfHistoricalDays():
    allBests = []

    maxHistoricalDays = 65

    for predictionDays in range(1, 60):
        historicalDaysToTest = list(range(2, maxHistoricalDays))
        bestHistoricalDays = None
        bestMSE = None
        meanSquaredErrors = []
        for historicalDays in historicalDaysToTest:
            meanSquaredError = backtestPriceSimulation(predictionDays=predictionDays, daysOfHistoricalData=historicalDays)
            # print(f"Prediction days: {predictionDays} - Historical Days To Use: {historicalDays} - Final MSE {meanSquaredError:.5f}")
            meanSquaredErrors.append(meanSquaredError)

            if bestMSE is None or meanSquaredError < bestMSE:
                bestMSE = meanSquaredError
                bestHistoricalDays = historicalDays

        print(f"Best historical days for {predictionDays} is {bestHistoricalDays} at an MSE of {bestMSE}")
        allBests.append(bestHistoricalDays)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_xlim([1, maxHistoricalDays])

        ax.set_ylim([0, min(0.25, numpy.max(meanSquaredErrors) * 1.1)])
        ax.plot(historicalDaysToTest, meanSquaredErrors)
        plt.savefig(f"optimal-historical-days-chart-{predictionDays}.png")
        plt.close(fig)

    print(allBests)
    plt.plot(range(1, 60), allBests)
    plt.savefig(f"all-optimal-historical-days-to-use.png")
