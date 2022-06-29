import numpy
import random
import os.path
from algotrader import historical_data
import matplotlib.pyplot as plt
from algotrader.global_services import globalExecutor

class PriceSimulationParameters:
    def __init__(self, datapoints):
    #     self.dayChangeValues = numpy.array(list(filter(lambda d: d is not None, map(lambda d: d.dayChange, datapoints))))
    #     self.gapPreviousValues = numpy.array(list(filter(lambda d: d is not None, map(lambda d: d.gapPrevious, datapoints))))
    #     self.gapNextValues = numpy.array(list(filter(lambda d: d is not None, map(lambda d: d.gapNext, datapoints))))

        self.dayChangeValues = list(filter(lambda d: d is not None, map(lambda d: d.dayChange, datapoints)))
        self.gapPreviousValues = list(filter(lambda d: d is not None, map(lambda d: d.gapPrevious, datapoints)))
        self.gapNextValues = list(filter(lambda d: d is not None, map(lambda d: d.gapNext, datapoints)))

        self.dayChangeStd = numpy.std(self.dayChangeValues)
        self.dayChangeMean = numpy.mean(self.dayChangeValues)

        self.gapPreviousStd = numpy.std(self.gapPreviousValues)
        self.gapPreviousMean = numpy.mean(self.gapPreviousValues)

        self.gapNextStd = numpy.std(self.gapNextValues)
        self.gapNextMean = numpy.mean(self.gapNextValues)


class SinglePriceSimulation:
    def __init__(self, simulationParameters):
        self.simulationParameters = simulationParameters
    
    def runPriceSimulation(self, currentOpenPrice, numDays):
        dayChangeValues = self.simulationParameters.dayChangeValues
        gapPreviousValues = self.simulationParameters.gapPreviousValues
        gapNextValues = self.simulationParameters.gapNextValues

        dayChangeStd = self.simulationParameters.dayChangeStd
        dayChangeMean = self.simulationParameters.dayChangeMean

        gapPreviousStd = self.simulationParameters.gapPreviousStd
        gapPreviousMean = self.simulationParameters.gapPreviousMean

        # sampledDayChangeValues = numpy.random.choice(a=dayChangeValues, size=numDays, replace=True)
        # sampledGapPreviousValues = numpy.random.choice(a=gapPreviousValues, size=(numDays - 1), replace=True)

        # sampledDayChangeValues = random.choices(dayChangeValues, k=numDays)
        # sampledGapPreviousValues = random.choices(gapPreviousValues, k=(numDays - 1))

        sampledDayChangeValues = random.sample(dayChangeValues, k=numDays)
        sampledGapPreviousValues = random.sample(gapPreviousValues, k=(numDays - 1))

        cumulativeDayChanges = numpy.prod(sampledDayChangeValues)
        cumulativeGapPrevious = numpy.prod(sampledGapPreviousValues)
        lastDatapoint = historical_data.PriceDatapoint()
        lastDatapoint.close = float(currentOpenPrice * cumulativeDayChanges * cumulativeGapPrevious)
        lastDatapoint.open = float(lastDatapoint.close / sampledDayChangeValues[-1])

        return lastDatapoint

class MonteCarloPriceSimulation:
    def __init__(self, datapoints, currentOpenPrice, numDays, numberOfSimulations):
        self.simulationParameters = PriceSimulationParameters(datapoints)
        self.currentOpenPrice = currentOpenPrice
        self.numDays = numDays
        self.numberOfSimulations = numberOfSimulations
        self.endingPrices = []

    def runSimulations(self):
        self.endingPrices = []
        for n in range(self.numberOfSimulations):
            simulation = SinglePriceSimulation(self.simulationParameters)
            lastDatapoint = simulation.runPriceSimulation(self.currentOpenPrice, self.numDays)
            self.endingPrices.append(lastDatapoint.close)

        self.endingPrices = numpy.array(self.endingPrices)

        return self.endingPrices

    def computeEndProfitsAtStrike(self, strikePrice, contract):
        if contract == "PUT":
            return numpy.maximum(0, numpy.subtract(strikePrice, self.endingPrices))
        elif contract == "CALL":
            return numpy.maximum(0, numpy.subtract(self.endingPrices, strikePrice))


    def computeProbabilityOptionInMoney(self, strikePrice, contract):
        profits = self.computeEndProfitsAtStrike(strikePrice, contract)
        probabilityInTheMoney = float(numpy.count_nonzero(profits)) / float(len(self.endingPrices))

        return probabilityInTheMoney

    def computeExpectedProfit(self, strikePrice, contract):
        profits = self.computeEndProfitsAtStrike(strikePrice, contract)
        return numpy.mean(profits)


class MonteCarloInvestmentSimulation:
    def __init__(self, priceSimulation, consecutiveTradesPerSimulation, numberOfSimulations, outlierProportionToDiscard):
        self.priceSimulation = priceSimulation
        self.consecutiveTradesPerSimulation = consecutiveTradesPerSimulation
        self.numberOfSimulations = numberOfSimulations
        self.outlierProportionToDiscard = outlierProportionToDiscard


    def simulatePortfolio(self, strikePrice, contractCost, contract, proportionToInvest):
        startingCapital = 10000
        capital = startingCapital
        for n in range(self.consecutiveTradesPerSimulation):
            contractsToBuy = round((capital * proportionToInvest) / contractCost)
            capital = capital - contractCost * contractsToBuy

            endingPrice = random.choice(self.priceSimulation.endingPrices)
            if contract == "PUT":
                gain = strikePrice - endingPrice
            elif contract == "CALL":
                gain = endingPrice - strikePrice
            # print(capital, proportionToInvest, contractsToBuy, gain)
            if gain > 0:
                capital = capital + gain * contractsToBuy

        return capital / startingCapital

    def computeAverageReturn(self, strikePrice, contractCost, contract, proportionToInvest):
        returns = []
        numberTimesLossed = 0
        for n in range(self.numberOfSimulations):
            portfolioReturn = self.simulatePortfolio(float(strikePrice), contractCost, contract, proportionToInvest)
            if portfolioReturn < 1.0:
                numberTimesLossed += 1
            returns.append(portfolioReturn)

        returns = list(sorted(returns))

        outlierCutoff = int(len(returns) * self.outlierProportionToDiscard)
        if outlierCutoff > 0:
            returns = returns[outlierCutoff:-outlierCutoff]

        averageReturn = numpy.mean(returns)

        lossRate = float(numberTimesLossed) / float(self.numberOfSimulations)

        return averageReturn, lossRate

    def computeOptimalInvestmentAmount(self, strikePrice, contractCost, contract, symbol):
        futures = []

        proportionsToTest = []
        proportionsToTest.extend(numpy.arange(0.002, 0.01, 0.002))
        proportionsToTest.extend(numpy.arange(0.01, 0.05, 0.01))
        proportionsToTest.extend(numpy.arange(0.05, 0.20, 0.025))
        proportionsToTest.extend(numpy.arange(0.20, 1.01, 0.05))

        for proportionToInvest in proportionsToTest:
            future = globalExecutor.submit(self.computeAverageReturn, strikePrice, contractCost, contract, proportionToInvest)
            futures.append((proportionToInvest, future))

        allAverageReturns = []
        allAdjustedReturns = []
        allAdjustedProportions = []
        allProportions = []
        allLossRates = []
        for proportionToInvest, future in futures:
            averageReturn, lossRate = future.result()

            adjustedProportion = proportionToInvest * (1.0 - lossRate)
            adjustedReturn = averageReturn * (1.0 - lossRate)

            allAverageReturns.append(averageReturn)
            allAdjustedReturns.append(adjustedReturn)
            allAdjustedProportions.append(adjustedProportion)
            allProportions.append(proportionToInvest)
            allLossRates.append(lossRate)

        adjustedReturnFit = numpy.polyfit(allProportions, allAdjustedReturns, deg=3)
        polyAdjustedReturnLine = numpy.poly1d(adjustedReturnFit)

        averageReturnFit = numpy.polyfit(allProportions, allAverageReturns, deg=3)
        polyAverageReturnLine = numpy.poly1d(averageReturnFit)

        lossRateFit = numpy.polyfit(allProportions, allLossRates, deg=3)
        polyLossRateLine = numpy.poly1d(lossRateFit)

        adjustedProportionFit = numpy.polyfit(allProportions, allAdjustedProportions, deg=3)
        polyAdjustedProportionLine = numpy.poly1d(adjustedProportionFit)

        xp = numpy.linspace(0, 1, 1000)

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.scatter(allProportions, numpy.array(allAverageReturns), 25, 'blue', label='Average Return (assuming 100% invested)')
        ax.scatter(allProportions, numpy.array(allLossRates), 25, 'green', label='Loss Rate')
        ax.scatter(allProportions, numpy.array(allAdjustedReturns), 25, 'red', label='Adjusted Return (assuming 1 - lossRate invested)')
        ax.scatter(allProportions, numpy.array(allAdjustedProportions), 25, 'grey', label='Loss Adjusted Proportions To Invest')
        ax.plot(xp, polyAverageReturnLine(xp), 25, 'blue', label='Average Return Trend')
        ax.plot(xp, polyLossRateLine(xp), 25, 'green', label='Loss Rate Trend')
        ax.plot(xp, polyAdjustedReturnLine(xp), 25, 'red', label='Adjusted Return Trend')
        ax.plot(xp, polyAdjustedProportionLine(xp), 25, 'grey', label='Loss Adjusted Proportion To Invest Trend')
        ax.set_xlim([0, 1])

        ylimit = 1.0
        ylimit = max(ylimit, numpy.max(allAdjustedReturns) * 1.1)
        ylimit = max(ylimit, numpy.max(allAverageReturns) * 1.1)

        ax.set_ylim([-0.1, ylimit])
        ax.set_title(f"Returns v.s. proportion of cash invested {symbol} at {strikePrice}")
        ax.axhline(0, color='black')
        ax.legend()

        if not os.path.exists("images"):
            os.mkdir("images")
        plt.savefig(f"images/{symbol}-{strikePrice}-{contract}-optimal-investment-proportion.png")
        plt.close(fig)

        returnFitOptimalAdjustedReturnRate = None
        returnFitOptimalProportionToInvest = None
        returnFitOptimalAdjustedProportionToInvest = None
        returnFitOptimalLossRate = None

        for proportionToInvest in xp:
            adjustedReturnRate = polyAdjustedReturnLine(proportionToInvest)
            lossRate = polyLossRateLine(proportionToInvest)
            adjustedProportionToInvest = polyAdjustedProportionLine(proportionToInvest)

            if returnFitOptimalAdjustedReturnRate is None or adjustedReturnRate > returnFitOptimalAdjustedReturnRate:
                returnFitOptimalAdjustedReturnRate = adjustedReturnRate
                returnFitOptimalProportionToInvest = proportionToInvest
                returnFitOptimalAdjustedProportionToInvest = adjustedProportionToInvest
                returnFitOptimalLossRate = lossRate

        # print(f"Best amount to invest, {bestProportionToInvest:.3f}: {bestAverageReturn:.3f}, {bestLossRate:.3f}, {returnFitOptimalProportionToInvest:.3f}, {returnFitOptimalLossRate:.3f}")

        returnFitOptimalAdjustedProportionToInvest = max(0.0, min(1.0, returnFitOptimalAdjustedProportionToInvest))
        returnFitOptimalLossRate = max(0.0, min(1.0, returnFitOptimalLossRate))
        returnFitOptimalProportionToInvest = max(0.0, min(1.0, returnFitOptimalProportionToInvest))

        return returnFitOptimalAdjustedProportionToInvest, returnFitOptimalLossRate, returnFitOptimalProportionToInvest
