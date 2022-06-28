import numpy
import random
import historical_data
import matplotlib.pyplot as plt
from global_services import globalExecutor

class PriceSimulationParameters:
    def __init__(self, datapoints):
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

        sampledDayChangeValues = random.sample(dayChangeValues, numDays)
        sampledGapPreviousValues = random.sample(gapPreviousValues, numDays)
        random.shuffle(sampledDayChangeValues)
        random.shuffle(sampledGapPreviousValues)

        lastDatapoint = None
        nextDatapoint = historical_data.PriceDatapoint()
        for n in range(numDays):
            if n == 0:
                nextDatapoint.open = currentOpenPrice
            else:
                gapPrevious = sampledGapPreviousValues[n]
                nextDatapoint.open = lastDatapoint.close * gapPrevious

            dayChange = sampledDayChangeValues[n]
            nextDatapoint.close = nextDatapoint.open * dayChange

            lastDatapoint = nextDatapoint

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

        return self.endingPrices

    def computeProbabilityOptionInMoney(self, strikePrice, contract):
        countPricesBelowTarget = 0
        for price in self.endingPrices:
            if contract == "PUT":
                if price < strikePrice:
                    countPricesBelowTarget += 1
            elif contract == "CALL":
                if price > strikePrice:
                    countPricesBelowTarget += 1

        probabilityInTheMoney = float(countPricesBelowTarget) / float(len(self.endingPrices))

        return probabilityInTheMoney

    def computeExpectedProfit(self, strikePrice, contract):
        profits = []
        for endingPrice in self.endingPrices:
            if contract == "PUT":
                if endingPrice < strikePrice:
                    profits.append(strikePrice - endingPrice)
                else:
                    profits.append(0)
            elif contract == "CALL":
                if endingPrice > strikePrice:
                    profits.append(endingPrice - strikePrice)
                else:
                    profits.append(0)
        return numpy.mean(profits)


class MonteCarloInvestmentSimulation:
    def __init__(self, priceSimulation, consecutiveTradesPerSimulation, numberOfSimulations):
        self.priceSimulation = priceSimulation
        self.consecutiveTradesPerSimulation = consecutiveTradesPerSimulation
        self.numberOfSimulations = numberOfSimulations


    def simulatePortfolio(self, strikePrice, contractCost, proportionToInvest):
        startingCapital = 10000
        capital = startingCapital
        for n in range(self.consecutiveTradesPerSimulation):
            contractsToBuy = round((capital * proportionToInvest) / contractCost)
            capital = capital - contractCost * contractsToBuy

            endingPrice = random.choice(self.priceSimulation.endingPrices)
            gain = strikePrice - endingPrice
            # print(capital, proportionToInvest, contractsToBuy, gain)
            if gain > 0:
                capital = capital + gain * contractsToBuy

        return capital / startingCapital

    def computeAverageReturn(self, strikePrice, contractCost, proportionToInvest):
        returns = []
        numberTimesLossed = 0
        for n in range(self.numberOfSimulations):
            portfolioReturn = self.simulatePortfolio(float(strikePrice), contractCost, proportionToInvest)
            if portfolioReturn < 1.0:
                numberTimesLossed += 1
            returns.append(portfolioReturn)

        returns = list(sorted(returns))

        outlierCutoff = int(len(returns) * 0.0001)
        averageReturn = numpy.mean(returns[outlierCutoff:-outlierCutoff])
        # averageReturn = numpy.mean(returns)

        lossRate = float(numberTimesLossed) / float(self.numberOfSimulations)

        return averageReturn, lossRate

    def computeOptimalInvestmentAmount(self, strikePrice, contractCost):
        bestAverageReturn = None
        bestProportionToInvest = None
        bestLossRate = None
        futures = []
        for proportionToInvest in numpy.arange(0.05, 1.01, 0.05):
            future = globalExecutor.submit(self.computeAverageReturn, strikePrice, contractCost, proportionToInvest)
            futures.append((proportionToInvest, future))

        allReturns = []
        allProportions = []
        allLossRates = []
        for proportionToInvest, future in futures:
            averageReturn, lossRate = future.result()

            allReturns.append(averageReturn)
            allProportions.append(proportionToInvest)
            allLossRates.append(lossRate)

            print(f"{float(strikePrice):.2f}", f"{proportionToInvest:.2f}", f"{averageReturn:.2f}", f"{lossRate:.2f}")
            if bestAverageReturn is None or averageReturn > bestAverageReturn:
                bestAverageReturn = averageReturn
                bestProportionToInvest = proportionToInvest
                bestLossRate = lossRate

        returnFit = numpy.polyfit(allProportions, allReturns, deg=2)
        polyReturnLine = numpy.poly1d(returnFit)

        lossRateFit = numpy.polyfit(allProportions, allLossRates, deg=2)
        polyLossRateLine = numpy.poly1d(lossRateFit)

        xp = numpy.linspace(0, 1, 1000)

        plt.scatter(allProportions, allReturns, 25, 'blue')
        plt.scatter(allProportions, numpy.array(allLossRates) * 10, 25, 'green')
        plt.plot(xp, polyReturnLine(xp), 25, 'red')
        plt.plot(xp, polyLossRateLine(xp) * 10, 25, 'yellow')
        # plt.show()

        returnFitOptimalReturnRate = None
        returnFitOptimalProportionToInvest = None
        returnFitOptimalLossRate = None

        for proportionToInvest in xp:
            returnRate = polyReturnLine(proportionToInvest)
            lossRate = polyLossRateLine(proportionToInvest)

            if returnFitOptimalReturnRate is None or returnRate > returnFitOptimalReturnRate:
                returnFitOptimalReturnRate = returnRate
                returnFitOptimalProportionToInvest = proportionToInvest
                returnFitOptimalLossRate = lossRate

        print(
            f"Best amount to invest, {bestProportionToInvest:.2f}: {bestAverageReturn:.2f}, {bestLossRate:.2f}, {returnFitOptimalProportionToInvest:.2f}, {returnFitOptimalLossRate:.2f}")

        return max(0.0, min(1.0, returnFitOptimalProportionToInvest)), max(0.0, min(1.0, returnFitOptimalLossRate))
