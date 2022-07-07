import multiprocessing

numWorkers = multiprocessing.cpu_count()

priceSimulationTradingDaysOfHistoricalDataToUse = 120
priceSimulationNumberOfSimulations = 100000

investmentSimulationConsecutiveTrades = 25
investmentSimulationNumberOfSimulations = 1000
# investmentSimulationNumberOfSimulations = 10000
investmentSimulationOutlierProportionToDiscard = 0.001

optionPriceIncrement = 0.5
optionChainStartPriceRatio = 0.5
optionChainEndPriceRatio = 2.0
optionClearingPriceSpreadMidpoint = 0.7
optionMaxExpirationTimeDays = 25

verboseOutput = False
generateCharts = False

symbolsToTrade = [
    # Tech stocks
    "MGC",
    "HOOD",
    "COIN",
    "AAPL",
    "MSFT",
    "GOOG",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "AVGO",
    "ASML",
    "ORCL",
    "CSCO",
    "ADBE",
    "CRM",
    "INTC",
    "QCOM",
    "TXN",
    "AMD",
    "IBM",
    "SAP",
    "INTU",
    "SONY",
    "NOW",
    "PYPL",
    "AMAT",
    "NFLX",
    "BKNG",
    "ADI",
    "MU",
    "ABNB",
    # "ATVI", # Removing activision blizzard because they are going through an acquisition, which makes things unpredictable
    "VMW",
    "PANW",
    "TEAM",
    "SNOW",
    "SHOP",
    "UBER",
    "ROP",
    "NXPI",
    "CRWD",
    "ADSK",
    "WDAY",
    "SQ",
    "DELL",
    "HPQ",
    "EA",
    "ZM",
    "VEEV",
    "ANET",
    "TWTR",
    "DDOG",
    "STM",
    "NOK",
    "ERIC",
    "GPN",
    "MCHP"
]
