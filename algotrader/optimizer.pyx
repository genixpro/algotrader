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

    percentiles = []
    differences = []
    for n in range(1, len(datapoints) - daysOfHistoricalData - predictionDays - bufferDays):
        predictionPoint = len(datapoints) - n - 1
        dataEndPoint = predictionPoint - predictionDays
        dataStartPoint = dataEndPoint - daysOfHistoricalData

        simulationDataPoints = datapoints[dataStartPoint + 1:dataEndPoint + 1]

        historicalsEndDate = simulationDataPoints[-1].datetime

        actualDataPoint = datapoints[predictionPoint]
        actualClosingPrice = actualDataPoint.close

        (simulation, currentOpenPrice) = analyzer.runPriceSimulation(symbol, historicalsEndDate, predictionDays, datapoints=simulationDataPoints)

        simulationDifferences = numpy.array(simulation.endingPrices) - numpy.array(actualClosingPrice)
        simulationDifferences /= numpy.array(actualClosingPrice)

        differences.extend(simulationDifferences)

        percentile = (simulation.endingPrices < actualClosingPrice).sum() / len(simulation.endingPrices)
        percentiles.append(percentile)

    # fig, ax = plt.subplots(figsize=(12, 6))
    # ax.hist(percentiles, bins=20)
    # # plt.show()
    # ax.set_xlim([0, 1])
    # plt.savefig(f"percentiles-{symbol}-{predictionDays}-{daysOfHistoricalData}.png")
    # plt.close(fig)

    percentileBuckets = 20
    percentileHistogram = numpy.histogram(percentiles, bins=percentileBuckets, range=(0.0, 1.0))[0]
    expectedValuesPerBucket = len(percentiles) / percentileBuckets
    distributionError = numpy.absolute(percentileHistogram - expectedValuesPerBucket).mean()
    # distributionError = numpy.std(percentileHistogram)

    lossSquared = numpy.square(differences)
    meanSquaredError = numpy.mean(lossSquared)
    return meanSquaredError, distributionError


def backtestPriceSimulation(predictionDays, daysOfHistoricalData):
    simulationExecutions = []
    for symbol in constants.symbolsToTrade:
        future = global_services.globalExecutor.submit(backtestPriceSimulationOneSymbol, symbol, predictionDays, daysOfHistoricalData)
        simulationExecutions.append((symbol, future))

    meanSquaredErrors = []
    distributionErrors = []
    for simulationTuple in simulationExecutions:
        (symbol, future) = simulationTuple
        meanSquaredError, distributionError = future.result()
        # print(f"Symbol {symbol} - Average error {meanSquaredError:.4f}")
        meanSquaredErrors.append(meanSquaredError)
        distributionErrors.append(distributionError)


    averageMeanSquaredError = numpy.mean(meanSquaredErrors)
    averageDistributionError = numpy.mean(distributionErrors)

    return averageMeanSquaredError, averageDistributionError

def optimizeNumberOfHistoricalDays():
    allBests = []

    maxHistoricalDays = 150

    allPredictionDays = list(range(1, 60, 5))
    for predictionDays in allPredictionDays:
        historicalDaysToTest = list(range(predictionDays, maxHistoricalDays, 5))

        allErrors = []
        meanSquaredErrors = []
        distributionErrors = []
        for historicalDays in historicalDaysToTest:
            meanSquaredError, distributionError = backtestPriceSimulation(predictionDays=predictionDays, daysOfHistoricalData=historicalDays)
            print(f"Prediction days: {predictionDays} - Historical Days To Use: {historicalDays} - Final MSE {meanSquaredError:.6f} and Final Distribution Error: {distributionError:.3f}")
            meanSquaredErrors.append(meanSquaredError)
            distributionErrors.append(distributionError)
            allErrors.append((historicalDays, meanSquaredError, distributionError))


        bestMeanSquaredError = numpy.array(meanSquaredErrors).min()
        bestDistributionError = numpy.array(distributionErrors).min()

        print(f"Best MSE: {bestMeanSquaredError:.6f} and Best Distribution Error: {bestDistributionError:.3f}")

        bestHistoricalDays = None
        bestJointError = None
        jointErrors = []
        for historicalDays, meanSquaredError, distributionError in allErrors:
            meanSquaredErrorRatio = meanSquaredError / bestMeanSquaredError
            distributionErrorRatio = distributionError / bestDistributionError
            jointError = numpy.mean([meanSquaredErrorRatio, distributionErrorRatio])
            jointErrors.append(jointError)
            
            if bestJointError is None or jointError < bestJointError:
                bestJointError = jointError
                bestHistoricalDays = historicalDays

        print(f"Best historical days for {predictionDays} is {bestHistoricalDays} at with a joint error of {bestJointError}")
        allBests.append(bestHistoricalDays)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_xlim([1, maxHistoricalDays])

        ax.set_ylim([0.1, 2.0])
        ax.plot(historicalDaysToTest, jointErrors / numpy.mean(jointErrors), color='grey', label="Joint Error")
        ax.plot(historicalDaysToTest, meanSquaredErrors / numpy.mean(meanSquaredErrors), color='blue', label="Mean Squared Error")
        ax.plot(historicalDaysToTest, distributionErrors / numpy.mean(distributionErrors), color='red', label="Distribution Error")
        ax.legend()
        plt.savefig(f"optimal-historical-days-chart-{predictionDays}.png")
        plt.close(fig)

    print(allBests)
    plt.plot(allPredictionDays, allBests)
    plt.savefig(f"all-optimal-historical-days-to-use.png")
