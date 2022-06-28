import datetime
from pprint import pprint
from matplotlib import pyplot as plt
import numpy
import numpy.random
import ameritrade
import historicaldata
import simulation
import constants

def showEndingPriceChart(endingPrices):
    plt.hist(endingPrices, bins=25)
    plt.show()

def computeExpectedProfitsForFullOptionsChain(priceSimulation, centerPriceForChain, optionPriceIncrement,  contract):
    optionChainStart = round(centerPriceForChain * constants.optionChainStartPriceRatio)
    optionChainEnd = round(centerPriceForChain * constants.optionChainEndPriceRatio)

    strikePrices = numpy.arange(optionChainStart, optionChainEnd, optionPriceIncrement)
    profitsByStrike = {}
    for strikePrice in strikePrices:
        # probabilityInTheMoney = computeProbabilityOptionInMoney(priceSimulation, strikePrice, contract)
        # print(f"Probability of being in the money at a strike of ${strikePrice:.2f}: {probabilityInTheMoney * 100:.2f}%")
        # showEndingPriceChart(endingPrices)

        expectedProfit = priceSimulation.computeExpectedProfit(strikePrice, contract)
        # print(f"Expected profit of option at strike of ${strikePrice:.2f} is ${expectedProfit:.2f}")

        profitsByStrike[f"{strikePrice:.1f}"] = float(f"{expectedProfit:.2f}")
    return profitsByStrike

def computeClearingPriceForOption(optionDetails):
    spread = optionDetails['ask'] - optionDetails['bid']
    clearingPrice = optionDetails['bid'] + spread * constants.optionClearingPriceSpreadMidpoint
    return clearingPrice

def compareOptionChainContracts(priceSimulation, putProfitsByStrike, callProfitsByStrike, putOptionChain, callOptionChain, expiration):
    comparisons = {}
    for strikePrice in putOptionChain['putExpDateMap'][expiration].keys():
        if strikePrice not in putProfitsByStrike:
            # Skip this strike. Its soo far from the current center,
            # we didn't make a prediction for it
            continue

        putOptionDetails = putOptionChain['putExpDateMap'][expiration][strikePrice][0]
        callOptionDetails = callOptionChain['callExpDateMap'][expiration][strikePrice][0]

        expirationDateObj = datetime.datetime.utcfromtimestamp(putOptionDetails['expirationDate'] / 1000)
        now = datetime.datetime.now()
        differenceDays = (expirationDateObj - now).days

        putClearingPrice = computeClearingPriceForOption(putOptionDetails)
        callClearingPrice = computeClearingPriceForOption(callOptionDetails)

        investmentSimulation = simulation.MonteCarloInvestmentSimulation(priceSimulation=priceSimulation, 
                                                                         consecutiveTradesPerSimulation=constants.investmentSimulationConsecutiveTrades,
                                                                         numberOfSimulations=constants.investmentSimulationNumberOfSimulations,                                                                         
                                                                         )
        proportionToInvest, lossRate = investmentSimulation.computeOptimalInvestmentAmount(strikePrice, putClearingPrice)

        putProbabilityInTheMoney = priceSimulation.computeProbabilityOptionInMoney(float(strikePrice), 'PUT')
        callProbabilityInTheMoney = priceSimulation.computeProbabilityOptionInMoney(float(strikePrice), 'CALL')

        proportionToInvest = min(proportionToInvest, putProbabilityInTheMoney)

        putExpectedProfit = putProfitsByStrike[strikePrice]
        putGain = putExpectedProfit - putClearingPrice
        putReturn = (putGain / putClearingPrice) * proportionToInvest
        putROI = numpy.power(1 + putReturn, 365 / differenceDays) - 1

        callExpectedProfit = callProfitsByStrike[strikePrice]
        callGain = callExpectedProfit - callClearingPrice
        callReturn = (callGain / callClearingPrice) * proportionToInvest
        callROI = numpy.power(1 + callReturn, 365 / differenceDays) - 1

        comparisons[strikePrice] = {
            "putExpectedProfit": putExpectedProfit,
            "putClearingPrice": putClearingPrice,
            "callExpectedProfit": callExpectedProfit,
            "callClearingPrice": callClearingPrice,
            "putGain": float(f"{putGain:.2f}"),
            "callGain": float(f"{callGain:.2f}"),
            "putROI": float(f"{putROI:.2f}"),
            "callROI": float(f"{callROI:.3f}"),
            "putReturn": float(f"{putReturn:.2f}"),
            "callReturn": float(f"{callReturn:.3f}"),
            "putProbabilityInTheMoney": float(f"{putProbabilityInTheMoney:.3f}"),
            "callProbabilityInTheMoney": float(f"{callProbabilityInTheMoney:.3f}"),
            "putProportionToInvest": proportionToInvest,
            "putLossRate": lossRate,
        }

        pprint(comparisons[strikePrice])

    return comparisons



def analyzeSymbolOptions():
    putOptionChain = ameritrade.getOptionChain(constants.symbolToAnalyze, "PUT")
    callOptionChain = ameritrade.getOptionChain(constants.symbolToAnalyze, "CALL")

    print("Available option expiration dates")
    pprint(list(putOptionChain['putExpDateMap'].keys()))

    historicalsStartDate = datetime.datetime.now() - datetime.timedelta(days=constants.priceSimulationDaysOfHistoricalDataToUse)
    historicalsEndDate = datetime.datetime.now() + datetime.timedelta(days=1)

    historicals = historicaldata.HistoricalPrices()

    datapoints = historicals.getProcessedTimeSeriesBetweenDates(constants.symbolToAnalyze, historicalsStartDate, historicalsEndDate)

    currentOpenPrice = datapoints[-1].open
    datapoints = datapoints[:-1]

    priceSimulation = simulation.MonteCarloPriceSimulation(
        datapoints=datapoints,
        currentOpenPrice=currentOpenPrice,
        numDays=constants.tradingDaysRemaining,
        numberOfSimulations=constants.priceSimulationNumberOfSimulations
    )
    priceSimulation.runSimulations()

    putProfitsByStrike = computeExpectedProfitsForFullOptionsChain(priceSimulation, currentOpenPrice, constants.optionPriceIncrement, "PUT")
    callProfitsByStrike = computeExpectedProfitsForFullOptionsChain(priceSimulation, currentOpenPrice, constants.optionPriceIncrement, "CALL")

    print("Here are the expected profits at different strikes for PUT options:")
    pprint(putProfitsByStrike)

    comparisons = compareOptionChainContracts(priceSimulation, putProfitsByStrike, callProfitsByStrike, putOptionChain, callOptionChain, constants.expirationToAnalyze)
    print("Here are the comparison details for different option contracts")
    pprint(comparisons)

    print("Here are put returns by strike")
    putGains = {
        float(strikePrice): comparison['putReturn']
        for strikePrice, comparison in comparisons.items()
    }
    pprint(putGains)
    # plt.scatter(putGains.keys(), putGains.values())
    # plt.show()

    # bestAmountsToGamble = []
    # probabilities = list(numpy.arange(0, 1, 0.03))
    # for probability in probabilities:
    #     amount = computeOptimalInvestmentAmount(probability)
    #     bestAmountsToGamble.append(amount)
    #
    # plt.scatter(probabilities, bestAmountsToGamble)
    # plt.show()
