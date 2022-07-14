# cython: language_level=3, boundscheck=True
import pyximport
pyximport.install()

import datetime
from pprint import pprint, pformat
from matplotlib import pyplot as plt
import numpy
import numpy.random
import holidays
from algotrader import ameritrade
from algotrader import historical_data
from algotrader import simulation
from algotrader import constants
from algotrader import correlation_analysis
import concurrent.futures
import time
import csv

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

def getOptionChainDetailsFieldForContractType(contract):
    if contract == "PUT":
        detailFieldName = "putExpDateMap"
    elif contract == "CALL":
        detailFieldName = "callExpDateMap"

    return detailFieldName

def compareOptionChainContracts(priceSimulation, profitsByStrike, optionChain, expiration, contract, symbol):
    comparisons = {}
    detailFieldName = getOptionChainDetailsFieldForContractType(contract)

    for strikePrice in optionChain[detailFieldName][expiration].keys():
        if strikePrice not in profitsByStrike:
            # Skip this strike. Its soo far from the current center,
            # we didn't make a prediction for it
            continue

        optionDetails = optionChain[detailFieldName][expiration][strikePrice][0]

        expirationDateObj = datetime.datetime.utcfromtimestamp(optionDetails['expirationDate'] / 1000)
        now = datetime.datetime.now()
        differenceDays = max(1, (expirationDateObj - now).days)

        clearingPrice = computeClearingPriceForOption(optionDetails)

        if clearingPrice <= 0:
            print("bad option")
            pprint(optionDetails)
            continue

        investmentSimulation = simulation.MonteCarloInvestmentSimulation(priceSimulation=priceSimulation,
                                                                         consecutiveTradesPerSimulation=constants.investmentSimulationConsecutiveTrades,
                                                                         numberOfSimulations=constants.investmentSimulationNumberOfSimulations,
                                                                         outlierProportionToDiscard=constants.investmentSimulationOutlierProportionToDiscard,
                                                                         )

        optimalInvestmentProportion, lossRate, nonAdjustedOptimalInvestmentProportion = investmentSimulation.computeOptimalInvestmentAmount(strikePrice, clearingPrice, contract, symbol, expiration)

        probabilityInTheMoney = priceSimulation.computeProbabilityOptionInMoney(float(strikePrice), contract)

        proportionToInvest = min(optimalInvestmentProportion, probabilityInTheMoney)

        expectedProfit = profitsByStrike[strikePrice]
        gain = expectedProfit - clearingPrice
        optionReturn = (gain / clearingPrice) * proportionToInvest
        optionDailyReturn = numpy.power(1 + optionReturn, 1 / differenceDays) - 1

        comparisons[float(strikePrice)] = {
            "symbol": symbol,
            "expiration": expiration,
            "strike": strikePrice,
            "contract": contract,
            "expectedProfit": round(expectedProfit, 2),
            "clearingPrice": round(clearingPrice, 2),
            "gain": round(gain, 3),
            "dailyReturn": round(optionDailyReturn, 5),
            "return": round(abs(optionReturn), 3),
            "probabilityInTheMoney": round(probabilityInTheMoney, 3),
            "optimalInvestmentProportion": round(optimalInvestmentProportion, 3),
            "proportionToInvest": round(proportionToInvest, 3),
            "lossRate": round(lossRate, 3),
            "nonAdjustedOptimalInvestmentProportion": round(nonAdjustedOptimalInvestmentProportion, 3)
        }

        if constants.verboseOutput:
            print(f"{contract} with strike price {strikePrice}")
            print(pformat({strikePrice: comparisons[float(strikePrice)]}))

    return comparisons

def runPriceSimulation(symbol, historicalsEndDate, predictionDays, datapoints=None):
    startingPrice = None

    if datapoints is None:
        historicals = historical_data.HistoricalPrices()
        datapoints = historicals.getProcessedTimeSeries(symbol, historicalsEndDate, constants.priceSimulationTradingDaysOfHistoricalDataToUse + 1)
        isSimulatingDuringMarketHours = True

        # TODO: unsure if this should be set to the current days open price,
        #  or the current price right as of this moment (which would be the "close" price here)
        #  Currently setting it to the current price right as of this moment, so we make sure we
        #  consider price movements that occurred already today. But this isn't a perfect or
        #  principled way of considering the current intra-day price movement. Really the first
        #  step of the price simulation should just be done with a smaller variance depending on
        #  how many hours of trading are left in the current day.
        startingPrice = datapoints[-1].close
        datapoints = datapoints[:-1]
    else:
        isSimulatingDuringMarketHours = False
        startingPrice = datapoints[-1].close

    if constants.verboseOutput:
        print(f"Latest datapoint for symbol {symbol}")
        pprint(datapoints[-1].__dict__)

    priceSimulation = simulation.MonteCarloPriceSimulation(
        datapoints=datapoints,
        startingPrice=startingPrice,
        numDays=predictionDays,
        numberOfSimulations=constants.priceSimulationNumberOfSimulations,
        isSimulatingDuringMarketHours=isSimulatingDuringMarketHours,
    )
    priceSimulation.runSimulations()

    return (priceSimulation, startingPrice)

def getDatetimeObjectForOptionExpiration(expiration):
    return datetime.datetime.strptime(expiration.split(":")[0], "%Y-%m-%d")

def computeTradingDaysRemainingForExpiration(expiration):
    us_holidays = holidays.country_holidays('US')

    currentDate = datetime.datetime.now()

    expirationDate = getDatetimeObjectForOptionExpiration(expiration)

    tradingDays = 0
    while currentDate < expirationDate:
        # Check if its between monday and friday
        if currentDate.isoweekday() >=1 and currentDate.isoweekday() <= 5:
            dateWithoutTime = datetime.date(year=currentDate.year, month=currentDate.month, day=currentDate.day)
            if dateWithoutTime not in us_holidays:
                tradingDays += 1

        currentDate = currentDate + datetime.timedelta(days=1)

    # Add in one extra day for the expiration date itself
    tradingDays += 1

    return tradingDays

def analyzeSymbolOptions(symbol, contract, priceIncrement):
    if constants.verboseOutput:
        print(f"{symbol} {contract} Fetching current options quotes")
    putOptionChain = ameritrade.getOptionChain(symbol, contract)

    expirationDates = list(putOptionChain[getOptionChainDetailsFieldForContractType(contract)].keys())
    if constants.verboseOutput:
        print(f"{symbol} {contract} Available option expiration dates")
        pprint(expirationDates)

    allComparisons = []

    for expiration in expirationDates:
        daysDiff = (getDatetimeObjectForOptionExpiration(expiration) - datetime.datetime.now()).days
        if daysDiff > constants.optionMaxExpirationTimeDays:
            if constants.verboseOutput:
                print(f"Skipping analysis for {symbol} {contract} {expiration} because its too far in the future")
            continue
        if daysDiff < constants.optionMinExpirationTimeDays:
            if constants.verboseOutput:
                print(f"Skipping analysis for {symbol} {contract} {expiration} because its too soon")
            continue

        tradingDaysRemaining = computeTradingDaysRemainingForExpiration(expiration)

        if constants.verboseOutput:
            print(f"{symbol} {contract} {expiration} Running primary price simulation for {tradingDaysRemaining} trading days")
        historicalsEndDate = datetime.datetime.now() + datetime.timedelta(days=1)
        (priceSimulation, currentOpenPrice) = runPriceSimulation(
            symbol=symbol,
            historicalsEndDate=historicalsEndDate,
            predictionDays=tradingDaysRemaining)

        if constants.verboseOutput:
            print(f"{symbol} {contract} {expiration} Computing expected profits for all the different available options")
        profitsByStrike = computeExpectedProfitsForFullOptionsChain(priceSimulation, currentOpenPrice, priceIncrement, contract)

        if constants.verboseOutput:
            print(f"{symbol} {contract} {expiration} Here are the expected profits at different strikes for the options:")
            pprint(profitsByStrike)

        comparisons = compareOptionChainContracts(priceSimulation, profitsByStrike, putOptionChain, expiration, contract, symbol)
        # print("Here are the comparison details for different option contracts")
        # pprint(comparisons)

        if constants.verboseOutput:
            print(f"{symbol} {contract} {expiration} Here are the returns by strike")
            allReturns = {
                float(strikePrice): comparison['return']
                for strikePrice, comparison in comparisons.items()
            }
            pprint(allReturns)

        allComparisons.extend(comparisons.values())

    return allComparisons

    # plt.scatter(allReturns.keys(), allReturns.values(), label="Returns by strike")
    # plt.show()

def computeAllOptionsComparisons():
    # topExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    topExecutor = concurrent.futures.ProcessPoolExecutor(max_workers=constants.numWorkers)

    allComparisonFutures = []
    for symbol in constants.symbolsToTrade:
        # Analyze the PUTS
        putFuture = topExecutor.submit(analyzeSymbolOptions,
            symbol=symbol,
            contract="PUT",
            priceIncrement=constants.optionPriceIncrement,
        )
        time.sleep(0.1)

        # Analyze the CALLS
        callFuture = topExecutor.submit(analyzeSymbolOptions,
            symbol=symbol,
            contract="CALL",
            priceIncrement=constants.optionPriceIncrement,
        )
        time.sleep(0.1)

        allComparisonFutures.append((symbol, putFuture, callFuture))

    allComparisons = []
    for symbol, putFuture, callFuture in allComparisonFutures:
        print(f"Fetching results for symbol {symbol}")

        putResult = putFuture.result()
        callResult = callFuture.result()

        symbolComparisons = []
        symbolComparisons.extend(putResult)
        symbolComparisons.extend(callResult)
        symbolComparisons = list(sorted(symbolComparisons, key=lambda comparison: comparison['dailyReturn'], reverse=True))

        # Output the top ten options by return
        print(f"Best options for this symbol ({symbol})")
        pprint(symbolComparisons[:10], indent=8)

        allComparisons.extend(symbolComparisons)
    return allComparisons

def analyzeAllOptions():
    allComparisons = computeAllOptionsComparisons()

    allComparisons = list(sorted(allComparisons, key=lambda comparison: comparison['dailyReturn'], reverse=True))

    # Output the top ten options by return
    print("Outputting the best options across all symbols and categories")
    pprint(allComparisons[:10], indent=8)

    with open("options.csv", "wt") as f:
        dictWriter = csv.DictWriter(f, fieldnames=list(allComparisons[0].keys()))
        dictWriter.writeheader()
        dictWriter.writerows(allComparisons)

    # Now we filter the options for ones with a high probability of being in the money
    filteredOptions = filter(lambda c: c['probabilityInTheMoney'] > 0.5, allComparisons)

    # Filter for options that wont cost too much to purchase
    filteredOptions = filter(lambda c: c['clearingPrice'] < 2, filteredOptions)

    # Filter for options with a positive expected return
    filteredOptions = filter(lambda c: c['gain'] > 0, filteredOptions)
    filteredOptions = list(filteredOptions)

    # print("filteredOptions", filteredOptions)

    with open("filtered-options.csv", "wt") as f:
        dictWriter = csv.DictWriter(f, fieldnames=list(list(filteredOptions)[0].keys()))
        dictWriter.writeheader()
        dictWriter.writerows(filteredOptions)

    # Compute the cross correlation table
    allPairs, correlationGrid, correlationTable = correlation_analysis.computeCrossCorrelationTable()

    print("Main decorrelated option chain")

    # Now we compute the chain
    chosenOptions = []
    for n in range(5):
        # print("filteredOptions")
        # pprint(filteredOptions)
        # print(len(filteredOptions))
        remainingSymbols = list(set(c['symbol'] for c in filteredOptions))
        # print("remainingSymbols", remainingSymbols)
        currentChain = list(set(c['symbol'] for c in chosenOptions))
        chosenOption = None
        chainCorrelation = 0
        if len(chosenOptions) == 0:
            chosenOption = filteredOptions[0]
        else:
            nextSymbolCorrelations = correlation_analysis.findNextNonCorrelatedSymbols(currentChain, correlationTable, remainingSymbols)
            # Choose the best option from among the top 5 least correlated symbols remaining in the list
            nextSymbols = [val[0] for val in nextSymbolCorrelations[:5]]
            for c in filteredOptions:
                if c['symbol'] in nextSymbols:
                    chosenOption = c
                    symbolIndex = nextSymbols.index(c['symbol'])
                    chainCorrelation = nextSymbolCorrelations[symbolIndex][1]
                    break

        if chosenOption is None:
            print("There are no more options that can be included into the chain.")
            break

        chosenOptions.append(chosenOption)
        filteredOptions = list(filter(lambda c: c['symbol'] != chosenOption['symbol'], filteredOptions))
        print(f"{chosenOption['contract']} {chosenOption['symbol']} {chosenOption['expiration']} {chosenOption['strike']}. GAIN: {chosenOption['gain']} RETURN: {chosenOption['dailyReturn']} PROPORTION: {chosenOption['optimalInvestmentProportion']}. CHAIN CORRELATION: {chainCorrelation}. PROB: {chosenOption['probabilityInTheMoney']}. CLEAR: {chosenOption['clearingPrice']}")

    with open("chosen-options.csv", "wt") as f:
        dictWriter = csv.DictWriter(f, fieldnames=list(chosenOptions[0].keys()))
        dictWriter.writeheader()
        dictWriter.writerows(chosenOptions)
