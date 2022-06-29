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
    historicalDaysToTest = list(range(23, 150))
    meanSquaredErrors = []
    for historicalDays in historicalDaysToTest:
        meanSquaredError = backtestPriceSimulation(daysOfHistoricalData=historicalDays)
        print(f"Days: {historicalDays} - Final MSE {meanSquaredError:.5f}")
        meanSquaredErrors.append(meanSquaredError)

    plt.plot(historicalDaysToTest, meanSquaredErrors)
    plt.show()
